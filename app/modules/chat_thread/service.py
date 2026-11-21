from uuid import UUID

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat_thread.exceptions import ChatThreadNotFoundError
from app.modules.chat_thread.models import ChatThread
from app.modules.chat_thread.repository import ChatThreadRepository
from .schemas import ChatMessageResponse, ChatHistoryResponse


class ChatThreadService:
    """管理会话业务流程和写入事务。"""

    def __init__(self, session: AsyncSession, agent: CompiledStateGraph):
        self.session = session
        self.repository = ChatThreadRepository(session)
        self.agent = agent

    async def add(self, user_id: int, title: str) -> ChatThread:
        # 写事务正常退出时自动提交，出现异常时自动回滚。
        async with self.session.begin():
            thread = ChatThread(user_id=user_id, title=title)
            self.repository.add(thread)
        return thread

    async def list_by_user(self, user_id: int) -> list[ChatThread]:
        return await self.repository.list_by_user(user_id)

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
            # 1. 删除会话的所有快照
            await self.agent.checkpointer.adelete_thread(thread_id)
            # 2. 删除会话
            await self.repository.delete(thread)

    async def _require_owned(self, thread_id: UUID, user_id: int) -> ChatThread:
        # 按会话 ID 和用户 ID 一起查询，找不到时交给全局异常处理器响应。
        thread = await self.repository.find_owned(thread_id, user_id)
        if thread is None:
            raise ChatThreadNotFoundError
        return thread

    async def get_chat_history(self, user_id: int, thread_id: UUID):
        # 1. 校验当前对话是否属于当前用户
        thread = await self.repository.find_owned(thread_id, user_id)
        if thread is None:
            raise ChatThreadNotFoundError
        # 2. 查询会话历史
        config = {"configurable": {"thread_id": thread_id}}
        state_snapshot = await self.agent.aget_state(config)
        # 3. 封装历史消息
        messages = []
        for message in state_snapshot.values.get('messages', []):
            # 判断类型，决定role
            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            else:
                continue
            if message.content:
                messages.append(ChatMessageResponse(role=role, content=message.text))

        return ChatHistoryResponse(
            thread_id=thread_id,
            messages=messages
        )