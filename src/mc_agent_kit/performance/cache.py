"""
知识库缓存优化

提供 LRU 缓存和知识检索缓存功能。
"""

import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    hit_count: int = 0


class LRUCache:
    """
    LRU（最近最少使用）缓存

    使用示例:
        cache = LRUCache(max_size=100)
        cache.set("key", "value")
        value = cache.get("key")
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int | None = None):
        """
        初始化 LRU 缓存

        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 条目存活时间（秒），None 表示永不过期
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = None  # 线程安全时可添加

    def get(self, key: str) -> Any | None:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在或过期返回 None
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]

        # 检查是否过期
        if self._is_expired(entry):
            self._remove(key)
            return None

        # 更新访问时间和命中次数
        entry.accessed_at = time.time()
        entry.hit_count += 1

        # 移动到末尾（最近使用）
        self._cache.move_to_end(key)

        return entry.value

    def set(self, key: str, value: Any) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        # 如果已存在，更新
        if key in self._cache:
            entry = self._cache[key]
            entry.value = value
            entry.accessed_at = time.time()
            self._cache.move_to_end(key)
        else:
            # 检查是否需要淘汰
            if len(self._cache) >= self.max_size:
                self._evict()

            # 添加新条目
            entry = CacheEntry(key=key, value=value)
            self._cache[key] = entry

    def delete(self, key: str) -> bool:
        """
        删除缓存条目

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        return self._remove(key)

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()

    def stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        total_hits = sum(e.hit_count for e in self._cache.values())

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "total_hits": total_hits,
            "avg_hits": total_hits / len(self._cache) if self._cache else 0,
            "ttl_seconds": self.ttl_seconds,
        }

    def _is_expired(self, entry: CacheEntry) -> bool:
        """检查条目是否过期"""
        if self.ttl_seconds is None:
            return False
        return (time.time() - entry.created_at) > self.ttl_seconds

    def _remove(self, key: str) -> bool:
        """删除条目"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def _evict(self) -> None:
        """淘汰最久未使用的条目"""
        if self._cache:
            # 删除第一个（最久未使用）
            self._cache.popitem(last=False)


class KnowledgeCache:
    """
    知识库检索缓存

    缓存搜索结果，加速重复查询。

    使用示例:
        cache = KnowledgeCache(max_size=500)
        results = cache.get_or_set(
            query="如何创建实体",
            compute_fn=lambda: kb.search("如何创建实体")
        )
    """

    def __init__(
        self,
        max_size: int = 500,
        ttl_seconds: int = 3600,
        persist_dir: str | None = None,
    ):
        """
        初始化知识库缓存

        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 缓存存活时间（秒）
            persist_dir: 持久化目录
        """
        self._lru = LRUCache(max_size=max_size, ttl_seconds=ttl_seconds)
        self.persist_dir = Path(persist_dir) if persist_dir else None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "computes": 0,
        }

    def get_or_set(self, query: str, compute_fn: callable) -> Any:
        """
        获取或计算缓存值

        Args:
            query: 查询字符串
            compute_fn: 计算函数（缓存未命中时调用）

        Returns:
            缓存值或计算结果
        """
        key = self._generate_key(query)

        # 尝试从缓存获取
        result = self._lru.get(key)
        if result is not None:
            self._stats["hits"] += 1
            return result

        # 缓存未命中，计算并缓存
        self._stats["misses"] += 1
        self._stats["computes"] += 1

        result = compute_fn()
        self._lru.set(key, result)

        return result

    def invalidate(self, query: str) -> bool:
        """
        使缓存失效

        Args:
            query: 查询字符串

        Returns:
            是否成功删除
        """
        key = self._generate_key(query)
        return self._lru.delete(key)

    def clear(self) -> None:
        """清空缓存"""
        self._lru.clear()
        self._stats = {"hits": 0, "misses": 0, "computes": 0}

    def stats(self) -> dict[str, Any]:
        """
        获取缓存统计

        Returns:
            统计信息
        """
        hit_rate = (
            self._stats["hits"] / (self._stats["hits"] + self._stats["misses"])
            if (self._stats["hits"] + self._stats["misses"]) > 0
            else 0
        )

        return {
            **self._stats,
            "hit_rate": hit_rate,
            "cache_size": self._lru.stats()["size"],
        }

    def persist(self) -> None:
        """持久化缓存到磁盘"""
        if not self.persist_dir:
            return

        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # 保存缓存数据
        cache_data = []
        for entry in self._lru._cache.values():
            if not self._lru._is_expired(entry):
                cache_data.append({
                    "key": entry.key,
                    "value": entry.value,
                    "created_at": entry.created_at,
                })

        cache_path = self.persist_dir / "knowledge_cache.json"
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False)

    def load(self) -> int:
        """
        从磁盘加载缓存

        Returns:
            加载的条目数
        """
        if not self.persist_dir:
            return 0

        cache_path = self.persist_dir / "knowledge_cache.json"
        if not cache_path.exists():
            return 0

        try:
            with open(cache_path, encoding="utf-8") as f:
                cache_data = json.load(f)

            count = 0
            for item in cache_data:
                # 检查是否过期
                if self._lru.ttl_seconds:
                    age = time.time() - item["created_at"]
                    if age > self._lru.ttl_seconds:
                        continue

                self._lru.set(item["key"], item["value"])
                count += 1

            return count
        except Exception:
            return 0

    def _generate_key(self, query: str) -> str:
        """生成缓存键"""
        return hashlib.md5(query.encode()).hexdigest()
