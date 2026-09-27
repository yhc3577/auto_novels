"""TrackingService — 唯一的单事务多表写入入口。

铁律：
- chapters + chapter_records 必须在同一事务里 upsert（保证一致性）
- 返回 state_revision 给 graph 节点写回 StoryState
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chapter import ChapterRecordRepository, ChapterRepository
from app.services.wordcount import WordcountService


@dataclass
class ChapterTransaction:
    """Graph 节点 → TrackingService 的输入契约。

    LLM 产生的所有 artifact（除了 chapter_content）打包在这里，
    TrackingService 负责一次性落 2 张表。
    """

    chapter_no: int
    chapter_content: str
    chapter_title: str | None = None
    # 摘要字段（v0.2 落地）
    summary_text: str | None = None
    chapter_hook: str | None = None
    continuity_to_next: str | None = None
    open_conflicts: list[str] | None = None
    location: str | None = None
    pov: str | None = None
    emotion_arc: dict | None = None
    characters_in_scene: list[dict] | None = None
    foreshadowing_changes: list[dict] | None = None
    # 留作未来扩展（demo 不存）
    extra: dict = field(default_factory=dict)


@dataclass
class TrackingSnapshot:
    """commit 后的快照，回填 StoryState."""

    chapter_id: int
    chapter_no: int
    state_revision: int
    final_wordcount: int


class TrackingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.chapter_repo = ChapterRepository(session)
        self.record_repo = ChapterRecordRepository(session)
        self.wc = WordcountService()

    async def init(self, project_id: int) -> int:
        """返回该项目当前的 state_revision（= 已 commit 的最大 chapter_no）。

        demo 简化：state_revision == max(chapter_no)。
        """
        last = await self.chapter_repo.last_chapter_no(project_id)
        return last

    async def commit(self, project_id: int, tx: ChapterTransaction) -> TrackingSnapshot:
        """单事务写入 chapters + chapter_records。"""
        wordcount = self.wc.measure(tx.chapter_content)
        state_revision = tx.chapter_no  # 简化语义：版本号 = 章节号

        chapter = await self.chapter_repo.upsert(
            project_id=project_id,
            chapter_no=tx.chapter_no,
            content=tx.chapter_content,
            wordcount=wordcount,
            title=tx.chapter_title,
            state_revision=state_revision,
        )

        record = await self.record_repo.upsert(
            project_id=project_id,
            chapter_no=tx.chapter_no,
            chapter_id=chapter.id,
            summary_text=tx.summary_text,
            chapter_hook=tx.chapter_hook,
            continuity_to_next=tx.continuity_to_next,
            open_conflicts=tx.open_conflicts,
            location=tx.location,
            pov=tx.pov,
            emotion_arc=tx.emotion_arc,
            characters_in_scene=tx.characters_in_scene,
            foreshadowing_changes=tx.foreshadowing_changes,
            state_revision=state_revision,
        )

        return TrackingSnapshot(
            chapter_id=chapter.id,
            chapter_no=tx.chapter_no,
            state_revision=record.state_revision,
            final_wordcount=wordcount,
        )