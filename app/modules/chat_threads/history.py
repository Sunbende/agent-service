from typing import Any
from uuid import UUID

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.base import CheckpointTuple, PendingWrite
from langgraph.graph.message import add_messages
from langgraph.pregel._task_status import read_task_statuses

from app.modules.chat_threads.schemas import ChatHistoryMessage, ChatHistoryResponse


def build_chat_history(
    thread_id: UUID, checkpoint: CheckpointTuple | None
) -> ChatHistoryResponse:
    """将检查点中的会话状态转换为前端历史消息。"""
    if checkpoint is None:
        return ChatHistoryResponse(thread_id=thread_id, messages=[], interrupt=None)

    saved_messages = checkpoint.checkpoint["channel_values"].get("messages", [])
    pending_writes = checkpoint.pending_writes or []
    # 暂停时，本轮已写入但尚未合并到快照的消息也应出现在历史里。
    for _, channel, value in pending_writes:
        if channel == "messages":
            saved_messages = add_messages(saved_messages, value)

    messages: list[ChatHistoryMessage] = []
    for message in saved_messages:
        if isinstance(message, HumanMessage):
            messages.append(ChatHistoryMessage(role="user", content=message.text))
        elif isinstance(message, AIMessage):
            # 只读取可展示的正文和显式保存的附加信息，跳过仅含工具调用的回复。
            content = message.text
            additional_info = message.additional_kwargs.get("additional_info")
            if content.strip() or additional_info is not None:
                messages.append(
                    ChatHistoryMessage(
                        role="assistant", content=content, additional_info=additional_info
                    )
                )

    return ChatHistoryResponse(
        thread_id=thread_id,
        messages=messages,
        interrupt=_find_pending_interrupt(pending_writes),
    )


def _find_pending_interrupt(pending_writes: list[PendingWrite]) -> dict[str, Any] | None:
    # 按 LangGraph 的任务状态判断是否仍在等待确认，已完成任务可能保留旧的中断记录。
    for task in read_task_statuses(pending_writes).values():
        for interrupt in task.pending_interrupts:
            if isinstance(interrupt.value, dict):
                return interrupt.value
    return None
