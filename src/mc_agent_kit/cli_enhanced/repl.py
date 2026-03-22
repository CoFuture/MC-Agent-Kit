"""Interactive CLI REPL (Read-Eval-Print Loop) for MC-Agent-Kit.

This module provides an interactive command-line interface with:
- Command history navigation
- Auto-completion support
- Multi-line input
- Command aliases
- Session management
"""

from __future__ import annotations

import shlex
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ReplState(Enum):
    """REPL session state."""
    IDLE = "idle"
    RUNNING = "running"
    MULTI_LINE = "multi_line"
    EXITING = "exiting"
    ERROR = "error"


@dataclass
class ReplCommand:
    """A command in the REPL."""
    name: str
    description: str = ""
    usage: str = ""
    aliases: list[str] = field(default_factory=list)
    handler: Callable[[list[str], dict], ReplResult] | None = None
    subcommands: dict[str, ReplCommand] = field(default_factory=dict)

    def get_help(self) -> str:
        """Get help text for this command."""
        lines = [f"{self.name}: {self.description}"]
        if self.usage:
            lines.append(f"  Usage: {self.usage}")
        if self.aliases:
            lines.append(f"  Aliases: {', '.join(self.aliases)}")
        if self.subcommands:
            lines.append("  Subcommands:")
            for name, cmd in self.subcommands.items():
                lines.append(f"    {name}: {cmd.description}")
        return "\n".join(lines)


@dataclass
class ReplResult:
    """Result of a REPL command execution."""
    success: bool
    output: str = ""
    error: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    exit: bool = False  # True if this command should exit the REPL
    state_change: ReplState | None = None


@dataclass
class ReplConfig:
    """Configuration for the REPL."""
    prompt: str = "mc-agent> "
    continue_prompt: str = "... "
    history_file: str | None = None
    max_history: int = 1000
    welcome_message: str = "Welcome to MC-Agent-Kit REPL. Type 'help' for commands."
    exit_message: str = "Goodbye!"
    enable_multi_line: bool = True
    multi_line_end: str = ""
    enable_aliases: bool = True
    case_insensitive: bool = True
    debug: bool = False


