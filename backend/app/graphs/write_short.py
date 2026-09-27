"""WriteGraphShort — 短篇写作图（§3.4 短篇路径）.

  route_scenario
    └─► write_prose      (agent: narrative_writer, compact prompt)
    └─► wordcount_checkpoint
    └─► tracking_commit
    └─► END

vs 长篇：跳过 write_prep / quality_scan；prompt 紧凑（一气呵成）；字数较短。
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _push_stage(state: StoryState, name: str, *, notes: str | None = None) -> list:
    stages = list(state.get("stages") or [])
    entry: dict = {"name": name, "status": "running", "started_at": _now()}
    if notes:
        entry["notes"] = notes
    stages.append(entry)
    return stages


def _complete_stage(state: StoryState, name: str, status: str = "done") -> list:
    stages = list(state.get("stages") or [])
    for s in reversed(stages):
        if s["name"] == name and s["status"] == "running":
            s["status"] = status
            s["finished_at"] = _now()
            break
    return stages


async def route_scenario_node(state: StoryState, **deps: Any) -> dict:
    """短篇：chapter_no=1（demo 简化，每次新建短篇 chapter_no 递进）."""
    session: AsyncSession = deps["session"]
    project_id = state["project_id"]
    if not state.get("chapter_no"):
        last = await TrackingService(session).init(project_id)
        chapter_no = last + 1
    else:
        chapter_no = int(state["chapter_no"])
    # 短篇默认字数 800
    target = int(state.get("target_wordcount") or 800)
    return {
        "chapter_no": chapter_no,
        "target_wordcount": target,
        "length": "short",
        "stages": _push_stage(state, "route_scenario", notes=f"length=short target={target}"),
    }


async def write_prose_node(state: StoryState, **deps: Any) -> dict:
    """短篇：紧凑 prompt，要求一气呵成、不超过 1500 字."""
    factory: LLMFactory = deps["llm_factory"]
    agent = build_narrative_writer(factory)
    chapter_no = int(state["chapter_no"])
    target = int(state.get("target_wordcount") or 800)

    prompt = (
        f"【短篇】项目 {state['project_id']} · chapter_no={chapter_no}。\n"
        f"主题: {state.get('user_input', '')}\n"
        f"字数: {target} (±25%)\n"
        "要求：开篇即冲突、单一情绪线、首尾呼应、不留悬念句。\n"
        "直接输出 markdown 正文。"
    )
    msg = await agent.run(prompt)
    body = (msg.content or "").strip()
    if not body.lstrip().startswith("#"):
        body = f"# 短篇 · {state.get('user_input', '')[:20]}\n\n" + body

    stages = _complete_stage(state, "route_scenario")
    stages = stages + [{"name": "write_prose", "status": "running", "started_at": _now()}]
    return {"prose_draft": body, "stages": stages}


async def wordcount_checkpoint_node(state: StoryState, **deps: Any) -> dict:
    wc = WordcountService()
    body = state.get("prose_draft") or ""
    target = int(state.get("target_wordcount") or 800)
    report = wc.checkpoint(body, target, tolerance=0.25)
    stages = _complete_stage(state, "write_prose")
    stages = stages + [
        {
            "name": "wordcount_checkpoint",
            "status": "running",
            "started_at": _now(),
            "notes": f"actual={report['actual']} target={report['target']} passed={report['passed']}",
        }
    ]
    return {"wordcount_report": report, "stages": stages}


async def tracking_commit_node(state: StoryState, **deps: Any) -> dict:
    session: AsyncSession = deps["session"]
    project_id = state["project_id"]
    chapter_no = int(state["chapter_no"])
    body = state.get("prose_draft") or ""
    summary = body if len(body) <= 140 else body[:140] + "…"

    tx = ChapterTransaction(
        chapter_no=chapter_no,
        chapter_content=body,
        chapter_title=f"短篇 · {chapter_no}",
        summary_text=summary,
        chapter_hook=None,
        emotion_arc={"start": "tense", "end": "resolved", "intensity": "high"},
    )
    snap = await TrackingService(session).commit(project_id, tx)
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
        "stages": stages,
    }


def build_write_short_graph():
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
    return g.compile(name="write_short")