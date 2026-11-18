class ApplicationError(Exception):
    """应用业务异常基类。"""

    # 子类可覆盖 HTTP 状态码、客户端识别的错误码和对外提示。
    status_code: int = 500
    code: str = "APPLICATION_ERROR"
    message: str = "服务器内部错误"
