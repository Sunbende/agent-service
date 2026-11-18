from app.core.exceptions import ApplicationError


class ChatThreadNotFoundError(ApplicationError):
    """会话不存在或不属于当前用户。"""

    # 两种情形使用相同的响应，避免透露其他用户的会话是否存在。
    status_code = 400
    code = "CHAT_THREAD_NOT_FOUND"
    message = "会话不存在或不属于当前用户"
