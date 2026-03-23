"""
性能优化模块

提供缓存增强、并行处理、懒加载等性能优化功能。
"""

from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import os
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class CacheMetrics:
    """缓存指标"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size: int = 0
    max_size: int = 0
    created_at: float = field(default_factory=time.time)

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0.0

    @property
    def uptime(self) -> float:
        return time.time() - self.created_at


class EnhancedLRUCache(Generic[K, V]):
    """增强 LRU 缓存

    支持 TTL、最大容量、指标统计。

    使用示例:
        cache = EnhancedLRUCache(max_size=1000, ttl_seconds=3600)
        cache.set("key", value)
        value = cache.get("key")
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: float | None = None,
        on_evict: Callable[[K, V], None] | None = None,
    ) -> None:
        """初始化缓存

        Args:
            max_size: 最大容量
            ttl_seconds: TTL（秒），None 表示永不过期
            on_evict: 淘汰回调
        """
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._on_evict = on_evict
        self._cache: OrderedDict[K, tuple[V, float]] = OrderedDict()
        self._lock = threading.RLock()
        self._metrics = CacheMetrics(max_size=max_size)

    def get(self, key: K) -> V | None:
        """获取缓存值

        Args:
            key: 键

        Returns:
            值或 None
        """
        with self._lock:
            if key not in self._cache:
                self._metrics.misses += 1
                return None

            value, timestamp = self._cache[key]

            # 检查 TTL
            if self._ttl is not None:
                if time.time() - timestamp > self._ttl:
                    self._evict(key)
                    self._metrics.misses += 1
                    return None

            # 移到末尾（最近使用）
            self._cache.move_to_end(key)
            self._metrics.hits += 1
            return value

    def set(self, key: K, value: V) -> None:
        """设置缓存值

        Args:
            key: 键
            value: 值
        """
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                # 检查容量
                while len(self._cache) >= self._max_size:
                    self._evict_oldest()

            self._cache[key] = (value, time.time())
            self._metrics.total_size = len(self._cache)

    def delete(self, key: K) -> bool:
        """删除缓存值

        Args:
            key: 键

        Returns:
            bool: 是否成功删除
        """
        with self._lock:
            if key in self._cache:
                self._evict(key)
                return True
            return False

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            if self._on_evict:
                for key, (value, _) in self._cache.items():
                    self._on_evict(key, value)
            self._cache.clear()
            self._metrics.total_size = 0

    def contains(self, key: K) -> bool:
        """检查键是否存在"""
        with self._lock:
            if key not in self._cache:
                return False
            if self._ttl is not None:
                value, timestamp = self._cache[key]
                if time.time() - timestamp > self._ttl:
                    return False
            return True

    def get_or_set(self, key: K, factory: Callable[[], V]) -> V:
        """获取或设置缓存值

        Args:
            key: 键
            factory: 值工厂函数

        Returns:
            值
        """
        value = self.get(key)
        if value is not None:
            return value

        value = factory()
        self.set(key, value)
        return value

    def _evict(self, key: K) -> None:
        """淘汰指定键"""
        if key in self._cache:
            value, _ = self._cache.pop(key)
            self._metrics.evictions += 1
            if self._on_evict:
                self._on_evict(key, value)

    def _evict_oldest(self) -> None:
        """淘汰最旧的键"""
        if self._cache:
            key, (value, _) = self._cache.popitem(last=False)
            self._metrics.evictions += 1
            if self._on_evict:
                self._on_evict(key, value)

    def get_metrics(self) -> CacheMetrics:
        """获取缓存指标"""
        with self._lock:
            return CacheMetrics(
                hits=self._metrics.hits,
                misses=self._metrics.misses,
                evictions=self._metrics.evictions,
                total_size=len(self._cache),
                max_size=self._max_size,
                created_at=self._metrics.created_at,
            )

    def __len__(self) -> int:
        return len(self._cache)

    def __contains__(self, key: K) -> bool:
        return self.contains(key)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    tags: set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    access_count: int = 0
    size: int = 0  # 字节数


