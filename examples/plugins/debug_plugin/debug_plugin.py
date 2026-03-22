"""Debug assistant plugin for MC-Agent-Kit.

This plugin demonstrates how to create a plugin that helps
with debugging code and analyzing errors.

Features:
- Analyze error messages and provide suggestions
- Detect common code issues
- Provide debugging tips
- Generate fix suggestions
"""

import ast
import logging
import re
import traceback
from dataclasses import dataclass
from typing import Any

from mc_agent_kit.plugin import PluginBase, PluginResult

logger = logging.getLogger(__name__)


@dataclass
class ErrorPattern:
    """Error pattern definition."""

    pattern: str
    error_type: str
    description: str
    suggestions: list[str]
    fix_example: str | None = None


# Common error patterns
ERROR_PATTERNS = [
    ErrorPattern(
        pattern=r"NameError: name '(\w+)' is not defined",
        error_type="NameError",
        description="Variable or function is not defined",
        suggestions=[
            "Check if the variable is defined before use",
            "Check for typos in variable name",
            "Import required modules",
        ],
        fix_example="# Define the variable before use\n{var} = value",
    ),
    ErrorPattern(
        pattern=r"TypeError: (\w+\(\).*?) argument",
        error_type="TypeError",
        description="Incorrect argument type passed to function",
        suggestions=[
            "Check the function signature",
            "Verify argument types match expected types",
            "Add type checking if needed",
        ],
    ),
    ErrorPattern(
        pattern=r"KeyError: '(\w+)'",
        error_type="KeyError",
        description="Key not found in dictionary",
        suggestions=[
            "Check if the key exists before access",
            "Use .get() method with default value",
            "Verify the dictionary contents",
        ],
        fix_example="# Use .get() with default\nvalue = my_dict.get('{key}', default_value)",
    ),
    ErrorPattern(
        pattern=r"IndexError: list index out of range",
        error_type="IndexError",
        description="List index is out of valid range",
        suggestions=[
            "Check list length before accessing",
            "Use negative indexing for last element",
            "Add bounds checking",
        ],
        fix_example="# Check length before access\nif index < len(my_list):\n    value = my_list[index]",
    ),
    ErrorPattern(
        pattern=r"AttributeError: '(\w+)' object has no attribute '(\w+)'",
        error_type="AttributeError",
        description="Object does not have the requested attribute",
        suggestions=[
            "Check object type",
            "Verify attribute name spelling",
            "Use hasattr() to check existence",
        ],
        fix_example="# Check attribute exists\nif hasattr(obj, '{attr}'):\n    value = obj.{attr}",
    ),
    ErrorPattern(
        pattern=r"ValueError: (.+)",
        error_type="ValueError",
        description="Invalid value provided",
        suggestions=[
            "Validate input values",
            "Check value constraints",
            "Add input validation",
        ],
    ),
    ErrorPattern(
        pattern=r"IndentationError: (.+)",
        error_type="IndentationError",
        description="Incorrect indentation in code",
        suggestions=[
            "Check indentation consistency (spaces vs tabs)",
            "Verify code block indentation",
            "Use consistent indentation (4 spaces recommended)",
        ],
    ),
    ErrorPattern(
        pattern=r"SyntaxError: (.+)",
        error_type="SyntaxError",
        description="Syntax error in code",
        suggestions=[
            "Check for missing parentheses/brackets",
            "Verify string quotes are matched",
            "Check for missing colons after if/for/while/def",
        ],
    ),
    ErrorPattern(
        pattern=r"ImportError: (.+)",
        error_type="ImportError",
        description="Failed to import module",
        suggestions=[
            "Verify module is installed",
            "Check module name spelling",
            "Install missing package: pip install <package>",
        ],
    ),
    ErrorPattern(
        pattern=r"ZeroDivisionError",
        error_type="ZeroDivisionError",
        description="Division by zero",
        suggestions=[
            "Check divisor before division",
            "Add zero check",
            "Use try-except for error handling",
        ],
        fix_example="# Check before division\nif divisor != 0:\n    result = numerator / divisor",
    ),
]


@dataclass
class CodeIssue:
    """Code issue detected."""

    line: int
    issue_type: str
    description: str
    severity: str  # "error", "warning", "info"
    suggestion: str | None = None


