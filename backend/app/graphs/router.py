"""RouterGraph — 主分发图（§3.1）.

  intent_router      ← 启发式 + LLM 兜底
    └─► project_lookup    ← TrackingService.check
    └─► author_memory     ← MemoryService.query (预留 hook)
    └─► dispatch          ← conditional: write_long / write_short / scan / 预留位
    └─► END

设计原则：
- RouterGraph 自己 dispatch（不交给 API 层），符合"主 agent 分发"语义
- 已实现 intent：write_long / write_short / scan → 调对应子图
- 预留 intent：review / analyze / memory_query / deslop / import_book → 返回 not_implemented
- unknown → 兜底，提示用户澄清
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents import build_intent_router
from app.agents.llm_factory import LLMFactory
from app.agents import IMPLEMENTED_INTENTS
from app.db import AsyncSession
from app.graphs.state import StoryState
from app.services.tracking import TrackingService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _push_stage(state: StoryState, name: str, *, notes: str | None = None) -> list:
    stages = list(state.get("stages") or [])
    entry: dict = {"name": name, "status": "running", "started_at": _now()}
    if notes:
        entry["notes"] = notes
    stages.append(entry)
    return stages


def _complete_stage(stages: list, name: str, status: str = "done") -> list:
    for s in reversed(stages):
        if s["name"] == name and s["status"] == "running":
            s["status"] = status
            s["finished_at"] = _now()
            break
    return stages


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


async def intent_router_node(state: StoryState, **deps: Any) -> dict:
    """两段式意图识别：启发式 → LLM 兜底.

    显式 scenario（explicit_scenario ∈ write_long/write_short/scan）跳过识别.
    """
    factory: LLMFactory = deps["llm_factory"]
    explicit = state.get("explicit_scenario")
    if explicit and explicit != "auto":
        intent = explicit
    else:
        agent = build_intent_router(factory)
        intent = await agent.classify(state.get("user_input") or "")

    stages = _push_stage(state, "intent_router", notes=f"intent={intent}")
    return {
        "intent": intent,
        "stages": stages,
    }


async def project_lookup_node(state: StoryState, **deps: Any) -> dict:
    """TrackingService.check → state_revision 同步."""
    session: AsyncSession = deps["session"]
    project_id = state["project_id"]
    snap = await TrackingService(session).check(project_id)
    stages = _complete_stage(state.get("stages") or [], "intent_router")
    stages = stages + [
        {
            "name": "project_lookup",
            "status": "running",
            "started_at": _now(),
            "notes": f"state_revision={snap.state_revision}",
        }
    ]
    return {
        "state_revision": snap.state_revision,
        "stages": stages,
    }


async def author_memory_node(state: StoryState, **deps: Any) -> dict:
    """预留：调 MemoryService 召回作者记忆。demo 阶段 empty OK."""
    stages = _complete_stage(state.get("stages") or [], "project_lookup")
    stages = stages + [
        {
            "name": "author_memory",
            "status": "skipped",
            "started_at": _now(),
            "finished_at": _now(),
            "notes": "MemoryService not yet wired in demo",
        }
    ]
    return {"stages": stages}


async def dispatch_node(state: StoryState, **deps: Any) -> dict:
    """主分发节点：调对应子图（write_long / write_short / scan）或返回 not_implemented."""
    intent = state.get("intent") or "unknown"
    registry = deps["registry"]
    stages = _complete_stage(state.get("stages") or [], "author_memory")
    stages = stages + [
        {"name": "dispatch", "status": "running", "started_at": _now(), "notes": f"intent={intent}"}
    ]

    # 1) 未识别 → 兜底
    if intent == "unknown" or intent not in (
        "write_long", "write_short", "scan",
        "review", "analyze", "memory_query", "deslop", "import_book",
    ):
        stages = _complete_stage(stages, "dispatch", status="done")
        return {
            "graph_invoked": "none",
            "supported": False,
            "notice": "无法识别你的意图。请尝试：'写长篇第3章' / '写个短篇' / '扫榜' / '审查' / '拆书'。",
            "stages": stages,
        }

    # 2) 已实现的子图 → 调对应图（共用 StoryState，deps 透传）
    if intent in IMPLEMENTED_INTENTS:
        subgraph = getattr(registry, intent)  # write_long / write_short / scan
        # 准备子图初始 state：去掉显式 scenario 字段（避免子图误用）
        sub_state = dict(state)
        sub_state.pop("explicit_scenario", None)
        sub_state["stages"] = []  # 子图重置 stages
        try:
            sub_result = await subgraph.ainvoke(
                sub_state,
                config={"deps": deps},
            )
        except Exception as e:  # pragma: no cover - infra error path
            stages = _complete_stage(stages, "dispatch", status="failed")
            return {
                "graph_invoked": intent,
                "supported": True,
                "errors": [f"subgraph_failed: {type(e).__name__}: {e}"],
                "stages": stages,
            }
        # 合并：子图结果 + dispatcher 上下文
        merged = dict(sub_result)
        merged["graph_invoked"] = intent
        merged["supported"] = True
        merged["notice"] = None
        # stages 拼接
        merged["stages"] = stages + (sub_result.get("stages") or [])
        return merged

    # 3) 预留子图 → not_implemented 占位
    notice_map = {
        "review":       "多视角审查（ReviewGraph）预留中，敬请期待。",
        "analyze":      "拆书（AnalyzeGraph）预留中，敬请期待。",
        "memory_query": "作者记忆查询预留中，敬请期待。",
        "deslop":       "去 AI 味（DeslopGraph）预留中，敬请期待。",
        "import_book":  "外部书导入（ImportGraph）预留中，敬请期待。",
    }
    stages = _complete_stage(stages, "dispatch", status="done")
    return {
        "graph_invoked": intent,
        "supported": False,
        "notice": notice_map.get(intent, f"{intent} 子图预留中。"),
        "stages": stages,
    }


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build_router_graph():
    g = StateGraph(StoryState)
    g.add_node("intent_router", intent_router_node)
    g.add_node("project_lookup", project_lookup_node)
    g.add_node("author_memory", author_memory_node)
    g.add_node("dispatch", dispatch_node)

    g.set_entry_point("intent_router")
    g.add_edge("intent_router", "project_lookup")
    g.add_edge("project_lookup", "author_memory")
    g.add_edge("author_memory", "dispatch")
    g.add_edge("dispatch", END)

    return g.compile(name="router")