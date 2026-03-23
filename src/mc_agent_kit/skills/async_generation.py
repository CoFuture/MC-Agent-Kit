"""
异步代码生成模块

提供异步代码生成、批量生成优化、增量缓存策略等功能。
"""

from __future__ import annotations

import asyncio
import hashlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union

from mc_agent_kit.skills.llm_integration import (
    ChatMessage,
    LLMConfig,
    LLMResponse,
    LLMService,
    MessageRole,
)
from mc_agent_kit.skills.smart_generation import (
    CodeStyle,
    GeneratedCode,
    GenerationRequest,
    GenerationStrategy,
    SmartCodeGenerator,
)


@dataclass
class AsyncGenerationResult:
    """异步生成结果"""
    request_id: str
    code: Optional[GeneratedCode] = None
    error: Optional[str] = None
    latency: float = 0.0
    cached: bool = False


@dataclass
class BatchGenerationConfig:
    """批量生成配置"""
    max_concurrent: int = 5
    timeout: float = 120.0
    retry_failed: bool = True
    max_retries: int = 2
    use_cache: bool = True


@dataclass
class BatchGenerationResult:
    """批量生成结果"""
    total_requests: int
    successful: int
    failed: int
    cached: int
    results: list[AsyncGenerationResult]
    total_latency: float
    average_latency: float


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    ttl: float
    hits: int = 0

    def is_expired(self) -> bool:
        """是否过期"""
        if self.ttl <= 0:
            return False
        return time.time() - self.created_at > self.ttl


