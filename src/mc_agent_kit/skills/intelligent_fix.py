"""
智能错误修复模块

提供错误模式学习、自动修复建议生成、修复效果预测和修复验证机制。
"""

from __future__ import annotations

import ast
import difflib
import hashlib
import re
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class ErrorCategory(Enum):
    """错误类别"""
    SYNTAX = "syntax"
    NAME = "name"
    TYPE = "type"
    KEY = "key"
    INDEX = "index"
    ATTRIBUTE = "attribute"
    VALUE = "value"
    RUNTIME = "runtime"
    IMPORT = "import"
    INDENTATION = "indentation"
    MODSDK = "modsdk"


class FixConfidence(Enum):
    """修复置信度"""
    HIGH = "high"  # > 0.8
    MEDIUM = "medium"  # 0.5 - 0.8
    LOW = "low"  # < 0.5


class FixStatus(Enum):
    """修复状态"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    MANUAL_REQUIRED = "manual_required"


@dataclass
class ErrorPattern:
    """错误模式"""
    pattern: str  # 正则表达式
    category: ErrorCategory
    message_template: str
    fix_template: str | None
    confidence: float
    examples: list[str] = field(default_factory=list)
    learn_count: int = 0


@dataclass
class FixSuggestion:
    """修复建议"""
    description: str
    code_fix: str
    confidence: FixConfidence
    auto_applicable: bool
    explanation: str
    line_start: int
    line_end: int
    priority: int = 0  # 越小优先级越高


@dataclass
class FixResult:
    """修复结果"""
    status: FixStatus
    original_code: str
    fixed_code: str
    changes: list[dict[str, Any]]
    suggestions_applied: list[str]
    warnings: list[str]
    test_passed: bool | None = None


@dataclass
class ErrorAnalysis:
    """错误分析结果"""
    error_type: str
    category: ErrorCategory
    message: str
    line: int
    column: int | None
    traceback: str
    context: dict[str, Any]
    suggestions: list[FixSuggestion]


class ErrorPatternLearner:
    """错误模式学习器

    从历史错误数据中学习错误模式。

    使用示例:
        learner = ErrorPatternLearner()
        learner.learn("NameError: name 'x' is not defined", fixed_code)
        patterns = learner.get_patterns()
    """

    def __init__(self) -> None:
        """初始化学习器"""
        self._patterns: dict[str, ErrorPattern] = {}
        self._error_history: list[dict[str, Any]] = []
        self._lock = threading.Lock()

        # 初始化内置模式
        self._init_builtin_patterns()

    def _init_builtin_patterns(self) -> None:
        """初始化内置错误模式"""
        patterns = [
            ErrorPattern(
                pattern=r"NameError:\s*name\s+'(\w+)'\s+is\s+not\s+defined",
                category=ErrorCategory.NAME,
                message_template="变量 '{var}' 未定义",
                fix_template="确保变量 '{var}' 在使用前已定义",
                confidence=0.9,
                examples=["NameError: name 'x' is not defined"],
            ),
            ErrorPattern(
                pattern=r"KeyError:\s*['\"](\w+)['\"]",
                category=ErrorCategory.KEY,
                message_template="字典中不存在键 '{var}'",
                fix_template="使用 dict.get('{var}', default) 或检查键是否存在",
                confidence=0.85,
                examples=["KeyError: 'speed'"],
            ),
            ErrorPattern(
                pattern=r"AttributeError:\s*'(\w+)'\s+object\s+has\s+no\s+attribute\s+'(\w+)'",
                category=ErrorCategory.ATTRIBUTE,
                message_template="对象 '{obj}' 没有属性 '{attr}'",
                fix_template="检查对象类型或使用 hasattr() 检查属性",
                confidence=0.8,
                examples=["AttributeError: 'dict' object has no attribute 'append'"],
            ),
            ErrorPattern(
                pattern=r"IndexError:\s*list\s+index\s+out\s+of\s+range",
                category=ErrorCategory.INDEX,
                message_template="列表索引超出范围",
                fix_template="检查列表长度后再访问，使用 len(list) > index",
                confidence=0.85,
                examples=["IndexError: list index out of range"],
            ),
            ErrorPattern(
                pattern=r"TypeError:\s*'(\w+)'\s+object\s+is\s+not\s+(\w+)",
                category=ErrorCategory.TYPE,
                message_template="'{obj}' 对象不能 {action}",
                fix_template="检查对象类型，进行类型转换",
                confidence=0.75,
                examples=["TypeError: 'str' object is not callable"],
            ),
            ErrorPattern(
                pattern=r"ValueError:\s*(.+)",
                category=ErrorCategory.VALUE,
                message_template="值错误: {detail}",
                fix_template="检查输入值的有效性",
                confidence=0.7,
                examples=["ValueError: invalid literal for int()"],
            ),
            ErrorPattern(
                pattern=r"IndentationError:\s*(.+)",
                category=ErrorCategory.INDENTATION,
                message_template="缩进错误: {detail}",
                fix_template="检查代码缩进，使用 4 空格缩进",
                confidence=0.9,
                examples=["IndentationError: expected an indented block"],
            ),
            ErrorPattern(
                pattern=r"SyntaxError:\s*(.+)",
                category=ErrorCategory.SYNTAX,
                message_template="语法错误: {detail}",
                fix_template="检查语法，确保括号、引号匹配",
                confidence=0.85,
                examples=["SyntaxError: invalid syntax"],
            ),
            ErrorPattern(
                pattern=r"ImportError:\s*(.+)",
                category=ErrorCategory.IMPORT,
                message_template="导入错误: {detail}",
                fix_template="检查模块名称或安装缺失的依赖",
                confidence=0.8,
                examples=["ImportError: No module named 'xxx'"],
            ),
            ErrorPattern(
                pattern=r"ListenEvent.*'(\w+)'.*not\s+found",
                category=ErrorCategory.MODSDK,
                message_template="ModSDK 事件 '{event}' 未找到",
                fix_template="检查事件名称拼写，确保使用正确的事件名",
                confidence=0.85,
                examples=["ListenEvent: 'OnServerStartt' not found"],
            ),
        ]

        for pattern in patterns:
            key = hashlib.md5(pattern.pattern.encode()).hexdigest()[:8]
            self._patterns[key] = pattern

    def learn(
        self,
        error_message: str,
        error_code: str,
        fixed_code: str | None = None,
    ) -> ErrorPattern | None:
        """从错误中学习

        Args:
            error_message: 错误信息
            error_code: 错误代码
            fixed_code: 修复后的代码（可选）

        Returns:
            ErrorPattern | None: 学习到的模式
        """
        with self._lock:
            # 记录历史
            self._error_history.append({
                "error": error_message,
                "code": error_code,
                "fixed": fixed_code,
                "timestamp": time.time(),
            })

            # 尝试匹配现有模式
            for key, pattern in self._patterns.items():
                match = re.search(pattern.pattern, error_message, re.IGNORECASE)
                if match:
                    pattern.learn_count += 1
                    if error_message not in pattern.examples:
                        pattern.examples.append(error_message)
                    return pattern

            # 创建新模式
            new_pattern = self._create_pattern(error_message, error_code, fixed_code)
            if new_pattern:
                key = hashlib.md5(new_pattern.pattern.encode()).hexdigest()[:8]
                self._patterns[key] = new_pattern
                return new_pattern

            return None

    def _create_pattern(
        self,
        error_message: str,
        error_code: str,
        fixed_code: str | None,
    ) -> ErrorPattern | None:
        """创建新的错误模式"""
        # 提取错误类型
        error_type_match = re.match(r'(\w+Error):', error_message)
        if not error_type_match:
            return None

        error_type = error_type_match.group(1)

        # 创建通用模式
        pattern_str = re.escape(error_type) + r":\s*(.+)"

        return ErrorPattern(
            pattern=pattern_str,
            category=self._categorize_error(error_type),
            message_template=f"{error_type}: {{detail}}",
            fix_template="检查错误详情并进行修复",
            confidence=0.5,
            examples=[error_message],
            learn_count=1,
        )

    def _categorize_error(self, error_type: str) -> ErrorCategory:
        """分类错误"""
        category_map = {
            "NameError": ErrorCategory.NAME,
            "KeyError": ErrorCategory.KEY,
            "AttributeError": ErrorCategory.ATTRIBUTE,
            "IndexError": ErrorCategory.INDEX,
            "TypeError": ErrorCategory.TYPE,
            "ValueError": ErrorCategory.VALUE,
            "SyntaxError": ErrorCategory.SYNTAX,
            "IndentationError": ErrorCategory.INDENTATION,
            "ImportError": ErrorCategory.IMPORT,
        }
        return category_map.get(error_type, ErrorCategory.RUNTIME)

    def get_patterns(self) -> list[ErrorPattern]:
        """获取所有模式"""
        with self._lock:
            return list(self._patterns.values())

    def get_pattern_for_error(self, error_message: str) -> ErrorPattern | None:
        """获取匹配错误消息的模式"""
        for pattern in self._patterns.values():
            if re.search(pattern.pattern, error_message, re.IGNORECASE):
                return pattern
        return None


class IntelligentFixer:
    """智能修复器

    提供错误分析、修复建议生成和自动修复功能。

    使用示例:
        fixer = IntelligentFixer()
        analysis = fixer.analyze_error(error_message, code)
        result = fixer.apply_fix(code, analysis.suggestions[0])
    """

    def __init__(self) -> None:
        """初始化修复器"""
        self._learner = ErrorPatternLearner()
        self._fix_history: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def analyze_error(
        self,
        error_message: str,
        code: str,
        traceback_str: str | None = None,
    ) -> ErrorAnalysis:
        """分析错误

        Args:
            error_message: 错误信息
            code: 代码内容
            traceback_str: 追溯信息（可选）

        Returns:
            ErrorAnalysis: 错误分析结果
        """
        # 解析错误信息
        error_type, message, line, column = self._parse_error(error_message, traceback_str)

        # 获取模式
        pattern = self._learner.get_pattern_for_error(error_message)

        # 确定类别
        category = pattern.category if pattern else ErrorCategory.RUNTIME

        # 提取上下文
        context = self._extract_context(code, line)

        # 生成建议
        suggestions = self._generate_suggestions(
            error_type,
            message,
            code,
            line,
            category,
            pattern,
        )

        return ErrorAnalysis(
            error_type=error_type,
            category=category,
            message=message,
            line=line,
            column=column,
            traceback=traceback_str or "",
            context=context,
            suggestions=suggestions,
        )

    def _parse_error(
        self,
        error_message: str,
        traceback_str: str | None,
    ) -> tuple[str, str, int, int | None]:
        """解析错误信息"""
        # 提取错误类型
        error_type_match = re.match(r'(\w+Error|Exception):', error_message)
        error_type = error_type_match.group(1) if error_type_match else "UnknownError"

        # 提取消息
        message = error_message.split(":", 1)[1].strip() if ":" in error_message else error_message

        # 提取行号
        line = 0
        column = None

        if traceback_str:
            line_match = re.search(r'File ".*", line (\d+)', traceback_str)
            if line_match:
                line = int(line_match.group(1))

        return error_type, message, line, column

    def _extract_context(self, code: str, line: int) -> dict[str, Any]:
        """提取错误上下文"""
        lines = code.split("\n")

        context = {
            "line_content": lines[line - 1] if 0 < line <= len(lines) else "",
            "prev_lines": lines[max(0, line - 3):line - 1] if line > 1 else [],
            "next_lines": lines[line:line + 2] if line < len(lines) else [],
        }

        return context

    def _generate_suggestions(
        self,
        error_type: str,
        message: str,
        code: str,
        line: int,
        category: ErrorCategory,
        pattern: ErrorPattern | None,
    ) -> list[FixSuggestion]:
        """生成修复建议"""
        suggestions: list[FixSuggestion] = []

        if category == ErrorCategory.NAME:
            suggestions.extend(self._generate_name_fix(message, code, line))

        elif category == ErrorCategory.KEY:
            suggestions.extend(self._generate_key_fix(message, code, line))

        elif category == ErrorCategory.ATTRIBUTE:
            suggestions.extend(self._generate_attribute_fix(message, code, line))

        elif category == ErrorCategory.INDEX:
            suggestions.extend(self._generate_index_fix(code, line))

        elif category == ErrorCategory.TYPE:
            suggestions.extend(self._generate_type_fix(message, code, line))

        elif category == ErrorCategory.INDENTATION:
            suggestions.extend(self._generate_indentation_fix(code, line))

        elif category == ErrorCategory.SYNTAX:
            suggestions.extend(self._generate_syntax_fix(message, code, line))

        elif category == ErrorCategory.MODSDK:
            suggestions.extend(self._generate_modsdk_fix(message, code, line))

        else:
            # 通用建议
            suggestions.append(FixSuggestion(
                description="检查代码逻辑",
                code_fix="",
                confidence=FixConfidence.LOW,
                auto_applicable=False,
                explanation="无法自动修复，请检查代码逻辑",
                line_start=line,
                line_end=line,
            ))

        return suggestions

    def _generate_name_fix(
        self,
        message: str,
        code: str,
        line: int,
    ) -> list[FixSuggestion]:
        """生成 NameError 修复建议"""
        suggestions: list[FixSuggestion] = []

        # 提取未定义的变量名
        match = re.search(r"name\s+'(\w+)'\s+is\s+not\s+defined", message)
        if not match:
            return suggestions

        var_name = match.group(1)
        lines = code.split("\n")

        if 0 < line <= len(lines):
            line_content = lines[line - 1]

            # 建议使用全局变量或定义变量
            suggestions.append(FixSuggestion(
                description=f"定义变量 '{var_name}'",
                code_fix=f"{var_name} = None  # TODO: 初始化变量\n{line_content}",
                confidence=FixConfidence.MEDIUM,
                auto_applicable=False,
                explanation=f"变量 '{var_name}' 在使用前需要定义",
                line_start=line,
                line_end=line,
                priority=1,
            ))

            # 检查是否可能是拼写错误
            defined_vars = self._extract_defined_vars(code)
            similar = difflib.get_close_matches(var_name, defined_vars, n=1, cutoff=0.6)
            if similar:
                suggestions.append(FixSuggestion(
                    description=f"使用相似变量 '{similar[0]}'",
                    code_fix=line_content.replace(var_name, similar[0]),
                    confidence=FixConfidence.HIGH,
                    auto_applicable=True,
                    explanation=f"'{var_name}' 可能是 '{similar[0]}' 的拼写错误",
                    line_start=line,
                    line_end=line,
                    priority=0,
                ))

        return suggestions

    def _generate_key_fix(
        self,
        message: str,
        code: str,
        line: int,
    ) -> list[FixSuggestion]:
        """生成 KeyError 修复建议"""
        suggestions: list[FixSuggestion] = []

        match = re.search(r"['\"](\w+)['\"]", message)
        if not match:
            return suggestions

        key = match.group(1)
        lines = code.split("\n")

        if 0 < line <= len(lines):
            line_content = lines[line - 1]

            # 查找字典访问模式
            dict_access = re.search(r"(\w+)\[['\"]" + re.escape(key) + r"['\"]\]", line_content)
            if dict_access:
                dict_name = dict_access.group(1)

                # 建议 1: 使用 .get() 方法
                safe_access = f"{dict_name}.get('{key}', '')"
                new_line = line_content.replace(dict_access.group(0), safe_access)
                suggestions.append(FixSuggestion(
                    description=f"使用 {dict_name}.get('{key}') 方法",
                    code_fix=new_line,
                    confidence=FixConfidence.HIGH,
                    auto_applicable=True,
                    explanation=f"使用 .get() 方法可以避免 KeyError，返回默认值而不是抛出异常",
                    line_start=line,
                    line_end=line,
                    priority=0,
                ))

                # 建议 2: 检查键是否存在
                check_key = f"if '{key}' in {dict_name}:\n    {line_content}\nelse:\n    # 处理键不存在的情况"
                suggestions.append(FixSuggestion(
                    description=f"检查键 '{key}' 是否存在",
                    code_fix=check_key,
                    confidence=FixConfidence.MEDIUM,
                    auto_applicable=False,
                    explanation="在使用键之前检查它是否存在",
                    line_start=line,
                    line_end=line,
                    priority=1,
                ))

        return suggestions

    def _generate_attribute_fix(
        self,
        message: str,
        code: str,
        line: int,
    ) -> list[FixSuggestion]:
        """生成 AttributeError 修复建议"""
        suggestions: list[FixSuggestion] = []

        match = re.search(r"'(\w+)'\s+object\s+has\s+no\s+attribute\s+'(\w+)'", message)
        if not match:
            return suggestions

        obj_type = match.group(1)
        attr = match.group(2)
        lines = code.split("\n")

        if 0 < line <= len(lines):
            line_content = lines[line - 1]

            # 建议: 使用 hasattr 检查
            suggestions.append(FixSuggestion(
                description=f"使用 hasattr() 检查属性 '{attr}'",
                code_fix=f"if hasattr(obj, '{attr}'):\n    {line_content}\nelse:\n    # 处理属性不存在",
                confidence=FixConfidence.MEDIUM,
                auto_applicable=False,
                explanation=f"'{obj_type}' 对象没有属性 '{attr}'，使用 hasattr() 检查",
                line_start=line,
                line_end=line,
            ))

            # 建议: 使用 getattr 获取属性
            suggestions.append(FixSuggestion(
                description=f"使用 getattr() 获取属性",
                code_fix=line_content.replace(f".{attr}", f".get('{attr}', None)"),
                confidence=FixConfidence.LOW,
                auto_applicable=False,
                explanation="使用 getattr() 可以提供默认值",
                line_start=line,
                line_end=line,
            ))

        return suggestions

    def _generate_index_fix(
        self,
        code: str,
        line: int,
    ) -> list[FixSuggestion]:
        """生成 IndexError 修复建议"""
        suggestions: list[FixSuggestion] = []

        lines = code.split("\n")

        if 0 < line <= len(lines):
            line_content = lines[line - 1]

            # 查找列表访问模式
            list_access = re.search(r"(\w+)\[(\d+)\]", line_content)
            if list_access:
                list_name = list_access.group(1)
                index = list_access.group(2)

                # 建议: 检查索引范围
                safe_access = f"if len({list_name}) > {index}:\n    {line_content}\nelse:\n    # 处理索引超出范围"
                suggestions.append(FixSuggestion(
                    description=f"检查 {list_name} 的长度",
                    code_fix=safe_access,
                    confidence=FixConfidence.HIGH,
                    auto_applicable=False,
                    explanation="在访问列表元素之前检查索引是否有效",
                    line_start=line,
                    line_end=line,
                ))

        return suggestions

    def _generate_type_fix(
        self,
        message: str,
        code: str,
        line: int,
    ) -> list[FixSuggestion]:
        """生成 TypeError 修复建议"""
        suggestions: list[FixSuggestion] = []

        lines = code.split("\n")

        if 0 < line <= len(lines):
            line_content = lines[line - 1]

            # 建议: 检查类型
            suggestions.append(FixSuggestion(
                description="检查变量类型",
                code_fix=f"if isinstance(var, expected_type):\n    {line_content}",
                confidence=FixConfidence.MEDIUM,
                auto_applicable=False,
                explanation="TypeError 通常是因为操作数类型不正确，检查类型后再操作",
                line_start=line,
                line_end=line,
            ))

        return suggestions

    def _generate_indentation_fix(
        self,
        code: str,
        line: int,
    ) -> list[FixSuggestion]:
        """生成缩进错误修复建议"""
        suggestions: list[FixSuggestion] = []

        lines = code.split("\n")

        if 0 < line <= len(lines):
            line_content = lines[line - 1]

            # 建议: 修复缩进
            suggestions.append(FixSuggestion(
                description="修复缩进为 4 空格",
                code_fix="    " + line_content.lstrip(),
                confidence=FixConfidence.HIGH,
                auto_applicable=True,
                explanation="Python 使用缩进来定义代码块，使用 4 空格缩进",
                line_start=line,
                line_end=line,
            ))

        return suggestions

    def _generate_syntax_fix(
        self,
        message: str,
        code: str,
        line: int,
    ) -> list[FixSuggestion]:
        """生成语法错误修复建议"""
        suggestions: list[FixSuggestion] = []

        lines = code.split("\n")

        if 0 < line <= len(lines):
            line_content = lines[line - 1]

            # 检查常见语法问题
            # 1. 缺少冒号
            if line_content.rstrip().endswith(("if", "else", "for", "while", "def", "class", "try", "except", "finally")):
                suggestions.append(FixSuggestion(
                    description="添加缺失的冒号",
                    code_fix=line_content.rstrip() + ":",
                    confidence=FixConfidence.HIGH,
                    auto_applicable=True,
                    explanation="语句末尾缺少冒号",
                    line_start=line,
                    line_end=line,
                ))

            # 2. 括号不匹配
            open_parens = line_content.count("(") - line_content.count(")")
            open_brackets = line_content.count("[") - line_content.count("]")
            open_braces = line_content.count("{") - line_content.count("}")

            if open_parens > 0:
                suggestions.append(FixSuggestion(
                    description="补全缺失的右括号",
                    code_fix=line_content + ")" * open_parens,
                    confidence=FixConfidence.HIGH,
                    auto_applicable=True,
                    explanation=f"缺少 {open_parens} 个右括号",
                    line_start=line,
                    line_end=line,
                ))

        return suggestions

    def _generate_modsdk_fix(
        self,
        message: str,
        code: str,
        line: int,
    ) -> list[FixSuggestion]:
        """生成 ModSDK 错误修复建议"""
        suggestions: list[FixSuggestion] = []

        # 提取事件/API 名称
        event_match = re.search(r"'(\w+)'", message)

        if event_match:
            name = event_match.group(1)
            lines = code.split("\n")

            if 0 < line <= len(lines):
                line_content = lines[line - 1]

                # 建议检查拼写
                known_events = [
                    "OnServerStart", "OnServerStop", "OnAddServerPlayer",
                    "OnDelServerPlayer", "OnServerChat", "OnEntityCreated",
                    "OnEntityDestroyed", "OnPlayerAttack", "OnBlockActivated",
                ]

                similar = difflib.get_close_matches(name, known_events, n=1, cutoff=0.6)
                if similar:
                    suggestions.append(FixSuggestion(
                        description=f"使用正确的事件名 '{similar[0]}'",
                        code_fix=line_content.replace(name, similar[0]),
                        confidence=FixConfidence.HIGH,
                        auto_applicable=True,
                        explanation=f"'{name}' 可能是 '{similar[0]}' 的拼写错误",
                        line_start=line,
                        line_end=line,
                    ))

        return suggestions

    def _extract_defined_vars(self, code: str) -> list[str]:
        """提取已定义的变量"""
        variables = set()

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables.add(target.id)
                elif isinstance(node, ast.FunctionDef):
                    variables.add(node.name)
                    for arg in node.args.args:
                        variables.add(arg.arg)
        except SyntaxError:
            # 正则表达式后备
            var_pattern = r'^\s*(\w+)\s*='
            for line in code.split("\n"):
                match = re.match(var_pattern, line)
                if match:
                    variables.add(match.group(1))

        return list(variables)

    def apply_fix(
        self,
        code: str,
        suggestion: FixSuggestion,
        verify: bool = True,
    ) -> FixResult:
        """应用修复建议

        Args:
            code: 原始代码
            suggestion: 修复建议
            verify: 是否验证修复

        Returns:
            FixResult: 修复结果
        """
        lines = code.split("\n")

        if not suggestion.auto_applicable:
            return FixResult(
                status=FixStatus.MANUAL_REQUIRED,
                original_code=code,
                fixed_code=code,
                changes=[],
                suggestions_applied=[],
                warnings=["此修复建议需要手动确认"],
            )

        # 应用修复
        if suggestion.line_start > 0 and suggestion.line_start <= len(lines):
            # 单行修复
            if suggestion.line_start == suggestion.line_end:
                old_line = lines[suggestion.line_start - 1]
                lines[suggestion.line_start - 1] = suggestion.code_fix
                changes = [{
                    "line": suggestion.line_start,
                    "old": old_line,
                    "new": suggestion.code_fix,
                }]
            else:
                # 多行修复
                old_lines = lines[suggestion.line_start - 1:suggestion.line_end]
                new_lines = suggestion.code_fix.split("\n")
                lines[suggestion.line_start - 1:suggestion.line_end] = new_lines
                changes = [{
                    "line_start": suggestion.line_start,
                    "line_end": suggestion.line_end,
                    "old": "\n".join(old_lines),
                    "new": suggestion.code_fix,
                }]
        else:
            return FixResult(
                status=FixStatus.FAILED,
                original_code=code,
                fixed_code=code,
                changes=[],
                suggestions_applied=[],
                warnings=["无效的行号"],
            )

        fixed_code = "\n".join(lines)

        # 验证修复
        test_passed = None
        if verify:
            test_passed = self._verify_fix(code, fixed_code)

        # 确定状态
        if test_passed is False:
            status = FixStatus.PARTIAL
        else:
            status = FixStatus.SUCCESS

        return FixResult(
            status=status,
            original_code=code,
            fixed_code=fixed_code,
            changes=changes,
            suggestions_applied=[suggestion.description],
            warnings=[],
            test_passed=test_passed,
        )

    def _verify_fix(self, original_code: str, fixed_code: str) -> bool:
        """验证修复是否有效"""
        try:
            ast.parse(fixed_code)
            return True
        except SyntaxError:
            return False

    def predict_fix_effectiveness(
        self,
        suggestion: FixSuggestion,
        code: str,
    ) -> float:
        """预测修复效果

        Args:
            suggestion: 修复建议
            code: 原始代码

        Returns:
            float: 预测成功率 (0.0 - 1.0)
        """
        # 基于置信度和自动适用性
        base_score = {
            FixConfidence.HIGH: 0.9,
            FixConfidence.MEDIUM: 0.7,
            FixConfidence.LOW: 0.4,
        }[suggestion.confidence]

        if suggestion.auto_applicable:
            # 自动适用的修复通常更可靠
            base_score += 0.05

        # 检查代码复杂度
        try:
            tree = ast.parse(code)
            complexity = sum(1 for _ in ast.walk(tree) if isinstance(_, (ast.If, ast.For, ast.While)))
            if complexity > 10:
                base_score -= 0.1
        except SyntaxError:
            base_score -= 0.2

        return min(1.0, max(0.0, base_score))


# 全局实例
_fixer: IntelligentFixer | None = None


def get_intelligent_fixer() -> IntelligentFixer:
    """获取全局修复器"""
    global _fixer
    if _fixer is None:
        _fixer = IntelligentFixer()
    return _fixer


def analyze_and_fix(error_message: str, code: str) -> FixResult | None:
    """便捷函数：分析并修复错误

    Args:
        error_message: 错误信息
        code: 代码内容

    Returns:
        FixResult | None: 修复结果
    """
    fixer = get_intelligent_fixer()
    analysis = fixer.analyze_error(error_message, code)

    if analysis.suggestions:
        # 选择优先级最高的建议
        best = min(analysis.suggestions, key=lambda s: s.priority)
        if best.auto_applicable:
            return fixer.apply_fix(code, best)

    return None