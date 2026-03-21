"""
重构建议引擎

分析代码并提供重构建议。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from .smells import CodeSmell, SmellType

if TYPE_CHECKING:
    pass


class RefactorType(Enum):
    """重构类型"""

    EXTRACT_FUNCTION = "extract_function"  # 提取函数
    EXTRACT_VARIABLE = "extract_variable"  # 提取变量
    EXTRACT_CLASS = "extract_class"  # 提取类
    INLINE_VARIABLE = "inline_variable"  # 内联变量
    INLINE_FUNCTION = "inline_function"  # 内联函数
    RENAME = "rename"  # 重命名
    MOVE_METHOD = "move_method"  # 移动方法
    MOVE_FIELD = "move_field"  # 移动字段
    ENCAPSULATE_FIELD = "encapsulate_field"  # 封装字段
    REPLACE_MAGIC_NUMBER = "replace_magic_number"  # 替换魔法数字
    SIMPLIFY_CONDITION = "simplify_condition"  # 简化条件
    DECOMPOSE_CONDITION = "decompose_condition"  # 分解条件
    INTRODUCE_NULL_OBJECT = "introduce_null_object"  # 引入空对象
    INTRODUCE_ASSERTION = "introduce_assertion"  # 引入断言
    ADD_TYPE_HINT = "add_type_hint"  # 添加类型注解
    ADD_DOCSTRING = "add_docstring"  # 添加文档字符串


@dataclass
class RefactorSuggestion:
    """重构建议"""

    type: RefactorType  # 重构类型
    message: str  # 描述信息
    line: int  # 行号
    end_line: int | None = None  # 结束行号
    original_code: str = ""  # 原始代码
    suggested_code: str = ""  # 建议代码
    explanation: str = ""  # 解释说明
    priority: int = 0  # 优先级（越高越重要）
    auto_applicable: bool = False  # 是否可自动应用

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "type": self.type.value,
            "message": self.message,
            "line": self.line,
            "end_line": self.end_line,
            "original_code": self.original_code,
            "suggested_code": self.suggested_code,
            "explanation": self.explanation,
            "priority": self.priority,
            "auto_applicable": self.auto_applicable,
        }


class RefactorEngine:
    """重构建议引擎

    分析代码异味并提供具体的重构建议。

    Example:
        >>> engine = RefactorEngine()
        >>> suggestions = engine.suggest_refactors(smells, code)
        >>> for s in suggestions:
        ...     print(f"{s.type.value}: {s.message}")
    """

    def __init__(self) -> None:
        """初始化重构引擎"""
        self._refactor_handlers: dict[SmellType, callable] = {
            SmellType.LONG_FUNCTION: self._suggest_extract_function,
            SmellType.MAGIC_NUMBER: self._suggest_replace_magic_number,
            SmellType.BARE_EXCEPT: self._suggest_fix_bare_except,
            SmellType.MISSING_DOCSTRING: self._suggest_add_docstring,
            SmellType.DEEPLY_NESTED: self._suggest_simplify_nesting,
            SmellType.HIGH_COMPLEXITY: self._suggest_reduce_complexity,
            SmellType.SHORT_NAME: self._suggest_rename,
            SmellType.LONG_NAME: self._suggest_rename,
            SmellType.PRINT_DEBUG: self._suggest_replace_print,
        }

    def suggest_refactors(self, smells: list[CodeSmell], code: str) -> list[RefactorSuggestion]:
        """根据代码异味生成重构建议

        Args:
            smells: 代码异味列表
            code: 源代码

        Returns:
            重构建议列表
        """
        suggestions: list[RefactorSuggestion] = []
        lines = code.split("\n")

        for smell in smells:
            handler = self._refactor_handlers.get(smell.type)
            if handler:
                suggestion = handler(smell, lines)
                if suggestion:
                    suggestions.append(suggestion)

        # 按优先级和行号排序
        suggestions.sort(key=lambda s: (-s.priority, s.line))

        return suggestions

    def _suggest_extract_function(
        self, smell: CodeSmell, lines: list[str]
    ) -> RefactorSuggestion | None:
        """建议提取函数"""
        if not smell.end_line:
            return None

        # 提取原始代码
        original = "\n".join(lines[smell.line - 1 : smell.end_line])

        return RefactorSuggestion(
            type=RefactorType.EXTRACT_FUNCTION,
            message="将函数拆分为更小的函数",
            line=smell.line,
            end_line=smell.end_line,
            original_code=original,
            suggested_code="# 建议提取为独立函数\n# def extracted_function(...):\n#     ...",
            explanation="长函数难以理解和维护。建议将其拆分为多个职责单一的函数。",
            priority=8,
            auto_applicable=False,
        )

    def _suggest_replace_magic_number(
        self, smell: CodeSmell, lines: list[str]
    ) -> RefactorSuggestion | None:
        """建议替换魔法数字"""
        if smell.line > len(lines):
            return None

        line = lines[smell.line - 1]
        match = re.search(r"(?<!\w)(\d{3,})(?!\w)", line)
        if not match:
            return None

        magic_num = match.group(1)

        return RefactorSuggestion(
            type=RefactorType.REPLACE_MAGIC_NUMBER,
            message=f"将魔法数字 {magic_num} 替换为有意义的常量",
            line=smell.line,
            original_code=line.strip(),
            suggested_code=f"MAGIC_NUMBER = {magic_num}  # TODO: 替换为有意义的名称",
            explanation=f"魔法数字 {magic_num} 缺乏语义，难以理解其含义。将其定义为常量可以提高代码可读性。",
            priority=5,
            auto_applicable=True,
        )

    def _suggest_fix_bare_except(
        self, smell: CodeSmell, lines: list[str]
    ) -> RefactorSuggestion | None:
        """建议修复裸 except"""
        if smell.line > len(lines):
            return None

        line = lines[smell.line - 1]
        indent = len(line) - len(line.lstrip())
        indent_str = line[:indent]

        return RefactorSuggestion(
            type=RefactorType.SIMPLIFY_CONDITION,
            message="指定具体的异常类型",
            line=smell.line,
            original_code=line.strip(),
            suggested_code=f"{indent_str}except Exception as e:",
            explanation="裸 except 会捕获所有异常，包括系统退出和键盘中断。建议指定具体的异常类型。",
            priority=9,
            auto_applicable=True,
        )

    def _suggest_add_docstring(
        self, smell: CodeSmell, lines: list[str]
    ) -> RefactorSuggestion | None:
        """建议添加文档字符串"""
        if smell.line > len(lines):
            return None

        line = lines[smell.line - 1]
        indent = len(line) - len(line.lstrip())
        indent_str = line[:indent]

        # 根据类型生成模板
        if "函数" in smell.message:
            docstring = f'{indent_str}    """TODO: 添加函数描述\n\n    Args:\n        TODO: 添加参数说明\n\n    Returns:\n        TODO: 添加返回值说明\n    """'
        elif "类" in smell.message:
            docstring = f'{indent_str}    """TODO: 添加类描述\n\n    Attributes:\n        TODO: 添加属性说明\n    """'
        else:
            docstring = f'{indent_str}    """TODO: 添加描述"""'

        return RefactorSuggestion(
            type=RefactorType.ADD_DOCSTRING,
            message="添加文档字符串",
            line=smell.line,
            original_code=line.strip(),
            suggested_code=docstring,
            explanation="文档字符串帮助其他开发者理解代码的用途和使用方法。",
            priority=4,
            auto_applicable=False,
        )

    def _suggest_simplify_nesting(
        self, smell: CodeSmell, lines: list[str]
    ) -> RefactorSuggestion | None:
        """建议简化嵌套"""
        return RefactorSuggestion(
            type=RefactorType.SIMPLIFY_CONDITION,
            message="使用提前返回或提取函数简化嵌套",
            line=smell.line,
            original_code="# 深度嵌套的代码",
            suggested_code="# 使用 if not condition: return 提前退出\n# 或将嵌套逻辑提取到独立函数",
            explanation="过深的嵌套使代码难以阅读。使用提前返回（guard clause）可以减少嵌套层级。",
            priority=7,
            auto_applicable=False,
        )

    def _suggest_reduce_complexity(
        self, smell: CodeSmell, lines: list[str]
    ) -> RefactorSuggestion | None:
        """建议降低复杂度"""
        return RefactorSuggestion(
            type=RefactorType.DECOMPOSE_CONDITION,
            message="简化条件逻辑",
            line=smell.line,
            original_code="# 复杂的条件逻辑",
            suggested_code="# 将复杂条件提取为独立函数\n# def should_process(...):\n#     return condition1 and condition2",
            explanation="复杂的条件逻辑难以理解。将条件提取为独立的函数或使用字典映射可以简化代码。",
            priority=7,
            auto_applicable=False,
        )

    def _suggest_rename(self, smell: CodeSmell, lines: list[str]) -> RefactorSuggestion | None:
        """建议重命名"""
        if smell.line > len(lines):
            return None

        return RefactorSuggestion(
            type=RefactorType.RENAME,
            message=smell.suggestion,
            line=smell.line,
            original_code=lines[smell.line - 1].strip(),
            suggested_code="# 使用更具描述性的名称",
            explanation=smell.message,
            priority=6,
            auto_applicable=False,
        )

    def _suggest_replace_print(
        self, smell: CodeSmell, lines: list[str]
    ) -> RefactorSuggestion | None:
        """建议替换 print"""
        if smell.line > len(lines):
            return None

        line = lines[smell.line - 1]
        indent = len(line) - len(line.lstrip())
        indent_str = line[:indent]

        # 提取 print 参数
        match = re.search(r"print\s*\((.*)\)", line)
        args = match.group(1) if match else "..."

        return RefactorSuggestion(
            type=RefactorType.EXTRACT_FUNCTION,
            message="使用日志模块替代 print",
            line=smell.line,
            original_code=line.strip(),
            suggested_code=f"{indent_str}import logging\n{indent_str}logging.debug({args})",
            explanation="print 语句不适合生产环境。使用日志模块可以更好地控制输出级别和格式。",
            priority=5,
            auto_applicable=True,
        )

    def generate_diff(self, suggestion: RefactorSuggestion) -> str:
        """生成差异描述"""
        lines = []
        lines.append(f"--- 原始 (行 {suggestion.line})")
        lines.append("+++ 建议")
        lines.append(f"- {suggestion.original_code}")
        lines.append(f"+ {suggestion.suggested_code}")
        return "\n".join(lines)
