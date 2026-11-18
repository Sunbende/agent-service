from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.product.models import Product
from app.modules.product.repository import ProductRepository


class ProductService:
    """组织产品业务流程，并调用 Repository 查询数据。"""

    def __init__(self, session: AsyncSession):
        self.repository = ProductRepository(session)

    async def list_products(self, category: str | None = None) -> list[Product]:
        return await self.repository.find_by_category(category)

    async def list_candidates(
        self,
        categories: list[str],
        premium_min: Decimal | None,
        limit_per_category: int,
    ) -> list[Product]:
        candidates: list[Product] = []
        # 对险种去重并保留请求中的顺序；每个险种单独查询指定数量。
        for category in dict.fromkeys(categories):
            candidates.extend(
                await self.repository.find_limited_by_category(
                    category, premium_min, limit_per_category
                )
            )
        return candidates
