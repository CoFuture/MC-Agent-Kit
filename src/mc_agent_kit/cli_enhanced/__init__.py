"""CLI enhancement module for MC-Agent-Kit.

This module provides enhanced CLI features including:
- Interactive REPL mode
- Command history persistence
- Command aliases and shortcuts
- Colored output and progress bars
"""

from mc_agent_kit.cli_enhanced.repl import (
    CLIRepl,
    ReplConfig,
    ReplCommand,
    ReplResult,
    ReplState,
    create_repl,
)
from mc_agent_kit.cli_enhanced.history import (
    CommandHistory,
    HistoryEntry,
    HistoryConfig,
    create_history,
)
from mc_agent_kit.cli_enhanced.output import (
    ColoredOutput,
    OutputConfig,
    ProgressBar,
    ProgressConfig,
    Spinner,
    SpinnerConfig,
    Color,
    Style,
    create_output,
    create_progress_bar,
    create_spinner,
)
from mc_agent_kit.cli_enhanced.aliases import (
    CommandAlias,
    AliasManager,
    AliasConfig,
    create_alias_manager,
    get_builtin_aliases,
)

__all__ = [
    # REPL
    "CLIRepl",
    "ReplConfig",
    "ReplCommand",
    "ReplResult",
    "ReplState",
    "create_repl",
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