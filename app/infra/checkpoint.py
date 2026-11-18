from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from langgraph.checkpoint.base import CheckpointTuple
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from starlette.concurrency import run_in_threadpool

from app.core.config import settings


@asynccontextmanager
async def open_checkpointer() -> AsyncIterator[PostgresSaver]:
    """在应用生命周期内管理检查点连接池。"""
    db = settings.db
    # 同步 Psycopg 连接在线程池执行，兼容 Windows 上的 Uvicorn 事件循环。
    pool = ConnectionPool(
        kwargs={
            "host": db.host,
            "port": db.port,
            "dbname": db.name,
            "user": db.user,
            "password": db.password,
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
        min_size=1,
        open=False,
    )
    try:
        pool.open()
        checkpointer = PostgresSaver(
            pool, serde=JsonPlusSerializer(allowed_msgpack_modules=None)
        )
        await run_in_threadpool(checkpointer.setup)
        yield checkpointer
    finally:
        await run_in_threadpool(pool.close)


async def load_thread_checkpoint(
    checkpointer: PostgresSaver, thread_id: UUID
) -> CheckpointTuple | None:
    # 不指定 checkpoint_id 时，读取该会话根命名空间中最新的检查点。
    return await run_in_threadpool(
        checkpointer.get_tuple,
        {"configurable": {"thread_id": str(thread_id), "checkpoint_ns": ""}},
    )
