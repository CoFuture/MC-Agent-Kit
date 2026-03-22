"""
迭代 #25 测试 - 提高测试覆盖率

测试目标:
- plugin/sandbox.py
- plugin/hot_reload.py
- plugin/dependency.py
"""

from pathlib import Path

import pytest

from mc_agent_kit.plugin import (
    Dependency,
    DependencyManager,
    DependencyReport,
    DependencyType,
    HotReloadConfig,
    PluginHotReloader,
    PluginManager,
    SandboxConfig,
    SandboxPermission,
)
from mc_agent_kit.plugin.sandbox import CodeValidator


class TestSandboxConfigEnhanced:
    """SandboxConfig 增强测试"""

    def test_full_permission(self) -> None:
        """测试完全权限"""
        config = SandboxConfig.full_access()
        assert config.permission == SandboxPermission.FULL
        assert config.allow_network is True
        assert config.allow_subprocess is True
        assert config.allow_file_write is True

    def test_restricted_permission(self) -> None:
        """测试受限权限"""
        config = SandboxConfig.restricted()
        assert config.permission == SandboxPermission.RESTRICTED
        assert config.allow_network is False
        assert config.allow_subprocess is False
        assert config.allow_file_write is False

    def test_custom_allowed_modules(self) -> None:
        """测试自定义允许模块"""
        config = SandboxConfig(
            allowed_modules=["json", "re", "math"],
            blocked_modules=[]
        )
        assert "json" in config.allowed_modules
        assert "re" in config.allowed_modules

    def test_path_restrictions(self) -> None:
        """测试路径限制"""
        config = SandboxConfig(
            allowed_paths=["/data"],
            blocked_paths=["/etc/passwd"]
        )
        assert "/data" in config.allowed_paths
        assert "/etc/passwd" in config.blocked_paths

    def test_to_dict(self) -> None:
        """测试序列化为字典"""
        config = SandboxConfig.restricted()
        data = config.to_dict()
        assert "permission" in data
        assert "allowed_modules" in data


class TestCodeValidator:
    """CodeValidator 测试"""

    def test_validate_dangerous_import(self) -> None:
        """测试危险导入检测"""
        code = """
import os
os.system("rm -rf /")
"""
        config = SandboxConfig()
        validator = CodeValidator(config)
        result, violations = validator.validate(code)
        assert result is False  # 有违规

    def test_validate_subprocess(self) -> None:
        """测试 subprocess 检测"""
        code = """
import subprocess
subprocess.run(["ls"])
"""
        config = SandboxConfig()
        validator = CodeValidator(config)
        result, violations = validator.validate(code)
        assert result is False

    def test_validate_eval(self) -> None:
        """测试 eval/exec 检测"""
        code = """
result = eval("1 + 1")
"""
        config = SandboxConfig()
        validator = CodeValidator(config)
        result, violations = validator.validate(code)
        assert result is False


class TestDependencyEnhanced:
    """Dependency 增强测试"""

    def test_dependency_to_dict(self) -> None:
        """测试依赖序列化"""
        dep = Dependency(
            name="requests",
            type=DependencyType.PYTHON,
            version_range=">=2.28.0",
            optional=False
        )
        data = dep.to_dict()
        assert data["name"] == "requests"
        assert data["version_range"] == ">=2.28.0"
        assert data["type"] == "python"

    def test_dependency_from_dict(self) -> None:
        """测试从字典创建依赖"""
        data = {
            "name": "numpy",
            "version_range": ">=1.20.0",
            "type": "python",
            "optional": True
        }
        dep = Dependency.from_dict(data)
        assert dep.name == "numpy"
        assert dep.version_range == ">=1.20.0"
        assert dep.optional is True


class TestDependencyManagerEnhanced:
    """DependencyManager 增强测试"""

    def test_check_dependencies(self) -> None:
        """测试检查依赖"""
        manager = DependencyManager()
        deps = [
            Dependency(name="pytest", type=DependencyType.PYTHON),
            Dependency(name="nonexistent_xyz", type=DependencyType.PYTHON, optional=True)
        ]
        report = manager.check_dependencies(deps)
        assert isinstance(report, DependencyReport)

    def test_get_installed_packages(self) -> None:
        """测试获取已安装包列表"""
        manager = DependencyManager()
        packages = manager.get_installed_packages()
        assert isinstance(packages, dict)
        # pytest 应该在列表中
        assert any("pytest" in pkg.lower() for pkg in packages.keys())


class TestHotReloadConfigEnhanced:
    """HotReloadConfig 增强测试"""

    def test_custom_exclude_patterns(self) -> None:
        """测试自定义排除模式"""
        config = HotReloadConfig(
            exclude_patterns=["*.log", "*.tmp", "docs/*"]
        )
        assert "*.log" in config.exclude_patterns
        assert "*.tmp" in config.exclude_patterns

    def test_notify_callback_callable(self) -> None:
        """测试通知回调可调用"""
        called = []

        def notify(name: str, success: bool, msg: str) -> None:
            called.append((name, success, msg))

        config = HotReloadConfig(notify_callback=notify)
        assert config.notify_callback is not None
        config.notify_callback("test", True, "ok")
        assert len(called) == 1


class TestPluginHotReloaderEnhanced:
    """PluginHotReloader 增强测试"""

    def test_watch_nonexistent_directory(self) -> None:
        """测试监控不存在的目录"""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        # 监控不存在的目录应该不抛出异常
        reloader.watch_directory(Path("/nonexistent/path/xyz"))

    def test_unwatch_nonexistent_plugin(self) -> None:
        """测试取消监控不存在的插件"""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        # 取消监控不存在的插件应该不抛出异常
        reloader.unwatch_plugin("nonexistent_plugin")

    def test_multiple_callbacks(self) -> None:
        """测试多个回调"""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        calls = []

        def callback1(event) -> None:
            calls.append(("cb1", event.plugin_name))

        def callback2(event) -> None:
            calls.append(("cb2", event.plugin_name))

        reloader.add_reload_callback(callback1)
        reloader.add_reload_callback(callback2)

        assert len(reloader._on_reload_callbacks) == 2

        reloader.remove_reload_callback(callback1)
        assert len(reloader._on_reload_callbacks) == 1

    def test_events_limit(self) -> None:
        """测试事件数量限制"""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        # 添加大量事件
        for i in range(150):
            from mc_agent_kit.plugin import ReloadEvent
            reloader._record_event(ReloadEvent(
                plugin_name=f"plugin_{i}",
                file_path=f"/path/{i}",
                success=True
            ))

        # 应该有限制
        events = reloader.get_events(limit=200)
        assert len(events) <= 100  # 默认限制

    def test_start_stop_thread_safety(self) -> None:
        """测试启动停止线程安全"""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        # 多次启动应该安全
        reloader.start()
        assert reloader._running is True

        # 重复启动应该无效果
        reloader.start()
        assert reloader._running is True

        reloader.stop()
        assert reloader._running is False

        # 重复停止应该无效果
        reloader.stop()
        assert reloader._running is False

    def test_get_status_empty(self) -> None:
        """测试空状态"""
        manager = PluginManager()
        reloader = PluginHotReloader(manager)

        status = reloader.get_status()
        assert status["running"] is False
        assert status["watched_count"] == 0
        assert status["watched_plugins"] == []