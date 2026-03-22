"""Backwards compatibility for completion module.

This module re-exports from contrib.completion for backwards compatibility.
"""

from mc_agent_kit.contrib.completion.best_practices import (
    BestPractice,
    BestPracticeChecker,
    BestPracticeResult,
    PracticeCategory,
    PracticeSeverity,
)
from mc_agent_kit.contrib.completion.completer import (
    CodeCompleter,
    Completion,
    CompletionContext,
    CompletionKind,
    CompletionResult,
)
from mc_agent_kit.contrib.completion.refactor import (
    RefactorEngine,
    RefactorSuggestion,
    RefactorType,
)
from mc_agent_kit.contrib.completion.smells import (
    CodeSmell,
    SmellCategory,
    SmellDetector,
    SmellDetectorConfig,
    SmellSeverity,
    SmellType,
)

__all__ = [
    "CodeCompleter",
    "Completion",
    "CompletionContext",
    "CompletionKind",
    "CompletionResult",
    "CodeSmell",
    "SmellCategory",
    "SmellDetector",
    "SmellDetectorConfig",
    "SmellSeverity",
    "SmellType",
    "RefactorEngine",
    "RefactorSuggestion",
    "RefactorType",
    "BestPractice",
    "BestPracticeChecker",
    "BestPracticeResult",
    "PracticeCategory",
    "PracticeSeverity",
]
