"""
多级缓存模块

提供 L1（内存）和 L2（磁盘）两级缓存，支持缓存预热、监控和失效策略。
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class CacheStats:
    """缓存统计"""
    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    evictions: int = 0
    warmup_hits: int = 0
    total_requests: int = 0

    @property
    def l1_hit_rate(self) -> float:
        total = self.l1_hits + self.l1_misses
        return self.l1_hits / total if total > 0 else 0.0

    @property
    def l2_hit_rate(self) -> float:
        total = self.l2_hits + self.l2_misses
        return self.l2_hits / total if total > 0 else 0.0

    @property
    def overall_hit_rate(self) -> float:
        total_hits = self.l1_hits + self.l2_hits
        return total_hits / self.total_requests if self.total_requests > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "l1_hits": self.l1_hits,
            "l1_misses": self.l1_misses,
            "l1_hit_rate": round(self.l1_hit_rate, 4),
            "l2_hits": self.l2_hits,
            "l2_misses": self.l2_misses,
            "l2_hit_rate": round(self.l2_hit_rate, 4),
            "overall_hit_rate": round(self.overall_hit_rate, 4),
            "evictions": self.evictions,
            "warmup_hits": self.warmup_hits,
            "total_requests": self.total_requests,
        }


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    ttl_seconds: int
    hits: int = 0
    size_bytes: int = 0
    tags: list[str] = field(default_factory=list)
    is_warmup: bool = False

    def is_expired(self) -> bool:
        if self.ttl_seconds <= 0:
            return False
        return time.time() - self.created_at > self.ttl_seconds

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "created_at": self.created_at,
            "ttl_seconds": self.ttl_seconds,
            "hits": self.hits,
            "size_bytes": self.size_bytes,
            "tags": self.tags,
            "is_warmup": self.is_warmup,
        }


@dataclass
class CacheConfig:
    """缓存配置"""
    # L1 配置
    l1_max_entries: int = 1000
    l1_max_size_mb: float = 100.0

    # L2 配置
    l2_enabled: bool = True
    l2_max_size_mb: float = 1000.0
    l2_cache_dir: Optional[str] = None

    # TTL 配置
    default_ttl_seconds: int = 3600

    # 预热配置
    warmup_enabled: bool = True
    warmup_on_startup: bool = True


class L1Cache:
    """L1 内存缓存"""

    def __init__(
        self,
        max_entries: int = 1000,
        max_size_bytes: int = 100 * 1024 * 1024,
    ) -> None:
        self._max_entries = max_entries
        self._max_size_bytes = max_size_bytes
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._current_size = 0
        self._lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if entry.is_expired():
                self._remove_entry(key)
                return None

            # 移动到末尾（最近使用）
            self._cache.move_to_end(key)
            entry.hits += 1
            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
        tags: Optional[list[str]] = None,
        is_warmup: bool = False,
    ) -> None:
        with self._lock:
            # 计算大小
            size_bytes = self._estimate_size(value)

            # 检查容量
            while (
                len(self._cache) >= self._max_entries or
                self._current_size + size_bytes > self._max_size_bytes
            ):
                if not self._evict_lru():
                    break

            # 移除旧条目
            if key in self._cache:
                self._remove_entry(key)

            # 添加新条目
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl_seconds=ttl_seconds,
                size_bytes=size_bytes,
                tags=tags or [],
                is_warmup=is_warmup,
            )
            self._cache[key] = entry
            self._current_size += size_bytes

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._current_size = 0

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "entries": len(self._cache),
                "max_entries": self._max_entries,
                "size_bytes": self._current_size,
                "max_size_bytes": self._max_size_bytes,
                "usage_percent": round(self._current_size / self._max_size_bytes * 100, 2),
            }

    def _remove_entry(self, key: str) -> None:
        if key in self._cache:
            entry = self._cache[key]
            self._current_size -= entry.size_bytes
            del self._cache[key]

    def _evict_lru(self) -> bool:
        if not self._cache:
            return False

        # 移除最久未使用的条目
        key, entry = self._cache.popitem(last=False)
        self._current_size -= entry.size_bytes
        return True

    def _estimate_size(self, value: Any) -> int:
        try:
            return len(json.dumps(value, default=str).encode())
        except Exception:
            return 0


class L2Cache:
    """L2 磁盘缓存"""

    def __init__(
        self,
        cache_dir: str | Path,
        max_size_bytes: int = 1000 * 1024 * 1024,
    ) -> None:
        self._cache_dir = Path(cache_dir)
        self._max_size_bytes = max_size_bytes
        self._lock = threading.RLock()
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> Any | None:
        file_path = self._get_file_path(key)

        with self._lock:
            if not file_path.exists():
                return None

            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)

                # 检查过期
                created_at = data.get("created_at", 0)
                ttl = data.get("ttl_seconds", 0)
                if ttl > 0 and time.time() - created_at > ttl:
                    file_path.unlink()
                    return None

                return data.get("value")

            except (json.JSONDecodeError, KeyError):
                return None

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
        tags: Optional[list[str]] = None,
    ) -> None:
        file_path = self._get_file_path(key)

        with self._lock:
            data = {
                "key": key,
                "value": value,
                "created_at": time.time(),
                "ttl_seconds": ttl_seconds,
                "tags": tags or [],
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

            # 检查容量
            self._check_capacity()

    def delete(self, key: str) -> bool:
        file_path = self._get_file_path(key)

        with self._lock:
            if file_path.exists():
                file_path.unlink()
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            for file in self._cache_dir.glob("*.cache"):
                file.unlink()

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            total_size = sum(
                f.stat().st_size
                for f in self._cache_dir.glob("*.cache")
            )
            entry_count = len(list(self._cache_dir.glob("*.cache")))

            return {
                "entries": entry_count,
                "size_bytes": total_size,
                "max_size_bytes": self._max_size_bytes,
                "usage_percent": round(total_size / self._max_size_bytes * 100, 2),
            }

    def _get_file_path(self, key: str) -> Path:
        # 使用哈希避免文件名过长
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:32]
        return self._cache_dir / f"{key_hash}.cache"

    def _check_capacity(self) -> None:
        # 获取所有缓存文件
        files = list(self._cache_dir.glob("*.cache"))
        total_size = sum(f.stat().st_size for f in files)

        # 如果超出容量，删除最旧的文件
        while total_size > self._max_size_bytes and files:
            # 按修改时间排序
            files.sort(key=lambda f: f.stat().st_mtime)
            oldest = files.pop(0)
            total_size -= oldest.stat().st_size
            oldest.unlink()


class MultiLevelCache:
    """
    多级缓存

    整合 L1 内存缓存和 L2 磁盘缓存。

    使用示例:
        cache = MultiLevelCache(config)
        cache.warmup()
        value = cache.get("key")
        cache.set("key", value, ttl=3600)
    """

    def __init__(self, config: Optional[CacheConfig] = None) -> None:
        self._config = config or CacheConfig()

        # 初始化 L1
        self._l1 = L1Cache(
            max_entries=self._config.l1_max_entries,
            max_size_bytes=int(self._config.l1_max_size_mb * 1024 * 1024),
        )

        # 初始化 L2
        self._l2: Optional[L2Cache] = None
        if self._config.l2_enabled and self._config.l2_cache_dir:
            self._l2 = L2Cache(
                cache_dir=self._config.l2_cache_dir,
                max_size_bytes=int(self._config.l2_max_size_mb * 1024 * 1024),
            )

        self._stats = CacheStats()
        self._warmup_functions: dict[str, Callable[[], dict[str, Any]]] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        with self._lock:
            self._stats.total_requests += 1

            # L1 查找
            value = self._l1.get(key)
            if value is not None:
                self._stats.l1_hits += 1
                return value

            self._stats.l1_misses += 1

            # L2 查找
            if self._l2:
                value = self._l2.get(key)
                if value is not None:
                    self._stats.l2_hits += 1
                    # 提升到 L1
                    self._l1.set(key, value)
                    return value

                self._stats.l2_misses += 1

            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        tags: Optional[list[str]] = None,
        is_warmup: bool = False,
    ) -> None:
        """设置缓存值"""
        ttl = ttl_seconds or self._config.default_ttl_seconds

        with self._lock:
            # 写入 L1
            self._l1.set(key, value, ttl, tags, is_warmup)

            # 写入 L2
            if self._l2:
                self._l2.set(key, value, ttl, tags)

    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self._lock:
            l1_deleted = self._l1.delete(key)
            l2_deleted = self._l2.delete(key) if self._l2 else False
            return l1_deleted or l2_deleted

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._l1.clear()
            if self._l2:
                self._l2.clear()
            self._stats = CacheStats()

    def register_warmup(
        self,
        name: str,
        func: Callable[[], dict[str, Any]],
    ) -> None:
        """注册预热函数"""
        self._warmup_functions[name] = func

    def warmup(self) -> dict[str, int]:
        """执行预热"""
        results: dict[str, int] = {}

        if not self._config.warmup_enabled:
            return results

        for name, func in self._warmup_functions.items():
            try:
                data = func()
                count = 0
                for key, value in data.items():
                    self.set(key, value, is_warmup=True)
                    count += 1
                results[name] = count
            except Exception:
                results[name] = 0

        return results

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            stats = self._stats.to_dict()
            stats["l1"] = self._l1.get_stats()
            if self._l2:
                stats["l2"] = self._l2.get_stats()
            return stats

    def get_hit_rate(self) -> float:
        """获取命中率"""
        return self._stats.overall_hit_rate

    def invalidate_by_tag(self, tag: str) -> int:
        """按标签失效"""
        # 简化实现：需要在实际使用中维护标签索引
        return 0

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        # L1 和 L2 会自动检查过期
        return 0


# 全局实例
_multi_cache: Optional[MultiLevelCache] = None


def get_multi_level_cache(config: Optional[CacheConfig] = None) -> MultiLevelCache:
    """获取全局多级缓存"""
    global _multi_cache
    if _multi_cache is None:
        _multi_cache = MultiLevelCache(config)
    return _multi_cache