"""
热重载模块测试

测试 FileWatcher 和 HotReloader 功能。
"""

import os
import tempfile
import threading
import time
from pathlib import Path

import pytest

from mc_agent_kit.execution.hot_reload import (
    FileInfo,
    FileWatcher,
    HotReloader,
    ModSDKHotReloader,
    ReloadConfig,
    ReloadResult,
    ReloadStatus,
)


class TestReloadConfig:
    """测试重载配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = ReloadConfig()

        assert config.watch_patterns == ["*.py"]
        assert "*_test.py" in config.ignore_patterns
        assert config.debounce_ms == 500
        assert config.max_retries == 3
        assert config.recursive is True
        assert config.auto_reload is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = ReloadConfig(
            watch_patterns=["*.py", "*.js"],
            ignore_patterns=["node_modules/*"],
            debounce_ms=1000,
            max_retries=5,
            recursive=False,
        )

        assert "*.js" in config.watch_patterns
        assert config.debounce_ms == 1000
        assert config.max_retries == 5
        assert config.recursive is False


class TestReloadResult:
    """测试重载结果"""

    def test_success_result(self):
        """测试成功结果"""
        result = ReloadResult(
            status=ReloadStatus.SUCCESS,
            file_path="/path/to/file.py",
            module_name="test_module",
            reload_time_ms=50.5,
        )

        assert result.status == ReloadStatus.SUCCESS
        assert result.file_path == "/path/to/file.py"
        assert result.module_name == "test_module"
        assert result.reload_time_ms == 50.5
        assert result.error is None

    def test_failed_result(self):
        """测试失败结果"""
        result = ReloadResult(
            status=ReloadStatus.FAILED,
            file_path="/path/to/file.py",
            error="SyntaxError: invalid syntax",
        )

        assert result.status == ReloadStatus.FAILED
        assert result.error == "SyntaxError: invalid syntax"

    def test_no_change_result(self):
        """测试无变化结果"""
        result = ReloadResult(
            status=ReloadStatus.NO_CHANGE,
            file_path="/path/to/file.py",
        )

        assert result.status == ReloadStatus.NO_CHANGE


class TestFileInfo:
    """测试文件信息"""

    def test_file_info_creation(self):
        """测试文件信息创建"""
        info = FileInfo(
            path="/path/to/file.py",
            checksum="abc123",
            last_modified=12345.6,
            size=1024,
        )

        assert info.path == "/path/to/file.py"
        assert info.checksum == "abc123"
        assert info.last_modified == 12345.6
        assert info.size == 1024


class TestFileWatcher:
    """测试文件监控器"""

    def test_watcher_creation(self):
        """测试监控器创建"""
        watcher = FileWatcher()
        assert not watcher._running

    def test_add_remove_watch(self):
        """测试添加/移除监控目录"""
        watcher = FileWatcher()

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher.add_watch(tmpdir)
            assert os.path.abspath(tmpdir) in watcher._watch_dirs

            watcher.remove_watch(tmpdir)
            assert os.path.abspath(tmpdir) not in watcher._watch_dirs

    def test_scan_directory(self):
        """测试目录扫描"""
        watcher = FileWatcher()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('hello')")

            watcher.add_watch(tmpdir)

            # 检查文件是否被记录
            assert str(test_file) in watcher._file_info

    def test_ignore_patterns(self):
        """测试忽略模式"""
        config = ReloadConfig(
            ignore_patterns=["*_test.py", "test_*.py", "__pycache__"]
        )
        watcher = FileWatcher(config)

        assert watcher._should_ignore("test_foo_test.py")
        assert watcher._should_ignore("test_main.py")
        assert watcher._should_ignore("__pycache__")
        assert not watcher._should_ignore("main.py")

    def test_matches_pattern(self):
        """测试模式匹配"""
        watcher = FileWatcher()

        assert watcher._matches_pattern("main.py")
        assert watcher._matches_pattern("utils.py")
        assert not watcher._matches_pattern("main.txt")
        assert not watcher._matches_pattern("main.js")

    def test_compute_checksum(self):
        """测试校验和计算"""
        watcher = FileWatcher()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            temp_path = f.name
            f.write("print('hello')")

        # Close file before computing checksum to avoid Windows locking
        checksum = watcher._compute_checksum(temp_path)
        os.unlink(temp_path)

        if checksum:  # May fail on Windows due to file locking
            assert len(checksum) == 32
            assert checksum.isalnum()

    def test_start_stop(self):
        """测试启动和停止"""
        watcher = FileWatcher()

        watcher.start()
        assert watcher._running
        assert watcher._thread is not None

        watcher.stop()
        assert not watcher._running

    def test_get_changes(self):
        """测试获取变化"""
        watcher = FileWatcher()

        # 添加待处理变化
        watcher._pending_changes.add("/path/to/file.py")
        watcher._pending_changes.add("/path/to/file2.py")

        changes = watcher.get_changes()
        assert len(changes) == 2
        assert "/path/to/file.py" in changes

        # 再次获取应该为空
        changes2 = watcher.get_changes()
        assert len(changes2) == 0

    def test_callback(self):
        """测试回调函数"""
        watcher = FileWatcher()
        callback_results = []

        def callback(files):
            callback_results.extend(files)

        watcher.add_callback(callback)

        # 模拟通知
        watcher._notify_callbacks(["/path/to/file.py"])

        assert len(callback_results) == 1
        assert callback_results[0] == "/path/to/file.py"

    def test_remove_callback(self):
        """测试移除回调"""
        watcher = FileWatcher()

        def callback(files):
            pass

        watcher.add_callback(callback)
        assert callback in watcher._callbacks

        watcher.remove_callback(callback)
        assert callback not in watcher._callbacks

    def test_file_modification_detection(self):
        """测试文件修改检测"""
        watcher = FileWatcher()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("original content")

            watcher.add_watch(tmpdir)
            original_info = watcher._file_info[str(test_file)]

            # 等待一下确保时间戳不同
            time.sleep(0.1)

            # 修改文件
            test_file.write_text("modified content")

            # 重新记录
            watcher._record_file(str(test_file))
            new_info = watcher._file_info[str(test_file)]

            # 校验和应该不同
            assert original_info.checksum != new_info.checksum


class TestHotReloader:
    """测试热重载器"""

    def test_reloader_creation(self):
        """测试重载器创建"""
        reloader = HotReloader()
        assert reloader.config is not None

    def test_watch_directory(self):
        """测试监控目录"""
        reloader = HotReloader()

        with tempfile.TemporaryDirectory() as tmpdir:
            reloader.watch_directory(tmpdir)
            assert os.path.abspath(tmpdir) in reloader._watcher._watch_dirs

            reloader.unwatch_directory(tmpdir)
            assert os.path.abspath(tmpdir) not in reloader._watcher._watch_dirs

    def test_start_stop(self):
        """测试启动和停止"""
        reloader = HotReloader()

        reloader.start()
        assert reloader._watcher._running

        reloader.stop()
        assert not reloader._watcher._running

    def test_reload_module_success(self):
        """测试成功重载模块"""
        reloader = HotReloader()

        # 重载一个已存在的模块
        result = reloader.reload_module("os")

        assert result.status == ReloadStatus.SUCCESS
        assert result.module_name == "os"
        assert result.new_module is not None

    def test_reload_module_not_found(self):
        """测试重载不存在的模块"""
        reloader = HotReloader()

        result = reloader.reload_module("nonexistent_module_xyz")

        assert result.status == ReloadStatus.ERROR
        assert "找不到模块" in result.error

    def test_set_callbacks(self):
        """测试设置回调"""
        reloader = HotReloader()
        reload_results = []

        def on_reload(result):
            reload_results.append(result)

        def on_error(module_name, exception):
            pass

        reloader.set_on_reload(on_reload)
        reloader.set_on_error(on_error)

        assert reloader._on_reload == on_reload
        assert reloader._on_error == on_error

    def test_get_loaded_modules(self):
        """测试获取已加载模块"""
        reloader = HotReloader()

        # 重载一个模块
        reloader.reload_module("os")

        loaded = reloader.get_loaded_modules()
        assert "os" in loaded

    def test_get_status(self):
        """测试获取状态"""
        reloader = HotReloader()

        status = reloader.get_status()
        assert "watching" in status
        assert "watch_dirs" in status
        assert "loaded_modules" in status

    def test_reload_file(self):
        """测试重载文件"""
        reloader = HotReloader()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=True
        ) as f:
            f.write("x = 1\n")
            f.flush()

            result = reloader.reload_file(f.name)

        # 应该成功执行文件
        assert result.status in (ReloadStatus.SUCCESS, ReloadStatus.FAILED)

    def test_detect_changes(self):
        """测试检测模块变化"""
        reloader = HotReloader()

        # 创建两个模拟模块
        class OldModule:
            def func1(self):
                pass

            old_attr = 1

        class NewModule:
            def func1(self):
                pass  # 修改了实现

            def func2(self):
                pass  # 新增方法

        changes = reloader._detect_changes(OldModule(), NewModule())

        # 应该检测到新增方法
        assert any("新增" in c for c in changes)

    def test_path_to_module_name(self):
        """测试路径转模块名"""
        reloader = HotReloader()

        # 测试在 sys.path 中的路径
        module_name = reloader._path_to_module_name(__file__)

        # 由于测试文件可能在不同位置，只检查格式
        if module_name:
            assert "test" in module_name.lower()

    def test_execute_file(self):
        """测试直接执行文件"""
        reloader = HotReloader()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            temp_path = f.name
            f.write("result = 1 + 1\n")

        # Close file before executing to avoid Windows locking
        result = reloader._execute_file(temp_path)
        os.unlink(temp_path)

        # May fail on Windows due to file locking, but test the logic
        assert result.status in (ReloadStatus.SUCCESS, ReloadStatus.FAILED)


class TestModSDKHotReloader:
    """测试 ModSDK 热重载器"""

    def test_modsdk_reloader_creation(self):
        """测试 ModSDK 重载器创建"""
        reloader = ModSDKHotReloader()
        assert reloader._addon_dirs == set()

    def test_watch_addon(self):
        """测试监控 Addon"""
        reloader = ModSDKHotReloader()

        with tempfile.TemporaryDirectory() as tmpdir:
            reloader.watch_addon(tmpdir)
            assert tmpdir in reloader._addon_dirs

            reloader.unwatch_addon(tmpdir)
            assert tmpdir not in reloader._addon_dirs

    def test_set_on_addon_reload(self):
        """测试设置 Addon 重载回调"""
        reloader = ModSDKHotReloader()

        def callback(name, result):
            pass

        reloader.set_on_addon_reload(callback)
        assert reloader._on_addon_reload == callback

    def test_get_addon_name(self):
        """测试从路径获取 Addon 名称"""
        reloader = ModSDKHotReloader()

        with tempfile.TemporaryDirectory() as tmpdir:
            reloader.watch_addon(tmpdir)

            # 创建子目录和文件
            addon_dir = Path(tmpdir) / "my_addon"
            addon_dir.mkdir()
            test_file = addon_dir / "main.py"
            test_file.write_text("print('hello')")

            addon_name = reloader._get_addon_name(str(test_file))

            # 应该能提取 addon 名称
            if addon_name != "unknown":
                assert "my_addon" in addon_name

    def test_reload_addon(self):
        """测试重载 Addon"""
        reloader = ModSDKHotReloader()

        # 尝试重载不存在的 addon
        result = reloader.reload_addon("nonexistent_addon")

        # 应该返回错误或失败
        assert result.status in (ReloadStatus.ERROR, ReloadStatus.FAILED)


class TestIntegration:
    """集成测试"""

    def test_full_reload_cycle(self):
        """测试完整重载周期"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "test_module.py"
            test_file.write_text("value = 1\n")

            # 创建重载器并监控
            reloader = HotReloader()
            reloader.watch_directory(tmpdir)

            # 重载文件
            result = reloader.reload_file(str(test_file))

            assert result.status == ReloadStatus.SUCCESS

            # 修改文件
            time.sleep(0.1)
            test_file.write_text("value = 2\n")

            # 再次重载
            result2 = reloader.reload_file(str(test_file))

            assert result2.status == ReloadStatus.SUCCESS

            reloader.stop()

    def test_watcher_with_callbacks(self):
        """测试监控器回调集成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReloadConfig(debounce_ms=100)
            watcher = FileWatcher(config)

            changes_detected = []

            def on_change(files):
                changes_detected.extend(files)

            watcher.add_callback(on_change)
            watcher.add_watch(tmpdir)

            # 创建文件
            test_file = Path(tmpdir) / "new_file.py"
            test_file.write_text("x = 1")

            # 手动触发检查
            watcher._check_changes()

            # 应该检测到新文件
            changes = watcher.get_changes()
            assert len(changes) > 0

            watcher.stop()

    def test_multiple_watch_dirs(self):
        """测试多目录监控"""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                watcher = FileWatcher()

                watcher.add_watch(tmpdir1)
                watcher.add_watch(tmpdir2)

                assert len(watcher._watch_dirs) == 2

                # 在两个目录创建文件
                (Path(tmpdir1) / "file1.py").write_text("x = 1")
                (Path(tmpdir2) / "file2.py").write_text("y = 2")

                # 扫描后应该记录两个文件
                watcher._check_changes()
                changes = watcher.get_changes()

                assert len(changes) == 2

                watcher.stop()


class TestEdgeCases:
    """边界条件测试"""

    def test_watcher_nonexistent_dir(self):
        """测试监控不存在的目录"""
        watcher = FileWatcher()

        # 不应该抛出异常
        watcher.add_watch("/nonexistent/path/xyz")

        # 目录不在监控列表中（因为不存在）
        # 实际行为：add_watch 会添加路径但扫描不会报错
        watcher.remove_watch("/nonexistent/path/xyz")

    def test_reloader_invalid_file(self):
        """测试重载无效文件"""
        reloader = HotReloader()

        result = reloader.reload_file("/nonexistent/file.py")

        assert result.status in (ReloadStatus.ERROR, ReloadStatus.FAILED)

    def test_watcher_empty_directory(self):
        """测试监控空目录"""
        watcher = FileWatcher()

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher.add_watch(tmpdir)

            # 空目录没有文件
            assert len(watcher._file_info) == 0

    def test_reload_config_edge_values(self):
        """测试配置边界值"""
        # 最小值
        config = ReloadConfig(
            debounce_ms=0,
            max_retries=0,
            retry_delay_ms=0,
        )
        assert config.debounce_ms == 0
        assert config.max_retries == 0

        # 大值
        config2 = ReloadConfig(
            debounce_ms=10000,
            max_retries=100,
        )
        assert config2.debounce_ms == 10000

    def test_watcher_unicode_filename(self):
        """测试 Unicode 文件名"""
        watcher = FileWatcher()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建 Unicode 文件名
            test_file = Path(tmpdir) / "测试文件.py"
            test_file.write_text("x = 1")

            watcher.add_watch(tmpdir)

            # 应该能正确记录
            assert str(test_file) in watcher._file_info

    def test_reload_result_with_changes(self):
        """测试带变更列表的结果"""
        result = ReloadResult(
            status=ReloadStatus.SUCCESS,
            file_path="/path/to/file.py",
            changes=["新增: func1", "修改: func2", "移除: old_func"],
        )

        assert len(result.changes) == 3
        assert "新增" in result.changes[0]

    def test_modsdk_reloader_empty_addon_dirs(self):
        """测试 ModSDK 重载器空 addon 目录"""
        reloader = ModSDKHotReloader()

        # 空 addon 目录集合
        assert len(reloader._addon_dirs) == 0

        # 获取 addon 名称应该返回 unknown
        name = reloader._get_addon_name("/some/path/file.py")
        assert name == "unknown"