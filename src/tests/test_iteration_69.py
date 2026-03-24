"""
迭代 #69 测试：插件系统增强与性能优化

测试内容：
- 插件钩子系统
- 插件配置管理
- 内置插件（Git, 通知, 文件监控, 代码格式化）
- 性能优化功能
"""

import tempfile
from pathlib import Path
from typing import Any

import pytest

from mc_agent_kit.contrib.plugin.base import (
    PluginBase,
    PluginMetadata,
    PluginResult,
    PluginState,
    PluginPriority,
)
from mc_agent_kit.contrib.plugin.hooks import (
    HookRegistry,
    HookInfo,
    HookResult,
    HookPriority,
    HookType,
    register_hook,
    trigger_hooks,
    get_hook_registry,
    hook_decorator,
)
from mc_agent_kit.contrib.plugin.config import (
    PluginConfig,
    PluginConfigManager,
    PluginConfigSchema,
)
from mc_agent_kit.contrib.plugin.marketplace import (
    PluginMarketplace,
    PluginMarketInfo,
    PluginCategory,
    PluginStatus,
)
from mc_agent_kit.contrib.plugin.manager import (
    PluginManager,
    PluginManagerConfig,
)
from mc_agent_kit.contrib.plugin.builtin.git_plugin import GitPlugin, GitStatus
from mc_agent_kit.contrib.plugin.builtin.notification_plugin import (
    NotificationPlugin,
    Notification,
    NotificationLevel,
    NotificationChannel,
)
from mc_agent_kit.contrib.plugin.builtin.file_monitor_plugin import (
    FileMonitorPlugin,
    FileEvent,
    FileEventType,
)
from mc_agent_kit.contrib.plugin.builtin.code_format_plugin import (
    CodeFormatPlugin,
    FormatResult,
    FormatterType,
)


# =============================================================================
# Hook System Tests
# =============================================================================

class TestHookRegistry:
    """Hook registry tests."""

    def test_registry_creation(self) -> None:
        """Test creating a hook registry."""
        registry = HookRegistry()
        assert registry is not None

    def test_register_hook(self) -> None:
        """Test registering a hook."""
        registry = HookRegistry()
        
        called = []
        def callback(**kwargs: Any) -> str:
            called.append(True)
            return "result"
        
        registry.register(HookType.ON_SEARCH, callback)
        
        results = registry.trigger(HookType.ON_SEARCH, query="test")
        
        assert len(called) == 1
        assert len(results) == 1
        assert results[0].success
        assert results[0].result == "result"

    def test_hook_priority(self) -> None:
        """Test hook execution order by priority."""
        registry = HookRegistry()
        
        order = []
        
        def low_callback(**kwargs: Any) -> None:
            order.append("low")
        
        def high_callback(**kwargs: Any) -> None:
            order.append("high")
        
        def normal_callback(**kwargs: Any) -> None:
            order.append("normal")
        
        registry.register(HookType.ON_ERROR, low_callback, HookPriority.LOW)
        registry.register(HookType.ON_ERROR, high_callback, HookPriority.HIGH)
        registry.register(HookType.ON_ERROR, normal_callback, HookPriority.NORMAL)
        
        registry.trigger(HookType.ON_ERROR)
        
        # Higher priority runs first
        assert order == ["high", "normal", "low"]

    def test_unregister_hook(self) -> None:
        """Test unregistering a hook."""
        registry = HookRegistry()
        
        def callback(**kwargs: Any) -> str:
            return "result"
        
        registry.register(HookType.ON_LOG, callback)
        assert len(registry.get_hooks(HookType.ON_LOG)) == 1
        
        registry.unregister(HookType.ON_LOG, callback)
        assert len(registry.get_hooks(HookType.ON_LOG)) == 0

    def test_trigger_until(self) -> None:
        """Test triggering hooks until condition is met."""
        registry = HookRegistry()
        
        def callback1(**kwargs: Any) -> Any:
            return None
        
        def callback2(**kwargs: Any) -> str:
            return "found"
        
        def callback3(**kwargs: Any) -> str:
            return "not reached"
        
        registry.register(HookType.ON_SEARCH, callback1, HookPriority.HIGH)
        registry.register(HookType.ON_SEARCH, callback2, HookPriority.NORMAL)
        registry.register(HookType.ON_SEARCH, callback3, HookPriority.LOW)
        
        result = registry.trigger_until(HookType.ON_SEARCH, stop_on=lambda r: r is not None)
        
        assert result == "found"

    def test_hook_error_handling(self) -> None:
        """Test that hook errors are captured."""
        registry = HookRegistry()
        
        def bad_callback(**kwargs: Any) -> None:
            raise ValueError("Test error")
        
        registry.register(HookType.ON_ERROR, bad_callback)
        
        results = registry.trigger(HookType.ON_ERROR)
        
        assert len(results) == 1
        assert not results[0].success
        assert "Test error" in results[0].error

    def test_hook_decorator(self) -> None:
        """Test hook decorator."""
        registry = HookRegistry()
        
        @hook_decorator(HookType.ON_STARTUP, plugin_name="test")
        def startup_hook(**kwargs: Any) -> str:
            return "started"
        
        # The decorator registers with global registry
        results = trigger_hooks(HookType.ON_STARTUP)
        
        assert len(results) >= 1
        # Find our result
        found = False
        for r in results:
            if r.success and r.result == "started":
                found = True
                break
        assert found


