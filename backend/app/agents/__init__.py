"""Agent package — 只放真正调 LLM 的 agent。纯规则 / 工具请放 app/services/ 或 app/tools/.

现有 agent（全部 ainvoke 真调用 LLM）：
- narrative_writer   章节正文生成（write_long / write_short）
- intent_router      意图识别（启发式 + LLM 兜底）
- scan_explorer      扫榜报告摘要
- chapter_designer   章节细纲设计

已下沉到 service（不再算 agent）：
- OutlineValidator   → app/services/outline_validator.py（纯规则）
"""

from app.agents.chapter_designer import ChapterDesigner, build_chapter_designer
from app.agents.intent_router import (
    HEURISTIC_RULES,
    IMPLEMENTED_INTENTS,
    INTENT_LABELS,
    IntentRouter,
    build_intent_router,
    heuristic_intent,
)
from app.agents.llm_factory import LLMFactory, get_llm_factory
from app.agents.narrative_writer import build_narrative_writer
from app.agents.prose_consistency import (
    ProseConsistencyChecker,
    build_prose_consistency_checker,
)
from app.agents.scan_explorer import ScanExplorer, build_scan_explorer

__all__ = [
    # factory
    "LLMFactory",
    "get_llm_factory",
    # 真 agent（都调 LLM）
    "build_narrative_writer",
    "build_intent_router",
    "IntentRouter",
    "ScanExplorer",
    "build_scan_explorer",
    "ChapterDesigner",
    "build_chapter_designer",
    "ProseConsistencyChecker",
    "build_prose_consistency_checker",
    # 公开常量 / 纯函数
    "heuristic_intent",
    "INTENT_LABELS",
    "IMPLEMENTED_INTENTS",
    "HEURISTIC_RULES",
]