"""Plugin version compatibility checking."""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class VersionCompatibility(Enum):
    """Version compatibility level."""

    COMPATIBLE = "compatible"
    MINOR_ISSUES = "minor_issues"
    MAJOR_ISSUES = "major_issues"
    INCOMPATIBLE = "incompatible"


@dataclass
class Version:
    """Semantic version representation.

    Attributes:
        major: Major version number
        minor: Minor version number
        patch: Patch version number
        prerelease: Prerelease identifier (e.g., 'alpha', 'beta')
        build: Build metadata
    """

    major: int = 0
    minor: int = 0
    patch: int = 0
    prerelease: str | None = None
    build: str | None = None

    @classmethod
    def parse(cls, version_str: str) -> "Version":
        """Parse version string.

        Supports formats:
        - 1.0.0
        - 1.0.0-alpha
        - 1.0.0-alpha.1
        - 1.0.0+build
        - 1.0.0-alpha+build

        Args:
            version_str: Version string to parse

        Returns:
            Version object

        Raises:
            ValueError: If version string is invalid
        """
        # Pattern for semantic versioning
        pattern = r'^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:-([a-zA-Z0-9.]+))?(?:\+([a-zA-Z0-9.]+))?$'
        match = re.match(pattern, version_str.strip())
        if not match:
            raise ValueError(f"Invalid version string: {version_str}")

        major = int(match.group(1))
        minor = int(match.group(2)) if match.group(2) else 0
        patch = int(match.group(3)) if match.group(3) else 0
        prerelease = match.group(4)
        build = match.group(5)

        return cls(major=major, minor=minor, patch=patch, prerelease=prerelease, build=build)

    def __str__(self) -> str:
        """Convert to string."""
        result = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            result += f"-{self.prerelease}"
        if self.build:
            result += f"+{self.build}"
        return result

    def __lt__(self, other: "Version") -> bool:
        """Compare versions."""
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        # Prerelease versions have lower precedence
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
        if self.prerelease and other.prerelease:
            return self.prerelease < other.prerelease
        return False

    def __le__(self, other: "Version") -> bool:
        return self == other or self < other

    def __gt__(self, other: "Version") -> bool:
        return not self <= other

    def __ge__(self, other: "Version") -> bool:
        return not self < other

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return False
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.prerelease == other.prerelease
        )

    def __hash__(self) -> int:
        return hash(str(self))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "prerelease": self.prerelease,
            "build": self.build,
            "string": str(self),
        }


@dataclass
class VersionRange:
    """Version range specification.

    Supports formats:
    - Exact: "1.0.0"
    - Greater than: ">1.0.0"
    - Greater or equal: ">=1.0.0"
    - Less than: "<1.0.0"
    - Less or equal: "<=1.0.0"
    - Range: ">=1.0.0,<2.0.0"
    - Caret: "^1.0.0" (compatible with 1.x.x)
    - Tilde: "~1.0.0" (compatible with 1.0.x)
    """

    constraints: list[tuple[str, Version]] = field(default_factory=list)

    @classmethod
    def parse(cls, range_str: str) -> "VersionRange":
        """Parse version range string.

        Args:
            range_str: Version range string

        Returns:
            VersionRange object
        """
        constraints: list[tuple[str, Version]] = []

        # Split by comma
        parts = [p.strip() for p in range_str.split(",")]

        for part in parts:
            part = part.strip()

            # Handle caret (^) - compatible with major.minor
            if part.startswith("^"):
                version = Version.parse(part[1:])
                # Allow same major, any minor/patch >= given
                constraints.append((">=", version))
                # Upper bound is next major
                upper = Version(major=version.major + 1, minor=0, patch=0)
                constraints.append(("<", upper))

            # Handle tilde (~) - compatible with major.minor
            elif part.startswith("~"):
                version = Version.parse(part[1:])
                # Allow same major.minor, any patch >= given
                constraints.append((">=", version))
                # Upper bound is next minor
                upper = Version(major=version.major, minor=version.minor + 1, patch=0)
                constraints.append(("<", upper))

            # Handle comparison operators
            elif part.startswith(">="):
                constraints.append((">=", Version.parse(part[2:])))
            elif part.startswith("<="):
                constraints.append(("<=", Version.parse(part[2:])))
            elif part.startswith(">"):
                constraints.append((">", Version.parse(part[1:])))
            elif part.startswith("<"):
                constraints.append(("<", Version.parse(part[1:])))
            elif part.startswith("=="):
                constraints.append(("==", Version.parse(part[2:])))
            else:
                # Exact match
                constraints.append(("==", Version.parse(part)))

        return cls(constraints=constraints)

    def contains(self, version: Version) -> bool:
        """Check if version is within range.

        Args:
            version: Version to check

        Returns:
            True if version is within range
        """
        for op, constraint_version in self.constraints:
            if op == "==" and version != constraint_version:
                return False
            elif op == ">" and version <= constraint_version:
                return False
            elif op == ">=" and version < constraint_version:
                return False
            elif op == "<" and version >= constraint_version:
                return False
            elif op == "<=" and version > constraint_version:
                return False

        return True

    def __str__(self) -> str:
        """Convert to string."""
        parts = []
        for op, version in self.constraints:
            parts.append(f"{op}{version}")
        return ",".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "constraints": [[op, str(v)] for op, v in self.constraints],
            "string": str(self),
        }


