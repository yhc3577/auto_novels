"""Auth API — /api/auth/register, /api/auth/login, /api/auth/me."""

from __future__ import annotations

from fastapi import APIRouter

from app.deps import CurrentUserDep, SessionDep
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.services.auth import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(payload: RegisterRequest, session: SessionDep) -> AuthResponse:
    """注册新用户 → 返 JWT token."""
    svc = AuthService(session)
    user, token = await svc.register(username=payload.username, password=payload.password)
    return AuthResponse(
        token=token,
        user_id=user.id,
        username=user.username,
        created_at=user.created_at,
    )


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, session: SessionDep) -> AuthResponse:
    """登录 → 返 JWT token."""
    svc = AuthService(session)
    user, token = await svc.login(username=payload.username, password=payload.password)
    return AuthResponse(
        token=token,
        user_id=user.id,
        username=user.username,
        created_at=user.created_at,
    )


@router.get("/me", response_model=AuthResponse)
async def me(user: CurrentUserDep) -> AuthResponse:
    """验证 token 还有效，返当前 user.

    用于前端 page reload 时检查登录态。
    token 已过期则 current_user_dep 抛 401。
    """
    return AuthResponse(
        token="",  # 不返明文 token（前端 localStorage 里有）
        user_id=user.id,
        username=user.username,
        created_at=user.created_at,
    )