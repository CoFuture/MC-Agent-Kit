"""
自动修复器模块

根据诊断结果自动修复代码错误。
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from datetime import datetime
from difflib import unified_diff
from enum import Enum
from typing import Any, Callable

from .diagnoser import (
    DiagnosisResult,
    ErrorDiagnoser,
    ErrorInfo,
    ErrorType,
    FixSuggestion,
)


class FixStatus(Enum):
    """修复状态"""

    SUCCESS = "success"  # 修复成功
    PARTIAL = "partial"  # 部分修复
    FAILED = "failed"  # 修复失败
    SKIPPED = "skipped"  # 跳过（需要人工确认）
    MANUAL_REQUIRED = "manual_required"  # 需要人工处理


@dataclass
class Replacement:
    """代码替换"""

    start_line: int  # 起始行
    end_line: int  # 结束行
    original: str  # 原始代码
    replacement: str  # 替换代码
    description: str  # 替换描述


@dataclass
class FixContext:
    """修复上下文"""

    file_path: str | None = None  # 文件路径
    original_code: str = ""  # 原始代码
    line_start: int = 1  # 起始行号
    indent: str = ""  # 缩进
    variables: dict[str, Any] = field(default_factory=dict)  # 变量上下文


@dataclass
class FixResult:
    """修复结果"""

    status: FixStatus  # 修复状态
    original_code: str  # 原始代码
    fixed_code: str  # 修复后代码
    replacements: list[Replacement]  # 替换列表
    message: str = ""  # 消息
    suggestions: list[FixSuggestion] = field(default_factory=list)  # 剩余建议
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳


class AutoFixer:
    """
    自动修复器。

    根据错误诊断结果自动修复代码。

    使用示例:
        fixer = AutoFixer()
        result = fixer.fix(code, diagnosis_result)
        if result.status == FixStatus.SUCCESS:
            print(result.fixed_code)
    """

    def __init__(self, auto_apply: bool = False):
        """
        初始化自动修复器。

        Args:
            auto_apply: 是否自动应用所有可自动修复的建议
        """
        self.auto_apply = auto_apply
        self.diagnoser = ErrorDiagnoser()
        self._fix_handlers: dict[ErrorType, Callable] = {
            ErrorType.KEY_ERROR: self._fix_key_error,
            ErrorType.ATTRIBUTE_ERROR: self._fix_attribute_error,
            ErrorType.INDEX_ERROR: self._fix_index_error,
            ErrorType.ZERO_DIVISION_ERROR: self._fix_zero_division,
        }

    def fix(
        self,
        code: str,
        diagnosis: DiagnosisResult,
        context: FixContext | None = None,
    ) -> FixResult:
        """
        修复代码。

        Args:
            code: 原始代码
            diagnosis: 诊断结果
            context: 修复上下文

        Returns:
            FixResult: 修复结果
        """
        if context is None:
            context = FixContext(original_code=code)

        error_info = diagnosis.error_info
        suggestions = list(diagnosis.suggestions)

        # 检查是否有可自动修复的建议
        auto_fixable = [s for s in suggestions if s.auto_fixable]

        if not auto_fixable:
            return FixResult(
                status=FixStatus.MANUAL_REQUIRED,
                original_code=code,
                fixed_code=code,
                replacements=[],
                message="没有可自动修复的建议，需要人工处理",
                suggestions=suggestions,
            )

        # 获取最高优先级的自动修复建议
        best_suggestion = max(auto_fixable, key=lambda s: s.priority)

        # 调用对应的修复处理器
        handler = self._fix_handlers.get(error_info.error_type)
        if handler:
            fixed_code, replacements = handler(code, error_info, best_suggestion, context)
        else:
            # 通用修复
            fixed_code, replacements = self._generic_fix(code, error_info, best_suggestion, context)

        # 检查是否有修复被应用
        if fixed_code != code:
            remaining_suggestions = [s for s in suggestions if s != best_suggestion]
            status = FixStatus.SUCCESS if not remaining_suggestions else FixStatus.PARTIAL

            return FixResult(
                status=status,
                original_code=code,
                fixed_code=fixed_code,
                replacements=replacements,
                message=f"应用了修复：{best_suggestion.description}",
                suggestions=remaining_suggestions,
            )

        return FixResult(
            status=FixStatus.FAILED,
            original_code=code,
            fixed_code=code,
            replacements=[],
            message="无法应用修复",
            suggestions=suggestions,
        )

    def fix_from_error_log(self, code: str, error_log: str) -> FixResult:
        """
        从错误日志修复代码。

        Args:
            code: 原始代码
            error_log: 错误日志

        Returns:
            FixResult: 修复结果
        """
        diagnosis = self.diagnoser.diagnose(error_log)
        return self.fix(code, diagnosis)

    def _fix_key_error(
        self,
        code: str,
        error_info: ErrorInfo,
        suggestion: FixSuggestion,
        context: FixContext,
    ) -> tuple[str, list[Replacement]]:
        """修复 KeyError"""
        missing_key = error_info.context.get("missing_key", "")
        if not missing_key:
            return code, []

        lines = code.split("\n")
        replacements = []
        new_lines = list(lines)

        # 查找字典访问模式
        pattern = re.compile(rf"(\w+)\[['\"]({re.escape(missing_key)})['\"]\]")

        for i, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                dict_name = match.group(1)
                original = f"{dict_name}['{missing_key}']"
                replacement = f"{dict_name}.get('{missing_key}', None)"

                new_line = line.replace(original, replacement)
                new_lines[i] = new_line

                replacements.append(
                    Replacement(
                        start_line=i + 1,
                        end_line=i + 1,
                        original=original,
                        replacement=replacement,
                        description=f"使用 .get() 方法安全访问键 '{missing_key}'",
                    )
                )

        return "\n".join(new_lines), replacements

    def _fix_attribute_error(
        self,
        code: str,
        error_info: ErrorInfo,
        suggestion: FixSuggestion,
        context: FixContext,
    ) -> tuple[str, list[Replacement]]:
        """修复 AttributeError"""
        missing_attr = error_info.context.get("missing_attribute", "")
        if not missing_attr:
            return code, []

        lines = code.split("\n")
        replacements = []
        new_lines = list(lines)

        # 查找属性访问模式
        pattern = re.compile(rf"(\w+)\.{re.escape(missing_attr)}")

        for i, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                obj_name = match.group(1)
                original = f"{obj_name}.{missing_attr}"
                replacement = f"getattr({obj_name}, '{missing_attr}', None)"

                new_line = line.replace(original, replacement)
                new_lines[i] = new_line

                replacements.append(
                    Replacement(
                        start_line=i + 1,
                        end_line=i + 1,
                        original=original,
                        replacement=replacement,
                        description=f"使用 getattr() 安全访问属性 '{missing_attr}'",
                    )
                )

        return "\n".join(new_lines), replacements

    def _fix_index_error(
        self,
        code: str,
        error_info: ErrorInfo,
        suggestion: FixSuggestion,
        context: FixContext,
    ) -> tuple[str, list[Replacement]]:
        """修复 IndexError"""
        lines = code.split("\n")
        replacements = []
        new_lines = list(lines)

        # 查找列表索引访问模式
        pattern = re.compile(r"(\w+)\[(\w+)\]")

        for i, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                list_name = match.group(1)
                index_name = match.group(2)
                original = f"{list_name}[{index_name}]"
                replacement = f"{list_name}[{index_name}] if 0 <= {index_name} < len({list_name}) else None"

                new_line = line.replace(original, replacement)
                new_lines[i] = new_line

                replacements.append(
                    Replacement(
                        start_line=i + 1,
                        end_line=i + 1,
                        original=original,
                        replacement=replacement,
                        description="添加索引边界检查",
                    )
                )

        return "\n".join(new_lines), replacements

    def _fix_zero_division(
        self,
        code: str,
        error_info: ErrorInfo,
        suggestion: FixSuggestion,
        context: FixContext,
    ) -> tuple[str, list[Replacement]]:
        """修复 ZeroDivisionError"""
        lines = code.split("\n")
        replacements = []
        new_lines = list(lines)

        # 查找除法模式
        pattern = re.compile(r"(\w+)\s*/\s*(\w+)")

        for i, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                dividend = match.group(1)
                divisor = match.group(2)
                original = f"{dividend} / {divisor}"
                replacement = f"{dividend} / {divisor} if {divisor} != 0 else None"

                new_line = line.replace(original, replacement)
                new_lines[i] = new_line

                replacements.append(
                    Replacement(
                        start_line=i + 1,
                        end_line=i + 1,
                        original=original,
                        replacement=replacement,
                        description="添加除零检查",
                    )
                )

        return "\n".join(new_lines), replacements

    def _generic_fix(
        self,
        code: str,
        error_info: ErrorInfo,
        suggestion: FixSuggestion,
        context: FixContext,
    ) -> tuple[str, list[Replacement]]:
        """通用修复处理器"""
        if suggestion.code_before and suggestion.code_after:
            lines = code.split("\n")
            replacements = []
            new_lines = list(lines)

            for i, line in enumerate(lines):
                if suggestion.code_before in line:
                    new_line = line.replace(suggestion.code_before, suggestion.code_after)
                    new_lines[i] = new_line

                    replacements.append(
                        Replacement(
                            start_line=i + 1,
                            end_line=i + 1,
                            original=suggestion.code_before,
                            replacement=suggestion.code_after,
                            description=suggestion.description,
                        )
                    )

            return "\n".join(new_lines), replacements

        return code, []

    def preview_fix(self, code: str, diagnosis: DiagnosisResult) -> str:
        """
        预览修复结果（生成 diff）。

        Args:
            code: 原始代码
            diagnosis: 诊断结果

        Returns:
            diff 字符串
        """
        result = self.fix(code, diagnosis)

        if result.fixed_code == code:
            return "没有可应用的修复"

        diff = unified_diff(
            code.splitlines(keepends=True),
            result.fixed_code.splitlines(keepends=True),
            fromfile="original",
            tofile="fixed",
        )

        return "".join(diff)

    def batch_fix(
        self,
        code: str,
        error_logs: list[str],
    ) -> FixResult:
        """
        批量修复多个错误。

        Args:
            code: 原始代码
            error_logs: 错误日志列表

        Returns:
            FixResult: 最终修复结果
        """
        current_code = code
        all_replacements = []
        remaining_suggestions = []

        for error_log in error_logs:
            diagnosis = self.diagnoser.diagnose(error_log)
            result = self.fix(current_code, diagnosis)

            current_code = result.fixed_code
            all_replacements.extend(result.replacements)
            remaining_suggestions.extend(result.suggestions)

        status = FixStatus.SUCCESS if current_code != code else FixStatus.FAILED

        return FixResult(
            status=status,
            original_code=code,
            fixed_code=current_code,
            replacements=all_replacements,
            message=f"应用了 {len(all_replacements)} 个修复",
            suggestions=remaining_suggestions,
        )

    def is_auto_fixable(self, error_type: ErrorType) -> bool:
        """检查错误类型是否可自动修复"""
        return error_type in self._fix_handlers

    def get_supported_errors(self) -> list[ErrorType]:
        """获取支持自动修复的错误类型"""
        return list(self._fix_handlers.keys())
