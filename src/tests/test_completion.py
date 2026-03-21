"""
代码补全模块测试

测试智能代码补全、代码异味检测、重构建议和最佳实践推荐功能。
"""

import pytest

from mc_agent_kit.completion import (
    BestPractice,
    BestPracticeChecker,
    BestPracticeResult,
    CodeCompleter,
    CodeSmell,
    Completion,
    CompletionContext,
    CompletionKind,
    CompletionResult,
    PracticeCategory,
    PracticeSeverity,
    RefactorEngine,
    RefactorSuggestion,
    RefactorType,
    SmellCategory,
    SmellDetector,
    SmellSeverity,
    SmellType,
)


class TestCompletion:
    """测试补全数据结构"""

    def test_completion_defaults(self) -> None:
        """测试补全项默认值"""
        comp = Completion(label="test", kind=CompletionKind.API)

        assert comp.label == "test"
        assert comp.kind == CompletionKind.API
        assert comp.detail == ""
        assert comp.insert_text == "test"
        assert comp.sort_text == "test"
        assert comp.filter_text == "test"

    def test_completion_custom(self) -> None:
        """测试自定义补全项"""
        comp = Completion(
            label="GetConfig",
            kind=CompletionKind.API,
            detail="Get configuration",
            insert_text="GetConfig()",
            priority=10,
        )

        assert comp.label == "GetConfig"
        assert comp.detail == "Get configuration"
        assert comp.insert_text == "GetConfig()"
        assert comp.priority == 10


class TestCompletionContext:
    """测试补全上下文"""

    def test_from_code_simple(self) -> None:
        """测试从代码创建上下文"""
        code = "def test():\n    pass"
        ctx = CompletionContext.from_code(code, cursor_line=0, cursor_column=0)

        assert ctx.code == code
        assert ctx.cursor_line == 0
        assert ctx.cursor_column == 0
        assert ctx.line_prefix == ""
        assert ctx.line_suffix == "def test():"

    def test_from_code_with_prefix(self) -> None:
        """测试带前缀的上下文"""
        code = "GetEngine"
        ctx = CompletionContext.from_code(code, cursor_line=0, cursor_column=9)

        assert ctx.line_prefix == "GetEngine"
        assert ctx.line_suffix == ""

    def test_get_prefix_before_dot(self) -> None:
        """测试获取点号前缀"""
        code = "GetConfig."
        ctx = CompletionContext.from_code(code, cursor_line=0, cursor_column=10)

        prefix = ctx.get_prefix_before_dot()
        assert prefix == "GetConfig"

    def test_get_prefix_before_dot_no_dot(self) -> None:
        """测试无点号时的前缀"""
        code = "GetConfig"
        ctx = CompletionContext.from_code(code, cursor_line=0, cursor_column=9)

        prefix = ctx.get_prefix_before_dot()
        assert prefix is None

    def test_get_call_context(self) -> None:
        """测试获取函数调用上下文"""
        code = "CreateEngineEntity("
        ctx = CompletionContext.from_code(code, cursor_line=0, cursor_column=20)

        result = ctx.get_call_context()
        assert result is not None
        assert result[0] == "CreateEngineEntity"
        assert result[1] == 0

    def test_get_call_context_with_args(self) -> None:
        """测试带参数的函数调用上下文"""
        code = "CreateEngineEntity(type, "
        ctx = CompletionContext.from_code(code, cursor_line=0, cursor_column=26)

        result = ctx.get_call_context()
        assert result is not None
        assert result[0] == "CreateEngineEntity"
        assert result[1] == 1


