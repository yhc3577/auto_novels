"""Service package — Layer 2 (业务用例编排).

铁律：
- 唯一被 Agent / Graph 调用的层
- 事务边界在这里
- 不感知 HTTP / API schema

服务分类：
- 数据访问编排：ChapterService / TrackingService
- 上下文召回：ContextService
- 工具（确定性）：WordcountService / OutlineValidator / OutlinePreValidator / ProsePostChecker
"""

from app.services.chapter import ChapterService
from app.services.context import ContextService
from app.services.outline_pre_validator import OutlinePreValidator
from app.services.outline_validator import (
    OutlineValidator,
    extract_keywords,
    validate_outline,
)
from app.services.prose_post_checker import ProsePostChecker
from app.services.tracking import TrackingService
from app.services.wordcount import WordcountService

__all__ = [
    # 数据访问编排
    "ChapterService",
    "TrackingService",
    # 上下文召回
    "ContextService",
    # 工具（确定性，不调 LLM）
    "WordcountService",
    "OutlineValidator",
    "OutlinePreValidator",
    "ProsePostChecker",
    # 纯函数
    "extract_keywords",
    "validate_outline",
]