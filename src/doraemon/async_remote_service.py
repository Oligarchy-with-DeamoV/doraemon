"""Compatibility shim for ``doraemon.async_remote_service``.

This module is **deprecated**. Import from :mod:`doraemon.services` instead::

    from doraemon.services import AsyncService, create_async_service

Imports from this module continue to work but emit a
:class:`DeprecationWarning`.
"""

from __future__ import annotations

import warnings

from doraemon.services.async_service import (
    AsyncConnectionManager,
    AsyncService,
    AsyncServiceConfig,
    AsyncServiceRegistry,
    async_service_call,
    create_async_service,
    get_async_service,
)

warnings.warn(
    "doraemon.async_remote_service is deprecated; "
    "import from doraemon.services instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "AsyncConnectionManager",
    "AsyncService",
    "AsyncServiceConfig",
    "AsyncServiceRegistry",
    "async_service_call",
    "create_async_service",
    "get_async_service",
]