class IncrementalCache:
    """增量缓存

    支持基于内容哈希的增量缓存，避免重复生成。
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl: float = 3600.0,
    ) -> None:
        self._cache: dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._ttl = ttl
        self._lock = threading.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }

    def _compute_key(
        self,
        prompt: str,
        strategy: GenerationStrategy,
        style: CodeStyle,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """计算缓存键"""
        content = f"{prompt}:{strategy.value}:{style.value}"
        if context:
            content += f":{str(sorted(context.items()))}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def get(
        self,
        prompt: str,
        strategy: GenerationStrategy,
        style: CodeStyle,
        context: Optional[dict[str, Any]] = None,
    ) -> Optional[GeneratedCode]:
        """获取缓存"""
        key = self._compute_key(prompt, strategy, style, context)

        with self._lock:
            entry = self._cache.get(key)
            if entry and not entry.is_expired():
                entry.hits += 1
                self._stats["hits"] += 1
                return entry.value

            self._stats["misses"] += 1
            return None

    def set(
        self,
        prompt: str,
        strategy: GenerationStrategy,
        style: CodeStyle,
        value: GeneratedCode,
        context: Optional[dict[str, Any]] = None,
        ttl: Optional[float] = None,
    ) -> None:
        """设置缓存"""
        key = self._compute_key(prompt, strategy, style, context)

        with self._lock:
            # 检查容量
            if len(self._cache) >= self._max_size:
                self._evict()

            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl=ttl or self._ttl,
            )

    def _evict(self) -> None:
        """淘汰条目 (LRU)"""
        if not self._cache:
            return

        # 找到最少使用的条目
        min_key = min(self._cache.keys(), key=lambda k: self._cache[k].hits)
        del self._cache[min_key]
        self._stats["evictions"] += 1

    def invalidate(
        self,
        prompt: Optional[str] = None,
        strategy: Optional[GenerationStrategy] = None,
    ) -> int:
        """失效缓存"""
        with self._lock:
            if prompt is None and strategy is None:
                count = len(self._cache)
                self._cache.clear()
                return count

            keys_to_remove: list[str] = []
            for key, entry in self._cache.items():
                if prompt and prompt in str(entry.value):
                    keys_to_remove.append(key)
                elif strategy and hasattr(entry.value, "strategy_used"):
                    if entry.value.strategy_used == strategy:
                        keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._cache[key]

            return len(keys_to_remove)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total if total > 0 else 0

            return {
                **self._stats,
                "size": len(self._cache),
                "hit_rate": hit_rate,
            }


class AsyncCodeGenerator:
    """异步代码生成器

    支持异步生成、批量生成、增量缓存等功能。
    """

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        cache: Optional[IncrementalCache] = None,
        default_style: CodeStyle = CodeStyle.MODSDK_BEST_PRACTICE,
    ) -> None:
        self._generator = SmartCodeGenerator(
            default_style=default_style,
            llm_config=llm_config or LLMConfig(
                provider=LLMProvider.MOCK,
                model="mock-model",
            ),
        )
        self._cache = cache or IncrementalCache()
        self._llm_service: Optional[LLMService] = None
        if llm_config:
            self._llm_service = LLMService(llm_config)
        self._executor = ThreadPoolExecutor(max_workers=5)

    def set_llm_service(self, llm_service: LLMService) -> None:
        """设置 LLM 服务"""
        self._llm_service = llm_service

    async def generate_async(
        self,
        request: GenerationRequest,
        use_cache: bool = True,
    ) -> AsyncGenerationResult:
        """异步生成代码"""
        request_id = hashlib.md5(
            f"{request.prompt}:{time.time()}".encode()
        ).hexdigest()[:16]
        start_time = time.time()

        style = request.style or CodeStyle.MODSDK_BEST_PRACTICE

        # 检查缓存
        if use_cache:
            cached = self._cache.get(
                request.prompt,
                request.strategy,
                style,
                request.context,
            )
            if cached:
                return AsyncGenerationResult(
                    request_id=request_id,
                    code=cached,
                    latency=time.time() - start_time,
                    cached=True,
                )

        try:
            # 异步执行生成
            loop = asyncio.get_event_loop()
            code = await loop.run_in_executor(
                self._executor,
                lambda: self._generator.generate(request),
            )

            # 缓存结果
            if use_cache:
                self._cache.set(
                    request.prompt,
                    request.strategy,
                    style,
                    code,
                    request.context,
                )

            return AsyncGenerationResult(
                request_id=request_id,
                code=code,
                latency=time.time() - start_time,
                cached=False,
            )

        except Exception as e:
            return AsyncGenerationResult(
                request_id=request_id,
                error=str(e),
                latency=time.time() - start_time,
            )

    async def generate_batch_async(
        self,
        requests: list[GenerationRequest],
        config: Optional[BatchGenerationConfig] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BatchGenerationResult:
        """异步批量生成"""
        config = config or BatchGenerationConfig()
        start_time = time.time()

        results: list[AsyncGenerationResult] = []
        semaphore = asyncio.Semaphore(config.max_concurrent)

        async def generate_with_semaphore(
            request: GenerationRequest,
            index: int,
        ) -> AsyncGenerationResult:
            async with semaphore:
                result = await self.generate_async(
                    request,
                    use_cache=config.use_cache,
                )

                if progress_callback:
                    completed = sum(1 for r in results if r is not None)
                    progress_callback(completed + 1, len(requests))

                return result

        # 创建所有任务
        tasks = [
            generate_with_semaphore(request, i)
            for i, request in enumerate(requests)
        ]

        # 执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        final_results: list[AsyncGenerationResult] = []
        successful = 0
        failed = 0
        cached = 0

        for result in results:
            if isinstance(result, Exception):
                final_results.append(AsyncGenerationResult(
                    request_id="error",
                    error=str(result),
                ))
                failed += 1
            elif isinstance(result, AsyncGenerationResult):
                final_results.append(result)
                if result.error:
                    failed += 1
                else:
                    successful += 1
                    if result.cached:
                        cached += 1

        total_latency = time.time() - start_time

        return BatchGenerationResult(
            total_requests=len(requests),
            successful=successful,
            failed=failed,
            cached=cached,
            results=final_results,
            total_latency=total_latency,
            average_latency=total_latency / len(requests) if requests else 0,
        )

    def generate_batch_sync(
        self,
        requests: list[GenerationRequest],
        config: Optional[BatchGenerationConfig] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BatchGenerationResult:
        """同步批量生成"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.generate_batch_async(requests, config, progress_callback),
        )

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        return self._cache.get_stats()

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.invalidate()

    def preload_templates(
        self,
        template_names: list[str],
    ) -> dict[str, GeneratedCode]:
        """预加载模板"""
        results: dict[str, GeneratedCode] = {}

        for name in template_names:
            # 使用模板名作为提示
            request = GenerationRequest(
                prompt=name,
                strategy=GenerationStrategy.TEMPLATE,
            )
            code = self._generator.generate(request)
            results[name] = code

            # 缓存结果
            self._cache.set(
                name,
                GenerationStrategy.TEMPLATE,
                CodeStyle.MODSDK_BEST_PRACTICE,
                code,
            )

        return results


