"""Shared LangGraph state — 跨子图共享 + LangGraph reducer.

reducer 策略：
- stages：用自定义 _append_unique_stages —— 按 (name, started_at) 去重
  防止 subgraph-as-node 时父图 stages 被子图重复累积（子图 state 含父 stages）
- errors / open_conflicts / foreshadowing_changes / characters_in_scene：
  operator.add —— 简单 list 追加
- 其他字段：默认"最后一次写入为准"（无 reducer）
"""

from __future__ import annotations

import operator
from datetime import datetime
from typing import Annotated, Any, Literal, TypedDict


# ---------------------------------------------------------------------------
# Custom reducer for stages
# ---------------------------------------------------------------------------


def _append_unique_stages(old: list, new: list) -> list:
    """按 (name, started_at) 去重追加 stage events.

    为什么需要：subgraph-as-node 模式下，子图节点的 state 从父 state 继承，
    子图内部累积 stages 会**包含**父图已有的 events。如果父子都用 operator.add，
    父图 patch 时会把这些 events 再次 append，stages 列表出现重复。

    解决：去重 by (name, started_at)。非 dict 元素（如字符串）直接追加不做去重。
    """
    seen: set = set()
    for e in old:
        if isinstance(e, dict):
            seen.add((e.get("name"), e.get("started_at")))
    out = list(old)
    for e in new:
        if isinstance(e, dict):
            key = (e.get("name"), e.get("started_at"))
            if key not in seen:
                seen.add(key)
                out.append(e)
        else:
            out.append(e)
    return out


# ---------------------------------------------------------------------------
# Status types
# ---------------------------------------------------------------------------


class StageStatus(TypedDict, total=False):
    name: str
    status: Literal["pending", "running", "done", "skipped", "failed"]
    started_at: str
    finished_at: str
    notes: str


class StoryState(TypedDict, total=False):
    # ----- 累积字段（带 reducer）-----
    stages: Annotated[list, _append_unique_stages]
    errors: Annotated[list[str], operator.add]
    open_conflicts: Annotated[list[str], operator.add]
    foreshadowing_changes: Annotated[list[dict], operator.add]
    characters_in_scene: Annotated[list[dict], operator.add]

    # ----- session -----
    request_id: str
    user_input: str

    # ----- project -----
    project_id: int
    project_slug: str
    user_id: int                                  # owner — graph 节点可见，写入 owner-scoped 表时用

    # ----- intent / dispatch -----
    intent: str
    explicit_scenario: str  # router 输入：auto / write_long / write_short / scan
    graph_invoked: str
    supported: bool
    notice: str | None

    # ----- write (long / short 共用) -----
    length: Literal["long", "short"]
    chapter_no: int
    target_wordcount: int
    prose_draft: str
    wordcount_report: dict

    # ----- write 长篇 专用 -----
    recall: dict
    chapter_outline: dict                       # chapter_design 产出
    pre_write_validation_report: dict           # pre_write_validate 产出
    post_write_check_report: dict               # post_write_check 产出（含 normalized_prose）
    consistency_report: dict                    # prose_consistency (LLM) 产出
    pre_write_retry_count: int                  # pre_write 循环计数
    design_iteration: int                       # chapter_design → write_prose 循环计数
    interrupt_pending: bool                     # 是否需要人工审核
    interrupt_reason: str | None                # 人工审核原因
    quality_report: dict
    chapter_hook: str
    summary_text: str
    continuity_to_next: str
    location: str
    pov: str
    emotion_arc: dict

    # ----- scan 专用 -----
    platforms: list[str]
    scan_topic: str
    scan_results: list[dict]
    scan_report: str

    # ----- completion -----
    chapter_id: int | None
    state_revision: int
    final_wordcount: int | None
    report: str
    extra: dict[str, Any]