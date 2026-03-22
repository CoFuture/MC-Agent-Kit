"""
用户体验优化模块

提供友好的 CLI 输出、错误消息增强和使用提示
"""

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
]