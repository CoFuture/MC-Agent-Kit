"""
热重载模块

提供代码热重载功能，支持文件监控和自动重载。
"""

import hashlib
import importlib
import importlib.util
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ReloadStatus(Enum):
    """重载状态"""

    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    NO_CHANGE = "no_change"  # 无变化
    SKIPPED = "skipped"  # 跳过
    ERROR = "error"  # 错误


@dataclass
class ReloadConfig:
    """重载配置"""

    watch_patterns: list[str] = field(default_factory=lambda: ["*.py"])  # 监控文件模式
    ignore_patterns: list[str] = field(
        default_factory=lambda: ["*_test.py", "test_*.py", "__pycache__/*"]
    )  # 忽略模式
    debounce_ms: int = 500  # 防抖时间（毫秒）
    max_retries: int = 3  # 最大重试次数
    retry_delay_ms: int = 100  # 重试延迟（毫秒）
    recursive: bool = True  # 递归监控子目录
    auto_reload: bool = True  # 自动重载
    notify_on_reload: bool = True  # 重载时通知


@dataclass
class ReloadResult:
    """重载结果"""

    status: ReloadStatus
    file_path: str
    module_name: str | None = None
    old_module: Any = None
    new_module: Any = None
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    reload_time_ms: float = 0.0  # 重载耗时（毫秒）
    changes: list[str] = field(default_factory=list)  # 变更描述


@dataclass
class FileInfo:
    """文件信息"""

    path: str
    checksum: str
    last_modified: float
    size: int


class FileWatcher:
    """
    文件监控器。

    监控文件变化，支持：
    - 文件修改检测
    - 文件新增/删除检测
    - 防抖处理
    - 模式过滤

    使用示例:
        watcher = FileWatcher()
        watcher.add_watch("/path/to/dir")
        watcher.start()
        
        # 检查变化
        changes = watcher.get_changes()
        
        watcher.stop()
    """

    def __init__(self, config: ReloadConfig | None = None):
        """
        初始化文件监控器。

        Args:
            config: 监控配置
        """
        self.config = config or ReloadConfig()
        self._watch_dirs: set[str] = set()
        self._file_info: dict[str, FileInfo] = {}
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._callbacks: list[Callable[[list[str]], None]] = []
        self._pending_changes: set[str] = set()
        self._last_change_time: float = 0

    def add_watch(self, path: str) -> None:
        """
        添加监控目录。

        Args:
            path: 目录路径
        """
        with self._lock:
            self._watch_dirs.add(os.path.abspath(path))
            self._scan_directory(path)

    def remove_watch(self, path: str) -> None:
        """
        移除监控目录。

        Args:
            path: 目录路径
        """
        with self._lock:
            abs_path = os.path.abspath(path)
            self._watch_dirs.discard(abs_path)
            # 移除该目录下的文件信息
            to_remove = [f for f in self._file_info if f.startswith(abs_path)]
            for f in to_remove:
                del self._file_info[f]

    def start(self) -> None:
        """开始监控"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def get_changes(self) -> list[str]:
        """
        获取变化的文件列表。

        Returns:
            变化的文件路径列表
        """
        with self._lock:
            changes = list(self._pending_changes)
            self._pending_changes.clear()
            return changes

    def add_callback(self, callback: Callable[[list[str]], None]) -> None:
        """添加变化回调"""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[list[str]], None]) -> None:
        """移除变化回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _scan_directory(self, path: str) -> None:
        """扫描目录并记录文件信息"""
        if not os.path.exists(path):
            return

        for root, dirs, files in os.walk(path):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if not self._should_ignore(d)]

            for file in files:
                file_path = os.path.join(root, file)

                if self._should_ignore(file):
                    continue

                if not self._matches_pattern(file):
                    continue

                self._record_file(file_path)

    def _record_file(self, file_path: str) -> None:
        """记录文件信息"""
        try:
            stat = os.stat(file_path)
            checksum = self._compute_checksum(file_path)

            self._file_info[file_path] = FileInfo(
                path=file_path,
                checksum=checksum,
                last_modified=stat.st_mtime,
                size=stat.st_size,
            )
        except Exception as e:
            logger.warning(f"记录文件信息失败: {file_path}: {e}")

    def _compute_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def _matches_pattern(self, filename: str) -> bool:
        """检查文件是否匹配监控模式"""
        from fnmatch import fnmatch

        for pattern in self.config.watch_patterns:
            if fnmatch(filename, pattern):
                return True
        return False

    def _should_ignore(self, name: str) -> bool:
        """检查是否应该忽略"""
        from fnmatch import fnmatch

        for pattern in self.config.ignore_patterns:
            if fnmatch(name, pattern):
                return True
        return False

    def _watch_loop(self) -> None:
        """监控循环"""
        while self._running:
            try:
                self._check_changes()
            except Exception as e:
                logger.error(f"检查变化失败: {e}")

            time.sleep(0.5)

    def _check_changes(self) -> None:
        """检查文件变化"""
        current_time = time.time()
        changed_files: list[str] = []

        with self._lock:
            for watch_dir in self._watch_dirs:
                if not os.path.exists(watch_dir):
                    continue

                for root, dirs, files in os.walk(watch_dir):
                    dirs[:] = [d for d in dirs if not self._should_ignore(d)]

                    for file in files:
                        file_path = os.path.join(root, file)

                        if self._should_ignore(file) or not self._matches_pattern(file):
                            continue

                        if file_path not in self._file_info:
                            # 新文件
                            changed_files.append(file_path)
                            self._record_file(file_path)
                        else:
                            # 检查变化
                            try:
                                stat = os.stat(file_path)
                                old_info = self._file_info[file_path]

                                if (
                                    stat.st_mtime > old_info.last_modified
                                    or stat.st_size != old_info.size
                                ):
                                    new_checksum = self._compute_checksum(file_path)
                                    if new_checksum != old_info.checksum:
                                        changed_files.append(file_path)
                                        self._record_file(file_path)
                            except Exception:
                                pass

        if changed_files:
            self._pending_changes.update(changed_files)
            self._last_change_time = current_time

            # 防抖后触发回调
            if current_time - self._last_change_time >= self.config.debounce_ms / 1000:
                self._notify_callbacks(list(self._pending_changes))


    def _notify_callbacks(self, changed_files: list[str]) -> None:
        """通知回调"""
        for callback in self._callbacks:
            try:
                callback(changed_files)
            except Exception as e:
                logger.error(f"回调执行失败: {e}")


