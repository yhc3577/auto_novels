"""Agent package — 横向层，只调 Service，不感知 ORM."""

from app.agents.llm_factory import LLMFactory, get_llm_factory
from app.agents.narrative_writer import build_narrative_writer

__all__ = ["LLMFactory", "get_llm_factory", "build_narrative_writer"]