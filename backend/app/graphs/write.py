"""WriteGraph — 最薄实现（4 节点）:

  route_scenario
    └─► write_prose      (agent: narrative_writer)
    └─► wordcount_checkpoint (service: WordcountService)
    └─► tracking_commit   (service: TrackingService — 单事务多表写入)
    └─► END

铁律：
- graph 节点不直接 import repository / models
- 只通过 service 操作 DB
- agent 只能被 graph 节点调用，agent 本身不感知 session
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents import build_narrative_writer
from app.agents.llm_factory import LLMFactory
from app.db import AsyncSession
from app.graphs.state import StoryState
from app.services.tracking import ChapterTransaction, TrackingService
from app.services.wordcount import WordcountService


# ---------------------------------------------------------------------------
# Stage helpers
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _push_stage(state: StoryState, name: str) -> list:
    stages = list(state.get("stages") or [])
    stages.append({"name": name, "status": "running", "started_at": _now()})
    return stages


def _complete_stage(state: StoryState, name: str, status: str = "done") -> list:
    stages = list(state.get("stages") or [])
    for s in reversed(stages):
        if s["name"] == name and s["status"] == "running":
            s["status"] = status
            s["finished_at"] = _now()
            break
    return stages


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


async def route_scenario_node(state: StoryState, **deps: Any) -> dict:
    """默认 chapter_no = last_committed + 1。"""
    session: AsyncSession = deps["session"]
    factory: LLMFactory = deps["llm_factory"]
    project_id = state["project_id"]
    user_input = state.get("user_input") or ""

    # 推算 chapter_no（若用户未传）
    if not state.get("chapter_no"):
        tracking = TrackingService(session)
        last = await tracking.init(project_id)
        chapter_no = last + 1
    else:
        chapter_no = int(state["chapter_no"])

    target = int(state.get("target_wordcount") or 1500)

    return {
        "chapter_no": chapter_no,
        "target_wordcount": target,
        "stages": _push_stage(state, "route_scenario"),
        "extra": {"factory_provider": factory.provider},
    }


async def write_prose_node(state: StoryState, **deps: Any) -> dict:
    """调 narrative_writer 生成正文。"""
    factory: LLMFactory = deps["llm_factory"]
    agent = build_narrative_writer(factory)
    chapter_no = int(state["chapter_no"])
    target = int(state.get("target_wordcount") or 1500)

    prompt = (
        f"项目 {state['project_id']} 第 {chapter_no} 章。\n"
        f"用户输入: {state.get('user_input', '')}\n"
        f"目标字数: {target} (±20%)\n"
        "请直接输出 markdown 正文。"
    )
    msg = await agent.run(prompt)
    body = (msg.content or "").strip()
    if not body:
        body = f"# 第{chapter_no}章\n\n（写作失败，请检查 LLM provider。）"
    elif not body.lstrip().startswith("#"):
        body = f"# 第{chapter_no}章\n\n" + body

    stages = _complete_stage(state, "route_scenario")
    stages = stages + [{"name": "write_prose", "status": "running", "started_at": _now()}]

    return {
        "prose_draft": body,
        "stages": stages,
    }


async def wordcount_checkpoint_node(state: StoryState, **deps: Any) -> dict:
    """字数校验（CJK + 英文）。"""
    wc = WordcountService()
    body = state.get("prose_draft") or ""
    target = int(state.get("target_wordcount") or 1500)
    report = wc.checkpoint(body, target)

    stages = _complete_stage(state, "write_prose")
    stages = stages + [
        {
            "name": "wordcount_checkpoint",
            "status": "running",
            "started_at": _now(),
            "notes": f"actual={report['actual']} target={report['target']} passed={report['passed']}",
        }
    ]

    return {
        "wordcount_report": report,
        "stages": stages,
    }


async def tracking_commit_node(state: StoryState, **deps: Any) -> dict:
    """原子化写入 chapters + chapter_records（铁律：唯一 commit 入口）。"""
    session: AsyncSession = deps["session"]
    project_id = state["project_id"]
    chapter_no = int(state["chapter_no"])
    body = state.get("prose_draft") or ""

    wc_report = state.get("wordcount_report") or {}
    summary = (body[:140] + "…") if len(body) > 140 else body
    hook_match = body.split("\n\n")[-1][:200] if "\n\n" in body else body[:200]

    tx = ChapterTransaction(
        chapter_no=chapter_no,
        chapter_content=body,
        chapter_title=f"第{chapter_no}章",
        summary_text=summary,
        chapter_hook=hook_match,
        continuity_to_next=None,
        open_conflicts=None,
        location=None,
        pov=None,
        emotion_arc={"start": "neutral", "end": "tense", "intensity": "medium"},
        characters_in_scene=None,
        foreshadowing_changes=None,
    )
    tracking = TrackingService(session)
    snap = await tracking.commit(project_id, tx)
    # 由调用方统一 await session.commit() —— 这里仅 flush

    stages = _complete_stage(state, "wordcount_checkpoint")
    stages = stages + [
        {
            "name": "tracking_commit",
            "status": "running",
            "started_at": _now(),
            "notes": f"chapter_id={snap.chapter_id} wordcount={snap.final_wordcount}",
        }
    ]

    return {
        "chapter_id": snap.chapter_id,
        "state_revision": snap.state_revision,
        "final_wordcount": snap.final_wordcount,
        "summary_text": summary,
        "chapter_hook": hook_match,
        "stages": stages,
    }


# ---------------------------------------------------------------------------
# Build graph
# ---------------------------------------------------------------------------


def build_write_graph():
    g = StateGraph(StoryState)

    g.add_node("route_scenario", route_scenario_node)
    g.add_node("write_prose", write_prose_node)
    g.add_node("wordcount_checkpoint", wordcount_checkpoint_node)
    g.add_node("tracking_commit", tracking_commit_node)

    g.set_entry_point("route_scenario")
    g.add_edge("route_scenario", "write_prose")
    g.add_edge("write_prose", "wordcount_checkpoint")
    g.add_edge("wordcount_checkpoint", "tracking_commit")
    g.add_edge("tracking_commit", END)

    return g.compile(name="write_demo")