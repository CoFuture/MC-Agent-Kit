"""
代码生成质量检查器

检查生成的代码质量，包括语法检查、风格检查和最佳实践检查。
"""

from __future__ import annotations
import ast
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class QualityIssueSeverity(Enum):
    """问题严重程度"""

    ERROR = "error"  # 必须修复
    WARNING = "warning"  # 建议修复
    INFO = "info"  # 信息提示


class QualityIssueCategory(Enum):
    """问题类别"""

    SYNTAX = "syntax"  # 语法错误
    STYLE = "style"  # 代码风格
    BEST_PRACTICE = "best_practice"  # 最佳实践
    SECURITY = "security"  # 安全问题
    PERFORMANCE = "performance"  # 性能问题
    COMPATIBILITY = "compatibility"  # 兼容性问题


@dataclass
class QualityIssue:
    """质量问题"""

    line: int
    column: int
    message: str
    severity: QualityIssueSeverity
    category: QualityIssueCategory
    rule_id: str
    suggestion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "line": self.line,
            "column": self.column,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "rule_id": self.rule_id,
            "suggestion": self.suggestion,
        }


@dataclass
class QualityReport:
    """质量检查报告"""

    code: str
    issues: list[QualityIssue] = field(default_factory=list)
    score: float = 100.0
    passed: bool = True

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == QualityIssueSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == QualityIssueSeverity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == QualityIssueSeverity.INFO)

    def calculate_score(self) -> float:
        """计算质量分数 (0-100)"""
        score = 100.0
        for issue in self.issues:
            if issue.severity == QualityIssueSeverity.ERROR:
                score -= 15
            elif issue.severity == QualityIssueSeverity.WARNING:
                score -= 5
            elif issue.severity == QualityIssueSeverity.INFO:
                score -= 1
        return max(0.0, min(100.0, score))

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code[:500] + "..." if len(self.code) > 500 else self.code,
            "issues": [i.to_dict() for i in self.issues],
            "score": self.calculate_score(),
            "passed": self.error_count == 0,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
        }


@dataclass
class QualityCheckConfig:
    """质量检查配置"""

    check_syntax: bool = True
    check_style: bool = True
    check_best_practices: bool = True
    check_security: bool = True
    check_performance: bool = True
    check_compatibility: bool = True
    max_line_length: int = 100
    max_function_length: int = 100
    max_complexity: int = 10
    min_score_to_pass: float = 60.0


