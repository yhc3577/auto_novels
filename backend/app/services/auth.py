"""AuthService — 密码哈希 + JWT 签发 + 用户管理用例.

职责边界：
- 纯函数 hash/verify/create_token/decode_token —— 不依赖 session，可独立测试
- AuthService.register/login —— 组合 repo + 纯函数，做用例
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings
from app.errors import AuthenticationError, ConflictError
from app.models.user import User
from app.repositories.user import UserRepository


# bcrypt rounds (cost factor). 12 ≈ 250ms per hash on CPU.
_BCRYPT_ROUNDS = 12


# ---- 纯函数：密码 ----

def hash_password(plain: str) -> str:
    """bcrypt 哈希（自动加 salt, cost=12）.

    bcrypt 单次 hash 限 72 字节——超过自动截断（OWASP 推荐）。
    """
    return bcrypt.hashpw(plain.encode("utf-8")[:72], bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except ValueError:
        # 哈希格式错误（旧数据 / 损坏） → 视为不匹配
        return False


# ---- 纯函数：JWT ----

def create_access_token(*, user_id: int, username: str) -> str:
    """签发 JWT (HS256).

    payload: { sub: user_id, username, exp, iat }
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """解 JWT. 失败抛 AuthenticationError."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise AuthenticationError(f"invalid or expired token: {e}") from e


# ---- 用例 ----

class AuthService:
    def __init__(self, session) -> None:
        # 用 duck typing，不强制 import AsyncSession 类型（避免循环）
        self.repo = UserRepository(session)

    async def register(self, *, username: str, password: str) -> tuple[User, str]:
        """注册新用户 → 返回 (user, jwt_token).

        重复用户名抛 ConflictError(409)。
        """
        # 预检查：避免不必要的 bcrypt 运算
        existing = await self.repo.get_by_username(username)
        if existing is not None:
            raise ConflictError(
                f"username '{username}' already exists",
                details={"username": username},
            )
        user = await self.repo.create(
            username=username,
            password_hash=hash_password(password),
        )
        token = create_access_token(user_id=user.id, username=user.username)
        return user, token

    async def login(self, *, username: str, password: str) -> tuple[User, str]:
        """登录 → 返回 (user, jwt_token).

        用户不存在或密码错误统一抛 AuthenticationError(401)，不区分以避免用户名枚举攻击。
        """
        user = await self.repo.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("invalid username or password")
        # 更新 last_login_at
        user.last_login_at = datetime.now(timezone.utc)
        await self.repo.session.flush()

        token = create_access_token(user_id=user.id, username=user.username)
        return user, token

    async def get_current_user(self, token: str) -> User:
        """从 JWT 解出当前用户."""
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
        return await self.repo.get_by_id(user_id)