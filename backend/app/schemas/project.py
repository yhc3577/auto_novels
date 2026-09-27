"""Project DTO."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

Slug = Annotated[str, StringConstraints(min_length=2, max_length=128, pattern=r"^[a-z0-9-]+$")]
Title = Annotated[str, StringConstraints(min_length=1, max_length=256)]


class ProjectCreate(BaseModel):
    slug: Slug
    title: Title
    genre: str | None = None
    platform: str | None = None


class ProjectOut(BaseModel):
    id: int
    slug: str
    title: str
    genre: str | None
    platform: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    chapter_count: int = Field(default=0, description="已 commit 的章节数")