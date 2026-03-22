"""
缓存增强模块

提供缓存预热、批量操作、命中率监控和优化持久化策略
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CacheMetrics:
    """缓存指标"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    updates: int = 0
    warmup_hits: int = 0
    batch_operations: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "updates": self.updates,
            "warmup_hits": self.warmup_hits,
            "batch_operations": self.batch_operations,
            "hit_rate": round(self.hit_rate, 4),
        }


@dataclass
class CacheEntryEnhanced:
    """增强缓存条目"""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    ttl_seconds: int = 3600
    hits: int = 0
    size_bytes: int = 0
    tags: set[str] = field(default_factory=set)
    is_warmup: bool = False  # 是否来自预热

    def is_expired(self) -> bool:
        if self.ttl_seconds <= 0:
            return False
        return time.time() - self.created_at > self.ttl_seconds

    def touch(self) -> None:
        """更新访问"""
        self.hits += 1
        self.updated_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "ttl_seconds": self.ttl_seconds,
            "hits": self.hits,
            "size_bytes": self.size_bytes,
            "tags": list(self.tags),
            "is_warmup": self.is_warmup,
        }


# 预热函数类型
WarmupFunction = Callable[[], dict[str, Any]]


@dataclass
class WarmupConfig:
    """预热配置"""
    enabled: bool = True
    warmup_functions: dict[str, WarmupFunction] = field(default_factory=dict)
    cache_ttl: int = 7200  # 预热数据缓存 2 小时
    background: bool = True  # 是否后台执行


