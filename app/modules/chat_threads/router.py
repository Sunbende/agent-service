from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import get_session
from app.modules.chat_threads.models import ChatThread
from app.modules.chat_threads.schemas import ChatThreadCreate, ChatThreadResponse
from app.modules.chat_threads.service import ChatThreadService

router = APIRouter(prefix="/api/v1/chat-threads", tags=["会话管理相关接口"])


# 通过依赖注入复用当前请求的数据库 Session 来构造 Service。
def get_chat_thread_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ChatThreadService:
    return ChatThreadService(session)


# 会话接口统一从 x-user-id 请求头读取演示阶段的用户 ID。
@router.post("", response_model=ChatThreadResponse)
async def create_chat_thread(
    request: ChatThreadCreate,
    user_id: Annotated[int, Header(alias="x-user-id")],
    service: Annotated[ChatThreadService, Depends(get_chat_thread_service)],
) -> ChatThread:
    """创建会话。"""
    return await service.add(user_id, request.title)


@router.get("", response_model=list[ChatThreadResponse])
async def list_chat_threads(
    user_id: Annotated[int, Header(alias="x-user-id")],
    service: Annotated[ChatThreadService, Depends(get_chat_thread_service)],
) -> list[ChatThread]:
    """查询当前用户的会话列表。"""
    return await service.list_by_user(user_id)


@router.patch("/{thread_id}", response_model=ChatThreadResponse)
async def rename_chat_thread(
    thread_id: UUID,
    request: ChatThreadCreate,
    user_id: Annotated[int, Header(alias="x-user-id")],
    service: Annotated[ChatThreadService, Depends(get_chat_thread_service)],
) -> ChatThread:
    """重命名指定会话。"""
    # FastAPI 会先将路径参数校验并转换成 UUID，再进入 Service。
    return await service.rename(thread_id, user_id, request.title)


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_thread(
    thread_id: UUID,
    user_id: Annotated[int, Header(alias="x-user-id")],
    service: Annotated[ChatThreadService, Depends(get_chat_thread_service)],
) -> Response:
    """删除指定会话。"""
    await service.delete(thread_id, user_id)
    # 删除成功后返回空响应体。
    return Response(status_code=status.HTTP_204_NO_CONTENT)
