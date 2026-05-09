"""Tests for :class:`doraemon.services.BaseService`."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
import responses

from doraemon.services import BaseService


@dataclass
class _Input:
    query: str


@dataclass
class _Output:
    result: str


@pytest.fixture
def service() -> BaseService:
    return BaseService(
        name="test_base_service",
        service_url="https://api.example.com/echo",
        service_method="post",
        input_proto=_Input,
        output_proto=_Output,
    )


@responses.activate
def test_base_service_happy_path(service: BaseService):
    responses.post(
        "https://api.example.com/echo",
        json={"result": "pong"},
        status=200,
    )

    out = service(timeout=5.0, json={"query": "ping"})

    assert isinstance(out, _Output)
    assert out.result == "pong"


@responses.activate
def test_base_service_returns_none_on_non_200(service: BaseService):
    responses.post("https://api.example.com/echo", status=500)

    out = service(timeout=5.0, json={"query": "ping"})

    assert out is None


@responses.activate
def test_base_service_returns_none_on_invalid_input(service: BaseService):
    # Missing the required "query" field — proto validation must reject it.
    out = service(timeout=5.0, json={"unknown": "x"})

    assert out is None
    # No request should have been sent.
    assert len(responses.calls) == 0


@responses.activate
def test_base_service_returns_none_on_invalid_output(service: BaseService):
    responses.post(
        "https://api.example.com/echo",
        json={"unexpected": "shape"},
        status=200,
    )

    out = service(timeout=5.0, json={"query": "ping"})

    assert out is None
