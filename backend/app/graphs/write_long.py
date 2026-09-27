"""WriteGraphLong — 长篇章节写作图（6 节点设计-写作-校验 闭环）.

完整拓扑：

  chapter_design (LLM)
       ↓
  pre_write_validate (服务节点，确定性)
       ├─ pass ─────────────────────────────→ write_prose
       └─ fail + retry<MAX → chapter_design  (循环)
       └─ fail + retry≥MAX → write_prose    (best-effort)
       ↓
  write_prose (LLM)
       ↓
  post_write_check (服务节点，确定性 6 项门禁)
       ├─ pass ─────────────────────────────→ prose_consistency
       └─ fail + retry<MAX → write_prose    (循环)
       └─ fail + retry≥MAX → prose_consistency (best-effort)
       ↓
  prose_consistency (LLM 轻校验)
       ├─ low/medium severity ──────────────→ tracking_commit
       └─ high severity:
           ├─ design_iteration < MAX → chapter_design (full redo)
           └─ design_iteration ≥ MAX:
               ├─ LLM 推荐 human_review → interrupt_human → END
               └─ LLM 推荐 redo (但已耗尽) → tracking_commit (best-effort)
       ↓
  tracking_commit (服务节点，原子 DB 事务)
       ↓
       END

节点性质：
- LLM agent (3)：chapter_design / write_prose / prose_consistency
- 服务节点 (4)：pre_write_validate / post_write_check / tracking_commit / interrupt_human

闭环控制：
- MAX_PRE_WRITE_RETRIES  控制 pre_write_validate 失败时的 chapter_design 重做次数
- MAX_DESIGN_ITERATIONS  控制 prose_consistency 严重偏离时的 chapter_design 重做次数
- 重试超过上限时降级为 best-effort 放行（不阻塞正文产出）
"""

from __future__ import annotations

from datetime import datetime, timezone

from langgraph.graph import END, StateGraph

from app.agents import (
    build_chapter_designer,
    build_narrative_writer,
    build_prose_consistency_checker,
)
from app.agents.llm_factory import LLMFactory
from app.db import AsyncSession
from app.graphs.state import StoryState
from app.services.context import ContextService
from app.services.outline_pre_validator import OutlinePreValidator
from app.services.prose_post_checker import ProsePostChecker
from app.services.tracking import ChapterTransaction, TrackingService


# ---------------------------------------------------------------------------
# 闭环控制参数
# ---------------------------------------------------------------------------

MAX_PRE_WRITE_RETRIES = 1       # pre_write 失败时 chapter_design 最多重做 1 次
MAX_DESIGN_ITERATIONS = 1       # prose_consistency 严重偏离时 chapter_design 最多重做 1 次
MAX_POST_WRITE_RETRIES = 1      # post_write 失败时 write_prose 最多重写 1 次

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
# LLM agent 节点（3 个）
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

    # --- 3) 反馈注入（pre_write_validate 失败 OR prose_consistency 严重偏离）---
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

    iter_note = (
        f"design_iter={iteration} pre_write_retry={pre_write_retry}"
    )
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
    """LLM agent：根据已校验细纲 + post_write/prose_consistency feedback 生成正文."""
    factory: LLMFactory = deps["llm_factory"]
    agent = build_narrative_writer(factory)
    chapter_no = int(state["chapter_no"])
    target = int(state.get("target_wordcount") or 3000)
    recall = state.get("recall") or {}
    outline = state.get("chapter_outline") or {}
    iteration = int(state.get("design_iteration") or 0)

    # 注入反馈（post_write_check + prose_consistency + pre_write_validation）
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


async def prose_consistency_node(state: StoryState, **deps) -> dict:
    """LLM 轻校验节点：对比正文 vs 本章细纲 beats 的剧情一致性.

    输出 consistency_report；自增 design_iteration 为下一轮重试做准备。
    """
    factory: LLMFactory = deps["llm_factory"]
    checker = build_prose_consistency_checker(factory)
    outline = state.get("chapter_outline") or {}
    prose = state.get("prose_draft") or ""

    report = await checker.check(outline=outline, prose=prose)

    iteration = int(state.get("design_iteration") or 0)
    return {
        "consistency_report": report,
        # 高 severity 走 redo 时，下一轮 chapter_design 看到的 iter 是 +1
        "design_iteration": iteration + 1 if report.get("severity") == "high" else iteration,
        "stages": [
            _stage(
                "prose_consistency",
                notes=(
                    f"deviation={report.get('deviation_score', 0):.2f} "
                    f"severity={report.get('severity')} "
                    f"rec={report.get('recommendation')}"
                ),
            ),
        ],
    }


