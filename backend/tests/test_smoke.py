"""Smoke tests — wordcount + iron rule."""

from __future__ import annotations

import ast
from pathlib import Path

from app.services.wordcount import WordcountService


# ---------------------------------------------------------------------------
# WordcountService
# ---------------------------------------------------------------------------


def test_wordcount_cjk():
    wc = WordcountService()
    text = "回到雾港的夜晚"  # 7 个汉字
    assert wc.measure(text) == 7


def test_wordcount_ascii():
    wc = WordcountService()
    assert wc.measure("hello world foo") == 3


def test_wordcount_mixed():
    wc = WordcountService()
    # 4 个汉字 + 2 个 ASCII 词
    assert wc.measure("雾港 hello 夜 world") == 6


def test_wordcount_checkpoint_passed():
    wc = WordcountService()
    text = "啊" * 100  # 100 字
    r = wc.checkpoint(text, target=100, tolerance=0.2)
    assert r["passed"] is True
    assert r["actual"] == 100


def test_wordcount_checkpoint_failed():
    wc = WordcountService()
    text = "啊" * 50
    r = wc.checkpoint(text, target=100, tolerance=0.2)
    assert r["passed"] is False


# ---------------------------------------------------------------------------
# Iron rule: agents / graphs 不能 import repository / models
# ---------------------------------------------------------------------------


def _imports_from(path: Path, *, file_suffix: str = ".py") -> set[str]:
    """AST 扫描：提取 `from app.X import Y` 的 X 模块前缀."""
    imports: set[str] = set()
    for py in path.rglob(f"*{file_suffix}"):
        if "__pycache__" in py.parts:
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("app."):
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