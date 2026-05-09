"""Compatibility shim for ``doraemon.remote_service``.

This module is **deprecated**. Import from :mod:`doraemon.services` instead::

    from doraemon.services import BaseService

Imports from this module continue to work but emit a
:class:`DeprecationWarning`.
"""

from __future__ import annotations

import warnings

from doraemon.services.base_service import BaseService

warnings.warn(
    "doraemon.remote_service is deprecated; import from doraemon.services instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["BaseService"]
