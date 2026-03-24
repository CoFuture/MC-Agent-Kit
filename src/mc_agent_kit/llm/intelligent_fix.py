"""
智能修复模块

基于 LLM 的智能错误诊断和修复功能。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .base import (
    ChatMessage,
    CompletionResult,
    LLMConfig,
)
from .manager import LLMManager


class FixConfidence(Enum):
    """修复置信度"""
    HIGH = "high"      # 高置信度，可以直接应用
    MEDIUM = "medium"  # 中等置信度，建议人工确认
    LOW = "low"        # 低置信度，仅供参考


@dataclass
class ErrorContext:
    """错误上下文"""
    error_type: str = ""
    error_message: str = ""
    error_line: int | None = None
    file_path: str = ""
    code: str = ""
    stack_trace: str = ""
    related_code: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "error_line": self.error_line,
            "file_path": self.file_path,
            "code": self.code,
            "stack_trace": self.stack_trace,
            "related_code": self.related_code,
        }


@dataclass
class FixSuggestion:
    """修复建议"""
    description: str
    confidence: FixConfidence
    fix_code: str = ""
    explanation: str = ""
    line_start: int | None = None
    line_end: int | None = None
    related_docs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "confidence": self.confidence.value,
            "fix_code": self.fix_code,
            "explanation": self.explanation,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "related_docs": self.related_docs,
        }


@dataclass
class DiagnosisResult:
    """诊断结果"""
    error_type: str
    root_cause: str
    impact: str  # high, medium, low
    fix_suggestions: list[FixSuggestion]
    raw_result: CompletionResult | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": self.error_type,
            "root_cause": self.root_cause,
            "impact": self.impact,
            "fix_suggestions": [s.to_dict() for s in self.fix_suggestions],
            "raw_result": self.raw_result.to_dict() if self.raw_result else None,
        }


@dataclass
class FixResult:
    """修复结果"""
    original_code: str
    fixed_code: str
    changes: list[dict[str, Any]]
    success: bool
    message: str = ""
    raw_result: CompletionResult | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_code": self.original_code,
            "fixed_code": self.fixed_code,
            "changes": self.changes,
            "success": self.success,
            "message": self.message,
            "raw_result": self.raw_result.to_dict() if self.raw_result else None,
        }


class IntelligentFixer:
    """
    智能修复器

    基于 LLM 诊断错误并生成修复建议。
    """

    def __init__(
        self,
        llm_config: LLMConfig | None = None,
    ) -> None:
        self.llm_config = llm_config or LLMConfig(provider="mock")
        self.llm_manager = LLMManager()

    def diagnose(
        self,
        error_context: ErrorContext,
        **kwargs: Any,
    ) -> DiagnosisResult:
        """
        诊断错误

        Args:
            error_context: 错误上下文
            **kwargs: 额外参数

        Returns:
            DiagnosisResult: 诊断结果
        """
        # 构建消息
        messages = [
            ChatMessage.system(self._build_diagnosis_system_prompt()),
            ChatMessage.user(self._build_diagnosis_prompt(error_context)),
        ]

        # 调用 LLM
        result = self.llm_manager.complete(messages, self.llm_config, **kwargs)

        # 解析结果
        return self._parse_diagnosis_result(result.content, result)

    async def diagnose_async(
        self,
        error_context: ErrorContext,
        **kwargs: Any,
    ) -> DiagnosisResult:
        """
        异步诊断错误

        Args:
            error_context: 错误上下文
            **kwargs: 额外参数

        Returns:
            DiagnosisResult: 诊断结果
        """
        # 构建消息
        messages = [
            ChatMessage.system(self._build_diagnosis_system_prompt()),
            ChatMessage.user(self._build_diagnosis_prompt(error_context)),
        ]

        # 调用 LLM
        result = await self.llm_manager.complete_async(messages, self.llm_config, **kwargs)

        # 解析结果
        return self._parse_diagnosis_result(result.content, result)

    def fix(
        self,
        error_context: ErrorContext,
        diagnosis: DiagnosisResult | None = None,
        **kwargs: Any,
    ) -> FixResult:
        """
        修复代码

        Args:
            error_context: 错误上下文
            diagnosis: 诊断结果（可选）
            **kwargs: 额外参数

        Returns:
            FixResult: 修复结果
        """
        # 如果没有提供诊断结果，先诊断
        if diagnosis is None:
            diagnosis = self.diagnose(error_context, **kwargs)

        # 选择最佳修复建议
        best_fix = self._select_best_fix(diagnosis.fix_suggestions)

        if not best_fix:
            return FixResult(
                original_code=error_context.code,
                fixed_code=error_context.code,
                changes=[],
                success=False,
                message="无法生成修复建议",
            )

        # 应用修复
        fixed_code, changes = self._apply_fix(
            error_context.code,
            best_fix,
            error_context.error_line,
        )

        return FixResult(
            original_code=error_context.code,
            fixed_code=fixed_code,
            changes=changes,
            success=True,
            message=best_fix.description,
        )

    async def fix_async(
        self,
        error_context: ErrorContext,
        diagnosis: DiagnosisResult | None = None,
        **kwargs: Any,
    ) -> FixResult:
        """
        异步修复代码

        Args:
            error_context: 错误上下文
            diagnosis: 诊断结果（可选）
            **kwargs: 额外参数

        Returns:
            FixResult: 修复结果
        """
        # 如果没有提供诊断结果，先诊断
        if diagnosis is None:
            diagnosis = await self.diagnose_async(error_context, **kwargs)

        # 选择最佳修复建议
        best_fix = self._select_best_fix(diagnosis.fix_suggestions)

        if not best_fix:
            return FixResult(
                original_code=error_context.code,
                fixed_code=error_context.code,
                changes=[],
                success=False,
                message="无法生成修复建议",
            )

        # 应用修复
        fixed_code, changes = self._apply_fix(
            error_context.code,
            best_fix,
            error_context.error_line,
        )

        return FixResult(
            original_code=error_context.code,
            fixed_code=fixed_code,
            changes=changes,
            success=True,
            message=best_fix.description,
        )

    def _build_diagnosis_system_prompt(self) -> str:
        """构建诊断系统提示"""
        return '''你是一个 Minecraft 网易版 ModSDK 错误诊断专家。
你的任务是分析错误信息，找出根本原因，并提供修复建议。

## 分析维度
1. **错误类型**: 识别具体的错误类型
2. **根本原因**: 找出导致错误的根本原因
3. **影响范围**: 评估错误的影响程度
4. **修复方案**: 提供具体的修复建议

## 输出格式
请以 JSON 格式输出诊断结果：
```json
{
  "error_type": "错误类型",
  "root_cause": "根本原因分析",
  "impact": "high|medium|low",
  "fix_suggestions": [
    {
      "description": "修复描述",
      "confidence": "high|medium|low",
      "fix_code": "修复代码",
      "explanation": "修复说明"
    }
  ]
}
```

注意：
- 只输出 JSON，不要有其他内容
- confidence 表示修复置信度
- 提供 2-3 个修复建议'''

    def _build_diagnosis_prompt(self, context: ErrorContext) -> str:
        """构建诊断用户提示"""
        parts = ["请诊断以下错误:\n"]

        parts.append(f"错误类型: {context.error_type}")
        parts.append(f"错误信息: {context.error_message}")

        if context.file_path:
            parts.append(f"文件: {context.file_path}")
        if context.error_line:
            parts.append(f"行号: {context.error_line}")

        if context.code:
            parts.append(f"\n代码:\n```python\n{context.code}\n```")

        if context.stack_trace:
            parts.append(f"\n堆栈跟踪:\n```\n{context.stack_trace}\n```")

        return "\n".join(parts)

    def _parse_diagnosis_result(
        self,
        content: str,
        raw_result: CompletionResult,
    ) -> DiagnosisResult:
        """解析诊断结果"""
        import json

        # 尝试提取 JSON
        json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))

                fix_suggestions = []
                for item in data.get("fix_suggestions", []):
                    confidence_str = item.get("confidence", "medium").upper()
                    try:
                        confidence = FixConfidence[confidence_str]
                    except KeyError:
                        confidence = FixConfidence.MEDIUM

                    fix_suggestions.append(FixSuggestion(
                        description=item.get("description", ""),
                        confidence=confidence,
                        fix_code=item.get("fix_code", ""),
                        explanation=item.get("explanation", ""),
                    ))

                return DiagnosisResult(
                    error_type=data.get("error_type", ""),
                    root_cause=data.get("root_cause", ""),
                    impact=data.get("impact", "medium"),
                    fix_suggestions=fix_suggestions,
                    raw_result=raw_result,
                )
            except json.JSONDecodeError:
                pass

        # 解析失败，返回默认结果
        return DiagnosisResult(
            error_type="Unknown",
            root_cause="无法解析错误",
            impact="medium",
            fix_suggestions=[],
            raw_result=raw_result,
        )

    def _select_best_fix(self, suggestions: list[FixSuggestion]) -> FixSuggestion | None:
        """选择最佳修复建议"""
        if not suggestions:
            return None

        # 优先选择高置信度的修复
        for confidence in [FixConfidence.HIGH, FixConfidence.MEDIUM, FixConfidence.LOW]:
            for suggestion in suggestions:
                if suggestion.confidence == confidence and suggestion.fix_code:
                    return suggestion

        # 如果没有带代码的修复，返回第一个
        return suggestions[0] if suggestions else None

    def _apply_fix(
        self,
        code: str,
        fix: FixSuggestion,
        error_line: int | None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """应用修复"""
        lines = code.split("\n")
        changes = []

        if fix.fix_code and error_line and error_line > 0:
            # 替换错误行
            original_line = lines[error_line - 1] if error_line <= len(lines) else ""
            lines[error_line - 1] = fix.fix_code
            changes.append({
                "type": "replace",
                "line": error_line,
                "original": original_line,
                "replacement": fix.fix_code,
            })

        return "\n".join(lines), changes


def diagnose_error(
    error_context: ErrorContext,
    llm_config: LLMConfig | None = None,
) -> DiagnosisResult:
    """
    便捷函数：诊断错误

    Args:
        error_context: 错误上下文
        llm_config: LLM 配置

    Returns:
        DiagnosisResult: 诊断结果
    """
    fixer = IntelligentFixer(llm_config)
    return fixer.diagnose(error_context)


def fix_error(
    error_context: ErrorContext,
    llm_config: LLMConfig | None = None,
) -> FixResult:
    """
    便捷函数：修复错误

    Args:
        error_context: 错误上下文
        llm_config: LLM 配置

    Returns:
        FixResult: 修复结果
    """
    fixer = IntelligentFixer(llm_config)
    return fixer.fix(error_context)