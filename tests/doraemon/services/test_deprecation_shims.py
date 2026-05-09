"""Tests for the deprecated module shims and back-compat aliases."""

from __future__ import annotations

import warnings


def test_remote_service_shim_emits_deprecation_warning():
    # Force import every time so the warning fires reliably.
    import importlib
    import sys

    sys.modules.pop("doraemon.remote_service", None)

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        module = importlib.import_module("doraemon.remote_service")

    assert any(
        issubclass(w.category, DeprecationWarning)
        and "doraemon.remote_service" in str(w.message)
        for w in captured
    )
    assert hasattr(module, "BaseService")


def test_remote_service_enhanced_shim_exports_factory():
    import importlib
    import sys

    sys.modules.pop("doraemon.remote_service_enhanced", None)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        module = importlib.import_module("doraemon.remote_service_enhanced")

    assert any(issubclass(w.category, DeprecationWarning) for w in captured)
    for name in ("EnhancedService", "create_service", "ServiceConfig"):
        assert hasattr(module, name)


def test_async_remote_service_shim_exports_async_factory():
    import importlib
    import sys

    sys.modules.pop("doraemon.async_remote_service", None)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        module = importlib.import_module("doraemon.async_remote_service")

    assert any(issubclass(w.category, DeprecationWarning) for w in captured)
    for name in ("AsyncService", "create_async_service", "AsyncServiceConfig"):
        assert hasattr(module, name)


def test_top_level_remote_service_alias():
    """``doraemon.RemoteService`` must alias :class:`BaseService`."""
    from doraemon import BaseService, RemoteService

    assert RemoteService is BaseService


def test_doraemon_version_attribute():
    """``doraemon.__version__`` should be a non-empty string."""
    import doraemon

    assert isinstance(doraemon.__version__, str)
    assert doraemon.__version__
