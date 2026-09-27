"""ScanGraph — 扫榜图（§3.6 placeholder 实现）.

  search_platform → collect_results → summarize_report → END
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents import build_scan_explorer
from app.agents.llm_factory import LLMFactory
from app.graphs.state import StoryState


DEFAULT_PLATFORMS = ("fanqie", "qidian", "zongheng")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stage(name: str, status: str = "done", notes: str | None = None) -> dict:
    s: dict = {
        "name": name,
        "status": status,
        "started_at": _now(),
        "finished_at": _now(),
    }
    if notes:
        s["notes"] = notes
    return s


async def search_platform_node(state: StoryState, **deps) -> dict:
    platforms = list(state.get("platforms") or DEFAULT_PLATFORMS)
    topic = (state.get("user_input") or "").strip() or state.get("scan_topic") or "都市悬疑"
    return {
        "platforms": platforms,
        "scan_topic": topic,
        "stages": [_stage("search_platform", notes=f"platforms={platforms}")],
    }


async def collect_results_node(state: StoryState, **deps) -> dict:
    topic = state.get("scan_topic") or "都市悬疑"
    rng = random.Random(hash(topic))
    results: list[dict] = []
    for plat in state.get("platforms") or DEFAULT_PLATFORMS:
        for i in range(3):
            results.append({
                "platform": plat,
                "rank": i + 1,
                "title": f"{topic} · 样例 {rng.randint(100, 999)}",
                "author": f"作者{rng.randint(1000, 9999)}",
                "genre": topic,
                "hot_index": rng.randint(50, 100),
                "wordcount": rng.choice([30000, 80000, 150000, 300000]),
            })
    return {
        "scan_results": results,
        "stages": [_stage("collect_results", notes=f"collected={len(results)} rows")],
    }


async def summarize_report_node(state: StoryState, **deps) -> dict:
    factory: LLMFactory = deps["llm_factory"]
    agent = build_scan_explorer(factory)
    payload = {
        "topic": state.get("scan_topic"),
        "platforms": state.get("platforms"),
        "results": state.get("scan_results", []),
    }
    msg = await agent.summarize(payload)
    report = (msg.content or "").strip()
    return {
        "scan_report": report,
        "stages": [_stage("summarize_report", notes=f"report_len={len(report)}")],
    }


def build_scan_graph():
    g = StateGraph(StoryState)
    g.add_node("search_platform", search_platform_node)
    g.add_node("collect_results", collect_results_node)
    g.add_node("summarize_report", summarize_report_node)

    g.set_entry_point("search_platform")
    g.add_edge("search_platform", "collect_results")
    g.add_edge("collect_results", "summarize_report")
    g.add_edge("summarize_report", END)

    return g.compile(name="scan")