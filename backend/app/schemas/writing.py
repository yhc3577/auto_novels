"""Writing DTO — 写章节请求/响应."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class WriteRequest(BaseModel):
    """触发一次写章节流."""

    project_id: int = Field(gt=0)
    chapter_no: int | None = Field(
        default=None,
        gt=0,
        description="不传则默认写下一章（last_committed + 1）",
    )
    user_input: str = Field(min_length=1, max_length=2000)
    target_wordcount: int = Field(default=1500, gt=0, le=50000)


class StageStatus(BaseModel):
    name: str
    status: Literal["pending", "running", "done", "skipped", "failed"]
    started_at: datetime | None = None
    finished_at: datetime | None = None
    notes: str | None = None


class WriteResponse(BaseModel):
    project_id: int
    chapter_no: int
    chapter_id: int | None
    state_revision: int
    final_wordcount: int | None
    stages: list[StageStatus]
    chapter_hook: str | None = None
    summary_text: str | None = None
    errors: list[str] = []