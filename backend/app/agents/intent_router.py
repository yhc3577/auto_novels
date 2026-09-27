"""IntentRouter agent — 启发式 + LLM 兜底的两段式意图识别.

对外暴露：
- INTENT_LABELS（标签全集，含预留位）
- HEURISTIC_RULES（关键词表）
- IntentRouter.classify(text) -> str
- heuristic_intent(text) -> str  (纯函数，便于测试)
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_factory import LLMFactory


# ---------------------------------------------------------------------------
# 标签 + 启发式规则（公开常量，便于测试和文档化）
# ---------------------------------------------------------------------------


# 当前已实现 + 未来预留（review / analyze / memory_query / deslop / import）
INTENT_LABELS: tuple[str, ...] = (
    # 已实现
    "write_long",    # 长篇章节写作
    "write_short",   # 短篇写作
    "scan",          # 扫榜
    # 预留（Router 会识别但返回 not_implemented）
    "review",        # 多视角审查（ReviewGraph 未来）
    "analyze",       # 拆书（AnalyzeGraph 未来）
    "memory_query",  # 记忆查询
    "deslop",        # 去 AI 味（DeslopGraph 未来）
    "import_book",   # 导入外部书（ImportGraph 未来）
    # 兜底
    "unknown",
)

IMPLEMENTED_INTENTS: frozenset[str] = frozenset({"write_long", "write_short", "scan"})

HEURISTIC_RULES: tuple[tuple[str, str], ...] = (
    # --- write_long ---
    ("写长篇",     "write_long"),
    ("长篇章节",   "write_long"),
    ("长篇",       "write_long"),
    ("继续写",     "write_long"),
    ("写第",       "write_long"),
    ("开书",       "write_long"),
    ("open_book",  "write_long"),
    # --- write_short ---
    ("写短篇",     "write_short"),
    ("短篇",       "write_short"),
    ("一个短故事", "write_short"),
    ("短故事",     "write_short"),
    ("short",      "write_short"),
    # --- scan ---
    ("扫榜",       "scan"),
    ("扫一下",     "scan"),
    ("扫描",       "scan"),
    ("scan",       "scan"),
    # --- review ---
    ("审查",       "review"),
    ("review",     "review"),
    # --- analyze ---
    ("拆书",       "analyze"),
    ("拆",         "analyze"),
    ("analyze",    "analyze"),
    # --- memory_query ---
    ("回忆",       "memory_query"),
    ("现在写到",   "memory_query"),
)


def heuristic_intent(text: str) -> str:
    """纯函数版：substr 匹配关键词，按规则顺序返回首个命中标签."""
    text = (text or "").lower()
    for kw, label in HEURISTIC_RULES:
        if kw in text:
            return label
    return "unknown"


SYSTEM_PROMPT = (
    "你是意图路由器。把用户输入归类为以下之一：\n"
    + ", ".join(INTENT_LABELS)
    + "\n只输出标签，不要任何解释。"
)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class IntentRouter:
    """封装启发式 + LLM 兜底."""

    def __init__(self, factory: LLMFactory) -> None:
        self.factory = factory

    async def classify(self, user_input: str) -> str:
        # 第一段：启发式
        label = heuristic_intent(user_input)
        if label != "unknown":
            return label

        # 第二段：LLM 兜底
        llm = self.factory.get("intent_router", temperature=0.0)
        sys_msg = SystemMessage(content=SYSTEM_PROMPT)
        user_msg = HumanMessage(content=(user_input or "").strip() or "(empty)")
        result = await llm.ainvoke([sys_msg, user_msg])
        text = result.content if isinstance(result.content, str) else str(result.content)
        # 取响应里第一个出现的已知 label
        return next(
            (lbl for lbl in INTENT_LABELS if lbl in text.lower()),
            "unknown",
        )


def build_intent_router(factory: LLMFactory) -> IntentRouter:
    return IntentRouter(factory)