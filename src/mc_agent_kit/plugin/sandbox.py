"""Plugin sandbox for secure plugin execution."""

import ast
import logging
import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SandboxPermission(Enum):
    """Sandbox permission levels."""

    FULL = "full"  # Full system access
    STANDARD = "standard"  # Standard plugin access
    RESTRICTED = "restricted"  # Minimal access


class RestrictedOperationError(Exception):
    """Raised when a restricted operation is attempted."""

    pass


@dataclass
class SandboxConfig:
    """Configuration for plugin sandbox.

    Attributes:
        permission: Permission level
        allowed_modules: Whitelist of allowed modules
        blocked_modules: Blacklist of blocked modules
        allowed_paths: Whitelist of allowed file paths
        blocked_paths: Blacklist of blocked file paths
        max_memory_mb: Maximum memory usage in MB
        max_execution_time_s: Maximum execution time in seconds
        allow_network: Allow network access
        allow_subprocess: Allow subprocess execution
        allow_file_write: Allow file write operations
    """

    permission: SandboxPermission = SandboxPermission.STANDARD
    allowed_modules: list[str] = field(default_factory=list)
    blocked_modules: list[str] = field(default_factory=lambda: [
        "os",
        "subprocess",
        "sys",
        "builtins",
        "importlib",
        "ctypes",
        "multiprocessing",
    ])
    allowed_paths: list[str] = field(default_factory=list)
    blocked_paths: list[str] = field(default_factory=list)
    max_memory_mb: int = 256
    max_execution_time_s: float = 30.0
    allow_network: bool = False
    allow_subprocess: bool = False
    allow_file_write: bool = False

    @classmethod
    def full_access(cls) -> "SandboxConfig":
        """Create config with full access."""
        return cls(permission=SandboxPermission.FULL, blocked_modules=[], allow_network=True, allow_subprocess=True, allow_file_write=True)

    @classmethod
    def restricted(cls) -> "SandboxConfig":
        """Create restricted config."""
        return cls(permission=SandboxPermission.RESTRICTED, allow_network=False, allow_subprocess=False, allow_file_write=False)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "permission": self.permission.value,
            "allowed_modules": self.allowed_modules,
            "blocked_modules": self.blocked_modules,
            "allowed_paths": self.allowed_paths,
            "blocked_paths": self.blocked_paths,
            "max_memory_mb": self.max_memory_mb,
            "max_execution_time_s": self.max_execution_time_s,
            "allow_network": self.allow_network,
            "allow_subprocess": self.allow_subprocess,
            "allow_file_write": self.allow_file_write,
        }


@dataclass
class SandboxViolation:
    """Record of a sandbox violation.

    Attributes:
        operation: Operation that was attempted
        module: Module involved (if applicable)
        path: Path involved (if applicable)
        message: Description of the violation
    """

    operation: str
    module: str | None = None
    path: str | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation": self.operation,
            "module": self.module,
            "path": self.path,
            "message": self.message,
        }


class SandboxContext:
    """Context manager for sandboxed execution."""

    def __init__(self, config: SandboxConfig) -> None:
        """Initialize sandbox context.

        Args:
            config: Sandbox configuration
        """
        self.config = config
        self._violations: list[SandboxViolation] = []
        self._original_import: Any = None
        self._original_open: Any = None
        self._thread_local = threading.local()

    def __enter__(self) -> "SandboxContext":
        """Enter sandbox context."""
        if self.config.permission == SandboxPermission.FULL:
            return self

        # Store original functions
        import builtins

        self._original_import = builtins.__import__
        self._original_open = builtins.open

        # Install sandboxed versions
        builtins.__import__ = self._sandboxed_import
        builtins.open = self._sandboxed_open

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit sandbox context."""
        if self.config.permission == SandboxPermission.FULL:
            return

        # Restore original functions
        import builtins

        if self._original_import:
            builtins.__import__ = self._original_import
        if self._original_open:
            builtins.open = self._original_open

    def _sandboxed_import(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Sandboxed import function."""
        # Check if module is allowed
        if self.config.allowed_modules and name not in self.config.allowed_modules:
            violation = SandboxViolation(
                operation="import",
                module=name,
                message=f"Module '{name}' is not in allowed list",
            )
            self._violations.append(violation)
            raise RestrictedOperationError(f"Import of module '{name}' is not allowed")

        # Check if module is blocked
        root_module = name.split(".")[0]
        if root_module in self.config.blocked_modules:
            violation = SandboxViolation(
                operation="import",
                module=name,
                message=f"Module '{root_module}' is blocked",
            )
            self._violations.append(violation)
            raise RestrictedOperationError(f"Import of module '{root_module}' is blocked")

        return self._original_import(name, *args, **kwargs)

    def _sandboxed_open(self, file: Any, *args: Any, **kwargs: Any) -> Any:
        """Sandboxed open function."""
        file_path = Path(file) if not isinstance(file, Path) else file

        # Check write access
        mode = args[0] if args else kwargs.get("mode", "r")
        if "w" in mode or "a" in mode or "x" in mode:
            if not self.config.allow_file_write:
                violation = SandboxViolation(
                    operation="file_write",
                    path=str(file_path),
                    message="File write operations are not allowed",
                )
                self._violations.append(violation)
                raise RestrictedOperationError("File write operations are not allowed")

        # Check path restrictions
        if self.config.blocked_paths:
            for blocked in self.config.blocked_paths:
                if str(file_path).startswith(blocked):
                    violation = SandboxViolation(
                        operation="file_access",
                        path=str(file_path),
                        message=f"Path '{file_path}' is blocked",
                    )
                    self._violations.append(violation)
                    raise RestrictedOperationError(f"Access to '{file_path}' is blocked")

        if self.config.allowed_paths:
            allowed = False
            for allowed_path in self.config.allowed_paths:
                if str(file_path).startswith(allowed_path):
                    allowed = True
                    break
            if not allowed:
                violation = SandboxViolation(
                    operation="file_access",
                    path=str(file_path),
                    message=f"Path '{file_path}' is not in allowed list",
                )
                self._violations.append(violation)
                raise RestrictedOperationError(f"Access to '{file_path}' is not allowed")

        return self._original_open(file, *args, **kwargs)

    def get_violations(self) -> list[SandboxViolation]:
        """Get recorded violations."""
        return list(self._violations)

    def clear_violations(self) -> None:
        """Clear recorded violations."""
        self._violations.clear()


