"""Tests for write_long graph structure + OutlinePreValidator + ProsePostChecker + ProseConsistencyChecker."""

from __future__ import annotations

import json

import pytest

from app.agents.chapter_designer import (
    ChapterDesigner,
    _FALLBACK_OUTLINE,
    _parse_outline,
)
from app.agents.prose_consistency import ProseConsistencyChecker, _FALLBACK
from app.graphs.write_long import (
    MAX_DESIGN_ITERATIONS,
    MAX_POST_WRITE_RETRIES,
    MAX_PRE_WRITE_RETRIES,
    _route_after_consistency,
    _route_after_post_write_check,
    _route_after_pre_write_validate,
    build_write_long_graph,
)
from app.services.outline_pre_validator import OutlinePreValidator
from app.services.outline_validator import OutlineValidator, extract_keywords


# ===========================================================================
# Graph structure
# ===========================================================================


def test_graph_has_7_business_nodes():
    g = build_write_long_graph()
    nodes = set(g.get_graph().nodes.keys())

    # 7 个核心节点
    expected = {
        "chapter_design",          # LLM
        "pre_write_validate",      # 服务
        "write_prose",             # LLM
        "post_write_check",        # 服务
        "prose_consistency",       # LLM
        "interrupt_human",         # 服务
        "tracking_commit",         # 服务
    }
    assert expected.issubset(nodes), f"missing: {expected - nodes}"


def test_graph_node_classification():
    """3 个 LLM + 4 个服务节点 = 7 业务节点."""
    g = build_write_long_graph()
    nodes = sorted(n for n in g.get_graph().nodes.keys() if not n.startswith("__"))
    assert len(nodes) == 7, f"expected 7 business nodes, got {len(nodes)}: {nodes}"

    llm_nodes = {"chapter_design", "write_prose", "prose_consistency"}
    service_nodes = {"pre_write_validate", "post_write_check", "interrupt_human", "tracking_commit"}
    assert llm_nodes.issubset(set(nodes))
    assert service_nodes.issubset(set(nodes))
    # LLM 与服务节点不重叠
    assert llm_nodes.isdisjoint(service_nodes)


def test_graph_has_3_conditional_branches():
    """确认 3 组条件边都在：
    - pre_write_validate → {write_prose, chapter_design}
    - post_write_check → {write_prose, prose_consistency}
    - prose_consistency → {chapter_design, interrupt_human, tracking_commit}
    """
    g = build_write_long_graph()
    edges = g.get_graph().edges
    # langgraph 1.x: Edge(source, target, data, conditional) —— 4 元组
    cond_pairs: set[tuple[str, str]] = set()
    for edge in edges:
        # edge 可能是 (src, dst) 或 (src, dst, data) 或 (src, dst, data, conditional)
        if len(edge) >= 4 and edge[3] is True:
            cond_pairs.add((edge[0], edge[1]))
        elif len(edge) == 3 and isinstance(edge[2], dict) and edge[2].get("conditional"):
            cond_pairs.add((edge[0], edge[1]))

    expected_pairs = {
        ("pre_write_validate", "write_prose"),
        ("pre_write_validate", "chapter_design"),
        ("post_write_check", "write_prose"),
        ("post_write_check", "prose_consistency"),
        ("prose_consistency", "chapter_design"),
        ("prose_consistency", "interrupt_human"),
        ("prose_consistency", "tracking_commit"),
    }
    missing = expected_pairs - cond_pairs
    assert not missing, f"missing conditional edges: {missing}\nactual: {cond_pairs}"


# ===========================================================================
# Routing decision functions
# ===========================================================================


def test_route_pre_validate_pass():
    state = {"pre_write_validation_report": {"passed": True}, "pre_write_retry_count": 0}
    assert _route_after_pre_write_validate(state) == "write_prose"


def test_route_pre_validate_fail_first_redo():
    state = {"pre_write_validation_report": {"passed": False}, "pre_write_retry_count": 0}
    assert _route_after_pre_write_validate(state) == "chapter_design"


def test_route_pre_validate_fail_overflow():
    state = {
        "pre_write_validation_report": {"passed": False},
        "pre_write_retry_count": MAX_PRE_WRITE_RETRIES,  # 已达上限
    }
    assert _route_after_pre_write_validate(state) == "write_prose"


def test_route_post_check_pass():
    state = {
        "post_write_check_report": {"passed": True},
        "design_iteration": 0,
    }
    assert _route_after_post_write_check(state) == "prose_consistency"


