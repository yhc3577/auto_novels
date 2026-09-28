"""ProjectRepository — CRUD for projects 表.

user-scoped：所有查询默认按 user_id 过滤，避免跨用户访问。
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ConflictError, NotFoundError
from app.models.project import Project


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        slug: str,
        title: str,
        user_id: int,
        genre: str | None = None,
        platform: str | None = None,
    ) -> Project:
        """创建项目，必传 user_id."""
        project = Project(
            slug=slug,
            title=title,
            genre=genre,
            platform=platform,
            status="active",
            user_id=user_id,
        )
        self.session.add(project)
        try:
            await self.session.flush()
        except IntegrityError as e:
            raise ConflictError(
                f"project slug '{slug}' already exists for this user",
                details={"slug": slug, "user_id": user_id},
            ) from e
        return project

    async def get(self, project_id: int, *, user_id: int) -> Project:
        """按 project_id 取，必传 user_id——只能取到自己 owner 的项目.

        别人的项目 → 抛 NotFoundError(404)，不暴露存在性（避免 ID 枚举）。
        """
        stmt = select(Project).where(
            Project.id == project_id, Project.user_id == user_id
        )
        project = (await self.session.execute(stmt)).scalar_one_or_none()
        if project is None:
            raise NotFoundError(f"project {project_id} not found")
        return project

    async def find_by_slug(self, slug: str, *, user_id: int) -> Project | None:
        stmt = select(Project).where(
            Project.slug == slug, Project.user_id == user_id
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_for_user(
        self, *, user_id: int, limit: int = 50, offset: int = 0
    ) -> list[Project]:
        """列出 user_id 的所有项目（按 id desc）."""
        stmt = (
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def count_for_user(self, *, user_id: int) -> int:
        from sqlalchemy import func as sqlfunc

        stmt = select(sqlfunc.count(Project.id)).where(Project.user_id == user_id)
        return int((await self.session.execute(stmt)).scalar_one())