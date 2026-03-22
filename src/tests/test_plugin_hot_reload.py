"""Tests for plugin hot reload functionality."""

import tempfile
import time
from pathlib import Path

import pytest

from mc_agent_kit.plugin import (
    HotReloadConfig,
    PluginHotReloader,
    PluginManager,
    ReloadEvent,
    WatchedPlugin,
)


class TestHotReloadConfig:
    """Tests for HotReloadConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = HotReloadConfig()
        assert config.watch_interval_ms == 500
        assert config.debounce_ms == 300
        assert config.auto_enable is True
        assert config.notify_callback is None
        assert "__pycache__" in config.exclude_patterns

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = HotReloadConfig(
            watch_interval_ms=1000,
            debounce_ms=500,
            auto_enable=False,
        )
        assert config.watch_interval_ms == 1000
        assert config.debounce_ms == 500
        assert config.auto_enable is False

    def test_notify_callback(self) -> None:
        """Test notify callback."""
        called = []

        def callback(name: str, success: bool, msg: str) -> None:
            called.append((name, success, msg))

        config = HotReloadConfig(notify_callback=callback)
        assert config.notify_callback is not None
        config.notify_callback("test", True, "OK")
        assert called == [("test", True, "OK")]


class TestReloadEvent:
    """Tests for ReloadEvent."""

    def test_basic_event(self) -> None:
        """Test basic event creation."""
        event = ReloadEvent(
            plugin_name="test_plugin",
            file_path="/path/to/plugin",
            success=True,
        )
        assert event.plugin_name == "test_plugin"
        assert event.success is True
        assert event.error is None
        assert event.reload_time_ms == 0.0

    def test_failed_event(self) -> None:
        """Test failed event."""
        event = ReloadEvent(
            plugin_name="test",
            file_path="/path",
            success=False,
            error="Something went wrong",
        )
        assert event.success is False
        assert event.error == "Something went wrong"


class TestWatchedPlugin:
    """Tests for WatchedPlugin."""

    def test_basic_watched_plugin(self) -> None:
        """Test basic watched plugin."""
        plugin = WatchedPlugin(
            name="test",
            path=Path("/plugins/test"),
        )
        assert plugin.name == "test"
        assert plugin.last_modified == 0.0
        assert plugin.checksum == ""

    def test_watched_plugin_with_checksum(self) -> None:
        """Test watched plugin with checksum."""
        plugin = WatchedPlugin(
            name="test",
            path=Path("/plugins/test"),
            last_modified=12345.0,
            checksum="abc123",
        )
        assert plugin.last_modified == 12345.0
        assert plugin.checksum == "abc123"


class TestPluginHotReloader:
    """Tests for PluginHotReloader."""

    def test_init(self) -> None:
        """Test initialization."""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)
        assert reloader.manager is manager
        assert reloader.config is not None

    def test_init_with_config(self) -> None:
        """Test initialization with config."""
        manager = PluginManager()
        config = HotReloadConfig(watch_interval_ms=1000)
        reloader = PluginHotReloader(manager, config)
        assert reloader.config.watch_interval_ms == 1000

    def test_watch_plugin(self) -> None:
        """Test watching a plugin."""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_path = Path(tmpdir) / "test_plugin"
            plugin_path.mkdir()

            reloader.watch_plugin("test_plugin", plugin_path)
            assert "test_plugin" in reloader._watched

    def test_unwatch_plugin(self) -> None:
        """Test unwatching a plugin."""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_path = Path(tmpdir) / "test_plugin"
            plugin_path.mkdir()

            reloader.watch_plugin("test_plugin", plugin_path)
            assert "test_plugin" in reloader._watched

            result = reloader.unwatch_plugin("test_plugin")
            assert result is True
            assert "test_plugin" not in reloader._watched

    def test_unwatch_nonexistent_plugin(self) -> None:
        """Test unwatching a plugin that doesn't exist."""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        result = reloader.unwatch_plugin("nonexistent")
        assert result is False

    def test_watch_directory(self) -> None:
        """Test watching a directory."""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create plugin directories with manifests
            plugin1 = Path(tmpdir) / "plugin1"
            plugin1.mkdir()
            (plugin1 / "plugin.json").write_text('{"name": "plugin1"}')

            plugin2 = Path(tmpdir) / "plugin2"
            plugin2.mkdir()
            (plugin2 / "plugin.json").write_text('{"name": "plugin2"}')

            # Directory without manifest (should be ignored)
            not_a_plugin = Path(tmpdir) / "not_a_plugin"
            not_a_plugin.mkdir()

            reloader.watch_directory(tmpdir)
            assert "plugin1" in reloader._watched
            assert "plugin2" in reloader._watched
            assert "not_a_plugin" not in reloader._watched

    def test_start_stop(self) -> None:
        """Test start and stop."""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        assert reloader._running is False

        reloader.start()
        assert reloader._running is True

        reloader.stop()
        assert reloader._running is False

    def test_get_status(self) -> None:
        """Test getting status."""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        status = reloader.get_status()
        assert status["running"] is False
        assert status["watched_count"] == 0
        assert status["watched_plugins"] == []

    def test_get_status_with_plugins(self) -> None:
        """Test getting status with watched plugins."""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_path = Path(tmpdir) / "test"
            plugin_path.mkdir()
            reloader.watch_plugin("test", plugin_path)

            status = reloader.get_status()
            assert status["watched_count"] == 1
            assert "test" in status["watched_plugins"]

    def test_reload_plugin_not_watched(self) -> None:
        """Test reloading a plugin that's not watched."""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        event = reloader.reload_plugin("nonexistent")
        assert event.success is False
        assert "not being watched" in event.error

    def test_reload_callback(self) -> None:
        """Test reload callback."""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        events: list[ReloadEvent] = []

        def on_reload(event: ReloadEvent) -> None:
            events.append(event)

        reloader.add_reload_callback(on_reload)

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_path = Path(tmpdir) / "test"
            plugin_path.mkdir()
            reloader.watch_plugin("test", plugin_path)

            # Trigger reload
            event = reloader.reload_plugin("test")
            assert len(events) == 1
            assert events[0].plugin_name == "test"

    def test_remove_callback(self) -> None:
        """Test removing callback."""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        def callback(event: ReloadEvent) -> None:
            pass

        reloader.add_reload_callback(callback)
        assert callback in reloader._on_reload_callbacks

        reloader.remove_reload_callback(callback)
        assert callback not in reloader._on_reload_callbacks

    def test_get_events(self) -> None:
        """Test getting events."""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        # Add some events manually
        for i in range(5):
            reloader._record_event(
                ReloadEvent(
                    plugin_name=f"plugin_{i}",
                    file_path=f"/path/{i}",
                    success=True,
                )
            )

        events = reloader.get_events()
        assert len(events) == 5

        events_limited = reloader.get_events(limit=2)
        assert len(events_limited) == 2

    def test_max_events_limit(self) -> None:
        """Test that events are trimmed at max limit."""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        # Add more than max events
        for i in range(150):
            reloader._record_event(
                ReloadEvent(
                    plugin_name=f"plugin_{i}",
                    file_path=f"/path/{i}",
                    success=True,
                )
            )

        # Should be trimmed to max
        assert len(reloader._events) == reloader._max_events


