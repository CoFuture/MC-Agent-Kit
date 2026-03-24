"""Output formatting for LLM CLI commands.

Provides formatted output for code generation, review, and fix results.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from io import StringIO
from typing import Any, Iterator


class OutputFormat(Enum):
    """Output format types."""

    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    ANSI = "ansi"


@dataclass
class StreamChunk:
    """A chunk of streaming output."""

    content: str
    is_final: bool = False
    metadata: dict[str, Any] | None = None


class CodeFormatter:
    """Formatter for code output."""

    def __init__(
        self,
        format: OutputFormat = OutputFormat.TEXT,
        use_colors: bool = True,
    ):
        """Initialize formatter.

        Args:
            format: Output format
            use_colors: Whether to use ANSI colors
        """
        self.format = format
        self.use_colors = use_colors and sys.stdout.isatty()

    def format_code(
        self,
        code: str,
        language: str = "python",
        filename: str | None = None,
    ) -> str:
        """Format code for output.

        Args:
            code: Code content
            language: Programming language
            filename: Optional filename

        Returns:
            Formatted code
        """
        if self.format == OutputFormat.JSON:
            import json
            return json.dumps({
                "code": code,
                "language": language,
                "filename": filename,
            }, ensure_ascii=False)

        if self.format == OutputFormat.MARKDOWN:
            lines = []
            if filename:
                lines.append(f"### {filename}\n")
            lines.append(f"```{language}")
            lines.append(code)
            lines.append("```")
            return "\n".join(lines)

        # Text format with optional colors
        lines = []
        if filename:
            if self.use_colors:
                lines.append(self._color(f"📄 {filename}", "cyan", bold=True))
            else:
                lines.append(f"📄 {filename}")
            lines.append("")

        if self.use_colors:
            lines.append(self._color("Code:", "yellow"))
        else:
            lines.append("Code:")

        lines.append(code)
        return "\n".join(lines)

    def format_imports(self, imports: list[str]) -> str:
        """Format import statements.

        Args:
            imports: List of import statements

        Returns:
            Formatted imports
        """
        if not imports:
            return ""

        if self.format == OutputFormat.JSON:
            import json
            return json.dumps({"imports": imports}, ensure_ascii=False)

        lines = ["Required imports:"]
        for imp in imports:
            if self.use_colors:
                lines.append(f"  {self._color(imp, 'green')}")
            else:
                lines.append(f"  {imp}")
        return "\n".join(lines)

    def format_dependencies(self, dependencies: list[str]) -> str:
        """Format dependencies.

        Args:
            dependencies: List of dependencies

        Returns:
            Formatted dependencies
        """
        if not dependencies:
            return ""

        if self.format == OutputFormat.JSON:
            import json
            return json.dumps({"dependencies": dependencies}, ensure_ascii=False)

        lines = ["Dependencies:"]
        for dep in dependencies:
            if self.use_colors:
                lines.append(f"  • {self._color(dep, 'blue')}")
            else:
                lines.append(f"  • {dep}")
        return "\n".join(lines)

    def format_notes(self, notes: list[str]) -> str:
        """Format notes.

        Args:
            notes: List of notes

        Returns:
            Formatted notes
        """
        if not notes:
            return ""

        if self.format == OutputFormat.JSON:
            import json
            return json.dumps({"notes": notes}, ensure_ascii=False)

        lines = ["Notes:"]
        for note in notes:
            if self.use_colors:
                lines.append(f"  💡 {self._color(note, 'yellow')}")
            else:
                lines.append(f"  💡 {note}")
        return "\n".join(lines)

    def format_warnings(self, warnings: list[str]) -> str:
        """Format warnings.

        Args:
            warnings: List of warnings

        Returns:
            Formatted warnings
        """
        if not warnings:
            return ""

        if self.format == OutputFormat.JSON:
            import json
            return json.dumps({"warnings": warnings}, ensure_ascii=False)

        lines = ["Warnings:"]
        for warning in warnings:
            if self.use_colors:
                lines.append(f"  ⚠️  {self._color(warning, 'yellow')}")
            else:
                lines.append(f"  ⚠️  {warning}")
        return "\n".join(lines)

    def _color(
        self,
        text: str,
        color: str,
        bold: bool = False,
    ) -> str:
        """Apply ANSI color to text.

        Args:
            text: Text to color
            color: Color name
            bold: Whether to make bold

        Returns:
            Colored text
        """
        if not self.use_colors:
            return text

        colors = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "cyan": "\033[96m",
            "white": "\033[97m",
        }
        reset = "\033[0m"
        bold_code = "\033[1m" if bold else ""

        color_code = colors.get(color, "")
        return f"{bold_code}{color_code}{text}{reset}"


class StreamOutput:
    """Handler for streaming output."""

    def __init__(
        self,
        file: Any = None,
        use_colors: bool = True,
        prefix: str = "",
    ):
        """Initialize stream output.

        Args:
            file: Output file (default: stdout)
            use_colors: Whether to use colors
            prefix: Prefix for each line
        """
        self.file = file or sys.stdout
        self.use_colors = use_colors and hasattr(self.file, "isatty") and self.file.isatty()
        self.prefix = prefix
        self._buffer = StringIO()
        self._last_line_len = 0

    def write(self, chunk: StreamChunk) -> None:
        """Write a chunk to output.

        Args:
            chunk: Stream chunk
        """
        content = chunk.content

        if self.prefix:
            # Add prefix to each line
            lines = content.split("\n")
            content = "\n".join(f"{self.prefix}{line}" for line in lines)

        self._buffer.write(content)
        self.file.write(content)
        self.file.flush()

    def write_line(self, text: str = "") -> None:
        """Write a line.

        Args:
            text: Line content
        """
        self.write(StreamChunk(f"{text}\n"))

    def write_styled(
        self,
        text: str,
        color: str = "white",
        bold: bool = False,
    ) -> None:
        """Write styled text.

        Args:
            text: Text to write
            color: Color name
            bold: Whether bold
        """
        if self.use_colors:
            text = self._color(text, color, bold)
        self.write(StreamChunk(text))

    def clear_line(self) -> None:
        """Clear current line."""
        if self.use_colors:
            self.file.write("\r\033[K")
            self.file.flush()

    def update_line(self, text: str) -> None:
        """Update current line (overwrite).

        Args:
            text: New line content
        """
        self.clear_line()
        self.file.write(text)
        self.file.flush()
        self._last_line_len = len(text)

    def get_buffer(self) -> str:
        """Get accumulated buffer content.

        Returns:
            Buffer content
        """
        return self._buffer.getvalue()

    def reset_buffer(self) -> None:
        """Reset the buffer."""
        self._buffer = StringIO()

    def _color(
        self,
        text: str,
        color: str,
        bold: bool = False,
    ) -> str:
        """Apply ANSI color."""
        colors = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "cyan": "\033[96m",
            "white": "\033[97m",
        }
        reset = "\033[0m"
        bold_code = "\033[1m" if bold else ""

        color_code = colors.get(color, "")
        return f"{bold_code}{color_code}{text}{reset}"


def format_code_result(
    result: dict[str, Any],
    format: OutputFormat = OutputFormat.TEXT,
    use_colors: bool = True,
) -> str:
    """Format code generation result.

    Args:
        result: Generation result
        format: Output format
        use_colors: Whether to use colors

    Returns:
        Formatted result
    """
    formatter = CodeFormatter(format, use_colors)

    if format == OutputFormat.JSON:
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)

    lines = []

    # Title
    if result.get("success"):
        title = "✅ Code Generated Successfully"
    else:
        title = "❌ Code Generation Failed"
    lines.append(title)
    lines.append("")

    # Code
    if code := result.get("code"):
        lines.append(formatter.format_code(code))

    # Imports
    if imports := result.get("imports"):
        lines.append("")
        lines.append(formatter.format_imports(imports))

    # Dependencies
    if dependencies := result.get("dependencies"):
        lines.append("")
        lines.append(formatter.format_dependencies(dependencies))

    # Notes
    if notes := result.get("notes"):
        lines.append("")
        lines.append(formatter.format_notes(notes))

    # Warnings
    if warnings := result.get("warnings"):
        lines.append("")
        lines.append(formatter.format_warnings(warnings))

    # Confidence
    if confidence := result.get("confidence"):
        lines.append("")
        lines.append(f"Confidence: {confidence}")

    return "\n".join(lines)


def format_review_result(
    result: dict[str, Any],
    format: OutputFormat = OutputFormat.TEXT,
    use_colors: bool = True,
) -> str:
    """Format code review result.

    Args:
        result: Review result
        format: Output format
        use_colors: Whether to use colors

    Returns:
        Formatted result
    """
    formatter = CodeFormatter(format, use_colors)

    if format == OutputFormat.JSON:
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)

    lines = []

    # Summary
    score = result.get("score", 0)
    grade = result.get("grade", "F")
    passed = result.get("passed", False)

    if passed:
        lines.append(f"✅ Code Review Passed (Score: {score}, Grade: {grade})")
    else:
        lines.append(f"❌ Code Review Failed (Score: {score}, Grade: {grade})")

    lines.append("")

    # Issues
    issues = result.get("issues", [])
    if issues:
        lines.append(f"Issues ({len(issues)}):")
        lines.append("")

        for issue in issues:
            severity = issue.get("severity", "info")
            category = issue.get("category", "unknown")
            message = issue.get("message", "")
            line_num = issue.get("line")
            suggestion = issue.get("suggestion")

            # Severity icon
            icon = {
                "critical": "🔴",
                "error": "❌",
                "warning": "⚠️",
                "info": "ℹ️",
                "hint": "💡",
            }.get(severity, "📝")

            lines.append(f"  {icon} [{category}] {message}")
            if line_num:
                lines.append(f"     Line: {line_num}")
            if suggestion:
                lines.append(f"     Suggestion: {suggestion}")
            lines.append("")

    # Summary text
    if summary := result.get("summary"):
        lines.append("Summary:")
        lines.append(f"  {summary}")

    return "\n".join(lines)


def create_code_formatter(
    format: OutputFormat = OutputFormat.TEXT,
    use_colors: bool = True,
) -> CodeFormatter:
    """Create a code formatter.

    Args:
        format: Output format
        use_colors: Whether to use colors

    Returns:
        CodeFormatter instance
    """
    return CodeFormatter(format, use_colors)


def create_stream_output(
    file: Any = None,
    use_colors: bool = True,
    prefix: str = "",
) -> StreamOutput:
    """Create a stream output handler.

    Args:
        file: Output file
        use_colors: Whether to use colors
        prefix: Line prefix

    Returns:
        StreamOutput instance
    """
    return StreamOutput(file, use_colors, prefix)