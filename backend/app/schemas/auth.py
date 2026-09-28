"""Auth DTO — 登录注册请求/响应."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

Username = Annotated[str, StringConstraints(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")]
Password = Annotated[str, StringConstraints(min_length=6, max_length=128)]


class RegisterRequest(BaseModel):
    username: Username
    password: Password


class LoginRequest(BaseModel):
    username: Username
    password: Password


class AuthResponse(BaseModel):
    """登录/注册成功响应."""

    token: str
    user_id: int
    username: str
    created_at: datetime | None = None