"""
异步版本的远程服务客户端
支持异步调用和批量处理
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp
import structlog
from dacite import from_dict

logger = structlog.getLogger(__name__)


@dataclass
class AsyncServiceConfig:
    """异步服务配置"""
    name: str
    service_url: str
    service_method: str
    input_proto: Any
    output_proto: Any
    timeout: float = 30.0
    max_retries: int = 3
    connector_limit: int = 100
    connector_limit_per_host: int = 30
    verify_ssl: bool = True
    headers: Optional[Dict[str, str]] = None


class AsyncConnectionManager:
    """异步连接管理器"""
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions = {}
            cls._instance._initialized = False
        return cls._instance
    
    async def get_session(self, service_name: str, config: AsyncServiceConfig) -> aiohttp.ClientSession:
        """获取或创建异步会话"""
        async with self._lock:
            if service_name not in self._sessions:
                connector = aiohttp.TCPConnector(
                    limit=config.connector_limit,
                    limit_per_host=config.connector_limit_per_host,
                    ssl=config.verify_ssl
                )
                
                timeout = aiohttp.ClientTimeout(total=config.timeout)
                
                headers = config.headers or {}
                
                session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers=headers
                )
                
                self._sessions[service_name] = session
                logger.info(f"Created async session for service: {service_name}")
        
        return self._sessions[service_name]
    
    async def close_session(self, service_name: str):
        """关闭指定服务的会话"""
        async with self._lock:
            if service_name in self._sessions:
                await self._sessions[service_name].close()
                del self._sessions[service_name]
                logger.info(f"Closed async session for service: {service_name}")
    
    async def close_all_sessions(self):
        """关闭所有会话"""
        async with self._lock:
            for session in self._sessions.values():
                await session.close()
            self._sessions.clear()


class AsyncService:
    """异步服务类"""
    
    def __init__(self, config: AsyncServiceConfig):
        self.config = config
        self.connection_manager = AsyncConnectionManager()
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure = 0
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_timeout = 60
    
    def _is_circuit_breaker_open(self) -> bool:
        """检查熔断器状态"""
        if self._circuit_breaker_failures >= self._circuit_breaker_threshold:
            if time.time() - self._circuit_breaker_last_failure < self._circuit_breaker_timeout:
                return True
            else:
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
            logger.error("check proto failed.", exception=e)
            return False
    
    async def __call__(
        self,
        timeout: Optional[float] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[Any]:
        """异步调用远程服务"""
        
        # 检查熔断器
        if self._is_circuit_breaker_open():
            logger.error(f"Circuit breaker is open for service: {self.config.name}")
            return None
        
        # 验证输入数据
        _check_data = next((x for x in [data, json_data, params] if x is not None), {})
        if not self.check_proto(data=_check_data, proto=self.config.input_proto):
            logger.error(f"Input validation failed for service: {self.config.name}")
            return None
        
        # 获取会话
        session = await self.connection_manager.get_session(self.config.name, self.config)
        
        # 合并headers
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        logger.info(f"Making async request to service: {self.config.name}")
        
        try:
            # 发送异步请求
            async with getattr(session, self.config.service_method)(
                url=self.config.service_url,
                params=params,
                json=json_data,
                data=data,
                headers=request_headers
            ) as response:
                
                if response.status != 200:
                    self._record_failure()
                    logger.error(f"Request failed with status: {response.status}")
                    return None
                
                # 解析响应
                try:
                    result_data = await response.json()
                except Exception as e:
                    self._record_failure()
                    logger.error(f"Failed to parse JSON response: {e}")
                    return None
                
                # 验证输出数据
                if not self.check_proto(result_data, self.config.output_proto):
                    self._record_failure()
                    logger.error(f"Output validation failed for service: {self.config.name}")
                    return None
                
                # 记录成功
                self._record_success()
                logger.info(f"Service request successful: {self.config.name}")
                
                return from_dict(self.config.output_proto, result_data)
                
        except Exception as e:
            self._record_failure()
            logger.error(f"Request exception: {e}")
            return None
    
    async def batch_call(
        self,
        requests: List[Dict[str, Any]],
        max_concurrent: int = 10
    ) -> List[Optional[Any]]:
        """批量异步调用"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def single_request(request_data):
            async with semaphore:
                return await self(**request_data)
        
        tasks = [single_request(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch request failed: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def close(self):
        """关闭服务连接"""
        await self.connection_manager.close_session(self.config.name)


class AsyncServiceRegistry:
    """异步服务注册表"""
    _services = {}
    
    @classmethod
    def register(cls, config: AsyncServiceConfig) -> AsyncService:
        """注册异步服务"""
        service = AsyncService(config)
        cls._services[config.name] = service
        logger.info(f"Registered async service: {config.name}")
        return service
    
    @classmethod
    def get_service(cls, name: str) -> Optional[AsyncService]:
        """获取已注册的异步服务"""
        return cls._services.get(name)
    
    @classmethod
    async def close_all(cls):
        """关闭所有服务"""
        for service in cls._services.values():
            await service.close()


# 便利函数
def create_async_service(
    name: str,
    service_url: str,
    service_method: str,
    input_proto: Any,
    output_proto: Any,
    **kwargs
) -> AsyncService:
    """创建异步服务"""
    config = AsyncServiceConfig(
        name=name,
        service_url=service_url,
        service_method=service_method,
        input_proto=input_proto,
        output_proto=output_proto,
        **kwargs
    )
    return AsyncServiceRegistry.register(config)


async def get_async_service(name: str) -> Optional[AsyncService]:
    """获取异步服务"""
    return AsyncServiceRegistry.get_service(name)


# 异步装饰器
def async_service_call(service_name: str):
    """异步服务调用装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            service = AsyncServiceRegistry.get_service(service_name)
            if not service:
                raise ValueError(f"Async service {service_name} not found")
            
            # 从函数参数中提取服务调用参数
            call_kwargs = {}
            service_params = ['timeout', 'params', 'json_data', 'data', 'headers']
            for param in service_params:
                if param in kwargs:
                    call_kwargs[param] = kwargs.pop(param)
            
            return await service(**call_kwargs)
        return wrapper
    return decorator
