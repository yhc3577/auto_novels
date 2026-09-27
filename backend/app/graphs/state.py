"""Shared LangGraph state — 跨子图共享的状态.

字段分组：
- session / project：路由 + project 上下文
- intent / dispatch：意图识别 + 分发
- write_long / write_short：写章节共用
- scan：扫榜专用
- completion：完成态
"""

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
    # ----- session -----
    request_id: str
    user_input: str

    # ----- project -----
    project_id: int
    project_slug: str

    # ----- intent / dispatch -----
    intent: str               # write_long / write_short / scan / review / analyze / memory_query / unknown
    graph_invoked: str        # 实际调用的子图名
    supported: bool           # 该 intent 当前是否已实现
    notice: str | None        # 预留 intent 的友好提示

    # ----- write (long / short 共用) -----
    length: Literal["long", "short"]
    chapter_no: int
    target_wordcount: int
    prose_draft: str
    wordcount_report: dict

    # ----- write 长篇 专用 -----
    recall: dict              # ContextService 召回包
    quality_report: dict
    chapter_hook: str
    summary_text: str
    continuity_to_next: str
    open_conflicts: list[str]
    location: str
    pov: str
    emotion_arc: dict
    characters_in_scene: list[dict]
    foreshadowing_changes: list[dict]

    # ----- scan 专用 -----
    platforms: list[str]
    scan_topic: str
    scan_results: list[dict]
    scan_report: str

    # ----- completion -----
    chapter_id: int | None
    state_revision: int
    final_wordcount: int | None
    stages: list[StageStatus]
    report: str
    errors: list[str]
    extra: dict[str, Any]