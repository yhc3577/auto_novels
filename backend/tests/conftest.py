"""Pytest fixtures — async session + clean DB."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session_factory


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """每个测试一个 session；不 commit，自动 rollback。"""
    factory = get_session_factory()
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def clean_db() -> AsyncIterator[None]:
    """每个测试清空 3 张业务表（保留 schema）。"""
    factory = get_session_factory()
    async with factory() as session:
        await session.execute(text("TRUNCATE TABLE chapter_records, chapters, projects RESTART IDENTITY CASCADE"))
        await session.commit()
    yield