class EnhancedCache:
    """
    增强缓存管理器

    提供：
    - 缓存预热
    - 批量操作
    - 命中率监控
    - 优化持久化
    """

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        max_entries: int = 100,
        max_size_bytes: int = 10 * 1024 * 1024,  # 10MB
        default_ttl: int = 3600,
        warmup_config: WarmupConfig | None = None,
    ):
        self._cache: dict[str, CacheEntryEnhanced] = {}
        self._cache_dir = Path(cache_dir) if cache_dir else None
        self._max_entries = max_entries
        self._max_size_bytes = max_size_bytes
        self._default_ttl = default_ttl
        self._metrics = CacheMetrics()
        self._warmup_config = warmup_config or WarmupConfig()
        self._tag_index: dict[str, set[str]] = defaultdict(set)  # tag -> keys
        self._lock = threading.RLock()

        # 加载持久化缓存
        if self._cache_dir:
            self._load_from_disk()

    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        content = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _estimate_size(self, value: Any) -> int:
        """估算值大小"""
        try:
            return len(json.dumps(value, default=str).encode())
        except Exception:
            return 0

    def _load_from_disk(self) -> None:
        """从磁盘加载缓存"""
        if not self._cache_dir:
            return

        cache_file = self._cache_dir / "enhanced_cache.json"
        if not cache_file.exists():
            return

        try:
            with open(cache_file, encoding="utf-8") as f:
                data = json.load(f)

            for entry_data in data.get("entries", []):
                entry = CacheEntryEnhanced(
                    key=entry_data["key"],
                    value=entry_data["value"],
                    created_at=entry_data["created_at"],
                    updated_at=entry_data.get("updated_at", entry_data["created_at"]),
                    ttl_seconds=entry_data.get("ttl_seconds", self._default_ttl),
                    hits=entry_data.get("hits", 0),
                    size_bytes=entry_data.get("size_bytes", 0),
                    tags=set(entry_data.get("tags", [])),
                    is_warmup=entry_data.get("is_warmup", False),
                )
                if not entry.is_expired():
                    self._cache[entry.key] = entry
                    # 更新标签索引
                    for tag in entry.tags:
                        self._tag_index[tag].add(entry.key)

            # 加载指标
            if "metrics" in data:
                self._metrics.hits = data["metrics"].get("hits", 0)
                self._metrics.misses = data["metrics"].get("misses", 0)
                self._metrics.evictions = data["metrics"].get("evictions", 0)

        except (json.JSONDecodeError, KeyError):
            pass

    def _save_to_disk(self) -> None:
        """保存缓存到磁盘（增量保存）"""
        if not self._cache_dir:
            return

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self._cache_dir / "enhanced_cache.json"

        data = {
            "entries": [e.to_dict() for e in self._cache.values()],
            "metrics": self._metrics.to_dict(),
            "saved_at": time.time(),
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get(self, *args, **kwargs) -> Any | None:
        """
        获取缓存值

        Args:
            *args: 位置参数（用于生成键）
            **kwargs: 关键字参数（用于生成键）

        Returns:
            缓存值或 None
        """
        with self._lock:
            key = self._generate_key(*args, **kwargs)

            if key in self._cache:
                entry = self._cache[key]

                if entry.is_expired():
                    del self._cache[key]
                    self._remove_from_tag_index(key, entry.tags)
                    self._metrics.misses += 1
                    return None

                entry.touch()
                self._metrics.hits += 1
                if entry.is_warmup:
                    self._metrics.warmup_hits += 1
                return entry.value

            self._metrics.misses += 1
            return None

    def _remove_from_tag_index(self, key: str, tags: set[str]) -> None:
        """从标签索引移除"""
        for tag in tags:
            self._tag_index[tag].discard(key)
            if not self._tag_index[tag]:
                del self._tag_index[tag]

    def set(
        self,
        value: Any,
        *args,
        ttl_seconds: int | None = None,
        tags: set[str] | None = None,
        is_warmup: bool = False,
        **kwargs,
    ) -> None:
        """
        设置缓存值

        Args:
            value: 缓存值
            *args: 位置参数（用于生成键）
            ttl_seconds: TTL（秒）
            tags: 标签集合
            is_warmup: 是否来自预热
            **kwargs: 关键字参数（用于生成键）
        """
        with self._lock:
            key = self._generate_key(*args, **kwargs)

            # 计算大小
            size_bytes = self._estimate_size(value)

            # 检查容量
            current_size = sum(e.size_bytes for e in self._cache.values())
            if (len(self._cache) >= self._max_entries or
                current_size + size_bytes > self._max_size_bytes):
                if key not in self._cache:
                    self._evict_lru()

            # 移除旧条目的标签索引
            if key in self._cache:
                old_entry = self._cache[key]
                self._remove_from_tag_index(key, old_entry.tags)

            entry = CacheEntryEnhanced(
                key=key,
                value=value,
                ttl_seconds=ttl_seconds or self._default_ttl,
                size_bytes=size_bytes,
                tags=tags or set(),
                is_warmup=is_warmup,
            )
            self._cache[key] = entry
            self._metrics.updates += 1

            # 更新标签索引
            for tag in entry.tags:
                self._tag_index[tag].add(key)

    def _evict_lru(self) -> None:
        """移除最少使用的条目"""
        if not self._cache:
            return

        # 找到 hits 最少且最旧的条目
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (self._cache[k].hits, self._cache[k].updated_at)
        )
        entry = self._cache[lru_key]
        del self._cache[lru_key]
        self._remove_from_tag_index(lru_key, entry.tags)
        self._metrics.evictions += 1

    # === 批量操作 ===

    def get_batch(self, keys: list[tuple]) -> dict[str, Any]:
        """
        批量获取缓存值

        Args:
            keys: 键列表，每个元素是 (args, kwargs) 元组

        Returns:
            键到值的映射
        """
        result = {}
        with self._lock:
            for args, kwargs in keys:
                key = self._generate_key(*args, **kwargs)
                value = self.get(*args, **kwargs)
                if value is not None:
                    result[key] = value

        self._metrics.batch_operations += 1
        return result

    def set_batch(
        self,
        items: list[tuple[Any, tuple, dict]],
        ttl_seconds: int | None = None,
        tags: set[str] | None = None,
        is_warmup: bool = False,
    ) -> int:
        """
        批量设置缓存值

        Args:
            items: 项列表，每个元素是 (value, args, kwargs) 元组
            ttl_seconds: TTL
            tags: 标签
            is_warmup: 是否来自预热

        Returns:
            成功设置的条目数
        """
        count = 0
        with self._lock:
            for value, args, kwargs in items:
                self.set(
                    value,
                    *args,
                    ttl_seconds=ttl_seconds,
                    tags=tags,
                    is_warmup=is_warmup,
                    **kwargs,
                )
                count += 1

        self._metrics.batch_operations += 1
        return count

    def invalidate_batch(self, keys: list[tuple]) -> int:
        """
        批量失效缓存

        Args:
            keys: 键列表

        Returns:
            成功移除的条目数
        """
        count = 0
        with self._lock:
            for args, kwargs in keys:
                key = self._generate_key(*args, **kwargs)
                if key in self._cache:
                    entry = self._cache[key]
                    del self._cache[key]
                    self._remove_from_tag_index(key, entry.tags)
                    count += 1

        return count

    def invalidate_by_tag(self, tag: str) -> int:
        """
        按标签失效缓存

        Args:
            tag: 标签

        Returns:
            成功移除的条目数
        """
        if tag not in self._tag_index:
            return 0

        count = 0
        with self._lock:
            keys_to_remove = list(self._tag_index[tag])
            for key in keys_to_remove:
                if key in self._cache:
                    entry = self._cache[key]
                    del self._cache[key]
                    self._remove_from_tag_index(key, entry.tags)
                    count += 1

        return count

    # === 预热功能 ===

    def warmup(self) -> int:
        """
        执行缓存预热

        Returns:
            预热的条目数
        """
        if not self._warmup_config.enabled:
            return 0

        count = 0
        for name, func in self._warmup_config.warmup_functions.items():
            try:
                data = func()
                if isinstance(data, dict):
                    for key, value in data.items():
                        self.set(
                            value,
                            key,
                            ttl_seconds=self._warmup_config.cache_ttl,
                            tags={"warmup", name},
                            is_warmup=True,
                        )
                        count += 1
            except Exception:
                pass

        if self._cache_dir:
            self._save_to_disk()

        return count

    def register_warmup_function(self, name: str, func: WarmupFunction) -> None:
        """
        注册预热函数

        Args:
            name: 预热函数名称
            func: 预热函数，返回要缓存的键值对
        """
        self._warmup_config.warmup_functions[name] = func

    # === 监控 ===

    def get_metrics(self) -> CacheMetrics:
        """获取缓存指标"""
        return self._metrics

    def get_stats(self) -> dict[str, Any]:
        """获取详细统计"""
        total_size = sum(e.size_bytes for e in self._cache.values())
        warmup_count = sum(1 for e in self._cache.values() if e.is_warmup)

        return {
            "entries": len(self._cache),
            "max_entries": self._max_entries,
            "total_size_bytes": total_size,
            "max_size_bytes": self._max_size_bytes,
            "size_usage": round(total_size / self._max_size_bytes * 100, 2) if self._max_size_bytes > 0 else 0,
            "warmup_entries": warmup_count,
            "tags": len(self._tag_index),
            **self._metrics.to_dict(),
        }

    def clear(self) -> int:
        """清空缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._tag_index.clear()
            self._metrics = CacheMetrics()

            if self._cache_dir:
                cache_file = self._cache_dir / "enhanced_cache.json"
                if cache_file.exists():
                    cache_file.unlink()

            return count

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        expired_keys = []
        with self._lock:
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                entry = self._cache[key]
                del self._cache[key]
                self._remove_from_tag_index(key, entry.tags)

            if expired_keys and self._cache_dir:
                self._save_to_disk()

        return len(expired_keys)

    def persist(self) -> None:
        """持久化缓存"""
        if self._cache_dir:
            self._save_to_disk()


# 全局增强缓存实例
_global_enhanced_cache: EnhancedCache | None = None


def get_enhanced_cache(
    cache_dir: str | Path | None = None,
    max_entries: int = 100,
    max_size_bytes: int = 10 * 1024 * 1024,
    default_ttl: int = 3600,
    warmup_config: WarmupConfig | None = None,
) -> EnhancedCache:
    """
    获取全局增强缓存实例

    Args:
        cache_dir: 缓存目录
        max_entries: 最大条目数
        max_size_bytes: 最大字节数
        default_ttl: 默认 TTL
        warmup_config: 预热配置

    Returns:
        增强缓存实例
    """
    global _global_enhanced_cache

    if _global_enhanced_cache is None:
        _global_enhanced_cache = EnhancedCache(
            cache_dir=cache_dir,
            max_entries=max_entries,
            max_size_bytes=max_size_bytes,
            default_ttl=default_ttl,
            warmup_config=warmup_config,
        )

    return _global_enhanced_cache


def clear_enhanced_cache() -> int:
    """清空全局增强缓存"""
    global _global_enhanced_cache

    if _global_enhanced_cache is None:
        return 0

    return _global_enhanced_cache.clear()