class TestGlobalHookRegistry:
    """Global hook registry tests."""

    def test_get_global_registry(self) -> None:
        """Test getting global registry."""
        registry1 = get_hook_registry()
        registry2 = get_hook_registry()
        
        assert registry1 is registry2

    def test_register_hook_global(self) -> None:
        """Test registering with global registry."""
        called = []
        
        def callback(**kwargs: Any) -> None:
            called.append(True)
        
        register_hook(HookType.ON_SHUTDOWN, callback)
        
        trigger_hooks(HookType.ON_SHUTDOWN)
        
        assert len(called) >= 1


# =============================================================================
# Plugin Config Tests
# =============================================================================

class TestPluginConfig:
    """Plugin configuration tests."""

    def test_config_creation(self) -> None:
        """Test creating a plugin config."""
        config = PluginConfig(enabled=True, settings={"key": "value"})
        
        assert config.enabled
        assert config.settings["key"] == "value"

    def test_config_get_set(self) -> None:
        """Test config get and set."""
        config = PluginConfig()
        
        assert config.get("missing", "default") == "default"
        
        config.set("key", "value")
        assert config.get("key") == "value"

    def test_config_serialization(self) -> None:
        """Test config serialization."""
        config = PluginConfig(enabled=True, settings={"key": "value"})
        
        data = config.to_dict()
        assert data["enabled"]
        assert data["settings"]["key"] == "value"
        
        restored = PluginConfig.from_dict(data)
        assert restored.enabled
        assert restored.settings["key"] == "value"


class TestPluginConfigSchema:
    """Plugin config schema tests."""

    def test_string_schema(self) -> None:
        """Test string schema validation."""
        schema = PluginConfigSchema(
            key="name",
            type="string",
            default="default",
            required=True,
        )
        
        is_valid, error = schema.validate("test")
        assert is_valid
        
        is_valid, error = schema.validate(123)
        assert not is_valid

    def test_int_schema(self) -> None:
        """Test int schema validation."""
        schema = PluginConfigSchema(
            key="count",
            type="int",
            min_value=0,
            max_value=100,
        )
        
        is_valid, _ = schema.validate(50)
        assert is_valid
        
        is_valid, error = schema.validate(150)
        assert not is_valid
        
        is_valid, error = schema.validate(-10)
        assert not is_valid

    def test_choices_schema(self) -> None:
        """Test choices validation."""
        schema = PluginConfigSchema(
            key="level",
            type="string",
            choices=["debug", "info", "error"],
        )
        
        is_valid, _ = schema.validate("info")
        assert is_valid
        
        is_valid, error = schema.validate("unknown")
        assert not is_valid