class CodeQualityChecker:
    """代码质量检查器

    检查生成的代码质量。

    使用示例:
        checker = CodeQualityChecker()
        report = checker.check(generated_code)
        if report.passed:
            print(f"代码质量通过，分数: {report.score}")
        else:
            print(f"发现问题: {report.error_count} 个错误")
    """

    # Python 2.7 兼容性警告模式
    PYTHON2_INCOMPATIBLE_PATTERNS = [
        (r"\bfstring\b", "f-string 在 Python 2.7 中不支持"),
        (r"\basync\s+def\b", "async/await 在 Python 2.7 中不支持"),
        (r"\bawait\b", "async/await 在 Python 2.7 中不支持"),
        (r":\s*str\b", "类型注解在 Python 2.7 中不支持"),
        (r":\s*int\b", "类型注解在 Python 2.7 中不支持"),
        (r":\s*bool\b", "类型注解在 Python 2.7 中不支持"),
        (r"->\s*\w+", "返回类型注解在 Python 2.7 中不支持"),
        (r"\bprint\s*\([^)]*\)", "print 函数形式在 ModSDK 中可能有问题"),
    ]

    # 安全问题模式
    SECURITY_PATTERNS = [
        (r"\beval\s*\(", "使用 eval 可能存在安全风险"),
        (r"\bexec\s*\(", "使用 exec 可能存在安全风险"),
        (r"\b__import__\s*\(", "动态导入可能存在安全风险"),
        (r"\bcompile\s*\(", "动态编译可能存在安全风险"),
    ]

    # 性能问题模式
    PERFORMANCE_PATTERNS = [
        (r"for\s+\w+\s+in\s+range\s*\(\s*len\s*\(", "建议使用 enumerate() 替代 range(len())"),
        (r"\.append\s*\([^)]*\)\s*$", "在循环中使用 append 可能效率较低"),
        (r"print\s*\(", "生产代码中应避免 print 语句"),
    ]

    # ModSDK 最佳实践
    MODSDK_BEST_PRACTICES = [
        (r"ListenForEvent\s*\([^,]+,\s*[^,]+,\s*\w+\)", "事件监听应使用函数而非 lambda"),
        (r"GetEngineCompFactory\s*\(\s*\)", "GetEngineCompFactory() 应缓存结果"),
        (r"CreateEngineEntityByType\s*\(", "创建实体后应检查返回值"),
    ]

    def __init__(self, config: QualityCheckConfig | None = None):
        """初始化检查器

        Args:
            config: 检查配置
        """
        self.config = config or QualityCheckConfig()

    def check(self, code: str) -> QualityReport:
        """检查代码质量

        Args:
            code: 要检查的代码

        Returns:
            质量检查报告
        """
        report = QualityReport(code=code)

        # 语法检查
        if self.config.check_syntax:
            self._check_syntax(code, report)

        # 如果语法错误，直接返回
        if report.error_count > 0:
            report.passed = False
            return report

        # 风格检查
        if self.config.check_style:
            self._check_style(code, report)

        # 最佳实践检查
        if self.config.check_best_practices:
            self._check_best_practices(code, report)

        # 安全检查
        if self.config.check_security:
            self._check_security(code, report)

        # 性能检查
        if self.config.check_performance:
            self._check_performance(code, report)

        # 兼容性检查 (ModSDK 使用 Python 2.7)
        if self.config.check_compatibility:
            self._check_compatibility(code, report)

        # 计算分数并判断是否通过
        report.score = report.calculate_score()
        report.passed = (
            report.error_count == 0 and report.score >= self.config.min_score_to_pass
        )

        return report

    def _check_syntax(self, code: str, report: QualityReport) -> None:
        """检查语法错误"""
        try:
            ast.parse(code)
        except SyntaxError as e:
            report.issues.append(
                QualityIssue(
                    line=e.lineno or 1,
                    column=e.offset or 0,
                    message=f"语法错误: {e.msg}",
                    severity=QualityIssueSeverity.ERROR,
                    category=QualityIssueCategory.SYNTAX,
                    rule_id="SYNTAX001",
                    suggestion="修复语法错误",
                )
            )

    def _check_style(self, code: str, report: QualityReport) -> None:
        """检查代码风格"""
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            # 检查行长度
            if len(line) > self.config.max_line_length:
                report.issues.append(
                    QualityIssue(
                        line=i,
                        column=self.config.max_line_length,
                        message=f"行长度超过 {self.config.max_line_length} 字符",
                        severity=QualityIssueSeverity.WARNING,
                        category=QualityIssueCategory.STYLE,
                        rule_id="STYLE001",
                        suggestion="拆分长行",
                    )
                )

            # 检查尾随空格
            if line.rstrip() != line and line.strip():
                report.issues.append(
                    QualityIssue(
                        line=i,
                        column=len(line.rstrip()),
                        message="行尾有多余空格",
                        severity=QualityIssueSeverity.INFO,
                        category=QualityIssueCategory.STYLE,
                        rule_id="STYLE002",
                        suggestion="删除行尾空格",
                    )
                )

        # 检查函数长度
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno + 1
                    if func_lines > self.config.max_function_length:
                        report.issues.append(
                            QualityIssue(
                                line=node.lineno,
                                column=0,
                                message=f"函数 '{node.name}' 过长 ({func_lines} 行)",
                                severity=QualityIssueSeverity.WARNING,
                                category=QualityIssueCategory.STYLE,
                                rule_id="STYLE003",
                                suggestion="考虑拆分函数",
                            )
                        )
        except Exception:
            pass

    def _check_best_practices(self, code: str, report: QualityReport) -> None:
        """检查最佳实践"""
        lines = code.split("\n")

        # ModSDK 最佳实践
        for pattern, message in self.MODSDK_BEST_PRACTICES:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    report.issues.append(
                        QualityIssue(
                            line=i,
                            column=0,
                            message=message,
                            severity=QualityIssueSeverity.INFO,
                            category=QualityIssueCategory.BEST_PRACTICE,
                            rule_id="BP001",
                            suggestion="参考 ModSDK 最佳实践文档",
                        )
                    )

        # 检查 TODO 注释
        for i, line in enumerate(lines, 1):
            if "TODO" in line.upper():
                report.issues.append(
                    QualityIssue(
                        line=i,
                        column=0,
                        message="存在未完成的 TODO",
                        severity=QualityIssueSeverity.INFO,
                        category=QualityIssueCategory.BEST_PRACTICE,
                        rule_id="BP002",
                        suggestion="完成或删除 TODO 注释",
                    )
                )

    def _check_security(self, code: str, report: QualityReport) -> None:
        """检查安全问题"""
        lines = code.split("\n")

        for pattern, message in self.SECURITY_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    report.issues.append(
                        QualityIssue(
                            line=i,
                            column=0,
                            message=message,
                            severity=QualityIssueSeverity.WARNING,
                            category=QualityIssueCategory.SECURITY,
                            rule_id="SEC001",
                            suggestion="避免使用潜在不安全的函数",
                        )
                    )

    def _check_performance(self, code: str, report: QualityReport) -> None:
        """检查性能问题"""
        lines = code.split("\n")

        for pattern, message in self.PERFORMANCE_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    report.issues.append(
                        QualityIssue(
                            line=i,
                            column=0,
                            message=message,
                            severity=QualityIssueSeverity.INFO,
                            category=QualityIssueCategory.PERFORMANCE,
                            rule_id="PERF001",
                            suggestion="优化代码以提高性能",
                        )
                    )

    def _check_compatibility(self, code: str, report: QualityReport) -> None:
        """检查 ModSDK 兼容性 (Python 2.7)"""
        lines = code.split("\n")

        for pattern, message in self.PYTHON2_INCOMPATIBLE_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    report.issues.append(
                        QualityIssue(
                            line=i,
                            column=0,
                            message=message,
                            severity=QualityIssueSeverity.WARNING,
                            category=QualityIssueCategory.COMPATIBILITY,
                            rule_id="COMPAT001",
                            suggestion="使用 Python 2.7 兼容的语法",
                        )
                    )

    def quick_check(self, code: str) -> tuple[bool, list[str]]:
        """快速检查代码是否有明显问题

        Args:
            code: 要检查的代码

        Returns:
            (是否通过, 错误消息列表)
        """
        errors = []

        # 语法检查
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"语法错误 (行 {e.lineno}): {e.msg}")
            return False, errors

        # 快速兼容性检查
        for pattern, message in self.PYTHON2_INCOMPATIBLE_PATTERNS[:3]:
            if re.search(pattern, code):
                errors.append(message)

        return len(errors) == 0, errors


def check_code_quality(code: str, config: QualityCheckConfig | None = None) -> QualityReport:
    """检查代码质量的便捷函数

    Args:
        code: 要检查的代码
        config: 检查配置

    Returns:
        质量检查报告
    """
    checker = CodeQualityChecker(config)
    return checker.check(code)


def validate_generated_code(code: str) -> tuple[bool, str]:
    """验证生成的代码

    Args:
        code: 生成的代码

    Returns:
        (是否有效, 错误消息或成功消息)
    """
    # 基本检查
    if not code or not code.strip():
        return False, "生成的代码为空"

    # 语法检查
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f"语法错误 (行 {e.lineno}): {e.msg}"

    # 质量检查
    checker = CodeQualityChecker()
    report = checker.check(code)

    if report.error_count > 0:
        errors = [i.message for i in report.issues if i.severity == QualityIssueSeverity.ERROR]
        return False, f"发现 {report.error_count} 个错误: {'; '.join(errors[:3])}"

    if report.warning_count > 0:
        return True, f"代码有效，但有 {report.warning_count} 个警告 (分数: {report.score:.1f})"

    return True, f"代码质量良好 (分数: {report.score:.1f})"