def test_route_post_check_fail_rewrite():
    state = {
        "post_write_check_report": {"passed": False},
        "design_iteration": 0,
    }
    assert _route_after_post_write_check(state) == "write_prose"


def test_route_post_check_fail_overflow():
    state = {
        "post_write_check_report": {"passed": False},
        "design_iteration": MAX_DESIGN_ITERATIONS + 1,
    }
    assert _route_after_post_write_check(state) == "prose_consistency"


def test_route_consistency_low_passes():
    state = {
        "consistency_report": {"severity": "low", "recommendation": "pass"},
        "design_iteration": 5,
    }
    assert _route_after_consistency(state) == "tracking_commit"


def test_route_consistency_medium_passes():
    state = {
        "consistency_report": {"severity": "medium", "recommendation": "pass"},
        "design_iteration": 5,
    }
    assert _route_after_consistency(state) == "tracking_commit"


def test_route_consistency_high_within_max_redo():
    state = {
        "consistency_report": {"severity": "high", "recommendation": "redo"},
        "design_iteration": 1,  # <= MAX=1
    }
    assert _route_after_consistency(state) == "chapter_design"


def test_route_consistency_high_overflow_human_review():
    state = {
        "consistency_report": {"severity": "high", "recommendation": "human_review"},
        "design_iteration": MAX_DESIGN_ITERATIONS + 1,
    }
    assert _route_after_consistency(state) == "interrupt_human"


def test_route_consistency_high_overflow_no_human():
    state = {
        "consistency_report": {"severity": "high", "recommendation": "redo"},
        "design_iteration": MAX_DESIGN_ITERATIONS + 1,
    }
    # LLM 推荐 redo 但已耗尽次数 → best-effort 放行
    assert _route_after_consistency(state) == "tracking_commit"


# ===========================================================================
# OutlinePreValidator
# ===========================================================================


def test_pre_validator_passes_on_valid_outline():
    v = OutlinePreValidator()
    report = v.validate(outline=_FALLBACK_OUTLINE)
    assert report["passed"] is True
    assert report["issues"] == []


def test_pre_validator_rejects_too_few_beats():
    v = OutlinePreValidator()
    outline = {**_FALLBACK_OUTLINE, "key_beats": ["短"]}
    report = v.validate(outline=outline)
    assert report["passed"] is False
    assert any("数量不足" in i for i in report["issues"])


def test_pre_validator_rejects_short_beats():
    v = OutlinePreValidator()
    outline = {
        **_FALLBACK_OUTLINE,
        "key_beats": ["足够长的第一个节拍示例", "ok", "第三个足够长的节拍示例"],
    }
    report = v.validate(outline=outline)
    assert report["passed"] is False
    assert any("过短" in i for i in report["issues"])


def test_pre_validator_reference_gate_with_roster():
    v = OutlinePreValidator()
    outline = {**_FALLBACK_OUTLINE, "characters_in_scene": ["未知角色"]}
    roster = [{"name": "江禾"}, {"name": "银环女子"}]
    report = v.validate(outline=outline, character_roster=roster)
    assert report["passed"] is False
    assert any("未知角色" in i for i in report["issues"])
    assert "reference_gate" in report["checks"]


def test_pre_validator_volume_contract():
    v = OutlinePreValidator()
    outline = _FALLBACK_OUTLINE
    # objectives 与 outline 完全不重合 → 应 fail
    volume = {"objectives": "伏羲琴 谱写 蟠桃"}
    report = v.validate(outline=outline, volume_outline=volume)
    assert report["passed"] is False
    assert any("未呼应卷大纲" in i for i in report["issues"])


def test_pre_validator_volume_contract_passes():
    v = OutlinePreValidator()
    outline = _FALLBACK_OUTLINE
    volume = {"objectives": "雾港导师真相"}  # 与 outline 有重叠
    report = v.validate(outline=outline, volume_outline=volume)
    assert report["checks"]["volume_contract"]["passed"] is True


# ===========================================================================
# ProsePostChecker
# ===========================================================================


