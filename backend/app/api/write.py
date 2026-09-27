"""Write endpoint — 触发 WriteGraph 跑一次写章节流."""

from __future__ import annotations

from fastapi import APIRouter

from app.agents import get_llm_factory
from app.deps import SessionDep
from app.graphs import build_write_graph
from app.repositories.project import ProjectRepository
from app.schemas.writing import StageStatus, WriteRequest, WriteResponse

router = APIRouter(prefix="/api/write", tags=["write"])


@router.post("", response_model=WriteResponse)
async def write_chapter(payload: WriteRequest, session: SessionDep) -> WriteResponse:
    # 校验项目存在
    project = await ProjectRepository(session).get(payload.project_id)

    # 准备 deps（铁律：graph 不直接 import repository / models）
    deps = {
        "session": session,
        "llm_factory": get_llm_factory(),
    }

    initial_state = {
        "project_id": payload.project_id,
        "chapter_no": payload.chapter_no,
        "user_input": payload.user_input,
        "target_wordcount": payload.target_wordcount,
        "stages": [],
        "errors": [],
    }

    graph = build_write_graph()
    result = await graph.ainvoke(initial_state, config={"deps": deps})

    # 路由层统一 commit
    await session.commit()

    stages_raw = result.get("stages") or []
    return WriteResponse(
        project_id=project.id,
        chapter_no=int(result.get("chapter_no") or 0),
        chapter_id=result.get("chapter_id"),
        state_revision=int(result.get("state_revision") or 0),
        final_wordcount=result.get("final_wordcount"),
        stages=[StageStatus(**s) for s in stages_raw],
        chapter_hook=result.get("chapter_hook"),
        summary_text=result.get("summary_text"),
        errors=result.get("errors") or [],
    )