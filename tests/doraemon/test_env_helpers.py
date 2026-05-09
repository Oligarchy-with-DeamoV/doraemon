"""Tests for env-var helpers in scripts that previously had hardcoded secrets.

These exercise the security regression: missing env vars must raise a clear
:class:`RuntimeError` rather than silently picking up defaults.
"""

from __future__ import annotations

import pytest

from doraemon.database_utils.main import (
    _require_env as _require_db_env,
)
from doraemon.database_utils.main import (
    load_api_config,
    load_db_config,
)
from doraemon.gpt_utils.chatgpt_api import (
    _require_env as _require_gpt_env,
)
from doraemon.gpt_utils.chatgpt_api import (
    request_openai,
)


def test_db_require_env_raises_when_missing(monkeypatch):
    monkeypatch.delenv("ABSOLUTELY_NOT_SET_VAR", raising=False)
    with pytest.raises(RuntimeError, match="ABSOLUTELY_NOT_SET_VAR"):
        _require_db_env("ABSOLUTELY_NOT_SET_VAR")


def test_gpt_require_env_raises_when_missing(monkeypatch):
    monkeypatch.delenv("ABSOLUTELY_NOT_SET_VAR", raising=False)
    with pytest.raises(RuntimeError, match="ABSOLUTELY_NOT_SET_VAR"):
        _require_gpt_env("ABSOLUTELY_NOT_SET_VAR")


def test_load_db_config_reads_env(monkeypatch):
    monkeypatch.setenv("DORAEMON_DB_NAME", "name")
    monkeypatch.setenv("DORAEMON_DB_USER", "user")
    monkeypatch.setenv("DORAEMON_DB_PASSWORD", "pw")
    monkeypatch.setenv("DORAEMON_DB_HOST", "host")
    monkeypatch.setenv("DORAEMON_DB_PORT", "5433")

    cfg = load_db_config()

    assert cfg.dbname == "name"
    assert cfg.user == "user"
    assert cfg.password == "pw"
    assert cfg.host == "host"
    assert cfg.port == 5433
    assert cfg.as_kwargs()["host"] == "host"


def test_load_api_config_reads_env(monkeypatch):
    monkeypatch.setenv("DORAEMON_EMBEDDING_API_ENDPOINT", "https://api.example.com")
    monkeypatch.setenv("DORAEMON_EMBEDDING_API_TOKEN", "tok")

    cfg = load_api_config()

    assert cfg.endpoint == "https://api.example.com"
    assert cfg.token == "tok"
    assert cfg.request_headers()["Authorization"] == "Bearer tok"


def test_request_openai_raises_with_missing_env(monkeypatch):
    """Without ``OPENAI_*`` env, the helper must surface a RuntimeError."""
    for var in (
        "GPT_TEMPERATURE",
        "OPENAI_API_BASE",
        "OPENAI_API_VERSION",
        "OPENAI_API_KEY",
        "OPENAI_DEPLOYMENT_NAME",
        "OPENAI_API_TYPE",
        "OPENAI_MODEL_NAME",
    ):
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(RuntimeError):
        request_openai([{"role": "user", "content": "hi"}])
