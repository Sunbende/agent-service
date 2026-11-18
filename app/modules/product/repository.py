from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.product.models import Product


class ProductRepository:
    """只负责产品数据访问，不处理 HTTP 参数或组装响应。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_category(self, category: str | None = None) -> list[Product]:
        # 默认只查询有效产品；传入分类时再增加分类过滤。
        query = select(Product).where(Product.status == "active")
        if category is not None:
            query = query.where(Product.category == category)

        # 按产品 ID 升序返回全部符合条件的记录。
        result = await self.session.scalars(query.order_by(Product.id.asc()))
        return list(result.all())

    async def find_limited_by_category(
        self, category: str, premium_min: Decimal | None, limit: int
    ) -> list[Product]:
        # 每次只查一个险种，并且只返回有效产品。
        query = select(Product).where(
            Product.status == "active", Product.category == category
        )
        if premium_min is not None:
            # 仅保留最低保费小于指定预算的产品。
            query = query.where(Product.min_premium < premium_min)

        # 先按最低保费排序，再按 ID 保证同价产品顺序稳定。
        result = await self.session.scalars(
            query.order_by(Product.min_premium.asc().nullslast(), Product.id.asc())
            .limit(limit)
        )
        return list(result.all())
