"""Repository package — Layer 3 (数据访问).

铁律：
- 纯 CRUD，无业务规则
- 唯一可 import SQLAlchemy ORM 的层
- 不暴露给 Agent / Graph
"""

from app.repositories.chapter import ChapterRecordRepository, ChapterRepository
from app.repositories.project import ProjectRepository

__all__ = ["ProjectRepository", "ChapterRepository", "ChapterRecordRepository"]