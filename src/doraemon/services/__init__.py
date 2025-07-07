"""
Doraemon Services Module

提供企业级远程服务调用框架，包含：
- 同步和异步服务调用
- 连接池管理
- 熔断器模式
- 响应缓存
- 服务注册与发现
- 监控指标
- 配置管理

使用示例:
    # 同步服务
    from doraemon.services import create_service
    
    service = create_service(
        name="my_service",
        service_url="http://api.example.com/endpoint",
        service_method="post",
        input_proto=InputProto,
        output_proto=OutputProto
    )
    
    result = service(json_data={"key": "value"})
    
    # 异步服务
    from doraemon.services import create_async_service
    
    async_service = create_async_service(
        name="my_async_service",
        service_url="http://api.example.com/endpoint",
        service_method="post",
        input_proto=InputProto,
        output_proto=OutputProto
    )
    
    result = await async_service(json_data={"key": "value"})
"""

from .async_service import (
    AsyncConnectionManager,
    AsyncService,
    AsyncServiceConfig,
    AsyncServiceRegistry,
    async_service_call,
    create_async_service,
    get_async_service,
)
from .base_service import BaseService
from .config_manager import ServiceConfigManager, ServiceMonitor, global_monitor
from .enhanced_service import (
    ConnectionManager,
    EnhancedService,
    ResponseCache,
    ServiceConfig,
    ServiceRegistry,
    create_service,
    get_service,
    service_call,
)

__all__ = [
    # 基础服务
    'BaseService',
    
    # 增强同步服务
    'ServiceConfig',
    'ConnectionManager', 
    'ServiceRegistry',
    'ResponseCache',
    'EnhancedService',
    'create_service',
    'get_service',
    'service_call',
    
    # 异步服务
    'AsyncServiceConfig',
    'AsyncConnectionManager',
    'AsyncService', 
    'AsyncServiceRegistry',
    'create_async_service',
    'get_async_service',
    'async_service_call',
    
    # 配置和监控
    'ServiceConfigManager',
    'ServiceMonitor',
    'global_monitor'
]
