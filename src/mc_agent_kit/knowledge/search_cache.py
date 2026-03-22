"""
搜索结果缓存模块

实现搜索结果 LRU 缓存，支持：
- LRU 缓存淘汰策略
- TTL 过期机制
- 缓存命中率统计
- 缓存预热功能
"""

import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class SearchCacheEntry:
    """搜索缓存条目"""
    query: str
    results: list[Any]
    search_type: str = "all"
    limit: int = 10
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    hit_count: int = 0
    compute_time_ms: float = 0.0


@dataclass
class SearchCacheStats:
    """搜索缓存统计"""
    total_entries: int = 0
    total_hits: int = 0
    total_misses: int = 0
    total_compute_time_ms: float = 0.0
    hit_rate: float = 0.0
    avg_compute_time_ms: float = 0.0
    size_bytes: int = 0


class SearchResultCache:
    """
    搜索结果缓存

    缓存知识库搜索结果，加速重复查询。

    使用示例:
        cache = SearchResultCache(max_size=500, ttl_seconds=3600)
        
        # 预热缓存
        cache.warmup(queries=["创建实体", "获取玩家"], search_fn=my_search)
        
        # 搜索（自动缓存）
        results = cache.get_or_compute(
            query="如何创建实体",
            compute_fn=lambda: kb.search("如何创建实体")
        )
        
        # 查看统计
        print(cache.get_stats())
    """

    def __init__(
        self,
        max_size: int = 500,
        ttl_seconds: int = 3600,
        persist_path: str | None = None,
    ):
        """
        初始化搜索结果缓存。

        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 缓存有效期（秒）
            persist_path: 持久化文件路径
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.persist_path = Path(persist_path) if persist_path else None
        self._cache: OrderedDict[str, SearchCacheEntry] = OrderedDict()
        self._stats = SearchCacheStats()

    def get(
        self,
        query: str,
        search_type: str = "all",
        limit: int = 10,
    ) -> list[Any] | None:
        """
        获取缓存的搜索结果。

        Args:
            query: 查询字符串
            search_type: 搜索类型
            limit: 结果数量限制

        Returns:
            缓存的结果，不存在或过期返回 None
        """
        key = self._make_key(query, search_type, limit)

        if key not in self._cache:
            self._stats.total_misses += 1
            return None

        entry = self._cache[key]

        # 检查是否过期
        if self._is_expired(entry):
            self._remove(key)
            self._stats.total_misses += 1
            return None

        # 更新访问信息
        entry.accessed_at = time.time()
        entry.hit_count += 1
        self._stats.total_hits += 1

        # 移动到末尾（最近使用）
        self._cache.move_to_end(key)

        return entry.results

    def set(
        self,
        query: str,
        results: list[Any],
        search_type: str = "all",
        limit: int = 10,
        compute_time_ms: float = 0.0,
    ) -> None:
        """
        设置缓存。

        Args:
            query: 查询字符串
            results: 搜索结果
            search_type: 搜索类型
            limit: 结果数量限制
            compute_time_ms: 计算耗时
        """
        key = self._make_key(query, search_type, limit)

        # 如果已存在，更新
        if key in self._cache:
            entry = self._cache[key]
            entry.results = results
            entry.compute_time_ms = compute_time_ms
            entry.accessed_at = time.time()
            self._cache.move_to_end(key)
        else:
            # 检查是否需要淘汰
            if len(self._cache) >= self.max_size:
                self._evict()

            # 添加新条目
            entry = SearchCacheEntry(
                query=query,
                results=results,
                search_type=search_type,
                limit=limit,
                compute_time_ms=compute_time_ms,
            )
            self._cache[key] = entry
            self._stats.total_entries += 1

        self._stats.total_compute_time_ms += compute_time_ms

    def get_or_compute(
        self,
        query: str,
        compute_fn: Callable[[], list[Any]],
        search_type: str = "all",
        limit: int = 10,
    ) -> list[Any]:
        """
        获取或计算搜索结果。

        Args:
            query: 查询字符串
            compute_fn: 计算函数
            search_type: 搜索类型
            limit: 结果数量限制

        Returns:
            搜索结果
        """
        # 尝试获取缓存
        results = self.get(query, search_type, limit)
        if results is not None:
            return results

        # 缓存未命中，计算
        self._stats.total_misses += 1
        start_time = time.time()
        results = compute_fn()
        compute_time_ms = (time.time() - start_time) * 1000

        # 存入缓存
        self.set(query, results, search_type, limit, compute_time_ms)

        return results

    def warmup(
        self,
        queries: list[str],
        search_fn: Callable[[str, str, int], list[Any]],
        search_type: str = "all",
        limit: int = 10,
    ) -> dict[str, bool]:
        """
        缓存预热。

        Args:
            queries: 预热查询列表
            search_fn: 搜索函数
            search_type: 搜索类型
            limit: 结果数量限制

        Returns:
            每个查询的预热结果
        """
        results = {}

        for query in queries:
            try:
                search_results = search_fn(query, search_type, limit)
                self.set(query, search_results, search_type, limit)
                results[query] = True
            except Exception:
                results[query] = False

        return results

    def invalidate(
        self,
        query: str,
        search_type: str = "all",
        limit: int = 10,
    ) -> bool:
        """
        使指定缓存失效。

        Args:
            query: 查询字符串
            search_type: 搜索类型
            limit: 结果数量限制

        Returns:
            是否成功删除
        """
        key = self._make_key(query, search_type, limit)
        return self._remove(key)

    def invalidate_all(self) -> int:
        """
        使所有缓存失效。

        Returns:
            清除的条目数
        """
        count = len(self._cache)
        self._cache.clear()
        self._stats.total_entries = 0
        return count

    def prune_expired(self) -> int:
        """
        清理过期条目。

        Returns:
            清理的条目数
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if self._is_expired(entry)
        ]

        for key in expired_keys:
            self._remove(key)

        return len(expired_keys)

    def get_stats(self) -> SearchCacheStats:
        """
        获取缓存统计。

        Returns:
            统计信息
        """
        total = self._stats.total_hits + self._stats.total_misses
        if total > 0:
            self._stats.hit_rate = self._stats.total_hits / total

        if self._stats.total_hits > 0:
            self._stats.avg_compute_time_ms = (
                self._stats.total_compute_time_ms / self._stats.total_hits
            )

        self._stats.total_entries = len(self._cache)
        self._stats.size_bytes = self._estimate_size()

        return self._stats

    def get_hot_queries(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        获取热门查询。

        Args:
            limit: 返回数量

        Returns:
            热门查询列表
        """
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].hit_count,
            reverse=True,
        )

        return [
            {
                "query": entry.query,
                "hit_count": entry.hit_count,
                "search_type": entry.search_type,
            }
            for _, entry in sorted_entries[:limit]
        ]

    def persist(self) -> bool:
        """
        持久化缓存到磁盘。

        Returns:
            是否成功
        """
        if not self.persist_path:
            return False

        try:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "entries": [
                    {
                        "query": entry.query,
                        "results": entry.results,
                        "search_type": entry.search_type,
                        "limit": entry.limit,
                        "created_at": entry.created_at,
                        "compute_time_ms": entry.compute_time_ms,
                    }
                    for entry in self._cache.values()
                    if not self._is_expired(entry)
                ],
                "stats": {
                    "total_hits": self._stats.total_hits,
                    "total_misses": self._stats.total_misses,
                },
            }

            with open(self.persist_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, default=str)

            return True
        except Exception:
            return False

    def load(self) -> int:
        """
        从磁盘加载缓存。

        Returns:
            加载的条目数
        """
        if not self.persist_path or not self.persist_path.exists():
            return 0

        try:
            with open(self.persist_path, encoding="utf-8") as f:
                data = json.load(f)

            count = 0
            for item in data.get("entries", []):
                # 检查是否过期
                if self.ttl_seconds:
                    age = time.time() - item.get("created_at", time.time())
                    if age > self.ttl_seconds:
                        continue

                self.set(
                    query=item["query"],
                    results=item["results"],
                    search_type=item.get("search_type", "all"),
                    limit=item.get("limit", 10),
                    compute_time_ms=item.get("compute_time_ms", 0.0),
                )
                count += 1

            # 恢复统计
            stats = data.get("stats", {})
            self._stats.total_hits = stats.get("total_hits", 0)
            self._stats.total_misses = stats.get("total_misses", 0)

            return count
        except Exception:
            return 0

    def _make_key(self, query: str, search_type: str, limit: int) -> str:
        """生成缓存键"""
        key_str = f"{search_type}:{limit}:{query}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _is_expired(self, entry: SearchCacheEntry) -> bool:
        """检查条目是否过期"""
        if self.ttl_seconds is None:
            return False
        return (time.time() - entry.created_at) > self.ttl_seconds

    def _remove(self, key: str) -> bool:
        """删除条目"""
        if key in self._cache:
            del self._cache[key]
            self._stats.total_entries -= 1
            return True
        return False

    def _evict(self) -> None:
        """淘汰最久未使用的条目"""
        if self._cache:
            self._cache.popitem(last=False)

    def _estimate_size(self) -> int:
        """估算缓存大小"""
        try:
            return len(json.dumps([
                entry.results for entry in self._cache.values()
            ], default=str))
        except Exception:
            return 0


def create_search_cache(
    max_size: int = 500,
    ttl_seconds: int = 3600,
    persist_path: str | None = None,
) -> SearchResultCache:
    """
    创建搜索缓存实例的便捷函数。

    Args:
        max_size: 最大缓存条目数
        ttl_seconds: 缓存有效期
        persist_path: 持久化文件路径

    Returns:
        SearchResultCache 实例
    """
    return SearchResultCache(
        max_size=max_size,
        ttl_seconds=ttl_seconds,
        persist_path=persist_path,
    )