class SmartCache:
    """智能缓存

    支持标签、TTL、大小追踪、持久化。

    使用示例:
        cache = SmartCache(max_size_mb=100)
        cache.set("api:CreateEntity", data, tags=["api", "entity"], ttl=3600)
        cache.invalidate_by_tag("entity")  # 使所有 entity 标签的缓存失效
    """

    def __init__(
        self,
        max_size_mb: float = 100,
        default_ttl: float | None = None,
        persist_path: str | None = None,
    ) -> None:
        """初始化智能缓存

        Args:
            max_size_mb: 最大大小（MB）
            default_ttl: 默认 TTL（秒）
            persist_path: 持久化路径
        """
        self._max_size_bytes = int(max_size_mb * 1024 * 1024)
        self._default_ttl = default_ttl
        self._persist_path = persist_path

        self._entries: dict[str, CacheEntry] = {}
        self._tag_index: dict[str, set[str]] = {}  # tag -> keys
        self._lock = threading.RLock()
        self._metrics = CacheMetrics()

        # 加载持久化数据
        if persist_path and Path(persist_path).exists():
            self._load_from_disk()

    def set(
        self,
        key: str,
        value: Any,
        tags: set[str] | None = None,
        ttl: float | None = None,
    ) -> None:
        """设置缓存

        Args:
            key: 键
            value: 值
            tags: 标签
            ttl: TTL（秒）
        """
        with self._lock:
            # 计算大小
            try:
                size = len(json.dumps(value))
            except (TypeError, ValueError):
                size = 0

            # 如果已存在，先删除
            if key in self._entries:
                self._delete_internal(key)

            # 检查大小限制
            while self._metrics.total_size + size > self._max_size_bytes:
                self._evict_lru()

            # 创建条目
            ttl = ttl if ttl is not None else self._default_ttl
            entry = CacheEntry(
                key=key,
                value=value,
                tags=tags or set(),
                expires_at=time.time() + ttl if ttl else None,
                size=size,
            )

            self._entries[key] = entry
            self._metrics.total_size += size

            # 更新标签索引
            for tag in entry.tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                self._tag_index[tag].add(key)

    def get(self, key: str) -> Any | None:
        """获取缓存

        Args:
            key: 键

        Returns:
            值或 None
        """
        with self._lock:
            if key not in self._entries:
                self._metrics.misses += 1
                return None

            entry = self._entries[key]

            # 检查过期
            if entry.expires_at and time.time() > entry.expires_at:
                self._delete_internal(key)
                self._metrics.misses += 1
                return None

            # 更新访问计数
            entry.access_count += 1
            self._metrics.hits += 1
            return entry.value

    def delete(self, key: str) -> bool:
        """删除缓存

        Args:
            key: 键

        Returns:
            bool: 是否成功
        """
        with self._lock:
            if key in self._entries:
                self._delete_internal(key)
                return True
            return False

    def invalidate_by_tag(self, tag: str) -> int:
        """使指定标签的所有缓存失效

        Args:
            tag: 标签

        Returns:
            int: 失效数量
        """
        with self._lock:
            if tag not in self._tag_index:
                return 0

            keys = list(self._tag_index[tag])
            for key in keys:
                self._delete_internal(key)

            return len(keys)

    def get_by_tag(self, tag: str) -> dict[str, Any]:
        """获取指定标签的所有缓存

        Args:
            tag: 标签

        Returns:
            dict: 键值对
        """
        with self._lock:
            if tag not in self._tag_index:
                return {}

            result = {}
            for key in self._tag_index[tag]:
                value = self.get(key)
                if value is not None:
                    result[key] = value
            return result

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._entries.clear()
            self._tag_index.clear()
            self._metrics = CacheMetrics()

    def persist(self) -> None:
        """持久化到磁盘"""
        if not self._persist_path:
            return

        with self._lock:
            data = {
                key: {
                    "value": entry.value,
                    "tags": list(entry.tags),
                    "expires_at": entry.expires_at,
                }
                for key, entry in self._entries.items()
            }

            path = Path(self._persist_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

    def get_metrics(self) -> dict[str, Any]:
        """获取指标"""
        with self._lock:
            return {
                "hits": self._metrics.hits,
                "misses": self._metrics.misses,
                "hit_rate": self._metrics.hit_rate,
                "total_size_bytes": self._metrics.total_size,
                "entry_count": len(self._entries),
                "tag_count": len(self._tag_index),
                "max_size_bytes": self._max_size_bytes,
            }

    def _delete_internal(self, key: str) -> None:
        """内部删除方法"""
        if key not in self._entries:
            return

        entry = self._entries.pop(key)
        self._metrics.total_size -= entry.size
        self._metrics.evictions += 1

        # 更新标签索引
        for tag in entry.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(key)
                if not self._tag_index[tag]:
                    del self._tag_index[tag]

    def _evict_lru(self) -> None:
        """淘汰最少使用的条目"""
        if not self._entries:
            return

        # 找到访问次数最少的
        lru_key = min(self._entries.keys(), key=lambda k: self._entries[k].access_count)
        self._delete_internal(lru_key)

    def _load_from_disk(self) -> None:
        """从磁盘加载"""
        if not self._persist_path:
            return

        try:
            with open(self._persist_path, encoding="utf-8") as f:
                data = json.load(f)

            for key, item in data.items():
                self.set(
                    key,
                    item["value"],
                    tags=set(item.get("tags", [])),
                    ttl=None,  # 不恢复 TTL
                )
        except (OSError, json.JSONDecodeError):
            pass


class ParallelProcessor:
    """并行处理器

    提供线程池和进程池并行处理。

    使用示例:
        processor = ParallelProcessor(max_workers=4)
        results = processor.map(process_item, items)
    """

    def __init__(self, max_workers: int | None = None) -> None:
        """初始化处理器

        Args:
            max_workers: 最大工作线程/进程数，None 自动检测
        """
        self._max_workers = max_workers or os.cpu_count() or 4
        self._thread_pool: ThreadPoolExecutor | None = None
        self._process_pool: ProcessPoolExecutor | None = None

    def map_threaded(
        self,
        func: Callable[[Any], Any],
        items: list[Any],
        timeout: float | None = None,
    ) -> list[Any]:
        """线程并行映射

        Args:
            func: 处理函数
            items: 输入列表
            timeout: 超时时间

        Returns:
            list: 结果列表
        """
        if not items:
            return []

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = [executor.submit(func, item) for item in items]
            results = []
            for future in as_completed(futures, timeout=timeout):
                try:
                    results.append(future.result())
                except Exception:
                    results.append(None)
            return results

    def map_process(
        self,
        func: Callable[[Any], Any],
        items: list[Any],
        timeout: float | None = None,
    ) -> list[Any]:
        """进程并行映射

        Args:
            func: 处理函数
            items: 输入列表
            timeout: 超时时间

        Returns:
            list: 结果列表
        """
        if not items:
            return []

        with ProcessPoolExecutor(max_workers=self._max_workers) as executor:
            futures = [executor.submit(func, item) for item in items]
            results = []
            for future in as_completed(futures, timeout=timeout):
                try:
                    results.append(future.result())
                except Exception:
                    results.append(None)
            return results

    async def map_async(
        self,
        func: Callable[[Any], Any],
        items: list[Any],
    ) -> list[Any]:
        """异步映射

        Args:
            func: 处理函数
            items: 输入列表

        Returns:
            list: 结果列表
        """
        if not items:
            return []

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            tasks = [loop.run_in_executor(executor, func, item) for item in items]
            return await asyncio.gather(*tasks, return_exceptions=True)


class LazyLoader:
    """懒加载器

    支持延迟导入和加载模块。

    使用示例:
        # 延迟导入
        np = LazyLoader.import_("numpy")

        # 延迟加载函数
        data = LazyLoader.load(lambda: expensive_operation())
    """

    @staticmethod
    def import_(module_name: str) -> Any:
        """延迟导入模块

        Args:
            module_name: 模块名

        Returns:
            模块对象
        """
        import importlib

        class LazyModule:
            def __init__(self, name: str) -> None:
                self._name = name
                self._module: Any = None

            def _load(self) -> Any:
                if self._module is None:
                    self._module = importlib.import_module(self._name)
                return self._module

            def __getattr__(self, name: str) -> Any:
                return getattr(self._load(), name)

        return LazyModule(module_name)

    @staticmethod
    def load(loader: Callable[[], Any]) -> Any:
        """延迟加载值

        Args:
            loader: 加载函数

        Returns:
            值
        """
        class LazyValue:
            def __init__(self, load_func: Callable[[], Any]) -> None:
                self._loader = load_func
                self._value: Any = None
                self._loaded = False

            def _load(self) -> Any:
                if not self._loaded:
                    self._value = self._loader()
                    self._loaded = True
                return self._value

            def __call__(self, *args: Any, **kwargs: Any) -> Any:
                value = self._load()
                if callable(value):
                    return value(*args, **kwargs)
                return value

            def __getattr__(self, name: str) -> Any:
                return getattr(self._load(), name)

        return LazyValue(loader)


class PerformanceMonitor:
    """性能监控器

    监控函数执行时间和内存使用。

    使用示例:
        monitor = PerformanceMonitor()

        @monitor.track("api_search")
        def search_api(query):
            ...

        # 获取统计
        stats = monitor.get_stats("api_search")
    """

    def __init__(self, max_samples: int = 1000) -> None:
        """初始化监控器

        Args:
            max_samples: 最大样本数
        """
        self._max_samples = max_samples
        self._samples: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def track(self, name: str) -> Callable[[Callable[..., V]], Callable[..., V]]:
        """装饰器：追踪执行时间

        Args:
            name: 追踪名称

        Returns:
            装饰器
        """
        def decorator(func: Callable[..., V]) -> Callable[..., V]:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> V:
                start = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    elapsed = time.perf_counter() - start
                    self._record(name, elapsed)
            return wrapper
        return decorator

    def _record(self, name: str, elapsed: float) -> None:
        """记录样本"""
        with self._lock:
            if name not in self._samples:
                self._samples[name] = []
            self._samples[name].append(elapsed)
            if len(self._samples[name]) > self._max_samples:
                self._samples[name].pop(0)

    def get_stats(self, name: str) -> dict[str, float]:
        """获取统计

        Args:
            name: 名称

        Returns:
            dict: 统计信息
        """
        with self._lock:
            if name not in self._samples or not self._samples[name]:
                return {}

            samples = self._samples[name]
            return {
                "count": len(samples),
                "min": min(samples),
                "max": max(samples),
                "mean": sum(samples) / len(samples),
                "recent": samples[-1] if samples else 0,
            }

    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """获取所有统计"""
        with self._lock:
            return {name: self.get_stats(name) for name in self._samples}


# 全局实例
_smart_cache: SmartCache | None = None
_parallel_processor: ParallelProcessor | None = None
_performance_monitor: PerformanceMonitor | None = None


def get_smart_cache() -> SmartCache:
    """获取全局智能缓存"""
    global _smart_cache
    if _smart_cache is None:
        _smart_cache = SmartCache()
    return _smart_cache


def get_parallel_processor() -> ParallelProcessor:
    """获取全局并行处理器"""
    global _parallel_processor
    if _parallel_processor is None:
        _parallel_processor = ParallelProcessor()
    return _parallel_processor


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor