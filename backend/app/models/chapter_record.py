"""ChapterRecord ORM — 对应 chapter_records 表（v0.2 落地的摘要/钩子表）。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ChapterRecord(Base):
    __tablename__ = "chapter_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chapter_no: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    chapter_id: Mapped[int | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL")
    )
    summary_text: Mapped[str | None] = mapped_column(Text)
    chapter_hook: Mapped[str | None] = mapped_column(Text)
    continuity_to_next: Mapped[str | None] = mapped_column(Text)
    open_conflicts: Mapped[list | None] = mapped_column(JSONB)
    location: Mapped[str | None] = mapped_column(String(128))
    pov: Mapped[str | None] = mapped_column(String(32))
    emotion_arc: Mapped[dict | None] = mapped_column(JSONB)
    characters_in_scene: Mapped[list | None] = mapped_column(JSONB)
    foreshadowing_changes: Mapped[list | None] = mapped_column(JSONB)
    state_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )