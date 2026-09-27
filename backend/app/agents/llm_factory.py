"""LLM factory + MockChatModel.

demo 默认走 mock：返回根据 [role:xxx] 标签选择的预置 payload。

切真 LLM 一行 env：
- LLM_PROVIDER=anthropic  →  ChatAnthropic（直连 Anthropic）
- LLM_PROVIDER=openai     →  ChatOpenAI（直连 OpenAI）
- LLM_PROVIDER=newapi     →  ChatOpenAI 通过 NewAPI 网关（OpenAI 兼容协议）

NewAPI 网关说明：
- 兼容 OpenAI Chat Completions 协议
- 配置 NEWAPI_BASE_URL（如 https://your-newapi-domain/v1）+ NEWAPI_API_KEY（网关发的 key）
- 模型名按 NewAPI 约定，通常是 "<provider>/<model>" 格式
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
    """根据 system prompt 里的 [role:xxx] 标签返回预置正文.

    不调任何外部 API，方便 demo 零依赖跑通。
    """

    role_payloads: dict[str, str]

    @property
    def _llm_type(self) -> str:
        # langchain-core 0.3+ 要求子类实现 _llm_type
        return "mock"

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
        # langchain 1.x 要求返回 ChatResult，包含 .generations: list[ChatGeneration]
        from langchain_core.outputs import ChatGeneration, ChatResult
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=payload))])


def _default_payloads() -> dict[str, str]:
    """Mock 模式下每个 agent 的预置正文."""
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
        "narrative_writer_short": (
            "# 雾港短篇 · 雨夜寄件人\n\n"
            "雨从下午四点开始下。邮局柜台后，老周把当天的最后一份包裹单推过来，地址一栏写着「雾港旧城3号」。\n\n"
            "三年前那场大火之后，旧城3号就不存在了。\n\n"
            "老周没说话，把包裹放进身后的储物格。等他回过头时，柜台前已经没人，只有一把湿透的黑伞斜靠在椅背上。"
        ),
        "intent_router": "write_long",
        "scan_explorer": (
            "# 扫榜报告（mock）\n\n"
            "## fanqie 平台\n"
            "- 《雾港来客》近 7 日热度 +18%\n"
            "- 同题材共 12 本在榜，前 5 占据 70% 阅读量\n\n"
            "## qidian 平台\n"
            "- 都市悬疑类稳居分类榜 TOP3\n"
            "- 短篇（< 5 万字）窗口打开\n\n"
            "## 建议\n"
            "1. 雾港题材可继续深挖，建议加入更多地点细节\n"
            "2. 短篇窗口期可考虑同步发布\n"
            "3. 钩子密度可参考 TOP3 同类作品的第 1 章结尾"
        ),
        "chapter_designer": (
            "{"
            "\"opening_hook\": \"雨夜的雾港站台，江禾提着黑色皮箱走出列车。\","
            "\"key_beats\": ["
            "\"抵达雾港，撞见导师失踪前信中提到的银环女子\","
            "\"前往旧公寓，发现导师留下的加密手稿\","
            "\"与神秘势力第一次正面交锋，付出代价\""
            "],"
            "\"conflict\": \"追寻导师失踪真相 vs 雾港暗中势力的阻挠\","
            "\"climax\": \"旧公寓中的手稿被截获，江禾负伤\","
            "\"closing_hook\": \"银环女子留下半枚钥匙和一句话：'别去港区码头'。\","
            "\"characters_in_scene\": [\"江禾\", \"银环女子\", \"雾港暗哨\"],"
            "\"location\": \"雾港旧城 · 旧公寓\","
            "\"pov\": \"江禾\""
            "}"
        ),
        "prose_consistency": (
            "{"
            "\"deviation_score\": 0.0,"
            "\"severity\": \"low\","
            "\"issues\": [],"
            "\"recommendation\": \"pass\""
            "}"
        ),
        "default": "（mock LLM: 没有匹配 [role] 标签，返回默认空响应）",
    }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


ProviderName = Literal["mock", "anthropic", "openai", "newapi"]


class LLMFactory:
    """按 role 名分配 ChatModel.

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
            self._real = ChatAnthropic(
                model=settings.llm_writer_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                anthropic_api_key=settings.anthropic_api_key,
            )

        elif self.provider == "openai":
            from langchain_openai import ChatOpenAI
            self._real = ChatOpenAI(
                model=settings.llm_writer_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                api_key=settings.openai_api_key,
            )

        elif self.provider == "newapi":
            # NewAPI 网关：OpenAI 兼容协议 → 用 ChatOpenAI + 自定义 base_url
            from langchain_openai import ChatOpenAI
            if not settings.newapi_base_url:
                raise ValueError(
                    "LLM_PROVIDER=newapi 时必须设置 NEWAPI_BASE_URL"
                )
            if not settings.newapi_api_key:
                raise ValueError(
                    "LLM_PROVIDER=newapi 时必须设置 NEWAPI_API_KEY"
                )
            self._real = ChatOpenAI(
                model=settings.llm_writer_model,         # 如 "anthropic/claude-sonnet-4-5" 或 "MiniMax-M3"
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,       # reasoning 模型需要 ≥ 4000
                base_url=settings.newapi_base_url,        # 如 "https://your-newapi-domain/v1"
                api_key=settings.newapi_api_key,         # NewAPI 网关签发的 key
                # 透传 default_headers 给某些 NewAPI 部署需要带额外 header 的场景
                default_headers={"X-Source": "auto_novels"},
            )

        else:
            # mock / 未知 provider → 走 mock
            self._real = self._mock

        return self._real

    def get(self, role: str = "default", *, temperature: float | None = None) -> BaseChatModel:
        """按 role 取一个 ChatModel.

        - mock：返回 MockChatModel（内部按 [role:xxx] tag 分流）
        - 真 provider：返回对应后端（demo 阶段所有 role 共用同一实例）
        """
        if self.provider == "mock":
            return self._mock
        # 真实 provider：不区分 role（demo 简化），未来可按 role 拆不同模型
        return self._real_model()


@lru_cache(maxsize=1)
def get_llm_factory() -> LLMFactory:
    return LLMFactory(provider=settings.llm_provider)  # type: ignore[arg-type]