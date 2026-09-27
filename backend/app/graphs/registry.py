"""GraphRegistry — 单例 + 懒加载 + 预留扩展位.

当前实现：router / write_long / write_short / scan
预留位：review / analyze / deslop / import（raise NotImplementedError，但接口已注册）

调用方用法：
    registry = get_registry()
    graph = registry.write_long          # property 触发编译
    result = await graph.ainvoke(state, config={"deps": deps})
"""

from __future__ import annotations

from functools import lru_cache

from app.graphs.router import build_router_graph
from app.graphs.scan import build_scan_graph
from app.graphs.write_long import build_write_long_graph
from app.graphs.write_short import build_write_short_graph


class _ReservedSubgraph(NotImplementedError):
    """预留子图访问时抛错，便于上层做降级."""


class GraphRegistry:
    def __init__(self) -> None:
        self._router: object | None = None
        self._write_long: object | None = None
        self._write_short: object | None = None
        self._scan: object | None = None

    # --- 已实现 ---

    @property
    def router(self):
        if self._router is None:
            self._router = build_router_graph()
        return self._router

    @property
    def write_long(self):
        if self._write_long is None:
            self._write_long = build_write_long_graph()
        return self._write_long

    @property
    def write_short(self):
        if self._write_short is None:
            self._write_short = build_write_short_graph()
        return self._write_short

    @property
    def scan(self):
        if self._scan is None:
            self._scan = build_scan_graph()
        return self._scan

    # --- 预留位（接口存在，实现 TODO）---

    @property
    def review(self):  # pragma: no cover - reserved
        raise _ReservedSubgraph(
            "review subgraph is reserved for future expansion "
            "(multi-perspective review, see docs/langgraph-status-v0.1.md §6)"
        )

    @property
    def analyze(self):  # pragma: no cover - reserved
        raise _ReservedSubgraph(
            "analyze subgraph is reserved for future expansion "
            "(long/short book deconstruction, see docs/langgraph-status-v0.1.md §6)"
        )

    @property
    def deslop(self):  # pragma: no cover - reserved
        raise _ReservedSubgraph(
            "deslop subgraph is reserved for future expansion "
            "(7-gate AI-flavor removal)"
        )

    @property
    def import_book(self):  # pragma: no cover - reserved
        raise _ReservedSubgraph(
            "import_book subgraph is reserved for future expansion "
            "(external book import, see docs/langgraph-status-v0.1.md §7.3)"
        )


@lru_cache(maxsize=1)
def get_registry() -> GraphRegistry:
    return GraphRegistry()


__all__ = ["GraphRegistry", "get_registry"]