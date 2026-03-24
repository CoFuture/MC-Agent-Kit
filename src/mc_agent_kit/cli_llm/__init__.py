"""LLM CLI integration module for MC-Agent-Kit.

This module provides CLI commands for LLM-powered features:
- mc-gen: Code generation, review, and fix commands
- mc-llm: Chat and query commands with LLM
"""

from .chat import (
    ChatSession,
    ChatSessionConfig,
    ChatMessage as SessionMessage,
    create_chat_session,
    chat_interactive,
)
from .commands import (
    diagnose_command,
    fix_command,
    generate_command,
    review_command,
)
from .config import (
    LLMCliConfig,
    LLMCliConfigManager,
    create_llm_cli_config,
    load_llm_cli_config,
)
from .output import (
    CodeFormatter,
    OutputFormat,
    StreamOutput,
    create_code_formatter,
    create_stream_output,
    format_code_result,
    format_review_result,
)

__all__ = [
    # Chat
    "ChatSession",
    "ChatSessionConfig",
    "SessionMessage",
    "create_chat_session",
    "chat_interactive",
    # Commands
    "generate_command",
    "review_command",
    "diagnose_command",
    "fix_command",
    # Config
    "LLMCliConfig",
    "LLMCliConfigManager",
    "create_llm_cli_config",
    "load_llm_cli_config",
    # Output
    "CodeFormatter",
    "OutputFormat",
    "StreamOutput",
    "create_code_formatter",
    "create_stream_output",
    "format_code_result",
    "format_review_result",
]