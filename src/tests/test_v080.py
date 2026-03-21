"""
测试 v0.8.0 新增功能

包括游戏内执行器、日志分析器、错误诊断器和自动修复器。
"""

import pytest
from mc_agent_kit.execution import (
    GameExecutionConfig,
    GameExecutor,
    GameExecutorState,
)
from mc_agent_kit.log_capture import (
    AlertSeverity,
    ErrorPattern,
    LogAnalyzer,
    LogAggregator,
    PatternCategory,
)
from mc_agent_kit.autofix import (
    AutoFixer,
    ErrorDiagnoser,
    ErrorType,
    FixStatus,
)


class TestGameExecutor:
    """测试游戏执行器"""

    def test_game_execution_config_defaults(self):
        """测试配置默认值"""
        config = GameExecutionConfig()
        assert config.game_exe_path == ""
        assert config.config_path == ""
        assert config.logging_host == "127.0.0.1"
        assert config.logging_port == 0
        assert config.auto_start is False
        assert config.auto_stop is True
        assert config.capture_logs is True

    def test_game_executor_initial_state(self):
        """测试执行器初始状态"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)
        assert executor.session.state == GameExecutorState.IDLE
        assert executor.session.process is None
        assert executor.session.log_server is None

    def test_game_executor_get_session_info(self):
        """测试获取会话信息"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)
        info = executor.get_session_info()
        assert info["state"] == "idle"
        assert info["game_pid"] is None
        assert info["execution_count"] == 0

    def test_game_executor_is_game_running(self):
        """测试游戏运行状态检查"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)
        assert executor.is_game_running() is False

    def test_game_executor_get_recent_logs(self):
        """测试获取最近日志"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)
        logs = executor.get_recent_logs()
        assert logs == []

    def test_game_executor_set_callbacks(self):
        """测试设置回调函数"""
        config = GameExecutionConfig()
        executor = GameExecutor(config)

        called = []

        def on_log(log):
            called.append(("log", log))

        def on_error(error):
            called.append(("error", error))

        executor.set_log_callback(on_log)
        executor.set_error_callback(on_error)

        # 模拟日志处理
        executor._handle_log("test log")
        assert ("log", "test log") in called


class TestLogAnalyzer:
    """测试日志分析器"""

    def test_log_analyzer_initialization(self):
        """测试分析器初始化"""
        analyzer = LogAnalyzer()
        assert len(analyzer.patterns) > 0  # 有内置模式
        assert analyzer._running is False

    def test_log_analyzer_builtin_patterns(self):
        """测试内置错误模式"""
        analyzer = LogAnalyzer()
        patterns = analyzer.get_patterns()
        pattern_names = [p.name for p in patterns]

        assert "SyntaxError" in pattern_names
        assert "NameError" in pattern_names
        assert "TypeError" in pattern_names
        assert "KeyError" in pattern_names

    def test_log_analyzer_add_pattern(self):
        """测试添加自定义模式"""
        analyzer = LogAnalyzer(use_builtin_patterns=False)
        pattern = ErrorPattern(
            name="CustomError",
            pattern=__import__("re").compile(r"CustomError:\s*(.+)"),
            category=PatternCategory.CUSTOM,
            severity=AlertSeverity.ERROR,
            description="自定义错误",
        )
        analyzer.add_pattern(pattern)
        patterns = analyzer.get_patterns()
        assert len(patterns) == 1
        assert patterns[0].name == "CustomError"

    def test_log_analyzer_remove_pattern(self):
        """测试移除模式"""
        analyzer = LogAnalyzer()
        initial_count = len(analyzer.get_patterns())
        analyzer.remove_pattern("SyntaxError")
        assert len(analyzer.get_patterns()) == initial_count - 1

    def test_log_analyzer_process_log(self):
        """测试处理日志"""
        analyzer = LogAnalyzer()
        entry = analyzer.process_log("This is an info log")
        assert entry.level.value == "INFO"

    def test_log_analyzer_match_patterns(self):
        """测试模式匹配"""
        analyzer = LogAnalyzer()
        entry = analyzer.process_log("NameError: name 'x' is not defined")
        matches = analyzer.match_patterns(entry)
        assert len(matches) > 0
        assert matches[0].pattern.name == "NameError"

    def test_log_analyzer_get_statistics(self):
        """测试获取统计"""
        analyzer = LogAnalyzer()
        analyzer.process_log("info log")
        analyzer.process_log("warning log")

        stats = analyzer.get_statistics()
        assert stats["total_logs"] == 2


