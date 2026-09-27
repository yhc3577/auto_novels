"""ProseConsistencyChecker — LLM 轻校验 agent.

职责：对比【本章细纲】和【章节正文】，判断正文是否兑现了细纲的剧情承诺。
这是 write_long 图中第三个 LLM 节点（其它两个是 chapter_designer / narrative_writer）。

输出 schema（mock 模式直接返回低风险放行）：
{
    "deviation_score":  0.0~1.0,        # 0=完全一致, 1=完全跑题
    "severity":         "low"|"medium"|"high",
    "issues":           list[str],       # 具体偏离点
    "recommendation":   "pass"|"redo"|"human_review",
    "rationale":        str,             # LLM 给出的判断理由（demo: 可选）
}

调用方式（跟 narrative_writer 一致）：
    factory = LLMFactory(provider="mock")
    agent = ProseConsistencyChecker(factory)
    report = await agent.check(outline=outline, prose=prose)
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.llm_factory import LLMFactory


SYSTEM_PROMPT = (
    "你是章节一致性审查员（lightweight judge）。\n"
    "[role:prose_consistency]\n"
    "对比【本章细纲 beats】和【章节正文】，判断正文是否兑现了细纲的剧情承诺。\n"
    "输出 JSON：\n"
    "{\n"
    '  "deviation_score": 0.0~1.0,  // 0=完全一致, 1=完全跑题\n'
    '  "severity":        "low"|"medium"|"high",\n'
    '  "issues":          [str, ...],   // 具体偏离点\n'
    '  "recommendation":  "pass"|"redo"|"human_review"\n'
    "}\n"
    "阈值（建议）：\n"
    "- low:    deviation < 0.3 → pass\n"
    "- medium: 0.3~0.6     → pass（放行，事后人工 review）\n"
    "- high:   > 0.6        → 看类型：剧情未兑现→redo；纯风格/人设问题→human_review\n"
    "只输出合法 JSON，不要任何额外解释。"
)


_FALLBACK: dict[str, Any] = {
    "deviation_score": 0.0,
    "severity": "low",
    "issues": [],
    "recommendation": "pass",
    "rationale": "（LLM 解析失败，降级放行）",
}


class ProseConsistencyChecker:
    def __init__(self, factory: LLMFactory) -> None:
        self.factory = factory

    async def check(self, *, outline: dict, prose: str) -> dict[str, Any]:
        llm = self.factory.get("prose_consistency", temperature=0.2)
        # 正文截断到 3000 字避免 prompt 过长（demo 简化）
        truncated_prose = prose[:3000] + ("\n...(truncated)" if len(prose) > 3000 else "")
        user_payload = json.dumps(
            {"outline": outline, "prose": truncated_prose},
            ensure_ascii=False,
            indent=2,
        )
        sys_msg = SystemMessage(content=SYSTEM_PROMPT)
        user_msg = HumanMessage(content=user_payload)
        result: AIMessage = await llm.ainvoke([sys_msg, user_msg])
        text = result.content if isinstance(result.content, str) else str(result.content)
        return self._parse(text)

    def _parse(self, text: str) -> dict[str, Any]:
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return dict(_FALLBACK)

        out = dict(_FALLBACK)
        for k in ("deviation_score", "severity", "issues", "recommendation", "rationale"):
            if k in data:
                out[k] = data[k]
        # 类型归一
        if not isinstance(out["issues"], list):
            out["issues"] = [str(out["issues"])]
        try:
            out["deviation_score"] = float(out["deviation_score"])
        except (TypeError, ValueError):
            out["deviation_score"] = 0.0
        if out["severity"] not in ("low", "medium", "high"):
            out["severity"] = "low"
        if out["recommendation"] not in ("pass", "redo", "human_review"):
            out["recommendation"] = "pass"
        return out


def build_prose_consistency_checker(factory: LLMFactory) -> ProseConsistencyChecker:
    return ProseConsistencyChecker(factory)


__all__ = ["ProseConsistencyChecker", "build_prose_consistency_checker"]