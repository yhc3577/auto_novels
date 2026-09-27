"""ScanExplorer agent — 扫榜结果摘要.

demo 阶段：基于 collect_results 的 mock 数据生成 markdown 摘要报告。
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.llm_factory import LLMFactory

SYSTEM_PROMPT = (
    "你是扫榜分析师。\n"
    "[role:scan_explorer]\n"
    "基于给出的扫榜原始数据，输出 markdown 摘要报告：\n"
    "- 每个平台 1-3 个关键观察\n"
    "- 题材热度排序\n"
    "- 给作者的建议（不超过 3 条）"
)


class ScanExplorer:
    def __init__(self, factory: LLMFactory) -> None:
        self.factory = factory

    async def summarize(self, payload: dict) -> AIMessage:
        import json

        llm = self.factory.get("scan_explorer", temperature=0.5)
        sys_msg = SystemMessage(content=SYSTEM_PROMPT)
        user_msg = HumanMessage(content=json.dumps(payload, ensure_ascii=False, indent=2))
        return await llm.ainvoke([sys_msg, user_msg])


def build_scan_explorer(factory: LLMFactory) -> ScanExplorer:
    return ScanExplorer(factory)