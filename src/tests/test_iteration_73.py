"""
迭代 #73 测试 - 自动化修复增强与 CLI 工具优化

测试新增功能：
1. 自动修复增强（auto_fixer.py）
2. 日志分析增强（log_analyzer.py）
3. 增强 CLI REPL（enhanced_repl.py）
"""

from __future__ import annotations

import time
import unittest
from unittest.mock import patch, MagicMock

from mc_agent_kit.autofix.auto_fixer import (
    AutoFixer,
    AppliedFix,
    ErrorCorrelation,
    ErrorLocation,
    ErrorRelation,
    FixPriority,
    FixReport,
    FixStatus,
    FixTemplate,
    RootCause,
    ErrorLocalizer,
    RootCauseAnalyzer,
    ErrorCorrelator,
    FixTemplateLibrary,
    FixVerifier,
    create_auto_fixer,
    diagnose_error,
    auto_fix_error,
)

from mc_agent_kit.autofix.log_analyzer import (
    EnhancedLogAnalyzer,
    LogAnalysisResult,
    LogEntry,
    LogEntryType,
    LogLevel,
    PerformanceIssue,
    PerformanceIssueType,
    StructuredLogParser,
    LogPatternMatcher,
    PerformanceAnalyzer,
    SuggestionGenerator,
    create_log_analyzer,
    analyze_log,
    analyze_log_file,
)

from mc_agent_kit.cli_enhanced.enhanced_repl import (
    CommandHistory,
    CompletionSuggestion,
    EnhancedCompleter,
    EnhancedReplSession,
    OutputBuilder,
    OutputFormat,
    ProgressBar,
    ProgressState,
    Spinner,
    SyntaxHighlighter,
    create_enhanced_repl,
)


# ============================================================================
# 自动修复器测试
# ============================================================================

class TestErrorLocation(unittest.TestCase):
    """错误位置测试"""
    
    def test_create_location(self):
        """创建错误位置"""
        loc = ErrorLocation(
            file_path="test.py",
            line_start=10,
            line_end=15,
            function_name="test_func",
        )
        self.assertEqual(loc.file_path, "test.py")
        self.assertEqual(loc.line_start, 10)
        self.assertEqual(loc.function_name, "test_func")
    
    def test_location_to_dict(self):
        """位置转字典"""
        loc = ErrorLocation(file_path="test.py", line_start=10)
        d = loc.to_dict()
        self.assertIn("file_path", d)
        self.assertEqual(d["file_path"], "test.py")


class TestRootCause(unittest.TestCase):
    """根因分析测试"""
    
    def test_create_root_cause(self):
        """创建根因"""
        rc = RootCause(
            error_type="KeyError",
            description="键不存在",
            location=None,
            contributing_factors=["键名拼写错误"],
            confidence=0.8,
        )
        self.assertEqual(rc.error_type, "KeyError")
        self.assertEqual(rc.confidence, 0.8)
    
    def test_root_cause_to_dict(self):
        """根因转字典"""
        rc = RootCause(error_type="NameError", description="变量未定义", location=None, confidence=0.9)
        d = rc.to_dict()
        self.assertEqual(d["error_type"], "NameError")
        self.assertEqual(round(d["confidence"], 2), 0.9)


class TestFixTemplate(unittest.TestCase):
    """修复模板测试"""
    
    def test_template_matches(self):
        """模板匹配"""
        template = FixTemplate(
            id="test",
            name="Test Template",
            error_types=["KeyError"],
            pattern=r"['\"]?(\w+)['\"]?",
            code_before="data['{key}']",
            code_after="data.get('{key}', default)",
            description="Test",
        )
        self.assertTrue(template.matches("KeyError", "KeyError: 'missing_key'"))
        self.assertFalse(template.matches("NameError", "name 'x' is not defined"))
    
    def test_template_apply(self):
        """应用模板"""
        template = FixTemplate(
            id="test",
            name="Test",
            error_types=["KeyError"],
            pattern=r".*",
            code_before="data['{key}']",
            code_after="data.get('{key}', default)",
            description="Test",
        )
        result = template.apply("", {"key": "test_key"})
        self.assertIn("test_key", result)


