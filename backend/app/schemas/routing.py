"""Router DTO — 统一意图识别入口的请求/响应."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.writing import StageStatus

Scenario = Literal["auto", "write_long", "write_short", "scan"]


class RouterRequest(BaseModel):
    """统一入口：自动识别意图或显式指定."""

    project_id: int = Field(gt=0)
    user_input: str = Field(min_length=1, max_length=2000)
    explicit_scenario: Scenario | None = Field(
        default="auto",
        description="auto = 跑意图识别；write_long/write_short/scan = 跳过识别直接 dispatch",
    )


class RouterResponse(BaseModel):
    """意图识别 + 分发结果."""

    intent: str = Field(description="识别/指定的意图，如 write_long")
    graph_invoked: str = Field(description="实际调用的子图名，如 write_long")
    supported: bool = Field(description="该 intent 当前是否已实现")
    state_revision: int | None = None
    final_wordcount: int | None = None
    stages: list[StageStatus] = []
    payload: dict = Field(default_factory=dict, description="子图原始返回")
    errors: list[str] = []
    notice: str | None = Field(
        default=None,
        description="对预留 intent 的友好提示（如 '此功能开发中'）",
    )