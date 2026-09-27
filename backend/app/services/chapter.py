"""ChapterService — 章节读侧业务。

写侧（commit）走 TrackingService；这里只负责查询编排。
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chapter import ChapterRecordRepository, ChapterRepository
from app.repositories.project import ProjectRepository


class ChapterService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.project_repo = ProjectRepository(session)
        self.chapter_repo = ChapterRepository(session)
        self.record_repo = ChapterRecordRepository(session)

    async def next_chapter_no(self, project_id: int) -> int:
        last = await self.chapter_repo.last_chapter_no(project_id)
        return last + 1

    async def list_with_records(self, project_id: int) -> list[dict]:
        chapters = await self.chapter_repo.list_for_project(project_id)
        out = []
        for ch in chapters:
            rec = await self.record_repo.get_by_no(project_id, ch.chapter_no)
            out.append(
                {
                    "id": ch.id,
                    "chapter_no": ch.chapter_no,
                    "title": ch.title,
                    "wordcount": ch.wordcount,
                    "state_revision": ch.state_revision,
                    "summary_text": rec.summary_text if rec else None,
                    "chapter_hook": rec.chapter_hook if rec else None,
                    "created_at": ch.created_at.isoformat(),
                }
            )
        return out