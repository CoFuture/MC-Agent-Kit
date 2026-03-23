"""
Code Tools Module

代码工具，提供格式化、Lint、测试等功能。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

__all__ = [
    "CodeTools",
    "format_code",
    "lint_code",
    "run_tests",
    "check_syntax",
]


class CodeTools:
    """代码工具类"""

    @staticmethod
    def format(
        code: str,
        language: str = "python",
        style: str = "pep8",
    ) -> dict[str, Any]:
        """格式化代码"""
        return format_code(code, language, style)

    @staticmethod
    def lint(
        code: str,
        language: str = "python",
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Lint 代码"""
        return lint_code(code, language, config)

    @staticmethod
    def test(
        path: str,
        pattern: str = "test_*.py",
        verbose: bool = True,
    ) -> dict[str, Any]:
        """运行测试"""
        return run_tests(path, pattern, verbose)

    @staticmethod
    def check_syntax(code: str, language: str = "python") -> dict[str, Any]:
        """检查语法"""
        return check_syntax(code, language)


def format_code(
    code: str,
    language: str = "python",
    style: str = "pep8",
) -> dict[str, Any]:
    """
    格式化代码

    Args:
        code: 代码内容
        language: 编程语言
        style: 代码风格

    Returns:
        格式化结果
    """
    try:
        if language != "python":
            return {
                "success": False,
                "error": f"Unsupported language: {language}",
            }

        # 使用 ruff 格式化（如果可用）
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "format", "--stdin-filename", "code.py"],
                input=code,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "formatted_code": result.stdout,
                    "original_length": len(code),
                    "formatted_length": len(result.stdout),
                }
            else:
                # 如果 ruff 不可用，使用内置简单格式化
                return _simple_format(code)

        except FileNotFoundError:
            # ruff 未安装，使用内置简单格式化
            return _simple_format(code)

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _simple_format(code: str) -> dict[str, Any]:
    """简单代码格式化"""
    try:
        lines = code.split("\n")
        formatted_lines = []

        indent_level = 0
        for line in lines:
            stripped = line.strip()

            if not stripped:
                formatted_lines.append("")
                continue

            # 减少缩进
            if stripped.startswith((")", "}", "]")):
                indent_level = max(0, indent_level - 1)

            formatted_lines.append("    " * indent_level + stripped)

            # 增加缩进
            if stripped.endswith((":", "{", "[", "(")):
                indent_level += 1

        formatted_code = "\n".join(formatted_lines)

        return {
            "success": True,
            "formatted_code": formatted_code,
            "original_length": len(code),
            "formatted_length": len(formatted_code),
            "note": "Simple formatting applied (ruff not available)",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def lint_code(
    code: str,
    language: str = "python",
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Lint 代码

    Args:
        code: 代码内容
        language: 编程语言
        config: Lint 配置

    Returns:
        Lint 结果
    """
    try:
        if language != "python":
            return {
                "success": False,
                "error": f"Unsupported language: {language}",
            }

        issues = []

        # 内置简单检查
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            # 检查行长度
            if len(line) > 100:
                issues.append({
                    "line": i,
                    "column": 100,
                    "type": "E501",
                    "message": "Line too long",
                    "severity": "warning",
                })

            # 检查尾随空格
            if line.rstrip() != line and line.strip():
                issues.append({
                    "line": i,
                    "column": len(line.rstrip()),
                    "type": "W291",
                    "message": "Trailing whitespace",
                    "severity": "warning",
                })

            # 检查 TODO 注释
            if "TODO" in line or "FIXME" in line:
                issues.append({
                    "line": i,
                    "column": line.find("TODO") if "TODO" in line else line.find("FIXME"),
                    "type": "TODO",
                    "message": "TODO/FIXME comment found",
                    "severity": "info",
                })

        # 尝试使用 ruff 检查
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", "--stdin-filename", "code.py"],
                input=code,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if line.startswith("code.py:"):
                        parts = line.split(":")
                        if len(parts) >= 4:
                            issues.append({
                                "line": int(parts[1]),
                                "column": int(parts[2]),
                                "type": parts[3].split()[0] if parts[3] else "E",
                                "message": line,
                                "severity": "error",
                            })

        except FileNotFoundError:
            pass

        return {
            "success": True,
            "issues": issues,
            "issue_count": len(issues),
            "error_count": sum(1 for i in issues if i.get("severity") == "error"),
            "warning_count": sum(1 for i in issues if i.get("severity") == "warning"),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def run_tests(
    path: str,
    pattern: str = "test_*.py",
    verbose: bool = True,
) -> dict[str, Any]:
    """
    运行测试

    Args:
        path: 测试路径
        pattern: 测试文件模式
        verbose: 是否详细输出

    Returns:
        测试结果
    """
    try:
        test_path = Path(path)

        if not test_path.exists():
            return {
                "success": False,
                "error": f"Test path not found: {path}",
            }

        # 构建 pytest 命令
        cmd = [sys.executable, "-m", "pytest"]

        if verbose:
            cmd.append("-v")

        cmd.extend([
            "--tb=short",
            "-q",
            str(test_path),
        ])

        # 运行测试
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        # 解析输出
        output = result.stdout + result.stderr
        passed = 0
        failed = 0
        skipped = 0
        errors = 0

        for line in output.split("\n"):
            if " passed" in line:
                parts = line.split()
                for part in parts:
                    if part.endswith("passed"):
                        try:
                            passed = int(part.replace("passed", ""))
                        except ValueError:
                            pass
            if " failed" in line:
                parts = line.split()
                for part in parts:
                    if part.endswith("failed"):
                        try:
                            failed = int(part.replace("failed", ""))
                        except ValueError:
                            pass
            if " skipped" in line:
                parts = line.split()
                for part in parts:
                    if part.endswith("skipped"):
                        try:
                            skipped = int(part.replace("skipped", ""))
                        except ValueError:
                            pass
            if " error" in line or " errors" in line:
                parts = line.split()
                for part in parts:
                    if "error" in part:
                        try:
                            errors = int(part.replace("errors", "").replace("error", ""))
                        except ValueError:
                            pass

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "total": passed + failed + skipped + errors,
            "output": output,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Test execution timed out",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def check_syntax(code: str, language: str = "python") -> dict[str, Any]:
    """
    检查语法

    Args:
        code: 代码内容
        language: 编程语言

    Returns:
        语法检查结果
    """
    try:
        if language != "python":
            return {
                "success": False,
                "error": f"Unsupported language: {language}",
            }

        # 使用 compile 检查语法
        compile(code, "<string>", "exec")

        return {
            "success": True,
            "valid": True,
            "message": "Syntax is valid",
        }

    except SyntaxError as e:
        return {
            "success": True,
            "valid": False,
            "error": str(e),
            "line": e.lineno,
            "column": e.offset,
            "message": e.msg,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }