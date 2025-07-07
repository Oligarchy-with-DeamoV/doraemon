import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, Literal, Optional, Union

import requests
import structlog
from dacite import from_dict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = structlog.getLogger(__name__)


@dataclass
class ServiceConfig:
    """服务配置类"""
    name: str
    service_url: str
    service_method: Literal["post", "get", "put", "delete", "patch"]
    input_proto: Any
    output_proto: Any
    timeout: float = 30.0
    max_retries: int = 3
    pool_connections: int = 10
    pool_maxsize: int = 20
    verify: bool = True
    headers: Optional[Dict[str, str]] = None


class ConnectionManager:
    """连接管理器 - 单例模式"""
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._sessions = {}
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._sessions = {}
            self._initialized = True
    
    def get_session(self, service_name: str, config: ServiceConfig) -> requests.Session:
        """获取或创建会话"""
        if service_name not in self._sessions:
            session = requests.Session()
            
            # 配置重试策略
            retry_strategy = Retry(
                total=config.max_retries,
                status_forcelist=[429, 500, 502, 503, 504],
                backoff_factor=0.3,
                raise_on_redirect=False,
                raise_on_status=False
            )
            
            # 配置HTTP适配器
            adapter = HTTPAdapter(
                pool_connections=config.pool_connections,
                pool_maxsize=config.pool_maxsize,
                max_retries=retry_strategy
            )
            
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # 设置默认headers
            if config.headers:
                session.headers.update(config.headers)
            
            self._sessions[service_name] = session
            logger.info(f"Created new session for service: {service_name}")
        
        return self._sessions[service_name]
    
    def close_session(self, service_name: str):
        """关闭指定服务的会话"""
        if service_name in self._sessions:
            self._sessions[service_name].close()
            del self._sessions[service_name]
            logger.info(f"Closed session for service: {service_name}")
    
    def close_all_sessions(self):
        """关闭所有会话"""
        for service_name in list(self._sessions.keys()):
            self.close_session(service_name)


class ServiceRegistry:
    """服务注册表"""
    _services = {}
    _lock = Lock()
    
    @classmethod
    def register(cls, config: ServiceConfig) -> 'EnhancedService':
        """注册服务"""
        with cls._lock:
            if config.name in cls._services:
                logger.warning(f"Service {config.name} already registered, updating configuration")
            
            service = EnhancedService(config)
            cls._services[config.name] = service
            logger.info(f"Registered service: {config.name}")
            return service
    
    @classmethod
    def get_service(cls, name: str) -> Optional['EnhancedService']:
        """获取已注册的服务"""
        return cls._services.get(name)
    
    @classmethod
    def list_services(cls) -> Dict[str, 'EnhancedService']:
        """列出所有已注册的服务"""
        return cls._services.copy()


class ResponseCache:
    """简单的响应缓存"""
    def __init__(self, ttl: int = 300):  # 默认5分钟TTL
        self._cache = {}
        self._timestamps = {}
        self._ttl = ttl
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            if key in self._cache:
                if time.time() - self._timestamps[key] < self._ttl:
                    return self._cache[key]
                else:
                    # 过期删除
                    del self._cache[key]
                    del self._timestamps[key]
        return None
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = time.time()
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()


