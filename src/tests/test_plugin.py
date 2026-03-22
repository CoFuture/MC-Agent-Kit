"""Tests for the plugin system."""

import json
import tempfile
from pathlib import Path

import pytest

from mc_agent_kit.plugin import (
    PluginBase,
    PluginInfo,
    PluginLoader,
    PluginManager,
    PluginMetadata,
    PluginPriority,
    PluginRegistry,
    PluginResult,
    PluginState,
)


class MockPlugin(PluginBase):
    """Mock plugin for testing."""

    def __init__(self) -> None:
        super().__init__()
        self.load_called = False
        self.unload_called = False
        self.enable_called = False
        self.disable_called = False
        self._metadata = PluginMetadata(
            name="mock-plugin",
            version="1.0.0",
            description="A mock plugin for testing",
            author="Test Author",
        )

    def on_load(self) -> None:
        self.load_called = True

    def on_unload(self) -> None:
        self.unload_called = True

    def on_enable(self) -> None:
        self.enable_called = True

    def on_disable(self) -> None:
        self.disable_called = True

    def execute(self, *args, **kwargs):
        return PluginResult(success=True, data={"args": args, "kwargs": kwargs})


class AnotherMockPlugin(PluginBase):
    """Another mock plugin for testing."""

    def __init__(self) -> None:
        super().__init__()
        self._metadata = PluginMetadata(
            name="another-plugin",
            version="2.0.0",
            description="Another mock plugin",
            dependencies=["mock-plugin"],
            provides=["feature-x"],
        )

    def on_load(self) -> None:
        pass

    def on_unload(self) -> None:
        pass


class TestPluginMetadata:
    """Tests for PluginMetadata."""

    def test_create_metadata(self):
        """Test creating metadata."""
        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="Test description",
            author="Test Author",
        )
        assert metadata.name == "test-plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test description"
        assert metadata.author == "Test Author"
        assert metadata.priority == PluginPriority.NORMAL
        assert metadata.dependencies == []
        assert metadata.provides == []

    def test_metadata_validation(self):
        """Test metadata validation."""
        with pytest.raises(ValueError):
            PluginMetadata(name="", version="1.0.0")

        with pytest.raises(ValueError):
            PluginMetadata(name="test", version="")

    def test_metadata_to_dict(self):
        """Test converting metadata to dict."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            description="desc",
            priority=PluginPriority.HIGH,
        )
        d = metadata.to_dict()
        assert d["name"] == "test"
        assert d["version"] == "1.0.0"
        assert d["description"] == "desc"
        assert d["priority"] == 75

    def test_metadata_from_dict(self):
        """Test creating metadata from dict."""
        d = {
            "name": "test",
            "version": "2.0.0",
            "description": "test desc",
            "priority": 50,
            "dependencies": ["dep1"],
            "provides": ["cap1"],
        }
        metadata = PluginMetadata.from_dict(d)
        assert metadata.name == "test"
        assert metadata.version == "2.0.0"
        assert metadata.description == "test desc"
        assert metadata.priority == PluginPriority.NORMAL
        assert metadata.dependencies == ["dep1"]
        assert metadata.provides == ["cap1"]


class TestPluginResult:
    """Tests for PluginResult."""

    def test_success_result(self):
        """Test successful result."""
        result = PluginResult(success=True, data={"key": "value"})
        assert result.success
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_error_result(self):
        """Test error result."""
        result = PluginResult(success=False, error="Something went wrong")
        assert not result.success
        assert result.error == "Something went wrong"

    def test_result_to_dict(self):
        """Test converting result to dict."""
        result = PluginResult(
            success=True, data=[1, 2, 3], error=None, duration_ms=10.5
        )
        d = result.to_dict()
        assert d["success"]
        assert d["data"] == [1, 2, 3]
        assert d["duration_ms"] == 10.5


class TestPluginBase:
    """Tests for PluginBase."""

    def test_plugin_initialization(self):
        """Test plugin initialization."""
        plugin = MockPlugin()
        assert plugin.state == PluginState.UNLOADED
        assert plugin.name == "mock-plugin"

    def test_plugin_config(self):
        """Test plugin configuration."""
        plugin = MockPlugin()
        plugin.set_config({"key": "value", "number": 42})
        assert plugin.get_config("key") == "value"
        assert plugin.get_config("number") == 42
        assert plugin.get_config("missing", "default") == "default"

    def test_plugin_lifecycle(self):
        """Test plugin lifecycle methods."""
        plugin = MockPlugin()
        plugin.on_load()
        assert plugin.load_called

        plugin.on_enable()
        assert plugin.enable_called

        plugin.on_disable()
        assert plugin.disable_called

        plugin.on_unload()
        assert plugin.unload_called

    def test_plugin_execute(self):
        """Test plugin execution."""
        plugin = MockPlugin()
        result = plugin.execute("arg1", "arg2", key="value")
        assert result.success
        assert result.data["args"] == ("arg1", "arg2")
        assert result.data["kwargs"] == {"key": "value"}


class TestPluginInfo:
    """Tests for PluginInfo."""

    def test_plugin_info(self):
        """Test creating plugin info."""
        metadata = PluginMetadata(name="test", version="1.0.0")
        info = PluginInfo(metadata=metadata)
        assert info.name == "test"
        assert info.version == "1.0.0"
        assert info.state == PluginState.UNLOADED
        assert not info.is_loaded
        assert not info.is_enabled

    def test_plugin_info_loaded_state(self):
        """Test plugin info loaded state."""
        metadata = PluginMetadata(name="test", version="1.0.0")
        info = PluginInfo(metadata=metadata)
        info.state = PluginState.LOADED
        assert info.is_loaded
        assert not info.is_enabled

    def test_plugin_info_enabled_state(self):
        """Test plugin info enabled state."""
        metadata = PluginMetadata(name="test", version="1.0.0")
        info = PluginInfo(metadata=metadata)
        info.state = PluginState.ENABLED
        assert info.is_loaded
        assert info.is_enabled

    def test_plugin_info_to_dict(self):
        """Test converting plugin info to dict."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            description="desc",
            author="author",
        )
        info = PluginInfo(metadata=metadata)
        info.state = PluginState.ENABLED
        d = info.to_dict()
        assert d["name"] == "test"
        assert d["version"] == "1.0.0"
        assert d["state"] == "enabled"
        assert d["is_loaded"]
        assert d["is_enabled"]


