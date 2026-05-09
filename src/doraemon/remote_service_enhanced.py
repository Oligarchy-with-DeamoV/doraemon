"""Compatibility shim for ``doraemon.remote_service_enhanced``.

This module is **deprecated**. Import from :mod:`doraemon.services` instead::

    from doraemon.services import EnhancedService, create_service

Imports from this module continue to work but emit a
:class:`DeprecationWarning`.
"""

from __future__ import annotations

import warnings

from doraemon.services.enhanced_service import (
    ConnectionManager,
    EnhancedService,
    ResponseCache,
    ServiceConfig,
    ServiceRegistry,
    create_service,
    get_service,
    service_call,
)

warnings.warn(
    "doraemon.remote_service_enhanced is deprecated; "
    "import from doraemon.services instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "ConnectionManager",
    "EnhancedService",
    "ResponseCache",
    "ServiceConfig",
    "ServiceRegistry",
    "create_service",
    "get_service",
    "service_call",
]