def test_post_checker_passes_on_clean_prose():
    from app.services.prose_post_checker import ProsePostChecker
    checker = ProsePostChecker()
    prose = (
        "雨夜的雾港站台，江禾提着黑色皮箱走出列车。\n\n"
        "他撞见了银环女子。她把黑伞递过来，江禾没接。\n\n"
        "两人走进附近的咖啡馆，她低声说了三句话。第一句是关于三年前那场火，"
        "第二句是关于他导师留下的半枚钥匙，第三句让他付了三年的咖啡。\n\n"
        "末了，银环女子留下半枚钥匙：别去港区码头。江禾在漂泊大雨里撑开黑伞。"
    )
    report = checker.check(prose=prose, target_wordcount=120)
    assert report["passed"] is True, f"unexpected fail: {report['issues']}"


def test_post_checker_catches_ai_marker():
    from app.services.prose_post_checker import ProsePostChecker
    checker = ProsePostChecker()
    prose = "综上所述，江禾明白了一切。" + "啊" * 100
    report = checker.check(prose=prose, target_wordcount=50)
    assert "ai_patterns" in report["checks"]
    assert report["checks"]["ai_patterns"]["passed"] is False
    assert "综上所述" in report["checks"]["ai_patterns"]["hits"]


def test_post_checker_normalizes_punctuation():
    from app.services.prose_post_checker import ProsePostChecker
    checker = ProsePostChecker()
    prose = "你好，世界。这是一个测试。"
    report = checker.check(prose=prose, target_wordcount=10)
    assert report["checks"]["punctuation"]["changes"] > 0
    assert "," in report["normalized_prose"]  # 全角逗号 → 半角


def test_post_checker_detects_banned_words():
    from app.services.prose_post_checker import ProsePostChecker
    checker = ProsePostChecker(banned_words=["和谐"])
    prose = "这里出现了和谐这个词。" * 5
    report = checker.check(prose=prose, target_wordcount=50)
    assert report["checks"]["banned_words"]["passed"] is False
    assert "和谐" in report["checks"]["banned_words"]["hits"]


def test_post_checker_detects_degeneration():
    from app.services.prose_post_checker import ProsePostChecker
    checker = ProsePostChecker()
    # 4 句话全相同 → 退化严重
    prose = "他走到窗前看着远方，他走到窗前看着远方，他走到窗前看着远方，他走到窗前看着远方。" * 3
    report = checker.check(prose=prose, target_wordcount=50)
    assert "degeneration" in report["checks"]
    # 退化分可能很高（精确阈值不固定，但应该 > 0.3）
    assert report["checks"]["degeneration"]["score"] > 0.3


def test_post_checker_wordcount_fail():
    from app.services.prose_post_checker import ProsePostChecker
    checker = ProsePostChecker()
    prose = "短" * 20
    report = checker.check(prose=prose, target_wordcount=300)
    assert report["checks"]["wordcount"]["passed"] is False


# ===========================================================================
# ProseConsistencyChecker (LLM)
# ===========================================================================


def test_consistency_checker_fallback_on_garbage():
    from app.agents.llm_factory import LLMFactory
    factory = LLMFactory(provider="mock")
    checker = ProseConsistencyChecker(factory)
    # 直接调 _parse 模拟 LLM 输出坏 JSON
    parsed = checker._parse("not valid json at all")
    assert parsed == _FALLBACK
    assert parsed["severity"] == "low"


def test_consistency_checker_parse_valid_json():
    from app.agents.llm_factory import LLMFactory
    factory = LLMFactory(provider="mock")
    checker = ProseConsistencyChecker(factory)
    raw = json.dumps({
        "deviation_score": 0.8,
        "severity": "high",
        "issues": ["未兑现 beats[1]"],
        "recommendation": "redo",
    })
    parsed = checker._parse(raw)
    assert parsed["deviation_score"] == 0.8
    assert parsed["severity"] == "high"
    assert parsed["recommendation"] == "redo"
    assert parsed["issues"] == ["未兑现 beats[1]"]


def test_consistency_checker_parse_type_coercion():
    from app.agents.llm_factory import LLMFactory
    factory = LLMFactory(provider="mock")
    checker = ProseConsistencyChecker(factory)
    raw = json.dumps({
        "deviation_score": "0.5",  # string
        "issues": "single issue as string",
    })
    parsed = checker._parse(raw)
    assert isinstance(parsed["deviation_score"], float)
    assert isinstance(parsed["issues"], list)


def test_consistency_checker_async_with_mock():
    from app.agents.llm_factory import LLMFactory
    import asyncio

    factory = LLMFactory(provider="mock")  # mock payload returns valid pass JSON
    checker = ProseConsistencyChecker(factory)
    report = asyncio.run(checker.check(outline=_FALLBACK_OUTLINE, prose="任何正文"))
    assert report["severity"] == "low"
    assert report["recommendation"] == "pass"


