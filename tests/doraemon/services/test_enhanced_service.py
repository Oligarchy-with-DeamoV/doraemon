"""Tests for :class:`doraemon.services.EnhancedService`."""

from __future__ import annotations

import time
import warnings
from dataclasses import dataclass

import pytest
import responses

from doraemon.services import (
    EnhancedService,
    ResponseCache,
    ServiceConfig,
    ServiceRegistry,
    create_service,
    get_service,
)


@dataclass
class _Input:
    query: str


@dataclass
class _Output:
    result: str


@pytest.fixture
def service() -> EnhancedService:
    return create_service(
        name="enhanced_test_service",
        service_url="https://api.example.com/echo",
        service_method="post",
        input_proto=_Input,
        output_proto=_Output,
        timeout=5.0,
        max_retries=0,
    )


# ---------------- happy path & error paths ----------------


@responses.activate
def test_enhanced_service_happy_path(service: EnhancedService):
    responses.post(
        "https://api.example.com/echo",
        json={"result": "pong"},
        status=200,
    )

    out = service(json_data={"query": "ping"})

    assert isinstance(out, _Output)
    assert out.result == "pong"


@responses.activate
def test_enhanced_service_returns_none_on_non_200(service: EnhancedService):
    responses.post("https://api.example.com/echo", status=503)
    assert service(json_data={"query": "ping"}) is None


@responses.activate
def test_enhanced_service_returns_none_on_invalid_input(service: EnhancedService):
    out = service(json_data={"unknown": "x"})
    assert out is None
    assert len(responses.calls) == 0


@responses.activate
def test_enhanced_service_returns_none_on_invalid_output(service: EnhancedService):
    responses.post(
        "https://api.example.com/echo",
        json={"oops": "wrong"},
        status=200,
    )
    assert service(json_data={"query": "ping"}) is None


@responses.activate
def test_enhanced_service_returns_none_on_unparseable_json(
    service: EnhancedService,
):
    responses.post(
        "https://api.example.com/echo",
        body="not json",
        status=200,
    )
    assert service(json_data={"query": "ping"}) is None


# ---------------- back-compat: json= alias ----------------


@responses.activate
def test_json_alias_emits_deprecation_warning(service: EnhancedService):
    responses.post(
        "https://api.example.com/echo",
        json={"result": "ok"},
        status=200,
    )
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        out = service(json={"query": "legacy"})

    assert isinstance(out, _Output)
    assert any(
        issubclass(w.category, DeprecationWarning) and "json=" in str(w.message)
        for w in captured
    )


def test_json_and_json_data_together_raises(service: EnhancedService):
    with pytest.raises(TypeError, match="not both"):
        service(json={"query": "a"}, json_data={"query": "b"})


# ---------------- caching ----------------


@responses.activate
def test_use_cache_returns_cached_result(service: EnhancedService):
    responses.post(
        "https://api.example.com/echo",
        json={"result": "cached"},
        status=200,
    )

    first = service(json_data={"query": "ping"}, use_cache=True)
    second = service(json_data={"query": "ping"}, use_cache=True)

    assert first.result == "cached"
    assert second.result == "cached"
    # Only one HTTP call was actually issued.
    assert len(responses.calls) == 1


def test_response_cache_expires_after_ttl():
    cache = ResponseCache(ttl=1)
    cache.set("k", "v")

    assert cache.get("k") == "v"

    # Expire by manipulating the timestamp directly.
    cache._timestamps["k"] -= 5
    assert cache.get("k") is None


def test_response_cache_clear():
    cache = ResponseCache(ttl=300)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None


# ---------------- circuit breaker ----------------


@responses.activate
def test_circuit_breaker_opens_after_threshold(service: EnhancedService):
    """Five consecutive failures should open the circuit and skip the call."""
    responses.post("https://api.example.com/echo", status=500)

    for _ in range(5):
        assert service(json_data={"query": "x"}) is None

    # Now circuit is open. Add a passing route — but it should not fire because
    # circuit-breaker short-circuits first.
    responses.replace(
        responses.POST,
        "https://api.example.com/echo",
        json={"result": "ok"},
        status=200,
    )

    out = service(json_data={"query": "x"})
    assert out is None


def test_circuit_breaker_resets_after_timeout(service: EnhancedService):
    service._circuit_breaker_failures = 5
    service._circuit_breaker_last_failure = time.time() - 9999  # long ago
    assert service._is_circuit_breaker_open() is False


# ---------------- registry & factory ----------------


def test_service_registry_register_and_get():
    config = ServiceConfig(
        name="registry_test",
        service_url="https://api.example.com/x",
        service_method="get",
        input_proto=_Input,
        output_proto=_Output,
    )
    s1 = ServiceRegistry.register(config)
    assert get_service("registry_test") is s1
    assert "registry_test" in ServiceRegistry.list_services()


def test_service_registry_get_unknown_returns_none():
    assert get_service("does_not_exist") is None


def test_create_service_registers_in_registry():
    create_service(
        name="factory_registered",
        service_url="https://api.example.com/y",
        service_method="get",
        input_proto=_Input,
        output_proto=_Output,
    )
    assert get_service("factory_registered") is not None


# ---------------- cache key stability (security regression) ----------------


def test_md5_cache_key_is_deterministic_and_marked_non_security(
    service: EnhancedService,
):
    """Regression: usedforsecurity=False kwarg must not change behavior."""
    a = service._generate_cache_key(json_data={"query": "x"})
    b = service._generate_cache_key(json_data={"query": "x"})
    assert a == b
    assert a != service._generate_cache_key(json_data={"query": "y"})