class TestCodeCompleter:
    """测试代码补全器"""

    def test_complete_api_prefix(self) -> None:
        """测试 API 前缀补全"""
        completer = CodeCompleter()
        ctx = CompletionContext.from_code("GetEngine", 0, 9)
        result = completer.complete(ctx)

        assert len(result.completions) > 0
        # 应该包含 GetEngine 相关的补全
        labels = [c.label for c in result.completions]
        assert "GetEngine" in labels or any("GetEngine" in l for l in labels)

    def test_complete_member(self) -> None:
        """测试成员补全"""
        completer = CodeCompleter()
        ctx = CompletionContext.from_code("GetConfig.", 0, 10)
        result = completer.complete(ctx)

        assert len(result.completions) > 0
        # 应该包含 GetConfig 的成员
        labels = [c.label for c in result.completions]
        assert "GetGameType" in labels or "GetEngineType" in labels

    def test_complete_event(self) -> None:
        """测试事件补全"""
        completer = CodeCompleter()
        ctx = CompletionContext.from_code("AddServer", 0, 9)
        result = completer.complete(ctx)

        assert len(result.completions) > 0
        labels = [c.label for c in result.completions]
        assert any("AddServerPlayerEvent" in l for l in labels)

    def test_complete_api_method(self) -> None:
        """测试 complete_api 方法"""
        completer = CodeCompleter()
        results = completer.complete_api("Get")

        assert len(results) > 0
        assert any("GetConfig" in r for r in results)

    def test_complete_event_method(self) -> None:
        """测试 complete_event 方法"""
        completer = CodeCompleter()
        results = completer.complete_event("Entity")

        assert len(results) > 0
        assert any("EntityHurtEvent" in r for r in results)


class TestCompletionResult:
    """测试补全结果"""

    def test_get_top_n(self) -> None:
        """测试获取前 N 个补全"""
        completions = [
            Completion(label="b", kind=CompletionKind.API, priority=1),
            Completion(label="a", kind=CompletionKind.API, priority=2),
            Completion(label="c", kind=CompletionKind.API, priority=0),
        ]
        result = CompletionResult(completions=completions, context=CompletionContext.from_code("", 0, 0))

        top = result.get_top_n(2)
        assert len(top) == 2
        # 按优先级排序
        assert top[0].priority >= top[1].priority


class TestCodeSmell:
    """测试代码异味"""

    def test_smell_creation(self) -> None:
        """测试创建代码异味"""
        smell = CodeSmell(
            type=SmellType.LONG_FUNCTION,
            message="Function too long",
            line=10,
            severity=SmellSeverity.MAJOR,
            category=SmellCategory.COMPLEXITY,
        )

        assert smell.type == SmellType.LONG_FUNCTION
        assert smell.line == 10
        assert smell.severity == SmellSeverity.MAJOR

    def test_smell_to_dict(self) -> None:
        """测试转换为字典"""
        smell = CodeSmell(
            type=SmellType.MAGIC_NUMBER,
            message="Magic number found",
            line=5,
        )

        d = smell.to_dict()
        assert d["type"] == "magic_number"
        assert d["line"] == 5


class TestSmellDetector:
    """测试代码异味检测器"""

    def test_detect_long_function(self) -> None:
        """测试检测长函数"""
        # 创建一个超过 50 行的函数
        code = "def long_function():\n" + "\n".join(["    x = 1"] * 60)

        detector = SmellDetector()
        smells = detector.detect(code)

        # 应该检测到长函数
        long_func_smells = [s for s in smells if s.type == SmellType.LONG_FUNCTION]
        assert len(long_func_smells) > 0

    def test_detect_many_parameters(self) -> None:
        """测试检测过多参数"""
        code = "def many_params(a, b, c, d, e, f, g, h):\n    pass"

        detector = SmellDetector()
        smells = detector.detect(code)

        param_smells = [s for s in smells if s.type == SmellType.MANY_PARAMETERS]
        assert len(param_smells) > 0

    def test_detect_bare_except(self) -> None:
        """测试检测裸 except"""
        code = "try:\n    pass\nexcept:\n    pass"

        detector = SmellDetector()
        smells = detector.detect(code)

        bare_smells = [s for s in smells if s.type == SmellType.BARE_EXCEPT]
        assert len(bare_smells) > 0

    def test_detect_magic_number(self) -> None:
        """测试检测魔法数字"""
        code = "timeout = 1000\nvalue = 12345"

        detector = SmellDetector()
        smells = detector.detect(code)

        magic_smells = [s for s in smells if s.type == SmellType.MAGIC_NUMBER]
        assert len(magic_smells) > 0

    def test_detect_print_debug(self) -> None:
        """测试检测 print 调试语句"""
        code = "print('debug message')"

        detector = SmellDetector()
        smells = detector.detect(code)

        print_smells = [s for s in smells if s.type == SmellType.PRINT_DEBUG]
        assert len(print_smells) > 0

    def test_detect_short_name(self) -> None:
        """测试检测短名称"""
        code = "def f():\n    pass"

        detector = SmellDetector()
        smells = detector.detect(code)

        short_name_smells = [s for s in smells if s.type == SmellType.SHORT_NAME]
        assert len(short_name_smells) > 0

    def test_detect_hardcoded_path(self) -> None:
        """测试检测硬编码路径"""
        code = 'path = "C:\\\\Users\\\\test"'

        detector = SmellDetector()
        smells = detector.detect(code)

        path_smells = [s for s in smells if s.type == SmellType.HARDCODED_PATH]
        assert len(path_smells) > 0

    def test_no_smells_clean_code(self) -> None:
        """测试干净代码无异味"""
        code = '''
def calculate_total(items: list) -> float:
    """Calculate total price."""
    total = 0.0
    for item in items:
        total += item.price
    return total
'''
        detector = SmellDetector()
        smells = detector.detect(code)

        # 可能有一些轻微的信息级别的异味，但不应该有严重的
        major_smells = [s for s in smells if s.severity in (SmellSeverity.MAJOR, SmellSeverity.CRITICAL)]
        assert len(major_smells) == 0


