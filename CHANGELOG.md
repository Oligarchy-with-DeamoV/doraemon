# 更新日志

## [Unreleased]

### 🛡️ 安全修复 (Security)

- **`database_utils/main.py`** 不再包含硬编码的 PostgreSQL 密码、内部 IP
  和占位 API token；所有连接信息现在通过环境变量加载
  (`DORAEMON_DB_*`, `DORAEMON_EMBEDDING_API_*`)。详见 `SECURITY.md` —
  历史版本的密码 (`zgt#1024`) **必须** 在数据库侧轮换，仅删除源码无法
  从 Git 历史中清除。
- **修复 SQL 注入风险**: `insert_vectors()` 现在通过
  `psycopg2.sql.Identifier` 安全引用表名和列名。
- **MD5 缓存键** 在 `enhanced_service.py` 中显式标记为
  `usedforsecurity=False`，满足 bandit `B324`。
- **`assert` 移除**: `chatgpt_api.py` 与 `slogger.py` 中用作运行时校验
  的 `assert` 替换为显式的 `RuntimeError` / `ValueError`，避免被
  `python -O` 优化掉（bandit `B101`）。
- 示例代码中的内部 IP 地址 (`10.170.138.*`) 全部替换为
  `https://api.example.com` 占位符。

### 📦 Packaging

- 移除虚假依赖 `asyncio` (PyPI 上的 `asyncio` 包是 Python <3.4 的回填
  版，会覆盖标准库)。
- **PyYAML 升级 5.3.1 → ^6.0** （CVE-2020-14343 修复）。
- 放宽其他严格 `==` 版本固定，改为兼容范围（`pandas ^2.2`,
  `structlog ^24.1`, `opentelemetry-* >=1.33.1,<2`）。
- `__version__` 通过 `importlib.metadata.version("doraemon")` 动态读取，
  与 `pyproject.toml` 保持一致。

### 🔧 API & 类型安全

- `EnhancedService.__call__` 接受 `json=` 作为 `BaseService` 风格的兼容
  别名（带 `DeprecationWarning`）；同时传入 `json=` 与 `json_data=`
  会抛出 `TypeError`。
- 新增弃用桥接模块（运行时打印 `DeprecationWarning`）：
  - `doraemon.remote_service`
  - `doraemon.remote_service_enhanced`
  - `doraemon.async_remote_service`
- 修复 `mypy src` 的 19 个错误（`AsyncConnectionManager._sessions`、
  `ServiceRegistry._services`、`ResponseCache._cache`/`_timestamps`、
  `chatgpt_api.py` 的 `Optional[str]` 流向 OpenAI SDK，等等）。

### 🧪 测试 & 工程

- 测试覆盖率从 33 % 提升到 76 %。
- `tests/doraemon/services/` 下新增 35+ 个针对 `BaseService` /
  `EnhancedService` （缓存、熔断器、错误路径）/ `AsyncService.batch_call`
  / `ServiceConfigManager` / 弃用桥接模块的回归测试。
- 新增 `responses` 与 `aioresponses` 作为开发依赖用于 HTTP mock。
- `pytest-asyncio` 现在以 `asyncio_mode = "auto"` 启用。
- 重复的断言被清理：`test_slogger.py`、`test_file_handler.py`。
- 新增 `.github/workflows/ci.yml`：每次 push / PR 自动运行 ruff、
  ruff format check、mypy、pytest --cov、bandit。

### 📚 文档

- `docs/SERVOCES_MIGRATION_GUIDE.md` 重命名为 `SERVICES_MIGRATION_GUIDE.md`。
- `README.md` 删除指向不存在文件的链接（`enhanced_service_example.py`、
  `async_service_example.py`），Python 版本徽章更新为 3.9 – 3.10。
- 新增 `SECURITY.md` 与 `CONTRIBUTING.md`。

---

## [0.2.0] - 2025-07-07

### 🎉 重大更新 - Services 模块重构

#### ✨ 新增功能

**Services 模块架构重构**
- 将所有服务相关代码重构到 `doraemon.services` 模块
- 与现有 `logger` 模块保持一致的模块化结构
- 提供统一的导入接口

