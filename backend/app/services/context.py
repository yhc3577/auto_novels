"""ContextService — 长篇章节写作的上下文召回.

职责：
- 给 narrative_writer / chapter_designer 喂"上一章钩子 + 参考材料 + 作者记忆 + 冲突清单"
- demo 阶段：返回最小骨架结构，让图能跑通

⚠️ 真正的"召回"涉及：
    1. 从 chapter_records 表里读 last_n 章 summary_text / chapter_hook
    2. 从 project_refs 表里读 reference_materials
    3. 从 author_memory 表里读作者风格/设定偏好
    4. 聚合 open_conflicts / foreshadowing_changes

TODO：等 DB schema 加完对应表后，把这些 repo 注入并实现真正的查询。
当前 stub 保证 state 字段稳定，agent 不会因 KeyError 崩溃。
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class ContextService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def assemble_recall(
        self,
        project_id: int,
        *,
        last_n: int = 3,
        include_refs: bool = True,
    ) -> dict:
        """召回写作上下文. demo 阶段返回固定骨架."""
        # TODO: 替换为真实查询
        #   recent = await self.chapter_repo.recent(project_id, n=last_n)
        #   refs   = await self.ref_repo.list(project_id) if include_refs else []
        return {
            "recent_chapter_summaries": [],   # list[str] · 最近 last_n 章 summary
            "reference_materials":     [],   # list[dict] · 用户上传的参考
            "author_memory":           [],   # list[str] · 作者风格偏好
            "open_conflicts":          [],   # list[str] · 待解决的冲突
            "worldview":               {},   # dict · 世界观设定（TODO）
            "book_outline":            {},   # dict · 书级大纲（TODO）
            "character_roster":        [],   # list[dict] · 人物卡（TODO）
        }


__all__ = ["ContextService"]