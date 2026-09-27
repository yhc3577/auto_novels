"""Narrative writer agent — 唯一负责生成正文的 agent（demo 阶段）.

接口约定：
- `run(prompt) -> AIMessage`（LangChain 原生）
- 不接收 session / repository / ORM — 只通过 factory 拿到 LLM
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.llm_factory import LLMFactory

SYSTEM_PROMPT = (
    "你是一位网文写手。\n"
    "[role:narrative_writer]\n"
    "请基于用户提供的项目信息、章节上下文、目标字数，输出 markdown 格式的章节正文。\n"
    "风格要求：网文质感、章节钩子强、对话与动作推进节奏。"
)


class NarrativeWriter:
    def __init__(self, factory: LLMFactory) -> None:
        self.factory = factory

    async def run(self, prompt: str) -> AIMessage:
        llm = self.factory.get("narrative_writer", temperature=0.8)
        sys_msg = SystemMessage(content=SYSTEM_PROMPT)
        user_msg = HumanMessage(content=prompt)
        return await llm.ainvoke([sys_msg, user_msg])


def build_narrative_writer(factory: LLMFactory) -> NarrativeWriter:
    return NarrativeWriter(factory)