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

    # LLM
    llm_provider: Literal["mock", "anthropic", "openai"] = "mock"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    llm_writer_model: str = Field(default="claude-sonnet-4-5")

    # PG — async DSN used at runtime; sync DSN used by Alembic / init script
    pg_dsn: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/auto_novels"
    )
    pg_sync_dsn: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/auto_novels"
    )

    # API
    app_host: str = "0.0.0.0"
    app_port: int = 8082
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    # Logging
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()