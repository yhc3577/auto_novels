"""ProsePostChecker — 写正文之后的确定性质量门禁（不调 LLM）.

6 项检查：
1. wordcount      — 字数是否在目标 ±20% 内
2. punctuation    — 全/半角标点归一（副作用：返回归一后的正文）
3. ai_patterns    — substring 扫 AI 词标记
4. degeneration   — 句子级 n-gram 重复检测
5. banned_words   — 禁用词扫描
6. length_floor   — 过短保护（< 100 字视为不合格）

返回 report schema：
{
    "passed":          bool,
    "issues":          list[str],
    "feedback":        list[str],   # 退回 write_prose 时注入 prompt
    "normalized_prose": str,        # 标点归一后的正文（如果无变化则等于原 prose）
    "checks": {
        <name>: {"passed": bool, ...}
    }
}
"""

from __future__ import annotations

import re
from collections import Counter

from langchain_core.tools import tool

from app.services.wordcount import WordcountService


# AI 词标记白名单（demo 简化版）
_AI_MARKERS: tuple[str, ...] = (
    "综上所述",
    "值得注意的是",
    "不难发现",
    "总而言之",
    "首先...其次...再次",
)

# 标点归一对照表（中文 → ASCII）
_PUNCT_PAIRS: tuple[tuple[str, str], ...] = (
    ("，", ","), ("。", "."), ("；", ";"),
    ("？", "?"), ("！", "!"), ("：", ":"),
    ("「", '"'), ("」", '"'),
    ("『", '"'), ("』", '"'),
)

_LENGTH_FLOOR = 100  # < 100 字视为不合格


class ProsePostChecker:
    """确定性质量门禁（不调 LLM，纯规则）."""

    def __init__(self, *, banned_words: list[str] | None = None) -> None:
        self.banned_words = banned_words or []
        self.wc = WordcountService()

    def check(
        self,
        *,
        prose: str,
        target_wordcount: int,
        ai_markers: tuple[str, ...] | None = None,
    ) -> dict:
        issues: list[str] = []
        feedback: list[str] = []
        ai_markers = ai_markers or _AI_MARKERS

        checks: dict = {}

        # --- 1) 标点归一（必须先做，后续检查基于归一后正文）---
        normalized, punct_changes = self._normalize_punctuation(prose)
        checks["punctuation"] = {
            "passed": True,
            "changes": len(punct_changes),
            "details": ", ".join(punct_changes[:3]) if punct_changes else "无需归一",
        }

        body = normalized

        # --- 2) 字数 ---
        actual = self.wc.measure(body)
        if target_wordcount > 0:
            wc_passed = abs(actual - target_wordcount) <= target_wordcount * 0.2
        else:
            wc_passed = actual >= _LENGTH_FLOOR
        checks["wordcount"] = {
            "passed": wc_passed,
            "actual": actual,
            "target": target_wordcount,
        }
        if not wc_passed:
            issues.append(
                f"字数 {actual} 偏离目标 {target_wordcount} ±20%"
            )
            feedback.append("扩写或精简，使字数落在目标 ±20% 区间内。")

        # --- 3) 长度下限 ---
        floor_passed = actual >= _LENGTH_FLOOR
        checks["length_floor"] = {
            "passed": floor_passed,
            "actual": actual,
            "floor": _LENGTH_FLOOR,
        }
        if not floor_passed:
            issues.append(f"正文过短（{actual} < {_LENGTH_FLOOR}）")

        # --- 4) AI 词 ---
        ai_hits = [kw for kw in ai_markers if kw in body]
        checks["ai_patterns"] = {
            "passed": len(ai_hits) == 0,
            "hits": ai_hits,
        }
        if ai_hits:
            issues.append(f"AI 词标记命中 {len(ai_hits)} 处：{ai_hits}")
            feedback.append("改写或删除 AI 套话：{}".format("、".join(ai_hits)))

        # --- 5) 退化检测（句子级 4-gram 重复率）---
        deg_score = self._detect_degeneration(body)
        deg_passed = deg_score < 0.3
        checks["degeneration"] = {
            "passed": deg_passed,
            "score": round(deg_score, 3),
        }
        if not deg_passed:
            issues.append(f"退化检测异常（重复度 {deg_score:.2f}）")
            feedback.append("避免重复句式和相同 n-gram 堆叠。")

        # --- 6) 禁用词 ---
        banned_hits = [w for w in self.banned_words if w in body]
        checks["banned_words"] = {
            "passed": len(banned_hits) == 0,
            "hits": banned_hits,
        }
        if banned_hits:
            issues.append(f"命中禁用词 {len(banned_hits)} 个：{banned_hits}")
            feedback.append(f"替换或删除禁用词：{banned_hits}")

        passed = all(c["passed"] for c in checks.values())
        return {
            "passed": passed,
            "issues": issues,
            "feedback": feedback,
            "checks": checks,
            "normalized_prose": normalized,
        }

    # ------------------------------------------------------------------
    # 内部规则
    # ------------------------------------------------------------------

    def _normalize_punctuation(self, prose: str) -> tuple[str, list[str]]:
        """全角标点 → 半角，返回 (normalized, 改动列表)."""
        changes: list[str] = []
        out = prose
        for full, half in _PUNCT_PAIRS:
            if full in out:
                count = out.count(full)
                changes.append(f"{full}→{half} ×{count}")
                out = out.replace(full, half)
        return out, changes

    def _detect_degeneration(self, prose: str) -> float:
        """句子级 4-gram 重复率（标点归一后的半角分隔符都算）."""
        # 标点归一后用半角分隔符切句
        sentences = re.split(r"[,。！？;\n]+", prose)
        sentences = [s.strip() for s in sentences if len(s.strip()) >= 5]
        if len(sentences) < 4:
            return 0.0
        n = 4
        ngrams: list[str] = []
        for s in sentences:
            chars = list(s)
            for i in range(len(chars) - n + 1):
                ngrams.append("".join(chars[i: i + n]))
        if not ngrams:
            return 0.0
        counter = Counter(ngrams)
        repeated = sum(c - 1 for c in counter.values() if c > 1)
        return repeated / len(ngrams)


__all__ = ["ProsePostChecker", "check_prose_post_write"]


# ---------------------------------------------------------------------------
# LangChain @tool 公开版（供 LLM agent bind_tools 调用）
# ---------------------------------------------------------------------------


@tool
def check_prose_post_write(
    prose: str,
    target_wordcount: int,
    ai_markers: list[str] | None = None,
    banned_words: list[str] | None = None,
) -> dict:
    """对【章节正文】运行 6 项写后确定性门禁：字数 + 标点归一 + AI 词 + 退化 + 禁用词 + 长度下限。

    Args:
        prose: 章节正文 markdown。
        target_wordcount: 目标字数（实际字数 ±20% 视为通过）。
        ai_markers: AI 词标记列表（可选，默认 4 个常见 AI 套话）。
        banned_words: 禁用词列表（可选，默认空）。

    Returns:
        dict 含 5 个字段：
            - passed (bool): 6 项检查是否全部通过
            - issues (list[str]): 问题清单
            - feedback (list[str]): 退回 write_prose 时注入 prompt 的反馈
            - checks (dict): 每项检查的详细结果
            - normalized_prose (str): 标点归一后的正文（如果无变化则等于原 prose）
    """
    checker = ProsePostChecker(banned_words=banned_words)
    return checker.check(
        prose=prose,
        target_wordcount=target_wordcount,
        ai_markers=tuple(ai_markers) if ai_markers else None,
    )