class HotReloader:
    """
    热重载器。

    支持模块热重载和文件监控自动重载。

    使用示例:
        reloader = HotReloader()
        
        # 手动重载
        result = reloader.reload_module("my_module")
        
        # 自动监控重载
        reloader.watch_directory("/path/to/project")
        reloader.start()
        
        # 停止
        reloader.stop()
    """

    def __init__(self, config: ReloadConfig | None = None):
        """
        初始化热重载器。

        Args:
            config: 重载配置
        """
        self.config = config or ReloadConfig()
        self._watcher = FileWatcher(self.config)
        self._loaded_modules: dict[str, Any] = {}
        self._module_files: dict[str, str] = {}  # 模块名 -> 文件路径
        self._on_reload: Callable[[ReloadResult], None] | None = None
        self._on_error: Callable[[str, Exception], None] | None = None
        self._reloading = False

    def watch_directory(self, path: str) -> None:
        """
        监控目录。

        Args:
            path: 目录路径
        """
        self._watcher.add_watch(path)

    def unwatch_directory(self, path: str) -> None:
        """
        取消监控目录。

        Args:
            path: 目录路径
        """
        self._watcher.remove_watch(path)

    def start(self) -> None:
        """开始监控和自动重载"""
        if self.config.auto_reload:
            self._watcher.add_callback(self._on_file_changed)
        self._watcher.start()

    def stop(self) -> None:
        """停止监控"""
        self._watcher.stop()

    def reload_module(self, module_name: str) -> ReloadResult:
        """
        重载模块。

        Args:
            module_name: 模块名

        Returns:
            ReloadResult: 重载结果
        """
        start_time = time.time()

        try:
            # 获取旧模块
            old_module = sys.modules.get(module_name)

            # 查找模块文件
            spec = importlib.util.find_spec(module_name)
            if not spec or not spec.origin:
                return ReloadResult(
                    status=ReloadStatus.ERROR,
                    file_path="",
                    module_name=module_name,
                    error=f"找不到模块: {module_name}",
                )

            file_path = spec.origin

            # 记录模块文件映射
            self._module_files[module_name] = file_path

            # 保存旧模块的引用
            if old_module:
                self._loaded_modules[module_name] = old_module

            # 重新加载模块
            new_module = importlib.reload(old_module) if old_module else importlib.import_module(module_name)

            # 计算耗时
            reload_time = (time.time() - start_time) * 1000

            # 比较新旧模块，找出变化
            changes = self._detect_changes(old_module, new_module)

            result = ReloadResult(
                status=ReloadStatus.SUCCESS,
                file_path=file_path,
                module_name=module_name,
                old_module=old_module,
                new_module=new_module,
                reload_time_ms=reload_time,
                changes=changes,
            )

            # 通知回调
            if self._on_reload:
                self._on_reload(result)

            return result

        except Exception as e:
            logger.error(f"重载模块失败: {module_name}: {e}")

            if self._on_error:
                self._on_error(module_name, e)

            return ReloadResult(
                status=ReloadStatus.FAILED,
                file_path=self._module_files.get(module_name, ""),
                module_name=module_name,
                error=str(e),
                reload_time_ms=(time.time() - start_time) * 1000,
            )

    def reload_file(self, file_path: str) -> ReloadResult:
        """
        重载文件。

        Args:
            file_path: 文件路径

        Returns:
            ReloadResult: 重载结果
        """
        # 将文件路径转换为模块名
        module_name = self._path_to_module_name(file_path)

        if module_name:
            return self.reload_module(module_name)

        # 如果无法转换为模块名，尝试直接执行文件
        return self._execute_file(file_path)

    def _path_to_module_name(self, file_path: str) -> str | None:
        """将文件路径转换为模块名"""
        # 在 sys.path 中查找匹配的路径
        abs_path = os.path.abspath(file_path)

        for path in sys.path:
            if abs_path.startswith(path):
                rel_path = os.path.relpath(abs_path, path)
                module_name = rel_path.replace(os.sep, ".").replace("/", ".")
                if module_name.endswith(".py"):
                    module_name = module_name[:-3]
                if module_name.endswith(".__init__"):
                    module_name = module_name[:-9]
                return module_name

        return None

    def _execute_file(self, file_path: str) -> ReloadResult:
        """直接执行文件"""
        start_time = time.time()

        try:
            # 创建新的模块命名空间
            module_name = f"_hot_reload_{hashlib.md5(file_path.encode()).hexdigest()[:8]}"

            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                return ReloadResult(
                    status=ReloadStatus.ERROR,
                    file_path=file_path,
                    error="无法创建模块规范",
                )

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            reload_time = (time.time() - start_time) * 1000

            return ReloadResult(
                status=ReloadStatus.SUCCESS,
                file_path=file_path,
                module_name=module_name,
                new_module=module,
                reload_time_ms=reload_time,
            )

        except Exception as e:
            return ReloadResult(
                status=ReloadStatus.FAILED,
                file_path=file_path,
                error=str(e),
                reload_time_ms=(time.time() - start_time) * 1000,
            )

    def _detect_changes(self, old_module: Any, new_module: Any) -> list[str]:
        """检测模块变化"""
        changes = []

        if old_module is None:
            return ["首次加载"]

        old_attrs = set(dir(old_module))
        new_attrs = set(dir(new_module))

        # 新增的属性
        added = new_attrs - old_attrs
        for attr in added:
            if not attr.startswith("_"):
                changes.append(f"新增: {attr}")

        # 移除的属性
        removed = old_attrs - new_attrs
        for attr in removed:
            if not attr.startswith("_"):
                changes.append(f"移除: {attr}")

        # 变化的函数/类
        for attr in old_attrs & new_attrs:
            if attr.startswith("_"):
                continue

            old_val = getattr(old_module, attr, None)
            new_val = getattr(new_module, attr, None)

            if callable(old_val) and callable(new_val):
                if hasattr(old_val, "__code__") and hasattr(new_val, "__code__"):
                    if old_val.__code__.co_code != new_val.__code__.co_code:
                        changes.append(f"修改: {attr}")

        return changes

    def _on_file_changed(self, changed_files: list[str]) -> None:
        """文件变化回调"""
        for file_path in changed_files:
            if file_path.endswith(".py"):
                result = self.reload_file(file_path)
                logger.info(f"重载 {file_path}: {result.status.value}")

    def set_on_reload(self, callback: Callable[[ReloadResult], None]) -> None:
        """设置重载回调"""
        self._on_reload = callback

    def set_on_error(self, callback: Callable[[str, Exception], None]) -> None:
        """设置错误回调"""
        self._on_error = callback

    def get_loaded_modules(self) -> dict[str, Any]:
        """获取已加载的模块"""
        return self._loaded_modules.copy()

    def get_status(self) -> dict[str, Any]:
        """获取重载器状态"""
        return {
            "watching": self._watcher._running,
            "watch_dirs": list(self._watcher._watch_dirs),
            "loaded_modules": len(self._loaded_modules),
            "tracked_files": len(self._module_files),
        }