class LazyLoader:
    """懒加载器

    延迟加载生成器实例，节省内存。
    """

    def __init__(
        self,
        factory: Callable[[], AsyncCodeGenerator],
    ) -> None:
        self._factory = factory
        self._instance: Optional[AsyncCodeGenerator] = None
        self._lock = threading.Lock()

    def get(self) -> AsyncCodeGenerator:
        """获取实例"""
        if self._instance is None:
            with self._lock:
                if self._instance is None:
                    self._instance = self._factory()
        return self._instance

    def reset(self) -> None:
        """重置实例"""
        with self._lock:
            self._instance = None


class MemoryOptimizedGenerator:
    """内存优化的生成器

    使用懒加载和内存池优化内存使用。
    """

    def __init__(
        self,
        max_cached_codes: int = 100,
        enable_lazy_loading: bool = True,
    ) -> None:
        self._max_cached_codes = max_cached_codes
        self._enable_lazy_loading = enable_lazy_loading
        self._code_pool: dict[str, GeneratedCode] = {}
        self._lock = threading.Lock()

        # 懒加载生成器
        self._generator_loader = LazyLoader(
            lambda: AsyncCodeGenerator()
        )

    def generate(
        self,
        request: GenerationRequest,
    ) -> GeneratedCode:
        """生成代码"""
        generator = self._generator_loader.get()
        result = asyncio.run(generator.generate_async(request))

        if result.code:
            self._maybe_cache(result.code)
            return result.code

        raise RuntimeError(result.error or "Generation failed")

    def _maybe_cache(self, code: GeneratedCode) -> None:
        """可能缓存代码"""
        with self._lock:
            if len(self._code_pool) >= self._max_cached_codes:
                # 简单的 FIFO 淘汰
                oldest_key = next(iter(self._code_pool))
                del self._code_pool[oldest_key]

            key = hashlib.md5(code.code.encode()).hexdigest()[:16]
            self._code_pool[key] = code

    def get_cached(self, key: str) -> Optional[GeneratedCode]:
        """获取缓存的代码"""
        return self._code_pool.get(key)

    def clear_pool(self) -> None:
        """清空内存池"""
        with self._lock:
            self._code_pool.clear()

    def get_memory_stats(self) -> dict[str, Any]:
        """获取内存统计"""
        with self._lock:
            total_chars = sum(len(c.code) for c in self._code_pool.values())
            return {
                "cached_count": len(self._code_pool),
                "total_chars": total_chars,
                "estimated_size_kb": total_chars / 1024,
            }


# 全局实例
_async_generator: Optional[AsyncCodeGenerator] = None
_memory_generator: Optional[MemoryOptimizedGenerator] = None


def get_async_generator(
    llm_config: Optional[LLMConfig] = None,
) -> AsyncCodeGenerator:
    """获取异步代码生成器实例"""
    global _async_generator
    if llm_config or _async_generator is None:
        _async_generator = AsyncCodeGenerator(llm_config)
    return _async_generator


def get_memory_optimized_generator() -> MemoryOptimizedGenerator:
    """获取内存优化的生成器实例"""
    global _memory_generator
    if _memory_generator is None:
        _memory_generator = MemoryOptimizedGenerator()
    return _memory_generator


async def generate_code_async(
    prompt: str,
    strategy: GenerationStrategy = GenerationStrategy.HYBRID,
    style: Optional[CodeStyle] = None,
    context: Optional[dict[str, Any]] = None,
) -> GeneratedCode:
    """便捷函数：异步生成代码"""
    request = GenerationRequest(
        prompt=prompt,
        strategy=strategy,
        style=style,
        context=context,
    )
    result = await get_async_generator().generate_async(request)
    if result.code:
        return result.code
    raise RuntimeError(result.error or "Generation failed")


async def generate_codes_batch_async(
    prompts: list[str],
    strategy: GenerationStrategy = GenerationStrategy.HYBRID,
    style: Optional[CodeStyle] = None,
) -> BatchGenerationResult:
    """便捷函数：异步批量生成代码"""
    requests = [
        GenerationRequest(prompt=prompt, strategy=strategy, style=style)
        for prompt in prompts
    ]
    return await get_async_generator().generate_batch_async(requests)