class DebugPlugin(PluginBase):
    """Debug assistant plugin.

    Provides debugging capabilities including error analysis
    and code issue detection.

    Example:
        >>> plugin = DebugPlugin()
        >>> result = plugin.execute("analyze_error", error="NameError: name 'x' is not defined")
        >>> print(result.data["suggestions"])
    """

    def __init__(self) -> None:
        """Initialize debug plugin."""
        self._max_suggestions = 5
        self._include_code_examples = True

    def set_config(self, config: dict[str, Any]) -> None:
        """Set plugin configuration.

        Args:
            config: Configuration dictionary
        """
        self._max_suggestions = config.get("max_suggestions", self._max_suggestions)
        self._include_code_examples = config.get(
            "include_code_examples", self._include_code_examples
        )

    def on_load(self) -> None:
        """Called when plugin is loaded."""
        logger.info("Debug plugin loaded")

    def on_enable(self) -> None:
        """Called when plugin is enabled."""
        logger.info("Debug plugin enabled")

    def on_disable(self) -> None:
        """Called when plugin is disabled."""
        logger.info("Debug plugin disabled")

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        logger.info("Debug plugin unloaded")

    def execute(self, action: str = "analyze_error", **kwargs: Any) -> PluginResult:
        """Execute plugin action.

        Args:
            action: Action to perform:
                - "analyze_error": Analyze an error message
                - "analyze_code": Analyze code for issues
                - "format_traceback": Format a traceback
                - "list_patterns": List known error patterns
                - "help": Get help information
            **kwargs: Action-specific arguments

        Returns:
            PluginResult with analysis results
        """
        try:
            if action == "analyze_error":
                return self._analyze_error(kwargs)
            elif action == "analyze_code":
                return self._analyze_code(kwargs)
            elif action == "format_traceback":
                return self._format_traceback(kwargs)
            elif action == "list_patterns":
                return self._list_patterns()
            elif action == "help":
                return self._get_help()
            else:
                return PluginResult(
                    success=False,
                    error=f"Unknown action: {action}",
                )
        except Exception as e:
            logger.error("Error executing debug action: %s", e)
            return PluginResult(success=False, error=str(e))

    def _analyze_error(self, kwargs: dict[str, Any]) -> PluginResult:
        """Analyze an error message.

        Args:
            kwargs: Arguments including 'error' (error message)

        Returns:
            PluginResult with analysis
        """
        error_msg = kwargs.get("error")
        if not error_msg:
            return PluginResult(
                success=False,
                error="Error message is required",
            )

        # Find matching pattern
        for pattern in ERROR_PATTERNS:
            match = re.search(pattern.pattern, error_msg)
            if match:
                groups = match.groups()

                # Format suggestions
                suggestions = pattern.suggestions[: self._max_suggestions]

                # Format fix example
                fix_example = None
                if self._include_code_examples and pattern.fix_example:
                    fix_example = pattern.fix_example
                    # Replace placeholders with captured groups
                    if groups:
                        for i, group in enumerate(groups):
                            fix_example = fix_example.replace(
                                f"{{{'var' if i == 0 else 'key' if 'key' in pattern.pattern else 'attr' if 'attr' in pattern.pattern else i}}}",
                                group,
                            )

                return PluginResult(
                    success=True,
                    data={
                        "error_type": pattern.error_type,
                        "description": pattern.description,
                        "suggestions": suggestions,
                        "fix_example": fix_example,
                        "matched": True,
                    },
                )

        # No pattern matched
        return PluginResult(
            success=True,
            data={
                "error_type": "Unknown",
                "description": "Unrecognized error pattern",
                "suggestions": [
                    "Check the full error message",
                    "Search for similar errors online",
                    "Add debug prints to locate the issue",
                ],
                "matched": False,
            },
        )

    def _analyze_code(self, kwargs: dict[str, Any]) -> PluginResult:
        """Analyze code for issues.

        Args:
            kwargs: Arguments including 'code' (source code)

        Returns:
            PluginResult with detected issues
        """
        code = kwargs.get("code")
        if not code:
            return PluginResult(
                success=False,
                error="Code is required",
            )

        issues: list[CodeIssue] = []

        # Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            issues.append(
                CodeIssue(
                    line=e.lineno or 1,
                    issue_type="SyntaxError",
                    description=str(e.msg),
                    severity="error",
                )
            )
            return PluginResult(
                success=True,
                data={
                    "issues": [
                        {
                            "line": i.line,
                            "type": i.issue_type,
                            "description": i.description,
                            "severity": i.severity,
                            "suggestion": i.suggestion,
                        }
                        for i in issues
                    ],
                    "total": len(issues),
                },
            )

        # Check for common issues
        for node in ast.walk(tree):
            # Check for bare except
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append(
                    CodeIssue(
                        line=node.lineno,
                        issue_type="BareExcept",
                        description="Bare 'except:' catches all exceptions including KeyboardInterrupt",
                        severity="warning",
                        suggestion="Use 'except Exception:' instead",
                    )
                )

            # Check for pass in finally
            if isinstance(node, ast.Try):
                for handler in node.finalbody:
                    if isinstance(handler, ast.Pass):
                        issues.append(
                            CodeIssue(
                                line=handler.lineno,
                                issue_type="EmptyFinally",
                                description="Empty finally block",
                                severity="info",
                            )
                        )

            # Check for == True/False
            if isinstance(node, ast.Compare):
                for comparator in node.comparators:
                    if isinstance(comparator, ast.Constant):
                        if comparator.value in (True, False):
                            issues.append(
                                CodeIssue(
                                    line=node.lineno,
                                    issue_type="BooleanComparison",
                                    description=f"Comparison with {comparator.value} is unnecessary",
                                    severity="info",
                                    suggestion="Remove the comparison, the value is already boolean",
                                )
                            )

            # Check for print statements (potential debug code)
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "print":
                    issues.append(
                        CodeIssue(
                            line=node.lineno,
                            issue_type="PrintStatement",
                            description="Print statement found (potential debug code)",
                            severity="info",
                            suggestion="Consider using logging instead",
                        )
                    )

        return PluginResult(
            success=True,
            data={
                "issues": [
                    {
                        "line": i.line,
                        "type": i.issue_type,
                        "description": i.description,
                        "severity": i.severity,
                        "suggestion": i.suggestion,
                    }
                    for i in issues
                ],
                "total": len(issues),
            },
        )

    def _format_traceback(self, kwargs: dict[str, Any]) -> PluginResult:
        """Format a traceback.

        Args:
            kwargs: Arguments including 'traceback' or 'exception'

        Returns:
            PluginResult with formatted traceback
        """
        tb_str = kwargs.get("traceback")
        exc = kwargs.get("exception")

        if exc:
            # Format exception object
            tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        elif not tb_str:
            return PluginResult(
                success=False,
                error="Traceback or exception is required",
            )

        # Parse traceback
        lines = tb_str.strip().split("\n")
        formatted_lines = []

        for line in lines:
            # Highlight file paths
            file_match = re.match(r'\s*File "(.+)", line (\d+)', line)
            if file_match:
                formatted_lines.append(
                    {
                        "type": "file",
                        "file": file_match.group(1),
                        "line": int(file_match.group(2)),
                    }
                )
            elif line.strip().startswith("raise"):
                formatted_lines.append({"type": "raise", "content": line.strip()})
            elif "Error" in line or "Exception" in line:
                formatted_lines.append({"type": "error", "content": line.strip()})

        return PluginResult(
            success=True,
            data={
                "raw": tb_str,
                "parsed": formatted_lines,
                "line_count": len(lines),
            },
        )

    def _list_patterns(self) -> PluginResult:
        """List known error patterns.

        Returns:
            PluginResult with pattern list
        """
        patterns = [
            {
                "error_type": p.error_type,
                "description": p.description,
                "suggestions": p.suggestions,
            }
            for p in ERROR_PATTERNS
        ]

        return PluginResult(
            success=True,
            data={
                "patterns": patterns,
                "total": len(patterns),
            },
        )

    def _get_help(self) -> PluginResult:
        """Get help information.

        Returns:
            PluginResult with help text
        """
        return PluginResult(
            success=True,
            data={
                "description": "Debug assistant plugin for MC-Agent-Kit",
                "actions": [
                    {
                        "name": "analyze_error",
                        "description": "Analyze an error message and provide suggestions",
                        "params": {
                            "error": "Error message (required)",
                        },
                    },
                    {
                        "name": "analyze_code",
                        "description": "Analyze code for common issues",
                        "params": {
                            "code": "Source code to analyze (required)",
                        },
                    },
                    {
                        "name": "format_traceback",
                        "description": "Format and parse a traceback",
                        "params": {
                            "traceback": "Traceback string (optional)",
                            "exception": "Exception object (optional)",
                        },
                    },
                    {
                        "name": "list_patterns",
                        "description": "List known error patterns",
                        "params": {},
                    },
                    {
                        "name": "help",
                        "description": "Show this help",
                        "params": {},
                    },
                ],
                "config": {
                    "max_suggestions": "Maximum suggestions to return (default: 5)",
                    "include_code_examples": "Include code fix examples (default: true)",
                },
            },
        )


# Plugin entry point
def create_plugin() -> DebugPlugin:
    """Create plugin instance.

    Returns:
        DebugPlugin instance
    """
    return DebugPlugin()