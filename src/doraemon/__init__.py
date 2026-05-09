"""
Doraemon - Python 开发工具箱

包含以下模块:
- logger: 结构化日志记录工具
- services: 企业级远程服务调用框架
- file_utils: 文件操作工具
- database_utils: 数据库工具
- gpt_utils: GPT API 工具
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .file_utils import *
from .logger import slogger
from .services import BaseService, create_async_service, create_service

# 保持向后兼容
from .services.base_service import BaseService as RemoteService

try:
    __version__ = version("doraemon")
except PackageNotFoundError:  # pragma: no cover - editable install w/o metadata
    __version__ = "0.0.0+unknown"

__all__ = [
    "slogger",
    "BaseService",
    "RemoteService",
    "create_service",
    "create_async_service",
    "__version__",
]
