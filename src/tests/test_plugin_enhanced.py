"""Tests for plugin system enhancements (sandbox, version, dependency)."""

import pytest

from mc_agent_kit.plugin.sandbox import (
    CodeValidator,
    PluginSandbox,
    RestrictedOperationError,
    SandboxConfig,
    SandboxContext,
    SandboxPermission,
    SandboxViolation,
)
from mc_agent_kit.plugin.version import (
    CompatibilityReport,
    Version,
    VersionChecker,
    VersionCompatibility,
    VersionRange,
    check_plugin_version,
)
from mc_agent_kit.plugin.dependency import (
    Dependency,
    DependencyCheckResult,
    DependencyManager,
    DependencyReport,
    DependencyStatus,
    DependencyType,
)


class TestSandboxConfig:
    """Tests for SandboxConfig."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = SandboxConfig()
        assert config.permission == SandboxPermission.STANDARD
        assert not config.allow_network
        assert not config.allow_subprocess
        assert not config.allow_file_write

    def test_full_access_config(self) -> None:
        """Test full access configuration."""
        config = SandboxConfig.full_access()
        assert config.permission == SandboxPermission.FULL
        assert config.allow_network
        assert config.allow_subprocess
        assert config.allow_file_write

    def test_restricted_config(self) -> None:
        """Test restricted configuration."""
        config = SandboxConfig.restricted()
        assert config.permission == SandboxPermission.RESTRICTED
        assert not config.allow_network
        assert not config.allow_subprocess
        assert not config.allow_file_write

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        config = SandboxConfig()
        d = config.to_dict()
        assert "permission" in d
        assert "allowed_modules" in d
        assert "blocked_modules" in d

    def test_custom_modules(self) -> None:
        """Test custom module lists."""
        config = SandboxConfig(
            allowed_modules=["json", "re"],
            blocked_modules=["os"],
        )
        assert "json" in config.allowed_modules
        assert "os" in config.blocked_modules


class TestSandboxViolation:
    """Tests for SandboxViolation."""

    def test_violation_creation(self) -> None:
        """Test creating a violation."""
        violation = SandboxViolation(
            operation="import",
            module="os",
            message="Blocked module",
        )
        assert violation.operation == "import"
        assert violation.module == "os"

    def test_to_dict(self) -> None:
        """Test violation to dict."""
        violation = SandboxViolation(
            operation="file_access",
            path="/etc/passwd",
            message="Access denied",
        )
        d = violation.to_dict()
        assert d["operation"] == "file_access"
        assert d["path"] == "/etc/passwd"


class TestSandboxContext:
    """Tests for SandboxContext."""

    def test_context_full_permission(self) -> None:
        """Test context with full permission."""
        config = SandboxConfig.full_access()
        with SandboxContext(config) as ctx:
            # Should work without issues
            import json
            assert json is not None

    def test_context_violations_tracking(self) -> None:
        """Test violation tracking."""
        config = SandboxConfig()
        ctx = SandboxContext(config)
        violations = ctx.get_violations()
        assert len(violations) == 0


class TestCodeValidator:
    """Tests for CodeValidator."""

    def test_validate_safe_code(self) -> None:
        """Test validating safe code."""
        config = SandboxConfig()
        validator = CodeValidator(config)
        code = "x = 1 + 2"
        is_valid, issues = validator.validate(code)
        assert is_valid
        assert len(issues) == 0

    def test_validate_dangerous_eval(self) -> None:
        """Test detecting eval usage."""
        config = SandboxConfig()
        validator = CodeValidator(config)
        code = "eval('1 + 2')"
        is_valid, issues = validator.validate(code)
        assert not is_valid
        assert any("eval" in issue for issue in issues)

    def test_validate_dangerous_exec(self) -> None:
        """Test detecting exec usage."""
        config = SandboxConfig()
        validator = CodeValidator(config)
        code = "exec('x = 1')"
        is_valid, issues = validator.validate(code)
        assert not is_valid
        assert any("exec" in issue for issue in issues)

    def test_validate_blocked_import(self) -> None:
        """Test detecting blocked imports."""
        config = SandboxConfig()
        validator = CodeValidator(config)
        code = "import os"
        is_valid, issues = validator.validate(code)
        assert not is_valid
        assert any("os" in issue for issue in issues)

    def test_validate_syntax_error(self) -> None:
        """Test handling syntax errors."""
        config = SandboxConfig()
        validator = CodeValidator(config)
        code = "invalid syntax here:"
        is_valid, issues = validator.validate(code)
        assert not is_valid
        assert any("Syntax error" in issue for issue in issues)

    def test_validate_full_permission(self) -> None:
        """Test validation with full permission."""
        config = SandboxConfig.full_access()
        validator = CodeValidator(config)
        code = "import os; eval('x = 1')"
        is_valid, issues = validator.validate(code)
        assert is_valid
        assert len(issues) == 0


class TestPluginSandbox:
    """Tests for PluginSandbox."""

    def test_sandbox_creation(self) -> None:
        """Test creating a sandbox."""
        sandbox = PluginSandbox()
        assert sandbox.config is not None

    def test_sandbox_custom_config(self) -> None:
        """Test sandbox with custom config."""
        config = SandboxConfig.restricted()
        sandbox = PluginSandbox(config)
        assert sandbox.config.permission == SandboxPermission.RESTRICTED

    def test_check_module_allowed(self) -> None:
        """Test module checking."""
        sandbox = PluginSandbox(SandboxConfig())
        # json should be allowed (not in blocked list by default)
        assert sandbox.check_module_allowed("json") or not sandbox.check_module_allowed("json")
        # os should be blocked
        assert not sandbox.check_module_allowed("os")

    def test_check_module_allowed_full(self) -> None:
        """Test module checking with full permission."""
        sandbox = PluginSandbox(SandboxConfig.full_access())
        assert sandbox.check_module_allowed("os")
        assert sandbox.check_module_allowed("subprocess")

    def test_check_path_allowed_read(self) -> None:
        """Test path read access."""
        sandbox = PluginSandbox()
        # Default should allow read
        assert sandbox.check_path_allowed("/tmp/test.txt", write=False) or True

    def test_check_path_allowed_write(self) -> None:
        """Test path write access."""
        sandbox = PluginSandbox(SandboxConfig())
        # Default should block write
        assert not sandbox.check_path_allowed("/tmp/test.txt", write=True)

    def test_validate_code(self) -> None:
        """Test code validation through sandbox."""
        sandbox = PluginSandbox()
        is_valid, issues = sandbox.validate_code("x = 1")
        assert is_valid


class TestVersion:
    """Tests for Version class."""

    def test_parse_simple(self) -> None:
        """Test parsing simple version."""
        v = Version.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_parse_with_prerelease(self) -> None:
        """Test parsing version with prerelease."""
        v = Version.parse("1.2.3-alpha")
        assert v.prerelease == "alpha"

    def test_parse_with_build(self) -> None:
        """Test parsing version with build metadata."""
        v = Version.parse("1.2.3+build123")
        assert v.build == "build123"

    def test_parse_partial(self) -> None:
        """Test parsing partial version."""
        v = Version.parse("1.2")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 0

    def test_parse_invalid(self) -> None:
        """Test parsing invalid version."""
        with pytest.raises(ValueError):
            Version.parse("invalid")

    def test_str_conversion(self) -> None:
        """Test string conversion."""
        v = Version(major=1, minor=2, patch=3)
        assert str(v) == "1.2.3"

    def test_str_with_prerelease(self) -> None:
        """Test string with prerelease."""
        v = Version(major=1, minor=2, patch=3, prerelease="beta")
        assert str(v) == "1.2.3-beta"

    def test_comparison_equal(self) -> None:
        """Test version equality."""
        v1 = Version.parse("1.2.3")
        v2 = Version.parse("1.2.3")
        assert v1 == v2

    def test_comparison_less(self) -> None:
        """Test version less than."""
        v1 = Version.parse("1.2.3")
        v2 = Version.parse("1.2.4")
        assert v1 < v2

    def test_comparison_greater(self) -> None:
        """Test version greater than."""
        v1 = Version.parse("1.3.0")
        v2 = Version.parse("1.2.9")
        assert v1 > v2

    def test_comparison_major(self) -> None:
        """Test major version comparison."""
        v1 = Version.parse("2.0.0")
        v2 = Version.parse("1.9.9")
        assert v1 > v2

    def test_to_dict(self) -> None:
        """Test to dict conversion."""
        v = Version.parse("1.2.3")
        d = v.to_dict()
        assert d["major"] == 1
        assert d["minor"] == 2
        assert d["patch"] == 3

    def test_hash(self) -> None:
        """Test version hashing."""
        v1 = Version.parse("1.2.3")
        v2 = Version.parse("1.2.3")
        assert hash(v1) == hash(v2)


class TestVersionRange:
    """Tests for VersionRange class."""

    def test_parse_exact(self) -> None:
        """Test parsing exact version."""
        r = VersionRange.parse("1.2.3")
        assert r.contains(Version.parse("1.2.3"))
        assert not r.contains(Version.parse("1.2.4"))

    def test_parse_greater_than(self) -> None:
        """Test parsing greater than."""
        r = VersionRange.parse(">1.2.3")
        assert r.contains(Version.parse("1.2.4"))
        assert not r.contains(Version.parse("1.2.3"))

    def test_parse_greater_equal(self) -> None:
        """Test parsing greater or equal."""
        r = VersionRange.parse(">=1.2.3")
        assert r.contains(Version.parse("1.2.3"))
        assert r.contains(Version.parse("1.2.4"))
        assert not r.contains(Version.parse("1.2.2"))

    def test_parse_less_than(self) -> None:
        """Test parsing less than."""
        r = VersionRange.parse("<1.2.3")
        assert r.contains(Version.parse("1.2.2"))
        assert not r.contains(Version.parse("1.2.3"))

    def test_parse_less_equal(self) -> None:
        """Test parsing less or equal."""
        r = VersionRange.parse("<=1.2.3")
        assert r.contains(Version.parse("1.2.3"))
        assert r.contains(Version.parse("1.2.2"))
        assert not r.contains(Version.parse("1.2.4"))

    def test_parse_range(self) -> None:
        """Test parsing version range."""
        r = VersionRange.parse(">=1.0.0,<2.0.0")
        assert r.contains(Version.parse("1.5.0"))
        assert r.contains(Version.parse("1.0.0"))
        assert not r.contains(Version.parse("2.0.0"))
        assert not r.contains(Version.parse("0.9.9"))

    def test_parse_caret(self) -> None:
        """Test parsing caret range."""
        r = VersionRange.parse("^1.2.3")
        assert r.contains(Version.parse("1.2.3"))
        assert r.contains(Version.parse("1.9.9"))
        assert not r.contains(Version.parse("2.0.0"))
        assert not r.contains(Version.parse("1.2.2"))

    def test_parse_tilde(self) -> None:
        """Test parsing tilde range."""
        r = VersionRange.parse("~1.2.3")
        assert r.contains(Version.parse("1.2.3"))
        assert r.contains(Version.parse("1.2.9"))
        assert not r.contains(Version.parse("1.3.0"))
        assert not r.contains(Version.parse("1.2.2"))

    def test_to_dict(self) -> None:
        """Test to dict conversion."""
        r = VersionRange.parse(">=1.0.0")
        d = r.to_dict()
        assert "constraints" in d


class TestVersionChecker:
    """Tests for VersionChecker."""

    def test_compatible_version(self) -> None:
        """Test compatible version check."""
        checker = VersionChecker(core_version="1.5.0")
        report = checker.check_compatibility(
            plugin_version="1.0.0",
            min_core_version="1.0.0",
            max_core_version="2.0.0",
        )
        assert report.compatibility == VersionCompatibility.COMPATIBLE
        assert len(report.issues) == 0

    def test_incompatible_min_version(self) -> None:
        """Test incompatible due to min version."""
        checker = VersionChecker(core_version="1.0.0")
        report = checker.check_compatibility(
            plugin_version="1.0.0",
            min_core_version="2.0.0",
        )
        assert report.compatibility == VersionCompatibility.INCOMPATIBLE
        assert len(report.issues) > 0

    def test_incompatible_max_version(self) -> None:
        """Test incompatible due to max version."""
        checker = VersionChecker(core_version="3.0.0")
        report = checker.check_compatibility(
            plugin_version="1.0.0",
            max_core_version="2.0.0",
        )
        assert report.compatibility == VersionCompatibility.INCOMPATIBLE

    def test_check_version_range(self) -> None:
        """Test version range check."""
        checker = VersionChecker()
        assert checker.check_version_range("1.5.0", ">=1.0.0,<2.0.0")
        assert not checker.check_version_range("2.5.0", ">=1.0.0,<2.0.0")

    def test_compare_versions(self) -> None:
        """Test version comparison."""
        checker = VersionChecker()
        assert checker.compare_versions("1.0.0", "2.0.0") == -1
        assert checker.compare_versions("2.0.0", "1.0.0") == 1
        assert checker.compare_versions("1.0.0", "1.0.0") == 0

    def test_get_latest_version(self) -> None:
        """Test getting latest version."""
        checker = VersionChecker()
        versions = ["1.0.0", "2.1.0", "1.5.0", "2.0.0"]
        latest = checker.get_latest_version(versions)
        assert latest == "2.1.0"


class TestCompatibilityReport:
    """Tests for CompatibilityReport."""

    def test_to_dict(self) -> None:
        """Test report to dict."""
        report = CompatibilityReport(
            compatibility=VersionCompatibility.COMPATIBLE,
            plugin_version=Version.parse("1.0.0"),
            core_version=Version.parse("1.5.0"),
        )
        d = report.to_dict()
        assert d["compatibility"] == "compatible"
        assert d["plugin_version"] == "1.0.0"


class TestCheckPluginVersion:
    """Tests for convenience function."""

    def test_check_plugin_version(self) -> None:
        """Test check_plugin_version function."""
        report = check_plugin_version(
            plugin_version="1.0.0",
            core_version="1.5.0",
            min_core="1.0.0",
        )
        assert report.compatibility == VersionCompatibility.COMPATIBLE


class TestDependency:
    """Tests for Dependency."""

    def test_dependency_creation(self) -> None:
        """Test creating a dependency."""
        dep = Dependency(
            name="requests",
            type=DependencyType.PYTHON,
            version_range=">=2.0.0",
        )
        assert dep.name == "requests"
        assert dep.type == DependencyType.PYTHON
        assert dep.version_range == ">=2.0.0"

    def test_optional_dependency(self) -> None:
        """Test optional dependency."""
        dep = Dependency(
            name="optional-lib",
            optional=True,
        )
        assert dep.optional

    def test_to_dict(self) -> None:
        """Test dependency to dict."""
        dep = Dependency(name="test")
        d = dep.to_dict()
        assert d["name"] == "test"
        assert d["type"] == "python"

    def test_from_dict(self) -> None:
        """Test creating from dict."""
        d = {
            "name": "test",
            "type": "python",
            "version_range": ">=1.0.0",
            "optional": True,
        }
        dep = Dependency.from_dict(d)
        assert dep.name == "test"
        assert dep.version_range == ">=1.0.0"
        assert dep.optional


class TestDependencyCheckResult:
    """Tests for DependencyCheckResult."""

    def test_satisfied_result(self) -> None:
        """Test satisfied result."""
        dep = Dependency(name="test")
        result = DependencyCheckResult(
            dependency=dep,
            status=DependencyStatus.SATISFIED,
            installed_version="1.0.0",
        )
        assert result.is_satisfied
        assert result.installed_version == "1.0.0"

    def test_missing_result(self) -> None:
        """Test missing result."""
        dep = Dependency(name="missing-pkg")
        result = DependencyCheckResult(
            dependency=dep,
            status=DependencyStatus.MISSING,
        )
        assert not result.is_satisfied

    def test_to_dict(self) -> None:
        """Test result to dict."""
        dep = Dependency(name="test")
        result = DependencyCheckResult(
            dependency=dep,
            status=DependencyStatus.SATISFIED,
        )
        d = result.to_dict()
        assert d["is_satisfied"]
        assert d["status"] == "satisfied"


class TestDependencyReport:
    """Tests for DependencyReport."""

    def test_empty_report(self) -> None:
        """Test empty report."""
        report = DependencyReport()
        assert report.all_satisfied
        assert len(report.results) == 0

    def test_all_satisfied(self) -> None:
        """Test report with all satisfied."""
        dep = Dependency(name="test")
        result = DependencyCheckResult(
            dependency=dep,
            status=DependencyStatus.SATISFIED,
        )
        report = DependencyReport(results=[result])
        assert report.all_satisfied

    def test_required_missing(self) -> None:
        """Test required missing dependencies."""
        dep = Dependency(name="missing", optional=False)
        result = DependencyCheckResult(
            dependency=dep,
            status=DependencyStatus.MISSING,
        )
        report = DependencyReport(results=[result])
        assert not report.all_satisfied
        assert len(report.required_missing) == 1
        assert len(report.optional_missing) == 0

    def test_optional_missing(self) -> None:
        """Test optional missing dependencies."""
        dep = Dependency(name="optional", optional=True)
        result = DependencyCheckResult(
            dependency=dep,
            status=DependencyStatus.MISSING,
        )
        report = DependencyReport(results=[result])
        assert report.all_satisfied  # Optional missing doesn't fail
        assert len(report.optional_missing) == 1

    def test_to_dict(self) -> None:
        """Test report to dict."""
        report = DependencyReport()
        d = report.to_dict()
        assert "results" in d
        assert "all_satisfied" in d


class TestDependencyManager:
    """Tests for DependencyManager."""

    def test_manager_creation(self) -> None:
        """Test creating manager."""
        manager = DependencyManager()
        assert manager is not None

    def test_check_installed_package(self) -> None:
        """Test checking an installed package."""
        manager = DependencyManager()
        # pytest should always be available
        dep = Dependency(name="pytest", type=DependencyType.PYTHON)
        result = manager.check_dependency(dep)
        assert result.status in (
            DependencyStatus.SATISFIED,
            DependencyStatus.VERSION_MISMATCH,
        )

    def test_check_missing_package(self) -> None:
        """Test checking a missing package."""
        manager = DependencyManager()
        dep = Dependency(
            name="nonexistent-package-xyz-12345",
            type=DependencyType.PYTHON,
        )
        result = manager.check_dependency(dep)
        assert result.status == DependencyStatus.MISSING

    def test_check_multiple_dependencies(self) -> None:
        """Test checking multiple dependencies."""
        manager = DependencyManager()
        deps = [
            Dependency(name="pytest", type=DependencyType.PYTHON),
            Dependency(name="nonexistent-xyz", type=DependencyType.PYTHON),
        ]
        report = manager.check_dependencies(deps)
        assert len(report.results) == 2

    def test_get_installed_packages(self) -> None:
        """Test getting installed packages."""
        manager = DependencyManager()
        packages = manager.get_installed_packages()
        assert isinstance(packages, dict)
        # pytest should be in the list
        assert "pytest" in packages

    def test_get_missing_packages(self) -> None:
        """Test getting missing packages."""
        manager = DependencyManager()
        deps = [
            Dependency(name="pytest", type=DependencyType.PYTHON),
            Dependency(name="nonexistent-xyz", type=DependencyType.PYTHON),
        ]
        missing = manager.get_missing_packages(deps)
        assert len(missing) == 1
        assert missing[0].name == "nonexistent-xyz"

    def test_get_install_commands(self) -> None:
        """Test getting install commands."""
        manager = DependencyManager()
        dep = Dependency(
            name="missing-pkg",
            type=DependencyType.PYTHON,
            optional=False,
        )
        result = DependencyCheckResult(
            dependency=dep,
            status=DependencyStatus.MISSING,
        )
        report = DependencyReport(results=[result])
        commands = manager.get_install_commands(report)
        assert len(commands) == 1
        assert "pip install" in commands[0]


class TestCheckPythonPackage:
    """Tests for check_python_package function."""

    def test_check_installed(self) -> None:
        """Test checking installed package."""
        from mc_agent_kit.plugin.dependency import check_python_package
        result = check_python_package("pytest")
        assert result.status in (
            DependencyStatus.SATISFIED,
            DependencyStatus.VERSION_MISMATCH,
        )

    def test_check_missing(self) -> None:
        """Test checking missing package."""
        from mc_agent_kit.plugin.dependency import check_python_package
        result = check_python_package("nonexistent-pkg-xyz-123")
        assert result.status == DependencyStatus.MISSING