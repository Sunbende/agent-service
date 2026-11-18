from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class ProductResponse(BaseModel):
    """保险产品响应结果，供产品列表和候选产品接口复用。"""

    # 从数据库模型的属性读取字段，交由 FastAPI 校验和序列化。
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    clause_name: str
    category: str
    insurer: str
    image_url: str
    description: str
    min_premium: Decimal | None
    max_premium: Decimal | None
    target_group: str | None
    highlights: list[str]
    status: str

    @field_validator("image_url", "description", mode="before")
    @classmethod
    def empty_text_for_null(cls, value: str | None) -> str:
        # 数据库允许空值，接口按文档返回字符串。
        return value or ""

    @field_validator("highlights", mode="before")
    @classmethod
    def empty_list_for_null(cls, value: list[str] | None) -> list[str]:
        # 数据库允许空值，接口始终返回数组。
        return value if value is not None else []