class CLIRepl:
    """Interactive CLI REPL for MC-Agent-Kit.

    Features:
    - Command registration and dispatch
    - History navigation (up/down arrows)
    - Auto-completion support
    - Multi-line input mode
    - Command aliases
    - Session management
    """

    def __init__(self, config: ReplConfig | None = None):
        """Initialize the REPL.

        Args:
            config: REPL configuration
        """
        self.config = config or ReplConfig()
        self._commands: dict[str, ReplCommand] = {}
        self._aliases: dict[str, str] = {}
        self._state = ReplState.IDLE
        self._multi_line_buffer: list[str] = []
        self._session_data: dict[str, Any] = {}
        self._hooks: dict[str, list[Callable]] = {
            "pre_command": [],
            "post_command": [],
            "on_error": [],
            "on_exit": [],
        }

        # Register built-in commands
        self._register_builtin_commands()

    def _register_builtin_commands(self) -> None:
        """Register built-in REPL commands."""
        # Help command
        self.register_command(ReplCommand(
            name="help",
            description="Show help for commands",
            usage="help [command]",
            aliases=["?", "h"],
            handler=self._cmd_help,
        ))

        # Exit command
        self.register_command(ReplCommand(
            name="exit",
            description="Exit the REPL",
            usage="exit",
            aliases=["quit", "q"],
            handler=self._cmd_exit,
        ))

        # Clear command
        self.register_command(ReplCommand(
            name="clear",
            description="Clear the screen",
            usage="clear",
            aliases=["cls"],
            handler=self._cmd_clear,
        ))

        # History command
        self.register_command(ReplCommand(
            name="history",
            description="Show command history",
            usage="history [n]",
            aliases=["hist"],
            handler=self._cmd_history,
        ))

        # Set command for session variables
        self.register_command(ReplCommand(
            name="set",
            description="Set a session variable",
            usage="set <name> <value>",
            handler=self._cmd_set,
        ))

        # Get command for session variables
        self.register_command(ReplCommand(
            name="get",
            description="Get a session variable",
            usage="get <name>",
            handler=self._cmd_get,
        ))

    def register_command(self, command: ReplCommand) -> None:
        """Register a command.

        Args:
            command: Command to register
        """
        name = command.name.lower() if self.config.case_insensitive else command.name
        self._commands[name] = command

        # Register aliases
        if self.config.enable_aliases:
            for alias in command.aliases:
                alias_name = alias.lower() if self.config.case_insensitive else alias
                self._aliases[alias_name] = name

    def unregister_command(self, name: str) -> bool:
        """Unregister a command.

        Args:
            name: Command name

        Returns:
            True if command was removed
        """
        name = name.lower() if self.config.case_insensitive else name
        if name in self._commands:
            del self._commands[name]
            # Remove aliases
            self._aliases = {a: c for a, c in self._aliases.items() if c != name}
            return True
        return False

    def get_command(self, name: str) -> ReplCommand | None:
        """Get a command by name or alias.

        Args:
            name: Command name or alias

        Returns:
            Command or None if not found
        """
        name = name.lower() if self.config.case_insensitive else name

        # Check direct command
        if name in self._commands:
            return self._commands[name]

        # Check alias
        if name in self._aliases:
            return self._commands.get(self._aliases[name])

        return None

    def list_commands(self) -> list[str]:
        """List all registered commands.

        Returns:
            List of command names
        """
        return list(self._commands.keys())

    def add_hook(self, event: str, callback: Callable) -> None:
        """Add a hook for an event.

        Args:
            event: Event name (pre_command, post_command, on_error, on_exit)
            callback: Callback function
        """
        if event in self._hooks:
            self._hooks[event].append(callback)

    def _run_hooks(self, event: str, *args, **kwargs) -> None:
        """Run hooks for an event.

        Args:
            event: Event name
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        for callback in self._hooks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                if self.config.debug:
                    print(f"Hook error: {e}")

    def parse_input(self, line: str) -> tuple[str, list[str]]:
        """Parse input line into command and arguments.

        Args:
            line: Input line

        Returns:
            Tuple of (command_name, arguments)
        """
        line = line.strip()
        if not line:
            return "", []

        try:
            parts = shlex.split(line)
        except ValueError:
            # Fallback to simple split for unbalanced quotes
            parts = line.split()

        if not parts:
            return "", []

        return parts[0], parts[1:]

    def execute(self, line: str) -> ReplResult:
        """Execute a command line.

        Args:
            line: Command line input

        Returns:
            Execution result
        """
        # Handle multi-line mode
        if self._state == ReplState.MULTI_LINE:
            return self._handle_multi_line(line)

        cmd_name, args = self.parse_input(line)

        if not cmd_name:
            return ReplResult(success=True)

        # Get command
        command = self.get_command(cmd_name)
        if not command:
            return ReplResult(
                success=False,
                error=f"Unknown command: {cmd_name}. Type 'help' for available commands.",
            )

        # Run pre-command hooks
        self._run_hooks("pre_command", cmd_name, args, self._session_data)

        # Execute command
        try:
            if command.handler:
                result = command.handler(args, self._session_data)
            else:
                result = ReplResult(
                    success=False,
                    error=f"Command '{cmd_name}' has no handler",
                )
        except Exception as e:
            result = ReplResult(
                success=False,
                error=f"Error executing '{cmd_name}': {e}",
            )
            self._run_hooks("on_error", cmd_name, args, e)

        # Update state if needed
        if result.state_change:
            self._state = result.state_change

        # Run post-command hooks
        self._run_hooks("post_command", cmd_name, args, result)

        return result

    def _handle_multi_line(self, line: str) -> ReplResult:
        """Handle multi-line input mode.

        Args:
            line: Input line

        Returns:
            Execution result
        """
        if line.strip() == self.config.multi_line_end:
            # End multi-line mode
            full_input = "\n".join(self._multi_line_buffer)
            self._multi_line_buffer = []
            self._state = ReplState.IDLE
            return self.execute(full_input)
        else:
            self._multi_line_buffer.append(line)
            return ReplResult(success=True, state_change=ReplState.MULTI_LINE)

    def start(self) -> None:
        """Start the REPL session."""
        print(self.config.welcome_message)
        self._state = ReplState.RUNNING

        while self._state not in (ReplState.EXITING,):
            try:
                # Get prompt
                if self._state == ReplState.MULTI_LINE:
                    prompt = self.config.continue_prompt
                else:
                    prompt = self.config.prompt

                # Read input
                line = input(prompt)

                # Execute
                result = self.execute(line)

                # Output result
                if result.output:
                    print(result.output)
                if result.error:
                    print(f"Error: {result.error}")

                # Check for exit
                if result.exit:
                    self._state = ReplState.EXITING

            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
                if self._state == ReplState.MULTI_LINE:
                    self._multi_line_buffer = []
                    self._state = ReplState.IDLE
            except EOFError:
                print()
                break

        # Run exit hooks
        self._run_hooks("on_exit", self._session_data)
        print(self.config.exit_message)

    # Built-in command handlers
    def _cmd_help(self, args: list[str], session: dict) -> ReplResult:
        """Handle help command."""
        if args:
            # Help for specific command
            cmd = self.get_command(args[0])
            if cmd:
                return ReplResult(success=True, output=cmd.get_help())
            else:
                return ReplResult(success=False, error=f"Unknown command: {args[0]}")
        else:
            # List all commands
            lines = ["Available commands:"]
            for name, cmd in sorted(self._commands.items()):
                lines.append(f"  {name}: {cmd.description}")
            lines.append("\nType 'help <command>' for detailed help.")
            return ReplResult(success=True, output="\n".join(lines))

    def _cmd_exit(self, args: list[str], session: dict) -> ReplResult:
        """Handle exit command."""
        return ReplResult(success=True, exit=True)

    def _cmd_clear(self, args: list[str], session: dict) -> ReplResult:
        """Handle clear command."""
        import os
        os.system("cls" if os.name == "nt" else "clear")
        return ReplResult(success=True)

    def _cmd_history(self, args: list[str], session: dict) -> ReplResult:
        """Handle history command."""
        # History is handled by the history module
        return ReplResult(
            success=True,
            output="History command requires history module integration.",
        )

    def _cmd_set(self, args: list[str], session: dict) -> ReplResult:
        """Handle set command."""
        if len(args) < 2:
            return ReplResult(
                success=False,
                error="Usage: set <name> <value>",
            )
        name = args[0]
        value = " ".join(args[1:])
        session[name] = value
        return ReplResult(success=True, output=f"Set {name} = {value}")

    def _cmd_get(self, args: list[str], session: dict) -> ReplResult:
        """Handle get command."""
        if not args:
            return ReplResult(
                success=False,
                error="Usage: get <name>",
            )
        name = args[0]
        if name in session:
            return ReplResult(success=True, output=f"{name} = {session[name]}")
        else:
            return ReplResult(success=False, error=f"Variable '{name}' not set")


def create_repl(config: ReplConfig | None = None) -> CLIRepl:
    """Create a REPL instance.

    Args:
        config: REPL configuration

    Returns:
        CLIRepl instance
    """
    return CLIRepl(config)