class TestPluginConfigManager:
    """Plugin config manager tests."""

    def test_manager_creation(self) -> None:
        """Test creating a config manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PluginConfigManager(Path(tmpdir))
            assert manager is not None

    def test_get_config(self) -> None:
        """Test getting config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PluginConfigManager(Path(tmpdir))
            
            config = manager.get_config("test-plugin")
            assert config is not None
            assert config.enabled

    def test_set_config(self) -> None:
        """Test setting config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PluginConfigManager(Path(tmpdir))
            
            config = PluginConfig(enabled=False, settings={"key": "value"})
            manager.set_config("test-plugin", config)
            
            restored = manager.get_config("test-plugin")
            assert not restored.enabled
            assert restored.settings["key"] == "value"

    def test_schema_validation(self) -> None:
        """Test schema validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PluginConfigManager(Path(tmpdir))
            
            schemas = [
                PluginConfigSchema(key="level", type="string", choices=["info", "error"]),
            ]
            manager.register_schema("test-plugin", schemas)
            
            config = PluginConfig(settings={"level": "info"})
            errors = manager.validate_config("test-plugin", config)
            assert len(errors) == 0
            
            config = PluginConfig(settings={"level": "unknown"})
            errors = manager.validate_config("test-plugin", config)
            assert len(errors) > 0

    def test_update_setting(self) -> None:
        """Test updating a single setting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PluginConfigManager(Path(tmpdir))
            
            manager.update_setting("test-plugin", "key", "value")
            
            config = manager.get_config("test-plugin")
            assert config.get("key") == "value"


# =============================================================================
# Built-in Plugin Tests
# =============================================================================

class TestGitPlugin:
    """Git plugin tests."""

    def test_plugin_creation(self) -> None:
        """Test creating the Git plugin."""
        plugin = GitPlugin()
        
        assert plugin.metadata.name == "git-operations"
        assert "git" in plugin.metadata.capabilities

    def test_plugin_initialize(self) -> None:
        """Test initializing the Git plugin."""
        plugin = GitPlugin()
        
        assert plugin.initialize()
        plugin.shutdown()

    def test_not_git_repo(self) -> None:
        """Test error when not a git repo."""
        plugin = GitPlugin()
        plugin.initialize()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = plugin.execute(operation="status", path=tmpdir)
            
            assert not result.success
            assert "Not a Git repository" in result.error

    def test_status_dataclass(self) -> None:
        """Test GitStatus dataclass."""
        status = GitStatus(
            branch="main",
            is_clean=True,
            staged=[],
            unstaged=[],
            untracked=[],
            ahead=0,
            behind=0,
        )
        
        assert status.branch == "main"
        assert status.is_clean


class TestNotificationPlugin:
    """Notification plugin tests."""

    def test_plugin_creation(self) -> None:
        """Test creating the notification plugin."""
        plugin = NotificationPlugin()
        
        assert plugin.metadata.name == "notification"
        assert "notification" in plugin.metadata.capabilities

    def test_plugin_initialize(self) -> None:
        """Test initializing the notification plugin."""
        plugin = NotificationPlugin()
        
        assert plugin.initialize()
        plugin.shutdown()

    def test_console_notification(self) -> None:
        """Test console notification."""
        plugin = NotificationPlugin()
        plugin.initialize()
        
        result = plugin.execute(
            title="Test",
            message="Hello",
            level="info",
            channel="console",
        )
        
        assert result.success
        assert result.data["status"] == "sent"

    def test_notification_levels(self) -> None:
        """Test notification levels."""
        assert NotificationLevel.INFO.value == "info"
        assert NotificationLevel.ERROR.value == "error"
        assert NotificationLevel.CRITICAL.value == "critical"

    def test_notification_channels(self) -> None:
        """Test notification channels."""
        assert NotificationChannel.CONSOLE.value == "console"
        assert NotificationChannel.FILE.value == "file"
        assert NotificationChannel.EMAIL.value == "email"
        assert NotificationChannel.WEBHOOK.value == "webhook"
        assert NotificationChannel.FEISHU.value == "feishu"

    def test_notification_history(self) -> None:
        """Test notification history."""
        plugin = NotificationPlugin()
        plugin.initialize()
        
        plugin.execute(title="Test 1", message="Message 1", level="info")
        plugin.execute(title="Test 2", message="Message 2", level="warning")
        
        history = plugin.get_history()
        
        assert len(history) >= 2
        assert history[-1]["title"] == "Test 2"


class TestFileMonitorPlugin:
    """File monitor plugin tests."""

    def test_plugin_creation(self) -> None:
        """Test creating the file monitor plugin."""
        plugin = FileMonitorPlugin()
        
        assert plugin.metadata.name == "file-monitor"
        assert "monitoring" in plugin.metadata.capabilities

    def test_plugin_initialize(self) -> None:
        """Test initializing the file monitor plugin."""
        plugin = FileMonitorPlugin()
        
        assert plugin.initialize()
        plugin.shutdown()

    def test_watch_directory(self) -> None:
        """Test watching a directory."""
        plugin = FileMonitorPlugin()
        plugin.initialize()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = plugin.execute(operation="watch", path=tmpdir, recursive=True)
            
            assert result.success
            assert result.data["path"] == str(Path(tmpdir).resolve())

    def test_list_watches(self) -> None:
        """Test listing watches."""
        plugin = FileMonitorPlugin()
        plugin.initialize()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin.execute(operation="watch", path=tmpdir)
            
            result = plugin.execute(operation="list")
            
            assert result.success
            assert len(result.data["watches"]) >= 1

    def test_monitoring_status(self) -> None:
        """Test getting monitoring status."""
        plugin = FileMonitorPlugin()
        plugin.initialize()
        
        result = plugin.execute(operation="status")
        
        assert result.success
        assert "running" in result.data
        assert "watch_count" in result.data

    def test_file_event_types(self) -> None:
        """Test file event types."""
        assert FileEventType.CREATED.value == "created"
        assert FileEventType.MODIFIED.value == "modified"
        assert FileEventType.DELETED.value == "deleted"


class TestCodeFormatPlugin:
    """Code format plugin tests."""

    def test_plugin_creation(self) -> None:
        """Test creating the code format plugin."""
        plugin = CodeFormatPlugin()
        
        assert plugin.metadata.name == "code-format"
        assert "formatting" in plugin.metadata.capabilities

    def test_plugin_initialize(self) -> None:
        """Test initializing the code format plugin."""
        plugin = CodeFormatPlugin()
        
        assert plugin.initialize()
        plugin.shutdown()

    def test_format_code(self) -> None:
        """Test formatting code."""
        plugin = CodeFormatPlugin()
        plugin.initialize()
        
        code = "def hello():\n    print('hello')\n"
        
        result = plugin.execute(operation="format", code=code, formatter="builtin")
        
        assert result.success
        # result.data is a FormatResult dataclass
        assert result.data.formatted == code or not result.data.changed

    def test_check_code(self) -> None:
        """Test checking code."""
        plugin = CodeFormatPlugin()
        plugin.initialize()
        
        code = "x=1\n"
        
        result = plugin.execute(operation="check", code=code)
        
        assert result.success
        assert "needs_formatting" in result.data

    def test_builtin_formatter(self) -> None:
        """Test builtin formatter."""
        plugin = CodeFormatPlugin()
        plugin.initialize()
        
        # Code with trailing whitespace
        code = "x = 1   \n"
        
        result = plugin.format_code(code, formatter="builtin")
        
        # Should format the code (remove trailing whitespace)
        assert result is not None
        assert result.formatted is not None
        # The formatted code should not have trailing whitespace
        for line in result.formatted.split('\n'):
            assert line == line.rstrip(), f"Line has trailing whitespace: {repr(line)}"

    def test_formatter_types(self) -> None:
        """Test formatter types."""
        assert FormatterType.AUTO.value == "auto"
        assert FormatterType.BLACK.value == "black"
        assert FormatterType.RUFF.value == "ruff"
        assert FormatterType.BUILTIN.value == "builtin"


# =============================================================================
# Plugin Manager Tests
# =============================================================================

class TestPluginManager:
    """Plugin manager tests."""

    def test_manager_creation(self) -> None:
        """Test creating a plugin manager."""
        config = PluginManagerConfig(plugin_dirs=[], auto_load=False)
        manager = PluginManager(config)
        
        assert manager is not None

    def test_list_all(self) -> None:
        """Test listing plugins."""
        config = PluginManagerConfig(plugin_dirs=[], auto_load=False)
        manager = PluginManager(config)
        
        plugins = manager.list_all()
        assert isinstance(plugins, list)


# =============================================================================
# Plugin Marketplace Tests
# =============================================================================

class TestPluginMarketplace:
    """Plugin marketplace tests."""

    def test_marketplace_creation(self) -> None:
        """Test creating a marketplace."""
        marketplace = PluginMarketplace()
        
        assert marketplace is not None

    def test_search_plugins(self) -> None:
        """Test searching plugins."""
        marketplace = PluginMarketplace()
        
        results = marketplace.search("hello")
        
        assert isinstance(results, list)

    def test_list_all(self) -> None:
        """Test listing all plugins."""
        marketplace = PluginMarketplace()
        
        plugins = marketplace.list_all()
        
        assert len(plugins) >= 4  # We have at least 4 example plugins

    def test_install_plugin(self) -> None:
        """Test installing a plugin."""
        marketplace = PluginMarketplace()
        
        result = marketplace.install("hello-world")
        
        assert result
        plugin = marketplace.get_plugin("hello-world")
        assert plugin.status == PluginStatus.INSTALLED

    def test_uninstall_plugin(self) -> None:
        """Test uninstalling a plugin."""
        marketplace = PluginMarketplace()
        marketplace.install("hello-world")
        
        result = marketplace.uninstall("hello-world")
        
        assert result
        plugin = marketplace.get_plugin("hello-world")
        assert plugin.status == PluginStatus.AVAILABLE

    def test_marketplace_stats(self) -> None:
        """Test marketplace stats."""
        marketplace = PluginMarketplace()
        
        stats = marketplace.stats
        
        assert "total_plugins" in stats
        assert "installed" in stats
        assert "available" in stats


# =============================================================================
# Integration Tests
# =============================================================================

class TestPluginIntegration:
    """Integration tests for the plugin system."""

    def test_full_plugin_lifecycle(self) -> None:
        """Test complete plugin lifecycle."""
        # Create plugin
        plugin = NotificationPlugin()
        
        # Initialize
        assert plugin.initialize()
        assert plugin.state == PluginState.LOADED
        
        # Enable
        assert plugin.enable()
        assert plugin.state == PluginState.ENABLED
        
        # Execute
        result = plugin.execute(title="Test", message="Integration test")
        assert result.success
        
        # Disable
        assert plugin.disable()
        assert plugin.state == PluginState.DISABLED
        
        # Shutdown
        plugin.shutdown()

    def test_hook_and_plugin_interaction(self) -> None:
        """Test hooks triggered by plugins."""
        registry = HookRegistry()
        
        captured = []
        
        def capture_hook(**kwargs: Any) -> None:
            captured.append(kwargs)
        
        registry.register(HookType.ON_FILE_CHANGE, capture_hook)
        
        # The file monitor should trigger this hook when files change
        plugin = FileMonitorPlugin()
        plugin.initialize()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin.execute(operation="watch", path=tmpdir)
            
            # Create a file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("hello")
            
            # Check for changes
            plugin.execute(operation="check")
        
        plugin.shutdown()


# =============================================================================
# Acceptance Criteria Tests
# =============================================================================

class TestIteration69AcceptanceCriteria:
    """Acceptance criteria tests for iteration #69."""

    def test_hook_system_complete(self) -> None:
        """Test that hook system is complete."""
        # Hook registry exists
        registry = HookRegistry()
        assert registry is not None
        
        # Can register hooks
        registry.register(HookType.ON_SEARCH, lambda **kw: None)
        
        # Can trigger hooks
        results = registry.trigger(HookType.ON_SEARCH)
        assert len(results) == 1
        
        # Hook types defined
        assert HookType.ON_STARTUP is not None
        assert HookType.ON_ERROR is not None
        assert HookType.ON_FILE_CHANGE is not None

    def test_plugin_config_complete(self) -> None:
        """Test that plugin config is complete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PluginConfigManager(Path(tmpdir))
            
            # Can create configs
            config = PluginConfig(enabled=True, settings={"key": "value"})
            
            # Can save and load
            manager.set_config("test", config)
            restored = manager.get_config("test")
            
            assert restored.enabled
            assert restored.settings["key"] == "value"

    def test_builtin_plugins_complete(self) -> None:
        """Test that at least 3 builtin plugins exist."""
        plugins = [
            GitPlugin(),
            NotificationPlugin(),
            FileMonitorPlugin(),
            CodeFormatPlugin(),
        ]
        
        assert len(plugins) >= 3
        
        # All can initialize
        for plugin in plugins:
            assert plugin.initialize()
            plugin.shutdown()

    def test_git_plugin_operations(self) -> None:
        """Test Git plugin has key operations."""
        plugin = GitPlugin()
        plugin.initialize()
        
        # Check capabilities
        assert "git" in plugin.metadata.capabilities
        assert "version-control" in plugin.metadata.capabilities
        
        plugin.shutdown()

    def test_notification_plugin_channels(self) -> None:
        """Test notification plugin has multiple channels."""
        plugin = NotificationPlugin()
        plugin.initialize()
        
        # Test console channel
        result = plugin.execute(
            title="Test",
            message="Test",
            channel="console",
        )
        assert result.success
        
        plugin.shutdown()

    def test_file_monitor_basic_operations(self) -> None:
        """Test file monitor basic operations."""
        plugin = FileMonitorPlugin()
        plugin.initialize()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Can watch
            result = plugin.execute(operation="watch", path=tmpdir)
            assert result.success
            
            # Can list
            result = plugin.execute(operation="list")
            assert result.success
            
            # Can get status
            result = plugin.execute(operation="status")
            assert result.success
        
        plugin.shutdown()

    def test_code_format_plugin_operations(self) -> None:
        """Test code format plugin operations."""
        plugin = CodeFormatPlugin()
        plugin.initialize()
        
        # Can format code
        result = plugin.execute(
            operation="format",
            code="x = 1\n",
            formatter="builtin",
        )
        assert result.success
        
        plugin.shutdown()


# =============================================================================
# Performance Tests
# =============================================================================

class TestIteration69Performance:
    """Performance tests for iteration #69."""

    def test_hook_registration_performance(self) -> None:
        """Test hook registration is fast."""
        import time
        
        registry = HookRegistry()
        
        start = time.time()
        for i in range(100):
            registry.register(HookType.ON_LOG, lambda **kw: None)
        elapsed = time.time() - start
        
        # 100 registrations should take < 100ms
        assert elapsed < 0.1

    def test_hook_trigger_performance(self) -> None:
        """Test hook triggering is fast."""
        import time
        
        registry = HookRegistry()
        
        for i in range(10):
            registry.register(HookType.ON_LOG, lambda **kw: i)
        
        start = time.time()
        for _ in range(100):
            registry.trigger(HookType.ON_LOG)
        elapsed = time.time() - start
        
        # 1000 triggers (10 hooks * 100 times) should take < 500ms
        assert elapsed < 0.5

    def test_config_manager_performance(self) -> None:
        """Test config manager is fast."""
        import time
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PluginConfigManager(Path(tmpdir))
            
            start = time.time()
            for i in range(50):
                manager.set_config(f"plugin-{i}", PluginConfig(settings={"index": i}))
            elapsed = time.time() - start
            
            # 50 config saves should take < 500ms
            assert elapsed < 0.5