"""ScanGraph — 扫榜图（§3.6 placeholder 实现）.

  search_platform → collect_results → summarize_report → END

demo 阶段：mock 平台列表 + mock 采集结果 + LLM 摘要报告。
生产：替换为真实平台 API（fanqie / qidian / 番茄 etc.）。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents import build_scan_explorer
from app.agents.llm_factory import LLMFactory
from app.graphs.state import StoryState


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


# 默认扫榜平台（demo mock）
DEFAULT_PLATFORMS = ("fanqie", "qidian", "zongheng")


async def search_platform_node(state: StoryState, **deps: Any) -> dict:
    """锁定本次扫榜的平台列表（demo 用默认；未来按 project.platform 派单）."""
    platforms = list(state.get("platforms") or DEFAULT_PLATFORMS)
    topic = (state.get("user_input") or "").strip() or state.get("scan_topic") or "都市悬疑"
    stages = _push_stage(state, "search_platform", notes=f"platforms={platforms}")
    return {
        "platforms": platforms,
        "scan_topic": topic,
        "stages": stages,
    }


async def collect_results_node(state: StoryState, **deps: Any) -> dict:
    """采集（mock）。

    每个平台返回 ~3 条结果：title / author / rank / genre / hot_index。
    """
    import random

    topic = state.get("scan_topic") or "都市悬疑"
    rng = random.Random(hash(topic))
    results: list[dict] = []
    for plat in state.get("platforms") or DEFAULT_PLATFORMS:
        for i in range(3):
            results.append(
                {
                    "platform": plat,
                    "rank": i + 1,
                    "title": f"{topic} · 样例 {rng.randint(100, 999)}",
                    "author": f"作者{rng.randint(1000, 9999)}",
                    "genre": topic,
                    "hot_index": rng.randint(50, 100),
                    "wordcount": rng.choice([30000, 80000, 150000, 300000]),
                }
            )
    stages = _complete_stage(state, "search_platform")
    stages = stages + [
        {
            "name": "collect_results",
            "status": "running",
            "started_at": _now(),
            "notes": f"collected={len(results)} rows",
        }
    ]
    return {"scan_results": results, "stages": stages}


async def summarize_report_node(state: StoryState, **deps: Any) -> dict:
    """调 scan_explorer 生成 markdown 摘要."""
    factory: LLMFactory = deps["llm_factory"]
    agent = build_scan_explorer(factory)
    payload = {
        "topic": state.get("scan_topic"),
        "platforms": state.get("platforms"),
        "results": state.get("scan_results", []),
    }
    msg = await agent.summarize(payload)
    report = (msg.content or "").strip()

    stages = _complete_stage(state, "collect_results")
    stages = stages + [
        {
            "name": "summarize_report",
            "status": "running",
            "started_at": _now(),
            "notes": f"report_len={len(report)}",
        }
    ]
    return {"scan_report": report, "stages": stages}


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