@dataclass
class CompatibilityReport:
    """Report of version compatibility check.

    Attributes:
        compatibility: Overall compatibility level
        plugin_version: Plugin version
        core_version: Core system version
        api_version: API version
        issues: List of compatibility issues
        recommendations: List of recommendations
    """

    compatibility: VersionCompatibility
    plugin_version: Version
    core_version: Version
    api_version: Version | None = None
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "compatibility": self.compatibility.value,
            "plugin_version": str(self.plugin_version),
            "core_version": str(self.core_version),
            "api_version": str(self.api_version) if self.api_version else None,
            "issues": self.issues,
            "recommendations": self.recommendations,
        }


class VersionChecker:
    """Version compatibility checker for plugins."""

    def __init__(
        self,
        core_version: str = "1.0.0",
        api_version: str | None = None,
    ) -> None:
        """Initialize version checker.

        Args:
            core_version: Current core system version
            api_version: Current API version
        """
        self.core_version = Version.parse(core_version)
        self.api_version = Version.parse(api_version) if api_version else None

    def check_compatibility(
        self,
        plugin_version: str,
        min_core_version: str | None = None,
        max_core_version: str | None = None,
        supported_api_versions: list[str] | None = None,
    ) -> CompatibilityReport:
        """Check plugin version compatibility.

        Args:
            plugin_version: Plugin version
            min_core_version: Minimum required core version
            max_core_version: Maximum supported core version
            supported_api_versions: List of supported API versions

        Returns:
            CompatibilityReport with results
        """
        plugin_v = Version.parse(plugin_version)
        issues: list[str] = []
        recommendations: list[str] = []

        # Check core version constraints
        if min_core_version:
            min_v = Version.parse(min_core_version)
            if self.core_version < min_v:
                issues.append(
                    f"Plugin requires core version >= {min_v}, "
                    f"but current is {self.core_version}"
                )
                recommendations.append(
                    f"Upgrade core system to version {min_v} or higher"
                )

        if max_core_version:
            max_v = Version.parse(max_core_version)
            if self.core_version > max_v:
                issues.append(
                    f"Plugin supports core version <= {max_v}, "
                    f"but current is {self.core_version}"
                )
                recommendations.append(
                    f"Use plugin version compatible with core {self.core_version}"
                )

        # Check API version compatibility
        if self.api_version and supported_api_versions:
            api_compatible = False
            for supported in supported_api_versions:
                try:
                    supported_range = VersionRange.parse(supported)
                    if supported_range.contains(self.api_version):
                        api_compatible = True
                        break
                except ValueError:
                    continue

            if not api_compatible:
                issues.append(
                    f"Plugin does not support API version {self.api_version}"
                )
                recommendations.append(
                    f"Use plugin version that supports API {self.api_version}"
                )

        # Determine overall compatibility
        if not issues:
            compatibility = VersionCompatibility.COMPATIBLE
        elif any("requires" in i or "does not support" in i or "supports core version" in i for i in issues):
            compatibility = VersionCompatibility.INCOMPATIBLE
        else:
            compatibility = VersionCompatibility.MAJOR_ISSUES

        return CompatibilityReport(
            compatibility=compatibility,
            plugin_version=plugin_v,
            core_version=self.core_version,
            api_version=self.api_version,
            issues=issues,
            recommendations=recommendations,
        )

    def check_version_range(
        self,
        version: str,
        range_str: str,
    ) -> bool:
        """Check if version is within a range.

        Args:
            version: Version to check
            range_str: Version range specification

        Returns:
            True if version is within range
        """
        try:
            v = Version.parse(version)
            r = VersionRange.parse(range_str)
            return r.contains(v)
        except ValueError:
            return False

    def compare_versions(self, v1: str, v2: str) -> int:
        """Compare two versions.

        Args:
            v1: First version
            v2: Second version

        Returns:
            -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
        """
        version1 = Version.parse(v1)
        version2 = Version.parse(v2)

        if version1 < version2:
            return -1
        elif version1 > version2:
            return 1
        return 0

    def get_latest_version(self, versions: list[str]) -> str:
        """Get the latest version from a list.

        Args:
            versions: List of version strings

        Returns:
            Latest version string
        """
        parsed = [Version.parse(v) for v in versions]
        return str(max(parsed))


def check_plugin_version(
    plugin_version: str,
    core_version: str = "1.0.0",
    min_core: str | None = None,
    max_core: str | None = None,
) -> CompatibilityReport:
    """Convenience function to check plugin version compatibility.

    Args:
        plugin_version: Plugin version
        core_version: Current core version
        min_core: Minimum required core version
        max_core: Maximum supported core version

    Returns:
        CompatibilityReport
    """
    checker = VersionChecker(core_version=core_version)
    return checker.check_compatibility(
        plugin_version=plugin_version,
        min_core_version=min_core,
        max_core_version=max_core,
    )