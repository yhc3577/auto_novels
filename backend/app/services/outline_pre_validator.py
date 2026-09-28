"""OutlinePreValidator — 写正文之前的细纲校验器（确定性服务，不调 LLM）.

校验 3 项：
1. beats_completeness  — beats 数量 / 长度 / 类型合规性
2. volume_contract     — 细纲是否呼应卷大纲的关键目标
3. reference_gate      — 细纲引用的 characters/location 是否在已知清单内

返回 report schema：
{
    "passed":   bool,
    "issues":   list[str],
    "feedback": list[str],   # 退回 chapter_design 时注入 prompt
    "checks":   {<name>: {"passed": bool, "details": str}}
}

模块级 @tool：
- validate_outline_pre_write  —— LangChain @tool，agent 可 bind_tools
"""

from __future__ import annotations

from langchain_core.tools import tool

from app.services.outline_validator import _impl_extract_keywords


class OutlinePreValidator:
    MIN_BEATS = 3
    MIN_BEAT_LEN = 4
    MAX_BEAT_LEN = 120

    def validate(
        self,
        *,
        outline: dict,
        volume_outline: dict | None = None,
        character_roster: list | None = None,
        known_locations: list | None = None,
    ) -> dict:
        issues: list[str] = []
        feedback: list[str] = []
        checks: dict = {
            "beats_completeness": {"passed": True, "details": ""},
            "volume_contract":    {"passed": True, "details": "卷大纲未提供（TODO: 等 schema 落地）"},
            "reference_gate":     {"passed": True, "details": "未提供 Roster（TODO: 等 schema 落地）"},
        }

        # --- 1) beats 完整性 ---
        beats = outline.get("key_beats", []) or []
        if not isinstance(beats, list):
            issues.append(f"key_beats 不是 list（got {type(beats).__name__}）")
            feedback.append("key_beats 必须是字符串列表。")
            checks["beats_completeness"]["passed"] = False
            beats = []
        elif len(beats) < self.MIN_BEATS:
            issues.append(f"key_beats 数量不足（{len(beats)} < {self.MIN_BEATS}）")
            feedback.append(f"key_beats 至少需要 {self.MIN_BEATS} 个，当前 {len(beats)} 个。")
            checks["beats_completeness"]["passed"] = False

        for i, beat in enumerate(beats):
            if not isinstance(beat, str):
                issues.append(f"beat[{i}] 不是字符串")
                checks["beats_completeness"]["passed"] = False
                continue
            if len(beat) < self.MIN_BEAT_LEN:
                issues.append(f"beat[{i}] 过短（{len(beat)} < {self.MIN_BEAT_LEN}）")
                feedback.append(f"beat[{i}] '{beat}' 至少 {self.MIN_BEAT_LEN} 字，需扩写。")
                checks["beats_completeness"]["passed"] = False
            elif len(beat) > self.MAX_BEAT_LEN:
                issues.append(f"beat[{i}] 过长（{len(beat)} > {self.MAX_BEAT_LEN}）")
                feedback.append(f"beat[{i}] 拆成多个 beat，或精简到 {self.MAX_BEAT_LEN} 字内。")
                checks["beats_completeness"]["passed"] = False

        checks["beats_completeness"]["details"] = (
            f"beats={len(beats)} (要求≥{self.MIN_BEATS})"
        )

        # --- 2) 卷大纲契约 ---
        if volume_outline:
            objectives = volume_outline.get("objectives", "") or ""
            outline_text = " ".join(
                [outline.get("opening_hook", "") or ""]
                + [str(b) for b in beats]
                + [outline.get("closing_hook", "") or ""]
            )
            # 抽取 objectives 的所有中文子串；命中任一即算覆盖
            all_kw = _impl_extract_keywords(objectives)
            hits_kw = [k for k in all_kw if k in outline_text]
            if all_kw and not hits_kw:
                issues.append("未呼应卷大纲的关键目标")
                feedback.append("细纲未呼应卷大纲的核心 objectives。")
                checks["volume_contract"]["passed"] = False
            checks["volume_contract"]["details"] = (
                f"卷大纲关键词命中 {len(hits_kw)}/{len(all_kw)}（举例 {hits_kw[:2]}）"
            )

        # --- 3) ReferenceGate ---
        if character_roster or known_locations:
            roster_names = {c.get("name") for c in (character_roster or []) if isinstance(c, dict)}
            known_locs = set(known_locations or [])
            scene_chars = outline.get("characters_in_scene", []) or []
            bad_chars = [c for c in scene_chars if roster_names and c not in roster_names]
            if bad_chars:
                issues.append(f"出场人物含未知角色: {bad_chars}")
                feedback.append(f"characters_in_scene 含未知角色 {bad_chars}，需对照 character_roster。")
                checks["reference_gate"]["passed"] = False
            loc = outline.get("location")
            if loc and known_locs and loc not in known_locs:
                issues.append(f"场景地点 {loc!r} 不在已知地点清单")
                feedback.append(f"地点 '{loc}' 不在 known_locations 内，需检查世界观设定。")
                checks["reference_gate"]["passed"] = False
            if roster_names or known_locs:
                checks["reference_gate"]["details"] = (
                    f"角色 {len(scene_chars) - len(bad_chars)}/{len(scene_chars)} 合规"
                    + (f"; 地点 {loc!r} 合规" if loc else "")
                )

        passed = all(c["passed"] for c in checks.values())
        return {
            "passed": passed,
            "issues": issues,
            "feedback": feedback,
            "checks": checks,
        }


# ---------------------------------------------------------------------------
# LangChain @tool 公开版（供 LLM agent bind_tools 调用）
# ---------------------------------------------------------------------------


@tool
def validate_outline_pre_write(
    outline: dict,
    volume_outline: dict | None = None,
    character_roster: list | None = None,
    known_locations: list | None = None,
) -> dict:
    """对【章节细纲】运行 3 项写前检查：beats 完整性 + 卷大纲契约 + ReferenceGate。

    Args:
        outline: 章节细纲 dict（至少含 key_beats 列表）。
        volume_outline: 卷级大纲 dict（可选，含 objectives 字段）。用于检查细纲是否呼应卷目标。
        character_roster: 项目人物 roster（可选，list[dict]，每项至少含 name 字段）。
        known_locations: 已知场景地点列表（可选，list[str]）。

    Returns:
        dict 含 4 个字段：
            - passed (bool): 综合是否通过（3 项检查全过）
            - issues (list[str]): 问题清单
            - feedback (list[str]): 退回 chapter_design 时注入 prompt 的反馈
            - checks (dict): 每项检查的详细结果
    """
    return OutlinePreValidator().validate(
        outline=outline,
        volume_outline=volume_outline,
        character_roster=character_roster,
        known_locations=known_locations,
    )


__all__ = ["OutlinePreValidator", "validate_outline_pre_write"]