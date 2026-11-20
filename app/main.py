from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.core.logging import configure_logging, get_logger
from app.modules.chat_threads.router import router as chat_thread_router
from app.modules.product.router import router as product_router

# 初始化日志系统
configure_logging(settings.logging.level)
logger = get_logger(__name__)

# 生命周期管理（预留）
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"【{settings.app.name}】应用启动中...")
    from app.infra.database import check_database, close_database
    from app.infra.checkpointer import init_checkpointer, close_checkpointer
    try:
        await check_database()
        await init_checkpointer()
        yield
    finally:
        logger.info("应用关闭中... ")
        await close_database()
        await close_checkpointer()

app = FastAPI(
    title=settings.app.name,
    debug=settings.app.debug,
    lifespan=lifespan,
)
# 将产品和会话模块的路由注册到同一个 FastAPI 应用。
app.include_router(product_router)
app.include_router(chat_thread_router)


# FastAPI 按异常类型匹配，全应用的 ApplicationError 子类都由此处理。
@app.exception_handler(ApplicationError)
async def handle_application_error(
    request: Request, exc: ApplicationError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


@app.get("/health", summary="健康检测接口")
async def health_check() -> dict[str, str]:
    logger.info("执行健康检查")
    return {"status": "ok"}

if __name__ == "__main__":
    import sys
    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=False,
        loop= "asyncio:SelectorEventLoop" if sys.platform == "win32" else "auto",
    )
