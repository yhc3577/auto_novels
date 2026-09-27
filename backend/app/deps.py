"""FastAPI dependencies — 异步 session 注入。

设计上复用 `session_scope`，保证：
- 同一事务边界（路由处理异常 → 全局 rollback）
- 路由函数拿到的就是 AsyncSession，看不到 engine / sessionmaker
"""

from __future__ import annotations

from typing import Annotated, AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import session_scope


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_scope() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]