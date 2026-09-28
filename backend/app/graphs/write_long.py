"""WriteGraphLong — 长篇章节写作图（4 节点精简版：设计-写作-校验-落库）.

精简后的拓扑（7 → 4 节点）：

  chapter_design (LLM)
       ↓
  pre_write_validate (服务)
       ├─ pass ──────────────────────────→ write_prose
       └─ fail + retry<MAX → chapter_design (loop)
       └─ fail + retry≥MAX → write_prose (best-effort)
       ↓
  write_prose (LLM)
       ↓
  validate_prose (合并节点：post_write + consistency + commit + interrupt)
       ├─ post_write fail + iter<MAX  → write_prose (loop，无 commit)
       ├─ post_write fail + iter≥MAX  → commit (best-effort) → END
       ├─ post_write pass + consistency low/medium → commit → END
       ├─ post_write pass + consistency high + iter<MAX → chapter_design (loop)
       └─ post_write pass + consistency high + iter≥MAX:
           ├─ LLM 推荐 human_review → commit + interrupt_pending → END
           └─ 其他推荐              → commit (best-effort) → END

节点性质：
- LLM agent (2)：chapter_design / write_prose
- 服务节点 (2)：pre_write_validate / validate_prose

闭环控制：
- MAX_PRE_WRITE_RETRIES 控制 pre_write_validate 失败时的 chapter_design 重做次数
- MAX_DESIGN_ITERATIONS 控制 validate_prose 触发 chapter_design 重做的次数

合并 validate_prose 节点内的决策矩阵：
┌────────────────────┬──────────────────┬───────┬────────────────────────────────────┐
│ post_write_check   │ consistency      │ iter  │ action                            │
├────────────────────┼──────────────────┼───────┼────────────────────────────────────┤
│ fail               │ (skipped)        │ <MAX  │ loop to write_prose (无 commit)    │
│ fail               │ (skipped)        │ >=MAX │ commit (best-effort)              │
│ pass               │ low/medium       │ any   │ commit (clean pass)               │
│ pass               │ high             │ <MAX  │ loop to chapter_design (无 commit) │
│ pass               │ high + human     │ >=MAX │ commit + interrupt_pending        │
│ pass               │ high + other     │ >=MAX │ commit (best-effort)              │
└────────────────────┴──────────────────┴───────┴────────────────────────────────────┘
"""

from __future__ import annotations

from datetime import datetime, timezone

from langgraph.graph import END, StateGraph

from app.agents import build_chapter_designer, build_narrative_writer
from app.agents.llm_factory import LLMFactory
from app.db import AsyncSession
from app.graphs.state import StoryState
from app.services.context import ContextService
from app.services.outline_pre_validator import OutlinePreValidator
from app.services.prose_post_checker import ProsePostChecker
from app.services.tracking import ChapterTransaction, TrackingService
from app.agents.prose_consistency import build_prose_consistency_checker


# ---------------------------------------------------------------------------
# 闭环控制参数
# ---------------------------------------------------------------------------

MAX_PRE_WRITE_RETRIES = 1
MAX_DESIGN_ITERATIONS = 1

_AI_MARKERS = ("综上所述", "值得注意的是", "不难发现", "总而言之")
_RECALL_LAST_N = 3


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stage(name: str, status: str = "done", notes: str | None = None) -> dict:
    s: dict = {
        "name": name,
        "status": status,
        "started_at": _now(),
        "finished_at": _now(),
    }
    if notes:
        s["notes"] = notes
    return s


# ---------------------------------------------------------------------------
# LLM agent 节点（2 个）
# ---------------------------------------------------------------------------


