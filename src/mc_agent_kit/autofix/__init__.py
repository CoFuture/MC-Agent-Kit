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
    AutoFixer as LegacyAutoFixer,
    FixContext,
    FixResult,
    FixStatus,
    Replacement,
)
from .auto_fixer import (
    AutoFixer,
    AppliedFix,
    ErrorCorrelation,
    ErrorLocation,
    ErrorRelation,
    FixPriority,
    FixReport,
    FixStatus as NewFixStatus,
    FixTemplate,
    RootCause,
    auto_fix_error,
    create_auto_fixer,
    diagnose_error,
)
from .log_analyzer import (
    EnhancedLogAnalyzer,
    LogAnalysisResult,
    LogEntry,
    LogEntryType,
    LogLevel,
    PerformanceIssue,
    PerformanceIssueType,
    analyze_log,
    analyze_log_file,
    create_log_analyzer,
)

__all__ = [
    # Diagnoser (legacy)
    "DiagnosisResult",
    "ErrorDiagnoser",
    "ErrorInfo",
    "ErrorType",
    "FixSuggestion",
    # Fixer (legacy)
    "LegacyAutoFixer",
    "FixContext",
    "FixResult",
    "FixStatus",
    "Replacement",
    # Auto Fixer (enhanced)
    "AutoFixer",
    "AppliedFix",
    "ErrorCorrelation",
    "ErrorLocation",
    "ErrorRelation",
    "FixPriority",
    "FixReport",
    "NewFixStatus",
    "FixTemplate",
    "RootCause",
    "auto_fix_error",
    "create_auto_fixer",
    "diagnose_error",
    # Log Analyzer
    "EnhancedLogAnalyzer",
    "LogAnalysisResult",
    "LogEntry",
    "LogEntryType",
    "LogLevel",
    "PerformanceIssue",
    "PerformanceIssueType",
    "analyze_log",
    "analyze_log_file",
    "create_log_analyzer",
]
