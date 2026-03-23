"""
用户体验优化模块

提供友好的 CLI 输出、错误消息增强和使用提示
"""

from .enhanced import (
    EnhancedUXManager,
    LocaleConfig,
    LocaleManager,
    MessageHistory,
    MessageHistoryEntry,
    MessageTemplate,
    TemplateRegistry,
    get_ux_manager,
    localized_message,
)
from .enhancer import (
    CLIOutputFormatter,
    MessageType,
    OutputFormat,
    UserExperienceEnhancer,
    UserMessage,
    UserMessageBuilder,
    error,
    hint,
    info,
    success,
    warning,
)
from .rich_output import (
    OutputTheme,
    ProgressInfo,
    RichOutputConfig,
    RichOutputManager,
    create_rich_output,
    get_rich_output,
)

__all__ = [
    # Base enhancer
    "MessageType",
    "OutputFormat",
    "UserMessage",
    "UserMessageBuilder",
    "UserExperienceEnhancer",
    "CLIOutputFormatter",
    "success",
    "error",
    "warning",
    "info",
    "hint",
    # Enhanced UX
    "EnhancedUXManager",
    "LocaleConfig",
    "LocaleManager",
    "MessageHistory",
    "MessageHistoryEntry",
    "MessageTemplate",
    "TemplateRegistry",
    "get_ux_manager",
    "localized_message",
    # Rich output
    "OutputTheme",
    "ProgressInfo",
    "RichOutputConfig",
    "RichOutputManager",
    "create_rich_output",
    "get_rich_output",
]
