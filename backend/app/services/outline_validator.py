"""OutlineValidator tool — 校验正文是否兑现了章节细纲.

工具性质：
- 不调任何 LLM，纯规则（substring 匹配 + 字数检查）
- 图节点直接调用：`OutlineValidator().validate(...)`
- 跟 WordcountService 同性质 —— 放在 services/ 而非 agents/

接口约定：
- `validate(outline, prose, target_wordcount) -> dict`：返回校验报告
- 输出 schema：
    {
        "passed":  bool,        # 是否通过
        "score":   float,       # 0~1 综合得分
        "feedback": list[str],   # 给写手的修改建议（重写时塞回 prompt）
        "checks": {
            "opening_hook_hit":   bool,
            "key_beats_coverage": float,   # 0~1, key_beats 中被覆盖比例
            "closing_hook_hit":   bool,
            "length_ok":          bool,
        },
    }

策略（demo 简化版）：
- 关键节拍覆盖：每个 beat 在正文中是否出现核心关键词（substring 子串匹配）
- 钩子命中：opening_hook / closing_hook 的前 8 字是否在正文相应位置出现
- 字数：复用 WordcountService.checkpoint

后续可扩展：接 LLM-as-judge 作可选升级，但默认走规则（速度快、可解释）。

模块级工具函数：
- extract_keywords       —— LangChain @tool
- validate_outline       —— LangChain @tool
两者都可用 `bind_tools([...])` 交给 LLM agent 调用。
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.tools import tool

from app.services.wordcount import WordcountService


@dataclass
class ValidationCheck:
    opening_hook_hit: bool
    key_beats_coverage: float
    closing_hook_hit: bool
    length_ok: bool


class OutlineValidator:
    """规则驱动的细纲一致性校验器（demo 阶段）."""

    # 钩子前后缀长度（substring 模糊匹配，避免 LLM 改写后失效）
    HOOK_PREFIX_LEN = 8

    def __init__(self) -> None:
        self.wc = WordcountService()

    def validate(
        self,
        *,
        outline: dict,
        prose: str,
        target_wordcount: int,
        tolerance: float = 0.2,
    ) -> dict:
        if not outline or not prose:
            return self._fail("细纲或正文为空")

        checks = ValidationCheck(
            opening_hook_hit=self._hook_hit(outline.get("opening_hook", ""), prose, region="head"),
            key_beats_coverage=self._beats_coverage(outline.get("key_beats", []), prose),
            closing_hook_hit=self._hook_hit(outline.get("closing_hook", ""), prose, region="tail"),
            length_ok=self._length_ok(prose, target_wordcount, tolerance),
        )

        # 综合得分（加权平均）
        score = (
            (1.0 if checks.opening_hook_hit else 0.0) * 0.25
            + checks.key_beats_coverage * 0.35
            + (1.0 if checks.closing_hook_hit else 0.0) * 0.25
            + (1.0 if checks.length_ok else 0.0) * 0.15
        )
        passed = score >= 0.7  # demo 阈值：≥ 70% 算通过

        feedback: list[str] = []
        if not checks.opening_hook_hit:
            feedback.append("开场钩子未体现：建议首段直接呼应细纲的 opening_hook 前半句。")
        if checks.key_beats_coverage < 1.0:
            miss = int(round((1 - checks.key_beats_coverage) * len(outline.get("key_beats", []))))
            feedback.append(f"key_beats 覆盖率 {checks.key_beats_coverage:.0%}，至少 {miss} 个节拍未兑现。")
        if not checks.closing_hook_hit:
            feedback.append("结尾钩子缺失：末段必须呼应 closing_hook。")
        if not checks.length_ok:
            feedback.append(f"字数偏离目标 ±{int(tolerance*100)}%，需要扩写或精简。")

        return {
            "passed": passed,
            "score": round(score, 3),
            "feedback": feedback,
            "checks": {
                "opening_hook_hit": checks.opening_hook_hit,
                "key_beats_coverage": round(checks.key_beats_coverage, 3),
                "closing_hook_hit": checks.closing_hook_hit,
                "length_ok": checks.length_ok,
            },
        }

    # ------------------------------------------------------------------
    # 内部规则
    # ------------------------------------------------------------------

    def _hook_hit(self, hook: str, prose: str, *, region: str) -> bool:
        """粗略判断：hook 的前 N 字是否出现在 prose 的 head/tail 区域."""
        if not hook:
            return True  # 没有要求就视为通过
        needle = hook.strip()[: self.HOOK_PREFIX_LEN]
        if len(needle) < 2:
            return True
        if region == "head":
            window = prose[: max(200, len(needle) * 4)]
        else:  # tail
            window = prose[-max(200, len(needle) * 4) :]
        return needle in window

    def _beats_coverage(self, beats: list[str], prose: str) -> float:
        """每个 beat 提取核心 2~N 字子串，命中率 = 命中 beat 数 / 总 beat 数."""
        if not beats:
            return 1.0
        hits = 0
        for beat in beats:
            # 使用 _impl_extract_keywords 快速路径（不走 @tool.invoke 的开铺）
            keywords = _impl_extract_keywords(beat)
            if any(kw in prose for kw in keywords):
                hits += 1
        return hits / len(beats)

    def _length_ok(self, prose: str, target: int, tolerance: float) -> bool:
        if target <= 0:
            return True
        report = self.wc.checkpoint(prose, target, tolerance=tolerance)
        return report["passed"]

    def _fail(self, reason: str) -> dict:
        return {
            "passed": False,
            "score": 0.0,
            "feedback": [reason],
            "checks": {
                "opening_hook_hit": False,
                "key_beats_coverage": 0.0,
                "closing_hook_hit": False,
                "length_ok": False,
            },
        }


# ---------------------------------------------------------------------------
# 模块级 LangChain @tool（让 LLM agent 可以 bind_tools 调用）
# ---------------------------------------------------------------------------
#
# 约定：
# - 私有函数 _impl_* 走原 Python 函数路径（快，供内部代码调用）
# - @tool 装饰的公开名供 agent bind_tools().invoke(...) 使用
# - 两套实现都委托同一份 impl，保证结果一致
# ---------------------------------------------------------------------------


def _impl_extract_keywords(beat: str) -> list[str]:
    """私实现：拆出所有连续中文 run，再从每个 run 生成 ≥2 字子串。

    返回所有子串（set 去重），开销极低（典型 beat 产生几十个子串）。
    """
    if not beat:
        return []

    runs: list[str] = []
    buf: list[str] = []
    for ch in beat:
        if "\u4e00" <= ch <= "\u9fff":
            buf.append(ch)
        else:
            if len(buf) >= 2:
                runs.append("".join(buf))
            buf = []
    if len(buf) >= 2:
        runs.append("".join(buf))

    keywords: set[str] = set()
    for run in runs:
        for i in range(len(run)):
            for j in range(i + 2, len(run) + 1):
                keywords.add(run[i:j])

    return sorted(keywords, key=len, reverse=True)


@tool
def extract_keywords(beat: str) -> list[str]:
    """从一句 beat 里抠出所有 ≥2 字的连续中文子串，可用于在 prose 里做 fuzzy 匹配.

    Args:
        beat: 章节细纲的一句话（任意中文文本）。

    Returns:
        list[str]: 该句产生的全部可能子串（按长度倒序），不包含 ASCII / 1 字词。
    """
    return _impl_extract_keywords(beat)


@tool
def validate_outline(
    outline: dict,
    prose: str,
    target_wordcount: int,
    tolerance: float = 0.2,
) -> dict:
    """对【细纲 × 正文】运行 4 项一致性检查：开场钩子命中 + 关键节拍覆盖 + 结尾钩子命中 + 字数。

    Args:
        outline: 章节细纲 dict，至少包含 opening_hook / key_beats / closing_hook。
        prose: 章节正文（markdown）。
        target_wordcount: 目标字数（与 ±tolerance 一起决定 length_ok）。
        tolerance: 字数容差比例，默认 0.2（20%）。

    Returns:
        dict 含 5 个字段：
            - passed (bool): 综合是否通过 (score >= 0.7)
            - score (float): 0~1 综合得分
            - feedback (list[str]): 未通过项的修改建议
            - checks (dict): 每项检查的详细结果
    """
    return OutlineValidator().validate(
        outline=outline,
        prose=prose,
        target_wordcount=target_wordcount,
        tolerance=tolerance,
    )


__all__ = [
    "OutlineValidator",
    "extract_keywords",
    "validate_outline",
]