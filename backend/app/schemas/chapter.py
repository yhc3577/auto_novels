"""Chapter DTO."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ChapterOut(BaseModel):
    id: int
    project_id: int
    chapter_no: int
    title: str | None
    wordcount: int
    state_revision: int
    summary_text: str | None = None
    chapter_hook: str | None = None
    created_at: datetime