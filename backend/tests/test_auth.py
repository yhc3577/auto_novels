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


# ===========================================================================
# JWT 中间件 (require_current_user) — 验证各业务端点都需要鉴权
# ===========================================================================


def _register_and_get_token(client: TestClient) -> str:
    """辅助：注册一个临时用户并返回 JWT."""
    import uuid
    uname = f"jwt_{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/auth/register",
        json={"username": uname, "password": "secret123"},
    )
    assert r.status_code == 201, r.text
    return r.json()["token"]


def test_api_me_without_token_401(client: TestClient):
    """GET /api/auth/me 无 token → 401."""
    r = client.get("/api/auth/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "authentication_error"


def test_api_me_with_valid_token_200(client: TestClient):
    """GET /api/auth/me 携正确 token → 200 + 用户信息."""
    token = _register_and_get_token(client)
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["username"].startswith("jwt_")
    assert body["user_id"] > 0


def test_api_me_with_garbage_token_401(client: TestClient):
    """携乱七八糟的 token → 401."""
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401


def test_api_me_with_malformed_header_401(client: TestClient):
    """Header 不是 Bearer 开头 → 401."""
    r = client.get("/api/auth/me", headers={"Authorization": "Basic xxx"})
    assert r.status_code == 401
    assert "missing or malformed" in r.json()["error"]["message"].lower() or "bearer" in r.json()["error"]["message"].lower()


def test_api_projects_requires_auth(client: TestClient):
    """GET /api/projects 无 token → 401."""
    r = client.get("/api/projects")
    assert r.status_code == 401


def test_api_projects_with_auth_ok(client: TestClient):
    """携 token 列出项目（可为空）→ 200."""
    token = _register_and_get_token(client)
    r = client.get("/api/projects", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_api_write_requires_auth(client: TestClient):
    """POST /api/write 无 token → 401."""
    r = client.post(
        "/api/write",
        json={"project_id": 1, "user_input": "x", "target_wordcount": 100},
    )
    assert r.status_code == 401


def test_api_router_requires_auth(client: TestClient):
    """POST /api/router 无 token → 401."""
    r = client.post(
        "/api/router",
        json={"project_id": 1, "user_input": "x", "explicit_scenario": "auto"},
    )
    assert r.status_code == 401


def test_api_healthz_does_not_require_auth(client: TestClient):
    """/api/healthz 不应被鉴权拦截（监控系统要能访问）."""
    r = client.get("/api/healthz")
    assert r.status_code == 200


def test_api_auth_login_does_not_require_auth(client: TestClient):
    """/api/auth/login 不应被鉴权拦截（不然永远登不上）."""
    r = client.post(
        "/api/auth/login",
        json={"username": "nobody123", "password": "somepassword"},
    )
    # 这里不是 401（鉴权失败），而是 401（用户不存在）—— 状态码巧合，
    # 但实际 response body 不一样。
    assert r.status_code == 401
    assert "invalid username or password" in r.json()["error"]["message"]


# ===========================================================================
# User-scoped 隔离 — user A 看不到 / 动不了 user B 的资源
# ===========================================================================


def _register_user(client: TestClient, uname: str, pwd: str = "secret123") -> tuple[str, int]:
    r = client.post(
        "/api/auth/register",
        json={"username": uname, "password": pwd},
    )
    assert r.status_code == 201, r.text
    return r.json()["token"], r.json()["user_id"]


def _create_project(client: TestClient, token: str, slug: str, title: str = "T") -> int:
    r = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"slug": slug, "title": title},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_user_scoped_list_only_returns_own_projects(client: TestClient):
    """user A 列出项目时，user B 的项目不应出现."""
    import uuid
    suf = uuid.uuid4().hex[:6]
    token_a, _ = _register_user(client, f"alice_{suf}")
    token_b, _ = _register_user(client, f"bob_{suf}")
    proj_a = _create_project(client, token_a, f"alice-proj-{suf}", "Alice's book")
    proj_b = _create_project(client, token_b, f"bob-proj-{suf}", "Bob's book")

    # Alice list 只返自己的
    r = client.get("/api/projects", headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()]
    assert proj_a in ids
    assert proj_b not in ids

    # Bob list 只返自己的
    r = client.get("/api/projects", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()]
    assert proj_b in ids
    assert proj_a not in ids


def test_user_scoped_get_other_users_project_returns_404(client: TestClient):
    """user A get user B 的 project → 404（不暴露存在性）."""
    import uuid
    suf = uuid.uuid4().hex[:6]
    token_a, _ = _register_user(client, f"getter_{suf}")
    token_b, _ = _register_user(client, f"owner_{suf}")
    proj_b = _create_project(client, token_b, f"secret-{suf}", "secret")

    r = client.get(
        f"/api/projects/{proj_b}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_user_scoped_same_slug_for_different_users_ok(client: TestClient):
    """两个 user 可以同名 slug — composite unique (user_id, slug)."""
    import uuid
    suf = uuid.uuid4().hex[:6]
    token_a, _ = _register_user(client, f"ua_{suf}")
    token_b, _ = _register_user(client, f"ub_{suf}")
    slug = f"shared-slug-{suf}"

    # Alice 建
    r1 = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"slug": slug, "title": "A's"},
    )
    assert r1.status_code == 201, r1.text

    # Bob 也能建同名
    r2 = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"slug": slug, "title": "B's"},
    )
    assert r2.status_code == 201, r2.text
    assert r1.json()["id"] != r2.json()["id"]


def test_user_scoped_same_slug_same_user_409(client: TestClient):
    """同一 user 重复 slug → 409."""
    import uuid
    suf = uuid.uuid4().hex[:6]
    token, _ = _register_user(client, f"dup_{suf}")
    slug = f"same-{suf}"

    r1 = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"slug": slug, "title": "1st"},
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"slug": slug, "title": "2nd"},
    )
    assert r2.status_code == 409


def test_user_scoped_write_other_users_project_404(client: TestClient):
    """user A 调 /api/write 写 user B 的 project → 404."""
    import uuid
    suf = uuid.uuid4().hex[:6]
    token_a, _ = _register_user(client, f"writer_{suf}")
    token_b, _ = _register_user(client, f"target_{suf}")
    proj_b = _create_project(client, token_b, f"target-{suf}", "T")

    r = client.post(
        "/api/write",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "project_id": proj_b,
            "user_input": "写第 1 章",
            "target_wordcount": 500,
        },
    )
    assert r.status_code == 404


def test_user_scoped_router_other_users_project_404(client: TestClient):
    """user A 调 /api/router 走 user B 的 project → 404."""
    import uuid
    suf = uuid.uuid4().hex[:6]
    token_a, _ = _register_user(client, f"router_{suf}")
    token_b, _ = _register_user(client, f"target2_{suf}")
    proj_b = _create_project(client, token_b, f"router-target-{suf}", "T")

    r = client.post(
        "/api/router",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "project_id": proj_b,
            "user_input": "x",
            "explicit_scenario": "auto",
        },
    )
    assert r.status_code == 404