"""FastAPI app entry."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import healthz_router, projects_router, write_router
from app.config import settings
from app.db import dispose_engine, get_engine
from app.errors import register_error_handlers
from app.logging_setup import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.log_level)
    # 启动时校验 DB 可达（失败也不致命，让 /api/healthz 报 ok=false）
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            from sqlalchemy import text

            await conn.execute(text("SELECT 1"))
    except Exception as e:  # pragma: no cover - infra check
        import logging

        logging.getLogger(__name__).warning("db connect failed at startup: %s", e)
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title="auto_novels backend",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)
    app.include_router(healthz_router)
    app.include_router(projects_router)
    app.include_router(write_router)

    return app


app = create_app()