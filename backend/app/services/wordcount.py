"""WordcountService — CJK 友好的字数统计。

纯函数风格，不需要 session（因此可不放进 service 也能复用）。
为了统一分层，仍放在 service 包内。

模块级 @tool：
- measure_wordcount    —— LangChain @tool，agent 可 bind_tools
- checkpoint_wordcount —— LangChain @tool，agent 可 bind_tools
"""

from __future__ import annotations

import re

from langchain_core.tools import tool


_CJK_CHAR = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
_ASCII_WORD = re.compile(r"[A-Za-z0-9_]+")


class WordcountService:
    """字数计量：CJK 按字、英文按词。"""

    def measure(self, text: str) -> int:
        if not text:
            return 0
        cjk = len(_CJK_CHAR.findall(text))
        ascii_words = len(_ASCII_WORD.findall(text))
        return cjk + ascii_words

    def checkpoint(self, text: str, target: int, *, tolerance: float = 0.2) -> dict:
        """返回 {actual, target, passed, ratio}.  within ±tolerance 视为通过."""
        actual = self.measure(text)
        if target <= 0:
            return {"actual": actual, "target": 0, "passed": True, "ratio": None}
        ratio = actual / target
        passed = abs(ratio - 1.0) <= tolerance
        return {
            "actual": actual,
            "target": target,
            "passed": passed,
            "ratio": round(ratio, 3),
        }


# ---------------------------------------------------------------------------
# LangChain @tool 公开版（供 LLM agent bind_tools 调用）
# ---------------------------------------------------------------------------


@tool
def measure_wordcount(text: str) -> int:
    """计量文本字数（CJK 按字、英文按词、混合求和）。

    Args:
        text: 任意文本字符串。

    Returns:
        int: 字数（空文本返回 0）。
    """
    return WordcountService().measure(text)


@tool
def checkpoint_wordcount(text: str, target: int, tolerance: float = 0.2) -> dict:
    """检查文本字数是否落在【目标 ±】 区间内。

    Args:
        text: 待检查的文本。
        target: 目标字数。
        tolerance: 容差比例，默认 0.2（20%）。

    Returns:
        dict 含 4 个字段：actual (int) / target (int) / passed (bool) / ratio (float|None)。
    """
    return WordcountService().checkpoint(text, target, tolerance=tolerance)


__all__ = [
    "WordcountService",
    "measure_wordcount",
    "checkpoint_wordcount",
]