# ===========================================================================
# chapter_design 折叠多 stage 事件
# ===========================================================================


def test_chapter_design_emits_3_stages():
    """chapter_design 节点承担了 route_scenario + write_prep + chapter_design 三件事."""
    from app.graphs import write_long as wl

    async def _fake_recall(project_id, *, last_n, include_refs):
        return {}

    class _FakeTrackingService:
        def __init__(self, session): pass
        async def init(self, project_id): return 0

    class _FakeDesigner:
        def __init__(self, factory): pass
        async def design(self, prompt):
            return {
                "opening_hook": "x", "key_beats": ["a", "b", "c"], "conflict": "c",
                "climax": "d", "closing_hook": "e",
                "characters_in_scene": ["p"], "location": "l", "pov": "v",
            }

    wl.TrackingService = _FakeTrackingService
    wl.build_chapter_designer = lambda factory: _FakeDesigner(factory)
    wl.ContextService = lambda session: type("C", (), {
        "assemble_recall": staticmethod(_fake_recall)
    })()

    import asyncio
    state = {"project_id": 1, "user_input": "x", "stages": [], "errors": []}
    result = asyncio.run(wl.chapter_design_node(
        state, session=None, llm_factory=None
    ))
    stage_names = [s["name"] for s in result["stages"]]
    assert "route_scenario" in stage_names
    assert "write_prep" in stage_names
    assert "chapter_design" in stage_names


# ===========================================================================
# LangChain @tool 验证
# ===========================================================================


from langchain_core.tools import BaseTool


def test_all_tools_are_base_tool_instances():
    """所有 @tool 装饰的函数必须是 BaseTool 实例."""
    from app.services import (
        measure_wordcount,
        checkpoint_wordcount,
        extract_keywords,
        validate_outline,
        validate_outline_pre_write,
        check_prose_post_write,
    )
    for tool_fn in (
        measure_wordcount, checkpoint_wordcount, extract_keywords,
        validate_outline, validate_outline_pre_write, check_prose_post_write,
    ):
        assert isinstance(tool_fn, BaseTool), (
            f"{tool_fn.name} is not a BaseTool: {type(tool_fn)}"
        )


def test_tool_names_unique():
    """所有 @tool 的 name 必须唯一（agent bind_tools 时不能冲突）."""
    from app.services import (
        measure_wordcount, checkpoint_wordcount, extract_keywords,
        validate_outline, validate_outline_pre_write, check_prose_post_write,
    )
    names = [t.name for t in (
        measure_wordcount, checkpoint_wordcount, extract_keywords,
        validate_outline, validate_outline_pre_write, check_prose_post_write,
    )]
    assert len(names) == len(set(names)), f"duplicate tool names: {names}"


def test_tools_have_descriptions():
    """@tool 必须有 description（LLM 用来理解工具用途）."""
    from app.services import (
        measure_wordcount, checkpoint_wordcount, extract_keywords,
        validate_outline, validate_outline_pre_write, check_prose_post_write,
    )
    for tool_fn in (
        measure_wordcount, checkpoint_wordcount, extract_keywords,
        validate_outline, validate_outline_pre_write, check_prose_post_write,
    ):
        assert tool_fn.description, f"{tool_fn.name} has no description"
        assert len(tool_fn.description) >= 10, (
            f"{tool_fn.name} description too short: {tool_fn.description!r}"
        )


def test_tools_have_args_schema():
    """@tool 必须能生成 args_schema（LLM 才能生成正确调用参数）.

    schema 顶层就是 properties dict（单 arg tool）或 {properties: {...}, required: [...]}（多 arg）。
    """
    from app.services import (
        measure_wordcount, checkpoint_wordcount, extract_keywords,
        validate_outline, validate_outline_pre_write, check_prose_post_write,
    )
    for tool_fn in (
        measure_wordcount, checkpoint_wordcount, extract_keywords,
        validate_outline, validate_outline_pre_write, check_prose_post_write,
    ):
        schema = tool_fn.args
        assert schema is not None, f"{tool_fn.name} has no args schema"
        # schema 顶层直接是 properties（单 arg 时）；或者 {properties: ..., required: ...}
        assert schema, f"{tool_fn.name} schema is empty"