class TestPluginRegistry:
    """Tests for PluginRegistry."""

    def test_register_plugin(self):
        """Test registering a plugin."""
        registry = PluginRegistry()
        metadata = PluginMetadata(name="test", version="1.0.0")
        info = PluginInfo(metadata=metadata)

        registry.register(info)
        assert registry.has_plugin("test")
        assert registry.get("test") == info

    def test_register_duplicate(self):
        """Test registering duplicate plugin."""
        registry = PluginRegistry()
        metadata = PluginMetadata(name="test", version="1.0.0")
        info1 = PluginInfo(metadata=metadata)
        info2 = PluginInfo(metadata=metadata)

        registry.register(info1)
        with pytest.raises(ValueError):
            registry.register(info2)

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        registry = PluginRegistry()
        metadata = PluginMetadata(name="test", version="1.0.0")
        info = PluginInfo(metadata=metadata)

        registry.register(info)
        assert registry.unregister("test")
        assert not registry.has_plugin("test")

    def test_unregister_nonexistent(self):
        """Test unregistering nonexistent plugin."""
        registry = PluginRegistry()
        assert not registry.unregister("nonexistent")

    def test_get_all_plugins(self):
        """Test getting all plugins."""
        registry = PluginRegistry()
        metadata1 = PluginMetadata(name="plugin1", version="1.0.0")
        metadata2 = PluginMetadata(name="plugin2", version="2.0.0")
        info1 = PluginInfo(metadata=metadata1)
        info2 = PluginInfo(metadata=metadata2)

        registry.register(info1)
        registry.register(info2)

        all_plugins = registry.get_all()
        assert len(all_plugins) == 2

    def test_capability_registration(self):
        """Test capability registration."""
        registry = PluginRegistry()
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            provides=["feature-a", "feature-b"],
        )
        info = PluginInfo(metadata=metadata)

        registry.register(info)
        assert registry.has_capability("feature-a")
        assert registry.has_capability("feature-b")

        plugins = registry.get_by_capability("feature-a")
        assert len(plugins) == 1
        assert plugins[0].name == "test"

    def test_capability_unregistration(self):
        """Test capability unregistration."""
        registry = PluginRegistry()
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            provides=["feature-a"],
        )
        info = PluginInfo(metadata=metadata)

        registry.register(info)
        assert registry.has_capability("feature-a")

        registry.unregister("test")
        assert not registry.has_capability("feature-a")

    def test_get_enabled_plugins(self):
        """Test getting enabled plugins."""
        registry = PluginRegistry()
        metadata1 = PluginMetadata(name="plugin1", version="1.0.0")
        metadata2 = PluginMetadata(name="plugin2", version="2.0.0")
        info1 = PluginInfo(metadata=metadata1)
        info2 = PluginInfo(metadata=metadata2)
        info1.state = PluginState.ENABLED

        registry.register(info1)
        registry.register(info2)

        enabled = registry.get_enabled()
        assert len(enabled) == 1
        assert enabled[0].name == "plugin1"

    def test_get_by_state(self):
        """Test getting plugins by state."""
        registry = PluginRegistry()
        metadata1 = PluginMetadata(name="plugin1", version="1.0.0")
        metadata2 = PluginMetadata(name="plugin2", version="2.0.0")
        info1 = PluginInfo(metadata=metadata1)
        info2 = PluginInfo(metadata=metadata2)
        info1.state = PluginState.ENABLED
        info2.state = PluginState.ERROR

        registry.register(info1)
        registry.register(info2)

        enabled = registry.get_by_state(PluginState.ENABLED)
        assert len(enabled) == 1

        errors = registry.get_by_state(PluginState.ERROR)
        assert len(errors) == 1

    def test_resolve_dependencies(self):
        """Test dependency resolution."""
        registry = PluginRegistry()
        metadata1 = PluginMetadata(name="base", version="1.0.0")
        metadata2 = PluginMetadata(
            name="dependent",
            version="1.0.0",
            dependencies=["base"],
        )
        info1 = PluginInfo(metadata=metadata1)
        info2 = PluginInfo(metadata=metadata2)

        registry.register(info1)
        registry.register(info2)

        resolved = registry.resolve_dependencies("dependent")
        assert resolved == ["base", "dependent"]

    def test_resolve_missing_dependency(self):
        """Test resolving missing dependency."""
        registry = PluginRegistry()
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            dependencies=["missing"],
        )
        info = PluginInfo(metadata=metadata)
        registry.register(info)

        with pytest.raises(ValueError):
            registry.resolve_dependencies("test")

    def test_circular_dependency(self):
        """Test circular dependency detection."""
        registry = PluginRegistry()
        metadata1 = PluginMetadata(
            name="a",
            version="1.0.0",
            dependencies=["b"],
        )
        metadata2 = PluginMetadata(
            name="b",
            version="1.0.0",
            dependencies=["a"],
        )
        info1 = PluginInfo(metadata=metadata1)
        info2 = PluginInfo(metadata=metadata2)

        registry.register(info1)
        registry.register(info2)

        with pytest.raises(ValueError, match="Circular dependency"):
            registry.resolve_dependencies("a")

    def test_get_capabilities(self):
        """Test getting all capabilities."""
        registry = PluginRegistry()
        metadata1 = PluginMetadata(
            name="plugin1",
            version="1.0.0",
            provides=["cap-a"],
        )
        metadata2 = PluginMetadata(
            name="plugin2",
            version="1.0.0",
            provides=["cap-b"],
        )
        info1 = PluginInfo(metadata=metadata1)
        info2 = PluginInfo(metadata=metadata2)

        registry.register(info1)
        registry.register(info2)

        capabilities = registry.get_capabilities()
        assert set(capabilities) == {"cap-a", "cap-b"}

    def test_clear(self):
        """Test clearing registry."""
        registry = PluginRegistry()
        metadata = PluginMetadata(name="test", version="1.0.0")
        info = PluginInfo(metadata=metadata)

        registry.register(info)
        registry.clear()
        assert not registry.has_plugin("test")


