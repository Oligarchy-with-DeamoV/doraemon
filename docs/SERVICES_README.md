# Doraemon Services 模块

## 简介

Doraemon Services 是一个企业级的远程服务调用框架，提供了完整的服务治理能力，包括连接池管理、熔断器、缓存、监控等功能。

## 特性

### 🚀 核心功能
- **连接池管理** - 高效的HTTP连接复用
- **熔断器模式** - 防止服务雪崩
- **响应缓存** - 减少重复请求开销
- **服务注册表** - 统一服务管理
- **监控指标** - 实时性能监控

### ⚡ 高级功能
- **异步支持** - 高并发场景优化
- **批量调用** - 高效的批处理
- **装饰器支持** - 简化代码编写
- **配置驱动** - YAML/JSON配置文件支持
- **向后兼容** - 平滑迁移

## 快速开始

### 安装依赖

```bash
# 基础功能
pip install requests dacite structlog

# 异步功能（可选）
pip install aiohttp

# 配置文件支持（可选）
pip install PyYAML
```

### 基础用法

```python
from doraemon.services import BaseService
from dataclasses import dataclass
from typing import List

@dataclass
class InputProto:
    question: str
    count: int

@dataclass  
class OutputProto:
    result: str
    
# 创建服务
service = BaseService(
    name="my_service",
    service_url="http://api.example.com/endpoint",
    service_method="post",
    input_proto=InputProto,
    output_proto=OutputProto
)

# 调用服务
result = service(
    json={"question": "Hello", "count": 1},
    timeout=30
)
```

### 增强功能

```python
from doraemon.services import create_service

# 创建增强服务
service = create_service(
    name="enhanced_service",
    service_url="http://api.example.com/endpoint", 
    service_method="post",
    input_proto=InputProto,
    output_proto=OutputProto,
    timeout=30.0,
    max_retries=3,
    pool_connections=10,
    pool_maxsize=20
)

# 使用缓存
result = service(
    json_data={"question": "Hello", "count": 1},
    use_cache=True,
    cache_ttl=300  # 5分钟缓存
)
```

### 异步调用

```python
from doraemon.services import create_async_service
import asyncio

async def main():
    # 创建异步服务
    service = create_async_service(
        name="async_service",
        service_url="http://api.example.com/endpoint",
        service_method="post", 
        input_proto=InputProto,
        output_proto=OutputProto
    )
    
    # 单个异步调用
    result = await service(
        json_data={"question": "Hello", "count": 1}
    )
    
    # 批量异步调用
    requests = [
        {"json_data": {"question": f"Question {i}", "count": 1}}
        for i in range(10)
    ]
    
    results = await service.batch_call(
        requests=requests,
        max_concurrent=5
    )
    
    await service.close()

asyncio.run(main())
```

### 装饰器用法

```python
from doraemon.services import service_call, create_service

# 首先注册服务
create_service(
    name="my_service",
    service_url="http://api.example.com/endpoint",
    service_method="post",
    input_proto=InputProto,
    output_proto=OutputProto
)

# 使用装饰器
@service_call("my_service", use_cache=True, cache_ttl=300)
def query_api(question: str, count: int = 1):
    return {
        "json_data": {"question": question, "count": count},
        "headers": {"Authorization": "Bearer token"}
    }

# 调用
result = query_api("What is AI?", count=5)
```

## 配置管理

### YAML 配置文件

```yaml
services:
  my_service:
    service_url: "http://api.example.com/endpoint"
    service_method: "post"
    input_proto: "myapp.protos.InputProto"
    output_proto: "myapp.protos.OutputProto"
    timeout: 30.0
    max_retries: 3
    pool_connections: 10
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer your-token"
```

### 从配置文件加载

```python
from doraemon.services import ServiceConfigManager

# 从YAML加载（需要安装PyYAML）
services = ServiceConfigManager.load_from_yaml("services.yaml")

# 从JSON加载
services = ServiceConfigManager.load_from_json("services.json")

# 使用加载的服务
my_service = services["my_service"]
result = my_service(json_data={"question": "Hello"})
```

## 监控和指标

```python
from doraemon.services import global_monitor

# 获取服务指标
metrics = global_monitor.get_metrics("my_service") 
print(f"成功率: {metrics['success_rate']}")
print(f"平均响应时间: {metrics['avg_response_time']}")

# 获取所有服务指标
all_metrics = global_monitor.get_all_metrics()
for service_name, metrics in all_metrics.items():
    print(f"{service_name}: {metrics}")
```

## 服务注册表

```python
from doraemon.services import get_service, ServiceRegistry

# 获取已注册的服务
service = get_service("my_service")

# 列出所有已注册服务
all_services = ServiceRegistry.list_services()
print(f"已注册服务: {list(all_services.keys())}")

# 健康检查
health_status = service.health_check()
print(f"服务健康状态: {'正常' if health_status else '异常'}")
```

## 性能对比

| 功能 | 基础服务 | 增强服务 | 异步服务 |
|------|----------|----------|----------|
| 连接复用 | ❌ | ✅ | ✅ |
| 响应缓存 | ❌ | ✅ | ❌ |
| 熔断器 | ❌ | ✅ | ✅ |
| 批量调用 | ❌ | ❌ | ✅ |
| 并发性能 | 低 | 中 | 高 |
| 资源使用 | 高 | 中 | 低 |

## 最佳实践

### 1. 服务配置
- 使用配置文件管理服务配置
- 设置合理的超时时间和重试次数
- 配置适当的连接池大小

### 2. 错误处理
- 使用熔断器防止雪崩
- 设置合理的失败阈值
- 监控服务健康状态

### 3. 性能优化
- 高并发场景使用异步服务
- 合理使用缓存减少重复请求
- 批量处理提高吞吐量

### 4. 监控运维
- 定期检查服务指标
- 设置告警阈值
- 记录和分析错误日志

## 示例项目

查看 `examples/` 目录下的完整示例：
- `services_module_example.py` - 基础使用示例
- `enhanced_service_example.py` - 增强功能示例
- `async_service_example.py` - 异步功能示例

## 迁移指南

如果你正在从旧版本迁移，请查看 [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) 获取详细的迁移指导。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！
