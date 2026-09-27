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