"""Router endpoint — 统一意图识别入口."""

from __future__ import annotations

from fastapi import APIRouter

from app.agents import get_llm_factory
from app.deps import CurrentUserDep, SessionDep
from app.graphs import get_registry
from app.repositories.project import ProjectRepository
from app.schemas.routing import RouterRequest, RouterResponse
from app.schemas.writing import StageStatus

router = APIRouter(prefix="/api/router", tags=["router"])


@router.post("", response_model=RouterResponse)
async def invoke_router(
    payload: RouterRequest, session: SessionDep, _user: CurrentUserDep
) -> RouterResponse:
    # 校验项目存在
    project = await ProjectRepository(session).get(payload.project_id)

    deps = {
        "session": session,
        "llm_factory": get_llm_factory(),
        "registry": get_registry(),
    }

    initial_state = {
        "project_id": payload.project_id,
        "user_input": payload.user_input,
        "explicit_scenario": payload.explicit_scenario or "auto",
        "stages": [],
        "errors": [],
    }

    graph = get_registry().router
    result = await graph.ainvoke(initial_state, config={"deps": deps})
    await session.commit()

    stages_raw = result.get("stages") or []
    return RouterResponse(
        intent=result.get("intent") or "unknown",
        graph_invoked=result.get("graph_invoked") or "none",
        supported=bool(result.get("supported")),
        state_revision=result.get("state_revision"),
        final_wordcount=result.get("final_wordcount"),
        stages=[StageStatus(**s) for s in stages_raw],
        payload={
            k: v
            for k, v in result.items()
            if k
            in (
                "prose_draft",
                "scan_results",
                "scan_report",
                "platforms",
                "scan_topic",
                "length",
                "chapter_no",
                "chapter_id",
                "summary_text",
                "chapter_hook",
                "wordcount_report",
                "quality_report",
            )
        },
        errors=result.get("errors") or [],
        notice=result.get("notice"),
    )