class EnhancedService:
    """增强的服务类"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.connection_manager = ConnectionManager()
        self.cache = ResponseCache()
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure = 0
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_timeout = 60  # 秒
    
    def _generate_cache_key(self, params=None, json_data=None, data=None) -> str:
        """生成缓存键"""
        import hashlib
        content = f"{self.config.service_url}:{params}:{json_data}:{data}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_circuit_breaker_open(self) -> bool:
        """检查熔断器是否开启"""
        if self._circuit_breaker_failures >= self._circuit_breaker_threshold:
            if time.time() - self._circuit_breaker_last_failure < self._circuit_breaker_timeout:
                return True
            else:
                # 重置熔断器
                self._circuit_breaker_failures = 0
        return False
    
    def _record_failure(self):
        """记录失败"""
        self._circuit_breaker_failures += 1
        self._circuit_breaker_last_failure = time.time()
    
    def _record_success(self):
        """记录成功"""
        self._circuit_breaker_failures = 0
    
    def check_proto(self, data, proto) -> bool:
        """验证数据格式"""
        try:
            from_dict(proto, data)
            return True
        except Exception as e:
            logger.error("check proto failed.", exception=str(e), proto=str(proto), data=data)
            return False
    
    def __call__(
        self,
        timeout: Optional[float] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        use_cache: bool = False,
        cache_ttl: int = 300
    ) -> Optional[Any]:
        """调用远程服务"""
        
        # 检查熔断器
        if self._is_circuit_breaker_open():
            logger.error(f"Circuit breaker is open for service: {self.config.name}")
            return None
        
        # 使用配置的默认超时时间
        timeout = timeout or self.config.timeout
        
        # 检查缓存
        if use_cache:
            cache_key = self._generate_cache_key(params, json_data, data)
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for service: {self.config.name}")
                return cached_result
        
        # 验证输入数据
        _check_data = next((x for x in [data, json_data, params] if x is not None), {})
        if not self.check_proto(data=_check_data, proto=self.config.input_proto):
            logger.error(
                "Transform input data to proto failed.",
                proto=str(self.config.input_proto),
                params=params,
                json_data=json_data,
                headers=headers,
                name=self.config.name,
            )
            return None
        
        # 获取会话
        session = self.connection_manager.get_session(self.config.name, self.config)
        
        # 合并headers
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        # 获取verify设置
        verify = self.config.verify
        if metadata and "verify" in metadata:
            verify = metadata["verify"]
        
        logger.info(
            "Request remote service.",
            json_data=json_data,
            params=params,
            headers=request_headers,
            service_url=self.config.service_url,
            service_method=self.config.service_method,
            name=self.config.name,
        )
        
        try:
            # 发送请求
            response = getattr(session, self.config.service_method)(
                url=self.config.service_url,
                params=params,
                data=data,
                json=json_data,
                verify=verify,
                headers=request_headers,
                timeout=timeout,
            )
            
            if response.status_code != 200:
                self._record_failure()
                logger.error(
                    "Request remote service failed.",
                    status_code=response.status_code,
                    headers=request_headers,
                    service_url=self.config.service_url,
                    service_method=self.config.service_method,
                    params=params,
                    json_data=json_data,
                    name=self.config.name,
                )
                return None
            
            # 解析响应
            try:
                result_data = response.json()
            except ValueError as e:
                self._record_failure()
                logger.error(f"Failed to parse JSON response: {e}")
                return None
            
            # 验证输出数据
            if not self.check_proto(result_data, self.config.output_proto):
                self._record_failure()
                logger.error(
                    "Transform output data to proto failed.",
                    proto=str(self.config.output_proto),
                    data=result_data,
                    headers=request_headers,
                    name=self.config.name,
                )
                return None
            
            # 记录成功
            self._record_success()
            
            logger.info(
                "Service requests success.",
                service_url=self.config.service_url,
                service_method=self.config.service_method,
                params=params,
                json_data=json_data,
                name=self.config.name,
                outputs=result_data,
            )
            
            # 转换为目标对象
            result = from_dict(self.config.output_proto, result_data)
            
            # 缓存结果
            if use_cache:
                self.cache.set(cache_key, result)
            
            return result
            
        except requests.exceptions.RequestException as e:
            self._record_failure()
            logger.error(
                "Request exception occurred.",
                exception=str(e),
                service_url=self.config.service_url,
                name=self.config.name,
            )
            return None
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            session = self.connection_manager.get_session(self.config.name, self.config)
            response = session.get(
                url=f"{self.config.service_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def close(self):
        """关闭服务连接"""
        self.connection_manager.close_session(self.config.name)


# 便利函数
def create_service(
    name: str,
    service_url: str,
    service_method: Literal["post", "get", "put", "delete", "patch"],
    input_proto: Any,
    output_proto: Any,
    **kwargs
) -> EnhancedService:
    """创建并注册服务"""
    config = ServiceConfig(
        name=name,
        service_url=service_url,
        service_method=service_method,
        input_proto=input_proto,
        output_proto=output_proto,
        **kwargs
    )
    return ServiceRegistry.register(config)


def get_service(name: str) -> Optional[EnhancedService]:
    """获取已注册的服务"""
    return ServiceRegistry.get_service(name)


# 装饰器支持
def service_call(service_name: str, use_cache: bool = False, cache_ttl: int = 300):
    """服务调用装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            service = get_service(service_name)
            if not service:
                raise ValueError(f"Service {service_name} not found")
            
            # 调用原函数获取服务调用参数
            func_result = func(*args, **kwargs)
            
            # 如果原函数返回字典，用作服务调用参数
            if isinstance(func_result, dict):
                call_kwargs = func_result.copy()
                call_kwargs['use_cache'] = use_cache
                call_kwargs['cache_ttl'] = cache_ttl
                return service(**call_kwargs)
            else:
                # 如果原函数返回其他内容，直接返回
                return func_result
        return wrapper
    return decorator
