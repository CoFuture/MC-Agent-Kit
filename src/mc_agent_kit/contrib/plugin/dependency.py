"""Plugin dependency management."""

import logging
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .version import Version, VersionRange

logger = logging.getLogger(__name__)


class DependencyType(Enum):
    """Type of dependency."""

    PLUGIN = "plugin"  # Another plugin
    PYTHON = "python"  # Python package
    SYSTEM = "system"  # System-level dependency


class DependencyStatus(Enum):
    """Status of a dependency."""

    SATISFIED = "satisfied"  # Dependency is met
    MISSING = "missing"  # Dependency not found
    VERSION_MISMATCH = "version_mismatch"  # Wrong version installed
    ERROR = "error"  # Error checking dependency


@dataclass
class Dependency:
    """Plugin dependency specification.

    Attributes:
        name: Dependency name
        type: Dependency type
        version_range: Version requirement
        optional: Whether dependency is optional
        description: Description of why dependency is needed
        install_hint: Hint for installing the dependency
    """

    name: str
    type: DependencyType = DependencyType.PYTHON
    version_range: str | None = None
    optional: bool = False
    description: str = ""
    install_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "version_range": self.version_range,
            "optional": self.optional,
            "description": self.description,
            "install_hint": self.install_hint,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Dependency":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            type=DependencyType(data.get("type", "python")),
            version_range=data.get("version_range"),
            optional=data.get("optional", False),
            description=data.get("description", ""),
            install_hint=data.get("install_hint", ""),
        )


@dataclass
class DependencyCheckResult:
    """Result of checking a dependency.

    Attributes:
        dependency: The checked dependency
        status: Dependency status
        installed_version: Currently installed version (if any)
        required_version: Required version range
        message: Additional message
        install_hint: Hint for installing the dependency
    """

    dependency: Dependency
    status: DependencyStatus
    installed_version: str | None = None
    required_version: str | None = None
    message: str = ""
    install_hint: str = ""

    @property
    def is_satisfied(self) -> bool:
        """Check if dependency is satisfied."""
        return self.status == DependencyStatus.SATISFIED

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dependency": self.dependency.to_dict(),
            "status": self.status.value,
            "installed_version": self.installed_version,
            "required_version": self.required_version,
            "message": self.message,
            "install_hint": self.install_hint,
            "is_satisfied": self.is_satisfied,
        }


@dataclass
class DependencyReport:
    """Report of all dependency checks.

    Attributes:
        results: List of check results
        all_satisfied: Whether all dependencies are satisfied
        required_missing: List of missing required dependencies
        optional_missing: List of missing optional dependencies
    """

    results: list[DependencyCheckResult] = field(default_factory=list)

    @property
    def all_satisfied(self) -> bool:
        """Check if all required dependencies are satisfied."""
        return all(
            r.is_satisfied or r.dependency.optional
            for r in self.results
        )

    @property
    def required_missing(self) -> list[DependencyCheckResult]:
        """Get missing required dependencies."""
        return [
            r for r in self.results
            if not r.is_satisfied and not r.dependency.optional
        ]

    @property
    def optional_missing(self) -> list[DependencyCheckResult]:
        """Get missing optional dependencies."""
        return [
            r for r in self.results
            if not r.is_satisfied and r.dependency.optional
        ]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "results": [r.to_dict() for r in self.results],
            "all_satisfied": self.all_satisfied,
            "required_missing": [r.to_dict() for r in self.required_missing],
            "optional_missing": [r.to_dict() for r in self.optional_missing],
        }


