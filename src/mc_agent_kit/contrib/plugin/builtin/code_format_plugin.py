"""Code formatting plugin for MC-Agent-Kit.

Provides code formatting capabilities for Python and other languages.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from mc_agent_kit.contrib.plugin.base import (
    PluginBase,
    PluginMetadata,
    PluginResult,
    PluginPriority,
    PluginState,
)
from mc_agent_kit.contrib.plugin.hooks import HookType, HookPriority, register_hook
from mc_agent_kit.contrib.plugin.config import PluginConfigSchema


class FormatterType(Enum):
    """Code formatter type."""
    AUTO = "auto"
    BLACK = "black"
    RUFF = "ruff"
    YAPF = "yapf"
    AUTOPEP8 = "autopep8"
    ISORT = "isort"
    BUILTIN = "builtin"


@dataclass
class FormatResult:
    """Result of code formatting."""
    original: str
    formatted: str
    changed: bool
    formatter: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class FormatConfig:
    """Configuration for formatting."""
    formatter: FormatterType = FormatterType.AUTO
    line_length: int = 100
    indent_size: int = 4
    use_tabs: bool = False
    format_on_save: bool = False
    check_only: bool = False
    exclude_patterns: list[str] = field(default_factory=lambda: ["__pycache__", ".git", "venv", "node_modules"])


class CodeFormatPlugin(PluginBase):
    """Plugin for code formatting."""

    def __init__(self) -> None:
        """Initialize the code format plugin."""
        metadata = PluginMetadata(
            name="code-format",
            version="1.0.0",
            description="Code formatting plugin for Python",
            author="MC-Agent-Kit",
            capabilities=["formatting", "python", "code-quality"],
            priority=PluginPriority.NORMAL,
        )
        super().__init__(metadata)
        self._config = FormatConfig()

    def initialize(self) -> bool:
        """Initialize the plugin.
        
        Returns:
            True if successful.
        """
        # Set state to LOADED
        self._state = PluginState.LOADED
        
        # Register hook for file write
        register_hook(
            HookType.ON_FILE_WRITE,
            self._on_file_write,
            HookPriority.NORMAL,
            self.metadata.name,
            "Format Python files on write",
        )
        return True

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        pass

    def execute(self, **kwargs: Any) -> PluginResult:
        """Execute a formatting operation.
        
        Args:
            **kwargs: Operation parameters.
                - operation: Operation to perform (format, check, config)
                - code: Code to format (for format operation)
                - path: File path to format
                - formatter: Formatter to use
                - line_length: Line length limit
        
        Returns:
            Execution result.
        """
        operation = kwargs.get("operation", "format")
        
        operations = {
            "format": self._format,
            "check": self._check,
            "format_file": self._format_file,
            "check_file": self._check_file,
            "config": self._configure,
        }
        
        if operation not in operations:
            return PluginResult(
                success=False,
                error=f"Unknown operation: {operation}",
            )
        
        try:
            result = operations[operation](**kwargs)
            return PluginResult(success=True, data=result)
        except Exception as e:
            return PluginResult(success=False, error=str(e))

    def _format(self, **kwargs: Any) -> FormatResult:
        """Format code string.
        
        Returns:
            Format result.
        """
        code = kwargs.get("code", "")
        if not code:
            return FormatResult(
                original=code,
                formatted=code,
                changed=False,
                formatter="none",
                errors=["No code provided"],
            )
        
        formatter_type = self._get_formatter(kwargs.get("formatter"))
        line_length = kwargs.get("line_length", self._config.line_length)
        
        return self._format_code(code, formatter_type, line_length)

    def _check(self, **kwargs: Any) -> dict[str, Any]:
        """Check if code needs formatting.
        
        Returns:
            Check result.
        """
        code = kwargs.get("code", "")
        formatter_type = self._get_formatter(kwargs.get("formatter"))
        line_length = kwargs.get("line_length", self._config.line_length)
        
        result = self._format_code(code, formatter_type, line_length)
        
        return {
            "needs_formatting": result.changed,
            "formatter": result.formatter,
            "errors": result.errors,
        }

    def _format_file(self, **kwargs: Any) -> dict[str, Any]:
        """Format a file.
        
        Returns:
            Format result.
        """
        path = kwargs.get("path")
        if not path:
            raise ValueError("Path is required")
        
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        # Check if excluded
        if self._is_excluded(path):
            return {"formatted": False, "reason": "File is excluded"}
        
        # Read file
        with open(path, "r", encoding="utf-8") as f:
            original = f.read()
        
        formatter_type = self._get_formatter(kwargs.get("formatter"))
        result = self._format_code(original, formatter_type, self._config.line_length)
        
        if result.changed and not self._config.check_only:
            with open(path, "w", encoding="utf-8") as f:
                f.write(result.formatted)
        
        return {
            "formatted": result.changed,
            "path": str(path),
            "formatter": result.formatter,
            "errors": result.errors,
        }

    def _check_file(self, **kwargs: Any) -> dict[str, Any]:
        """Check if a file needs formatting.
        
        Returns:
            Check result.
        """
        path = kwargs.get("path")
        if not path:
            raise ValueError("Path is required")
        
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if self._is_excluded(path):
            return {"needs_formatting": False, "reason": "File is excluded"}
        
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
        
        formatter_type = self._get_formatter(kwargs.get("formatter"))
        result = self._format_code(code, formatter_type, self._config.line_length)
        
        return {
            "needs_formatting": result.changed,
            "path": str(path),
            "formatter": result.formatter,
            "errors": result.errors,
        }

    def _configure(self, **kwargs: Any) -> dict[str, Any]:
        """Update configuration.
        
        Returns:
            Current configuration.
        """
        if "formatter" in kwargs:
            self._config.formatter = FormatterType(kwargs["formatter"])
        if "line_length" in kwargs:
            self._config.line_length = int(kwargs["line_length"])
        if "format_on_save" in kwargs:
            self._config.format_on_save = bool(kwargs["format_on_save"])
        if "check_only" in kwargs:
            self._config.check_only = bool(kwargs["check_only"])
        if "exclude_patterns" in kwargs:
            self._config.exclude_patterns = list(kwargs["exclude_patterns"])
        
        return {
            "formatter": self._config.formatter.value,
            "line_length": self._config.line_length,
            "format_on_save": self._config.format_on_save,
            "check_only": self._config.check_only,
            "exclude_patterns": self._config.exclude_patterns,
        }

    def _get_formatter(self, formatter: str | None) -> FormatterType:
        """Get formatter type from string.
        
        Args:
            formatter: Formatter name.
            
        Returns:
            FormatterType enum.
        """
        if not formatter or formatter == "auto":
            return self._config.formatter
        
        try:
            return FormatterType(formatter.lower())
        except ValueError:
            return FormatterType.AUTO

    def _format_code(self, code: str, formatter_type: FormatterType, line_length: int) -> FormatResult:
        """Format code using specified formatter.
        
        Args:
            code: Code to format.
            formatter_type: Formatter to use.
            line_length: Line length limit.
            
        Returns:
            Format result.
        """
        # Try external formatters first
        if formatter_type == FormatterType.AUTO:
            # Try black, then ruff, then fall back to builtin
            for ft in [FormatterType.BLACK, FormatterType.RUFF]:
                if self._is_formatter_available(ft):
                    return self._format_with_external(code, ft, line_length)
            
            # Fall back to builtin formatter
            return self._format_builtin(code, line_length)
        
        if formatter_type in [FormatterType.BLACK, FormatterType.RUFF, FormatterType.YAPF, FormatterType.AUTOPEP8]:
            if self._is_formatter_available(formatter_type):
                return self._format_with_external(code, formatter_type, line_length)
            else:
                # Fall back to builtin
                result = self._format_builtin(code, line_length)
                result.warnings.append(f"Formatter {formatter_type.value} not available, using builtin")
                return result
        
        if formatter_type == FormatterType.ISORT:
            return self._format_imports(code, line_length)
        
        return self._format_builtin(code, line_length)

    def _is_formatter_available(self, formatter_type: FormatterType) -> bool:
        """Check if external formatter is available.
        
        Args:
            formatter_type: Formatter to check.
            
        Returns:
            True if available.
        """
        commands = {
            FormatterType.BLACK: ["black", "--version"],
            FormatterType.RUFF: ["ruff", "--version"],
            FormatterType.YAPF: ["yapf", "--version"],
            FormatterType.AUTOPEP8: ["autopep8", "--version"],
        }
        
        if formatter_type not in commands:
            return False
        
        try:
            subprocess.run(
                commands[formatter_type],
                capture_output=True,
                timeout=5,
            )
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _format_with_external(self, code: str, formatter_type: FormatterType, line_length: int) -> FormatResult:
        """Format code using external formatter.
        
        Args:
            code: Code to format.
            formatter_type: Formatter to use.
            line_length: Line length limit.
            
        Returns:
            Format result.
        """
        commands = {
            FormatterType.BLACK: ["black", "-", "--line-length", str(line_length)],
            FormatterType.RUFF: ["ruff", "format", "-", "--line-length", str(line_length)],
            FormatterType.YAPF: ["yapf", f"--style={{based_on_style: pep8, column_limit: {line_length}}}"],
            FormatterType.AUTOPEP8: ["autopep8", "-", f"--max-line-length={line_length}"],
        }
        
        cmd = commands.get(formatter_type)
        if not cmd:
            return FormatResult(
                original=code,
                formatted=code,
                changed=False,
                formatter=formatter_type.value,
                errors=[f"Unknown formatter: {formatter_type.value}"],
            )
        
        try:
            result = subprocess.run(
                cmd,
                input=code,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            formatted = result.stdout
            
            return FormatResult(
                original=code,
                formatted=formatted,
                changed=formatted != code,
                formatter=formatter_type.value,
                errors=[result.stderr] if result.returncode != 0 else [],
            )
        except subprocess.TimeoutExpired:
            return FormatResult(
                original=code,
                formatted=code,
                changed=False,
                formatter=formatter_type.value,
                errors=["Formatter timed out"],
            )
        except Exception as e:
            return FormatResult(
                original=code,
                formatted=code,
                changed=False,
                formatter=formatter_type.value,
                errors=[str(e)],
            )

    def _format_builtin(self, code: str, line_length: int) -> FormatResult:
        """Format code using builtin formatter.
        
        Args:
            code: Code to format.
            line_length: Line length limit.
            
        Returns:
            Format result.
        """
        errors = []
        warnings = []
        
        try:
            formatted = code
            
            # Normalize line endings
            formatted = formatted.replace("\r\n", "\n").replace("\r", "\n")
            
            # Remove trailing whitespace
            lines = formatted.split("\n")
            lines = [line.rstrip() for line in lines]
            formatted = "\n".join(lines)
            
            # Ensure file ends with newline
            if formatted and not formatted.endswith("\n"):
                formatted += "\n"
            
            # Fix indentation (convert tabs to spaces if configured)
            if not self._config.use_tabs:
                lines = formatted.split("\n")
                new_lines = []
                for line in lines:
                    if line and line[0] == "\t":
                        # Convert leading tabs to spaces
                        stripped = line.lstrip("\t")
                        tab_count = len(line) - len(stripped)
                        new_lines.append(" " * (tab_count * self._config.indent_size) + stripped)
                    else:
                        new_lines.append(line)
                formatted = "\n".join(new_lines)
            
            # Check line length
            long_lines = []
            for i, line in enumerate(formatted.split("\n"), 1):
                if len(line) > line_length:
                    long_lines.append(f"Line {i} exceeds {line_length} characters ({len(line)} chars)")
            
            if long_lines:
                warnings.extend(long_lines[:5])  # Limit to 5 warnings
            
            return FormatResult(
                original=code,
                formatted=formatted,
                changed=formatted != code,
                formatter="builtin",
                errors=errors,
                warnings=warnings,
            )
        except Exception as e:
            return FormatResult(
                original=code,
                formatted=code,
                changed=False,
                formatter="builtin",
                errors=[str(e)],
            )

    def _format_imports(self, code: str, line_length: int) -> FormatResult:
        """Format imports using isort.
        
        Args:
            code: Code to format.
            line_length: Line length limit.
            
        Returns:
            Format result.
        """
        # Simple builtin import sorting
        lines = code.split("\n")
        
        import_lines = []
        other_lines = []
        in_import_block = True
        
        for line in lines:
            stripped = line.strip()
            if in_import_block:
                if stripped.startswith("import ") or stripped.startswith("from "):
                    import_lines.append(line)
                elif stripped == "" or stripped.startswith("#"):
                    continue  # Skip empty lines and comments in import block
                else:
                    in_import_block = False
                    other_lines.append(line)
            else:
                other_lines.append(line)
        
        # Sort imports
        import_lines.sort()
        
        # Reconstruct
        if import_lines:
            formatted = "\n".join(import_lines) + "\n\n" + "\n".join(other_lines)
        else:
            formatted = code
        
        return FormatResult(
            original=code,
            formatted=formatted,
            changed=formatted != code,
            formatter="isort-builtin",
        )

    def _is_excluded(self, path: Path) -> bool:
        """Check if path is excluded.
        
        Args:
            path: Path to check.
            
        Returns:
            True if excluded.
        """
        path_str = str(path)
        for pattern in self._config.exclude_patterns:
            if pattern in path_str:
                return True
        return False

    def _on_file_write(self, file_path: str, content: str, **kwargs: Any) -> None:
        """Hook callback for file write.
        
        Args:
            file_path: Path to file.
            content: File content.
            **kwargs: Additional arguments.
        """
        if not self._config.format_on_save:
            return
        
        path = Path(file_path)
        
        # Only format Python files
        if path.suffix != ".py":
            return
        
        if self._is_excluded(path):
            return
        
        # Format the content
        result = self._format_code(content, self._config.formatter, self._config.line_length)
        
        if result.changed:
            # Update the content in kwargs
            kwargs["content"] = result.formatted

    def format_code(self, code: str, formatter: str = "auto", line_length: int = 100) -> FormatResult:
        """Format code string (convenience method).
        
        Args:
            code: Code to format.
            formatter: Formatter to use.
            line_length: Line length limit.
            
        Returns:
            Format result.
        """
        return self._format_code(code, self._get_formatter(formatter), line_length)

    def format_file(self, path: str) -> dict[str, Any]:
        """Format a file (convenience method).
        
        Args:
            path: Path to file.
            
        Returns:
            Format result.
        """
        return self.execute(operation="format_file", path=path).data

    @classmethod
    def get_config_schemas(cls) -> list[PluginConfigSchema]:
        """Get configuration schemas.
        
        Returns:
            List of config schemas.
        """
        return [
            PluginConfigSchema(
                key="formatter",
                type="string",
                default="auto",
                description="Formatter to use",
                choices=["auto", "black", "ruff", "yapf", "autopep8", "builtin"],
            ),
            PluginConfigSchema(
                key="line_length",
                type="int",
                default=100,
                description="Maximum line length",
                min_value=50,
                max_value=200,
            ),
            PluginConfigSchema(
                key="format_on_save",
                type="bool",
                default=False,
                description="Automatically format files on save",
            ),
            PluginConfigSchema(
                key="check_only",
                type="bool",
                default=False,
                description="Only check formatting without modifying files",
            ),
        ]