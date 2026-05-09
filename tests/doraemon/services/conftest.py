"""Shared fixtures for the services test suite.

These fixtures isolate the singleton ``ConnectionManager`` /
``AsyncConnectionManager`` and the registry/cache class state so tests don't
leak HTTP sessions or registered services across each other.
"""

from __future__ import annotations

import pytest

from doraemon.services import async_service, enhanced_service


@pytest.fixture(autouse=True)
def _reset_service_state():
    """Wipe singleton + registry state before and after every test."""
    enhanced_service.ServiceRegistry._services.clear()
    async_service.AsyncServiceRegistry._services.clear()

    # Reset sync ConnectionManager singleton
    cm = enhanced_service.ConnectionManager()
    for name in list(cm._sessions):
        cm.close_session(name)

    # Reset async manager (sessions are aiohttp objects but cleared in-place;
    # closing them properly requires a running loop, so just drop refs here).
    acm = async_service.AsyncConnectionManager()
    if hasattr(acm, "_sessions"):
        acm._sessions.clear()

    yield

    enhanced_service.ServiceRegistry._services.clear()
    async_service.AsyncServiceRegistry._services.clear()
    for name in list(cm._sessions):
        cm.close_session(name)
    if hasattr(acm, "_sessions"):
        acm._sessions.clear()