class TestLogAggregator:
    """测试日志聚合器"""

    def test_log_aggregator_add_log(self):
        """测试添加日志"""
        aggregator = LogAggregator()
        entry = aggregator.add_log("test log")
        assert entry.raw == "test log"

    def test_log_aggregator_query(self):
        """测试查询日志"""
        aggregator = LogAggregator()
        aggregator.add_log("error log")
        aggregator.add_log("info log")

        from mc_agent_kit.log_capture.parser import LogLevel

        errors = aggregator.query(level=LogLevel.INFO)
        assert len(errors) >= 1

    def test_log_aggregator_clear(self):
        """测试清空日志"""
        aggregator = LogAggregator()
        aggregator.add_log("test log")
        aggregator.clear()
        assert len(aggregator._logs) == 0


class TestErrorDiagnoser:
    """测试错误诊断器"""

    def test_diagnose_name_error(self):
        """测试诊断 NameError"""
        diagnoser = ErrorDiagnoser()
        result = diagnoser.diagnose("NameError: name 'x' is not defined")

        assert result.error_info.error_type == ErrorType.NAME_ERROR
        assert "x" in result.error_info.context.get("undefined_name", "")
        assert len(result.suggestions) > 0

    def test_diagnose_key_error(self):
        """测试诊断 KeyError"""
        diagnoser = ErrorDiagnoser()
        result = diagnoser.diagnose("KeyError: 'missing_key'")

        assert result.error_info.error_type == ErrorType.KEY_ERROR
        assert len(result.suggestions) > 0

    def test_diagnose_type_error(self):
        """测试诊断 TypeError"""
        diagnoser = ErrorDiagnoser()
        result = diagnoser.diagnose("TypeError: unsupported operand type(s)")

        assert result.error_info.error_type == ErrorType.TYPE_ERROR
        assert len(result.suggestions) > 0

    def test_diagnose_index_error(self):
        """测试诊断 IndexError"""
        diagnoser = ErrorDiagnoser()
        result = diagnoser.diagnose("IndexError: list index out of range")

        assert result.error_info.error_type == ErrorType.INDEX_ERROR

    def test_diagnose_attribute_error(self):
        """测试诊断 AttributeError"""
        diagnoser = ErrorDiagnoser()
        result = diagnoser.diagnose("AttributeError: 'NoneType' object has no attribute 'x'")

        assert result.error_info.error_type == ErrorType.ATTRIBUTE_ERROR

    def test_diagnose_syntax_error(self):
        """测试诊断 SyntaxError"""
        diagnoser = ErrorDiagnoser()
        result = diagnoser.diagnose("SyntaxError: invalid syntax")

        assert result.error_info.error_type == ErrorType.SYNTAX_ERROR

    def test_diagnose_import_error(self):
        """测试诊断 ImportError"""
        diagnoser = ErrorDiagnoser()
        result = diagnoser.diagnose("ImportError: No module named 'missing_module'")

        assert result.error_info.error_type == ErrorType.IMPORT_ERROR

    def test_diagnose_zero_division(self):
        """测试诊断 ZeroDivisionError"""
        diagnoser = ErrorDiagnoser()
        result = diagnoser.diagnose("ZeroDivisionError: division by zero")

        assert result.error_info.error_type == ErrorType.ZERO_DIVISION_ERROR

    def test_diagnose_unknown_error(self):
        """测试诊断未知错误"""
        diagnoser = ErrorDiagnoser()
        result = diagnoser.diagnose("Some random error message")

        assert result.error_info.error_type == ErrorType.UNKNOWN

    def test_diagnose_traceback(self):
        """测试诊断 traceback"""
        diagnoser = ErrorDiagnoser()
        traceback_text = """Traceback (most recent call last):
  File "test.py", line 10, in <module>
    print(x)
NameError: name 'x' is not defined"""
        result = diagnoser.diagnose_traceback(traceback_text)

        assert result.error_info.error_type == ErrorType.NAME_ERROR
        assert result.error_info.traceback == traceback_text

    def test_analyze_code(self):
        """测试代码分析"""
        diagnoser = ErrorDiagnoser()
        errors = diagnoser.analyze_code("def func(")  # 语法错误
        assert len(errors) > 0
        assert errors[0].error_type == ErrorType.SYNTAX_ERROR

    def test_get_fixable_errors(self):
        """测试获取可修复错误类型"""
        diagnoser = ErrorDiagnoser()
        fixable = diagnoser.get_fixable_errors()
        assert ErrorType.KEY_ERROR in fixable
        assert ErrorType.INDEX_ERROR in fixable