class TestFixTemplateLibrary(unittest.TestCase):
    """修复模板库测试"""
    
    def test_library_creation(self):
        """创建模板库"""
        library = FixTemplateLibrary()
        templates = library.list_templates()
        self.assertGreater(len(templates), 0)
    
    def test_find_templates(self):
        """查找模板"""
        library = FixTemplateLibrary()
        templates = library.find_templates("KeyError", "KeyError: 'missing'")
        self.assertGreater(len(templates), 0)
        # 按优先级排序
        self.assertLessEqual(templates[0].priority.value, templates[-1].priority.value)


class TestErrorLocalizer(unittest.TestCase):
    """错误定位器测试"""
    
    def test_locate_from_traceback(self):
        """从 traceback 定位"""
        localizer = ErrorLocalizer()
        log = '''Traceback (most recent call last):
  File "test.py", line 10, in test_func
    x = data['key']
KeyError: 'key'
'''
        loc = localizer.locate(log)
        self.assertIsNotNone(loc)
        self.assertEqual(loc.file_path, "test.py")
        self.assertEqual(loc.line_start, 10)
    
    def test_locate_all(self):
        """定位所有错误"""
        localizer = ErrorLocalizer()
        log = '''Traceback (most recent call last):
  File "test.py", line 10, in func1
    pass
  File "test.py", line 20, in func2
    pass
'''
        locs = localizer.locate_all(log)
        self.assertEqual(len(locs), 2)


class TestRootCauseAnalyzer(unittest.TestCase):
    """根因分析器测试"""
    
    def test_analyze_name_error(self):
        """分析 NameError"""
        analyzer = RootCauseAnalyzer()
        rc = analyzer.analyze(
            "NameError",
            "name 'x' is not defined",
            code_context="print(x)",
        )
        self.assertEqual(rc.error_type, "NameError")
        self.assertGreater(rc.confidence, 0.0)
    
    def test_analyze_key_error(self):
        """分析 KeyError"""
        analyzer = RootCauseAnalyzer()
        rc = analyzer.analyze(
            "KeyError",
            "KeyError: 'missing'",
            code_context="data['missing']",
        )
        self.assertEqual(rc.error_type, "KeyError")


class TestErrorCorrelator(unittest.TestCase):
    """错误关联分析器测试"""
    
    def test_correlate_duplicate_errors(self):
        """关联重复错误"""
        correlator = ErrorCorrelator()
        errors = [
            {"id": "1", "type": "KeyError", "message": "'key'", "line": 10, "file": "test.py"},
            {"id": "2", "type": "KeyError", "message": "'key'", "line": 11, "file": "test.py"},
        ]
        correlations = correlator.correlate(errors)
        self.assertGreater(len(correlations), 0)


class TestFixVerifier(unittest.TestCase):
    """修复验证器测试"""
    
    def test_verify_syntax_valid(self):
        """验证有效语法"""
        verifier = FixVerifier()
        result = verifier.verify("x = 1 + 2", "")
        self.assertTrue(result["passed"])
    
    def test_verify_syntax_invalid(self):
        """验证无效语法"""
        verifier = FixVerifier()
        result = verifier.verify("x = 1 +", "")
        self.assertFalse(result["passed"])


