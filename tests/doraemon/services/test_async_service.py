"""Tests for :class:`doraemon.services.AsyncService`."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from aioresponses import aioresponses

from doraemon.services import (
    AsyncConnectionManager,
    create_async_service,
)


@dataclass
class _Input:
    query: str


@dataclass
class _Output:
    result: str


@pytest.fixture
def async_service():
    return create_async_service(
        name="async_test",
        service_url="https://api.example.com/echo",
        service_method="post",
        input_proto=_Input,
        output_proto=_Output,
        timeout=5.0,
    )


def test_async_connection_manager_is_singleton():
    a = AsyncConnectionManager()
    b = AsyncConnectionManager()
    assert a is b
    assert hasattr(a, "_sessions")


@pytest.mark.asyncio
async def test_async_service_happy_path(async_service):
    with aioresponses() as m:
        m.post(
            "https://api.example.com/echo",
            payload={"result": "pong"},
            status=200,
        )
        out = await async_service(json_data={"query": "ping"})

    assert isinstance(out, _Output)
    assert out.result == "pong"
    await async_service.close()


@pytest.mark.asyncio
async def test_async_service_returns_none_on_non_200(async_service):
    with aioresponses() as m:
        m.post("https://api.example.com/echo", status=502)
        assert await async_service(json_data={"query": "ping"}) is None
    await async_service.close()


@pytest.mark.asyncio
async def test_async_service_returns_none_on_invalid_input(async_service):
    out = await async_service(json_data={"unknown": "x"})
    assert out is None
    await async_service.close()


@pytest.mark.asyncio
async def test_async_service_batch_call(async_service):
    with aioresponses() as m:
        for _ in range(3):
            m.post(
                "https://api.example.com/echo",
                payload={"result": "ok"},
                status=200,
            )
        results = await async_service.batch_call(
            [{"json_data": {"query": "a"}} for _ in range(3)],
            max_concurrent=2,
        )

    assert len(results) == 3
    assert all(isinstance(r, _Output) for r in results)
    await async_service.close()
