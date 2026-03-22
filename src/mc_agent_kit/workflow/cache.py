"""
工作流缓存模块

提供工作流中间结果缓存，优化执行速度
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    ttl_seconds: int = 3600  # 默认 1 小时
    hits: int = 0

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl_seconds <= 0:
            return False
        return time.time() - self.created_at > self.ttl_seconds

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
            "ttl_seconds": self.ttl_seconds,
            "hits": self.hits,
        }


class WorkflowCache:
    """
    工作流缓存管理器

    用于缓存工作流中间结果，提高重复执行效率
    """

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        max_entries: int = 100,
        default_ttl: int = 3600,
    ):
        """
        初始化缓存

        Args:
            cache_dir: 缓存目录（可选，用于持久化）
            max_entries: 最大条目数
            default_ttl: 默认 TTL（秒）
        """
        self._cache: dict[str, CacheEntry] = {}
        self._cache_dir = Path(cache_dir) if cache_dir else None
        self._max_entries = max_entries
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

        # 加载持久化缓存
        if self._cache_dir:
            self._load_from_disk()

    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        content = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _load_from_disk(self) -> None:
        """从磁盘加载缓存"""
        if not self._cache_dir:
            return

        cache_file = self._cache_dir / "workflow_cache.json"
        if not cache_file.exists():
            return

        try:
            with open(cache_file, encoding="utf-8") as f:
                data = json.load(f)

            for entry_data in data.get("entries", []):
                entry = CacheEntry(
                    key=entry_data["key"],
                    value=entry_data["value"],
                    created_at=entry_data["created_at"],
                    ttl_seconds=entry_data.get("ttl_seconds", self._default_ttl),
                    hits=entry_data.get("hits", 0),
                )
                if not entry.is_expired():
                    self._cache[entry.key] = entry
        except (json.JSONDecodeError, KeyError):
            pass

    def _save_to_disk(self) -> None:
        """保存缓存到磁盘"""
        if not self._cache_dir:
            return

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self._cache_dir / "workflow_cache.json"

        data = {
            "entries": [e.to_dict() for e in self._cache.values()],
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
        key = self._generate_key(*args, **kwargs)

        if key in self._cache:
            entry = self._cache[key]

            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None

            entry.hits += 1
            self._hits += 1
            return entry.value

        self._misses += 1
        return None

    def set(
        self,
        value: Any,
        *args,
        ttl_seconds: int | None = None,
        **kwargs,
    ) -> None:
        """
        设置缓存值

        Args:
            value: 缓存值
            *args: 位置参数（用于生成键）
            ttl_seconds: TTL（秒）
            **kwargs: 关键字参数（用于生成键）
        """
        key = self._generate_key(*args, **kwargs)

        # 检查容量
        if len(self._cache) >= self._max_entries and key not in self._cache:
            # 移除最少使用的条目
            self._evict_lru()

        entry = CacheEntry(
            key=key,
            value=value,
            ttl_seconds=ttl_seconds or self._default_ttl,
        )
        self._cache[key] = entry

        # 持久化
        if self._cache_dir:
            self._save_to_disk()

    def _evict_lru(self) -> None:
        """移除最少使用的条目"""
        if not self._cache:
            return

        # 找到 hits 最少的条目
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].hits)
        del self._cache[lru_key]

    def invalidate(self, *args, **kwargs) -> bool:
        """
        使缓存失效

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            是否成功移除
        """
        key = self._generate_key(*args, **kwargs)

        if key in self._cache:
            del self._cache[key]
            if self._cache_dir:
                self._save_to_disk()
            return True

        return False

    def clear(self) -> int:
        """
        清空缓存

        Returns:
            清除的条目数
        """
        count = len(self._cache)
        self._cache.clear()
        self._hits = 0
        self._misses = 0

        if self._cache_dir:
            cache_file = self._cache_dir / "workflow_cache.json"
            if cache_file.exists():
                cache_file.unlink()

        return count

    def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计

        Returns:
            统计信息
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

        return {
            "entries": len(self._cache),
            "max_entries": self._max_entries,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "persisted": self._cache_dir is not None,
        }

    def cleanup_expired(self) -> int:
        """
        清理过期条目

        Returns:
            清理的条目数
        """
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys and self._cache_dir:
            self._save_to_disk()

        return len(expired_keys)


# 全局缓存实例
_global_cache: WorkflowCache | None = None


def get_workflow_cache(
    cache_dir: str | Path | None = None,
    max_entries: int = 100,
    default_ttl: int = 3600,
) -> WorkflowCache:
    """
    获取全局工作流缓存实例

    Args:
        cache_dir: 缓存目录
        max_entries: 最大条目数
        default_ttl: 默认 TTL

    Returns:
        工作流缓存实例
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = WorkflowCache(
            cache_dir=cache_dir,
            max_entries=max_entries,
            default_ttl=default_ttl,
        )

    return _global_cache


def clear_workflow_cache() -> int:
    """
    清空全局工作流缓存

    Returns:
    清除的条目数
    """
    global _global_cache

    if _global_cache is None:
        return 0

    return _global_cache.clear()
