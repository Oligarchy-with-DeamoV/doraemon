# Copilot Instructions for Doraemon

Doraemon is a Python development toolbox providing enterprise-grade utilities including structured logging, remote service calling framework, GPT API integration, and file/database utilities.

## Build, Test, and Lint Commands

### Environment Setup
```bash
# Install dependencies with Poetry
poetry install

# Activate Poetry shell
poetry shell
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src

# Run tests in parallel
poetry run pytest -n auto

# Run a single test file
poetry run pytest tests/doraemon/logger/test_slogger.py

# Run a specific test
poetry run pytest tests/doraemon/logger/test_slogger.py::test_specific_function

# Run async tests (uses pytest-asyncio)
poetry run pytest -k async
```

### Code Formatting
```bash
# Format code with Black
poetry run black src/ tests/
```

### Running Examples
```bash
# Basic service example
python examples/remote_service_example.py

# Services module example (comprehensive)
python examples/services_module_example.py
```

## Architecture Overview

### Module Organization
The codebase is structured into focused modules under `src/doraemon/`:
- **logger/** - Structured logging with OpenTelemetry integration
- **services/** - Enterprise remote service calling framework (main feature)
- **gpt_utils/** - OpenAI API wrapper utilities
- **database_utils/** - Database operation helpers
- **file_utils.py** - File operation utilities

### Services Module (Core Architecture)
The services module provides three layers of abstraction for HTTP service calls:

1. **BaseService** (`base_service.py`) - Original implementation, maintained for backward compatibility
   - Simple request/response handling with proto validation
   - Uses `requests` library directly
   - Proto validation via `dacite.from_dict()`

2. **EnhancedService** (`enhanced_service.py`) - Production-ready with enterprise features
   - **ConnectionManager** - Singleton managing HTTP connection pools per service
   - **ServiceRegistry** - Global registry for service reuse via `get_service()`
   - **ResponseCache** - TTL-based caching with configurable expiration
   - **CircuitBreaker** - Automatic failure detection and recovery (5 failures trigger open state, 60s recovery)
   - **ServiceMonitor** - Tracks success rates, response times, and call counts

3. **AsyncService** (`async_service.py`) - Asynchronous version for high-concurrency scenarios
   - Built on `aiohttp` instead of `requests`
   - **AsyncConnectionManager** - Manages aiohttp ClientSession instances
   - **AsyncServiceRegistry** - Async service registry
   - Supports `batch_call()` for concurrent requests with configurable max_concurrent limit

### Factory Functions
- `create_service()` - Creates EnhancedService instances with full feature set
- `create_async_service()` - Creates AsyncService instances for async/await usage
- Both register services automatically in their respective registries

### Configuration Management
- **ServiceConfigManager** (`config_manager.py`) - Load services from YAML/JSON config files
- **ServiceMonitor** - Global monitor instance (`global_monitor`) for metrics collection
- Example config: `examples/services_config.yaml`

### Backward Compatibility
The package maintains backward compatibility through aliasing:
```python
# Old import (still works)
from doraemon.remote_service import BaseService

# New import (recommended)
from doraemon.services import BaseService, create_service
from doraemon import create_service  # Shortest form
```

## Key Conventions

### Proto-Based Type Validation
All services use dataclasses as "protos" for input/output validation:
```python
@dataclass
class InputProto:
    query: str
    limit: int

@dataclass
class OutputProto:
    results: List[str]
    total: int
```
Services validate inputs using `dacite.from_dict()` before making requests and parse responses back to dataclass instances.

### Service Call Parameters
When calling services, use these parameter names consistently:
- **Enhanced/Async services**: `json_data`, `params`, `headers`, `use_cache`, `cache_ttl`
- **BaseService**: `json`, `params`, `data`, `headers`, `metadata`, `timeout`

Note the subtle difference: EnhancedService uses `json_data` while BaseService uses `json`.

### Structured Logging with slogger
Use `slogger` (from `doraemon.logger`) for all logging with structured key-value pairs:
```python
from doraemon import slogger

slogger.info("User action", user_id=123, action="login", ip_address="192.168.1.1")
slogger.error("Request failed", error=str(e), request_id=req_id)
```
Never use print statements or standard logging module in production code.

### Async Service Lifecycle
AsyncService instances must be properly closed to avoid resource leaks:
```python
async_service = create_async_service(...)
try:
    result = await async_service(...)
finally:
    await async_service.close()  # Always close after use
```

### Python Version Constraint
The project is locked to Python 3.9-3.10 (as specified in pyproject.toml: `">3.9,<3.11"`). Do not use features from Python 3.11+.

### Dependency Management
- Uses Poetry with Aliyun mirror as primary source (for Chinese users)
- All dependencies pinned in poetry.lock
- Optional dependencies: `aiohttp` (async), `PyYAML` (config files)
- Core dependencies: `structlog`, `openai`, `requests`, `dacite`, `pandas`

### Test Markers
Tests use markers for external dependencies:
```python
@pytest.mark.need_middlewares  # Marks tests requiring external services (Kafka, etc.)
```

### OpenTelemetry Integration
The logger module integrates with OpenTelemetry for distributed tracing. When modifying logger code, ensure OTel handlers remain functional.