class CodeValidator:
    """Validates code for security issues before execution."""

    DANGEROUS_FUNCTIONS = {
        "eval",
        "exec",
        "compile",
        "execfile",
        "__import__",
    }

    DANGEROUS_ATTRIBUTES = {
        "__class__",
        "__bases__",
        "__subclasses__",
        "__mro__",
        "__globals__",
        "__code__",
        "__builtins__",
    }

    def __init__(self, config: SandboxConfig) -> None:
        """Initialize code validator.

        Args:
            config: Sandbox configuration
        """
        self.config = config

    def validate(self, code: str) -> tuple[bool, list[str]]:
        """Validate code for security issues.

        Args:
            code: Python code to validate

        Returns:
            Tuple of (is_valid, list of issues found)
        """
        if self.config.permission == SandboxPermission.FULL:
            return True, []

        issues: list[str] = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, [f"Syntax error: {e}"]

        # Check for dangerous function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)
                if func_name in self.DANGEROUS_FUNCTIONS:
                    issues.append(f"Dangerous function call: {func_name}")

            # Check for dangerous attribute access
            if isinstance(node, ast.Attribute):
                if node.attr in self.DANGEROUS_ATTRIBUTES:
                    issues.append(f"Dangerous attribute access: {node.attr}")

            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in self.config.blocked_modules:
                        issues.append(f"Blocked import: {alias.name}")

            if isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]
                    if root in self.config.blocked_modules:
                        issues.append(f"Blocked import: {node.module}")

        return len(issues) == 0, issues

    def _get_func_name(self, node: ast.expr) -> str:
        """Get function name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return ""


class PluginSandbox:
    """Main sandbox class for plugin execution."""

    def __init__(self, config: SandboxConfig | None = None) -> None:
        """Initialize plugin sandbox.

        Args:
            config: Sandbox configuration, defaults to standard
        """
        self.config = config or SandboxConfig()
        self._validator = CodeValidator(self.config)

    def validate_code(self, code: str) -> tuple[bool, list[str]]:
        """Validate code before execution.

        Args:
            code: Code to validate

        Returns:
            Tuple of (is_valid, issues)
        """
        return self._validator.validate(code)

    def execute_in_sandbox(
        self, func: Any, *args: Any, **kwargs: Any
    ) -> tuple[Any, list[SandboxViolation]]:
        """Execute a function in the sandbox.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Tuple of (result, violations)
        """
        with SandboxContext(self.config) as ctx:
            result = func(*args, **kwargs)
            violations = ctx.get_violations()
            return result, violations

    def check_module_allowed(self, module_name: str) -> bool:
        """Check if a module is allowed.

        Args:
            module_name: Module name to check

        Returns:
            True if allowed, False otherwise
        """
        if self.config.permission == SandboxPermission.FULL:
            return True

        # Check whitelist
        if self.config.allowed_modules and module_name not in self.config.allowed_modules:
            return False

        # Check blacklist
        root = module_name.split(".")[0]
        if root in self.config.blocked_modules:
            return False

        return True

    def check_path_allowed(self, path: Path | str, write: bool = False) -> bool:
        """Check if a path is allowed for access.

        Args:
            path: Path to check
            write: Whether write access is needed

        Returns:
            True if allowed, False otherwise
        """
        if self.config.permission == SandboxPermission.FULL:
            return True

        # Check write permission
        if write and not self.config.allow_file_write:
            return False

        path_str = str(path)

        # Check blacklist
        for blocked in self.config.blocked_paths:
            if path_str.startswith(blocked):
                return False

        # Check whitelist
        if self.config.allowed_paths:
            for allowed in self.config.allowed_paths:
                if path_str.startswith(allowed):
                    return True
            return False

        return True

    def get_config(self) -> SandboxConfig:
        """Get current sandbox configuration."""
        return self.config

    def set_config(self, config: SandboxConfig) -> None:
        """Set sandbox configuration.

        Args:
            config: New configuration
        """
        self.config = config
        self._validator = CodeValidator(config)