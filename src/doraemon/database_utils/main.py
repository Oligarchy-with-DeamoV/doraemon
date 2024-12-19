import asyncio
import aiohttp
import psycopg2
from psycopg2.extras import execute_values

API_ENDPOINT = "http://10.170.138.230:9981/get_question_sentence_embedding"  # 替换为实际的 API 端点
DATABASE_CONFIG = {
    "dbname": "python_localtest_db",
    "user": "postgres",
    "password": "zgt#1024",
    "host": "10.170.138.230",
    "port": 5432,
}
TABLE_NAME = "documents"
BATCH_SIZE = 100
VECTOR_DIMENSION = 384
REQUEST_HEADERS = {
    "Authorization": "Bearer YOUR_API_TOKEN",
    "Content-Type": "application/json",
}
CONCURRENT_REQUESTS = 10  # 根据 API 限制调整


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


def create_table_if_not_exists(conn):
    """
    如果表不存在，则创建表。表结构包含一个文本列和一个 pgvector 列。
    """
    with conn.cursor() as cur:
        for q in create_table_list:
            cur.execute(q)
    conn.commit()
    print(f"检查并确保表已存在")


async def fetch_vector(session, text):
    params = {"sender_id": "local_test", "text": "你好", "version": "v1"}
    try:
        async with session.get(
            API_ENDPOINT, params=params, headers=REQUEST_HEADERS
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


async def batch_fetch_vectors(texts):
    connector = aiohttp.TCPConnector(limit=CONCURRENT_REQUESTS)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_vector(session, text) for text in texts]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]


def insert_vectors(conn, table_name, columns, data):
    with conn.cursor() as cur:
        sql = f"INSERT INTO {table_name} {columns} VALUES %s"
        execute_values(cur, sql, data, template=None, page_size=BATCH_SIZE)
    conn.commit()


async def main_async(data_items):
    # 连接到 PostgreSQL 数据库
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
    except psycopg2.Error as e:
        print(f"错误: 无法连接到数据库, 错误信息: {e}")
        return

    try:
        # 检查并创建表（如果不存在）
        create_table_if_not_exists(conn)

        total = len(data_items)
        for i in range(0, total, BATCH_SIZE):
            batch_texts = data_items[i : i + BATCH_SIZE]
            print(f"处理第 {i+1} 到 {i+len(batch_texts)} 条记录")
            batch_vectors = await batch_fetch_vectors(batch_texts)
            print(batch_vectors)
            if batch_vectors:
                columns = ()
                table_name = 'similar_question'
                insert_vectors(conn, batch_vectors)
        #         print(f"成功插入 {len(batch_vectors)} 条记录")
        #     else:
        #         print("本批次没有有效的向量数据插入")
    finally:
        conn.close()
        print("数据库连接已关闭")


def main():
    data_items = [
        "文本1",
        "文本2",
        "文本3",
        # 添加更多文本
    ]
    asyncio.run(main_async(data_items))


if __name__ == "__main__":
    main()
