"""
代码补全与优化模块

提供 ModSDK 智能代码补全、代码异味检测、重构建议和最佳实践推荐功能。
"""

from .best_practices import (
    BestPractice,
    BestPracticeChecker,
    BestPracticeResult,
    PracticeCategory,
    PracticeSeverity,
)
from .completer import (
    CodeCompleter,
    Completion,
    CompletionContext,
    CompletionKind,
    CompletionResult,
)
from .refactor import RefactorEngine, RefactorSuggestion, RefactorType
from .smells import (
    CodeSmell,
    SmellCategory,
    SmellDetector,
    SmellSeverity,
    SmellType,
)

__all__ = [
    # 补全
    "CodeCompleter",
    "Completion",
    "CompletionContext",
    "CompletionKind",
    "CompletionResult",
    # 代码异味
    "CodeSmell",
    "SmellDetector",
    "SmellType",
    "SmellSeverity",
    "SmellCategory",
    # 重构
    "RefactorEngine",
    "RefactorSuggestion",
    "RefactorType",
    # 最佳实践
    "BestPracticeChecker",
    "BestPractice",
    "BestPracticeResult",
    "PracticeCategory",
    "PracticeSeverity",
]
