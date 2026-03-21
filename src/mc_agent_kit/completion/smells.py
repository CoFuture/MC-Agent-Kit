"""
代码异味检测器

检测 ModSDK 代码中的常见问题和改进机会。
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class SmellType(Enum):
    """代码异味类型"""

    # 命名问题
    LONG_NAME = "long_name"  # 名称过长
    SHORT_NAME = "short_name"  # 名称过短
    MISLEADING_NAME = "misleading_name"  # 误导性命名
    INCONSISTENT_NAMING = "inconsistent_naming"  # 不一致命名

    # 复杂度问题
    LONG_FUNCTION = "long_function"  # 函数过长
    LONG_CLASS = "long_class"  # 类过长
    MANY_PARAMETERS = "many_parameters"  # 参数过多
    DEEPLY_NESTED = "deeply_nested"  # 嵌套过深
    HIGH_COMPLEXITY = "high_complexity"  # 圈复杂度过高

    # 重复问题
    DUPLICATE_CODE = "duplicate_code"  # 重复代码
    DUPLICATE_STRING = "duplicate_string"  # 重复字符串

    # 结构问题
    GOD_CLASS = "god_class"  # 上帝类
    FEATURE_ENVY = "feature_envy"  # 特性嫉妒
    PRIMITIVE_OBSESSION = "primitive_obsession"  # 基本类型偏执
    DATA_CLASS = "data_class"  # 数据类
    LARGE_CLASS = "large_class"  # 过大类

    # ModSDK 特定
    HARDCODED_PATH = "hardcoded_path"  # 硬编码路径
    MAGIC_NUMBER = "magic_number"  # 魔法数字
    MISSING_ERROR_HANDLER = "missing_error_handler"  # 缺少错误处理
    UNUSED_IMPORT = "unused_import"  # 未使用的导入
    BARE_EXCEPT = "bare_except"  # 裸 except
    PRINT_DEBUG = "print_debug"  # print 调试语句

    # 代码质量问题
    COMMENTED_CODE = "commented_code"  # 注释掉的代码
    TODO_COMMENT = "todo_comment"  # TODO 注释
    MISSING_DOCSTRING = "missing_docstring"  # 缺少文档字符串
    MISSING_TYPE_HINT = "missing_type_hint"  # 缺少类型注解


class SmellSeverity(Enum):
    """异味严重程度"""

    INFO = "info"  # 信息
    MINOR = "minor"  # 轻微
    MAJOR = "major"  # 重要
    CRITICAL = "critical"  # 严重


class SmellCategory(Enum):
    """异味类别"""

    NAMING = "naming"  # 命名
    COMPLEXITY = "complexity"  # 复杂度
    DUPLICATION = "duplication"  # 重复
    STRUCTURE = "structure"  # 结构
    MODSDK = "modsdk"  # ModSDK 特定
    QUALITY = "quality"  # 代码质量


@dataclass
class CodeSmell:
    """代码异味"""

    type: SmellType  # 异味类型
    message: str  # 描述信息
    line: int  # 行号
    column: int = 0  # 列号
    end_line: int | None = None  # 结束行号
    end_column: int | None = None  # 结束列号
    severity: SmellSeverity = SmellSeverity.MINOR  # 严重程度
    category: SmellCategory = SmellCategory.QUALITY  # 类别
    code_snippet: str = ""  # 代码片段
    suggestion: str = ""  # 修复建议
    fix_available: bool = False  # 是否可自动修复

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "type": self.type.value,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "severity": self.severity.value,
            "category": self.category.value,
            "suggestion": self.suggestion,
        }


@dataclass
class SmellDetectorConfig:
    """检测器配置"""

    max_line_length: int = 100  # 最大行长度
    max_function_lines: int = 50  # 函数最大行数
    max_class_lines: int = 300  # 类最大行数
    max_parameters: int = 5  # 最大参数数量
    max_nesting_depth: int = 4  # 最大嵌套深度
    max_complexity: int = 15  # 最大圈复杂度
    min_name_length: int = 2  # 最小名称长度
    max_name_length: int = 40  # 最大名称长度
    check_docstrings: bool = True  # 检查文档字符串
    check_type_hints: bool = False  # 检查类型注解（ModSDK 可选）
    check_print_debug: bool = True  # 检查 print 调试语句


class SmellDetector:
    """代码异味检测器

    检测代码中的各种问题并提供修复建议。

    Example:
        >>> detector = SmellDetector()
        >>> smells = detector.detect("def foo():\\n    pass")
        >>> for smell in smells:
        ...     print(f"{smell.type.value}: {smell.message}")
    """

    def __init__(self, config: SmellDetectorConfig | None = None) -> None:
        """初始化检测器

        Args:
            config: 检测器配置
        """
        self._config = config or SmellDetectorConfig()

    def detect(self, code: str) -> list[CodeSmell]:
        """检测代码中的异味

        Args:
            code: 源代码

        Returns:
            检测到的代码异味列表
        """
        smells: list[CodeSmell] = []

        # 解析 AST
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return smells

        lines = code.split("\n")

        # 运行各种检测器
        smells.extend(self._detect_naming_issues(tree, lines))
        smells.extend(self._detect_complexity_issues(tree, lines))
        smells.extend(self._detect_modsdk_issues(tree, lines))
        smells.extend(self._detect_quality_issues(tree, lines))
        smells.extend(self._detect_structure_issues(tree, lines))

        return smells

    def _detect_naming_issues(self, tree: ast.AST, lines: list[str]) -> list[CodeSmell]:
        """检测命名问题"""
        smells: list[CodeSmell] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                # 检查函数名长度
                if len(node.name) < self._config.min_name_length:
                    smells.append(
                        CodeSmell(
                            type=SmellType.SHORT_NAME,
                            message=f"函数名 '{node.name}' 过短",
                            line=node.lineno,
                            severity=SmellSeverity.MINOR,
                            category=SmellCategory.NAMING,
                            suggestion="使用更具描述性的名称",
                        )
                    )
                elif len(node.name) > self._config.max_name_length:
                    smells.append(
                        CodeSmell(
                            type=SmellType.LONG_NAME,
                            message=f"函数名 '{node.name}' 过长",
                            line=node.lineno,
                            severity=SmellSeverity.MINOR,
                            category=SmellCategory.NAMING,
                            suggestion="考虑简化名称或使用更通用的命名",
                        )
                    )

            elif isinstance(node, ast.ClassDef):
                if len(node.name) < self._config.min_name_length:
                    smells.append(
                        CodeSmell(
                            type=SmellType.SHORT_NAME,
                            message=f"类名 '{node.name}' 过短",
                            line=node.lineno,
                            severity=SmellSeverity.MINOR,
                            category=SmellCategory.NAMING,
                            suggestion="使用更具描述性的名称",
                        )
                    )

            elif isinstance(node, ast.Name):
                # 检查变量名（排除内置名）
                if node.id in ("l", "O", "I"):
                    smells.append(
                        CodeSmell(
                            type=SmellType.MISLEADING_NAME,
                            message=f"变量名 '{node.id}' 容易与数字混淆",
                            line=node.lineno,
                            severity=SmellSeverity.MINOR,
                            category=SmellCategory.NAMING,
                            suggestion="使用更具描述性的变量名",
                        )
                    )

        return smells

    def _detect_complexity_issues(self, tree: ast.AST, lines: list[str]) -> list[CodeSmell]:
        """检测复杂度问题"""
        smells: list[CodeSmell] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                # 计算函数行数
                func_lines = node.end_lineno - node.lineno + 1 if node.end_lineno else 0
                if func_lines > self._config.max_function_lines:
                    smells.append(
                        CodeSmell(
                            type=SmellType.LONG_FUNCTION,
                            message=f"函数 '{node.name}' 过长 ({func_lines} 行)",
                            line=node.lineno,
                            end_line=node.end_lineno,
                            severity=SmellSeverity.MAJOR,
                            category=SmellCategory.COMPLEXITY,
                            suggestion="考虑将函数拆分为更小的函数",
                        )
                    )

                # 检查参数数量
                arg_count = len(node.args.args) + len(node.args.kwonlyargs)
                if node.args.vararg:
                    arg_count += 1
                if node.args.kwarg:
                    arg_count += 1

                if arg_count > self._config.max_parameters:
                    smells.append(
                        CodeSmell(
                            type=SmellType.MANY_PARAMETERS,
                            message=f"函数 '{node.name}' 参数过多 ({arg_count} 个)",
                            line=node.lineno,
                            severity=SmellSeverity.MAJOR,
                            category=SmellCategory.COMPLEXITY,
                            suggestion="考虑使用配置对象或拆分函数",
                        )
                    )

                # 检查嵌套深度
                max_depth = self._get_max_nesting_depth(node)
                if max_depth > self._config.max_nesting_depth:
                    smells.append(
                        CodeSmell(
                            type=SmellType.DEEPLY_NESTED,
                            message=f"函数 '{node.name}' 嵌套过深 ({max_depth} 层)",
                            line=node.lineno,
                            severity=SmellSeverity.MAJOR,
                            category=SmellCategory.COMPLEXITY,
                            suggestion="使用提前返回或提取嵌套逻辑到独立函数",
                        )
                    )

                # 计算圈复杂度
                complexity = self._calculate_complexity(node)
                if complexity > self._config.max_complexity:
                    smells.append(
                        CodeSmell(
                            type=SmellType.HIGH_COMPLEXITY,
                            message=f"函数 '{node.name}' 圈复杂度过高 ({complexity})",
                            line=node.lineno,
                            severity=SmellSeverity.MAJOR,
                            category=SmellCategory.COMPLEXITY,
                            suggestion="简化条件逻辑，提取子函数",
                        )
                    )

            elif isinstance(node, ast.ClassDef):
                # 检查类行数
                class_lines = node.end_lineno - node.lineno + 1 if node.end_lineno else 0
                if class_lines > self._config.max_class_lines:
                    smells.append(
                        CodeSmell(
                            type=SmellType.LARGE_CLASS,
                            message=f"类 '{node.name}' 过大 ({class_lines} 行)",
                            line=node.lineno,
                            severity=SmellSeverity.MAJOR,
                            category=SmellCategory.STRUCTURE,
                            suggestion="考虑将类拆分为更小的类",
                        )
                    )

        return smells

    def _detect_modsdk_issues(self, tree: ast.AST, lines: list[str]) -> list[CodeSmell]:
        """检测 ModSDK 特定问题"""
        smells: list[CodeSmell] = []

        for i, line in enumerate(lines, 1):
            # 检查硬编码路径
            if re.search(r'["\'][A-Za-z]:\\', line) or re.search(r'["\']\/\w+\/', line):
                smells.append(
                    CodeSmell(
                        type=SmellType.HARDCODED_PATH,
                        message="检测到硬编码路径",
                        line=i,
                        severity=SmellSeverity.MINOR,
                        category=SmellCategory.MODSDK,
                        suggestion="使用配置或相对路径替代硬编码路径",
                    )
                )

            # 检查魔法数字
            magic_numbers = re.findall(r"(?<!\w)(\d{3,})(?!\w)", line)
            for num in magic_numbers:
                if not line.strip().startswith("#") and not re.search(r"# noqa", line):
                    smells.append(
                        CodeSmell(
                            type=SmellType.MAGIC_NUMBER,
                            message=f"检测到魔法数字: {num}",
                            line=i,
                            severity=SmellSeverity.INFO,
                            category=SmellCategory.MODSDK,
                            suggestion="将魔法数字定义为有意义的常量",
                        )
                    )

            # 检查 print 调试语句
            if self._config.check_print_debug:
                if re.search(r"\bprint\s*\(", line) and not re.search(r"# debug", line):
                    smells.append(
                        CodeSmell(
                            type=SmellType.PRINT_DEBUG,
                            message="检测到 print 调试语句",
                            line=i,
                            severity=SmellSeverity.INFO,
                            category=SmellCategory.MODSDK,
                            suggestion="使用日志模块替代 print，或添加 # debug 注释标记",
                        )
                    )

        # 检查裸 except
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    smells.append(
                        CodeSmell(
                            type=SmellType.BARE_EXCEPT,
                            message="使用裸 except，可能隐藏错误",
                            line=node.lineno,
                            severity=SmellSeverity.MAJOR,
                            category=SmellCategory.MODSDK,
                            suggestion="指定具体的异常类型，如 Exception",
                        )
                    )

        return smells

    def _detect_quality_issues(self, tree: ast.AST, lines: list[str]) -> list[CodeSmell]:
        """检测代码质量问题"""
        smells: list[CodeSmell] = []

        for i, line in enumerate(lines, 1):
            # 检查注释掉的代码
            stripped = line.strip()
            if stripped.startswith("#") and (
                re.match(r"#\s*(def|class|if|for|while|return|import|from)\b", stripped)
                or re.match(r"#\s*[a-zA-Z_]\s*=\s*", stripped)
            ):
                smells.append(
                    CodeSmell(
                        type=SmellType.COMMENTED_CODE,
                        message="检测到注释掉的代码",
                        line=i,
                        severity=SmellSeverity.INFO,
                        category=SmellCategory.QUALITY,
                        suggestion="删除不需要的代码或添加说明注释",
                    )
                )

            # 检查 TODO 注释
            if re.search(r"#\s*TODO|FIXME|XXX|HACK", line, re.IGNORECASE):
                smells.append(
                    CodeSmell(
                        type=SmellType.TODO_COMMENT,
                        message="检测到 TODO 注释",
                        line=i,
                        severity=SmellSeverity.INFO,
                        category=SmellCategory.QUALITY,
                        suggestion="处理 TODO 或创建任务跟踪",
                    )
                )

        # 检查文档字符串
        if self._config.check_docstrings:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        smells.append(
                            CodeSmell(
                                type=SmellType.MISSING_DOCSTRING,
                                message=f"{node.__class__.__name__[:-3]} '{node.name}' 缺少文档字符串",
                                line=node.lineno,
                                severity=SmellSeverity.INFO,
                                category=SmellCategory.QUALITY,
                                suggestion="添加文档字符串描述功能",
                            )
                        )

        return smells

    def _detect_structure_issues(self, tree: ast.AST, lines: list[str]) -> list[CodeSmell]:
        """检测结构问题"""
        smells: list[CodeSmell] = []

        # 检查数据类（只有属性没有方法的类）
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                assignments = [n for n in node.body if isinstance(n, ast.Assign)]

                # 如果只有 __init__ 且只是赋值
                if len(methods) == 1 and methods[0].name == "__init__":
                    # 检查是否只是简单赋值
                    init_body = methods[0].body
                    if all(isinstance(stmt, ast.Assign | ast.Pass) for stmt in init_body):
                        smells.append(
                            CodeSmell(
                                type=SmellType.DATA_CLASS,
                                message=f"类 '{node.name}' 可能是数据类",
                                line=node.lineno,
                                severity=SmellSeverity.INFO,
                                category=SmellCategory.STRUCTURE,
                                suggestion="考虑使用 @dataclass 装饰器或添加行为方法",
                            )
                        )

        return smells

    def _get_max_nesting_depth(self, node: ast.AST) -> int:
        """计算最大嵌套深度"""
        max_depth = 0

        def visit(node: ast.AST, current_depth: int) -> None:
            nonlocal max_depth
            if isinstance(node, ast.If | ast.For | ast.While | ast.With | ast.Try):
                current_depth += 1
                max_depth = max(max_depth, current_depth)

            for child in ast.iter_child_nodes(node):
                visit(child, current_depth)

        visit(node, 0)
        return max_depth

    def _calculate_complexity(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度

        for child in ast.walk(node):
            if isinstance(child, ast.If | ast.While | ast.For | ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # and/or 操作符增加复杂度
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                if child.ifs:
                    complexity += len(child.ifs)

        return complexity

    def get_severity_counts(self, smells: list[CodeSmell]) -> dict[SmellSeverity, int]:
        """获取各严重程度的数量"""
        counts: dict[SmellSeverity, int] = {}
        for smell in smells:
            counts[smell.severity] = counts.get(smell.severity, 0) + 1
        return counts

    def get_category_counts(self, smells: list[CodeSmell]) -> dict[SmellCategory, int]:
        """获取各类别的数量"""
        counts: dict[SmellCategory, int] = {}
        for smell in smells:
            counts[smell.category] = counts.get(smell.category, 0) + 1
        return counts