# ---------------------------------------------------------------------------
# 服务节点（不调 LLM，确定性 / DB / 状态切换）
# ---------------------------------------------------------------------------


async def pre_write_validate_node(state: StoryState, **deps) -> dict:
    """服务节点：写正文之前对细纲本身做确定性校验.

    3 项检查：beats 完整性 / 卷大纲契约 / ReferenceGate
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
    # 失败 + 本次需要重做 → 自增计数（chapter_design 下一轮会看到）
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


async def post_write_check_node(state: StoryState, **deps) -> dict:
    """服务节点：确定性 6 项质量门禁（字数 / 标点 / AI 词 / 退化 / 禁用词 / 长度下限）.

    失败时通过 design_iteration 触发 write_prose 重写。
    """
    # 优先用 post_write_check 的 normalized_prose，避免上游 prose_draft 与下游不一致
    body = state.get("prose_draft") or ""
    target = int(state.get("target_wordcount") or 3000)

    report = ProsePostChecker().check(
        prose=body,
        target_wordcount=target,
        ai_markers=_AI_MARKERS,
    )

    # 若有标点归一，把归一后的正文回写到 prose_draft，让下游 consistency / commit 都基于归一版
    normalized = report.get("normalized_prose") or body
    updates: dict = {
        "post_write_check_report": report,
        "stages": [
            _stage(
                "post_write_check",
                notes=f"passed={report['passed']} issues={len(report['issues'])}",
            ),
        ],
    }
    if normalized != body:
        updates["prose_draft"] = normalized
    return updates


async def interrupt_human_node(state: StoryState, **deps) -> dict:
    """服务节点：标记 interrupt_pending=True，等 API 层响应人工审核（demo: 不真暂停）."""
    consistency = state.get("consistency_report") or {}
    reason = (
        f"prose_consistency severity=high 且设计重做次数已耗尽。"
        f"LLM 推荐：{consistency.get('recommendation', 'human_review')}。"
        f"Issues: {consistency.get('issues', [])}"
    )
    return {
        "interrupt_pending": True,
        "interrupt_reason": reason,
        "stages": [
            _stage(
                "interrupt_human",
                notes=f"待人工审核: {reason[:80]}",
            ),
        ],
    }


async def tracking_commit_node(state: StoryState, **deps) -> dict:
    """服务节点：原子 DB 事务落库.

    一个事务里完成：
    - chapters 表：保存正文
    - chapter_records 表：保存摘要 / 钩子 / 角色 / 伏笔
    - projects 表：state_revision 自增 + 更新 total_wordcount（TODO: 等 schema 落地）
    - 派生视图重建（TODO: character 聚合 / foreshadow 索引）
    """
    session: AsyncSession = deps["session"]
    project_id = state["project_id"]
    chapter_no = int(state["chapter_no"])
    body = state.get("prose_draft") or ""
    summary = (body[:140] + "…") if len(body) > 140 else body
    hook = body.split("\n\n")[-1][:200] if "\n\n" in body else body[:200]

    outline = state.get("chapter_outline") or {}

    tx = ChapterTransaction(
        chapter_no=chapter_no,
        chapter_content=body,
        chapter_title=f"第{chapter_no}章",
        summary_text=summary,
        chapter_hook=hook,
        emotion_arc={"start": "neutral", "end": "tense", "intensity": "medium"},
        # 扩展字段（TODO: ChapterTransaction 加这些字段后启用）
        # characters_in_scene=outline.get("characters_in_scene", []),
        # location=outline.get("location"),
        # pov=outline.get("pov"),
        # foreshadowing_changes=[],
    )
    snap = await TrackingService(session).commit(project_id, tx)

    # 是否 best-effort（post_write 或 consistency 失败但已耗尽重写次数）
    post_check = state.get("post_write_check_report") or {}
    consistency = state.get("consistency_report") or {}
    pre_write = state.get("pre_write_validation_report") or {}
    notice_parts: list[str] = []
    if not post_check.get("passed"):
        notice_parts.append(f"post_write_check 未通过: {post_check.get('issues', [])[:2]}")
    if consistency.get("severity") == "high":
        notice_parts.append(
            f"prose_consistency severity=high: deviation={consistency.get('deviation_score'):.2f}"
        )
    if not pre_write.get("passed"):
        notice_parts.append(f"pre_write_validate 未通过: {pre_write.get('issues', [])[:2]}")

    notice = "; ".join(notice_parts) if notice_parts else None

    return {
        "chapter_id": snap.chapter_id,
        "state_revision": snap.state_revision,
        "final_wordcount": snap.final_wordcount,
        "summary_text": summary,
        "chapter_hook": hook,
        "notice": notice,
        "stages": [
            _stage(
                "tracking_commit",
                notes=f"chapter_id={snap.chapter_id} wordcount={snap.final_wordcount}"
                + (f" notice={(notice or '')[:40]}…" if notice else ""),
            ),
        ],
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
    # chapter_design 节点把自增后的值写回 state（pre_write_retry_count = retry+1）
    # 这里看的是"已经重做过几次"。如果 retry+1（自增后）<= MAX → 还能重做
    if retry < MAX_PRE_WRITE_RETRIES:
        return "chapter_design"
    return "write_prose"  # best-effort 继续往下


def _route_after_post_write_check(state: StoryState) -> str:
    """post_write_check 后决策：pass → consistency; fail 且未超限 → write_prose 重写."""
    report = state.get("post_write_check_report") or {}
    if report.get("passed"):
        return "prose_consistency"

    iter_after = int(state.get("design_iteration") or 0)
    if iter_after <= MAX_DESIGN_ITERATIONS:
        return "write_prose"
    return "prose_consistency"  # best-effort


def _route_after_consistency(state: StoryState) -> str:
    """prose_consistency 后决策：三路分支.

    - low/medium severity              → tracking_commit (放行)
    - high severity + iter<MAX         → chapter_design (full redo)
    - high severity + iter≥MAX:
        - LLM 推荐 human_review        → interrupt_human → END
        - 其他                          → tracking_commit (best-effort)
    """
    report = state.get("consistency_report") or {}
    severity = report.get("severity", "low")
    recommendation = report.get("recommendation", "pass")
    iter_after = int(state.get("design_iteration") or 0)

    if severity != "high":
        return "tracking_commit"

    # 高 severity
    if iter_after <= MAX_DESIGN_ITERATIONS:
        return "chapter_design"

    # 重做次数已耗尽
    if recommendation == "human_review":
        return "interrupt_human"

    return "tracking_commit"  # best-effort


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build_write_long_graph():
    g = StateGraph(StoryState)

    # 7 个节点：3 LLM + 4 服务
    g.add_node("chapter_design", chapter_design_node)
    g.add_node("pre_write_validate", pre_write_validate_node)
    g.add_node("write_prose", write_prose_node)
    g.add_node("post_write_check", post_write_check_node)
    g.add_node("prose_consistency", prose_consistency_node)
    g.add_node("interrupt_human", interrupt_human_node)
    g.add_node("tracking_commit", tracking_commit_node)

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

    g.add_edge("write_prose", "post_write_check")

    # 条件边 2：post_write_check → write_prose / prose_consistency
    g.add_conditional_edges(
        "post_write_check",
        _route_after_post_write_check,
        {
            "write_prose": "write_prose",
            "prose_consistency": "prose_consistency",
        },
    )

    # 条件边 3：prose_consistency → tracking_commit / chapter_design / interrupt_human
    g.add_conditional_edges(
        "prose_consistency",
        _route_after_consistency,
        {
            "tracking_commit": "tracking_commit",
            "chapter_design": "chapter_design",
            "interrupt_human": "interrupt_human",
        },
    )

    g.add_edge("interrupt_human", END)
    g.add_edge("tracking_commit", END)

    return g.compile(name="write_long")