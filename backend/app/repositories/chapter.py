"""Chapter / ChapterRecord repositories — CRUD."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import NotFoundError
from app.models.chapter import Chapter
from app.models.chapter_record import ChapterRecord


class ChapterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self,
        *,
        project_id: int,
        chapter_no: int,
        content: str,
        wordcount: int,
        title: str | None = None,
        state_revision: int = 0,
    ) -> Chapter:
        """写入或更新章节正文。"""
        stmt = (
            pg_insert(Chapter)
            .values(
                project_id=project_id,
                chapter_no=chapter_no,
                title=title,
                content=content,
                wordcount=wordcount,
                state_revision=state_revision,
            )
            .on_conflict_do_update(
                index_elements=["project_id", "chapter_no"],
                set_={
                    "title": title,
                    "content": content,
                    "wordcount": wordcount,
                    "state_revision": state_revision,
                },
            )
            .returning(Chapter)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_no(self, project_id: int, chapter_no: int) -> Chapter | None:
        stmt = select(Chapter).where(
            Chapter.project_id == project_id, Chapter.chapter_no == chapter_no
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get(self, chapter_id: int) -> Chapter:
        chapter = await self.session.get(Chapter, chapter_id)
        if chapter is None:
            raise NotFoundError(f"chapter {chapter_id} not found")
        return chapter

    async def last_chapter_no(self, project_id: int) -> int:
        """返回该项目已 commit 的最大 chapter_no；0 表示没有。"""
        from sqlalchemy import func as sqlfunc

        stmt = select(sqlfunc.max(Chapter.chapter_no)).where(Chapter.project_id == project_id)
        val = (await self.session.execute(stmt)).scalar_one()
        return int(val or 0)

    async def list_for_project(self, project_id: int) -> list[Chapter]:
        stmt = (
            select(Chapter)
            .where(Chapter.project_id == project_id)
            .order_by(Chapter.chapter_no)
        )
        return list((await self.session.execute(stmt)).scalars().all())


class ChapterRecordRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self,
        *,
        project_id: int,
        chapter_no: int,
        chapter_id: int | None,
        summary_text: str | None = None,
        chapter_hook: str | None = None,
        continuity_to_next: str | None = None,
        open_conflicts: list | None = None,
        location: str | None = None,
        pov: str | None = None,
        emotion_arc: dict | None = None,
        characters_in_scene: list | None = None,
        foreshadowing_changes: list | None = None,
        state_revision: int = 0,
    ) -> ChapterRecord:
        stmt = (
            pg_insert(ChapterRecord)
            .values(
                project_id=project_id,
                chapter_no=chapter_no,
                chapter_id=chapter_id,
                summary_text=summary_text,
                chapter_hook=chapter_hook,
                continuity_to_next=continuity_to_next,
                open_conflicts=open_conflicts,
                location=location,
                pov=pov,
                emotion_arc=emotion_arc,
                characters_in_scene=characters_in_scene,
                foreshadowing_changes=foreshadowing_changes,
                state_revision=state_revision,
            )
            .on_conflict_do_update(
                index_elements=["project_id", "chapter_no"],
                set_={
                    "chapter_id": chapter_id,
                    "summary_text": summary_text,
                    "chapter_hook": chapter_hook,
                    "continuity_to_next": continuity_to_next,
                    "open_conflicts": open_conflicts,
                    "location": location,
                    "pov": pov,
                    "emotion_arc": emotion_arc,
                    "characters_in_scene": characters_in_scene,
                    "foreshadowing_changes": foreshadowing_changes,
                    "state_revision": state_revision,
                },
            )
            .returning(ChapterRecord)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_no(self, project_id: int, chapter_no: int) -> ChapterRecord | None:
        stmt = select(ChapterRecord).where(
            ChapterRecord.project_id == project_id,
            ChapterRecord.chapter_no == chapter_no,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()