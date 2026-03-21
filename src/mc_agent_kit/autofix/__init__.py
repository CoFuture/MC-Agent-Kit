"""
自动修复模块

提供错误诊断和自动修复功能。
"""

from .diagnoser import (
    DiagnosisResult,
    ErrorDiagnoser,
    ErrorInfo,
    ErrorType,
    FixSuggestion,
)
from .fixer import (
    AutoFixer,
    FixContext,
    FixResult,
    FixStatus,
    Replacement,
)

__all__ = [
    # Diagnoser
    "DiagnosisResult",
    "ErrorDiagnoser",
    "ErrorInfo",
    "ErrorType",
    "FixSuggestion",
    # Fixer
    "AutoFixer",
    "FixContext",
    "FixResult",
    "FixStatus",
    "Replacement",
]
