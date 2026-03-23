"""
智能代码分析器模块

提供 ModSDK API 使用分析、性能瓶颈识别、潜在错误检测、最佳实践建议等功能。

迭代 #57: Agent 技能增强与 ModSDK 深度集成
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class IssueSeverity(Enum):
    """问题严重程度"""

    ERROR = "error"  # 错误
    WARNING = "warning"  # 警告
    INFO = "info"  # 信息
    HINT = "hint"  # 提示


class IssueType(Enum):
    """问题类型"""

    SYNTAX = "syntax"  # 语法问题
    API_USAGE = "api_usage"  # API 使用问题
    PERFORMANCE = "performance"  # 性能问题
    SECURITY = "security"  # 安全问题
    STYLE = "style"  # 代码风格
    BEST_PRACTICE = "best_practice"  # 最佳实践
    COMPATIBILITY = "compatibility"  # 兼容性问题


@dataclass
class Issue:
    """代码问题"""

    type: IssueType
    severity: IssueSeverity
    message: str
    file: str
    line: int
    column: int = 0
    end_line: int = 0
    end_column: int = 0
    code_snippet: str = ""
    fix_suggestion: Optional[str] = None
    fix_code: Optional[str] = None
    related_docs: list[str] = field(default_factory=list)


@dataclass
class APIUsage:
    """API 使用信息"""

    name: str
    module: str
    file: str
    line: int
    context: str
    parameters: list[Any] = field(default_factory=list)
    is_correct: bool = True
    issues: list[str] = field(default_factory=list)


@dataclass
class Suggestion:
    """改进建议"""

    title: str
    description: str
    file: str
    line: int
    code_before: str
    code_after: str
    impact: str  # 改进影响描述
    priority: int = 0  # 优先级，数字越大越重要


@dataclass
class AnalysisResult:
    """分析结果"""

    file: str
    issues: list[Issue]
    api_usages: list[APIUsage]
    suggestions: list[Suggestion]
    statistics: dict[str, Any]
    score: float = 0.0  # 代码质量分数 (0-100)


@dataclass
class PerformanceIssue:
    """性能问题"""

    type: str
    description: str
    location: str
    line: int
    impact: str  # high/medium/low
    suggestion: str


class CodeAnalyzer:
    """
    代码分析器

    分析 ModSDK 代码，检测问题并提供改进建议。
    """

    # ModSDK API 列表
    MODSDK_APIS = {
        # 实体相关
        "CreateEngineEntity": {"module": "实体", "params": 2, "return": "int"},
        "DestroyEntity": {"module": "实体", "params": 1, "return": "bool"},
        "GetEngineEntity": {"module": "实体", "params": 1, "return": "EngineEntity"},
        "SetEntityPos": {"module": "实体", "params": 4, "return": "bool"},
        "GetEntityPos": {"module": "实体", "params": 1, "return": "tuple"},
        "SetEntityMotion": {"module": "实体", "params": 4, "return": "bool"},
        "GetEntityMotion": {"module": "实体", "params": 1, "return": "tuple"},
        "SetEntityHealth": {"module": "实体", "params": 2, "return": "bool"},
        "GetEntityHealth": {"module": "实体", "params": 1, "return": "int"},
        # 玩家相关
        "GetPlayerName": {"module": "玩家", "params": 1, "return": "str"},
        "GetPlayerUID": {"module": "玩家", "params": 1, "return": "str"},
        "GetPlayerPos": {"module": "玩家", "params": 1, "return": "tuple"},
        "SetPlayerPos": {"module": "玩家", "params": 4, "return": "bool"},
        # 方块相关
        "SetBlock": {"module": "方块", "params": 4, "return": "bool"},
        "GetBlock": {"module": "方块", "params": 3, "return": "dict"},
        "DestroyBlock": {"module": "方块", "params": 3, "return": "bool"},
        # 物品相关
        "CreateEngineItemEntity": {"module": "物品", "params": 2, "return": "int"},
        "GetContainer": {"module": "物品", "params": 2, "return": "Container"},
        "GetContainerItem": {"module": "物品", "params": 2, "return": "dict"},
        "SetInvItemNum": {"module": "物品", "params": 3, "return": "bool"},
        # 聊天/消息相关
        "BroadcastToClient": {"module": "聊天", "params": 1, "return": "bool"},
        "NotifyToClient": {"module": "聊天", "params": 2, "return": "bool"},
        "SetTipMessage": {"module": "聊天", "params": 1, "return": "bool"},
        # UI 相关
        "CreateUI": {"module": "UI", "params": 3, "return": "int"},
        "DestroyUI": {"module": "UI", "params": 1, "return": "bool"},
        "GetUI": {"module": "UI", "params": 1, "return": "UI"},
    }

    # 常见错误模式
    ERROR_PATTERNS = [
        (
            r"except\s*:",
            IssueType.BEST_PRACTICE,
            IssueSeverity.WARNING,
            "捕获所有异常可能隐藏错误",
        ),
        (
            r"except\s+Exception\s*:",
            IssueType.BEST_PRACTICE,
            IssueSeverity.WARNING,
            "捕获 Exception 过于宽泛，建议捕获更具体的异常",
        ),
        (
            r"print\s*\(",
            IssueType.STYLE,
            IssueSeverity.INFO,
            "生产代码建议使用 logging 替代 print",
        ),
        (
            r"global\s+\w+",
            IssueType.BEST_PRACTICE,
            IssueSeverity.WARNING,
            "使用全局变量可能导致代码难以维护",
        ),
        (
            r"==\s*None",
            IssueType.STYLE,
            IssueSeverity.HINT,
            "建议使用 'is None' 而不是 '== None'",
        ),
        (
            r"!=\s*None",
            IssueType.STYLE,
            IssueSeverity.HINT,
            "建议使用 'is not None' 而不是 '!= None'",
        ),
    ]

    # 性能问题模式
    PERFORMANCE_PATTERNS = [
        (
            r"for\s+\w+\s+in\s+range\(len\((\w+)\)\)",
            "使用 range(len(...)) 效率较低",
            "建议使用 enumerate() 或直接遍历",
        ),
        (
            r"\+\s*=\s*\[",
            "循环中使用 += [] 效率较低",
            "建议使用 append() 或列表推导式",
        ),
        (
            r"\.format\s*\(",
            "str.format() 效率略低于 f-string",
            "建议使用 f-string (Python 3.6+)",
        ),
    ]

    def __init__(self, strict_mode: bool = False):
        """
        初始化代码分析器

        Args:
            strict_mode: 严格模式，启用更多检查
        """
        self.strict_mode = strict_mode
        self._ast_analyzer = ASTAnalyzer(self)

    def analyze(self, code: str, file: str = "<code>") -> AnalysisResult:
        """
        分析代码

        Args:
            code: 代码字符串
            file: 文件名

        Returns:
            分析结果
        """
        issues: list[Issue] = []
        api_usages: list[APIUsage] = []
        suggestions: list[Suggestion] = []

        # 语法分析
        syntax_issues = self._check_syntax(code, file)
        issues.extend(syntax_issues)

        if syntax_issues:
            # 有语法错误，跳过后续分析
            return AnalysisResult(
                file=file,
                issues=issues,
                api_usages=api_usages,
                suggestions=suggestions,
                statistics={"lines": 0, "syntax_errors": len(syntax_issues)},
                score=0.0,
            )

        # 模式匹配分析
        pattern_issues = self._check_patterns(code, file)
        issues.extend(pattern_issues)

        # API 使用分析
        api_usages = self._analyze_api_usage(code, file)

        # 性能分析
        perf_issues = self._check_performance(code, file)
        issues.extend(perf_issues)

        # 生成建议
        suggestions = self._generate_suggestions(code, file, issues)

        # 统计信息
        lines = code.count("\n") + 1
        statistics = {
            "lines": lines,
            "issues": len(issues),
            "errors": len([i for i in issues if i.severity == IssueSeverity.ERROR]),
            "warnings": len([i for i in issues if i.severity == IssueSeverity.WARNING]),
            "api_calls": len(api_usages),
        }

        # 计算质量分数
        score = self._calculate_score(issues, lines)

        return AnalysisResult(
            file=file,
            issues=issues,
            api_usages=api_usages,
            suggestions=suggestions,
            statistics=statistics,
            score=score,
        )

    def find_api_usage(self, code: str, file: str = "<code>") -> list[APIUsage]:
        """
        查找 API 使用

        Args:
            code: 代码字符串
            file: 文件名

        Returns:
            API 使用列表
        """
        return self._analyze_api_usage(code, file)

    def detect_issues(self, code: str, file: str = "<code>") -> list[Issue]:
        """
        检测问题

        Args:
            code: 代码字符串
            file: 文件名

        Returns:
            问题列表
        """
        issues: list[Issue] = []

        # 语法检查
        issues.extend(self._check_syntax(code, file))

        # 模式检查
        issues.extend(self._check_patterns(code, file))

        # 性能检查
        issues.extend(self._check_performance(code, file))

        return issues

    def suggest_improvements(self, code: str, file: str = "<code>") -> list[Suggestion]:
        """
        生成改进建议

        Args:
            code: 代码字符串
            file: 文件名

        Returns:
            改进建议列表
        """
        issues = self.detect_issues(code, file)
        return self._generate_suggestions(code, file, issues)

    # ==================== 私有方法 ====================

    def _check_syntax(self, code: str, file: str) -> list[Issue]:
        """检查语法"""
        issues: list[Issue] = []

        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(
                Issue(
                    type=IssueType.SYNTAX,
                    severity=IssueSeverity.ERROR,
                    message=f"语法错误: {e.msg}",
                    file=file,
                    line=e.lineno or 1,
                    column=e.offset or 0,
                )
            )

        return issues

    def _check_patterns(self, code: str, file: str) -> list[Issue]:
        """检查代码模式"""
        issues: list[Issue] = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            for pattern, issue_type, severity, message in self.ERROR_PATTERNS:
                if re.search(pattern, line):
                    issues.append(
                        Issue(
                            type=issue_type,
                            severity=severity,
                            message=message,
                            file=file,
                            line=i,
                            column=0,
                            code_snippet=line.strip(),
                        )
                    )

        return issues

    def _analyze_api_usage(self, code: str, file: str) -> list[APIUsage]:
        """分析 API 使用"""
        usages: list[APIUsage] = []

        # 查找 API 调用
        for api_name, api_info in self.MODSDK_APIS.items():
            pattern = rf"\b{api_name}\s*\("
            for match in re.finditer(pattern, code):
                # 获取行号
                line = code[: match.start()].count("\n") + 1
                # 获取上下文
                lines = code.split("\n")
                context = lines[line - 1] if line <= len(lines) else ""

                usages.append(
                    APIUsage(
                        name=api_name,
                        module=api_info["module"],
                        file=file,
                        line=line,
                        context=context.strip(),
                        is_correct=True,
                    )
                )

        return usages

    def _check_performance(self, code: str, file: str) -> list[Issue]:
        """检查性能问题"""
        issues: list[Issue] = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            for pattern, message, suggestion in self.PERFORMANCE_PATTERNS:
                if re.search(pattern, line):
                    issues.append(
                        Issue(
                            type=IssueType.PERFORMANCE,
                            severity=IssueSeverity.WARNING,
                            message=message,
                            file=file,
                            line=i,
                            column=0,
                            code_snippet=line.strip(),
                            fix_suggestion=suggestion,
                        )
                    )

        return issues

    def _generate_suggestions(
        self, code: str, file: str, issues: list[Issue]
    ) -> list[Suggestion]:
        """生成改进建议"""
        suggestions: list[Suggestion] = []

        for issue in issues:
            if issue.fix_suggestion and issue.line > 0:
                lines = code.split("\n")
                if issue.line <= len(lines):
                    code_before = lines[issue.line - 1].strip()

                    # 生成修复后的代码（简化）
                    code_after = self._generate_fix(issue, code_before)

                    suggestions.append(
                        Suggestion(
                            title=f"修复 {issue.type.value}",
                            description=issue.message,
                            file=file,
                            line=issue.line,
                            code_before=code_before,
                            code_after=code_after,
                            impact=f"解决 {issue.severity.value} 级别问题",
                            priority=5
                            if issue.severity == IssueSeverity.ERROR
                            else 3,
                        )
                    )

        return suggestions

    def _generate_fix(self, issue: Issue, code_before: str) -> str:
        """生成修复代码"""
        # 简化的修复生成
        if "is None" in issue.fix_suggestion or "is not None" in issue.fix_suggestion:
            return code_before.replace("== None", "is None").replace(
                "!= None", "is not None"
            )
        return f"# TODO: {issue.fix_suggestion}\n# {code_before}"

    def _calculate_score(self, issues: list[Issue], lines: int) -> float:
        """计算代码质量分数"""
        if lines == 0:
            return 100.0

        # 基础分数
        score = 100.0

        # 根据问题扣分
        for issue in issues:
            if issue.severity == IssueSeverity.ERROR:
                score -= 10
            elif issue.severity == IssueSeverity.WARNING:
                score -= 5
            elif issue.severity == IssueSeverity.INFO:
                score -= 1

        # 确保分数在 0-100 之间
        return max(0.0, min(100.0, score))


class ASTAnalyzer(ast.NodeVisitor):
    """AST 分析器"""

    def __init__(self, analyzer: CodeAnalyzer):
        self.analyzer = analyzer
        self.issues: list[Issue] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """访问函数定义"""
        # 检查函数复杂度
        complexity = self._calculate_complexity(node)
        if complexity > 10:
            self.issues.append(
                Issue(
                    type=IssueType.BEST_PRACTICE,
                    severity=IssueSeverity.WARNING,
                    message=f"函数 '{node.name}' 复杂度过高 ({complexity})",
                    file="",
                    line=node.lineno,
                )
            )

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """访问函数调用"""
        # 检查 API 调用
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in CodeAnalyzer.MODSDK_APIS:
                api_info = CodeAnalyzer.MODSDK_APIS[func_name]
                expected_params = api_info["params"]
                actual_params = len(node.args)

                if actual_params < expected_params:
                    self.issues.append(
                        Issue(
                            type=IssueType.API_USAGE,
                            severity=IssueSeverity.ERROR,
                            message=f"{func_name} 缺少参数，预期 {expected_params} 个",
                            file="",
                            line=node.lineno,
                        )
                    )

        self.generic_visit(node)

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """计算函数复杂度"""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity


def create_code_analyzer(strict_mode: bool = False) -> CodeAnalyzer:
    """创建代码分析器实例"""
    return CodeAnalyzer(strict_mode=strict_mode)