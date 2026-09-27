"""Write endpoint — 显式调 write_long 图（保留 /api/write 作为长篇直入口）.

新代码推荐用 /api/router（自动识别 + 分发）。
/api/write 保留以便客户端显式调长篇，语义不变。
"""

from __future__ import annotations

from fastapi import APIRouter

from app.agents import get_llm_factory
from app.deps import SessionDep
from app.graphs import get_registry
from app.repositories.project import ProjectRepository
from app.schemas.writing import StageStatus, WriteRequest, WriteResponse

router = APIRouter(prefix="/api/write", tags=["write"])


@router.post("", response_model=WriteResponse)
async def write_chapter(payload: WriteRequest, session: SessionDep) -> WriteResponse:
    project = await ProjectRepository(session).get(payload.project_id)

    deps = {
        "session": session,
        "llm_factory": get_llm_factory(),
        "registry": get_registry(),
    }

    initial_state = {
        "project_id": payload.project_id,
        "chapter_no": payload.chapter_no,
        "user_input": payload.user_input,
        "target_wordcount": payload.target_wordcount,
        "explicit_scenario": "write_long",
        "stages": [],
        "errors": [],
    }

    graph = get_registry().write_long
    result = await graph.ainvoke(initial_state, config={"deps": deps})
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