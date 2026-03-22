"""
CLI 测试

测试 mc-agent 命令行工具的所有子命令。
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from mc_agent_kit import cli
from mc_agent_kit.skills import get_registry


@pytest.fixture(autouse=True)
def clear_registry():
    """每次测试前清除 Skill 注册表"""
    registry = get_registry()
    registry._skills.clear()
    yield


class TestCLIList:
    """测试 list 命令"""

    def test_list_text_format(self, capsys):
        """测试文本格式输出"""
        args = mock.MagicMock()
        args.format = "text"

        result = cli.cmd_list(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "已注册的 Skills" in captured.out
        assert "modsdk-api-search" in captured.out

    def test_list_json_format(self, capsys):
        """测试 JSON 格式输出"""
        args = mock.MagicMock()
        args.format = "json"

        result = cli.cmd_list(args)
        assert result == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert len(data) > 0
        assert "name" in data[0]


class TestCLIAPI:
    """测试 api 命令"""

    def test_api_search_query(self, capsys):
        """测试关键词搜索"""
        args = mock.MagicMock()
        args.format = "json"
        args.query = "entity"
        args.name = None
        args.module = None
        args.scope = None
        args.limit = 5

        result = cli.cmd_api(args)
        assert result == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data.get("success") is True

    def test_api_search_by_name(self, capsys):
        """测试按名称搜索"""
        args = mock.MagicMock()
        args.format = "json"
        args.query = None
        args.name = "GetEngineType"
        args.module = None
        args.scope = None
        args.limit = 5

        result = cli.cmd_api(args)
        assert result == 0

    def test_api_search_by_module(self, capsys):
        """测试按模块过滤"""
        args = mock.MagicMock()
        args.format = "json"
        args.query = None
        args.name = None
        args.module = "实体"
        args.scope = None
        args.limit = 5

        result = cli.cmd_api(args)
        assert result == 0

    def test_api_search_by_scope(self, capsys):
        """测试按作用域过滤"""
        args = mock.MagicMock()
        args.format = "json"
        args.query = "get"
        args.name = None
        args.module = None
        args.scope = "client"
        args.limit = 5

        result = cli.cmd_api(args)
        assert result == 0


class TestCLIEvent:
    """测试 event 命令"""

    def test_event_search_query(self, capsys):
        """测试关键词搜索"""
        args = mock.MagicMock()
        args.format = "json"
        args.query = "player"
        args.name = None
        args.module = None
        args.scope = None
        args.limit = 5

        result = cli.cmd_event(args)
        assert result == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data.get("success") is True

    def test_event_search_by_scope(self, capsys):
        """测试按作用域过滤"""
        args = mock.MagicMock()
        args.format = "json"
        args.query = "add"
        args.name = None
        args.module = None
        args.scope = "server"
        args.limit = 5

        result = cli.cmd_event(args)
        assert result == 0


class TestCLIGen:
    """测试 gen 命令"""

    def test_gen_list_templates(self, capsys):
        """测试列出模板"""
        args = mock.MagicMock()
        args.format = "json"
        args.template = None
        args.params = None
        args.action = "list"
        args.keyword = None

        result = cli.cmd_gen(args)
        assert result == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data.get("success") is True

    def test_gen_code(self, capsys):
        """测试生成代码"""
        args = mock.MagicMock()
        args.format = "json"
        args.template = "event_listener"
        args.params = '{"event_name": "OnPlayerJoin", "handler_name": "on_join"}'
        args.action = "generate"
        args.keyword = None

        result = cli.cmd_gen(args)
        assert result == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data.get("success") is True
        assert "code" in data.get("data", {})

    def test_gen_invalid_params(self, capsys):
        """测试无效参数"""
        args = mock.MagicMock()
        args.format = "text"
        args.template = "event_listener"
        args.params = "not valid json"
        args.action = "generate"
        args.keyword = None

        result = cli.cmd_gen(args)
        assert result == 1

    def test_gen_search(self, capsys):
        """测试搜索模板"""
        args = mock.MagicMock()
        args.format = "json"
        args.template = None
        args.params = None
        args.action = "search"
        args.keyword = "event"

        result = cli.cmd_gen(args)
        assert result == 0


class TestCLIDebug:
    """测试 debug 命令"""

    def test_debug_diagnose(self, capsys):
        """测试错误诊断"""
        args = mock.MagicMock()
        args.format = "json"
        args.log = "SyntaxError: invalid syntax at line 10"
        args.file = None
        args.action = "diagnose"

        result = cli.cmd_debug(args)
        assert result == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data.get("success") is True

    def test_debug_list_patterns(self, capsys):
        """测试列出错误模式"""
        args = mock.MagicMock()
        args.format = "json"
        args.log = None
        args.file = None
        args.action = "list_errors"

        result = cli.cmd_debug(args)
        assert result == 0

    def test_debug_from_file(self, tmp_path, capsys):
        """测试从文件读取日志"""
        log_file = tmp_path / "error.log"
        log_file.write_text("NameError: name 'x' is not defined")

        args = mock.MagicMock()
        args.format = "json"
        args.log = None
        args.file = str(log_file)
        args.action = "diagnose"

        result = cli.cmd_debug(args)
        assert result == 0

    def test_debug_file_not_found(self, capsys):
        """测试文件不存在"""
        args = mock.MagicMock()
        args.format = "text"
        args.log = None
        args.file = "/nonexistent/file.log"
        args.action = "diagnose"

        result = cli.cmd_debug(args)
        assert result == 1

    def test_debug_no_input(self, capsys):
        """测试无输入"""
        args = mock.MagicMock()
        args.format = "text"
        args.log = None
        args.file = None
        args.action = "diagnose"

        result = cli.cmd_debug(args)
        assert result == 1


class TestCLIComplete:
    """测试 complete 命令"""

    def test_complete_code(self, capsys):
        """测试代码补全"""
        from mc_agent_kit.completion import CompletionContext, Completion, CompletionKind, CompletionResult

        args = mock.MagicMock()
        args.format = "json"
        args.code = "Get"
        args.file = None
        args.line = 1
        args.column = 3
        args.prefix = "Get"

        # Mock completer
        with mock.patch("mc_agent_kit.cli.CodeCompleter") as MockCompleter:
            mock_completer = mock.MagicMock()
            mock_completer.complete.return_value = CompletionResult(
                completions=[
                    Completion(label="GetEngineType", kind=CompletionKind.API),
                ],
                context=CompletionContext.from_code("Get", 0, 3),
            )
            MockCompleter.return_value = mock_completer

            result = cli.cmd_complete(args)
            assert result == 0

            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert "items" in data

    def test_complete_from_file(self, tmp_path, capsys):
        """测试从文件读取代码"""
        from mc_agent_kit.completion import CompletionContext, Completion, CompletionKind, CompletionResult

        code_file = tmp_path / "code.py"
        code_file.write_text("GetConfig")

        args = mock.MagicMock()
        args.format = "json"
        args.code = None
        args.file = str(code_file)
        args.line = 1
        args.column = 10
        args.prefix = "GetConfig"

        with mock.patch("mc_agent_kit.cli.CodeCompleter") as MockCompleter:
            mock_completer = mock.MagicMock()
            mock_completer.complete.return_value = CompletionResult(
                completions=[],
                context=CompletionContext.from_code("GetConfig", 0, 9),
            )
            MockCompleter.return_value = mock_completer

            result = cli.cmd_complete(args)
            assert result == 0

    def test_complete_file_not_found(self, capsys):
        """测试文件不存在"""
        args = mock.MagicMock()
        args.format = "text"
        args.code = None
        args.file = "/nonexistent/code.py"
        args.line = 1
        args.column = 0
        args.prefix = None

        result = cli.cmd_complete(args)
        assert result == 1

    def test_complete_no_input(self, capsys):
        """测试无输入"""
        args = mock.MagicMock()
        args.format = "text"
        args.code = None
        args.file = None
        args.line = 1
        args.column = 0
        args.prefix = None

        result = cli.cmd_complete(args)
        assert result == 1

    def test_complete_text_format(self, capsys):
        """测试文本格式输出"""
        from mc_agent_kit.completion import CompletionContext, Completion, CompletionKind, CompletionResult

        args = mock.MagicMock()
        args.format = "text"
        args.code = "Get"
        args.file = None
        args.line = 1
        args.column = 3
        args.prefix = "Get"

        with mock.patch("mc_agent_kit.cli.CodeCompleter") as MockCompleter:
            mock_completer = mock.MagicMock()
            mock_completer.complete.return_value = CompletionResult(
                completions=[],
                context=CompletionContext.from_code("Get", 0, 3),
            )
            MockCompleter.return_value = mock_completer

            result = cli.cmd_complete(args)
            assert result == 0

            captured = capsys.readouterr()
            assert "补全建议" in captured.out or "没有找到" in captured.out


class TestCLIRefactor:
    """测试 refactor 命令"""

    def test_refactor_detect(self, capsys):
        """测试检测代码异味"""
        from mc_agent_kit.completion import SmellDetector, SmellType, SmellSeverity, CodeSmell, SmellCategory

        code = '''
def very_long_function_with_too_many_parameters(a, b, c, d, e, f, g, h):
    if a:
        if b:
            if c:
                if d:
                    return a + b + c + d
    return None
'''
        args = mock.MagicMock()
        args.format = "json"
        args.code = code
        args.file = None
        args.action = "detect"

        # Mock detector
        with mock.patch("mc_agent_kit.cli.SmellDetector") as MockDetector:
            mock_detector = mock.MagicMock()
            mock_detector.detect.return_value = [
                CodeSmell(
                    type=SmellType.LONG_FUNCTION,
                    message="Function is too long",
                    line=1,
                    severity=SmellSeverity.MAJOR,
                    category=SmellCategory.COMPLEXITY,
                )
            ]
            MockDetector.return_value = mock_detector

            result = cli.cmd_refactor(args)
            assert result == 0

            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert "smells" in data

    def test_refactor_suggest(self, capsys):
        """测试生成重构建议"""
        from mc_agent_kit.completion import SmellDetector, SmellType, SmellSeverity, CodeSmell, SmellCategory, RefactorEngine, RefactorSuggestion, RefactorType

        code = '''
def test():
    x = 1
    magic = 42
    return magic + x
'''
        args = mock.MagicMock()
        args.format = "json"
        args.code = code
        args.file = None
        args.action = "suggest"

        with mock.patch("mc_agent_kit.cli.SmellDetector") as MockDetector:
            with mock.patch("mc_agent_kit.cli.RefactorEngine") as MockEngine:
                mock_detector = mock.MagicMock()
                mock_detector.detect.return_value = [
                    CodeSmell(
                        type=SmellType.MAGIC_NUMBER,
                        message="Magic number 42",
                        line=3,
                        severity=SmellSeverity.MINOR,
                        category=SmellCategory.MODSDK,
                    )
                ]
                MockDetector.return_value = mock_detector

                mock_engine = mock.MagicMock()
                mock_engine.suggest.return_value = [
                    RefactorSuggestion(
                        type=RefactorType.REPLACE_MAGIC_NUMBER,
                        message="Replace magic number with constant",
                        line=3,
                        auto_applicable=True,
                    )
                ]
                MockEngine.return_value = mock_engine

                result = cli.cmd_refactor(args)
                assert result == 0

                captured = capsys.readouterr()
                data = json.loads(captured.out)
                assert "suggestions" in data

    def test_refactor_from_file(self, tmp_path, capsys):
        """测试从文件读取代码"""
        from mc_agent_kit.completion import SmellDetector, CodeSmell, SmellType, SmellSeverity, SmellCategory

        code_file = tmp_path / "code.py"
        code_file.write_text("def test(): pass")

        args = mock.MagicMock()
        args.format = "json"
        args.code = None
        args.file = str(code_file)
        args.action = "detect"

        with mock.patch("mc_agent_kit.cli.SmellDetector") as MockDetector:
            mock_detector = mock.MagicMock()
            mock_detector.detect.return_value = []
            MockDetector.return_value = mock_detector

            result = cli.cmd_refactor(args)
            assert result == 0

    def test_refactor_file_not_found(self, capsys):
        """测试文件不存在"""
        args = mock.MagicMock()
        args.format = "text"
        args.code = None
        args.file = "/nonexistent/code.py"
        args.action = "detect"

        result = cli.cmd_refactor(args)
        assert result == 1

    def test_refactor_no_input(self, capsys):
        """测试无输入"""
        args = mock.MagicMock()
        args.format = "text"
        args.code = None
        args.file = None
        args.action = "detect"

        result = cli.cmd_refactor(args)
        assert result == 1


class TestCLICheck:
    """测试 check 命令"""

    def test_check_code(self, capsys):
        """测试检查最佳实践"""
        code = '''
def test():
    # 魔法数字
    return 42
'''
        args = mock.MagicMock()
        args.format = "json"
        args.code = code
        args.file = None
        args.action = "check"

        result = cli.cmd_check(args)
        assert result == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "results" in data

    def test_check_list(self, capsys):
        """测试列出最佳实践"""
        args = mock.MagicMock()
        args.format = "json"
        args.code = None
        args.file = None
        args.action = "list"

        result = cli.cmd_check(args)
        assert result == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "practices" in data

    def test_check_from_file(self, tmp_path, capsys):
        """测试从文件读取代码"""
        code_file = tmp_path / "code.py"
        code_file.write_text("def test(): pass")

        args = mock.MagicMock()
        args.format = "json"
        args.code = None
        args.file = str(code_file)
        args.action = "check"

        result = cli.cmd_check(args)
        assert result == 0

    def test_check_file_not_found(self, capsys):
        """测试文件不存在"""
        args = mock.MagicMock()
        args.format = "text"
        args.code = None
        args.file = "/nonexistent/code.py"
        args.action = "check"

        result = cli.cmd_check(args)
        assert result == 1

    def test_check_no_input(self, capsys):
        """测试无输入"""
        args = mock.MagicMock()
        args.format = "text"
        args.code = None
        args.file = None
        args.action = "check"

        result = cli.cmd_check(args)
        assert result == 1


class TestCLIAutofix:
    """测试 autofix 命令"""

    def test_autofix_diagnose(self, capsys):
        """测试诊断错误"""
        args = mock.MagicMock()
        args.format = "json"
        args.code = "x = data['key']"
        args.file = None
        args.error = "KeyError: 'key'"
        args.error_file = None
        args.action = "diagnose"

        result = cli.cmd_autofix(args)
        assert result == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "error_type" in data

    def test_autofix_fix(self, capsys):
        """测试自动修复"""
        args = mock.MagicMock()
        args.format = "json"
        args.code = "x = data['key']"
        args.file = None
        args.error = "KeyError: 'key'"
        args.error_file = None
        args.action = "fix"

        result = cli.cmd_autofix(args)
        assert result == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "status" in data
        assert "fixed_code" in data

    def test_autofix_preview(self, capsys):
        """测试预览修复"""
        args = mock.MagicMock()
        args.format = "json"
        args.code = "x = data['key']"
        args.file = None
        args.error = "KeyError: 'key'"
        args.error_file = None
        args.action = "preview"

        result = cli.cmd_autofix(args)
        assert result == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "diff" in data

    def test_autofix_from_file(self, tmp_path, capsys):
        """测试从文件读取代码和错误"""
        code_file = tmp_path / "code.py"
        code_file.write_text("x = data['key']")
        error_file = tmp_path / "error.log"
        error_file.write_text("KeyError: 'key'")

        args = mock.MagicMock()
        args.format = "json"
        args.code = None
        args.file = str(code_file)
        args.error = None
        args.error_file = str(error_file)
        args.action = "diagnose"

        result = cli.cmd_autofix(args)
        assert result == 0

    def test_autofix_file_not_found(self, capsys):
        """测试文件不存在"""
        args = mock.MagicMock()
        args.format = "text"
        args.code = None
        args.file = "/nonexistent/code.py"
        args.error = "KeyError: 'key'"
        args.error_file = None
        args.action = "diagnose"

        result = cli.cmd_autofix(args)
        assert result == 1

    def test_autofix_error_file_not_found(self, tmp_path, capsys):
        """测试错误文件不存在"""
        code_file = tmp_path / "code.py"
        code_file.write_text("x = data['key']")

        args = mock.MagicMock()
        args.format = "text"
        args.code = None
        args.file = str(code_file)
        args.error = None
        args.error_file = "/nonexistent/error.log"
        args.action = "diagnose"

        result = cli.cmd_autofix(args)
        assert result == 1

    def test_autofix_no_input(self, capsys):
        """测试无输入"""
        args = mock.MagicMock()
        args.format = "text"
        args.code = None
        args.file = None
        args.error = "KeyError: 'key'"
        args.error_file = None
        args.action = "diagnose"

        result = cli.cmd_autofix(args)
        assert result == 1


class TestCLIMain:
    """测试主入口"""

    def test_main_no_command(self):
        """测试无命令时显示帮助"""
        with mock.patch.object(sys, "argv", ["mc-agent"]):
            result = cli.main()
            assert result == 0

    def test_main_help(self):
        """测试帮助选项"""
        with mock.patch.object(sys, "argv", ["mc-agent", "--help"]):
            with pytest.raises(SystemExit) as exc:
                cli.main()
            assert exc.value.code == 0

    def test_main_list(self):
        """测试 list 命令"""
        with mock.patch.object(sys, "argv", ["mc-agent", "list", "--format", "json"]):
            result = cli.main()
            assert result == 0

    def test_main_api(self):
        """测试 api 命令"""
        with mock.patch.object(sys, "argv", ["mc-agent", "api", "-q", "entity", "--format", "json"]):
            result = cli.main()
            assert result == 0

    def test_main_event(self):
        """测试 event 命令"""
        with mock.patch.object(sys, "argv", ["mc-agent", "event", "-q", "player", "--format", "json"]):
            result = cli.main()
            assert result == 0

    def test_main_gen(self):
        """测试 gen 命令"""
        with mock.patch.object(sys, "argv", ["mc-agent", "gen", "-a", "list", "--format", "json"]):
            result = cli.main()
            assert result == 0


class TestPrintResult:
    """测试 print_result 函数"""

    def test_print_success_text(self, capsys):
        """测试成功结果文本输出"""
        result = {
            "success": True,
            "message": "操作成功",
            "data": {"key": "value"}
        }
        cli.print_result(result, "text")
        captured = capsys.readouterr()
        assert "✅" in captured.out
        assert "操作成功" in captured.out

    def test_print_success_json(self, capsys):
        """测试成功结果 JSON 输出"""
        result = {
            "success": True,
            "message": "操作成功",
            "data": {"key": "value"}
        }
        cli.print_result(result, "json")
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["success"] is True

    def test_print_failure_text(self, capsys):
        """测试失败结果文本输出"""
        result = {
            "success": False,
            "message": "操作失败",
            "error": "错误详情"
        }
        cli.print_result(result, "text")
        captured = capsys.readouterr()
        assert "❌" in captured.out
        assert "操作失败" in captured.out

    def test_print_list_data(self, capsys):
        """测试列表数据输出"""
        result = {
            "success": True,
            "data": [
                {"name": "item1", "value": 1},
                {"name": "item2", "value": 2}
            ]
        }
        cli.print_result(result, "text")
        captured = capsys.readouterr()
        assert "[1]" in captured.out
        assert "item1" in captured.out

    def test_print_with_suggestions(self, capsys):
        """测试带建议的输出"""
        result = {
            "success": False,
            "message": "操作失败",
            "suggestions": ["建议1", "建议2"]
        }
        cli.print_result(result, "text")
        captured = capsys.readouterr()
        assert "建议:" in captured.out or "•" in captured.out



