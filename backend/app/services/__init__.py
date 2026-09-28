"""Service package — Layer 2 (业务用例编排).

铁律：
- 唯一被 Agent / Graph 调用的层
- 事务边界在这里
- 不感知 HTTP / API schema

服务分类：
- 数据访问编排：ChapterService / TrackingService
- 上下文召回：ContextService
- 工具（确定性，不调 LLM）：
    - 类 API：WordcountService / OutlineValidator / OutlinePreValidator / ProsePostChecker
    - LangChain @tool：measure_wordcount / checkpoint_wordcount /
      extract_keywords / validate_outline / validate_outline_pre_write /
      check_prose_post_write
"""

from app.services.chapter import ChapterService
from app.services.context import ContextService
from app.services.outline_pre_validator import (
    OutlinePreValidator,
    validate_outline_pre_write,
)
from app.services.outline_validator import (
    OutlineValidator,
    extract_keywords,
    validate_outline,
)
from app.services.prose_post_checker import ProsePostChecker, check_prose_post_write
from app.services.tracking import TrackingService
from app.services.wordcount import (
    WordcountService,
    checkpoint_wordcount,
    measure_wordcount,
)

__all__ = [
    # 数据访问编排
    "ChapterService",
    "TrackingService",
    # 上下文召回
    "ContextService",
    # 工具类 API（供 graph 节点直接调用）
    "WordcountService",
    "OutlineValidator",
    "OutlinePreValidator",
    "ProsePostChecker",
    # LangChain @tool（供 agent bind_tools / .invoke()）
    "measure_wordcount",
    "checkpoint_wordcount",
    "extract_keywords",
    "validate_outline",
    "validate_outline_pre_write",
    "check_prose_post_write",
]