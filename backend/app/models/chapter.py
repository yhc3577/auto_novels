"""Chapter ORM — 对应 chapters 表（章节正文 + 元数据）。"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.project import Project


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chapter_no: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(256))
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    wordcount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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

    project: Mapped["Project"] = relationship(back_populates="chapters")

    __table_args__ = (
        # 同一项目下 chapter_no 唯一
        # 注：依赖 schema-pg-v0.1.sql 已建立 idx_chapters_project_no 索引
        # 实际唯一约束若需要可在 schema 补丁里加；这里由 service 层保证。
    )