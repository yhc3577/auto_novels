"""FastAPI dependencies — 异步 session 注入 + JWT 鉴权.

设计上复用 `session_scope`，保证：
- 同一事务边界（路由处理异常 → 全局 rollback）
- 路由函数拿到的就是 AsyncSession，看不到 engine / sessionmaker
"""

from __future__ import annotations

from typing import Annotated, AsyncIterator

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import session_scope
from app.errors import AuthenticationError
from app.models.user import User
from app.services.auth import AuthService


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_scope() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def require_current_user(
    session: SessionDep,
    authorization: str | None = Header(default=None),
) -> User:
    """JWT 鉴权依赖：从 Authorization: Bearer <token> 解出当前 User.

    任何已鉴权的端点（projects / write / router 等）都依赖它。
    - 缺 / 格式错 / 签名错 / 过期 token → AuthenticationError(401)
    - token 合法但用户已被删除 → AuthenticationError(401)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError(
            "missing or malformed Authorization header",
            details={"hint": "use 'Bearer <token>'"},
        )
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise AuthenticationError("empty bearer token")

    svc = AuthService(session)
    return await svc.get_current_user(token)


CurrentUserDep = Annotated[User, Depends(require_current_user)]