# Doraemon - Python 开发工具箱 🧰

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()

本项目是一个现代化的 Python 开发工具箱，将常用的开发工具和最佳实践集成到一个仓库中，提供企业级的开发体验。

## ✨ 主要特性

### 🎯 核心模块

1. **📝 Logger 模块** - 结构化日志记录
   - 文件输出支持
   - 敏感词过滤
   - OpenTelemetry 集成
   - 多种日志处理器

2. **🌐 Services 模块** - 企业级远程服务调用框架
   - 连接池管理
   - 熔断器模式
   - 响应缓存
   - 异步支持
   - 服务注册与发现
   - 监控指标
   - 装饰器支持

3. **🤖 GPT 工具** - OpenAI API 轻量封装
   - 支持自有 API 调用
   - 简化的接口设计

4. **📁 文件工具** - 常用文件操作工具

5. **🗄️ 数据库工具** - 数据库操作辅助工具

## 🚀 快速开始

### 安装

```bash
pip install doraemon
# 或者从源码安装
git clone https://github.com/your-repo/doraemon.git
cd doraemon
poetry install
```

### 基本使用

#### 日志记录

```python
from doraemon import slogger

# 使用结构化日志
slogger.info("用户登录", user_id=123, action="login")
slogger.error("处理失败", error="数据格式错误", request_id="abc123")
```

#### 远程服务调用

```python
from doraemon.services import create_service
from dataclasses import dataclass
from typing import List

# 定义数据结构
@dataclass
class RequestData:
    query: str
    limit: int

@dataclass  
class ResponseData:
    results: List[str]
    total: int

# 创建服务
service = create_service(
    name="api_service",
    service_url="https://api.example.com/search",
    service_method="post",
    input_proto=RequestData,
    output_proto=ResponseData,
    timeout=30.0,
    max_retries=3,
    pool_connections=10
)

# 调用服务
result = service(
    json_data={"query": "python", "limit": 10},
    use_cache=True,  # 启用缓存
    cache_ttl=300   # 缓存5分钟
)

if result:
    print(f"搜索到 {result.total} 条结果")
```

#### 异步服务调用

```python
import asyncio
from doraemon.services import create_async_service

async def main():
    # 创建异步服务
    async_service = create_async_service(
        name="async_api",
        service_url="https://api.example.com/data", 
        service_method="get",
        input_proto=RequestData,
        output_proto=ResponseData
    )
    
    # 单个异步调用
    result = await async_service(params={"id": 123})
    
    # 批量并发调用
    requests = [
        {"params": {"id": i}} for i in range(1, 11)
    ]
    results = await async_service.batch_call(
        requests=requests,
        max_concurrent=5
    )
    
    await async_service.close()

asyncio.run(main())
```

#### 装饰器使用

```python
from doraemon.services import service_call

# 注册服务后使用装饰器
@service_call("api_service", use_cache=True)
def search_data(query: str, limit: int = 10):
    """搜索数据的装饰器函数"""
    return {
        "json_data": {
            "query": query,
            "limit": limit
        },
        "headers": {"Content-Type": "application/json"}
    }

# 直接调用函数即可
result = search_data("python编程", limit=20)
```

## 📖 详细文档

### Services 模块架构

```
doraemon.services/
├── BaseService          # 基础服务类（向后兼容）
├── EnhancedService      # 增强服务类
├── AsyncService         # 异步服务类
├── ServiceRegistry      # 服务注册表
├── ConnectionManager    # 连接池管理
├── ResponseCache        # 响应缓存
└── ServiceMonitor       # 监控指标
```

### 高级特性

#### 连接池管理
```python
# 自动管理 HTTP 连接池，提升性能
service = create_service(
    name="high_perf_service",
    service_url="https://api.example.com",
    service_method="post",
    input_proto=InputProto,
    output_proto=OutputProto,
    pool_connections=20,    # 连接池大小
    pool_maxsize=50,        # 最大连接数
    max_retries=3           # 重试次数
)
```

#### 熔断器模式
```python
# 自动熔断故障服务，防止雪崩
# 当连续失败5次后，熔断器开启
# 60秒后自动尝试恢复
service = create_service(
    name="resilient_service",
    # ... 其他配置
)

# 服务会自动处理熔断逻辑
result = service(json_data=data)  # 熔断时返回 None
```

#### 服务监控
```python
from doraemon.services import global_monitor

# 获取服务调用指标
metrics = global_monitor.get_metrics("api_service")
print(f"成功率: {metrics['success_rate']}")
print(f"平均响应时间: {metrics['avg_response_time']}")

# 获取所有服务指标
all_metrics = global_monitor.get_all_metrics()
```

#### 配置文件管理
```yaml
# services_config.yaml
services:
  user_api:
    service_url: "https://api.example.com/users"
    service_method: "get"
    input_proto: "myapp.schemas.UserRequest"
    output_proto: "myapp.schemas.UserResponse"
    timeout: 30.0
    max_retries: 3
    pool_connections: 10
    headers:
      Authorization: "Bearer token"
```

```python
from doraemon.services import ServiceConfigManager

# 从配置文件加载服务
services = ServiceConfigManager.load_from_yaml("services_config.yaml")
user_service = services["user_api"]
```

## 🔄 迁移指南

如果你正在使用旧版本的 doraemon，请查看 [迁移指南](docs/SERVOCES_MIGRATION_GUIDE.md) 了解如何升级到新的 Services 模块。

### 向后兼容

旧的导入方式仍然支持：
```python
# 这些导入方式仍然可用
from doraemon.remote_service import BaseService
from doraemon.remote_service_enhanced import create_service
```

但建议使用新的导入方式：
```python
# 推荐的新方式
from doraemon.services import BaseService, create_service
from doraemon import create_service  # 更简洁
```

## 📋 示例文件

- [`examples/services_module_example.py`](examples/services_module_example.py) - Services 模块完整示例
- [`examples/enhanced_service_example.py`](examples/enhanced_service_example.py) - 增强功能示例
- [`examples/async_service_example.py`](examples/async_service_example.py) - 异步功能示例
- [`examples/remote_service_example.py`](examples/remote_service_example.py) - 基础服务示例

## 🛠️ 开发环境

### 要求
- Python 3.8+
- Poetry (用于依赖管理)

### 可选依赖
- `aiohttp` - 异步服务支持
- `PyYAML` - YAML 配置文件支持
- `structlog` - 结构化日志

### 安装开发依赖

```bash
git clone https://github.com/your-repo/doraemon.git
cd doraemon
poetry install
poetry shell
```

### 运行测试

```bash
poetry run pytest
```

### 运行示例

```bash
# 基础服务示例
python examples/remote_service_example.py

# 增强服务示例  
python examples/enhanced_service_example.py

# 异步服务示例
python examples/async_service_example.py

# 完整模块示例
python examples/services_module_example.py
```

## 🤝 贡献指南

欢迎贡献代码！请确保：

1. 代码符合 PEP 8 规范
2. 添加适当的测试用例
3. 更新相关文档
4. 提交前运行测试

## 📄 许可证

本项目采用 [Apache 2.0](LICENSE) 许可证。

## 🔗 相关链接

- [API 文档](docs/)
- [更新日志](CHANGELOG.md)
- [问题反馈](https://github.com/your-repo/doraemon/issues)
- [功能请求](https://github.com/your-repo/doraemon/discussions)

---

**让 Python 开发更简单、更高效！** 🚀
