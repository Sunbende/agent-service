from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatThreadCreate(BaseModel):
    """创建和重命名会话共用的请求结构。"""

    # 省略标题时使用默认值，提供标题时校验去掉首尾空白后的长度。
    title: str = Field(default="新会话", min_length=1, max_length=200)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> object:
        # 只处理字符串，其余类型交给 Pydantic 生成校验错误。
        return value.strip() if isinstance(value, str) else value


class ChatThreadResponse(BaseModel):
    """客服会话响应结果。"""

    # 从 ORM 对象读取响应所需的属性，例如 UUID 和时间字段。
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
