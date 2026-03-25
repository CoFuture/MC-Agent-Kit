"""CLI enhancement module for MC-Agent-Kit.

This module provides enhanced CLI features including:
- Interactive REPL mode
- Command history persistence
- Command aliases and shortcuts
- Colored output and progress bars
- Command completion
- Enhanced error messages
"""

from mc_agent_kit.cli_enhanced.aliases import (
    AliasConfig,
    AliasManager,
    CommandAlias,
    create_alias_manager,
    get_builtin_aliases,
)
from mc_agent_kit.cli_enhanced.completion import (
    CompletionContext,
    CompletionItem,
    CompletionType,
    Completer,
    CommandCompleter,
    FilePathCompleter,
    ApiNameCompleter,
    EventNameCompleter,
    CompositeCompleter,
    ArgumentCompleter,
    parse_completion_context,
    create_default_completer,
    format_completions,
)
from mc_agent_kit.cli_enhanced.errors import (
    ErrorCategory,
    ErrorSeverity,
    FixSuggestion,
    EnhancedError,
    ErrorEnhancer,
    ErrorPattern,
    create_error_enhancer,
    format_error,
    get_error_message,
)
from mc_agent_kit.cli_enhanced.history import (
    CommandHistory,
    HistoryConfig,
    HistoryEntry,
    create_history,
)
from mc_agent_kit.cli_enhanced.output import (
    Color,
    ColoredOutput,
    OutputConfig,
    ProgressBar,
    ProgressConfig,
    Spinner,
    SpinnerConfig,
    Style,
    create_output,
    create_progress_bar,
    create_spinner,
)
from mc_agent_kit.cli_enhanced.repl import (
    CLIRepl,
    ReplCommand,
    ReplConfig,
    ReplResult,
    ReplState,
    create_repl,
)
from mc_agent_kit.cli_enhanced.enhanced_repl import (
    CommandHistory as NewCommandHistory,
    CompletionSuggestion,
    EnhancedCompleter,
    EnhancedReplSession,
    OutputBuilder,
    OutputFormat,
    ProgressBar as NewProgressBar,
    ProgressState,
    Spinner as NewSpinner,
    SyntaxHighlighter,
    SyntaxToken,
    create_enhanced_repl,
    run_interactive,
)

__all__ = [
    # Completion
    "CompletionContext",
    "CompletionItem",
    "CompletionType",
    "Completer",
    "CommandCompleter",
    "FilePathCompleter",
    "ApiNameCompleter",
    "EventNameCompleter",
    "CompositeCompleter",
    "ArgumentCompleter",
    "parse_completion_context",
    "create_default_completer",
    "format_completions",
    # Error enhancement
    "ErrorCategory",
    "ErrorSeverity",
    "FixSuggestion",
    "EnhancedError",
    "ErrorEnhancer",
    "ErrorPattern",
    "create_error_enhancer",
    "format_error",
    "get_error_message",
    # REPL (legacy)
    "CLIRepl",
    "ReplConfig",
    "ReplCommand",
    "ReplResult",
    "ReplState",
    "create_repl",
    # Enhanced REPL
    "EnhancedReplSession",
    "EnhancedCompleter",
    "OutputBuilder",
    "OutputFormat",
    "CompletionSuggestion",
    "SyntaxHighlighter",
    "SyntaxToken",
    "NewCommandHistory",
    "NewProgressBar",
    "NewSpinner",
    "ProgressState",
    "create_enhanced_repl",
    "run_interactive",
    # History
    "CommandHistory",
    "HistoryEntry",
    "HistoryConfig",
    "create_history",
    # Output
    "ColoredOutput",
    "OutputConfig",
    "ProgressBar",
    "ProgressConfig",
    "Spinner",
    "SpinnerConfig",
    "Color",
    "Style",
    "create_output",
    "create_progress_bar",
    "create_spinner",
    # Aliases
    "CommandAlias",
    "AliasManager",
    "AliasConfig",
    "create_alias_manager",
    "get_builtin_aliases",
]