class TestPluginHotReloaderIntegration:
    """Integration tests for PluginHotReloader."""

    def test_file_change_detection(self) -> None:
        """Test file change detection."""
        manager = PluginManager()
        config = HotReloadConfig(
            watch_interval_ms=100,
            debounce_ms=50,
        )
        reloader = PluginHotReloader(manager, config)

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_path = Path(tmpdir) / "test_plugin"
            plugin_path.mkdir()
            plugin_file = plugin_path / "test.py"
            plugin_file.write_text("# initial content")

            reloader.watch_plugin("test_plugin", plugin_path)

            # Get initial checksum
            initial_checksum = reloader._watched["test_plugin"].checksum

            # Modify the file
            time.sleep(0.1)  # Ensure different timestamp
            plugin_file.write_text("# modified content")

            # Compute new checksum
            new_checksum = reloader._compute_checksum(plugin_path)

            assert initial_checksum != new_checksum

    def test_excluded_files(self) -> None:
        """Test that excluded files are ignored."""
        manager = PluginManager()
        config = HotReloadConfig(
            exclude_patterns=["*.pyc", "__pycache__", "test_*"],
        )
        reloader = PluginHotReloader(manager, config)

        from pathlib import PurePath

        assert reloader._should_exclude(PurePath("__pycache__"))
        assert reloader._should_exclude(PurePath("module.pyc"))
        assert reloader._should_exclude(PurePath("test_module.py"))
        assert not reloader._should_exclude(PurePath("main.py"))

    def test_notify_callback_on_reload(self) -> None:
        """Test that notify callback is called on reload."""
        notified = []

        def notify(name: str, success: bool, msg: str) -> None:
            notified.append((name, success, msg))

        manager = PluginManager()
        config = HotReloadConfig(notify_callback=notify)
        reloader = PluginHotReloader(manager, config)

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_path = Path(tmpdir) / "test"
            plugin_path.mkdir()
            reloader.watch_plugin("test", plugin_path)

            reloader.reload_plugin("test")

            assert len(notified) == 1
            assert notified[0][0] == "test"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_hot_reloader(self) -> None:
        """Test create_hot_reloader function."""
        from mc_agent_kit.plugin.hot_reload import create_hot_reloader

        manager = PluginManager()
        config = HotReloadConfig(watch_interval_ms=1000)

        with tempfile.TemporaryDirectory() as tmpdir:
            reloader = create_hot_reloader(
                manager,
                watch_dirs=[tmpdir],
                config=config,
            )

            assert reloader.manager is manager
            assert reloader.config.watch_interval_ms == 1000

    def test_reload_all_plugins(self) -> None:
        """Test reload_all_plugins function."""
        from mc_agent_kit.plugin.hot_reload import reload_all_plugins

        manager = PluginManager()

        # No plugins loaded, should return empty list
        events = reload_all_plugins(manager)
        assert events == []


class TestHotReloadAPI:
    """Tests for the public API."""

    def test_imports_from_init(self) -> None:
        """Test that classes can be imported from plugin module."""
        from mc_agent_kit.plugin import (
            HotReloadConfig,
            HotReloadStatus,
            PluginHotReloader,
            ReloadEvent,
            WatchedPlugin,
            create_hot_reloader,
            reload_all_plugins,
        )

        assert HotReloadConfig is not None
        assert HotReloadStatus is not None
        assert PluginHotReloader is not None
        assert ReloadEvent is not None
        assert WatchedPlugin is not None
        assert create_hot_reloader is not None
        assert reload_all_plugins is not None

    def test_hot_reload_status_enum(self) -> None:
        """Test HotReloadStatus enum."""
        from mc_agent_kit.plugin import HotReloadStatus

        assert HotReloadStatus.ENABLED.value == "enabled"
        assert HotReloadStatus.DISABLED.value == "disabled"
        assert HotReloadStatus.ERROR.value == "error"