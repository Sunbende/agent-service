from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import get_session
from app.modules.product.models import Product
from app.modules.product.schemas import ProductResponse
from app.modules.product.service import ProductService

router = APIRouter(prefix="/api/v1/products", tags=["产品管理相关接口"])


# 通过依赖注入复用会话创建逻辑，供产品接口获取 Service。
def get_product_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProductService:
    return ProductService(session)


@router.get("", response_model=list[ProductResponse])
async def list_products(
    service: Annotated[ProductService, Depends(get_product_service)],
    category: str | None = None,
) -> list[Product]:
    # HTTP 层接收分类参数，查询交给 Service，响应由 ProductResponse 校验。
    return await service.list_products(category)


@router.get("/candidates", response_model=list[ProductResponse])
async def list_candidates(
    service: Annotated[ProductService, Depends(get_product_service)],
    categories: Annotated[list[str], Query(min_length=1)],
    premium_min: Annotated[Decimal | None, Query(gt=0)] = None,
    limit_per_category: Annotated[int, Query(ge=1, le=10)] = 5,
) -> list[Product]:
    # 必须提供至少一个险种；预算需大于 0，每类最多返回 1～10 个。
    return await service.list_candidates(
        categories, premium_min, limit_per_category
    )