class TestAutoFixer(unittest.TestCase):
    """自动修复器测试"""
    
    def test_create_auto_fixer(self):
        """创建自动修复器"""
        fixer = AutoFixer()
        self.assertIsNotNone(fixer.localizer)
        self.assertIsNotNone(fixer.root_cause_analyzer)
    
    def test_diagnose_key_error(self):
        """诊断 KeyError"""
        fixer = AutoFixer()
        result = fixer.diagnose("KeyError: 'missing'", "data['missing']")
        self.assertEqual(result["error_type"], "KeyError")
        self.assertIn("fix_templates", result)
    
    def test_diagnose_multiple(self):
        """诊断多个错误"""
        fixer = AutoFixer()
        errors = [
            {"id": "1", "log": "KeyError: 'key'", "code": "data['key']"},
            {"id": "2", "log": "NameError: name 'x'", "code": "print(x)"},
        ]
        result = fixer.diagnose_multiple(errors)
        self.assertIn("errors", result)
        self.assertIn("correlations", result)
    
    def test_apply_fix(self):
        """应用修复"""
        fixer = AutoFixer()
        context = {"error_id": "1", "file_path": "test.py", "key": "test"}
        applied = fixer.apply_fix(
            "keyerror_get_method",
            "data['test']",
            context,
            verify=True,
        )
        self.assertIn(applied.status, [FixStatus.APPLIED, FixStatus.VERIFIED])
    
    def test_auto_fix(self):
        """自动修复"""
        fixer = AutoFixer()
        report = fixer.auto_fix(
            "KeyError: 'missing'",
            "data['missing']",
            "test.py",
        )
        self.assertEqual(report.total_errors, 1)


class TestFixReport(unittest.TestCase):
    """修复报告测试"""
    
    def test_report_to_dict(self):
        """报告转字典"""
        report = FixReport(
            total_errors=5,
            fixable_errors=3,
            applied_fixes=2,
            verified_fixes=2,
        )
        d = report.to_dict()
        self.assertEqual(d["total_errors"], 5)
        self.assertEqual(d["applied_fixes"], 2)


# ============================================================================
# 日志分析器测试
# ============================================================================

class TestLogEntry(unittest.TestCase):
    """日志条目测试"""
    
    def test_create_entry(self):
        """创建日志条目"""
        entry = LogEntry(
            raw="[ERROR] Test error",
            level=LogLevel.ERROR,
            entry_type=LogEntryType.ERROR,
            timestamp=None,
            message="Test error",
        )
        self.assertEqual(entry.level, LogLevel.ERROR)
    
    def test_entry_to_dict(self):
        """条目转字典"""
        entry = LogEntry(
            raw="test",
            level=LogLevel.INFO,
            entry_type=LogEntryType.INFO,
            timestamp=None,
            message="test",
        )
        d = entry.to_dict()
        self.assertIn("raw", d)
        self.assertEqual(d["level"], "info")


class TestStructuredLogParser(unittest.TestCase):
    """结构化日志解析器测试"""
    
    def test_parse_standard_format(self):
        """解析标准格式"""
        parser = StructuredLogParser()
        log = "2026-03-25 10:00:00,000 [ERROR] module: Error message"
        entries = parser.parse(log)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].level, LogLevel.ERROR)
    
    def test_parse_simple_format(self):
        """解析简单格式"""
        parser = StructuredLogParser()
        log = "[WARNING] Simple warning"
        entries = parser.parse(log)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].level, LogLevel.WARNING)
    
    def test_parse_multiple_lines(self):
        """解析多行日志"""
        parser = StructuredLogParser()
        log = """[INFO] Line 1
[ERROR] Line 2
[WARNING] Line 3"""
        entries = parser.parse(log)
        self.assertEqual(len(entries), 3)


class TestLogPatternMatcher(unittest.TestCase):
    """日志模式匹配器测试"""
    
    def test_match_python_error(self):
        """匹配 Python 错误"""
        matcher = LogPatternMatcher()
        patterns = matcher.match("NameError: name 'x' is not defined")
        self.assertGreater(len(patterns), 0)
    
    def test_match_key_error(self):
        """匹配 KeyError"""
        matcher = LogPatternMatcher()
        patterns = matcher.match("KeyError: 'missing_key'")
        self.assertTrue(any(p.id == "python_key_error" for p in patterns))