class TestPluginLoader:
    """Tests for PluginLoader."""

    def test_add_search_path(self):
        """Test adding search path."""
        loader = PluginLoader()
        loader.add_search_path("/path/to/plugins")
        assert Path("/path/to/plugins") in loader.get_search_paths()

    def test_remove_search_path(self):
        """Test removing search path."""
        loader = PluginLoader()
        loader.add_search_path("/path/to/plugins")
        assert loader.remove_search_path("/path/to/plugins")
        assert Path("/path/to/plugins") not in loader.get_search_paths()

    def test_discover_plugins_empty(self):
        """Test discovering plugins in empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PluginLoader()
            loader.add_search_path(tmpdir)
            discovered = loader.discover_plugins()
            assert discovered == []

    def test_load_from_file(self, tmp_path):
        """Test loading plugin from file."""
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class TestPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(
            name="file-plugin",
            version="1.0.0"
        )

    def on_load(self):
        pass

    def on_unload(self):
        pass
''')
        loader = PluginLoader()
        info = loader.load_from_path(plugin_file)

        assert info is not None
        assert info.name == "file-plugin"
        assert info.state == PluginState.LOADED
        assert info.instance is not None

    def test_load_from_directory_with_manifest(self, tmp_path):
        """Test loading plugin from directory with manifest."""
        plugin_dir = tmp_path / "manifest-plugin"
        plugin_dir.mkdir()

        manifest = plugin_dir / "plugin.json"
        manifest_data = {
            "name": "manifest-plugin",
            "version": "1.0.0",
            "description": "Plugin with manifest",
        }
        manifest.write_text(json.dumps(manifest_data))

        entry = plugin_dir / "plugin.py"
        entry.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class ManifestPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(
            name="manifest-plugin",
            version="1.0.0"
        )

    def on_load(self):
        pass

    def on_unload(self):
        pass
''')

        loader = PluginLoader()
        info = loader.load_from_path(plugin_dir)

        assert info is not None
        assert info.name == "manifest-plugin"

    def test_load_from_directory_without_manifest(self, tmp_path):
        """Test loading plugin from directory without manifest."""
        plugin_dir = tmp_path / "no-manifest-plugin"
        plugin_dir.mkdir()

        entry = plugin_dir / "plugin.py"
        entry.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class NoManifestPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(
            name="no-manifest",
            version="1.0.0"
        )

    def on_load(self):
        pass

    def on_unload(self):
        pass
''')

        loader = PluginLoader()
        info = loader.load_from_path(plugin_dir)

        assert info is not None
        assert info.name == "no-manifest"

    def test_load_invalid_path(self):
        """Test loading from invalid path."""
        loader = PluginLoader()
        info = loader.load_from_path("/nonexistent/path")
        assert info is None

    def test_load_all(self, tmp_path):
        """Test loading all plugins."""
        plugin1 = tmp_path / "plugin1.py"
        plugin1.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class Plugin1(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="plugin1", version="1.0.0")
    def on_load(self): pass
    def on_unload(self): pass
''')

        plugin2 = tmp_path / "plugin2.py"
        plugin2.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class Plugin2(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="plugin2", version="1.0.0")
    def on_load(self): pass
    def on_unload(self): pass
''')

        loader = PluginLoader()
        loader.add_search_path(tmp_path)
        loaded = loader.load_all()

        assert len(loaded) == 2
        assert loader.registry.has_plugin("plugin1")
        assert loader.registry.has_plugin("plugin2")

    def test_unload(self, tmp_path):
        """Test unloading plugin."""
        plugin_file = tmp_path / "test.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class UnloadTestPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="unload-test", version="1.0.0")
    def on_load(self): pass
    def on_unload(self): pass
''')

        loader = PluginLoader()
        info = loader.load_from_path(plugin_file)
        loader.registry.register(info)

        assert loader.unload("unload-test")
        assert not loader.registry.has_plugin("unload-test")


class TestPluginManager:
    """Tests for PluginManager."""

    def test_add_plugin_directory(self):
        """Test adding plugin directory."""
        manager = PluginManager()
        manager.add_plugin_directory("/path/to/plugins")
        assert Path("/path/to/plugins") in manager.loader.get_search_paths()

    def test_load_plugin(self, tmp_path):
        """Test loading plugin through manager."""
        plugin_file = tmp_path / "mgr_plugin.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class MgrPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="mgr-plugin", version="1.0.0")
    def on_load(self): pass
    def on_unload(self): pass
''')

        manager = PluginManager()
        info = manager.load_plugin(plugin_file)

        assert info is not None
        assert manager.has_plugin("mgr-plugin")

    def test_unload_plugin(self, tmp_path):
        """Test unloading plugin through manager."""
        plugin_file = tmp_path / "unload.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class UnloadPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="unload-mgr", version="1.0.0")
    def on_load(self): pass
    def on_unload(self): pass
''')

        manager = PluginManager()
        manager.load_plugin(plugin_file)

        assert manager.unload_plugin("unload-mgr")
        assert not manager.has_plugin("unload-mgr")

    def test_enable_disable_plugin(self, tmp_path):
        """Test enabling and disabling plugin."""
        plugin_file = tmp_path / "enable.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class EnablePlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="enable-test", version="1.0.0")
    def on_load(self): pass
    def on_unload(self): pass
    def on_enable(self): self.enabled = True
    def on_disable(self): self.enabled = False
''')

        manager = PluginManager()
        manager.load_plugin(plugin_file)

        assert manager.enable_plugin("enable-test")
        plugin_info = manager.get_plugin("enable-test")
        assert plugin_info.state == PluginState.ENABLED

        assert manager.disable_plugin("enable-test")
        assert plugin_info.state == PluginState.DISABLED

    def test_enable_with_dependencies(self, tmp_path):
        """Test enabling plugin with dependencies."""
        base_plugin = tmp_path / "base.py"
        base_plugin.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class BasePlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="base-dep", version="1.0.0")
    def on_load(self): pass
    def on_unload(self): pass
''')

        dep_plugin = tmp_path / "dependent.py"
        dep_plugin.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class DepPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(
            name="dep-plugin",
            version="1.0.0",
            dependencies=["base-dep"]
        )
    def on_load(self): pass
    def on_unload(self): pass
''')

        manager = PluginManager()
        manager.load_plugin(base_plugin)
        manager.load_plugin(dep_plugin)

        # Enable base first, then dependent
        manager.enable_plugin("base-dep")
        assert manager.enable_plugin("dep-plugin")

    def test_enable_missing_dependency(self, tmp_path):
        """Test enabling plugin with missing dependency."""
        plugin_file = tmp_path / "missing.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class MissingDepPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(
            name="missing-dep",
            version="1.0.0",
            dependencies=["nonexistent"]
        )
    def on_load(self): pass
    def on_unload(self): pass
''')

        manager = PluginManager()
        manager.load_plugin(plugin_file)

        # Should fail due to missing dependency
        assert not manager.enable_plugin("missing-dep")

    def test_execute_plugin(self, tmp_path):
        """Test executing plugin."""
        plugin_file = tmp_path / "exec.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata, PluginResult

class ExecPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="exec-test", version="1.0.0")
    def on_load(self): pass
    def on_unload(self): pass
    def execute(self, *args, **kwargs):
        return PluginResult(success=True, data={"executed": True})
''')

        manager = PluginManager()
        manager.load_plugin(plugin_file)
        manager.enable_plugin("exec-test")

        result = manager.execute_plugin("exec-test")
        assert result is not None
        assert result.success
        assert result.data == {"executed": True}

    def test_execute_disabled_plugin(self, tmp_path):
        """Test executing disabled plugin."""
        plugin_file = tmp_path / "disabled.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class DisabledPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="disabled-test", version="1.0.0")
    def on_load(self): pass
    def on_unload(self): pass
''')

        manager = PluginManager()
        manager.load_plugin(plugin_file)
        # Don't enable

        result = manager.execute_plugin("disabled-test")
        assert result is not None
        assert not result.success

    def test_plugin_config(self):
        """Test plugin configuration."""
        manager = PluginManager()
        manager.set_plugin_config("test-plugin", {"key": "value"})

        config = manager.get_plugin_config("test-plugin")
        assert config == {"key": "value"}

    def test_get_all_status(self, tmp_path):
        """Test getting all plugin status."""
        plugin_file = tmp_path / "status.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class StatusPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="status-test", version="1.0.0")
    def on_load(self): pass
    def on_unload(self): pass
''')

        manager = PluginManager()
        manager.load_plugin(plugin_file)
        manager.enable_plugin("status-test")

        statuses = manager.get_all_status()
        assert len(statuses) == 1
        assert statuses[0]["name"] == "status-test"
        assert statuses[0]["is_enabled"]

    def test_capability_helpers(self, tmp_path):
        """Test capability helper methods."""
        plugin_file = tmp_path / "cap.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class CapPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(
            name="cap-test",
            version="1.0.0",
            provides=["feature-x", "feature-y"]
        )
    def on_load(self): pass
    def on_unload(self): pass
''')

        manager = PluginManager()
        manager.load_plugin(plugin_file)

        assert manager.has_capability("feature-x")
        assert manager.has_capability("feature-y")
        assert not manager.has_capability("feature-z")

        capabilities = manager.get_capabilities()
        assert "feature-x" in capabilities
        assert "feature-y" in capabilities

    def test_reload_plugin(self, tmp_path):
        """Test reloading plugin."""
        plugin_file = tmp_path / "reload.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class ReloadPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="reload-test", version="1.0.0")
    def on_load(self): pass
    def on_unload(self): pass
''')

        manager = PluginManager()
        manager.load_plugin(plugin_file)
        manager.enable_plugin("reload-test")

        assert manager.reload_plugin("reload-test")
        plugin_info = manager.get_plugin("reload-test")
        assert plugin_info.state == PluginState.ENABLED

    def test_shutdown(self, tmp_path):
        """Test shutting down manager."""
        plugin_file = tmp_path / "shutdown.py"
        plugin_file.write_text('''
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class ShutdownPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(name="shutdown-test", version="1.0.0")
    def on_load(self): pass
    def on_unload(self): pass
''')

        manager = PluginManager()
        manager.load_plugin(plugin_file)
        manager.enable_plugin("shutdown-test")

        manager.shutdown()
        # After shutdown, the plugin should be unregistered
        assert manager.get_plugin("shutdown-test") is None or not manager.get_plugin("shutdown-test").is_enabled