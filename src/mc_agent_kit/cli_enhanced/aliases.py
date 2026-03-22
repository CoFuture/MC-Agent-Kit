"""Command aliases management for MC-Agent-Kit CLI.

This module provides:
- Command alias definitions
- Alias expansion
- Custom alias support
- Built-in aliases for common commands
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CommandAlias:
    """A command alias definition."""
    name: str
    command: str
    description: str = ""
    arguments: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)

    def expand(self, args: list[str] | None = None) -> str:
        """Expand alias to full command.

        Args:
            args: Additional arguments

        Returns:
            Expanded command string
        """
        result = self.command

        # Replace positional arguments
        for i, arg in enumerate(self.arguments):
            placeholder = f"${i + 1}"
            if args and i < len(args):
                result = result.replace(placeholder, args[i])
            elif placeholder in result:
                # Keep placeholder if no arg provided
                pass

        # Append extra arguments
        if args and len(args) > len(self.arguments):
            result += " " + " ".join(args[len(self.arguments):])

        # Replace $@ with all arguments
        if "$@" in result:
            all_args = " ".join(args) if args else ""
            result = result.replace("$@", all_args)

        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "command": self.command,
            "description": self.description,
            "arguments": self.arguments,
            "examples": self.examples,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CommandAlias:
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            command=data.get("command", ""),
            description=data.get("description", ""),
            arguments=data.get("arguments", []),
            examples=data.get("examples", []),
        )


@dataclass
class AliasConfig:
    """Configuration for alias manager."""
    aliases_file: str | None = None
    case_insensitive: bool = True
    allow_overwrite: bool = True


class AliasManager:
    """Command alias manager.

    Features:
    - Register and unregister aliases
    - Expand aliases to commands
    - Load/save aliases to file
    - Built-in common aliases
    """

    def __init__(self, config: AliasConfig | None = None):
        """Initialize alias manager.

        Args:
            config: Alias configuration
        """
        self.config = config or AliasConfig()
        self._aliases: dict[str, CommandAlias] = {}

        # Load built-in aliases
        for alias in get_builtin_aliases():
            self._aliases[self._normalize(alias.name)] = alias

        # Load from file
        if self.config.aliases_file:
            self.load()

    def _normalize(self, name: str) -> str:
        """Normalize alias name."""
        return name.lower() if self.config.case_insensitive else name

    def register(self, alias: CommandAlias) -> bool:
        """Register an alias.

        Args:
            alias: Alias to register

        Returns:
            True if registered successfully
        """
        name = self._normalize(alias.name)

        if name in self._aliases and not self.config.allow_overwrite:
            return False

        self._aliases[name] = alias
        return True

    def unregister(self, name: str) -> bool:
        """Unregister an alias.

        Args:
            name: Alias name

        Returns:
            True if alias was removed
        """
        name = self._normalize(name)
        if name in self._aliases:
            del self._aliases[name]
            return True
        return False

    def get(self, name: str) -> CommandAlias | None:
        """Get an alias by name.

        Args:
            name: Alias name

        Returns:
            CommandAlias or None
        """
        return self._aliases.get(self._normalize(name))

    def expand(self, name: str, args: list[str] | None = None) -> str | None:
        """Expand an alias to a command.

        Args:
            name: Alias name
            args: Additional arguments

        Returns:
            Expanded command or None if alias not found
        """
        alias = self.get(name)
        if alias:
            return alias.expand(args)
        return None

    def list_aliases(self) -> list[CommandAlias]:
        """List all registered aliases.

        Returns:
            List of aliases
        """
        return list(self._aliases.values())

    def list_names(self) -> list[str]:
        """List alias names.

        Returns:
            List of alias names
        """
        return list(self._aliases.keys())

    def is_alias(self, name: str) -> bool:
        """Check if name is a registered alias.

        Args:
            name: Name to check

        Returns:
            True if it's an alias
        """
        return self._normalize(name) in self._aliases

    def save(self, path: str | None = None) -> bool:
        """Save aliases to file.

        Args:
            path: Optional path override

        Returns:
            True if saved successfully
        """
        save_path = Path(path or self.config.aliases_file or "")
        if not save_path:
            return False

        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "version": 1,
                "aliases": [a.to_dict() for a in self._aliases.values()],
            }

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            return True
        except Exception:
            return False

    def load(self, path: str | None = None) -> bool:
        """Load aliases from file.

        Args:
            path: Optional path override

        Returns:
            True if loaded successfully
        """
        load_path = Path(path or self.config.aliases_file or "")
        if not load_path or not load_path.exists():
            return False

        try:
            with open(load_path, encoding="utf-8") as f:
                data = json.load(f)

            if data.get("version") == 1:
                for alias_data in data.get("aliases", []):
                    alias = CommandAlias.from_dict(alias_data)
                    self.register(alias)

            return True
        except Exception:
            return False


def get_builtin_aliases() -> list[CommandAlias]:
    """Get built-in aliases for common commands.

    Returns:
        List of built-in aliases
    """
    return [
        # Knowledge base aliases
        CommandAlias(
            name="s",
            command="kb search $@",
            description="Shortcut for kb search",
            examples=["s entity", "s create"],
        ),
        CommandAlias(
            name="api",
            command="kb api $@",
            description="Shortcut for kb api",
            examples=["api CreateEntity", "api GetConfig"],
        ),
        CommandAlias(
            name="evt",
            command="kb event $@",
            description="Shortcut for kb event",
            examples=["evt OnServerChat", "evt OnPlayerJoin"],
        ),

        # Create aliases
        CommandAlias(
            name="new",
            command="create project $@",
            description="Shortcut for create project",
            examples=["new my-addon"],
        ),
        CommandAlias(
            name="mkent",
            command="create entity $@",
            description="Shortcut for create entity",
            examples=["mkent my_entity"],
        ),
        CommandAlias(
            name="mkitem",
            command="create item $@",
            description="Shortcut for create item",
            examples=["mkitem my_item"],
        ),
        CommandAlias(
            name="mkblock",
            command="create block $@",
            description="Shortcut for create block",
            examples=["mkblock my_block"],
        ),

        # Launcher aliases
        CommandAlias(
            name="run",
            command="launcher run $@",
            description="Shortcut for launcher run",
            examples=["run ./my-addon"],
        ),
        CommandAlias(
            name="diag",
            command="launcher diagnose $@",
            description="Shortcut for launcher diagnose",
            examples=["diag"],
        ),

        # Stats aliases
        CommandAlias(
            name="stat",
            command="stats summary $@",
            description="Shortcut for stats summary",
            examples=["stat"],
        ),
        CommandAlias(
            name="hot",
            command="stats hot $@",
            description="Shortcut for stats hot",
            examples=["hot 10"],
        ),

        # Debug aliases
        CommandAlias(
            name="dbg",
            command="debug analyze $@",
            description="Shortcut for debug analyze",
            examples=["dbg error.log"],
        ),

        # Help aliases
        CommandAlias(
            name="?",
            command="help $@",
            description="Shortcut for help",
            examples=["? create", "? kb"],
        ),
    ]


def create_alias_manager(config: AliasConfig | None = None) -> AliasManager:
    """Create an alias manager.

    Args:
        config: Alias configuration

    Returns:
        AliasManager instance
    """
    return AliasManager(config)
