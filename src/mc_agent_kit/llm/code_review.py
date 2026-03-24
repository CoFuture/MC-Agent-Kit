"""
智能代码审查模块

基于 LLM 的智能代码审查功能。
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


class ReviewSeverity(Enum):
    """审查严重程度"""
    CRITICAL = "critical"  # 严重错误，必须修复
    ERROR = "error"        # 错误，应该修复
    WARNING = "warning"    # 警告，建议修复
    INFO = "info"          # 信息，可选修复
    HINT = "hint"          # 提示，仅供参考


class ReviewCategory(Enum):
    """审查类别"""
    SECURITY = "security"           # 安全问题
    PERFORMANCE = "performance"     # 性能问题
    MAINTAINABILITY = "maintainability"  # 可维护性
    STYLE = "style"                 # 代码风格
    MODSDK = "modsdk"               # ModSDK 特定问题
    LOGIC = "logic"                 # 逻辑错误
    SYNTAX = "syntax"               # 语法问题
    BEST_PRACTICE = "best_practice"  # 最佳实践


@dataclass
class ReviewIssue:
    """审查问题"""
    category: ReviewCategory
    severity: ReviewSeverity
    message: str
    line: int | None = None
    column: int | None = None
    code_snippet: str = ""
    suggestion: str = ""
    fix_code: str = ""
    related_docs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion,
            "fix_code": self.fix_code,
            "related_docs": self.related_docs,
        }


@dataclass
class ReviewResult:
    """审查结果"""
    issues: list[ReviewIssue]
    score: float
    grade: str  # A, B, C, D, F
    summary: str
    passed: bool
    category_scores: dict[str, float] = field(default_factory=dict)
    raw_result: CompletionResult | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "issues": [i.to_dict() for i in self.issues],
            "score": round(self.score, 2),
            "grade": self.grade,
            "summary": self.summary,
            "passed": self.passed,
            "category_scores": self.category_scores,
            "raw_result": self.raw_result.to_dict() if self.raw_result else None,
        }


class CodeReviewPromptBuilder:
    """
    代码审查提示构建器
    """

    @staticmethod
    def build_system_prompt() -> str:
        """构建系统提示"""
        return '''你是一个 Minecraft 网易版 ModSDK 代码审查专家。
你的任务是审查代码，发现潜在问题并提供改进建议。

## 审查维度
1. **安全性**: 检查潜在的安全漏洞和风险
2. **性能**: 检查性能瓶颈和优化机会
3. **可维护性**: 检查代码结构和可读性
4. **ModSDK 规范**: 检查 ModSDK 特定的最佳实践
5. **逻辑正确性**: 检查逻辑错误和边界情况

## 输出格式
请以 JSON 格式输出审查结果：
```json
{
  "issues": [
    {
      "category": "security|performance|maintainability|style|modsdk|logic|syntax|best_practice",
      "severity": "critical|error|warning|info|hint",
      "message": "问题描述",
      "line": 行号,
      "suggestion": "改进建议",
      "fix_code": "修复代码（可选）"
    }
  ],
  "score": 0-100,
  "summary": "审查总结"
}
```

注意：
- 只输出 JSON，不要有其他内容
- score 是整体评分，0-100
- summary 是简短的审查总结'''

    @staticmethod
    def build_prompt(code: str, file_path: str = "") -> str:
        """构建用户提示"""
        parts = [f"请审查以下代码:\n"]

        if file_path:
            parts.append(f"文件: {file_path}\n")

        parts.append(f"```python\n{code}\n```")
        return "\n".join(parts)


class IntelligentCodeReviewer:
    """
    智能代码审查器

    基于 LLM 审查代码质量。
    """

    def __init__(
        self,
        llm_config: LLMConfig | None = None,
    ) -> None:
        self.llm_config = llm_config or LLMConfig(provider="mock")
        self.llm_manager = LLMManager()
        self.prompt_builder = CodeReviewPromptBuilder()

    def review(
        self,
        code: str,
        file_path: str = "",
        **kwargs: Any,
    ) -> ReviewResult:
        """
        审查代码

        Args:
            code: 代码内容
            file_path: 文件路径
            **kwargs: 额外参数

        Returns:
            ReviewResult: 审查结果
        """
        # 先进行静态分析
        static_issues = self._static_analysis(code, file_path)

        # 构建 LLM 审查消息
        messages = [
            ChatMessage.system(self.prompt_builder.build_system_prompt()),
            ChatMessage.user(self.prompt_builder.build_prompt(code, file_path)),
        ]

        # 调用 LLM
        result = self.llm_manager.complete(messages, self.llm_config, **kwargs)

        # 解析 LLM 结果
        llm_issues = self._parse_llm_response(result.content)

        # 合并问题
        all_issues = static_issues + llm_issues

        # 计算分数
        score = self._calculate_score(all_issues)
        category_scores = self._calculate_category_scores(all_issues)

        # 生成等级
        grade = self._get_grade(score)

        # 判断是否通过
        passed = score >= 60 and not any(
            i.severity in (ReviewSeverity.CRITICAL, ReviewSeverity.ERROR)
            for i in all_issues
        )

        # 生成摘要
        summary = self._generate_summary(all_issues, score)

        return ReviewResult(
            issues=all_issues,
            score=score,
            grade=grade,
            summary=summary,
            passed=passed,
            category_scores=category_scores,
            raw_result=result,
        )

    async def review_async(
        self,
        code: str,
        file_path: str = "",
        **kwargs: Any,
    ) -> ReviewResult:
        """
        异步审查代码

        Args:
            code: 代码内容
            file_path: 文件路径
            **kwargs: 额外参数

        Returns:
            ReviewResult: 审查结果
        """
        # 先进行静态分析
        static_issues = self._static_analysis(code, file_path)

        # 构建 LLM 审查消息
        messages = [
            ChatMessage.system(self.prompt_builder.build_system_prompt()),
            ChatMessage.user(self.prompt_builder.build_prompt(code, file_path)),
        ]

        # 调用 LLM
        result = await self.llm_manager.complete_async(messages, self.llm_config, **kwargs)

        # 解析 LLM 结果
        llm_issues = self._parse_llm_response(result.content)

        # 合并问题
        all_issues = static_issues + llm_issues

        # 计算分数
        score = self._calculate_score(all_issues)
        category_scores = self._calculate_category_scores(all_issues)

        # 生成等级
        grade = self._get_grade(score)

        # 判断是否通过
        passed = score >= 60 and not any(
            i.severity in (ReviewSeverity.CRITICAL, ReviewSeverity.ERROR)
            for i in all_issues
        )

        # 生成摘要
        summary = self._generate_summary(all_issues, score)

        return ReviewResult(
            issues=all_issues,
            score=score,
            grade=grade,
            summary=summary,
            passed=passed,
            category_scores=category_scores,
            raw_result=result,
        )

    def _static_analysis(self, code: str, file_path: str) -> list[ReviewIssue]:
        """静态分析"""
        issues = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            # 检查安全问题
            if "eval(" in line or "exec(" in line:
                issues.append(ReviewIssue(
                    category=ReviewCategory.SECURITY,
                    severity=ReviewSeverity.ERROR,
                    message=f"使用危险的函数: {line.strip()}",
                    line=i,
                    suggestion="避免使用 eval/exec，考虑更安全的替代方案",
                ))

            if "password" in line.lower() or "secret" in line.lower():
                if "=" in line and not line.strip().startswith("#"):
                    issues.append(ReviewIssue(
                        category=ReviewCategory.SECURITY,
                        severity=ReviewSeverity.WARNING,
                        message="可能包含敏感信息",
                        line=i,
                        suggestion="不要在代码中硬编码敏感信息",
                    ))

            # 检查性能问题
            if re.search(r"for\s+\w+\s+in\s+range\(len\(", line):
                issues.append(ReviewIssue(
                    category=ReviewCategory.PERFORMANCE,
                    severity=ReviewSeverity.INFO,
                    message="使用 range(len()) 进行迭代",
                    line=i,
                    suggestion="考虑使用 enumerate() 或直接迭代",
                ))

            # 检查 ModSDK 特定问题
            if "mod.server" in line and "client" in file_path.lower():
                issues.append(ReviewIssue(
                    category=ReviewCategory.MODSDK,
                    severity=ReviewSeverity.ERROR,
                    message="客户端文件中使用了服务端 API",
                    line=i,
                    suggestion="请确认代码运行环境",
                ))

            if "mod.client" in line and "server" in file_path.lower():
                issues.append(ReviewIssue(
                    category=ReviewCategory.MODSDK,
                    severity=ReviewSeverity.ERROR,
                    message="服务端文件中使用了客户端 API",
                    line=i,
                    suggestion="请确认代码运行环境",
                ))

        return issues

    def _parse_llm_response(self, content: str) -> list[ReviewIssue]:
        """解析 LLM 响应"""
        issues = []

        # 尝试提取 JSON
        import json

        json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                for item in data.get("issues", []):
                    category_str = item.get("category", "best_practice").upper()
                    severity_str = item.get("severity", "info").upper()

                    try:
                        category = ReviewCategory[category_str]
                    except KeyError:
                        category = ReviewCategory.BEST_PRACTICE

                    try:
                        severity = ReviewSeverity[severity_str]
                    except KeyError:
                        severity = ReviewSeverity.INFO

                    issues.append(ReviewIssue(
                        category=category,
                        severity=severity,
                        message=item.get("message", ""),
                        line=item.get("line"),
                        suggestion=item.get("suggestion", ""),
                        fix_code=item.get("fix_code", ""),
                    ))
            except json.JSONDecodeError:
                pass

        return issues

    def _calculate_score(self, issues: list[ReviewIssue]) -> float:
        """计算分数"""
        if not issues:
            return 100.0

        penalties = {
            ReviewSeverity.CRITICAL: 30,
            ReviewSeverity.ERROR: 20,
            ReviewSeverity.WARNING: 10,
            ReviewSeverity.INFO: 2,
            ReviewSeverity.HINT: 1,
        }

        total_penalty = sum(penalties.get(i.severity, 1) for i in issues)
        return max(0, 100 - total_penalty)

    def _calculate_category_scores(self, issues: list[ReviewIssue]) -> dict[str, float]:
        """计算各分类分数"""
        category_issues: dict[ReviewCategory, list[ReviewIssue]] = {}
        for issue in issues:
            if issue.category not in category_issues:
                category_issues[issue.category] = []
            category_issues[issue.category].append(issue)

        scores = {}
        for category in ReviewCategory:
            cat_issues = category_issues.get(category, [])
            scores[category.value] = self._calculate_score(cat_issues)

        return scores

    def _get_grade(self, score: float) -> str:
        """获取等级"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _generate_summary(self, issues: list[ReviewIssue], score: float) -> str:
        """生成摘要"""
        if not issues:
            return "代码质量良好，未发现问题。"

        # 统计各类问题
        severity_counts: dict[ReviewSeverity, int] = {}
        for issue in issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1

        parts = [f"评分: {score:.0f}分"]

        if severity_counts.get(ReviewSeverity.CRITICAL, 0) > 0:
            parts.append(f"发现 {severity_counts[ReviewSeverity.CRITICAL]} 个严重问题")
        if severity_counts.get(ReviewSeverity.ERROR, 0) > 0:
            parts.append(f"发现 {severity_counts[ReviewSeverity.ERROR]} 个错误")
        if severity_counts.get(ReviewSeverity.WARNING, 0) > 0:
            parts.append(f"发现 {severity_counts[ReviewSeverity.WARNING]} 个警告")

        return "，".join(parts) + "。"


def review_code(
    code: str,
    file_path: str = "",
    llm_config: LLMConfig | None = None,
) -> ReviewResult:
    """
    便捷函数：审查代码

    Args:
        code: 代码内容
        file_path: 文件路径
        llm_config: LLM 配置

    Returns:
        ReviewResult: 审查结果
    """
    reviewer = IntelligentCodeReviewer(llm_config)
    return reviewer.review(code, file_path)