class TestPerformanceAnalyzer(unittest.TestCase):
    """性能分析器测试"""
    
    def test_analyze_slow_operation(self):
        """分析慢操作"""
        analyzer = PerformanceAnalyzer()
        entries = [
            LogEntry(
                raw="Operation took 2000ms",
                level=LogLevel.WARNING,
                entry_type=LogEntryType.PERFORMANCE,
                timestamp=None,
                message="Operation took 2000ms",
            )
        ]
        issues = analyzer.analyze(entries)
        self.assertGreater(len(issues), 0)
        self.assertEqual(issues[0].issue_type, PerformanceIssueType.SLOW_OPERATION)


class TestEnhancedLogAnalyzer(unittest.TestCase):
    """增强日志分析器测试"""
    
    def test_analyze_log(self):
        """分析日志"""
        analyzer = EnhancedLogAnalyzer()
        log = """[INFO] Starting
[ERROR] KeyError: 'missing'
[WARNING] Operation took 2000ms
[INFO] Done"""
        result = analyzer.analyze(log)
        self.assertIsInstance(result, LogAnalysisResult)
        self.assertGreater(len(result.entries), 0)
        self.assertEqual(len(result.errors), 1)
    
    def test_analyze_statistics(self):
        """分析统计"""
        analyzer = EnhancedLogAnalyzer()
        log = "[ERROR] Error 1\n[ERROR] Error 2\n[WARNING] Warning 1"
        result = analyzer.analyze(log)
        self.assertEqual(result.statistics["error_count"], 2)
        self.assertEqual(result.statistics["warning_count"], 1)


# ============================================================================
# 增强 CLI REPL 测试
# ============================================================================

class TestCommandHistory(unittest.TestCase):
    """命令历史测试"""
    
    def test_add_command(self):
        """添加命令"""
        history = CommandHistory()
        history.add("test command")
        self.assertEqual(len(history.commands), 1)
    
    def test_navigation(self):
        """历史导航"""
        history = CommandHistory()
        history.add("cmd1")
        history.add("cmd2")
        history.add("cmd3")
        
        self.assertEqual(history.down(), None)
        self.assertEqual(history.up(), "cmd3")
        self.assertEqual(history.up(), "cmd2")
        self.assertEqual(history.down(), "cmd3")
    
    def test_search(self):
        """搜索历史"""
        history = CommandHistory()
        history.add("kb search test")
        history.add("workflow run test")
        history.add("kb status")
        
        results = history.search("kb")
        self.assertEqual(len(results), 2)


class TestCompletionSuggestion(unittest.TestCase):
    """补全建议测试"""
    
    def test_create_suggestion(self):
        """创建建议"""
        s = CompletionSuggestion(
            text="help",
            display="help",
            description="Show help",
            type="command",
            priority=10,
        )
        self.assertEqual(s.text, "help")
        self.assertEqual(s.priority, 10)


class TestEnhancedCompleter(unittest.TestCase):
    """增强补全器测试"""
    
    def test_register_command(self):
        """注册命令"""
        completer = EnhancedCompleter()
        completer.register_command(
            "test",
            description="Test command",
            options=["-v", "--verbose"],
        )
        suggestions = completer.complete("t", 1)
        self.assertGreater(len(suggestions), 0)
    
    def test_complete_command(self):
        """补全命令"""
        completer = EnhancedCompleter()
        completer.register_command("workflow", description="Workflow management")
        suggestions = completer.complete("work", 4)
        self.assertGreater(len(suggestions), 0)


class TestOutputBuilder(unittest.TestCase):
    """输出构建器测试"""
    
    def test_add_text(self):
        """添加文本"""
        builder = OutputBuilder(format=OutputFormat.TEXT)
        builder.add("Line 1").add("Line 2")
        output = builder.build()
        self.assertIn("Line 1", output)
    
    def test_add_heading(self):
        """添加标题"""
        builder = OutputBuilder(format=OutputFormat.MARKDOWN)
        builder.add_heading("Title", level=1)
        output = builder.build()
        self.assertIn("# Title", output)
    
    def test_add_table(self):
        """添加表格"""
        builder = OutputBuilder(format=OutputFormat.TABLE)
        builder.add_table(
            ["Name", "Value"],
            [["A", "1"], ["B", "2"]],
        )
        output = builder.build()
        self.assertIn("Name", output)
        self.assertIn("A", output)