async def chapter_design_node(state: StoryState, **deps) -> dict:
    """LLM agent：初始化 + 召回上下文 + 章节细纲设计.

    收到 redo 信号时（design_iteration > 0 或 pre_write_retry_count > 0），
    把对应反馈注入 prompt。
    """
    session: AsyncSession = deps["session"]
    factory: LLMFactory = deps["llm_factory"]

    # --- 1) 初始化 ---
    project_id = state["project_id"]
    if not state.get("chapter_no"):
        last = await TrackingService(session).init(project_id)
        chapter_no = last + 1
    else:
        chapter_no = int(state["chapter_no"])
    target = int(state.get("target_wordcount") or 3000)
    iteration = int(state.get("design_iteration") or 0)
    pre_write_retry = int(state.get("pre_write_retry_count") or 0)

    # --- 2) 召回上下文 ---
    recall = await ContextService(session).assemble_recall(
        project_id, last_n=_RECALL_LAST_N, include_refs=True
    )

    # --- 3) 反馈注入（pre_write_validate 失败 OR validate_prose 高 severity）---
    feedback_lines: list[str] = []
    pw_report = state.get("pre_write_validation_report") or {}
    if not pw_report.get("passed"):
        feedback_lines.extend(pw_report.get("feedback") or [])
    consistency = state.get("consistency_report") or {}
    if consistency and consistency.get("severity") == "high":
        feedback_lines.extend(consistency.get("issues") or [])
        feedback_lines.append(
            f"consistency LLM 推荐: {consistency.get('recommendation')}"
        )
    feedback_section = (
        "\n# 上一轮反馈（请在细纲里修复）:\n" + "\n".join(f"- {f}" for f in feedback_lines)
        if feedback_lines
        else ""
    )

    # --- 4) LLM 设计 ---
    designer = build_chapter_designer(factory)
    prompt = (
        f"项目 {state['project_id']} · 准备写第 {chapter_no} 章（长篇）。\n"
        f"目标字数: {target} (±20%)\n"
        f"用户输入: {state.get('user_input', '')}\n"
        f"上一章钩子: {recall.get('recent_chapter_summaries', [])}\n"
        f"open conflicts: {recall.get('open_conflicts', [])}\n"
        f"作者记忆: {recall.get('author_memory', [])}\n"
        f"参考材料: {recall.get('reference_materials', [])}\n"
        f"当前重做轮次: design_iter={iteration} pre_write_retry={pre_write_retry}\n"
        f"{feedback_section}\n"
        "请输出本章的 JSON 细纲。"
    )
    outline = await designer.design(prompt)

    iter_note = f"design_iter={iteration} pre_write_retry={pre_write_retry}"
    return {
        "chapter_no": chapter_no,
        "target_wordcount": target,
        "length": "long",
        "design_iteration": iteration,
        "pre_write_retry_count": pre_write_retry,
        "recall": recall,
        "chapter_outline": outline,
        "stages": [
            _stage("route_scenario", notes=f"length=long target={target}"),
            _stage("write_prep"),
            _stage(
                "chapter_design",
                notes=(
                    f"{iter_note} beats={len(outline.get('key_beats', []))} "
                    f"chars={len(outline.get('characters_in_scene', []))}"
                ),
            ),
        ],
    }


async def write_prose_node(state: StoryState, **deps) -> dict:
    """LLM agent：根据已校验细纲 + validate_prose feedback 生成正文."""
    factory: LLMFactory = deps["llm_factory"]
    agent = build_narrative_writer(factory)
    chapter_no = int(state["chapter_no"])
    target = int(state.get("target_wordcount") or 3000)
    recall = state.get("recall") or {}
    outline = state.get("chapter_outline") or {}
    iteration = int(state.get("design_iteration") or 0)

    # 注入反馈（post_write_check + consistency）
    feedback_lines: list[str] = []
    pw_check = state.get("post_write_check_report") or {}
    if not pw_check.get("passed"):
        feedback_lines.extend(pw_check.get("feedback") or [])
    consistency = state.get("consistency_report") or {}
    if consistency and consistency.get("severity") == "high":
        feedback_lines.extend(consistency.get("issues") or [])
    feedback_section = (
        "\n【上一稿反馈，必须改进】:\n" + "\n".join(f"- {f}" for f in feedback_lines)
        if feedback_lines
        else ""
    )

    beats = outline.get("key_beats", [])
    outline_section = ""
    if outline:
        outline_section = (
            "\n【本章细纲（必须严格遵循）】:\n"
            f"- 开场钩子: {outline.get('opening_hook', '')}\n"
            f"- 关键节拍 ({len(beats)}):\n"
            + "\n".join(f"  · {b}" for b in beats)
            + f"\n- 核心冲突: {outline.get('conflict', '')}\n"
            f"- 高潮: {outline.get('climax', '')}\n"
            f"- 结尾钩子: {outline.get('closing_hook', '')}\n"
            f"- 场景: {outline.get('location', '')} · 视角: {outline.get('pov', '')}\n"
            f"- 出场人物: {', '.join(outline.get('characters_in_scene', []))}\n"
        )

    prompt = (
        f"项目 {state['project_id']} 第 {chapter_no} 章（长篇）。\n"
        f"用户输入: {state.get('user_input', '')}\n"
        f"目标字数: {target} (±20%)\n"
        f"上一章钩子: {recall.get('recent_chapter_summaries', [])}\n"
        f"参考材料: {recall.get('reference_materials', [])}\n"
        f"作者记忆: {recall.get('author_memory', [])}\n"
        f"open conflicts: {recall.get('open_conflicts', [])}\n"
        f"{outline_section}"
        f"{feedback_section}"
        "要求：严格遵循细纲；对话与动作推进节奏；结尾必须呼应 closing_hook 留出下一章悬念。"
        "请直接输出 markdown 正文。"
    )
    msg = await agent.run(prompt)
    body = (msg.content or "").strip()
    if not body.lstrip().startswith("#"):
        body = f"# 第{chapter_no}章\n\n" + body

    iter_note = "1st draft" if iteration == 0 else f"rewrite #{iteration}"
    return {
        "prose_draft": body,
        "stages": [_stage("write_prose", notes=f"{iter_note} len={len(body)}")],
    }