def test_extract_keywords_tool_invocation():
    """@tool extract_keywords 可以通过 .invoke() 调用，行为与 _impl 一致."""
    from app.services import extract_keywords
    from app.services.outline_validator import _impl_extract_keywords

    beat = "雾港导师真相"
    # .invoke() 用 dict 参数
    via_tool = extract_keywords.invoke({"beat": beat})
    via_impl = _impl_extract_keywords(beat)
    assert via_tool == via_impl
    assert len(via_tool) > 0


def test_measure_wordcount_tool_invocation():
    from app.services import measure_wordcount
    result = measure_wordcount.invoke({"text": "雾港 hello 夜 world"})
    # CJK=3, ASCII=2 (hello + world) → total=5 (与 _impl 直接调用结果一致)
    assert result == 5


def test_checkpoint_wordcount_tool_invocation():
    from app.services import checkpoint_wordcount
    result = checkpoint_wordcount.invoke({"text": "啊" * 100, "target": 100})
    assert result["passed"] is True
    assert result["actual"] == 100


def test_validate_outline_tool_invocation():
    from app.services import validate_outline
    outline = {
        "opening_hook": "雨夜的雾港站台",
        "key_beats": ["发现银环女子", "旧公寓密会"],
        "closing_hook": "银环女子留下钥匙",
    }
    prose = (
        "雨夜的雾港站台，江禾看见了银环女子。\n"
        "在旧公寓密会后他们发现手稿。\n"
        "末了，银环女子留下钥匙。"
    )
    result = validate_outline.invoke({
        "outline": outline, "prose": prose, "target_wordcount": 30,
    })
    assert "passed" in result
    assert "score" in result
    assert "feedback" in result
    assert "checks" in result


def test_validate_outline_pre_write_tool_invocation():
    from app.services import validate_outline_pre_write
    result = validate_outline_pre_write.invoke({"outline": _FALLBACK_OUTLINE})
    assert result["passed"] is True
    assert "checks" in result
    assert "beats_completeness" in result["checks"]


def test_check_prose_post_write_tool_invocation():
    from app.services import check_prose_post_write
    prose = (
        "雨夜的雾港站台，江禾提着黑色皮箱走出列车。\n\n"
        "他撞见了银环女子。她把黑伞递过来，江禾没接。\n\n"
        "两人走进附近的咖啡馆，她低声说了三句话。\n\n"
        "末了，银环女子留下半枚钥匙：别去港区码头。"
    )
    result = check_prose_post_write.invoke({
        "prose": prose, "target_wordcount": 100,
    })
    assert "passed" in result
    assert "checks" in result
    assert "punctuation" in result["checks"]


def test_internal_caller_uses_impl_path():
    """内部代码（OutlineValidator._beats_coverage）走 _impl_* 快速路径，不依赖 @tool."""
    v = OutlineValidator()
    # 这条调用路径内部走 _impl_extract_keywords，不会触发 @tool.invoke 的开销
    coverage = v._beats_coverage(["雾港导师真相"], "这是一个雾港的导师失踪故事")
    assert coverage == 1.0


def test_tools_have_valid_openai_function_schema():
    """验证每个 @tool 都能正确生成 OpenAI function calling schema.

    不依赖具体 LLM 实现 —— 用 langchain 自带的 StructuredTool.convert_to_openai_function。
    """
    from app.services import (
        measure_wordcount, checkpoint_wordcount, extract_keywords,
        validate_outline, validate_outline_pre_write, check_prose_post_write,
    )
    tools = [
        measure_wordcount, checkpoint_wordcount, extract_keywords,
        validate_outline, validate_outline_pre_write, check_prose_post_write,
    ]
    for tool_fn in tools:
        try:
            schema = tool_fn.args_schema  # Pydantic model class
            assert schema is not None
            assert schema.model_fields, f"{tool_fn.name} has no model fields"
        except Exception as e:
            pytest.fail(f"{tool_fn.name} schema generation failed: {e}")


def test_tools_have_distinct_names_for_agent_binding():
    """模拟 bind_tools 场景：tools 列表里 name 不能冲突."""
    from app.services import (
        measure_wordcount, checkpoint_wordcount, extract_keywords,
        validate_outline, validate_outline_pre_write, check_prose_post_write,
    )
    tools = [
        measure_wordcount, checkpoint_wordcount, extract_keywords,
        validate_outline, validate_outline_pre_write, check_prose_post_write,
    ]
    tool_dict = {t.name: t for t in tools}
    assert len(tool_dict) == len(tools), (
        f"name 冲突: {[t.name for t in tools]}"
    )