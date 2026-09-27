"""Project endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import select

from app.deps import SessionDep
from app.models.chapter import Chapter
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectOut

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _to_out(p, chapter_count: int) -> ProjectOut:
    return ProjectOut(
        id=p.id,
        slug=p.slug,
        title=p.title,
        genre=p.genre,
        platform=p.platform,
        status=p.status,
        created_at=p.created_at,
        updated_at=p.updated_at,
        chapter_count=chapter_count,
    )


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, session: SessionDep) -> ProjectOut:
    repo = ProjectRepository(session)
    project = await repo.create(
        slug=payload.slug,
        title=payload.title,
        genre=payload.genre,
        platform=payload.platform,
    )
    await session.flush()
    return _to_out(project, chapter_count=0)


@router.get("", response_model=list[ProjectOut])
async def list_projects(session: SessionDep, limit: int = 50, offset: int = 0) -> list[ProjectOut]:
    repo = ProjectRepository(session)
    projects = await repo.list_all(limit=limit, offset=offset)
    # 批量查每个项目的章节数
    if not projects:
        return []
    from sqlalchemy import func as sqlfunc

    stmt = (
        select(Chapter.project_id, sqlfunc.count(Chapter.id))
        .where(Chapter.project_id.in_([p.id for p in projects]))
        .group_by(Chapter.project_id)
    )
    rows = dict((await session.execute(stmt)).all())
    return [_to_out(p, chapter_count=rows.get(p.id, 0)) for p in projects]


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, session: SessionDep) -> ProjectOut:
    repo = ProjectRepository(session)
    project = await repo.get(project_id)
    from sqlalchemy import func as sqlfunc

    stmt = select(sqlfunc.count(Chapter.id)).where(Chapter.project_id == project_id)
    count = int((await session.execute(stmt)).scalar_one())
    return _to_out(project, chapter_count=count)