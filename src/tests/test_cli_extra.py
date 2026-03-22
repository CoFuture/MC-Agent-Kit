"""
CLI extra tests for better coverage.

Tests for uncovered lines in cli.py.
"""

import json
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

import pytest

from mc_agent_kit import cli
from mc_agent_kit.skills import get_registry


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear Skill registry before each test"""
    registry = get_registry()
    registry._skills.clear()
    yield


class TestCLIListExtra:
    """Extra tests for list command"""

    def test_list_text_format_with_skills(self, capsys):
        """Test text format output with skills"""
        args = mock.MagicMock()
        args.format = "text"

        result = cli.cmd_list(args)
        assert result == 0

        captured = capsys.readouterr()
        # Should show skills in text format
        assert "Skills" in captured.out or "modsdk" in captured.out


class TestCLIAPIExtra:
    """Extra tests for api command"""

    def test_api_text_format_output(self, capsys):
        """Test text format output"""
        args = mock.MagicMock()
        args.format = "text"
        args.query = "GetEngine"
        args.name = None
        args.module = None
        args.scope = None
        args.limit = 3

        result = cli.cmd_api(args)
        assert result == 0

    def test_api_text_format_output(self, capsys):
        """Test text format output"""
        args = mock.MagicMock()
        args.format = "text"
        args.query = "GetEngine"
        args.name = None
        args.module = None
        args.scope = None
        args.limit = 3

        result = cli.cmd_api(args)
        assert result == 0

    def test_api_with_all_filters(self, capsys):
        """Test api with all filters applied"""
        args = mock.MagicMock()
        args.format = "json"
        args.query = "entity"
        args.name = None
        args.module = "实体"
        args.scope = "client"
        args.limit = 5

        result = cli.cmd_api(args)
        assert result == 0


class TestCLIEventExtra:
    """Extra tests for event command"""

    def test_event_text_format_output(self, capsys):
        """Test text format output for events"""
        args = mock.MagicMock()
        args.format = "text"
        args.query = "player"
        args.name = None
        args.module = None
        args.scope = None
        args.limit = 5

        result = cli.cmd_event(args)
        assert result == 0


class TestCLIGenExtra:
    """Extra tests for gen command"""

    def test_gen_skill_not_registered(self, capsys):
        """Test when skill not registered"""
        registry = get_registry()
        registry._skills.clear()

        args = mock.MagicMock()
        args.format = "text"
        args.template = "event_listener"
        args.params = "{}"
        args.action = "generate"
        args.keyword = None

        result = cli.cmd_gen(args)
        assert result == 1

    def test_gen_text_format_output(self, capsys):
        """Test text format output"""
        args = mock.MagicMock()
        args.format = "text"
        args.template = "event_listener"
        args.params = '{"event_name": "OnPlayerJoin", "handler_name": "on_join"}'
        args.action = "generate"
        args.keyword = None

        result = cli.cmd_gen(args)
        assert result == 0

    def test_gen_search_text_format(self, capsys):
        """Test search action with text format"""
        args = mock.MagicMock()
        args.format = "text"
        args.template = None
        args.params = None
        args.action = "search"
        args.keyword = "event"

        result = cli.cmd_gen(args)
        assert result == 0

    def test_gen_info_action(self, capsys):
        """Test info action"""
        args = mock.MagicMock()
        args.format = "json"
        args.template = "event_listener"
        args.params = None
        args.action = "info"
        args.keyword = None

        result = cli.cmd_gen(args)
        assert result == 0


class TestCLIDebugExtra:
    """Extra tests for debug command"""

    def test_debug_text_format_output(self, capsys):
        """Test text format output"""
        args = mock.MagicMock()
        args.format = "text"
        args.log = "SyntaxError: invalid syntax at line 10"
        args.file = None
        args.action = "diagnose"

        result = cli.cmd_debug(args)
        assert result == 0

    def test_debug_analyze_action(self, capsys):
        """Test analyze action"""
        args = mock.MagicMock()
        args.format = "json"
        args.log = "NameError: name 'x' is not defined"
        args.file = None
        args.action = "analyze"

        result = cli.cmd_debug(args)
        assert result == 0


class TestCLICompleteExtra:
    """Extra tests for complete command"""

    def test_complete_with_completions_text_format(self, capsys):
        """Test complete with results in text format"""
        from mc_agent_kit.completion import (
            Completion,
            CompletionContext,
            CompletionKind,
            CompletionResult,
        )

        args = mock.MagicMock()
        args.format = "text"
        args.code = "GetEngine"
        args.file = None
        args.line = 1
        args.column = 8
        args.prefix = "GetEngine"

        with mock.patch("mc_agent_kit.cli.CodeCompleter") as MockCompleter:
            mock_completer = mock.MagicMock()
            mock_completer.complete.return_value = CompletionResult(
                completions=[
                    Completion(
                        label="GetEngineType",
                        kind=CompletionKind.API,
                        detail="Get engine type",
                        documentation="Returns engine type",
                    ),
                    Completion(
                        label="GetEngineVersion",
                        kind=CompletionKind.API,
                        detail="Get engine version",
                    ),
                ],
                context=CompletionContext.from_code("GetEngine", 0, 8),
            )
            MockCompleter.return_value = mock_completer

            result = cli.cmd_complete(args)
            assert result == 0

            captured = capsys.readouterr()
            assert "GetEngineType" in captured.out or "补全建议" in captured.out

    def test_complete_with_detail_and_documentation(self, capsys):
        """Test complete with detail and documentation"""
        from mc_agent_kit.completion import (
            Completion,
            CompletionContext,
            CompletionKind,
            CompletionResult,
        )

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
                completions=[
                    Completion(
                        label="GetConfig",
                        kind=CompletionKind.API,
                        detail="Get configuration",
                        documentation="Returns the configuration object",
                    ),
                ],
                context=CompletionContext.from_code("Get", 0, 3),
            )
            MockCompleter.return_value = mock_completer

            result = cli.cmd_complete(args)
            assert result == 0


class TestCLIRefactorExtra:
    """Extra tests for refactor command"""

    def test_refactor_detect_with_smells_text_format(self, capsys):
        """Test detect with smells in text format"""
        code = "def test(): pass"

        args = mock.MagicMock()
        args.format = "text"
        args.code = code
        args.file = None
        args.action = "detect"

        result = cli.cmd_refactor(args)
        assert result == 0

    def test_refactor_detect_no_smells(self, capsys):
        """Test detect with no smells"""
        args = mock.MagicMock()
        args.format = "text"
        args.code = "def simple(): pass"
        args.file = None
        args.action = "detect"

        with mock.patch("mc_agent_kit.cli.SmellDetector") as MockDetector:
            mock_detector = mock.MagicMock()
            mock_detector.detect.return_value = []
            MockDetector.return_value = mock_detector

            result = cli.cmd_refactor(args)
            assert result == 0

            captured = capsys.readouterr()
            assert "未检测到" in captured.out or "✅" in captured.out

    def test_refactor_suggest_with_suggestions_text_format(self, capsys):
        """Test suggest with suggestions in text format"""
        from mc_agent_kit.completion import (
            CodeSmell,
            RefactorSuggestion,
            RefactorType,
            SmellCategory,
            SmellSeverity,
            SmellType,
        )

        args = mock.MagicMock()
        args.format = "text"
        args.code = "x = 42  # magic number"
        args.file = None
        args.action = "suggest"

        with mock.patch("mc_agent_kit.cli.SmellDetector") as MockDetector:
            with mock.patch("mc_agent_kit.cli.RefactorEngine") as MockEngine:
                mock_detector = mock.MagicMock()
                mock_detector.detect.return_value = [
                    CodeSmell(
                        type=SmellType.MAGIC_NUMBER,
                        message="Magic number found",
                        line=1,
                        severity=SmellSeverity.MINOR,
                        category=SmellCategory.MODSDK,
                    )
                ]
                MockDetector.return_value = mock_detector

                mock_engine = mock.MagicMock()
                mock_engine.suggest.return_value = [
                    RefactorSuggestion(
                        type=RefactorType.REPLACE_MAGIC_NUMBER,
                        message="Replace with constant",
                        line=1,
                        auto_applicable=True,
                    )
                ]
                MockEngine.return_value = mock_engine

                result = cli.cmd_refactor(args)
                assert result == 0

    def test_refactor_suggest_no_suggestions(self, capsys):
        """Test suggest with no suggestions"""
        args = mock.MagicMock()
        args.format = "text"
        args.code = "def clean(): pass"
        args.file = None
        args.action = "suggest"

        with mock.patch("mc_agent_kit.cli.SmellDetector") as MockDetector:
            with mock.patch("mc_agent_kit.cli.RefactorEngine") as MockEngine:
                mock_detector = mock.MagicMock()
                mock_detector.detect.return_value = []
                MockDetector.return_value = mock_detector

                mock_engine = mock.MagicMock()
                mock_engine.suggest.return_value = []
                MockEngine.return_value = mock_engine

                result = cli.cmd_refactor(args)
                assert result == 0

                captured = capsys.readouterr()
                assert "无需重构" in captured.out or "✅" in captured.out


class TestCLICheckExtra:
    """Extra tests for check command"""

    def test_check_text_format_output(self, capsys):
        """Test check with text format output"""
        code = '''
def test():
    x = 42
    return x
'''

        args = mock.MagicMock()
        args.format = "text"
        args.code = code
        args.file = None
        args.action = "check"

        result = cli.cmd_check(args)
        assert result == 0

    def test_check_list_text_format(self, capsys):
        """Test list action with text format"""
        args = mock.MagicMock()
        args.format = "text"
        args.code = None
        args.file = None
        args.action = "list"

        result = cli.cmd_check(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "最佳实践" in captured.out


class TestCLIAutofixExtra:
    """Extra tests for autofix command"""

    def test_autofix_diagnose_text_format(self, capsys):
        """Test diagnose with text format"""
        args = mock.MagicMock()
        args.format = "text"
        args.code = "x = data['key']"
        args.file = None
        args.error = "KeyError: 'key'"
        args.error_file = None
        args.action = "diagnose"

        result = cli.cmd_autofix(args)
        assert result == 0

    def test_autofix_fix_text_format(self, capsys):
        """Test fix with text format"""
        args = mock.MagicMock()
        args.format = "text"
        args.code = "x = data['key']"
        args.file = None
        args.error = "KeyError: 'key'"
        args.error_file = None
        args.action = "fix"

        result = cli.cmd_autofix(args)
        assert result == 0

    def test_autofix_preview_text_format(self, capsys):
        """Test preview with text format"""
        args = mock.MagicMock()
        args.format = "text"
        args.code = "x = data['key']"
        args.file = None
        args.error = "KeyError: 'key'"
        args.error_file = None
        args.action = "preview"

        result = cli.cmd_autofix(args)
        assert result == 0

    def test_autofix_with_replacements(self, capsys):
        """Test autofix with actual replacements"""
        args = mock.MagicMock()
        args.format = "text"
        args.code = "x = data['key']"
        args.file = None
        args.error = "KeyError: 'key'"
        args.error_file = None
        args.action = "fix"

        result = cli.cmd_autofix(args)
        assert result == 0


class TestPrintResultExtra:
    """Extra tests for print_result function"""

    def test_print_result_with_code_data(self, capsys):
        """Test print result with code in data"""
        result = {
            "success": True,
            "data": {
                "code": "def hello():\n    print('hello')",
                "template": "event_listener",
            }
        }
        cli.print_result(result, "text")
        captured = capsys.readouterr()
        assert "code" in captured.out

    def test_print_result_with_errors_data(self, capsys):
        """Test print result with errors in data"""
        result = {
            "success": True,
            "data": {
                "errors": [
                    {
                        "error_type": "SyntaxError",
                        "message": "Invalid syntax",
                        "suggestions": ["Fix the syntax"]
                    }
                ]
            }
        }
        cli.print_result(result, "text")
        captured = capsys.readouterr()
        assert "errors" in captured.out.lower() or "SyntaxError" in captured.out

    def test_print_result_with_long_list(self, capsys):
        """Test print result with long list data"""
        result = {
            "success": True,
            "data": {
                "items": list(range(20))
            }
        }
        cli.print_result(result, "text")
        captured = capsys.readouterr()
        assert "items" in captured.out

    def test_print_result_failure_with_suggestions(self, capsys):
        """Test print failure result with suggestions"""
        result = {
            "success": False,
            "message": "Operation failed",
            "error": "Error detail",
            "suggestions": ["Try this", "Or try that"]
        }
        cli.print_result(result, "text")
        captured = capsys.readouterr()
        assert "失败" in captured.out or "❌" in captured.out


class TestMainFunction:
    """Tests for main function"""

    def test_main_list_command(self):
        """Test list command via main"""
        with mock.patch.object(sys, "argv", ["mc-agent", "list", "--format", "json"]):
            result = cli.main()
            assert result == 0


class TestSetupSkills:
    """Tests for setup_skills function"""

    def test_setup_skills_registers_all(self):
        """Test that setup_skills registers all skills"""
        registry = get_registry()
        registry._skills.clear()

        cli.setup_skills()

        skills = registry.list_all()
        assert len(skills) > 0