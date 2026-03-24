"""Advanced command completion for MC-Agent-Kit CLI.

This module provides intelligent command completion:
- Context-aware suggestions
- Argument completion
- File path completion
- API/Event name completion
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class CompletionType(Enum):
    """Types of completions."""
    COMMAND = "command"
    ARGUMENT = "argument"
    FILE_PATH = "file_path"
    DIRECTORY = "directory"
    API_NAME = "api_name"
    EVENT_NAME = "event_name"
    MODULE_NAME = "module_name"
    VARIABLE = "variable"
    VALUE = "value"


@dataclass
class CompletionItem:
    """A completion suggestion."""
    text: str
    display: str = ""
    type: CompletionType = CompletionType.VALUE
    description: str = ""
    priority: int = 0
    insert_text: str = ""  # Text to insert (may differ from display)

    def __post_init__(self):
        if not self.display:
            self.display = self.text
        if not self.insert_text:
            self.insert_text = self.text


@dataclass
class CompletionContext:
    """Context for completion."""
    line: str
    cursor_position: int
    command: str = ""
    argument_index: int = 0
    previous_arguments: list[str] = field(default_factory=list)
    current_word: str = ""
    before_cursor: str = ""

    @property
    def word_start(self) -> int:
        """Get the start position of the current word."""
        if not self.before_cursor:
            return self.cursor_position
        
        # Find the start of the current word
        match = re.search(r'(\S+)$', self.before_cursor)
        if match:
            return self.cursor_position - len(match.group(1))
        return self.cursor_position


class Completer:
    """Base completer class."""

    def complete(self, context: CompletionContext) -> list[CompletionItem]:
        """Get completions for the given context.

        Args:
            context: Completion context

        Returns:
            List of completion items
        """
        return []


class CommandCompleter(Completer):
    """Completer for CLI commands."""

    def __init__(self, commands: dict[str, Any] | None = None):
        """Initialize command completer.

        Args:
            commands: Dictionary of command info
        """
        self._commands = commands or {}
        self._aliases: dict[str, str] = {}

    def register_command(self, name: str, description: str = "", 
                         aliases: list[str] | None = None) -> None:
        """Register a command.

        Args:
            name: Command name
            description: Command description
            aliases: Command aliases
        """
        self._commands[name] = {"description": description, "aliases": aliases or []}
        for alias in aliases or []:
            self._aliases[alias] = name

    def complete(self, context: CompletionContext) -> list[CompletionItem]:
        """Get command completions."""
        if context.argument_index > 0:
            return []

        prefix = context.current_word.lower()
        items = []

        for name, info in self._commands.items():
            if name.lower().startswith(prefix):
                items.append(CompletionItem(
                    text=name,
                    type=CompletionType.COMMAND,
                    description=info.get("description", ""),
                    priority=10,
                ))

        for alias, cmd in self._aliases.items():
            if alias.lower().startswith(prefix):
                items.append(CompletionItem(
                    text=alias,
                    display=f"{alias} → {cmd}",
                    type=CompletionType.COMMAND,
                    description=f"Alias for {cmd}",
                    priority=5,
                ))

        return sorted(items, key=lambda x: (-x.priority, x.text))


class FilePathCompleter(Completer):
    """Completer for file paths."""

    def __init__(self, extensions: list[str] | None = None,
                 directories_only: bool = False):
        """Initialize file path completer.

        Args:
            extensions: Allowed file extensions
            directories_only: Only complete directories
        """
        self._extensions = extensions
        self._directories_only = directories_only

    def complete(self, context: CompletionContext) -> list[CompletionItem]:
        """Get file path completions."""
        path = context.current_word
        items = []

        # Handle relative paths
        if not os.path.isabs(path):
            base_dir = Path.cwd()
        else:
            base_dir = Path(path).parent

        try:
            # Get the directory and prefix
            if os.path.dirname(path):
                dir_path = base_dir / os.path.dirname(path)
                prefix = os.path.basename(path)
            else:
                dir_path = base_dir
                prefix = path

            if not dir_path.exists():
                return []

            for entry in dir_path.iterdir():
                if self._directories_only and not entry.is_dir():
                    continue

                name = entry.name
                if not name.lower().startswith(prefix.lower()):
                    continue

                if self._extensions and entry.is_file():
                    if not any(name.endswith(ext) for ext in self._extensions):
                        continue

                display = name
                if entry.is_dir():
                    display = name + "/"
                    insert = os.path.join(os.path.dirname(path), name) if os.path.dirname(path) else name
                else:
                    insert = os.path.join(os.path.dirname(path), name) if os.path.dirname(path) else name

                items.append(CompletionItem(
                    text=insert,
                    display=display,
                    type=CompletionType.DIRECTORY if entry.is_dir() else CompletionType.FILE_PATH,
                    priority=10 if entry.is_dir() else 5,
                ))

        except (OSError, PermissionError):
            pass

        return sorted(items, key=lambda x: (-x.priority, x.display))


class ApiNameCompleter(Completer):
    """Completer for ModSDK API names."""

    def __init__(self, api_names: list[str] | None = None):
        """Initialize API name completer.

        Args:
            api_names: List of API names
        """
        self._api_names = api_names or []
        self._by_module: dict[str, list[str]] = {}

        # Group by module
        for api in self._api_names:
            parts = api.split(".")
            if len(parts) > 1:
                module = parts[0]
                if module not in self._by_module:
                    self._by_module[module] = []
                self._by_module[module].append(api)

    def add_api(self, name: str) -> None:
        """Add an API name.

        Args:
            name: API name
        """
        if name not in self._api_names:
            self._api_names.append(name)
            parts = name.split(".")
            if len(parts) > 1:
                module = parts[0]
                if module not in self._by_module:
                    self._by_module[module] = []
                self._by_module[module].append(name)

    def complete(self, context: CompletionContext) -> list[CompletionItem]:
        """Get API name completions."""
        prefix = context.current_word.lower()
        items = []

        for api in self._api_names:
            if api.lower().startswith(prefix):
                # Show module info
                parts = api.split(".")
                module = parts[0] if len(parts) > 1 else ""

                items.append(CompletionItem(
                    text=api,
                    type=CompletionType.API_NAME,
                    description=f"Module: {module}" if module else "",
                    priority=10,
                ))

        # Also complete module names
        for module in self._by_module.keys():
            if module.lower().startswith(prefix):
                count = len(self._by_module[module])
                items.append(CompletionItem(
                    text=module,
                    type=CompletionType.MODULE_NAME,
                    description=f"{count} APIs",
                    priority=5,
                ))

        return sorted(items, key=lambda x: (-x.priority, x.text))


class EventNameCompleter(Completer):
    """Completer for ModSDK event names."""

    def __init__(self, event_names: list[str] | None = None):
        """Initialize event name completer.

        Args:
            event_names: List of event names
        """
        self._event_names = event_names or []

    def add_event(self, name: str) -> None:
        """Add an event name.

        Args:
            name: Event name
        """
        if name not in self._event_names:
            self._event_names.append(name)

    def complete(self, context: CompletionContext) -> list[CompletionItem]:
        """Get event name completions."""
        prefix = context.current_word.lower()
        items = []

        for event in self._event_names:
            if event.lower().startswith(prefix):
                items.append(CompletionItem(
                    text=event,
                    type=CompletionType.EVENT_NAME,
                    priority=10,
                ))

        return sorted(items, key=lambda x: x.text)


class CompositeCompleter(Completer):
    """Combines multiple completers."""

    def __init__(self, completers: list[Completer] | None = None):
        """Initialize composite completer.

        Args:
            completers: List of completers
        """
        self._completers = completers or []

    def add_completer(self, completer: Completer) -> None:
        """Add a completer.

        Args:
            completer: Completer to add
        """
        self._completers.append(completer)

    def complete(self, context: CompletionContext) -> list[CompletionItem]:
        """Get completions from all completers."""
        items = []
        for completer in self._completers:
            items.extend(completer.complete(context))
        return items


class ArgumentCompleter(Completer):
    """Completer for command arguments."""

    def __init__(self):
        """Initialize argument completer."""
        # Maps (command, arg_index) -> completer
        self._completers: dict[tuple[str, int], Completer] = {}
        # Maps argument name -> completer
        self._option_completers: dict[str, Completer] = {}

    def register_positional(self, command: str, index: int, 
                           completer: Completer) -> None:
        """Register a completer for a positional argument.

        Args:
            command: Command name
            index: Argument index
            completer: Completer to use
        """
        self._completers[(command, index)] = completer

    def register_option(self, option: str, completer: Completer) -> None:
        """Register a completer for an option value.

        Args:
            option: Option name (e.g., "--file")
            completer: Completer to use
        """
        self._option_completers[option] = completer

    def complete(self, context: CompletionContext) -> list[CompletionItem]:
        """Get argument completions."""
        # Check for option completion
        if context.previous_arguments:
            last_arg = context.previous_arguments[-1]
            if last_arg.startswith("-") and last_arg in self._option_completers:
                return self._option_completers[last_arg].complete(context)

        # Check for positional argument completion
        key = (context.command, context.argument_index)
        if key in self._completers:
            return self._completers[key].complete(context)

        return []


def parse_completion_context(line: str, cursor_position: int) -> CompletionContext:
    """Parse completion context from input line.

    Args:
        line: Input line
        cursor_position: Cursor position

    Returns:
        Completion context
    """
    before_cursor = line[:cursor_position]
    
    # Simple tokenization (handles quotes)
    tokens = []
    current = ""
    in_quotes = False
    quote_char = ""
    
    for char in before_cursor:
        if char in ('"', "'") and not in_quotes:
            in_quotes = True
            quote_char = char
        elif char == quote_char and in_quotes:
            in_quotes = False
            quote_char = ""
        elif char.isspace() and not in_quotes:
            if current:
                tokens.append(current)
                current = ""
        else:
            current += char
    
    # Handle the last token (current word being typed)
    current_word = current
    
    # If cursor is at a space, current_word is empty
    if before_cursor and before_cursor[-1].isspace():
        current_word = ""
    
    command = tokens[0] if tokens else ""
    previous_arguments = tokens[1:] if len(tokens) > 1 else []
    argument_index = len(previous_arguments)
    
    # Adjust for current word not being complete
    if current_word and not (before_cursor and before_cursor[-1].isspace()):
        argument_index = len(previous_arguments)
    else:
        argument_index = len(previous_arguments)
    
    return CompletionContext(
        line=line,
        cursor_position=cursor_position,
        command=command,
        argument_index=argument_index,
        previous_arguments=previous_arguments,
        current_word=current_word,
        before_cursor=before_cursor,
    )


def create_default_completer() -> CompositeCompleter:
    """Create the default completer with standard completions.

    Returns:
        Configured CompositeCompleter
    """
    # Create command completer
    command_completer = CommandCompleter()
    
    # Register all CLI commands
    commands = {
        "list": "List all Skills",
        "api": "Search ModSDK API",
        "event": "Search ModSDK events",
        "gen": "Generate ModSDK code",
        "debug": "Debug ModSDK errors",
        "complete": "Code completion",
        "refactor": "Code refactoring",
        "check": "Best practice check",
        "autofix": "Auto-fix errors",
        "create": "Create Addon project",
        "kb": "Knowledge base management",
        "run": "Run game with Addon",
        "logs": "Log analysis",
        "launcher": "Launcher diagnostics",
        "stats": "API usage statistics",
        "repl": "Interactive REPL",
        "config": "Configuration management",
        "docs": "Documentation generation",
        "wizard": "Interactive wizard",
        "batch": "Batch operations",
        "workflow": "Workflow management",
    }
    
    for cmd, desc in commands.items():
        command_completer.register_command(cmd, desc)
    
    # Create file path completer
    file_completer = FilePathCompleter()
    dir_completer = FilePathCompleter(directories_only=True)
    
    # Create API/Event completers
    api_completer = ApiNameCompleter()
    event_completer = EventNameCompleter()
    
    # Create argument completer
    arg_completer = ArgumentCompleter()
    
    # Register completions for specific arguments
    arg_completer.register_positional("api", 0, api_completer)
    arg_completer.register_positional("event", 0, event_completer)
    arg_completer.register_positional("run", 0, dir_completer)
    arg_completer.register_positional("create", 1, file_completer)
    arg_completer.register_option("--file", file_completer)
    arg_completer.register_option("--addon-path", dir_completer)
    arg_completer.register_option("--config-path", file_completer)
    arg_completer.register_option("--output", file_completer)
    
    # Create composite completer
    composite = CompositeCompleter([
        command_completer,
        file_completer,
        api_completer,
        event_completer,
        arg_completer,
    ])
    
    return composite


def format_completions(items: list[CompletionItem], 
                       max_width: int = 80) -> str:
    """Format completions for display.

    Args:
        items: Completion items
        max_width: Maximum line width

    Returns:
        Formatted string
    """
    if not items:
        return ""
    
    # Find max display length
    max_len = max(len(item.display) for item in items)
    max_len = min(max_len, max_width - 20)
    
    lines = []
    for item in items[:20]:  # Limit to 20 items
        display = item.display[:max_len]
        if item.description:
            desc = item.description[:max_width - max_len - 5]
            lines.append(f"  {display:<{max_len}}  {desc}")
        else:
            lines.append(f"  {display}")
    
    return "\n".join(lines)