class ModSDKHotReloader(HotReloader):
    """
    ModSDK 专用的热重载器。

    针对 ModSDK 开发环境优化：
    - 支持 Addon 目录监控
    - 支持配置文件重载
    - 支持资源文件更新通知
    """

    def __init__(self, config: ReloadConfig | None = None):
        super().__init__(config)
        self._addon_dirs: set[str] = set()
        self._on_addon_reload: Callable[[str, ReloadResult], None] | None = None

    def watch_addon(self, addon_path: str) -> None:
        """
        监控 Addon 目录。

        Args:
            addon_path: Addon 目录路径
        """
        self._addon_dirs.add(addon_path)
        self.watch_directory(addon_path)

    def unwatch_addon(self, addon_path: str) -> None:
        """
        取消监控 Addon 目录。

        Args:
            addon_path: Addon 目录路径
        """
        self._addon_dirs.discard(addon_path)
        self.unwatch_directory(addon_path)

    def reload_addon(self, addon_name: str) -> ReloadResult:
        """
        重载 Addon。

        Args:
            addon_name: Addon 名称

        Returns:
            ReloadResult: 重载结果
        """
        # 查找 Addon 的主模块
        module_name = f"addons.{addon_name}"
        return self.reload_module(module_name)

    def set_on_addon_reload(self, callback: Callable[[str, ReloadResult], None]) -> None:
        """设置 Addon 重载回调"""
        self._on_addon_reload = callback

    def _on_file_changed(self, changed_files: list[str]) -> None:
        """文件变化回调（覆盖父类）"""
        for file_path in changed_files:
            # 检查是否在 Addon 目录下
            is_addon = any(
                file_path.startswith(addon_dir) for addon_dir in self._addon_dirs
            )

            if file_path.endswith(".py"):
                result = self.reload_file(file_path)
                logger.info(f"重载 {file_path}: {result.status.value}")

                if is_addon and self._on_addon_reload:
                    addon_name = self._get_addon_name(file_path)
                    self._on_addon_reload(addon_name, result)

            elif file_path.endswith((".json", ".mcfunction", ".mcstructure")):
                # 资源文件变化，通知但不重载
                logger.info(f"资源文件变化: {file_path}")

    def _get_addon_name(self, file_path: str) -> str:
        """从文件路径获取 Addon 名称"""
        for addon_dir in self._addon_dirs:
            if file_path.startswith(addon_dir):
                rel_path = os.path.relpath(file_path, addon_dir)
                parts = rel_path.split(os.sep)
                if parts:
                    return parts[0]
        return "unknown"