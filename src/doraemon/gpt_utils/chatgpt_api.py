import os
from typing import Dict, List

from openai import AzureOpenAI, OpenAI


def request_openai(messages: List[Dict], params: Dict = {}):
    TEMPERATURE = os.getenv("GPT_TEMPERATURE")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
    OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME")
    OPENAI_API_TYPE = os.getenv("OPENAI_API_TYPE")
    OPENAI_API_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")
    assert all(
        x is not None
        for x in [
            TEMPERATURE,
            OPENAI_API_BASE,
            OPENAI_API_VERSION,
            OPENAI_API_TYPE,
            DEPLOYMENT_NAME,
            OPENAI_API_KEY,
            OPENAI_API_MODEL_NAME,
        ]
    )
    try:
        if OPENAI_API_TYPE == "azure":
            client = AzureOpenAI(
                azure_endpoint=OPENAI_API_BASE,  # pyright: ignore
                azure_deployment=DEPLOYMENT_NAME,
                api_key=OPENAI_API_KEY,
                api_version=OPENAI_API_VERSION,
                max_retries=2,
                timeout=120,
            )
            response = client.chat.completions.create(
                model=OPENAI_API_MODEL_NAME,  # pyright: ignore
                messages=messages,  # pyright: ignore
                temperature=float(TEMPERATURE) if TEMPERATURE is not None else 0.9,
                **params,
            )

        elif OPENAI_API_TYPE == "local":
            client = OpenAI(
                base_url=OPENAI_API_BASE,
                api_key=OPENAI_API_KEY,
                max_retries=2,
                timeout=120,
            )
            response = client.chat.completions.create(
                model=OPENAI_API_MODEL_NAME,  # pyright: ignore
                messages=messages,  # pyright: ignore
                temperature=float(TEMPERATURE) if TEMPERATURE is not None else 0.9,
                **params,
            )
        else:
            raise ValueError(f"{OPENAI_API_TYPE} is not local or azure")
        gpt_answer = response.choices[0].message.content
        return True, str(gpt_answer)
    except RuntimeError as e:
        return False, str(e)


if __name__ == "__main__":
    mmessages = [{"role": "user", "content": "你好"}]
    print(request_openai(mmessages))
    mmessages = [{"role": "user", "content": "讲100个子的故事"}]
    print(request_openai(mmessages, params={"max_tokens": 10}))