class TestRefactorSuggestion:
    """测试重构建议"""

    def test_suggestion_creation(self) -> None:
        """测试创建重构建议"""
        suggestion = RefactorSuggestion(
            type=RefactorType.EXTRACT_FUNCTION,
            message="Extract function",
            line=10,
            original_code="long code",
            suggested_code="# extracted",
            priority=5,
        )

        assert suggestion.type == RefactorType.EXTRACT_FUNCTION
        assert suggestion.line == 10
        assert suggestion.priority == 5

    def test_suggestion_to_dict(self) -> None:
        """测试转换为字典"""
        suggestion = RefactorSuggestion(
            type=RefactorType.RENAME,
            message="Rename variable",
            line=5,
        )

        d = suggestion.to_dict()
        assert d["type"] == "rename"
        assert d["line"] == 5


class TestRefactorEngine:
    """测试重构引擎"""

    def test_suggest_from_smells(self) -> None:
        """测试从异味生成建议"""
        smells = [
            CodeSmell(
                type=SmellType.BARE_EXCEPT,
                message="Bare except",
                line=3,
            )
        ]
        code = "try:\n    pass\nexcept:\n    pass"

        engine = RefactorEngine()
        suggestions = engine.suggest_refactors(smells, code)

        assert len(suggestions) > 0
        assert any(s.type == RefactorType.SIMPLIFY_CONDITION for s in suggestions)

    def test_suggest_magic_number_fix(self) -> None:
        """测试魔法数字修复建议"""
        smells = [
            CodeSmell(
                type=SmellType.MAGIC_NUMBER,
                message="Magic number: 1000",
                line=1,
            )
        ]
        code = "timeout = 1000"

        engine = RefactorEngine()
        suggestions = engine.suggest_refactors(smells, code)

        assert len(suggestions) > 0
        assert any(s.type == RefactorType.REPLACE_MAGIC_NUMBER for s in suggestions)


class TestBestPractice:
    """测试最佳实践"""

    def test_practice_creation(self) -> None:
        """测试创建最佳实践"""
        practice = BestPractice(
            id="TEST001",
            name="Test practice",
            category=PracticeCategory.PERFORMANCE,
            description="A test practice",
            rationale="Because it's good",
        )

        assert practice.id == "TEST001"
        assert practice.category == PracticeCategory.PERFORMANCE

    def test_practice_with_examples(self) -> None:
        """测试带示例的最佳实践"""
        practice = BestPractice(
            id="TEST002",
            name="Example practice",
            category=PracticeCategory.CODING_STYLE,
            description="Practice with examples",
            rationale="Examples help",
            examples_good=["good_code()"],
            examples_bad=["bad_code()"],
        )

        assert len(practice.examples_good) == 1
        assert len(practice.examples_bad) == 1


