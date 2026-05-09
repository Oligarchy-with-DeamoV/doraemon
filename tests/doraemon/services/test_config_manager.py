"""Tests for :class:`doraemon.services.ServiceConfigManager`."""

from __future__ import annotations

import json
from dataclasses import dataclass
from textwrap import dedent

import pytest

from doraemon.services import (
    EnhancedService,
    ServiceConfigManager,
    ServiceMonitor,
)


@dataclass
class _ProtoIn:
    q: str


@dataclass
class _ProtoOut:
    r: str


@pytest.fixture
def proto_module(monkeypatch):
    """Register the test protos under a stable importable name."""
    import sys
    import types

    mod = types.ModuleType("doraemon_test_protos")
    mod.ProtoIn = _ProtoIn
    mod.ProtoOut = _ProtoOut
    monkeypatch.setitem(sys.modules, "doraemon_test_protos", mod)
    yield "doraemon_test_protos"


def test_load_from_yaml(proto_module, tmp_path):
    cfg = tmp_path / "services.yaml"
    cfg.write_text(
        dedent(
            f"""\
            services:
              api_a:
                service_url: "https://api.example.com/a"
                service_method: "post"
                input_proto: "{proto_module}.ProtoIn"
                output_proto: "{proto_module}.ProtoOut"
                timeout: 12.0
            """
        ),
        encoding="utf-8",
    )

    services = ServiceConfigManager.load_from_yaml(str(cfg))
    assert "api_a" in services
    assert isinstance(services["api_a"], EnhancedService)
    assert services["api_a"].config.timeout == 12.0


def test_load_from_json(proto_module, tmp_path):
    cfg = tmp_path / "services.json"
    cfg.write_text(
        json.dumps(
            {
                "services": {
                    "api_b": {
                        "service_url": "https://api.example.com/b",
                        "service_method": "get",
                        "input_proto": f"{proto_module}.ProtoIn",
                        "output_proto": f"{proto_module}.ProtoOut",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    services = ServiceConfigManager.load_from_json(str(cfg))
    assert "api_b" in services
    assert services["api_b"].config.service_method == "get"


def test_service_monitor_record_and_summary():
    monitor = ServiceMonitor()
    monitor.record_request("svc", success=True, response_time=0.1)
    monitor.record_request("svc", success=False, response_time=0.5)

    summary = monitor.get_metrics("svc")
    assert summary["total_requests"] == 2
    assert summary["successful_requests"] == 1
    assert summary["failed_requests"] == 1
    assert "success_rate" in summary
    assert "avg_response_time" in summary


def test_service_monitor_unknown_service_returns_empty():
    monitor = ServiceMonitor()
    assert monitor.get_metrics("nope") == {}


def test_service_monitor_get_all_metrics():
    monitor = ServiceMonitor()
    monitor.record_request("a", True, 0.05)
    monitor.record_request("b", False, 0.10)
    all_metrics = monitor.get_all_metrics()
    assert set(all_metrics.keys()) == {"a", "b"}
