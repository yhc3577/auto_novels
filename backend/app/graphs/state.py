"""Shared LangGraph state for the demo WriteGraph."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, TypedDict


class StageStatus(TypedDict, total=False):
    name: str
    status: Literal["pending", "running", "done", "skipped", "failed"]
    started_at: str
    finished_at: str
    notes: str


class StoryState(TypedDict, total=False):
    # input
    project_id: int
    chapter_no: int
    user_input: str
    target_wordcount: int

    # artifacts (LLM-produced, before commit)
    prose_draft: str
    wordcount_report: dict
    chapter_hook: str
    summary_text: str

    # completion
    chapter_id: int | None
    state_revision: int
    final_wordcount: int | None
    stages: list[StageStatus]
    errors: list[str]
    extra: dict[str, Any]