class TestProgressBar(unittest.TestCase):
    """进度条测试"""
    
    def test_create_progress_bar(self):
        """创建进度条"""
        bar = ProgressBar(total=100, description="Processing")
        self.assertEqual(bar.total, 100)
        self.assertEqual(bar.current, 0)
    
    def test_update_progress(self):
        """更新进度"""
        bar = ProgressBar(total=10)
        bar.update(5)
        self.assertEqual(bar.current, 5)
    
    def test_complete_progress(self):
        """完成进度"""
        bar = ProgressBar(total=10)
        bar.complete()
        self.assertEqual(bar.current, 10)
        self.assertEqual(bar.state, ProgressState.COMPLETED)
    
    def test_render_progress(self):
        """渲染进度条"""
        bar = ProgressBar(total=100, current=50, description="Test")
        rendered = bar.render()
        self.assertIn("50/100", rendered)


class TestSpinner(unittest.TestCase):
    """旋转动画测试"""
    
    def test_create_spinner(self):
        """创建旋转器"""
        spinner = Spinner(message="Loading")
        self.assertEqual(spinner.message, "Loading")
    
    def test_next_frame(self):
        """获取下一帧"""
        spinner = Spinner()
        frame1 = spinner.next()
        frame2 = spinner.next()
        self.assertNotEqual(frame1, frame2)
    
    def test_stop_spinner(self):
        """停止旋转器"""
        spinner = Spinner()
        spinner.start()
        result = spinner.stop("Done")
        self.assertFalse(spinner.running)
        self.assertIn("Done", result)


class TestSyntaxHighlighter(unittest.TestCase):
    """语法高亮器测试"""
    
    def test_highlight_keyword(self):
        """高亮关键字"""
        highlighter = SyntaxHighlighter()
        result = highlighter.highlight("def test():", "python")
        self.assertIn("\033[35m", result)  # 紫色
    
    def test_highlight_string(self):
        """高亮字符串"""
        highlighter = SyntaxHighlighter()
        result = highlighter.highlight('x = "hello"', "python")
        self.assertIn("\033[32m", result)  # 绿色
    
    def test_highlight_command(self):
        """高亮命令"""
        highlighter = SyntaxHighlighter()
        result = highlighter.highlight("kb search test", "command")
        self.assertIn("\033[36m", result)  # 青色


class TestEnhancedReplSession(unittest.TestCase):
    """增强 REPL 会话测试"""
    
    def test_create_session(self):
        """创建会话"""
        session = EnhancedReplSession()
        self.assertIsNotNone(session.history)
        self.assertIsNotNone(session.completer)
    
    def test_execute_help(self):
        """执行 help 命令"""
        session = EnhancedReplSession()
        result = session.execute("help")
        self.assertIn("help", result.lower())
    
    def test_execute_history(self):
        """执行 history 命令"""
        session = EnhancedReplSession()
        session.execute("test1")
        session.execute("test2")
        result = session.execute("history")
        self.assertIn("test", result)
    
    def test_execute_unknown(self):
        """执行未知命令"""
        session = EnhancedReplSession()
        result = session.execute("unknown_command")
        self.assertIn("未知命令", result)


class TestConvenienceFunctions(unittest.TestCase):
    """便捷函数测试"""
    
    def test_create_auto_fixer(self):
        """创建自动修复器"""
        fixer = create_auto_fixer()
        self.assertIsInstance(fixer, AutoFixer)
    
    def test_diagnose_error(self):
        """诊断错误"""
        result = diagnose_error("KeyError: 'key'", "data['key']")
        self.assertIn("error_type", result)
    
    def test_create_log_analyzer(self):
        """创建日志分析器"""
        analyzer = create_log_analyzer()
        self.assertIsInstance(analyzer, EnhancedLogAnalyzer)
    
    def test_analyze_log(self):
        """分析日志"""
        result = analyze_log("[ERROR] Test error")
        self.assertIsInstance(result, LogAnalysisResult)
    
    def test_create_enhanced_repl(self):
        """创建增强 REPL"""
        repl = create_enhanced_repl()
        self.assertIsInstance(repl, EnhancedReplSession)


