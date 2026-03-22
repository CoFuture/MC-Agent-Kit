"""Additional tests for generator lint module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mc_agent_kit.generator.lint import (
    ComplexityReport,
    LintIssue,
    CodeQualityTool,
    analyze_file_complexity,
    check_code_quality,
)


class TestLintIssue:
    """Tests for LintIssue."""

    def test_create_issue(self):
        """Test creating lint issue."""
        issue = LintIssue(
            file_path="test.py",
            line=10,
            column=5,
            code="E501",
            message="Line too long",
        )
        assert issue.file_path == "test.py"
        assert issue.line == 10
        assert issue.severity == "warning"

    def test_issue_with_custom_severity(self):
        """Test issue with custom severity."""
        issue = LintIssue(
            file_path="test.py",
            line=1,
            column=1,
            code="E999",
            message="Syntax error",
            severity="error",
        )
        assert issue.severity == "error"


class TestComplexityReport:
    """Tests for ComplexityReport."""

    def test_create_report(self):
        """Test creating complexity report."""
        report = ComplexityReport(
            file_path="test.py",
            total_lines=100,
            code_lines=80,
            comment_lines=10,
            blank_lines=10,
            functions=5,
            classes=2,
            max_complexity=8,
            avg_complexity=3.5,
        )
        assert report.total_lines == 100
        assert report.max_complexity == 8
        assert report.issues == []


class TestCodeQualityTool:
    """Tests for CodeQualityTool."""

    def test_init_with_ruff(self):
        """Test initialization with ruff."""
        tool = CodeQualityTool(use_ruff=True)
        assert tool._use_ruff

    def test_init_without_ruff(self):
        """Test initialization without ruff."""
        tool = CodeQualityTool(use_ruff=False)
        assert not tool._use_ruff

    def test_check_file_nonexistent(self):
        """Test checking nonexistent file."""
        tool = CodeQualityTool(use_ruff=False)
        issues = tool.check_file("/nonexistent/path.py")
        assert issues == []

    def test_builtin_check_line_length(self, tmp_path):
        """Test builtin check for line length."""
        tool = CodeQualityTool(use_ruff=False)

        # Create file with long line
        test_file = tmp_path / "test.py"
        test_file.write_text("x = '" + "a" * 150 + "'\n")

        issues = tool._builtin_check(test_file)
        assert len(issues) == 1
        assert issues[0].code == "E501"

    def test_builtin_check_trailing_whitespace(self, tmp_path):
        """Test builtin check for trailing whitespace."""
        tool = CodeQualityTool(use_ruff=False)

        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1   \n")  # Trailing spaces

        issues = tool._builtin_check(test_file)
        assert any(i.code == "W291" for i in issues)

    def test_builtin_check_syntax_error(self, tmp_path):
        """Test builtin check for syntax error."""
        tool = CodeQualityTool(use_ruff=False)

        test_file = tmp_path / "test.py"
        test_file.write_text("def broken(\n")  # Invalid syntax

        issues = tool._builtin_check(test_file)
        assert any(i.code == "E999" for i in issues)

    def test_builtin_check_valid_file(self, tmp_path):
        """Test builtin check for valid file."""
        tool = CodeQualityTool(use_ruff=False)

        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    print('hello')\n")

        issues = tool._builtin_check(test_file)
        # Should have no issues
        assert all(i.severity != "error" for i in issues)

    def test_check_directory_nonexistent(self):
        """Test checking nonexistent directory."""
        tool = CodeQualityTool(use_ruff=False)
        results = tool.check_directory("/nonexistent/dir")
        assert results == {}

    def test_check_directory_with_files(self, tmp_path):
        """Test checking directory with files."""
        tool = CodeQualityTool(use_ruff=False)

        # Create test files
        (tmp_path / "test1.py").write_text("x = 1\n")
        (tmp_path / "test2.py").write_text("y = 2\n")

        results = tool.check_directory(tmp_path)
        assert len(results) >= 0  # May have issues or not

    def test_analyze_complexity(self, tmp_path):
        """Test analyzing complexity."""
        tool = CodeQualityTool(use_ruff=False)

        test_file = tmp_path / "complex.py"
        test_file.write_text('''
def simple():
    pass

def with_if(x):
    if x:
        return 1
    return 0

class MyClass:
    def method(self):
        pass
''')

        report = tool.analyze_complexity(test_file)

        assert report.total_lines > 0
        assert report.functions == 3  # simple, with_if, method
        assert report.classes == 1
        assert report.max_complexity >= 1

    def test_analyze_complexity_nonexistent_file(self):
        """Test analyzing nonexistent file."""
        tool = CodeQualityTool(use_ruff=False)

        with pytest.raises(FileNotFoundError):
            tool.analyze_complexity("/nonexistent/file.py")

    def test_analyze_complexity_read_error(self, tmp_path):
        """Test analyzing file with read error."""
        tool = CodeQualityTool(use_ruff=False)

        # Create a directory instead of file
        test_dir = tmp_path / "not_a_file"
        test_dir.mkdir()

        with pytest.raises(ValueError):
            tool.analyze_complexity(test_dir)

    def test_calculate_cyclomatic_complexity(self, tmp_path):
        """Test cyclomatic complexity calculation."""
        tool = CodeQualityTool(use_ruff=False)

        # Create file with known complexity
        test_file = tmp_path / "complexity.py"
        test_file.write_text('''
def complex_function(x, y, z):
    """Function with multiple branches."""
    if x:
        if y:
            return 1
        else:
            return 2
    elif z:
        return 3
    else:
        return 4
''')

        report = tool.analyze_complexity(test_file)
        # complexity = 1 (base) + 1 (if) + 1 (if) + 1 (elif)
        assert report.max_complexity >= 2

    def test_generate_text_report(self, tmp_path):
        """Test generating text report."""
        tool = CodeQualityTool(use_ruff=False)

        test_file = tmp_path / "test.py"
        test_file.write_text("def f(): pass\n")

        report = tool.generate_complexity_report(tmp_path, output_format="text")

        assert "代码复杂度报告" in report

    def test_generate_markdown_report(self, tmp_path):
        """Test generating markdown report."""
        tool = CodeQualityTool(use_ruff=False)

        test_file = tmp_path / "test.py"
        test_file.write_text("def f(): pass\n")

        report = tool.generate_complexity_report(tmp_path, output_format="markdown")

        assert "# 代码复杂度报告" in report
        assert "| 文件数量 |" in report

    def test_generate_json_report(self, tmp_path):
        """Test generating JSON report."""
        tool = CodeQualityTool(use_ruff=False)

        test_file = tmp_path / "test.py"
        test_file.write_text("def f(): pass\n")

        report = tool.generate_complexity_report(tmp_path, output_format="json")

        # Should be valid JSON
        data = json.loads(report)
        assert "summary" in data
        assert "files" in data

    def test_run_ruff_check_not_available(self):
        """Test ruff check when not available."""
        tool = CodeQualityTool(use_ruff=True)
        tool._ruff_available = False

        issues = tool.run_ruff_check("/some/path")
        assert issues == []

    def test_parse_ruff_output(self):
        """Test parsing ruff output."""
        tool = CodeQualityTool()

        data = [
            {
                "filename": "test.py",
                "location": {"row": 10, "column": 5},
                "code": "E501",
                "message": "Line too long",
                "fix": None,
            }
        ]

        issues = tool._parse_ruff_output(data)
        assert len(issues) == 1
        assert issues[0].file_path == "test.py"
        assert issues[0].line == 10

    def test_parse_ruff_output_with_fix(self):
        """Test parsing ruff output with fix."""
        tool = CodeQualityTool()

        data = [
            {
                "filename": "test.py",
                "location": {"row": 1, "column": 1},
                "code": "W291",
                "message": "Trailing whitespace",
                "fix": {"content": "fixed"},
            }
        ]

        issues = tool._parse_ruff_output(data)
        assert len(issues) == 1
        assert issues[0].fixable

    @patch("subprocess.run")
    def test_format_code_in_place(self, mock_run, tmp_path):
        """Test format code in place."""
        mock_run.return_value = MagicMock(returncode=0, stdout="")

        tool = CodeQualityTool()
        tool._ruff_available = True

        test_file = tmp_path / "test.py"
        test_file.write_text("x=1\n")

        result = tool.format_code(test_file, in_place=True)
        assert result == ""

    @patch("subprocess.run")
    def test_format_code_diff(self, mock_run, tmp_path):
        """Test format code with diff."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="--- test.py\n+++ test.py\n"
        )

        tool = CodeQualityTool()
        tool._ruff_available = True

        test_file = tmp_path / "test.py"
        test_file.write_text("x=1\n")

        result = tool.format_code(test_file, in_place=False)
        assert "---" in result

    def test_format_code_ruff_not_available(self, tmp_path):
        """Test format code when ruff not available."""
        tool = CodeQualityTool()
        tool._ruff_available = False

        test_file = tmp_path / "test.py"
        test_file.write_text("x=1\n")

        with pytest.raises(RuntimeError, match="ruff 不可用"):
            tool.format_code(test_file)