# ---------------------------------------------------------------------------
# 服务节点（2 个）
# ---------------------------------------------------------------------------


async def pre_write_validate_node(state: StoryState, **deps) -> dict:
    """服务节点：写正文之前对细纲本身做确定性校验（3 项检查）.

    路由点：pass → write_prose; fail + retry<MAX → chapter_design
    """
    outline = state.get("chapter_outline") or {}
    recall = state.get("recall") or {}

    report = OutlinePreValidator().validate(
        outline=outline,
        volume_outline=recall.get("volume_outline"),       # TODO: 等 schema 落地
        character_roster=recall.get("character_roster"),   # TODO: 等 schema 落地
        known_locations=recall.get("known_locations"),     # TODO: 等 schema 落地
    )

    retry = int(state.get("pre_write_retry_count") or 0)
    next_retry = retry + 1 if not report["passed"] and retry < MAX_PRE_WRITE_RETRIES else retry

    return {
        "pre_write_validation_report": report,
        "pre_write_retry_count": next_retry,
        "stages": [
            _stage(
                "pre_write_validate",
                notes=f"passed={report['passed']} issues={len(report['issues'])}",
            ),
        ],
    }


async def validate_prose_node(state: StoryState, **deps) -> dict:
    """合并节点：post_write_check (rule) + prose_consistency (LLM) + tracking_commit (DB) + interrupt.

    是整个图的"汇流点" —— 决定章节是循环重做还是落库。
    决策矩阵见模块顶部 docstring 表格。
    """
    session: AsyncSession = deps["session"]
    factory: LLMFactory = deps["llm_factory"]

    body = state.get("prose_draft") or ""
    target = int(state.get("target_wordcount") or 3000)
    iteration = int(state.get("design_iteration") or 0)

    stages: list[dict] = []

    # ===== 1) post_write_check (6 项确定性门禁) =====
    post_check = ProsePostChecker().check(
        prose=body, target_wordcount=target, ai_markers=_AI_MARKERS,
    )
    normalized = post_check.get("normalized_prose") or body
    stages.append(_stage(
        "post_write_check",
        notes=f"passed={post_check['passed']} issues={len(post_check['issues'])}",
    ))

    base: dict = {
        "post_write_check_report": post_check,
        "stages": stages,
    }
    if normalized != body:
        base["prose_draft"] = normalized

    # ===== 2) post_write fail 分支 =====
    if not post_check["passed"]:
        if iteration <= MAX_DESIGN_ITERATIONS:
            # loop to write_prose（无 commit，state 不含 chapter_id → 路由点会判别）
            base["design_iteration"] = iteration + 1
            stages.append(_stage(
                "validate_prose",
                notes=f"post_write fail → write_prose loop (iter {iteration}+1)",
            ))
            return base
        # best-effort commit
        notice = f"post_write_check 未通过 (best-effort): {post_check.get('issues', [])[:2]}"
        commit_result = await _do_commit(state, body=normalized, session=session, notice=notice)
        commit_stage = commit_result.pop("_commit_stage", None)
        if commit_stage:
            stages.append(commit_stage)
        return {**base, **commit_result}

    # ===== 3) post_write pass → prose_consistency (LLM) =====
    outline = state.get("chapter_outline") or {}
    checker = build_prose_consistency_checker(factory)
    consistency = await checker.check(outline=outline, prose=normalized)
    severity = consistency.get("severity", "low")
    recommendation = consistency.get("recommendation", "pass")
    stages.append(_stage(
        "prose_consistency",
        notes=f"deviation={consistency.get('deviation_score', 0):.2f} "
              f"severity={severity} rec={recommendation}",
    ))
    base["consistency_report"] = consistency

    # ===== 4) consistency high 分支 =====
    if severity == "high":
        if iteration <= MAX_DESIGN_ITERATIONS:
            # loop to chapter_design（无 commit）
            base["design_iteration"] = iteration + 1
            stages.append(_stage(
                "validate_prose",
                notes=f"consistency high → chapter_design loop (iter {iteration}+1)",
            ))
            return base
        # 已耗尽：best-effort commit + 可能 interrupt
        notice = (
            f"consistency severity=high deviation={consistency.get('deviation_score', 0):.2f} "
            f"LLM 推荐={recommendation} (best-effort commit)"
        )
        commit_result = await _do_commit(state, body=normalized, session=session, notice=notice)
        commit_stage = commit_result.pop("_commit_stage", None)
        if commit_stage:
            stages.append(commit_stage)
        if recommendation == "human_review":
            commit_result["interrupt_pending"] = True
            commit_result["interrupt_reason"] = notice
            stages.append(_stage("interrupt_human", notes=f"待人工审核: {notice[:60]}…"))
        return {**base, **commit_result}

    # ===== 5) clean pass → commit =====
    commit_result = await _do_commit(state, body=normalized, session=session, notice=None)
    commit_stage = commit_result.pop("_commit_stage", None)
    if commit_stage:
        stages.append(commit_stage)
    return {**base, **commit_result}