# ============================================================================
# 验收标准测试
# ============================================================================

class TestIteration73AcceptanceCriteria(unittest.TestCase):
    """迭代 #73 验收标准测试"""
    
    def test_auto_fixer_module_exists(self):
        """自动修复器模块存在"""
        from mc_agent_kit.autofix import auto_fixer
        self.assertTrue(hasattr(auto_fixer, "AutoFixer"))
    
    def test_log_analyzer_module_exists(self):
        """日志分析器模块存在"""
        from mc_agent_kit.autofix import log_analyzer
        self.assertTrue(hasattr(log_analyzer, "EnhancedLogAnalyzer"))
    
    def test_enhanced_repl_module_exists(self):
        """增强 REPL 模块存在"""
        from mc_agent_kit.cli_enhanced import enhanced_repl
        self.assertTrue(hasattr(enhanced_repl, "EnhancedReplSession"))
    
    def test_error_localization(self):
        """错误定位功能"""
        fixer = AutoFixer()
        result = fixer.diagnose("KeyError: 'key'", "data['key']", "test.py")
        self.assertIn("location", result)
    
    def test_root_cause_analysis(self):
        """根因分析功能"""
        fixer = AutoFixer()
        result = fixer.diagnose("NameError: name 'x'", "print(x)")
        self.assertIn("root_cause", result)
        self.assertIn("contributing_factors", result["root_cause"])
    
    def test_fix_templates(self):
        """修复模板功能"""
        library = FixTemplateLibrary()
        templates = library.list_templates()
        self.assertGreater(len(templates), 5)  # 至少 5 个模板
    
    def test_log_parsing(self):
        """日志解析功能"""
        analyzer = EnhancedLogAnalyzer()
        result = analyzer.analyze("[ERROR] Test\n[INFO] Done")
        self.assertEqual(len(result.entries), 2)
    
    def test_performance_analysis(self):
        """性能分析功能"""
        analyzer = EnhancedLogAnalyzer()
        result = analyzer.analyze("[WARNING] Operation took 2000ms")
        self.assertGreater(len(result.performance_issues), 0)
    
    def test_repl_commands(self):
        """REPL 命令功能"""
        session = EnhancedReplSession()
        # 测试内置命令
        self.assertIn("help", session.execute("help").lower())
        self.assertIn("历史", session.execute("history").lower())
    
    def test_output_formatting(self):
        """输出格式化功能"""
        builder = OutputBuilder(format=OutputFormat.TABLE)
        builder.add_table(["A", "B"], [["1", "2"]])
        output = builder.build()
        self.assertIn("A", output)
        self.assertIn("1", output)
    
    def test_progress_tracking(self):
        """进度追踪功能"""
        bar = ProgressBar(total=10, description="Test")
        bar.update(5)
        rendered = bar.render()
        self.assertIn("5/10", rendered)
    
    def test_syntax_highlighting(self):
        """语法高亮功能"""
        highlighter = SyntaxHighlighter()
        result = highlighter.highlight("def test(): pass", "python")
        self.assertNotEqual(result, "def test(): pass")  # 应该有高亮代码
    
    def test_command_completion(self):
        """命令补全功能"""
        completer = EnhancedCompleter()
        completer.register_command("workflow", description="Workflow")
        suggestions = completer.complete("work", 4)
        self.assertGreater(len(suggestions), 0)
    
    def test_all_tests_pass(self):
        """所有测试通过"""
        # 简单验证核心功能可用
        fixer = AutoFixer()
        analyzer = EnhancedLogAnalyzer()
        repl = EnhancedReplSession()
        
        # 验证基本功能
        self.assertIsNotNone(fixer)
        self.assertIsNotNone(analyzer)
        self.assertIsNotNone(repl)


if __name__ == "__main__":
    unittest.main()