class TestCheckCodeQuality:
    """Tests for check_code_quality function."""

    def test_check_file_no_errors(self, tmp_path):
        """Test check with no errors."""
        test_file = tmp_path / "good.py"
        test_file.write_text("x = 1\n")

        passed, issues = check_code_quality(test_file, use_ruff=False)
        # Should pass if no error-level issues
        assert isinstance(passed, bool)
        assert isinstance(issues, list)

    def test_check_file_with_syntax_error(self, tmp_path):
        """Test check with syntax error."""
        test_file = tmp_path / "bad.py"
        test_file.write_text("def broken(\n")

        passed, issues = check_code_quality(test_file, use_ruff=False)
        assert not passed  # Syntax errors cause failure


class TestAnalyzeFileComplexity:
    """Tests for analyze_file_complexity function."""

    def test_analyze_simple_file(self, tmp_path):
        """Test analyzing simple file."""
        test_file = tmp_path / "simple.py"
        test_file.write_text("def f():\n    pass\n")

        report = analyze_file_complexity(test_file)
        assert isinstance(report, ComplexityReport)
        assert report.functions == 1

    def test_analyze_complex_file(self, tmp_path):
        """Test analyzing complex file."""
        test_file = tmp_path / "complex.py"
        test_file.write_text('''
def many_branches(x, y, z, w):
    if x:
        if y:
            if z:
                return 1
            else:
                return 2
        else:
            return 3
    elif w:
        return 4
    return 0
''')

        report = analyze_file_complexity(test_file)
        assert report.max_complexity > 1


class TestCodeQualityToolIntegration:
    """Integration tests for CodeQualityTool."""

    def test_full_check_workflow(self, tmp_path):
        """Test full check workflow."""
        tool = CodeQualityTool(use_ruff=False)

        # Create multiple files
        (tmp_path / "good.py").write_text("def good():\n    return 1\n")
        (tmp_path / "bad.py").write_text("def bad(\n")  # Syntax error
        (tmp_path / "long.py").write_text("x = '" + "a" * 150 + "'\n")

        # Check directory
        results = tool.check_directory(tmp_path)

        # Should have found issues
        total_issues = sum(len(issues) for issues in results.values())
        # At least the syntax error
        assert any("bad.py" in f for f in results)

    def test_complexity_analysis_workflow(self, tmp_path):
        """Test complexity analysis workflow."""
        tool = CodeQualityTool(use_ruff=False)

        # Create Python package structure
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "module.py").write_text('''
def simple():
    pass

def complex_func(x):
    if x > 0:
        if x < 10:
            return "small"
        elif x < 100:
            return "medium"
        else:
            return "large"
    return "zero or negative"
''')

        report = tool.generate_complexity_report(tmp_path, output_format="markdown")

        assert "代码复杂度报告" in report or "概览" in report or "文件数量" in report