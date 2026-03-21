"""
代码质量工具

提供代码格式化检查、复杂度分析等功能。
"""

import ast
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class LintIssue:
    """代码问题"""

    file_path: str
    line: int
    column: int
    code: str
    message: str
    severity: str = "warning"  # error, warning, info
    fixable: bool = False


@dataclass
class ComplexityReport:
    """复杂度报告"""

    file_path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    functions: int
    classes: int
    max_complexity: int
    avg_complexity: float
    issues: list[LintIssue] = field(default_factory=list)


class CodeQualityTool:
    """代码质量工具

    提供代码检查、格式化、复杂度分析等功能。

    使用示例:
        tool = CodeQualityTool()

        # 检查文件
        issues = tool.check_file("path/to/file.py")

        # 复杂度分析
        report = tool.analyze_complexity("path/to/file.py")

        # 运行 ruff 检查
        issues = tool.run_ruff_check("path/to/code")
    """

    def __init__(self, use_ruff: bool = True):
        """初始化代码质量工具

        Args:
            use_ruff: 是否使用 ruff 进行检查
        """
        self._use_ruff = use_ruff
        self._ruff_available = self._check_ruff_available()

    def _check_ruff_available(self) -> bool:
        """检查 ruff 是否可用"""
        try:
            result = subprocess.run(
                ["ruff", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def check_file(self, file_path: str | Path) -> list[LintIssue]:
        """检查单个文件

        Args:
            file_path: 文件路径

        Returns:
            问题列表
        """
        issues = []

        # 使用 ruff 检查
        if self._use_ruff and self._ruff_available:
            issues.extend(self.run_ruff_check(file_path))
        else:
            # 使用内置检查
            issues.extend(self._builtin_check(file_path))

        return issues

    def check_directory(
        self,
        directory: str | Path,
        recursive: bool = True,
    ) -> dict[str, list[LintIssue]]:
        """检查目录

        Args:
            directory: 目录路径
            recursive: 是否递归检查

        Returns:
            文件路径 -> 问题列表
        """
        dir_path = Path(directory)
        results: dict[str, list[LintIssue]] = {}

        if not dir_path.exists():
            logger.warning(f"目录不存在: {directory}")
            return results

        # 使用 ruff 批量检查
        if self._use_ruff and self._ruff_available:
            issues = self.run_ruff_check(dir_path)
            for issue in issues:
                if issue.file_path not in results:
                    results[issue.file_path] = []
                results[issue.file_path].append(issue)
        else:
            # 内置检查
            pattern = "**/*.py" if recursive else "*.py"
            for py_file in dir_path.glob(pattern):
                issues = self._builtin_check(py_file)
                if issues:
                    results[str(py_file)] = issues

        return results

    def run_ruff_check(
        self,
        path: str | Path,
        fix: bool = False,
    ) -> list[LintIssue]:
        """运行 ruff 检查

        Args:
            path: 文件或目录路径
            fix: 是否自动修复

        Returns:
            问题列表
        """
        if not self._ruff_available:
            logger.warning("ruff 不可用，跳过检查")
            return []

        cmd = ["ruff", "check", str(path), "--output-format=json"]
        if fix:
            cmd.append("--fix")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            # ruff 返回非零表示有问题
            if result.returncode != 0 and result.stdout:
                import json

                try:
                    data = json.loads(result.stdout)
                    return self._parse_ruff_output(data)
                except json.JSONDecodeError:
                    pass

        except subprocess.SubprocessError as e:
            logger.error(f"ruff 检查失败: {e}")

        return []

    def _parse_ruff_output(self, data: list[dict]) -> list[LintIssue]:
        """解析 ruff 输出"""
        issues = []
        for item in data:
            issues.append(
                LintIssue(
                    file_path=item.get("filename", ""),
                    line=item.get("location", {}).get("row", 0),
                    column=item.get("location", {}).get("column", 0),
                    code=item.get("code", ""),
                    message=item.get("message", ""),
                    severity="error"
                    if "error" in item.get("code", "").lower()
                    else "warning",
                    fixable=item.get("fix") is not None,
                )
            )
        return issues

    def _builtin_check(self, file_path: str | Path) -> list[LintIssue]:
        """内置检查

        Args:
            file_path: 文件路径

        Returns:
            问题列表
        """
        issues = []
        path = Path(file_path)

        if not path.exists():
            return issues

        try:
            content = path.read_text(encoding="utf-8")
            lines = content.split("\n")
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return issues

        # 检查行长度
        max_line_length = 100
        for i, line in enumerate(lines, 1):
            if len(line) > max_line_length:
                issues.append(
                    LintIssue(
                        file_path=str(path),
                        line=i,
                        column=max_line_length,
                        code="E501",
                        message=f"行过长 ({len(line)} > {max_line_length})",
                        severity="warning",
                        fixable=False,
                    )
                )

        # 检查尾随空白
        for i, line in enumerate(lines, 1):
            if line.rstrip() != line and line.strip():
                issues.append(
                    LintIssue(
                        file_path=str(path),
                        line=i,
                        column=len(line.rstrip()),
                        code="W291",
                        message="尾随空白",
                        severity="info",
                        fixable=True,
                    )
                )

        # 检查语法
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append(
                LintIssue(
                    file_path=str(path),
                    line=e.lineno or 0,
                    column=e.offset or 0,
                    code="E999",
                    message=f"语法错误: {e.msg}",
                    severity="error",
                    fixable=False,
                )
            )

        return issues

    def analyze_complexity(self, file_path: str | Path) -> ComplexityReport:
        """分析代码复杂度

        Args:
            file_path: 文件路径

        Returns:
            复杂度报告
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            raise ValueError(f"读取文件失败: {e}") from e

        lines = content.split("\n")
        total_lines = len(lines)

        # 统计行数
        code_lines = 0
        comment_lines = 0
        blank_lines = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith("#"):
                comment_lines += 1
            else:
                code_lines += 1

        # 解析 AST
        try:
            tree = ast.parse(content)
        except SyntaxError:
            tree = ast.Module(body=[])

        # 统计函数和类
        functions = 0
        classes = 0
        complexities: list[int] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                functions += 1
                # 计算圈复杂度
                complexity = self._calculate_cyclomatic_complexity(node)
                complexities.append(complexity)
            elif isinstance(node, ast.ClassDef):
                classes += 1

        max_complexity = max(complexities) if complexities else 0
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0.0

        return ComplexityReport(
            file_path=str(path),
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            functions=functions,
            classes=classes,
            max_complexity=max_complexity,
            avg_complexity=avg_complexity,
        )

    def _calculate_cyclomatic_complexity(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> int:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度

        for child in ast.walk(node):
            # 分支语句
            if isinstance(child, ast.If | ast.For | ast.While | ast.ExceptHandler):
                complexity += 1
            # 逻辑运算符
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            # 条件表达式
            elif isinstance(child, ast.IfExp):
                complexity += 1
            # and/or 表达式
            elif isinstance(child, ast.Compare):
                complexity += len(child.ops)

        return complexity

    def generate_complexity_report(
        self,
        directory: str | Path,
        output_format: str = "text",
    ) -> str:
        """生成目录复杂度报告

        Args:
            directory: 目录路径
            output_format: 输出格式 (text/markdown/json)

        Returns:
            报告内容
        """
        dir_path = Path(directory)
        reports: list[ComplexityReport] = []

        for py_file in dir_path.glob("**/*.py"):
            try:
                report = self.analyze_complexity(py_file)
                reports.append(report)
            except Exception as e:
                logger.warning(f"分析失败 {py_file}: {e}")

        if output_format == "json":
            return self._generate_json_report(reports)
        if output_format == "markdown":
            return self._generate_markdown_report(reports)
        return self._generate_text_report(reports)

    def _generate_text_report(self, reports: list[ComplexityReport]) -> str:
        """生成文本报告"""
        lines = [
            "代码复杂度报告",
            "=" * 50,
            "",
        ]

        total_lines = 0
        total_code = 0
        total_functions = 0
        total_classes = 0
        high_complexity_files: list[tuple[str, int]] = []

        for report in reports:
            total_lines += report.total_lines
            total_code += report.code_lines
            total_functions += report.functions
            total_classes += report.classes

            if report.max_complexity > 10:
                high_complexity_files.append((report.file_path, report.max_complexity))

        lines.extend(
            [
                f"文件数量: {len(reports)}",
                f"总行数: {total_lines}",
                f"代码行数: {total_code}",
                f"函数数量: {total_functions}",
                f"类数量: {total_classes}",
                "",
                "高复杂度文件 (圈复杂度 > 10):",
                "-" * 30,
            ]
        )

        for file_path, complexity in sorted(high_complexity_files, key=lambda x: -x[1]):
            lines.append(f"  {file_path}: {complexity}")

        return "\n".join(lines)

    def _generate_markdown_report(self, reports: list[ComplexityReport]) -> str:
        """生成 Markdown 报告"""
        lines = [
            "# 代码复杂度报告",
            "",
            "## 概览",
            "",
            "| 指标 | 值 |",
            "|------|-----|",
        ]

        total_lines = sum(r.total_lines for r in reports)
        total_code = sum(r.code_lines for r in reports)
        total_functions = sum(r.functions for r in reports)
        total_classes = sum(r.classes for r in reports)

        lines.extend(
            [
                f"| 文件数量 | {len(reports)} |",
                f"| 总行数 | {total_lines} |",
                f"| 代码行数 | {total_code} |",
                f"| 函数数量 | {total_functions} |",
                f"| 类数量 | {total_classes} |",
                "",
                "## 文件详情",
                "",
                "| 文件 | 总行数 | 代码行数 | 函数 | 类 | 最大复杂度 |",
                "|------|--------|----------|------|-----|------------|",
            ]
        )

        for report in sorted(reports, key=lambda x: -x.max_complexity):
            lines.append(
                f"| {Path(report.file_path).name} | {report.total_lines} | "
                f"{report.code_lines} | {report.functions} | {report.classes} | "
                f"{report.max_complexity} |"
            )

        return "\n".join(lines)

    def _generate_json_report(self, reports: list[ComplexityReport]) -> str:
        """生成 JSON 报告"""
        import json

        data = {
            "summary": {
                "total_files": len(reports),
                "total_lines": sum(r.total_lines for r in reports),
                "total_code_lines": sum(r.code_lines for r in reports),
                "total_functions": sum(r.functions for r in reports),
                "total_classes": sum(r.classes for r in reports),
            },
            "files": [
                {
                    "path": r.file_path,
                    "total_lines": r.total_lines,
                    "code_lines": r.code_lines,
                    "comment_lines": r.comment_lines,
                    "blank_lines": r.blank_lines,
                    "functions": r.functions,
                    "classes": r.classes,
                    "max_complexity": r.max_complexity,
                    "avg_complexity": r.avg_complexity,
                }
                for r in reports
            ],
        }

        return json.dumps(data, ensure_ascii=False, indent=2)

    def format_code(
        self,
        file_path: str | Path,
        in_place: bool = False,
    ) -> str:
        """格式化代码

        Args:
            file_path: 文件路径
            in_place: 是否原地修改

        Returns:
            格式化后的代码（如果 in_place=False）
        """
        if not self._ruff_available:
            raise RuntimeError("ruff 不可用，无法格式化代码")

        path = Path(file_path)

        cmd = ["ruff", "format", str(path)]
        if not in_place:
            cmd.append("--diff")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if in_place:
            return ""
        return result.stdout


def check_code_quality(
    path: str | Path,
    use_ruff: bool = True,
) -> tuple[bool, list[LintIssue]]:
    """检查代码质量的便捷函数

    Args:
        path: 文件或目录路径
        use_ruff: 是否使用 ruff

    Returns:
        (是否通过, 问题列表)
    """
    tool = CodeQualityTool(use_ruff=use_ruff)
    path_obj = Path(path)

    if path_obj.is_file():
        issues = tool.check_file(path)
    else:
        all_issues = tool.check_directory(path)
        issues = []
        for file_issues in all_issues.values():
            issues.extend(file_issues)

    # 只有 error 级别的问题才算失败
    has_errors = any(i.severity == "error" for i in issues)
    return not has_errors, issues


def analyze_file_complexity(file_path: str | Path) -> ComplexityReport:
    """分析文件复杂度的便捷函数

    Args:
        file_path: 文件路径

    Returns:
        复杂度报告
    """
    tool = CodeQualityTool()
    return tool.analyze_complexity(file_path)