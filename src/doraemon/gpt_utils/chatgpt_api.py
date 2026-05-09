"""Lightweight OpenAI / Azure OpenAI request helper."""

from __future__ import annotations

import os
from typing import Any

from openai import AzureOpenAI, OpenAI


def _require_env(name: str) -> str:
    """Return the value of ``name`` or raise :class:`RuntimeError`."""
    value = os.environ.get(name)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def request_openai(
    messages: list[dict],
    params: dict | None = None,
) -> tuple[bool, str]:
    """Call OpenAI / Azure OpenAI with the configured environment.

    Required environment variables:

    - ``GPT_TEMPERATURE``
    - ``OPENAI_API_BASE``
    - ``OPENAI_API_VERSION``
    - ``OPENAI_API_TYPE`` (must be ``"azure"`` or ``"local"``)
    - ``OPENAI_DEPLOYMENT_NAME``
    - ``OPENAI_API_KEY``
    - ``OPENAI_MODEL_NAME``
    """
    if params is None:
        params = {}

    temperature = float(_require_env("GPT_TEMPERATURE"))
    api_base = _require_env("OPENAI_API_BASE")
    api_version = _require_env("OPENAI_API_VERSION")
    api_key = _require_env("OPENAI_API_KEY")
    deployment_name = _require_env("OPENAI_DEPLOYMENT_NAME")
    api_type = _require_env("OPENAI_API_TYPE")
    model_name = _require_env("OPENAI_MODEL_NAME")

    try:
        client: OpenAI | AzureOpenAI
        if api_type == "azure":
            client = AzureOpenAI(
                azure_endpoint=api_base,
                azure_deployment=deployment_name,
                api_key=api_key,
                api_version=api_version,
                max_retries=2,
                timeout=120,
            )
        elif api_type == "local":
            client = OpenAI(
                base_url=api_base,
                api_key=api_key,
                max_retries=2,
                timeout=120,
            )
        else:
            raise ValueError(f"{api_type} is not local or azure")

        response = client.chat.completions.create(
            model=model_name,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            **params,
        )
        gpt_answer = response.choices[0].message.content
        return True, str(gpt_answer)
    except RuntimeError as e:
        return False, str(e)


def _example_main() -> None:
    """Manual smoke entry point — runs only when invoked as a script."""
    sample: list[dict[str, Any]] = [{"role": "user", "content": "你好"}]
    print(request_openai(sample))
    sample = [{"role": "user", "content": "讲100个子的故事"}]
    print(request_openai(sample, params={"max_tokens": 10}))


if __name__ == "__main__":
    _example_main()
