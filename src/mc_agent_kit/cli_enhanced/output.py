"""Colored output and progress indicators for MC-Agent-Kit CLI.

This module provides:
- Colored text output
- Progress bars
- Spinners
- Tables and formatted output
"""

from __future__ import annotations

import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Color(Enum):
    """ANSI color codes."""
    BLACK = "30"
    RED = "31"
    GREEN = "32"
    YELLOW = "33"
    BLUE = "34"
    MAGENTA = "35"
    CYAN = "36"
    WHITE = "37"
    BRIGHT_BLACK = "90"
    BRIGHT_RED = "91"
    BRIGHT_GREEN = "92"
    BRIGHT_YELLOW = "93"
    BRIGHT_BLUE = "94"
    BRIGHT_MAGENTA = "95"
    BRIGHT_CYAN = "96"
    BRIGHT_WHITE = "97"

    # Background colors
    BG_BLACK = "40"
    BG_RED = "41"
    BG_GREEN = "42"
    BG_YELLOW = "43"
    BG_BLUE = "44"
    BG_MAGENTA = "45"
    BG_CYAN = "46"
    BG_WHITE = "47"


class Style(Enum):
    """ANSI style codes."""
    RESET = "0"
    BOLD = "1"
    DIM = "2"
    ITALIC = "3"
    UNDERLINE = "4"
    BLINK = "5"
    REVERSE = "7"
    HIDDEN = "8"
    STRIKETHROUGH = "9"


@dataclass
class OutputConfig:
    """Configuration for colored output."""
    use_color: bool = True
    stream: Any = None  # Defaults to sys.stdout
    width: int = 80
    force_color: bool = False  # Force color even if not a TTY


@dataclass
class ProgressConfig:
    """Configuration for progress bar."""
    total: int = 100
    width: int = 40
    fill_char: str = "█"
    empty_char: str = "░"
    prefix: str = ""
    suffix: str = ""
    show_percent: bool = True
    show_eta: bool = True
    color: Color | None = Color.GREEN


@dataclass
class SpinnerConfig:
    """Configuration for spinner."""
    frames: list[str] | None = None
    interval: float = 0.1
    message: str = "Loading..."
    color: Color | None = Color.CYAN


class ColoredOutput:
    """Colored text output handler.

    Features:
    - ANSI color support
    - Style formatting
    - Automatic TTY detection
    - Fallback for non-TTY environments
    """

    def __init__(self, config: OutputConfig | None = None):
        """Initialize output handler.

        Args:
            config: Output configuration
        """
        self.config = config or OutputConfig()
        self._stream = self.config.stream or sys.stdout
        self._is_tty = hasattr(self._stream, "isatty") and self._stream.isatty()

    def _should_use_color(self) -> bool:
        """Check if color should be used."""
        if self.config.force_color:
            return True
        if not self.config.use_color:
            return False
        return self._is_tty

    def colorize(
        self,
        text: str,
        color: Color | None = None,
        style: Style | list[Style] | None = None,
    ) -> str:
        """Apply color and style to text.

        Args:
            text: Text to colorize
            color: Text color
            style: Text style(s)

        Returns:
            Colorized text (or plain text if color disabled)
        """
        if not self._should_use_color():
            return text

        codes: list[str] = []

        if style:
            if isinstance(style, Style):
                codes.append(style.value)
            else:
                codes.extend(s.value for s in style)

        if color:
            codes.append(color.value)

        if not codes:
            return text

        start = "\033[" + ";".join(codes) + "m"
        end = "\033[" + Style.RESET.value + "m"

        return f"{start}{text}{end}"

    def print(
        self,
        text: str,
        color: Color | None = None,
        style: Style | list[Style] | None = None,
        end: str = "\n",
    ) -> None:
        """Print colored text.

        Args:
            text: Text to print
            color: Text color
            style: Text style(s)
            end: Line ending
        """
        output = self.colorize(text, color, style)
        self._stream.write(output + end)
        self._stream.flush()

    def success(self, text: str, prefix: str = "✓ ") -> None:
        """Print success message.

        Args:
            text: Message text
            prefix: Prefix to use
        """
        self.print(f"{prefix}{text}", color=Color.GREEN)

    def error(self, text: str, prefix: str = "✗ ") -> None:
        """Print error message.

        Args:
            text: Message text
            prefix: Prefix to use
        """
        self.print(f"{prefix}{text}", color=Color.RED)

    def warning(self, text: str, prefix: str = "! ") -> None:
        """Print warning message.

        Args:
            text: Message text
            prefix: Prefix to use
        """
        self.print(f"{prefix}{text}", color=Color.YELLOW)

    def info(self, text: str, prefix: str = "• ") -> None:
        """Print info message.

        Args:
            text: Message text
            prefix: Prefix to use
        """
        self.print(f"{prefix}{text}", color=Color.CYAN)

    def header(self, text: str) -> None:
        """Print header.

        Args:
            text: Header text
        """
        self.print(text, style=Style.BOLD)

    def dim(self, text: str) -> None:
        """Print dimmed text.

        Args:
            text: Text to print
        """
        self.print(text, style=Style.DIM)

    def table(
        self,
        headers: list[str],
        rows: list[list[str]],
        colors: list[Color | None] | None = None,
    ) -> None:
        """Print a formatted table.

        Args:
            headers: Column headers
            rows: Table rows
            colors: Optional column colors
        """
        # Calculate column widths
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))

        # Print header
        header_parts = []
        for i, h in enumerate(headers):
            if colors and i < len(colors) and colors[i]:
                header_parts.append(self.colorize(h.ljust(widths[i]), colors[i], Style.BOLD))
            else:
                header_parts.append(self.colorize(h.ljust(widths[i]), None, Style.BOLD))
        self.print("  ".join(header_parts))

        # Print separator
        separator = "  ".join("─" * w for w in widths)
        self.print(separator, style=Style.DIM)

        # Print rows
        for row in rows:
            row_parts = []
            for i, cell in enumerate(row):
                cell_str = str(cell).ljust(widths[i]) if i < len(widths) else str(cell)
                if colors and i < len(colors) and colors[i]:
                    row_parts.append(self.colorize(cell_str, colors[i]))
                else:
                    row_parts.append(cell_str)
            self.print("  ".join(row_parts))


