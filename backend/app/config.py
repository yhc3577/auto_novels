"""Settings — pydantic-settings with env file support."""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- LLM -----
    # provider 取值：mock | anthropic | openai | newapi
    llm_provider: Literal["mock", "anthropic", "openai", "newapi"] = "mock"

    # 直连 Anthropic / OpenAI
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    # NewAPI 网关（OpenAI 兼容协议）
    # 典型 base_url 形如：https://your-newapi-domain/v1
    # key 是 NewAPI 网关自己签发的，不是上游 provider 的 key
    newapi_base_url: str | None = None
    newapi_api_key: str | None = None

    # 模型名（demo 阶段所有 role 共用一个，production 可按 role 拆分）
    # NewAPI 下模型名通常是 "<provider>/<model>"，如 "anthropic/claude-sonnet-4-5"
    llm_writer_model: str = Field(default="claude-sonnet-4-5")
    llm_temperature: float = Field(default=0.8, ge=0.0, le=2.0)

    # reasoning 模型（如 MiniMax-M3、DeepSeek-R1）需要更大预算，否则正文被 token budget 截断
    # 4000 是经验值：reasoning + 正文 1500 中文字 刚刚好
    llm_max_tokens: int = Field(default=4000, ge=256)

    # ----- PG -----
    pg_dsn: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/auto_novels"
    )
    pg_sync_dsn: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/auto_novels"
    )

    # ----- API -----
    app_host: str = "0.0.0.0"
    app_port: int = 8082
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    # ----- Logging -----
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()