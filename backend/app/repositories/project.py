"""ProjectRepository — CRUD for projects 表."""

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
        genre: str | None = None,
        platform: str | None = None,
    ) -> Project:
        project = Project(
            slug=slug,
            title=title,
            genre=genre,
            platform=platform,
            status="active",
        )
        self.session.add(project)
        try:
            await self.session.flush()
        except IntegrityError as e:
            raise ConflictError(
                f"project slug '{slug}' already exists",
                details={"slug": slug},
            ) from e
        return project

    async def get(self, project_id: int) -> Project:
        project = await self.session.get(Project, project_id)
        if project is None:
            raise NotFoundError(f"project {project_id} not found")
        return project

    async def find_by_slug(self, slug: str) -> Project | None:
        stmt = select(Project).where(Project.slug == slug)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[Project]:
        stmt = (
            select(Project)
            .order_by(Project.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def count(self) -> int:
        from sqlalchemy import func as sqlfunc

        stmt = select(sqlfunc.count(Project.id))
        return int((await self.session.execute(stmt)).scalar_one())