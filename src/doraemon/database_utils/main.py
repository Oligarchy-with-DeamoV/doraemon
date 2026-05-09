"""Async batch vector ingestion script.

Loads PostgreSQL/API config from environment variables and inserts
question-embedding vectors into a pgvector-backed table.

Configuration (all required when running as a script):

- ``DORAEMON_DB_HOST`` / ``DORAEMON_DB_PORT`` / ``DORAEMON_DB_NAME``
  / ``DORAEMON_DB_USER`` / ``DORAEMON_DB_PASSWORD``
- ``DORAEMON_EMBEDDING_API_ENDPOINT``
- ``DORAEMON_EMBEDDING_API_TOKEN``

.. warning::

   Earlier revisions of this file shipped a hardcoded PostgreSQL password
   and an internal IP address. See ``SECURITY.md`` — anyone who cloned the
   repository before this fix may still have the leaked credential and the
   real password should be rotated externally.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any

import aiohttp
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

BATCH_SIZE = 100
VECTOR_DIMENSION = 384
CONCURRENT_REQUESTS = 10


KNOWLEDGE_QUESION_QUERY = """
create table if not exists knowledge_question (
    id int4 primary key,
    name varchar(500) not null,
    source varchar(10) not null,
    associate_doc_id int4,
    answer varchar not null,
    status varchar(20) not null,
    valid_time timestamp(6) not null,
    classify_id int4,
    insert_time timestamp(6) not null,
    insert_user varchar not null,
    update_time timestamp(6) not null,
    update_user varchar not null
);
"""

QUESTION_CLASSIFY_QUERY = """
create table if not exists question_classify(
    id int4 primary key,
    classify_name varchar not null,
    parent_id int4,
    insert_time timestamp(6) not null,
    insert_user varchar not null,
    update_time timestamp(6) not null,
    update_user varchar not null
);
"""

SIMILAR_QUESTION_QUERY = """
create table if not exists similar_question (
    id int4 primary key,
    standard_question_id int4 not null,
    question_name varchar not null,
    question_vector vector(384),
    insert_time timestamp(6) not null,
    insert_user varchar not null,
    update_time timestamp(6) not null,
    update_user varchar not null
);
"""

create_table_list = [
    SIMILAR_QUESTION_QUERY,
    QUESTION_CLASSIFY_QUERY,
    KNOWLEDGE_QUESION_QUERY,
]


@dataclass(frozen=True)
class DBConfig:
    """PostgreSQL connection settings, loaded from the environment."""

    dbname: str
    user: str
    password: str
    host: str
    port: int = 5432

    def as_kwargs(self) -> dict[str, Any]:
        return {
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password,
            "host": self.host,
            "port": self.port,
        }


@dataclass(frozen=True)
class APIConfig:
    """Embedding-API connection settings, loaded from the environment."""

    endpoint: str
    token: str

    def request_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "See module docstring for the full list."
        )
    return value


def load_db_config() -> DBConfig:
    """Build a :class:`DBConfig` from environment variables."""
    return DBConfig(
        dbname=_require_env("DORAEMON_DB_NAME"),
        user=_require_env("DORAEMON_DB_USER"),
        password=_require_env("DORAEMON_DB_PASSWORD"),
        host=_require_env("DORAEMON_DB_HOST"),
        port=int(os.environ.get("DORAEMON_DB_PORT", "5432")),
    )


def load_api_config() -> APIConfig:
    """Build an :class:`APIConfig` from environment variables."""
    return APIConfig(
        endpoint=_require_env("DORAEMON_EMBEDDING_API_ENDPOINT"),
        token=_require_env("DORAEMON_EMBEDDING_API_TOKEN"),
    )


def create_table_if_not_exists(conn: Any) -> None:
    """如果表不存在，则创建表。表结构包含一个文本列和一个 pgvector 列。"""
    with conn.cursor() as cur:
        for q in create_table_list:
            cur.execute(q)
    conn.commit()
    print("检查并确保表已存在")


async def fetch_vector(
    session: aiohttp.ClientSession,
    text: str,
    api: APIConfig,
) -> tuple[str, list[float]] | None:
    params = {"sender_id": "local_test", "text": text, "version": "v1"}
    try:
        async with session.get(
            api.endpoint, params=params, headers=api.request_headers()
        ) as response:
            if response.status == 200:
                data = await response.json()
                vector = data.get("text_embedding")
                if vector and len(vector) == VECTOR_DIMENSION:
                    return (text, vector)
                else:
                    print(f"警告: 向量维度不匹配或为空 for text: {text}")
                    return None
            else:
                print(f"错误: API 请求失败 for text: {text}, 状态码 {response.status}")
                return None
    except Exception as e:
        print(f"错误: 请求异常 for text: {text}, 错误信息: {e}")
        return None


async def batch_fetch_vectors(
    texts: list[str], api: APIConfig
) -> list[tuple[str, list[float]]]:
    connector = aiohttp.TCPConnector(limit=CONCURRENT_REQUESTS)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_vector(session, text, api) for text in texts]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]


def insert_vectors(
    conn: Any,
    table_name: str,
    columns: list[str],
    data: list[tuple[Any, ...]],
) -> None:
    """Bulk-insert ``data`` into ``table_name``.

    ``table_name`` and ``columns`` are quoted via :mod:`psycopg2.sql` to
    prevent SQL injection — never interpolate identifiers with f-strings.
    """
    if not columns:
        raise ValueError("`columns` must contain at least one column name")

    with conn.cursor() as cur:
        query = sql.SQL("INSERT INTO {table} ({columns}) VALUES %s").format(
            table=sql.Identifier(table_name),
            columns=sql.SQL(", ").join(sql.Identifier(c) for c in columns),
        )
        execute_values(cur, query, data, template=None, page_size=BATCH_SIZE)
    conn.commit()


async def main_async(data_items: list[str]) -> None:
    db_config = load_db_config()
    api_config = load_api_config()

    try:
        conn = psycopg2.connect(**db_config.as_kwargs())
    except psycopg2.Error as e:
        print(f"错误: 无法连接到数据库, 错误信息: {e}")
        return

    try:
        create_table_if_not_exists(conn)

        total = len(data_items)
        for i in range(0, total, BATCH_SIZE):
            batch_texts = data_items[i : i + BATCH_SIZE]
            print(f"处理第 {i + 1} 到 {i + len(batch_texts)} 条记录")
            batch_vectors = await batch_fetch_vectors(batch_texts, api_config)
            print(batch_vectors)
            if batch_vectors:
                # The legacy script lacks the additional NOT NULL columns
                # required by `similar_question` (id / standard_question_id /
                # timestamps / users). Refusing to silently insert partial
                # rows. Callers should construct full row tuples and call
                # `insert_vectors` directly.
                raise NotImplementedError(
                    "Schema-aware insertion is not implemented; "
                    "construct full rows and call insert_vectors() directly."
                )
    finally:
        conn.close()
        print("数据库连接已关闭")


def main() -> None:
    data_items = [
        "文本1",
        "文本2",
        "文本3",
    ]
    asyncio.run(main_async(data_items))


if __name__ == "__main__":
    main()
