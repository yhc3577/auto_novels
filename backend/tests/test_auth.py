"""Tests for AuthService + /api/auth endpoints.

覆盖：
- 纯函数 hash/verify/create_token/decode_token
- AuthService.register / login / get_current_user（用 in-memory SQLite）
- API endpoint（用 FastAPI TestClient + 真 PG）
"""

from __future__ import annotations

import os

import pytest

# 测试时强制用 SQLite in-memory (不依赖 PG)
os.environ.setdefault("PG_DSN", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-XXXXXXXXXXXXXXXXXXXXXXXXXX")

from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.services.auth import (  # noqa: E402
    AuthService,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# ===========================================================================
# 纯函数
# ===========================================================================


def test_hash_password_returns_different_hashes_for_same_input():
    h1 = hash_password("hello123")
    h2 = hash_password("hello123")
    assert h1 != h2, "bcrypt 每次都该生成新 salt"
    assert h1.startswith("$2b$"), "bcrypt 哈希以 $2b$ 开头"


def test_verify_password_roundtrip():
    h = hash_password("hello123")
    assert verify_password("hello123", h) is True
    assert verify_password("wrong", h) is False


def test_jwt_roundtrip():
    token = create_access_token(user_id=42, username="alice")
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["username"] == "alice"
    assert "exp" in payload and "iat" in payload


def test_decode_invalid_token_raises():
    from app.errors import AuthenticationError

    with pytest.raises(AuthenticationError):
        decode_access_token("not-a-valid-token")


# ===========================================================================
# AuthService 用例 (in-memory SQLite)
# ===========================================================================


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_auth_service_register_and_login():
    """注册 + 登录全流程."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    from app.models import Base

    # StaticPool 保证所有 session 共用一个 connection（in-memory SQLite 否则看不到数据）
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with Session() as session:
        svc = AuthService(session)
        user, token1 = await svc.register(username="alice", password="secret123")
        assert user.id is not None
        assert user.username == "alice"
        assert token1  # 非空
        await session.commit()

        # 重复注册抛 ConflictError
        from app.errors import ConflictError

        with pytest.raises(ConflictError):
            await svc.register(username="alice", password="other456")

    async with Session() as session:
        svc = AuthService(session)
        # 登录成功
        user, token2 = await svc.login(username="alice", password="secret123")
        assert user.username == "alice"
        assert user.last_login_at is not None
        assert token2

        # 错密码
        from app.errors import AuthenticationError

        with pytest.raises(AuthenticationError):
            await svc.login(username="alice", password="wrong")

        # 不存在的用户（不区分错误信息）
        with pytest.raises(AuthenticationError):
            await svc.login(username="nobody", password="secret123")

    await engine.dispose()


@pytest.mark.asyncio
async def test_auth_service_get_current_user():
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    from app.models import Base

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with Session() as session:
        svc = AuthService(session)
        user, token = await svc.register(username="bob", password="pass456")
        await session.commit()

    async with Session() as session:
        svc = AuthService(session)
        me = await svc.get_current_user(token)
        assert me.id == user.id
        assert me.username == "bob"

    await engine.dispose()


# ===========================================================================
# API endpoint (TestClient + 真 PG)
# ===========================================================================


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient — 用真 PG 跑（init_db 已建 users 表）."""
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_api_register_201(client: TestClient):
    """POST /api/auth/register → 201 + token."""
    import uuid
    uname = f"user_{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/auth/register",
        json={"username": uname, "password": "secret123"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert "token" in body and body["token"]
    assert body["username"] == uname
    assert body["user_id"] > 0
    assert body["created_at"] is not None


def test_api_register_duplicate_409(client: TestClient):
    """重复注册 → 409."""
    import uuid
    uname = f"dup_{uuid.uuid4().hex[:8]}"
    client.post(
        "/api/auth/register",
        json={"username": uname, "password": "secret123"},
    )
    r = client.post(
        "/api/auth/register",
        json={"username": uname, "password": "secret123"},
    )
    assert r.status_code == 409, r.text
    assert r.json()["error"]["code"] == "conflict"


def test_api_register_validation_short_password_422(client: TestClient):
    """密码太短 → 422."""
    r = client.post(
        "/api/auth/register",
        json={"username": "testuser2", "password": "abc"},
    )
    assert r.status_code == 422


def test_api_register_validation_invalid_username_422(client: TestClient):
    """用户名含非法字符 → 422."""
    r = client.post(
        "/api/auth/register",
        json={"username": "测试用户", "password": "secret123"},
    )
    assert r.status_code == 422


def test_api_login_ok(client: TestClient):
    """POST /api/auth/login → 200 + token."""
    import uuid
    uname = f"login_{uuid.uuid4().hex[:8]}"
    client.post(
        "/api/auth/register",
        json={"username": uname, "password": "secret123"},
    )
    r = client.post(
        "/api/auth/login",
        json={"username": uname, "password": "secret123"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["token"]
    assert body["username"] == uname


def test_api_login_wrong_password_401(client: TestClient):
    r = client.post(
        "/api/auth/login",
        json={"username": "loginuser1", "password": "wrongpwd"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "authentication_error"


def test_api_login_unknown_user_401(client: TestClient):
    import uuid
    r = client.post(
        "/api/auth/login",
        json={"username": f"ghost_{uuid.uuid4().hex[:8]}", "password": "secret123"},
    )
    assert r.status_code == 401


def test_settings_jwt_secret_default():
    """确保 settings.jwt_secret / algorithm / expire 都从 env 读."""
    assert settings.jwt_secret
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_expire_minutes >= 60