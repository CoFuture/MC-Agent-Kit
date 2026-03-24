"""Enhanced error messages and diagnostics for MC-Agent-Kit CLI.

This module provides:
- Detailed error messages
- Fix suggestions
- Documentation links
- Error categorization
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ErrorCategory(Enum):
    """Categories of errors."""
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    PERMISSION = "permission"
    RESOURCE = "resource"
    VALIDATION = "validation"
    DEPENDENCY = "dependency"
    USER_INPUT = "user_input"
    INTERNAL = "internal"
    MODSDK = "modsdk"


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"  # Cannot continue
    ERROR = "error"        # Operation failed
    WARNING = "warning"    # Non-critical issue
    INFO = "info"          # Informational


@dataclass
class FixSuggestion:
    """A suggestion for fixing an error."""
    description: str
    code_example: str = ""
    confidence: float = 0.0  # 0.0 to 1.0
    auto_fixable: bool = False
    doc_link: str = ""


@dataclass
class EnhancedError:
    """An enhanced error with details and suggestions."""
    error_type: str
    message: str
    category: ErrorCategory = ErrorCategory.INTERNAL
    severity: ErrorSeverity = ErrorSeverity.ERROR
    details: str = ""
    location: str = ""  # File:line or similar
    suggestions: list[FixSuggestion] = field(default_factory=list)
    related_docs: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "location": self.location,
            "suggestions": [
                {
                    "description": s.description,
                    "code_example": s.code_example,
                    "confidence": s.confidence,
                    "auto_fixable": s.auto_fixable,
                    "doc_link": s.doc_link,
                }
                for s in self.suggestions
            ],
            "related_docs": self.related_docs,
            "context": self.context,
        }

    def format(self, color: bool = True) -> str:
        """Format error for display.

        Args:
            color: Whether to use ANSI colors

        Returns:
            Formatted error string
        """
        lines = []

        # Severity indicator
        if color:
            colors = {
                ErrorSeverity.CRITICAL: "\033[91m",  # Red
                ErrorSeverity.ERROR: "\033[91m",     # Red
                ErrorSeverity.WARNING: "\033[93m",   # Yellow
                ErrorSeverity.INFO: "\033[94m",      # Blue
            }
            reset = "\033[0m"
            severity_color = colors.get(self.severity, "")
        else:
            severity_color = ""
            reset = ""

        icons = {
            ErrorSeverity.CRITICAL: "🔴",
            ErrorSeverity.ERROR: "❌",
            ErrorSeverity.WARNING: "⚠️",
            ErrorSeverity.INFO: "ℹ️",
        }

        icon = icons.get(self.severity, "❓")
        lines.append(f"{icon} {severity_color}{self.error_type}{reset}")
        lines.append(f"   {self.message}")
        lines.append("")

        # Location
        if self.location:
            lines.append(f"   📍 Location: {self.location}")
            lines.append("")

        # Details
        if self.details:
            lines.append("   Details:")
            for line in self.details.split("\n"):
                lines.append(f"      {line}")
            lines.append("")

        # Suggestions
        if self.suggestions:
            lines.append("   💡 Suggestions:")
            for i, s in enumerate(self.suggestions[:3], 1):
                lines.append(f"      {i}. {s.description}")
                if s.code_example:
                    lines.append(f"         Example: {s.code_example}")
                if s.doc_link:
                    lines.append(f"         Docs: {s.doc_link}")
            lines.append("")

        # Related docs
        if self.related_docs:
            lines.append("   📚 Related Documentation:")
            for doc in self.related_docs[:3]:
                lines.append(f"      - {doc}")
            lines.append("")

        return "\n".join(lines)


class ErrorEnhancer:
    """Enhances error messages with suggestions and context."""

    def __init__(self):
        """Initialize the error enhancer."""
        self._patterns: list[ErrorPattern] = []
        self._register_builtin_patterns()

    def _register_builtin_patterns(self) -> None:
        """Register built-in error patterns."""
        # Python errors
        self._patterns.extend([
            ErrorPattern(
                pattern=r"KeyError: ['\"](.+)['\"]",
                category=ErrorCategory.RUNTIME,
                severity=ErrorSeverity.ERROR,
                suggestions=[
                    FixSuggestion(
                        description="Check if the key exists before accessing",
                        code_example="if 'key' in dict: value = dict['key']",
                        confidence=0.8,
                    ),
                    FixSuggestion(
                        description="Use dict.get() with a default value",
                        code_example="value = dict.get('key', default_value)",
                        confidence=0.9,
                        auto_fixable=True,
                    ),
                ],
            ),
            ErrorPattern(
                pattern=r"AttributeError: '(\w+)' object has no attribute '(\w+)'",
                category=ErrorCategory.RUNTIME,
                severity=ErrorSeverity.ERROR,
                suggestions=[
                    FixSuggestion(
                        description="Check the object's available attributes",
                        code_example="print(dir(obj))  # List all attributes",
                        confidence=0.6,
                    ),
                    FixSuggestion(
                        description="Check if you need to call a method instead",
                        code_example="result = obj.method()  # Add parentheses",
                        confidence=0.7,
                    ),
                ],
            ),
            ErrorPattern(
                pattern=r"TypeError: '(\w+)' object is not (callable|subscriptable)",
                category=ErrorCategory.RUNTIME,
                severity=ErrorSeverity.ERROR,
                suggestions=[
                    FixSuggestion(
                        description="Check the type of your variable",
                        code_example="print(type(var))",
                        confidence=0.7,
                    ),
                ],
            ),
            ErrorPattern(
                pattern=r"IndentationError: (.+)",
                category=ErrorCategory.SYNTAX,
                severity=ErrorSeverity.ERROR,
                suggestions=[
                    FixSuggestion(
                        description="Fix indentation to match the surrounding code",
                        confidence=0.9,
                        auto_fixable=True,
                    ),
                ],
            ),
            ErrorPattern(
                pattern=r"SyntaxError: (.+)",
                category=ErrorCategory.SYNTAX,
                severity=ErrorSeverity.ERROR,
                suggestions=[
                    FixSuggestion(
                        description="Check for missing brackets, quotes, or colons",
                        confidence=0.8,
                    ),
                ],
            ),
            ErrorPattern(
                pattern=r"ImportError: No module named '(\w+)'",
                category=ErrorCategory.DEPENDENCY,
                severity=ErrorSeverity.ERROR,
                suggestions=[
                    FixSuggestion(
                        description="Install the missing module",
                        code_example="pip install <module_name>",
                        confidence=0.9,
                    ),
                ],
            ),
            # ModSDK specific errors
            ErrorPattern(
                pattern=r"KeyError: ['\"]speed['\"]",
                category=ErrorCategory.MODSDK,
                severity=ErrorSeverity.ERROR,
                suggestions=[
                    FixSuggestion(
                        description="Initialize 'speed' in entity configuration",
                        code_example="engineType = {'speed': 1.0, ...}",
                        confidence=0.9,
                        auto_fixable=True,
                    ),
                ],
                related_docs=[
                    "https://minecraft-zh.gamepedia.com/ModSDK开发指南",
                ],
            ),
            ErrorPattern(
                pattern=r"'NoneType' object has no attribute '(\w+)'",
                category=ErrorCategory.RUNTIME,
                severity=ErrorSeverity.ERROR,
                suggestions=[
                    FixSuggestion(
                        description="Check if the object was properly initialized",
                        code_example="if obj is not None: obj.method()",
                        confidence=0.8,
                    ),
                    FixSuggestion(
                        description="Add null check before accessing attributes",
                        code_example="result = obj.attr if obj else default",
                        confidence=0.9,
                    ),
                ],
            ),
            # Configuration errors
            ErrorPattern(
                pattern=r"FileNotFoundError: \[Errno .+\]: '(.+)'",
                category=ErrorCategory.RESOURCE,
                severity=ErrorSeverity.ERROR,
                suggestions=[
                    FixSuggestion(
                        description="Check if the file path is correct",
                        confidence=0.8,
                    ),
                    FixSuggestion(
                        description="Create the file if it doesn't exist",
                        confidence=0.6,
                    ),
                ],
            ),
            ErrorPattern(
                pattern=r"PermissionError: \[Errno .+\]: '(.+)'",
                category=ErrorCategory.PERMISSION,
                severity=ErrorSeverity.ERROR,
                suggestions=[
                    FixSuggestion(
                        description="Check file permissions",
                        code_example="# On Unix: chmod +rwx <file>",
                        confidence=0.8,
                    ),
                    FixSuggestion(
                        description="Run with appropriate permissions",
                        confidence=0.7,
                    ),
                ],
            ),
        ])

    def register_pattern(self, pattern: "ErrorPattern") -> None:
        """Register an error pattern.

        Args:
            pattern: ErrorPattern to register
        """
        self._patterns.append(pattern)

    def enhance(self, error: Exception, context: dict[str, Any] | None = None) -> EnhancedError:
        """Enhance an exception with suggestions.

        Args:
            error: The exception to enhance
            context: Additional context

        Returns:
            EnhancedError with suggestions
        """
        error_str = str(error)
        error_type = type(error).__name__

        # Default values
        enhanced = EnhancedError(
            error_type=error_type,
            message=error_str,
            context=context or {},
        )

        # Try to match patterns
        for ep in self._patterns:
            match = re.search(ep.pattern, error_str, re.IGNORECASE)
            if match:
                enhanced.category = ep.category
                enhanced.severity = ep.severity
                enhanced.suggestions = ep.suggestions.copy()
                enhanced.related_docs = ep.related_docs.copy()

                # Add context from match groups
                if match.groups():
                    enhanced.details = f"Matched: {match.group(0)}"

                break

        return enhanced

    def enhance_from_string(
        self, 
        error_str: str, 
        context: dict[str, Any] | None = None
    ) -> EnhancedError:
        """Enhance an error from string representation.

        Args:
            error_str: String representation of error
            context: Additional context

        Returns:
            EnhancedError with suggestions
        """
        # Try to parse error type and message
        match = re.match(r"(\w+Error|\w+Exception): (.+)", error_str)
        if match:
            error_type = match.group(1)
            message = match.group(2)
        else:
            error_type = "Error"
            message = error_str

        enhanced = EnhancedError(
            error_type=error_type,
            message=message,
            context=context or {},
        )

        # Try to match patterns
        for ep in self._patterns:
            match = re.search(ep.pattern, error_str, re.IGNORECASE)
            if match:
                enhanced.category = ep.category
                enhanced.severity = ep.severity
                enhanced.suggestions = ep.suggestions.copy()
                enhanced.related_docs = ep.related_docs.copy()
                break

        return enhanced


@dataclass
class ErrorPattern:
    """Pattern for matching and enhancing errors."""
    pattern: str
    category: ErrorCategory = ErrorCategory.INTERNAL
    severity: ErrorSeverity = ErrorSeverity.ERROR
    suggestions: list[FixSuggestion] = field(default_factory=list)
    related_docs: list[str] = field(default_factory=list)


def create_error_enhancer() -> ErrorEnhancer:
    """Create an error enhancer instance.

    Returns:
        Configured ErrorEnhancer
    """
    return ErrorEnhancer()


def format_error(error: Exception | str, context: dict[str, Any] | None = None) -> str:
    """Format an error with enhanced suggestions.

    Args:
        error: Exception or error string
        context: Additional context

    Returns:
        Formatted error string
    """
    enhancer = create_error_enhancer()
    
    if isinstance(error, Exception):
        enhanced = enhancer.enhance(error, context)
    else:
        enhanced = enhancer.enhance_from_string(error, context)
    
    return enhanced.format()


# Pre-defined error messages for common scenarios
ERROR_MESSAGES = {
    "config_not_found": EnhancedError(
        error_type="ConfigNotFoundError",
        message="Configuration file not found",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.ERROR,
        details="The specified configuration file does not exist.",
        suggestions=[
            FixSuggestion(
                description="Create a configuration file using the wizard",
                code_example="mc-agent wizard config",
                confidence=0.9,
            ),
            FixSuggestion(
                description="Specify the correct configuration path",
                code_example="mc-agent --config path/to/config.yaml",
                confidence=0.8,
            ),
        ],
    ),
    "invalid_addon_path": EnhancedError(
        error_type="InvalidAddonPathError",
        message="Invalid Addon path",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        details="The specified path is not a valid Addon directory.",
        suggestions=[
            FixSuggestion(
                description="Ensure the path contains a behavior_pack directory",
                confidence=0.9,
            ),
            FixSuggestion(
                description="Create a new Addon project",
                code_example="mc-agent create project my-addon",
                confidence=0.8,
            ),
        ],
    ),
    "game_not_found": EnhancedError(
        error_type="GameNotFoundError",
        message="Minecraft game not found",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        details="Could not locate the Minecraft executable.",
        suggestions=[
            FixSuggestion(
                description="Specify the game path explicitly",
                code_example="mc-agent run --game-path /path/to/game",
                confidence=0.9,
            ),
        ],
    ),
    "knowledge_base_empty": EnhancedError(
        error_type="KnowledgeBaseError",
        message="Knowledge base is empty or not indexed",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.WARNING,
        details="The knowledge base has not been built or is empty.",
        suggestions=[
            FixSuggestion(
                description="Build the knowledge base index",
                code_example="mc-agent kb build",
                confidence=0.9,
            ),
        ],
    ),
}


def get_error_message(key: str) -> EnhancedError | None:
    """Get a pre-defined error message.

    Args:
        key: Error message key

    Returns:
        EnhancedError or None if not found
    """
    return ERROR_MESSAGES.get(key)