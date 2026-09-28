"""UserRepository — CRUD for users 表."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ConflictError, NotFoundError
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, username: str, password_hash: str) -> User:
        """创建新用户.

        - username 必须唯一：冲突时抛 ConflictError(409)
        - password_hash 必须是已经哈希过的（明文由 service 层负责）
        """
        user = User(username=username, password_hash=password_hash)
        self.session.add(user)
        try:
            await self.session.flush()
        except IntegrityError as e:
            raise ConflictError(
                f"username '{username}' already exists",
                details={"username": username},
            ) from e
        return user

    async def get_by_id(self, user_id: int) -> User:
        user = await self.session.get(User, user_id)
        if user is None:
            raise NotFoundError(f"user {user_id} not found")
        return user

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return (await self.session.execute(stmt)).scalar_one_or_none()