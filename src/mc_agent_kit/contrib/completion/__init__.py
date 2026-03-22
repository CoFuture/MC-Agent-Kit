"""Code completion module for MC-Agent-Kit.

This module provides code completion, smell detection, and refactoring tools.
"""

from mc_agent_kit.contrib.completion.completer import (
    CodeCompleter,
    Completion,
    CompletionContext,
    CompletionKind,
    CompletionResult,
)
from mc_agent_kit.contrib.completion.smells import (
    CodeSmell,
    SmellCategory,
    SmellDetector,
    SmellDetectorConfig,
    SmellSeverity,
    SmellType,
)
from mc_agent_kit.contrib.completion.refactor import (
    RefactorEngine,
    RefactorSuggestion,
    RefactorType,
)
from mc_agent_kit.contrib.completion.best_practices import (
    BestPractice,
    BestPracticeChecker,
    BestPracticeResult,
    PracticeCategory,
    PracticeSeverity,
)

__all__ = [
    # Completer
    "CodeCompleter",
    "Completion",
    "CompletionContext",
    "CompletionKind",
    "CompletionResult",
    # Smells
    "CodeSmell",
    "SmellCategory",
    "SmellDetector",
    "SmellDetectorConfig",
    "SmellSeverity",
    "SmellType",
    # Refactor
    "RefactorEngine",
    "RefactorSuggestion",
    "RefactorType",
    # Best Practices
    "BestPractice",
    "BestPracticeChecker",
    "BestPracticeResult",
    "PracticeCategory",
    "PracticeSeverity",
]