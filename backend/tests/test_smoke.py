"""Tests for intent router + iron rule."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.agents import (
    HEURISTIC_RULES,
    IMPLEMENTED_INTENTS,
    INTENT_LABELS,
    heuristic_intent,
)
from app.graphs.router import _route_by_intent
from app.graphs.state import _append_unique_stages
from app.services.wordcount import WordcountService


# ---------------------------------------------------------------------------
# WordcountService
# ---------------------------------------------------------------------------


def test_wordcount_cjk():
    wc = WordcountService()
    assert wc.measure("回到雾港的夜晚") == 7


def test_wordcount_ascii():
    wc = WordcountService()
    assert wc.measure("hello world foo") == 3


def test_wordcount_mixed():
    wc = WordcountService()
    assert wc.measure("雾港 hello 夜 world") == 6


def test_wordcount_checkpoint_passed():
    wc = WordcountService()
    r = wc.checkpoint("啊" * 100, target=100, tolerance=0.2)
    assert r["passed"] is True


def test_wordcount_checkpoint_failed():
    wc = WordcountService()
    r = wc.checkpoint("啊" * 50, target=100, tolerance=0.2)
    assert r["passed"] is False


# ---------------------------------------------------------------------------
# Intent router — 启发式
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        # 长篇
        ("写长篇第3章", "write_long"),
        ("继续写", "write_long"),
        ("开书", "write_long"),
        ("写第5章", "write_long"),
        # 短篇
        ("写个短篇", "write_short"),
        ("一个短故事", "write_short"),
        # 扫榜
        ("扫榜", "scan"),
        ("扫一下悬疑题材", "scan"),
        # 审查
        ("审查一下", "review"),
        # 拆书
        ("拆书", "analyze"),
        # 兜底
        ("hello", "unknown"),
        ("", "unknown"),
    ],
)
def test_heuristic_intent(text, expected):
    assert heuristic_intent(text) == expected


def test_intent_labels_contain_implemented():
    """已实现的 intent 必须是 INTENT_LABELS 的子集."""
    for intent in IMPLEMENTED_INTENTS:
        assert intent in INTENT_LABELS


def test_implemented_intents_match_dispatch_targets():
    """dispatch 节点分发的三个意图必须都已实现."""
    assert IMPLEMENTED_INTENTS == frozenset({"write_long", "write_short", "scan"})


# ---------------------------------------------------------------------------
# stages reducer（_append_unique_stages）单测
# ---------------------------------------------------------------------------


def test_append_unique_stages_first_event():
    """初始状态为空：首次 add 一个 event."""
    result = _append_unique_stages([], [{"name": "a", "started_at": "t1"}])
    assert result == [{"name": "a", "started_at": "t1"}]


def test_append_unique_stages_dedup():
    """同名同 started_at → 去重."""
    old = [{"name": "a", "started_at": "t1", "status": "running"}]
    new = [{"name": "a", "started_at": "t1", "status": "done"}]
    result = _append_unique_stages(old, new)
    # 重复 event 只保留旧的（第一次写入优先）
    assert len(result) == 1
    assert result[0]["status"] == "running"


def test_append_unique_stages_different_time_appended():
    """同名不同时间 → 追加."""
    old = [{"name": "a", "started_at": "t1"}]
    new = [{"name": "a", "started_at": "t2"}]
    result = _append_unique_stages(old, new)
    assert len(result) == 2


def test_append_unique_stages_different_name_appended():
    """不同名 → 追加."""
    old = [{"name": "a", "started_at": "t1"}]
    new = [{"name": "b", "started_at": "t1"}]
    result = _append_unique_stages(old, new)
    assert len(result) == 2


def test_append_unique_stages_subgraph_pattern():
    """核心场景：父 stages + 子图累积（含父 stages 副本）→ 不重复."""
    parent_stages = [
        {"name": "intent_router", "started_at": "t1"},
        {"name": "project_lookup", "started_at": "t2"},
        {"name": "author_memory", "started_at": "t3"},
    ]
    # 子图作为节点：返回的 stages 包含父 stages 副本 + 子图新 events
    subgraph_return = parent_stages + [
        {"name": "route_scenario", "started_at": "t4"},
        {"name": "write_prose", "started_at": "t5"},
    ]
    merged = _append_unique_stages(parent_stages, subgraph_return)
    # 父 stages 不重复
    assert len(merged) == 5
    names = [s["name"] for s in merged]
    assert names == [
        "intent_router",
        "project_lookup",
        "author_memory",
        "route_scenario",
        "write_prose",
    ]


def test_append_unique_stages_skips_non_dict():
    """非 dict 元素直接追加，不报错."""
    result = _append_unique_stages([{"a": 1}], ["string", 42])
    assert result == [{"a": 1}, "string", 42]


# ---------------------------------------------------------------------------
# RouterGraph 条件边决策函数 _route_by_intent
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "intent,expected_target",
    [
        ("write_long",    "write_long"),
        ("write_short",   "write_short"),
        ("scan",          "scan"),
        # 预留 intent → placeholder
        ("review",        "placeholder"),
        ("analyze",       "placeholder"),
        ("memory_query",  "placeholder"),
        ("deslop",        "placeholder"),
        ("import_book",   "placeholder"),
        # 兜底
        ("unknown",       "placeholder"),
        ("",              "placeholder"),
    ],
)
def test_route_by_intent(intent, expected_target):
    state = {"intent": intent}
    assert _route_by_intent(state) == expected_target


def test_route_by_intent_missing_intent():
    """state 完全没 intent 字段 → placeholder."""
    assert _route_by_intent({}) == "placeholder"


# ---------------------------------------------------------------------------
# Iron rule
# ---------------------------------------------------------------------------


def _imports_from(path: Path) -> set[str]:
    imports: set[str] = set()
    for py in path.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app."):
                imports.add(node.module)
    return imports


def test_iron_rule_agents_do_not_import_repository_or_models():
    agents = Path(__file__).resolve().parents[1] / "app" / "agents"
    imports = _imports_from(agents)
    forbidden = {m for m in imports if m.startswith("app.repositories") or m.startswith("app.models")}
    assert not forbidden, f"agents 严禁 import repository/models: {forbidden}"


def test_iron_rule_graphs_do_not_import_repository_or_models():
    graphs = Path(__file__).resolve().parents[1] / "app" / "graphs"
    imports = _imports_from(graphs)
    forbidden = {m for m in imports if m.startswith("app.repositories") or m.startswith("app.models")}
    assert not forbidden, f"graphs 严禁 import repository/models: {forbidden}"