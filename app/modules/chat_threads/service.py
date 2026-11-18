from uuid import UUID

from langgraph.checkpoint.postgres import PostgresSaver
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.checkpoint import load_thread_checkpoint
from app.modules.chat_threads.exceptions import (
    ChatHistoryNotFoundError,
    ChatThreadNotFoundError,
)
from app.modules.chat_threads.history import build_chat_history
from app.modules.chat_threads.models import ChatThread
from app.modules.chat_threads.repository import ChatThreadRepository
from app.modules.chat_threads.schemas import ChatHistoryResponse


class ChatThreadService:
    """管理会话业务流程和写入事务。"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ChatThreadRepository(session)

    async def add(self, user_id: int, title: str) -> ChatThread:
        # 写事务正常退出时自动提交，出现异常时自动回滚。
        async with self.session.begin():
            thread = ChatThread(user_id=user_id, title=title)
            self.repository.add(thread)
        return thread

    async def list_by_user(self, user_id: int) -> list[ChatThread]:
        return await self.repository.list_by_user(user_id)

    async def get_history(
        self, thread_id: UUID, user_id: int, checkpointer: PostgresSaver
    ) -> ChatHistoryResponse:
        # 先核对元数据中的会话归属，再按会话 ID 读取消息检查点。
        if await self.repository.find_owned(thread_id, user_id) is None:
            raise ChatHistoryNotFoundError
        checkpoint = await load_thread_checkpoint(checkpointer, thread_id)
        return build_chat_history(thread_id, checkpoint)

    async def rename(self, thread_id: UUID, user_id: int, title: str) -> ChatThread:
        async with self.session.begin():
            thread = await self._require_owned(thread_id, user_id)
            thread.title = title
            # 先执行更新，再读取最新的 updated_at，避免序列化时触发异步查询。
            await self.session.flush()
            await self.session.refresh(thread)
        return thread

    async def delete(self, thread_id: UUID, user_id: int) -> None:
        async with self.session.begin():
            thread = await self._require_owned(thread_id, user_id)
            # 本模块管理的是 chat_threads 表中的会话元数据。
            await self.repository.delete(thread)

    async def _require_owned(self, thread_id: UUID, user_id: int) -> ChatThread:
        # 按会话 ID 和用户 ID 一起查询，找不到时交给全局异常处理器响应。
        thread = await self.repository.find_owned(thread_id, user_id, for_update=True)
        if thread is None:
            raise ChatThreadNotFoundError
        return thread
