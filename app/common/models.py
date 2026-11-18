from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# SQLAlchemy 的统一基类，所有数据库表模型都继承它。
class Base(DeclarativeBase):
    """数据库表模型的公共基类。"""

    def __repr__(self) -> str:
        """通用的 repr 方法，方便在控制台查看对象字段。"""
        attrs = {}
        for key, value in vars(self).items():
            if key.startswith("_"):
                continue
            attrs[key] = (
                value.strftime("%Y-%m-%d %H:%M:%S")
                if isinstance(value, datetime)
                else value
            )
        return f"{type(self).__name__}({attrs})"


# 创建时间混入类，供其它模型复用。
class CreateAtMixin:
    # 由数据库在插入时生成创建时间。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# 更新时间混入类，供其它模型复用。
class UpdateAtMixin:
    # SQLAlchemy 更新数据行时自动刷新该字段。
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