class TestAutoFixer:
    """测试自动修复器"""

    def test_fix_key_error(self):
        """测试修复 KeyError"""
        fixer = AutoFixer()
        code = "value = data['key']"
        error_log = "KeyError: 'key'"

        result = fixer.fix_from_error_log(code, error_log)
        assert result.status in [FixStatus.SUCCESS, FixStatus.PARTIAL]
        assert "get" in result.fixed_code

    def test_fix_attribute_error(self):
        """测试修复 AttributeError"""
        fixer = AutoFixer()
        code = "value = obj.attr"
        error_log = "AttributeError: 'NoneType' object has no attribute 'attr'"

        result = fixer.fix_from_error_log(code, error_log)
        assert result.status in [FixStatus.SUCCESS, FixStatus.PARTIAL]

    def test_fix_index_error(self):
        """测试修复 IndexError"""
        fixer = AutoFixer()
        code = "item = items[i]"
        error_log = "IndexError: list index out of range"

        result = fixer.fix_from_error_log(code, error_log)
        assert result.status in [FixStatus.SUCCESS, FixStatus.PARTIAL]

    def test_fix_zero_division(self):
        """测试修复 ZeroDivisionError"""
        fixer = AutoFixer()
        code = "result = a / b"
        error_log = "ZeroDivisionError: division by zero"

        result = fixer.fix_from_error_log(code, error_log)
        assert result.status in [FixStatus.SUCCESS, FixStatus.PARTIAL]

    def test_preview_fix(self):
        """测试预览修复"""
        fixer = AutoFixer()
        code = "value = data['key']"
        error_log = "KeyError: 'key'"

        diagnoser = ErrorDiagnoser()
        diagnosis = diagnoser.diagnose(error_log)
        diff = fixer.preview_fix(code, diagnosis)

        assert diff != "没有可应用的修复"

    def test_is_auto_fixable(self):
        """测试检查是否可自动修复"""
        fixer = AutoFixer()
        assert fixer.is_auto_fixable(ErrorType.KEY_ERROR) is True
        assert fixer.is_auto_fixable(ErrorType.SYNTAX_ERROR) is False

    def test_get_supported_errors(self):
        """测试获取支持的错误类型"""
        fixer = AutoFixer()
        supported = fixer.get_supported_errors()
        assert ErrorType.KEY_ERROR in supported
        assert ErrorType.INDEX_ERROR in supported

    def test_batch_fix(self):
        """测试批量修复"""
        fixer = AutoFixer()
        code = "value = data['key']\nitem = items[i]"
        error_logs = [
            "KeyError: 'key'",
            "IndexError: list index out of range",
        ]

        result = fixer.batch_fix(code, error_logs)
        assert len(result.replacements) > 0


class TestPatternCategory:
    """测试模式类别"""

    def test_pattern_categories(self):
        """测试所有模式类别"""
        categories = [
            PatternCategory.SYNTAX,
            PatternCategory.RUNTIME,
            PatternCategory.API,
            PatternCategory.EVENT,
            PatternCategory.CONFIG,
            PatternCategory.NETWORK,
            PatternCategory.MEMORY,
            PatternCategory.CUSTOM,
        ]
        for cat in categories:
            assert cat.value is not None


class TestAlertSeverity:
    """测试告警严重程度"""

    def test_alert_severities(self):
        """测试所有严重程度"""
        severities = [
            AlertSeverity.INFO,
            AlertSeverity.WARNING,
            AlertSeverity.ERROR,
            AlertSeverity.CRITICAL,
        ]
        for sev in severities:
            assert sev.value is not None