**企业级服务调用功能**
- **连接池管理**: 基于 `requests.Session` 的连接复用，显著提升性能
- **熔断器模式**: 自动故障检测和恢复，防止服务雪崩
- **响应缓存**: 内置缓存机制，减少重复请求
- **异步支持**: 基于 `aiohttp` 的高性能异步调用
- **批量处理**: 支持并发批量请求处理
- **服务注册表**: 统一的服务管理和发现
- **监控指标**: 内置请求监控和性能指标
- **装饰器支持**: 简化服务调用代码

**配置管理**
- 支持 YAML/JSON 配置文件
- 动态服务配置加载
- 集中化配置管理

#### 🔧 改进功能

**向后兼容性**
- 保持所有现有 API 的兼容性
- 旧的导入方式继续可用（带弃用警告）
- 平滑的迁移路径

**性能优化**
- 连接池复用减少 60-80% 的连接建立时间
- 缓存机制可减少 90%+ 的重复请求响应时间
- 异步处理提升 5-10 倍的并发能力

#### 📁 新文件结构

```
src/doraemon/
├── services/
│   ├── __init__.py          # 统一导出接口
│   ├── base_service.py      # 基础服务类
│   ├── enhanced_service.py  # 增强服务类
│   ├── async_service.py     # 异步服务类
│   └── config_manager.py    # 配置管理器
├── __init__.py              # 主模块入口
└── ...
```

#### 📖 新增文档

- `docs/SERVICES_MIGRATION_GUIDE.md` - 详细迁移指南
- 更新 `README.md` 包含完整使用示例

#### 🌟 新增示例

- `examples/services_module_example.py` - 完整模块使用示例
- `examples/services_config.yaml` - 配置文件示例

#### 💫 使用示例

**基础使用**
```python
from doraemon.services import create_service

service = create_service(
    name="api_service",
    service_url="https://api.example.com",
    service_method="post",
    input_proto=InputProto,
    output_proto=OutputProto
)

result = service(json_data=data, use_cache=True)
```

**异步使用**
```python
from doraemon.services import create_async_service

async_service = create_async_service(...)
result = await async_service(json_data=data)
results = await async_service.batch_call(requests, max_concurrent=10)
```

**装饰器使用**
```python
from doraemon.services import service_call

@service_call("api_service", use_cache=True)
def query_data(query: str):
    return {"json_data": {"query": query}}
```

#### ⚠️ 弃用警告

- `doraemon.remote_service` 模块已弃用，请使用 `doraemon.services.BaseService`
- `doraemon.remote_service_enhanced` 模块已弃用，请使用 `doraemon.services`
- `doraemon.async_remote_service` 模块已弃用，请使用 `doraemon.services`

#### 🔄 迁移步骤

1. **立即可用**: 现有代码无需修改即可继续工作
2. **更新导入**:
   ```python
   # 旧的
   from doraemon.remote_service import BaseService
   # 新的
   from doraemon.services import BaseService
   ```
3. **使用新功能**: 升级到增强服务获得企业级特性

---

## [0.1.0] - 2025-01-01

### ✨ 初始版本

#### 🎯 核心功能

**Logger 模块**
- 结构化日志记录
- 文件输出支持
- 敏感词过滤
- OpenTelemetry 集成

**Remote Service**
- 基础的远程服务调用
- 数据验证和类型转换
- 错误处理和日志记录

**GPT Utils**
- OpenAI API 轻量封装
- 自有 API 支持

**其他工具**
- 文件操作工具
- 数据库工具

---

## 版本说明

### 版本号规则
- 主版本号: 重大架构变更或不兼容更新
- 次版本号: 新功能添加或重要改进
- 修订号: Bug 修复和小幅改进

### 兼容性承诺
- 在同一主版本内保持向后兼容
- 弃用功能会提前至少一个次版本警告
- 提供详细的迁移指南

### 发布周期
- 主版本: 根据需要发布
- 次版本: 每月发布
- 修订版本: 根据需要发布