class ProgressBar:
    """Progress bar indicator.

    Features:
    - Visual progress display
    - ETA calculation
    - Percentage display
    - Color support
    """

    def __init__(self, config: ProgressConfig | None = None):
        """Initialize progress bar.

        Args:
            config: Progress bar configuration
        """
        self.config = config or ProgressConfig()
        self._current = 0
        self._start_time: float | None = None
        self._output = ColoredOutput()

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to human readable."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds / 3600)}h {int((seconds % 3600) / 60)}m"

    def _calculate_eta(self) -> float:
        """Calculate estimated time remaining."""
        if self._start_time is None or self._current == 0:
            return 0.0

        elapsed = time.time() - self._start_time
        if elapsed == 0:
            return 0.0

        rate = self._current / elapsed
        remaining = (self.config.total - self._current) / rate if rate > 0 else 0
        return remaining

    def update(self, n: int = 1) -> None:
        """Update progress.

        Args:
            n: Amount to increment
        """
        if self._start_time is None:
            self._start_time = time.time()

        self._current = min(self._current + n, self.config.total)
        self.display()

    def set_progress(self, current: int) -> None:
        """Set current progress.

        Args:
            current: Current progress value
        """
        if self._start_time is None:
            self._start_time = time.time()

        self._current = max(0, min(current, self.config.total))
        self.display()

    def display(self) -> None:
        """Display the progress bar."""
        percent = self._current / self.config.total if self.config.total > 0 else 0
        filled = int(self.config.width * percent)
        empty = self.config.width - filled

        # Build bar
        bar = self.config.fill_char * filled + self.config.empty_char * empty

        # Colorize bar
        if self.config.color and self._output._should_use_color():
            bar = self._output.colorize(bar, self.config.color)

        # Build suffix
        suffix_parts = []
        if self.config.show_percent:
            suffix_parts.append(f"{int(percent * 100)}%")
        if self.config.show_eta and self._current > 0:
            eta = self._calculate_eta()
            suffix_parts.append(f"ETA: {self._format_time(eta)}")

        suffix = " ".join(suffix_parts)
        if self.config.suffix:
            suffix = f"{suffix} {self.config.suffix}"

        # Print
        line = f"\r{self.config.prefix}|{bar}| {self._current}/{self.config.total} {suffix}"
        sys.stdout.write(line)
        sys.stdout.flush()

    def complete(self) -> None:
        """Mark progress as complete."""
        self._current = self.config.total
        self.display()
        print()  # New line after completion

    def reset(self) -> None:
        """Reset progress bar."""
        self._current = 0
        self._start_time = None

    def __enter__(self) -> ProgressBar:
        """Enter context manager."""
        return self

    def __exit__(self, *args) -> None:
        """Exit context manager."""
        if self._current < self.config.total:
            print()  # New line if not completed


class Spinner:
    """Loading spinner indicator.

    Features:
    - Animated spinner frames
    - Status messages
    - Color support
    """

    DEFAULT_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, config: SpinnerConfig | None = None):
        """Initialize spinner.

        Args:
            config: Spinner configuration
        """
        self.config = config or SpinnerConfig()
        self._frames = self.config.frames or self.DEFAULT_FRAMES
        self._frame_index = 0
        self._running = False
        self._output = ColoredOutput()

    def _render(self) -> str:
        """Render current spinner frame."""
        frame = self._frames[self._frame_index]

        if self.config.color and self._output._should_use_color():
            frame = self._output.colorize(frame, self.config.color)

        return f"{frame} {self.config.message}"

    def spin(self) -> str:
        """Get next spinner frame.

        Returns:
            Current spinner frame string
        """
        frame = self._render()
        self._frame_index = (self._frame_index + 1) % len(self._frames)
        return frame

    def update(self, message: str) -> None:
        """Update spinner message.

        Args:
            message: New message
        """
        self.config.message = message

    def display(self) -> None:
        """Display spinner frame."""
        line = f"\r{self.spin()}   "
        sys.stdout.write(line)
        sys.stdout.flush()

    def start(self) -> None:
        """Start the spinner."""
        self._running = True

    def stop(self, final_message: str | None = None) -> None:
        """Stop the spinner.

        Args:
            final_message: Optional final message to display
        """
        self._running = False
        sys.stdout.write("\r" + " " * (len(self.config.message) + 10) + "\r")
        if final_message:
            print(final_message)

    def __iter__(self) -> Iterator[str]:
        """Iterate over spinner frames."""
        while self._running:
            yield self.spin()
            time.sleep(self.config.interval)


def create_output(config: OutputConfig | None = None) -> ColoredOutput:
    """Create a colored output handler.

    Args:
        config: Output configuration

    Returns:
        ColoredOutput instance
    """
    return ColoredOutput(config)


def create_progress_bar(config: ProgressConfig | None = None) -> ProgressBar:
    """Create a progress bar.

    Args:
        config: Progress bar configuration

    Returns:
        ProgressBar instance
    """
    return ProgressBar(config)


def create_spinner(config: SpinnerConfig | None = None) -> Spinner:
    """Create a spinner.

    Args:
        config: Spinner configuration

    Returns:
        Spinner instance
    """
    return Spinner(config)
