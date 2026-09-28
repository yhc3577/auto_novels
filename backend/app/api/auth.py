"""Auth API — /api/auth/register, /api/auth/login."""

from __future__ import annotations

from fastapi import APIRouter

from app.deps import SessionDep
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