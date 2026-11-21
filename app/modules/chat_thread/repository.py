from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat_thread.models import ChatThread


class ChatThreadRepository:
    """负责会话数据访问，事务由 Service 管理。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, thread: ChatThread) -> None:
        # 将对象加入当前 Session，Service 提交事务时写入数据库。
        self.session.add(thread)

    async def list_by_user(self, user_id: int) -> list[ChatThread]:
        # 只查询当前用户的会话，最近更新的会话排在前面。
        result = await self.session.scalars(
            select(ChatThread)
            .where(ChatThread.user_id == user_id)
            .order_by(ChatThread.updated_at.desc(), ChatThread.created_at.desc())
        )
        return list(result.all())

    async def find_owned(self, thread_id: UUID, user_id: int) -> ChatThread | None:
        # 在写事务中锁定会话，避免重命名和删除同时修改同一条记录。
        return await self.session.scalar(
            select(ChatThread)
            .where(ChatThread.id == thread_id, ChatThread.user_id == user_id)
            .with_for_update()
        )

    async def delete(self, thread: ChatThread) -> None:
        # 将对象标记为待删除，随当前事务一并提交。
        await self.session.delete(thread)