class TestBestPracticeChecker:
    """测试最佳实践检查器"""

    def test_check_performance(self) -> None:
        """测试性能检查"""
        code = '''
def on_tick(args):
    for player in GetPlayerList():
        expensive_operation(player)
'''
        checker = BestPracticeChecker()
        results = checker.check(code)

        # 应该检测到 Tick 中的循环
        tick_issues = [r for r in results if r.practice.id == "PERF001"]
        assert len(tick_issues) > 0

    def test_check_style(self) -> None:
        """测试风格检查"""
        code = '''
def public_function(x):
    return x + 1
'''
        checker = BestPracticeChecker()
        results = checker.check(code)

        # 应该检测到缺少文档字符串
        doc_issues = [r for r in results if r.practice.id == "STYLE002"]
        assert len(doc_issues) > 0

    def test_check_security(self) -> None:
        """测试安全检查"""
        code = '''
def handle_command(args):
    process(args['value'])
'''
        checker = BestPracticeChecker()
        results = checker.check(code)

        # 应该检测到缺少输入验证
        security_issues = [r for r in results if r.practice.id == "SEC001"]
        assert len(security_issues) > 0

    def test_list_practices(self) -> None:
        """测试列出最佳实践"""
        checker = BestPracticeChecker()

        all_practices = checker.list_practices()
        assert len(all_practices) > 0

        perf_practices = checker.list_practices(PracticeCategory.PERFORMANCE)
        assert all(p.category == PracticeCategory.PERFORMANCE for p in perf_practices)

    def test_get_practice(self) -> None:
        """测试获取特定实践"""
        checker = BestPracticeChecker()

        practice = checker.get_practice("PERF001")
        assert practice is not None
        assert practice.name == "避免在 Tick 事件中进行昂贵操作"

    def test_get_summary(self) -> None:
        """测试获取摘要"""
        code = "def test():\n    pass"
        checker = BestPracticeChecker()
        results = checker.check(code)

        summary = checker.get_summary(results)
        assert "total" in summary
        assert "passed" in summary
        assert "failed" in summary


class TestBestPracticeResult:
    """测试最佳实践结果"""

    def test_result_creation(self) -> None:
        """测试创建结果"""
        practice = BestPractice(
            id="TEST001",
            name="Test",
            category=PracticeCategory.MODSDK,
            description="Test",
            rationale="Test",
        )
        result = BestPracticeResult(
            practice=practice,
            message="Check passed",
            line=10,
            passed=True,
        )

        assert result.practice.id == "TEST001"
        assert result.passed is True

    def test_result_to_dict(self) -> None:
        """测试转换为字典"""
        practice = BestPractice(
            id="TEST001",
            name="Test",
            category=PracticeCategory.MODSDK,
            description="Test",
            rationale="Test",
        )
        result = BestPracticeResult(
            practice=practice,
            message="Check failed",
            line=5,
            passed=False,
        )

        d = result.to_dict()
        assert d["practice_id"] == "TEST001"
        assert d["passed"] is False
        assert d["line"] == 5


class TestIntegration:
    """集成测试"""

    def test_full_analysis_workflow(self) -> None:
        """测试完整分析流程"""
        code = '''
def process_entity(entity_id):
    """Process an entity."""
    pos = GetEntityPos(entity_id)
    for i in range(100):
        expensive_call(i)
    return pos

def on_tick(args):
    for player in GetPlayerList():
        heavy_operation(player)
'''

        # 1. 检测代码异味
        detector = SmellDetector()
        smells = detector.detect(code)
        assert len(smells) > 0

        # 2. 生成重构建议
        engine = RefactorEngine()
        suggestions = engine.suggest_refactors(smells, code)
        assert len(suggestions) >= 0

        # 3. 检查最佳实践
        checker = BestPracticeChecker()
        results = checker.check(code)
        assert len(results) > 0

    def test_code_completion_workflow(self) -> None:
        """测试代码补全流程"""
        completer = CodeCompleter()

        # 测试 API 补全
        api_results = completer.complete_api("Get")
        assert len(api_results) > 0

        # 测试事件补全
        event_results = completer.complete_event("Entity")
        assert len(event_results) > 0