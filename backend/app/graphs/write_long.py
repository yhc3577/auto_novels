"""WriteGraphLong — 长篇章节写作图（§3.4 长篇路径）.

  route_scenario
    └─► write_prep      (service: ContextService.assemble_recall)
    └─► write_prose      (agent: narrative_writer)
    └─► wordcount_checkpoint (service: WordcountService)
    └─► quality_scan     (service: QualityService 4 项)
    └─► tracking_commit  (service: TrackingService — 单事务多表写入)
    └─► END

vs 短篇：含 write_prep / quality_scan；prompt 更详细（要求结构、节奏、钩子）。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents import build_narrative_writer
from app.agents.llm_factory import LLMFactory
from app.db import AsyncSession
from app.graphs.state import StoryState
from app.services.context import ContextService
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


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


async def route_scenario_node(state: StoryState, **deps: Any) -> dict:
    """长篇：推算 chapter_no + 锁定 length=long."""
    session: AsyncSession = deps["session"]
    project_id = state["project_id"]
    if not state.get("chapter_no"):
        last = await TrackingService(session).init(project_id)
        chapter_no = last + 1
    else:
        chapter_no = int(state["chapter_no"])
    target = int(state.get("target_wordcount") or 3000)
    return {
        "chapter_no": chapter_no,
        "target_wordcount": target,
        "length": "long",
        "stages": _push_stage(state, "route_scenario", notes=f"length=long target={target}"),
    }


async def write_prep_node(state: StoryState, **deps: Any) -> dict:
    """召回 last_n 章 + 参考材料 + 作者记忆."""
    session: AsyncSession = deps["session"]
    ctx = ContextService(session)
    recall = await ctx.assemble_recall(
        state["project_id"], last_n=3, include_refs=True
    )
    stages = _complete_stage(state, "route_scenario")
    stages = stages + [{"name": "write_prep", "status": "running", "started_at": _now()}]
    return {"recall": recall, "stages": stages}


async def write_prose_node(state: StoryState, **deps: Any) -> dict:
    """调 narrative_writer 生成正文。prompt 比短篇详细（含召回 + 钩子要求）."""
    factory: LLMFactory = deps["llm_factory"]
    agent = build_narrative_writer(factory)
    chapter_no = int(state["chapter_no"])
    target = int(state.get("target_wordcount") or 3000)
    recall = state.get("recall") or {}

    prompt = (
        f"项目 {state['project_id']} 第 {chapter_no} 章（长篇）。\n"
        f"用户输入: {state.get('user_input', '')}\n"
        f"目标字数: {target} (±20%)\n"
        f"上一章钩子: {recall.get('recent_chapter_summaries', [])}\n"
        f"参考材料: {recall.get('reference_materials', [])}\n"
        f"作者记忆: {recall.get('author_memory', [])}\n"
        f"open conflicts: {recall.get('open_conflicts', [])}\n"
        "要求：章节钩子强、对话与动作推进节奏、结尾留下下一章悬念。"
        "请直接输出 markdown 正文。"
    )
    msg = await agent.run(prompt)
    body = (msg.content or "").strip()
    if not body.lstrip().startswith("#"):
        body = f"# 第{chapter_no}章\n\n" + body

    stages = _complete_stage(state, "write_prep")
    stages = stages + [{"name": "write_prose", "status": "running", "started_at": _now()}]
    return {"prose_draft": body, "stages": stages}


async def wordcount_checkpoint_node(state: StoryState, **deps: Any) -> dict:
    wc = WordcountService()
    body = state.get("prose_draft") or ""
    target = int(state.get("target_wordcount") or 3000)
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
    return {"wordcount_report": report, "stages": stages}


async def quality_scan_node(state: StoryState, **deps: Any) -> dict:
    """4 项基础质量扫描（ai_patterns / degeneration / punctuation / banned_words）。

    demo 简化：不抛错，只标注。
    """
    body = state.get("prose_draft") or ""
    # 占位：用长度 + 关键词个数做最简 sanity check
    ai_marker_hits = sum(1 for kw in ["综上所述", "值得注意的是"] if kw in body)
    quality_report = {
        "ai_patterns": {"hits": ai_marker_hits, "passed": ai_marker_hits == 0},
        "wordcount": state.get("wordcount_report", {}),
    }
    stages = _complete_stage(state, "wordcount_checkpoint")
    stages = stages + [
        {
            "name": "quality_scan",
            "status": "running",
            "started_at": _now(),
            "notes": f"ai_patterns_hits={ai_marker_hits}",
        }
    ]
    return {"quality_report": quality_report, "stages": stages}


async def tracking_commit_node(state: StoryState, **deps: Any) -> dict:
    session: AsyncSession = deps["session"]
    project_id = state["project_id"]
    chapter_no = int(state["chapter_no"])
    body = state.get("prose_draft") or ""
    summary = (body[:140] + "…") if len(body) > 140 else body
    hook = body.split("\n\n")[-1][:200] if "\n\n" in body else body[:200]

    tx = ChapterTransaction(
        chapter_no=chapter_no,
        chapter_content=body,
        chapter_title=f"第{chapter_no}章",
        summary_text=summary,
        chapter_hook=hook,
        emotion_arc={"start": "neutral", "end": "tense", "intensity": "medium"},
    )
    snap = await TrackingService(session).commit(project_id, tx)
    stages = _complete_stage(state, "quality_scan")
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
        "chapter_hook": hook,
        "stages": stages,
    }


def build_write_long_graph():
    g = StateGraph(StoryState)
    g.add_node("route_scenario", route_scenario_node)
    g.add_node("write_prep", write_prep_node)
    g.add_node("write_prose", write_prose_node)
    g.add_node("wordcount_checkpoint", wordcount_checkpoint_node)
    g.add_node("quality_scan", quality_scan_node)
    g.add_node("tracking_commit", tracking_commit_node)
    g.set_entry_point("route_scenario")
    g.add_edge("route_scenario", "write_prep")
    g.add_edge("write_prep", "write_prose")
    g.add_edge("write_prose", "wordcount_checkpoint")
    g.add_edge("wordcount_checkpoint", "quality_scan")
    g.add_edge("quality_scan", "tracking_commit")
    g.add_edge("tracking_commit", END)
    return g.compile(name="write_long")