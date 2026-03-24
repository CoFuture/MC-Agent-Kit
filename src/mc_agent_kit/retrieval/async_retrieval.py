"""
异步检索模块

提供异步检索接口、并发搜索和结果流式返回。
"""

from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Optional

from ..retrieval.enhanced_retrieval import (
    EnhancedRetriever,
    EnhancedSearchResult,
    SearchReport,
)
from ..cache.multi_level_cache import get_multi_level_cache


@dataclass
class AsyncSearchConfig:
    """异步搜索配置"""
    max_concurrent_searches: int = 10
    timeout_seconds: float = 30.0
    cache_results: bool = True
    cache_ttl_seconds: int = 3600
    batch_size: int = 5


@dataclass
class SearchResultStream:
    """流式搜索结果"""
    query: str
    results: list[EnhancedSearchResult] = field(default_factory=list)
    is_complete: bool = False
    error: Optional[str] = None
    execution_time: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "results_count": len(self.results),
            "is_complete": self.is_complete,
            "error": self.error,
            "execution_time": self.execution_time,
        }


class AsyncRetriever:
    """
    异步检索器

    提供异步检索、并发搜索和流式结果。

    使用示例:
        retriever = AsyncRetriever()
        await retriever.start()

        # 异步搜索
        result = await retriever.search_async("创建实体")

        # 并发搜索
        results = await retriever.search_batch(["创建实体", "监听事件"])

        # 流式结果
        async for result in retriever.search_stream(queries):
            print(result)
    """

    def __init__(
        self,
        config: Optional[AsyncSearchConfig] = None,
    ) -> None:
        self._config = config or AsyncSearchConfig()
        self._retriever: Optional[EnhancedRetriever] = None
        self._cache = get_multi_level_cache()
        self._started = False
        self._search_semaphore: Optional[asyncio.Semaphore] = None
        self._lock = threading.RLock()

    async def start(self) -> None:
        """启动检索器"""
        with self._lock:
            if self._started:
                return

            self._retriever = EnhancedRetriever()
            self._search_semaphore = asyncio.Semaphore(self._config.max_concurrent_searches)
            self._started = True

    async def stop(self) -> None:
        """停止检索器"""
        with self._lock:
            self._started = False
            self._retriever = None

    async def search_async(
        self,
        query: str,
        top_k: int = 10,
    ) -> EnhancedSearchResult:
        """
        异步搜索

        Args:
            query: 查询字符串
            top_k: 返回结果数量

        Returns:
            搜索结果
        """
        if not self._started:
            await self.start()

        # 检查缓存
        if self._config.cache_results:
            cache_key = f"search:{query}:{top_k}"
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        async with self._search_semaphore:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._sync_search,
                query,
                top_k,
            )

        # 缓存结果
        if self._config.cache_results:
            self._cache.set(cache_key, result, self._config.cache_ttl_seconds)

        return result

    def _sync_search(self, query: str, top_k: int) -> EnhancedSearchResult:
        """同步搜索"""
        if self._retriever is None:
            raise RuntimeError("Retriever not initialized")
        return self._retriever.search(query, top_k)

    async def search_batch(
        self,
        queries: list[str],
        top_k: int = 10,
    ) -> list[EnhancedSearchResult]:
        """
        并发搜索

        Args:
            queries: 查询列表
            top_k: 每个查询返回的结果数量

        Returns:
            搜索结果列表
        """
        if not self._started:
            await self.start()

        tasks = [
            self.search_async(query, top_k)
            for query in queries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed: list[EnhancedSearchResult] = []
        for result in results:
            if isinstance(result, Exception):
                # 返回空结果
                processed.append(EnhancedSearchResult(
                    query="",
                    results=[],
                    total_time=0.0,
                ))
            else:
                processed.append(result)

        return processed

    async def search_stream(
        self,
        queries: list[str],
        top_k: int = 10,
    ) -> AsyncIterator[SearchResultStream]:
        """
        流式搜索结果

        Args:
            queries: 查询列表
            top_k: 结果数量

        Yields:
            流式结果
        """
        if not self._started:
            await self.start()

        for i in range(0, len(queries), self._config.batch_size):
            batch = queries[i:i + self._config.batch_size]

            batch_results = await self.search_batch(batch, top_k)

            for query, result in zip(batch, batch_results):
                stream_result = SearchResultStream(
                    query=query,
                    results=result.results,
                    is_complete=True,
                    execution_time=result.total_time,
                )
                yield stream_result

    async def search_with_timeout(
        self,
        query: str,
        top_k: int = 10,
        timeout: Optional[float] = None,
    ) -> Optional[EnhancedSearchResult]:
        """
        带超时的搜索

        Args:
            query: 查询
            top_k: 结果数量
            timeout: 超时时间

        Returns:
            搜索结果或 None（超时）
        """
        timeout_val = timeout or self._config.timeout_seconds

        try:
            return await asyncio.wait_for(
                self.search_async(query, top_k),
                timeout=timeout_val,
            )
        except asyncio.TimeoutError:
            return None

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        cache_stats = self._cache.get_stats()
        return {
            "started": self._started,
            "max_concurrent": self._config.max_concurrent_searches,
            "cache_hit_rate": cache_stats.get("overall_hit_rate", 0),
            "cache_stats": cache_stats,
        }


# 全局实例
_async_retriever: Optional[AsyncRetriever] = None


def get_async_retriever(config: Optional[AsyncSearchConfig] = None) -> AsyncRetriever:
    """获取全局异步检索器"""
    global _async_retriever
    if _async_retriever is None:
        _async_retriever = AsyncRetriever(config)
    return _async_retriever