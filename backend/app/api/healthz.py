"""Health check."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.db import get_session_factory

router = APIRouter(tags=["meta"])


@router.get("/api/healthz")
async def healthz() -> dict:
    db_ok = True
    try:
        factory = get_session_factory()
        async with factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {"ok": True, "db": db_ok}