async def _do_commit(state: StoryState, *, body: str, session: AsyncSession, notice: str | None) -> dict:
    """Helper：原子 DB 事务落库（章节 + chapter_records）."""
    project_id = state["project_id"]
    chapter_no = int(state["chapter_no"])
    summary = (body[:140] + "…") if len(body) > 140 else body
    hook = body.split("\n\n")[-1][:200] if "\n\n" in body else body[:200]

    tx = ChapterTransaction(
        chapter_no=chapter_no,
        chapter_content=body,
        chapter_title=f"第{chapter_no}章",
        summary_text=summary,
        chapter_hook=hook,
        emotion_arc={"start": "neutral", "end": "tense", "intensity": "medium"},
    )
    snap = await TrackingService(session).commit(project_id, tx)
    return {
        "chapter_id": snap.chapter_id,
        "state_revision": snap.state_revision,
        "final_wordcount": snap.final_wordcount,
        "summary_text": summary,
        "chapter_hook": hook,
        "notice": notice,
        "_commit_stage": _stage(
            "tracking_commit",
            notes=f"chapter_id={snap.chapter_id} wordcount={snap.final_wordcount}"
            + (f" notice={(notice or '')[:40]}…" if notice else ""),
        ),
    }


# ---------------------------------------------------------------------------
# 条件边决策函数
# ---------------------------------------------------------------------------


def _route_after_pre_write_validate(state: StoryState) -> str:
    """pre_write_validate 后决策：pass → write_prose; fail 且未超限 → chapter_design."""
    report = state.get("pre_write_validation_report") or {}
    if report.get("passed"):
        return "write_prose"
    retry = int(state.get("pre_write_retry_count") or 0)
    if retry < MAX_PRE_WRITE_RETRIES:
        return "chapter_design"
    return "write_prose"


def _route_after_validate_prose(state: StoryState) -> str:
    """validate_prose 后决策：依据 state 决定流向.

    - chapter_id 已设置（已 commit）→ END
    - post_write fail → write_prose (loop)
    - consistency high → chapter_design (loop)
    - 其他 → END（兜底，正常不会到这里）
    """
    if state.get("chapter_id"):
        return END
    post = state.get("post_write_check_report") or {}
    cons = state.get("consistency_report") or {}
    if not post.get("passed"):
        return "write_prose"
    if cons.get("severity") == "high":
        return "chapter_design"
    return END


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build_write_long_graph():
    g = StateGraph(StoryState)

    # 4 个节点：2 LLM agent + 2 服务
    g.add_node("chapter_design", chapter_design_node)
    g.add_node("pre_write_validate", pre_write_validate_node)
    g.add_node("write_prose", write_prose_node)
    g.add_node("validate_prose", validate_prose_node)

    g.set_entry_point("chapter_design")
    g.add_edge("chapter_design", "pre_write_validate")

    # 条件边 1：pre_write_validate → write_prose / chapter_design
    g.add_conditional_edges(
        "pre_write_validate",
        _route_after_pre_write_validate,
        {
            "write_prose": "write_prose",
            "chapter_design": "chapter_design",
        },
    )

    g.add_edge("write_prose", "validate_prose")

    # 条件边 2：validate_prose → END / write_prose / chapter_design
    g.add_conditional_edges(
        "validate_prose",
        _route_after_validate_prose,
        {
            END: END,
            "write_prose": "write_prose",
            "chapter_design": "chapter_design",
        },
    )

    return g.compile(name="write_long")