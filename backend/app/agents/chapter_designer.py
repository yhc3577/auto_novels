"""ChapterDesigner agent — 长篇章节细纲设计.

接口约定：
- `design(prompt) -> dict`：返回结构化细纲
- 不接 session / repository / ORM —— 只通过 factory 拿到 LLM
- 输出 schema：
    {
        "opening_hook":   str,        # 开场钩子（首段抓人）
        "key_beats":      list[str],  # 关键节拍（每拍一句话，3-5 拍）
        "conflict":       str,        # 本章核心冲突
        "climax":         str,        # 高潮位置
        "closing_hook":   str,        # 结尾钩子（引出下一章）
        "characters_in_scene": list[str],  # 出场人物
        "location":       str,        # 场景地点
        "pov":            str,        # 视角人物
    }

mock 模式：返回一个固定的"雾港第 N 章"细纲，方便联调。
真实 LLM 模式：交给 LLM 按 system prompt 生成 JSON。
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.llm_factory import LLMFactory


SYSTEM_PROMPT = (
    "你是长篇网文的章节细纲设计师。\n"
    "[role:chapter_designer]\n"
    "基于【卷/书级大纲 + 世界观 + 人物卡 + 上一章钩子 + 用户输入】，"
    "为下一章产出结构化细纲（JSON）。\n"
    "要求：\n"
    "1. key_beats 至少 3 个，每个一句话，节奏清晰\n"
    "2. opening_hook 与 closing_hook 必须强（悬念/反转/情绪）\n"
    "3. characters_in_scene 必须从已有角色清单里选，不允许生造\n"
    "4. 只能输出合法 JSON，不要任何额外解释"
)


class ChapterDesigner:
    def __init__(self, factory: LLMFactory) -> None:
        self.factory = factory

    async def design(self, prompt: str) -> dict:
        llm = self.factory.get("chapter_designer", temperature=0.6)
        sys_msg = SystemMessage(content=SYSTEM_PROMPT)
        user_msg = HumanMessage(content=prompt)
        result: AIMessage = await llm.ainvoke([sys_msg, user_msg])
        text = result.content if isinstance(result.content, str) else str(result.content)
        return _parse_outline(text)


def _parse_outline(raw: str) -> dict[str, Any]:
    """尽量从 LLM 输出里抠出 JSON；抠不出就降级到 mock 骨架."""
    # mock LLM 直接返回 JSON 字符串（见 llm_factory 默认 payload）
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return _normalize(data)
    except (json.JSONDecodeError, TypeError):
        pass

    # 兜底：返回硬编码细纲（保证图不会因 LLM 格式错误崩溃）
    return _FALLBACK_OUTLINE


def _normalize(d: dict[str, Any]) -> dict[str, Any]:
    """字段补全，防止 LLM 漏字段."""
    out = dict(_FALLBACK_OUTLINE)
    for k, v in d.items():
        if k in out:
            out[k] = v
    # list 字段强制 list[str]
    for list_key in ("key_beats", "characters_in_scene"):
        if not isinstance(out[list_key], list):
            out[list_key] = [str(out[list_key])]
    return out


_FALLBACK_OUTLINE: dict[str, Any] = {
    "opening_hook": "雨夜的雾港站台，江禾提着黑色皮箱走出列车。",
    "key_beats": [
        "抵达雾港，撞见导师失踪前信中提到的银环女子",
        "前往旧公寓，发现导师留下的加密手稿",
        "与神秘势力第一次正面交锋，付出代价",
    ],
    "conflict": "追寻导师失踪真相 vs 雾港暗中势力的阻挠",
    "climax": "旧公寓中的手稿被截获，江禾负伤",
    "closing_hook": "银环女子留下半枚钥匙和一句话：'别去港区码头'。",
    "characters_in_scene": ["江禾", "银环女子", "雾港暗哨"],
    "location": "雾港旧城 · 旧公寓",
    "pov": "江禾",
}


def build_chapter_designer(factory: LLMFactory) -> ChapterDesigner:
    return ChapterDesigner(factory)


__all__ = ["ChapterDesigner", "build_chapter_designer"]