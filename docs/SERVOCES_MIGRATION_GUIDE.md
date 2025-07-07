# Doraemon Services 模块重构迁移指南

## 概述

我们将所有 service 相关的代码重构到了 `doraemon.services` 模块下，与 `logger` 模块保持一致的结构。

## 新的模块结构

```
src/doraemon/
├── __init__.py              # 主模块入口，提供向后兼容
├── services/                # 新的 services 模块
│   ├── __init__.py         # 导出所有服务相关功能
│   ├── base_service.py     # 基础服务类（原 remote_service.py）
│   ├── enhanced_service.py # 增强服务类（原 remote_service_enhanced.py）
│   ├── async_service.py    # 异步服务类（原 async_remote_service.py）
│   └── config_manager.py   # 配置管理器（原 service_config_manager.py）
├── logger/                 # 现有的 logger 模块
└── ...                     # 其他模块
```

## 导入方式变更

### 旧的导入方式（仍然兼容）

```python
# 基础服务
from doraemon.remote_service import BaseService

# 增强服务
from doraemon.remote_service_enhanced import create_service, get_service

# 异步服务
from doraemon.async_remote_service import create_async_service
```

### 新的推荐导入方式

```python
# 从 services 模块导入所有功能
from doraemon.services import (
    # 基础服务
    BaseService,
    
    # 增强同步服务
    create_service,
    get_service,
    service_call,
    ServiceRegistry,
    
    # 异步服务
    create_async_service,
    get_async_service,
    async_service_call,
    AsyncServiceRegistry,
    
    # 配置管理
    ServiceConfigManager,
    global_monitor
)
```

### 顶层导入（简化用法）

```python
# 从主模块导入常用功能
from doraemon import BaseService, create_service, create_async_service
```

## 使用示例

### 1. 基础服务（向后兼容）

```python
from doraemon.services import BaseService

service = BaseService(
    name="my_service",
    service_url="http://api.example.com/endpoint",
    service_method="post",
    input_proto=InputProto,
    output_proto=OutputProto
)

result = service(json=data, timeout=30)
```

### 2. 增强服务

```python
from doraemon.services import create_service

service = create_service(
    name="enhanced_service",
    service_url="http://api.example.com/endpoint",
    service_method="post",
    input_proto=InputProto,
    output_proto=OutputProto,
    timeout=30.0,
    max_retries=3,
    pool_connections=10
)

# 使用缓存
result = service(json_data=data, use_cache=True, cache_ttl=300)
```

### 3. 异步服务

```python
from doraemon.services import create_async_service
import asyncio

async def main():
    service = create_async_service(
        name="async_service",
        service_url="http://api.example.com/endpoint",
        service_method="post",
        input_proto=InputProto,
        output_proto=OutputProto
    )
    
    # 单个调用
    result = await service(json_data=data)
    
    # 批量调用
    batch_results = await service.batch_call(requests, max_concurrent=10)
    
    await service.close()

asyncio.run(main())
```

### 4. 服务注册表

```python
from doraemon.services import get_service, ServiceRegistry

# 获取已注册的服务
service = get_service("my_service")

# 列出所有服务
all_services = ServiceRegistry.list_services()
```

### 5. 装饰器用法

```python
from doraemon.services import service_call, async_service_call

# 同步装饰器
@service_call("my_service", use_cache=True)
def query_data(question: str):
    return {"json_data": {"question": question}}

# 异步装饰器
@async_service_call("my_async_service")
async def async_query_data(question: str):
    return {"json_data": {"question": question}}
```

## 迁移步骤

### 1. 立即可用（无需修改代码）

由于我们保持了向后兼容，现有代码无需修改即可继续使用。

### 2. 渐进式迁移（推荐）

1. **更新导入语句**：
   ```python
   # 旧的
   from doraemon.remote_service import BaseService
   
   # 新的
   from doraemon.services import BaseService
   ```

2. **使用新功能**：
   - 升级到增强服务获得连接池、缓存、熔断器等功能
   - 使用异步服务提高并发性能
   - 使用装饰器简化代码

3. **配置管理**：
   - 将服务配置迁移到 YAML/JSON 文件
   - 使用 ServiceConfigManager 统一管理

### 3. 示例文件

- `examples/services_module_example.py` - 新模块使用示例
- `examples/enhanced_service_example.py` - 增强功能示例  
- `examples/async_service_example.py` - 异步功能示例

## 优势

1. **模块化**：代码结构更清晰，与 logger 模块保持一致
2. **向后兼容**：现有代码无需修改
3. **功能丰富**：连接池、缓存、熔断器、异步支持等企业级特性
4. **易于扩展**：模块化设计便于添加新功能
5. **统一管理**：所有服务相关功能在一个模块下

## 注意事项

1. **依赖项**：异步功能需要 `aiohttp`，配置文件功能需要 `PyYAML`
2. **向后兼容**：旧的导入方式将在未来版本中逐步废弃
3. **文档**：建议更新项目文档以反映新的模块结构

## 下一步

1. 测试新模块功能
2. 根据需要添加额外的配置选项
3. 完善错误处理和日志记录
4. 添加更多企业级特性（如服务发现、负载均衡等）
