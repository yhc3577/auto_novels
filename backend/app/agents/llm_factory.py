"""LLM factory + MockChatModel.

demo 默认走 mock：返回根据 [role:xxx] 标签选择的预置 payload。
生产只需改 LLM_PROVIDER=anthropic/openai + API key。
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage

from app.config import settings


# ---------------------------------------------------------------------------
# Mock chat model
# ---------------------------------------------------------------------------


class MockChatModel(BaseChatModel):
    """根据 system prompt 里的 [role:xxx] 标签返回预置正文。

    不调任何外部 API，方便 demo 零依赖跑通。
    """

    role_payloads: dict[str, str]

    def _generate(self, messages, stop=None, **kwargs):  # pragma: no cover - sync API
        raise NotImplementedError("MockChatModel is async-only")

    async def _agenerate(self, messages, stop=None, **kwargs) -> Any:
        # 找最后一个 system message，提取 [role:xxx] tag
        role = "default"
        for m in reversed(messages):
            if getattr(m, "type", None) == "system":
                content = m.content if isinstance(m.content, str) else str(m.content)
                if "[role:" in content:
                    role = content.split("[role:", 1)[1].split("]", 1)[0].strip()
                break

        payload = self.role_payloads.get(role) or self.role_payloads.get("default", "")
        return AIMessage(content=payload)


def _default_payloads() -> dict[str, str]:
    """Mock 模式下每个 agent 的预置正文。"""
    return {
        "narrative_writer": (
            "# 第一章 · 回到雾港的夜晚\n\n"
            "列车在午夜驶入雾港站台的那一刻，江禾就知道——这座城市从没有真正忘记过他。\n\n"
            "潮湿的空气裹着咸味钻进车窗，站台上的老式钟指向凌晨两点。三年了，导师的失踪悬案像"
            "一根生锈的钉子，牢牢扎在他的记忆里。江禾提起那只黑色皮箱，沿着空旷的月台走向出口。\n\n"
            "出口处有人在等他——不是导师，是一位穿着藏青色雨衣的中年女人，递过来一把黑伞。\n\n"
            "「你来得正好，」她说，声音被雨声压得几乎听不见，「雾港最近总有不该回来的人回来。」\n\n"
            "江禾没接伞，只是看了一眼她左耳上那只小小的银环——和导师失踪前留下的最后一封信里夹着的照片一模一样。"
        ),
        "default": "（mock LLM: 没有匹配 [role] 标签，返回默认空响应）",
    }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


ProviderName = Literal["mock", "anthropic", "openai"]


class LLMFactory:
    """按 role 名分配 ChatModel。

    demo 阶段所有 role 都返回同一个 mock 实例；
    真实 LLM 切换由 `provider` 决定具体后端。
    """

    def __init__(self, provider: ProviderName, *, payloads: dict[str, str] | None = None) -> None:
        self.provider = provider
        self._mock = MockChatModel(role_payloads=payloads or _default_payloads())
        self._real: BaseChatModel | None = None

    def _real_model(self) -> BaseChatModel:
        if self._real is not None:
            return self._real
        if self.provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            self._real = ChatAnthropic(model=settings.llm_writer_model, temperature=0.8)
        elif self.provider == "openai":
            from langchain_openai import ChatOpenAI

            self._real = ChatOpenAI(model="gpt-4o-mini", temperature=0.8)
        else:
            self._real = self._mock  # mock 走 fallback
        return self._real

    def get(self, role: str = "default", *, temperature: float | None = None) -> BaseChatModel:
        """按 role 取一个 ChatModel。demo 阶段都是 mock。"""
        if self.provider == "mock":
            return self._mock
        # 真实 provider 不区分 role（demo 简化）
        return self._real_model()


@lru_cache(maxsize=1)
def get_llm_factory() -> LLMFactory:
    return LLMFactory(provider=settings.llm_provider)  # type: ignore[arg-type]