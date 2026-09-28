"""ORM models — Layer 4 (持久化模型).

只映射 schema-pg-v0.1.sql + v0.2.sql 里最核心的 4 张表给 demo 用。
完整 19 张表的映射留待后续扩展。
"""

from app.models.base import Base
from app.models.chapter import Chapter
from app.models.chapter_record import ChapterRecord
from app.models.project import Project
from app.models.user import User

__all__ = ["Base", "Project", "Chapter", "ChapterRecord", "User"]