class DependencyManager:
    """Manager for plugin dependencies."""

    def __init__(self) -> None:
        """Initialize dependency manager."""
        self._installed_packages: dict[str, str] | None = None

    def check_dependency(self, dependency: Dependency) -> DependencyCheckResult:
        """Check a single dependency.

        Args:
            dependency: Dependency to check

        Returns:
            DependencyCheckResult with status
        """
        if dependency.type == DependencyType.PYTHON:
            return self._check_python_dependency(dependency)
        elif dependency.type == DependencyType.PLUGIN:
            return self._check_plugin_dependency(dependency)
        else:
            return DependencyCheckResult(
                dependency=dependency,
                status=DependencyStatus.ERROR,
                message=f"Unknown dependency type: {dependency.type}",
            )

    def check_dependencies(
        self, dependencies: list[Dependency]
    ) -> DependencyReport:
        """Check multiple dependencies.

        Args:
            dependencies: List of dependencies to check

        Returns:
            DependencyReport with all results
        """
        results = [self.check_dependency(dep) for dep in dependencies]
        return DependencyReport(results=results)

    def _check_python_dependency(
        self, dependency: Dependency
    ) -> DependencyCheckResult:
        """Check a Python package dependency.

        Args:
            dependency: Python dependency to check

        Returns:
            DependencyCheckResult
        """
        try:
            # Get installed version
            import importlib.metadata as metadata

            installed_version = metadata.version(dependency.name)
        except metadata.PackageNotFoundError:
            installed_version = None
        except Exception as e:
            return DependencyCheckResult(
                dependency=dependency,
                status=DependencyStatus.ERROR,
                message=f"Error checking package: {e}",
            )

        if not installed_version:
            return DependencyCheckResult(
                dependency=dependency,
                status=DependencyStatus.MISSING,
                message=f"Package '{dependency.name}' is not installed",
                install_hint=dependency.install_hint
                or f"pip install {dependency.name}",
            )

        # Check version constraint
        if dependency.version_range:
            try:
                version = Version.parse(installed_version)
                range_spec = VersionRange.parse(dependency.version_range)

                if not range_spec.contains(version):
                    return DependencyCheckResult(
                        dependency=dependency,
                        status=DependencyStatus.VERSION_MISMATCH,
                        installed_version=installed_version,
                        required_version=dependency.version_range,
                        message=f"Version mismatch: {dependency.name} "
                        f"is {installed_version}, but {dependency.version_range} required",
                    )
            except ValueError as e:
                logger.warning(
                    "Invalid version specification for %s: %s",
                    dependency.name, e
                )

        return DependencyCheckResult(
            dependency=dependency,
            status=DependencyStatus.SATISFIED,
            installed_version=installed_version,
            required_version=dependency.version_range,
        )

    def _check_plugin_dependency(
        self, dependency: Dependency
    ) -> DependencyCheckResult:
        """Check a plugin dependency.

        This is a placeholder - actual implementation would check
        the plugin registry.

        Args:
            dependency: Plugin dependency to check

        Returns:
            DependencyCheckResult
        """
        # Placeholder - would check against plugin registry
        return DependencyCheckResult(
            dependency=dependency,
            status=DependencyStatus.MISSING,
            message=f"Plugin '{dependency.name}' check not implemented",
        )

    def install_python_package(
        self,
        package: str,
        version: str | None = None,
        upgrade: bool = False,
    ) -> tuple[bool, str]:
        """Install a Python package.

        Args:
            package: Package name
            version: Optional version specification
            upgrade: Whether to upgrade if already installed

        Returns:
            Tuple of (success, message)
        """
        try:
            # Build pip command
            spec = f"{package}=={version}" if version else package
            cmd = [sys.executable, "-m", "pip", "install"]

            if upgrade:
                cmd.append("--upgrade")

            cmd.append(spec)

            # Run pip
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                return True, f"Successfully installed {spec}"
            else:
                return False, f"Failed to install {spec}: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, f"Installation timed out for {spec}"
        except Exception as e:
            return False, f"Error installing {spec}: {e}"

    def get_install_commands(
        self, report: DependencyReport
    ) -> list[str]:
        """Get install commands for missing dependencies.

        Args:
            report: Dependency report

        Returns:
            List of install commands
        """
        commands: list[str] = []

        for result in report.required_missing:
            if result.dependency.type == DependencyType.PYTHON:
                pkg = result.dependency.name
                if result.dependency.version_range:
                    # Extract minimum version from range
                    commands.append(f"pip install '{pkg}{result.dependency.version_range}'")
                else:
                    commands.append(f"pip install {pkg}")

        return commands

    def get_missing_packages(
        self, dependencies: list[Dependency]
    ) -> list[Dependency]:
        """Get list of missing Python packages.

        Args:
            dependencies: List of dependencies

        Returns:
            List of missing Python package dependencies
        """
        missing: list[Dependency] = []

        for dep in dependencies:
            if dep.type == DependencyType.PYTHON:
                result = self.check_dependency(dep)
                if result.status == DependencyStatus.MISSING:
                    missing.append(dep)

        return missing

    def get_installed_packages(self) -> dict[str, str]:
        """Get all installed Python packages.

        Returns:
            Dictionary of package name to version
        """
        if self._installed_packages is not None:
            return self._installed_packages

        try:
            import importlib.metadata as metadata

            packages = {}
            for dist in metadata.distributions():
                name = dist.metadata.get("Name", "")
                version = dist.metadata.get("Version", "")
                if name and version:
                    packages[name.lower()] = version

            self._installed_packages = packages
            return packages

        except Exception as e:
            logger.error("Error getting installed packages: %s", e)
            return {}

    def refresh_installed_packages(self) -> None:
        """Refresh the cache of installed packages."""
        self._installed_packages = None
        self.get_installed_packages()


def check_python_package(package: str, version_range: str | None = None) -> DependencyCheckResult:
    """Convenience function to check a Python package.

    Args:
        package: Package name
        version_range: Optional version requirement

    Returns:
        DependencyCheckResult
    """
    manager = DependencyManager()
    dep = Dependency(
        name=package,
        type=DependencyType.PYTHON,
        version_range=version_range,
    )
    return manager.check_dependency(dep)
