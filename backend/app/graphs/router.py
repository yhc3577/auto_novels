"""RouterGraph — 真正用 subgraph-as-node + LangGraph 条件边.

拓扑（最薄版：只有 1 个入口节点 + 条件边）：

                    intent_router
                          ↓
              ┌ _route_by_intent (Conditional) ─┐
              ▼                ▼                ▼                ▼
          write_long    write_short          scan         placeholder
          (subgraph)    (subgraph)        (subgraph)        (node)
              │                │                │                │
              └────────────────┴────────────────┘                │
                              ↓                                   ↓
                             END                                 END

关键点：
- 子图作为节点直接 add_node("write_long", build_write_long_graph())
- 状态合并由 LangGraph reducer 处理：stages 自动去重累积
- project 校验在 api/router.py 层做，state_revision 子图自己取（TrackingService.init）
- MemoryService 召回暂时不需要（write_prep_node 内 ContextService.assemble_recall 已覆盖）
"""

from __future__ import annotations

from datetime import datetime, timezone

from langgraph.graph import END, StateGraph

from app.agents import build_intent_router
from app.agents.llm_factory import LLMFactory
from app.graphs.scan import build_scan_graph
from app.graphs.state import StoryState
from app.graphs.write_long import build_write_long_graph
from app.graphs.write_short import build_write_short_graph


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


# ---------------------------------------------------------------------------
# 入口节点（唯一个）
# ---------------------------------------------------------------------------


async def intent_router_node(state: StoryState, **deps) -> dict:
    """两段式意图识别（启发式 → LLM 兜底）.

    explicit_scenario ∈ {write_long, write_short, scan} → 跳过识别。
    """
    factory: LLMFactory = deps["llm_factory"]
    explicit = state.get("explicit_scenario")
    if explicit and explicit != "auto":
        intent = explicit
    else:
        agent = build_intent_router(factory)
        intent = await agent.classify(state.get("user_input") or "")

    return {
        "intent": intent,
        "stages": [_stage("intent_router", notes=f"intent={intent}")],
    }


# ---------------------------------------------------------------------------
# placeholder 节点（unknown + 预留 intent）
# ---------------------------------------------------------------------------


_NOTICE_MAP = {
    "review":       "多视角审查（ReviewGraph）预留中，敬请期待。",
    "analyze":      "拆书（AnalyzeGraph）预留中，敬请期待。",
    "memory_query": "作者记忆查询预留中，敬请期待。",
    "deslop":       "去 AI 味（DeslopGraph）预留中，敬请期待。",
    "import_book":  "外部书导入（ImportGraph）预留中，敬请期待。",
}


async def placeholder_node(state: StoryState, **deps) -> dict:
    """兜底节点：unknown / 预留 intent 走这里."""
    intent = state.get("intent") or "unknown"
    if intent == "unknown":
        notice = (
            "无法识别你的意图。请尝试："
            "'写长篇第3章' / '写个短篇' / '扫榜' / '审查' / '拆书'。"
        )
    else:
        notice = _NOTICE_MAP.get(intent, f"{intent} 子图预留中。")
    return {
        "graph_invoked": "none",
        "supported": False,
        "notice": notice,
        "stages": [_stage("placeholder", notes=f"intent={intent} (not implemented)")],
    }


# ---------------------------------------------------------------------------
# 条件边决策函数（纯函数，易测）
# ---------------------------------------------------------------------------


def _route_by_intent(state: StoryState) -> str:
    """决策函数：返回下一个节点名."""
    intent = state.get("intent") or "unknown"
    if intent in ("write_long", "write_short", "scan"):
        return intent
    return "placeholder"


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build_router_graph():
    g = StateGraph(StoryState)

    # 唯一个入口节点
    g.add_node("intent_router", intent_router_node)

    # 分支：3 个子图作为节点 + 1 个 placeholder
    g.add_node("write_long", build_write_long_graph())
    g.add_node("write_short", build_write_short_graph())
    g.add_node("scan", build_scan_graph())
    g.add_node("placeholder", placeholder_node)

    g.set_entry_point("intent_router")

    # 条件边直接挂在入口节点上
    g.add_conditional_edges(
        "intent_router",
        _route_by_intent,
        {
            "write_long": "write_long",
            "write_short": "write_short",
            "scan": "scan",
            "placeholder": "placeholder",
        },
    )

    # 全部汇聚到 END
    g.add_edge("write_long", END)
    g.add_edge("write_short", END)
    g.add_edge("scan", END)
    g.add_edge("placeholder", END)

    return g.compile(name="router")