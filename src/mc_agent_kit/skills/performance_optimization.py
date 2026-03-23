"""
性能优化模块

提供 LLM 响应缓存、提示模板预编译、批量调用优化、内存监控等功能。
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class CacheStrategy(Enum):
    """缓存策略"""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    FIFO = "fifo"


class OptimizationType(Enum):
    """优化类型"""
    CACHE = "cache"
    PRECOMPILE = "precompile"
    BATCH = "batch"
    MEMORY = "memory"
    LATENCY = "latency"


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    ttl: Optional[float] = None
    size_bytes: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self) -> None:
        """更新访问时间"""
        self.last_accessed = time.time()
        self.access_count += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "ttl": self.ttl,
            "size_bytes": self.size_bytes,
            "is_expired": self.is_expired(),
        }


@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0

    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "total_size_bytes": self.total_size_bytes,
            "entry_count": self.entry_count,
            "hit_rate": self.hit_rate,
        }


@dataclass
class BatchResult:
    """批量结果"""
    results: list[Any]
    total_time: float
    average_time: float
    success_count: int
    error_count: int
    errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "results_count": len(self.results),
            "total_time": self.total_time,
            "average_time": self.average_time,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "errors": self.errors,
        }


@dataclass
class MemoryStats:
    """内存统计"""
    total_memory_mb: float = 0.0
    used_memory_mb: float = 0.0
    available_memory_mb: float = 0.0
    cache_memory_mb: float = 0.0
    object_count: int = 0

    @property
    def usage_percent(self) -> float:
        """使用率百分比"""
        if self.total_memory_mb == 0:
            return 0.0
        return (self.used_memory_mb / self.total_memory_mb) * 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_memory_mb": self.total_memory_mb,
            "used_memory_mb": self.used_memory_mb,
            "available_memory_mb": self.available_memory_mb,
            "cache_memory_mb": self.cache_memory_mb,
            "object_count": self.object_count,
            "usage_percent": self.usage_percent,
        }


@dataclass
class OptimizationReport:
    """优化报告"""
    optimization_type: OptimizationType
    before_metrics: dict[str, Any]
    after_metrics: dict[str, Any]
    improvement_percent: float
    recommendations: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "optimization_type": self.optimization_type.value,
            "before_metrics": self.before_metrics,
            "after_metrics": self.after_metrics,
            "improvement_percent": self.improvement_percent,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
        }


class LLMAcceleratorCache:
    """LLM 响应缓存

    提供 LLM 响应的智能缓存。

    使用示例:
        cache = LLMAcceleratorCache(max_size=1000)
        result = cache.get(prompt, config)
        if result is None:
            result = call_llm(prompt, config)
            cache.set(prompt, config, result)
    """

    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: float = 100.0,
        strategy: CacheStrategy = CacheStrategy.LRU,
        default_ttl: Optional[float] = 3600,
    ) -> None:
        """初始化缓存

        Args:
            max_size: 最大条目数
            max_memory_mb: 最大内存 (MB)
            strategy: 缓存策略
            default_ttl: 默认 TTL(秒)
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._max_memory_mb = max_memory_mb
        self._strategy = strategy
        self._default_ttl = default_ttl
        self._stats = CacheStats()
        self._lock = threading.Lock()

    def _make_key(
        self,
        prompt: str,
        config: Optional[dict[str, Any]] = None,
    ) -> str:
        """生成缓存键"""
        content = f"{prompt}:{json.dumps(config or {}, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _estimate_size(self, value: Any) -> int:
        """估算大小 (字节)"""
        try:
            return len(json.dumps(value).encode())
        except Exception:
            return 1024  # 默认 1KB

    def get(
        self,
        prompt: str,
        config: Optional[dict[str, Any]] = None,
    ) -> Optional[Any]:
        """获取缓存"""
        key = self._make_key(prompt, config)

        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats.misses += 1
                return None

            if entry.is_expired():
                self._remove(key)
                self._stats.misses += 1
                return None

            # 更新访问统计
            entry.touch()
            self._stats.hits += 1

            # LRU: 移动到末尾
            if self._strategy == CacheStrategy.LRU:
                self._cache.move_to_end(key)

            return entry.value

    def set(
        self,
        prompt: str,
        config: Optional[dict[str, Any]] = None,
        value: Any = None,
        ttl: Optional[float] = None,
    ) -> None:
        """设置缓存"""
        key = self._make_key(prompt, config)
        size = self._estimate_size(value)

        with self._lock:
            # 检查内存限制
            while (self._stats.total_size_bytes + size) > (self._max_memory_mb * 1024 * 1024):
                self._evict()

            # 检查大小限制
            while len(self._cache) >= self._max_size:
                self._evict()

            # 创建条目
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl if ttl is not None else self._default_ttl,
                size_bytes=size,
            )

            # 存储
            self._cache[key] = entry
            self._stats.total_size_bytes += size
            self._stats.entry_count = len(self._cache)

    def _evict(self) -> None:
        """驱逐条目"""
        if not self._cache:
            return

        key = self._select_eviction_target()
        if key:
            self._remove(key)
            self._stats.evictions += 1

    def _select_eviction_target(self) -> Optional[str]:
        """选择驱逐目标"""
        if not self._cache:
            return None

        if self._strategy == CacheStrategy.LRU:
            # 最早访问的
            return next(iter(self._cache))

        elif self._strategy == CacheStrategy.LFU:
            # 最少访问的
            return min(self._cache.keys(), key=lambda k: self._cache[k].access_count)

        elif self._strategy == CacheStrategy.FIFO:
            # 最早进入的
            return next(iter(self._cache))

        elif self._strategy == CacheStrategy.TTL:
            # 即将过期的
            now = time.time()
            return min(
                self._cache.keys(),
                key=lambda k: self._cache[k].created_at + (self._cache[k].ttl or float('inf')),
            )

        return next(iter(self._cache))

    def _remove(self, key: str) -> None:
        """移除条目"""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._stats.total_size_bytes -= entry.size_bytes
            self._stats.entry_count = len(self._cache)

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._stats.total_size_bytes = 0
            self._stats.entry_count = 0

    def get_stats(self) -> CacheStats:
        """获取统计"""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                total_size_bytes=self._stats.total_size_bytes,
                entry_count=len(self._cache),
            )

    def invalidate(self, prompt_pattern: str) -> int:
        """批量失效"""
        import re
        pattern = re.compile(prompt_pattern)
        removed = 0

        with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if pattern.search(entry.key)
            ]
            for key in keys_to_remove:
                self._remove(key)
                removed += 1

        return removed


class PromptTemplateCompiler:
    """提示模板编译器

    预编译提示模板，提升渲染性能。

    使用示例:
        compiler = PromptTemplateCompiler()
        compiled = compiler.compile("Hello {{name}}!")
        result = compiled.render(name="World")
    """

    def __init__(self) -> None:
        """初始化编译器"""
        self._compiled_templates: dict[str, Callable[[dict[str, Any]], str]] = {}
        self._template_hashes: dict[str, str] = {}
        self._lock = threading.Lock()

    def compile(self, template: str) -> Callable[[dict[str, Any]], str]:
        """编译模板"""
        import re

        # 生成哈希
        template_hash = hashlib.md5(template.encode()).hexdigest()

        with self._lock:
            if template_hash in self._compiled_templates:
                return self._compiled_templates[template_hash]

        # 提取变量
        variable_pattern = r'\{\{(\w+)\}\}'
        variables = re.findall(variable_pattern, template)

        # 创建编译函数
        def render(context: dict[str, Any]) -> str:
            result = template
            for var in variables:
                value = context.get(var, "")
                result = result.replace(f"{{{{{var}}}}}", str(value))
            return result

        with self._lock:
            self._compiled_templates[template_hash] = render
            self._template_hashes[template] = template_hash

        return render

    def render(
        self,
        template: str,
        context: dict[str, Any],
    ) -> str:
        """渲染模板（自动编译）"""
        compiled = self.compile(template)
        return compiled(context)

    def precompile_batch(self, templates: list[str]) -> int:
        """批量预编译"""
        count = 0
        for template in templates:
            self.compile(template)
            count += 1
        return count

    def get_stats(self) -> dict[str, Any]:
        """获取统计"""
        with self._lock:
            return {
                "compiled_count": len(self._compiled_templates),
                "templates": list(self._template_hashes.keys())[:10],  # 前 10 个
            }


class BatchOptimizer:
    """批量优化器

    优化批量 LLM 调用。

    使用示例:
        optimizer = BatchOptimizer(max_batch_size=10)
        results = optimizer.execute_batch(prompts, call_llm)
    """

    def __init__(
        self,
        max_batch_size: int = 10,
        max_concurrent: int = 5,
        timeout: float = 60.0,
    ) -> None:
        """初始化优化器

        Args:
            max_batch_size: 最大批量大小
            max_concurrent: 最大并发数
            timeout: 超时时间 (秒)
        """
        self._max_batch_size = max_batch_size
        self._max_concurrent = max_concurrent
        self._timeout = timeout
        self._semaphore = threading.Semaphore(max_concurrent)

    def execute_batch(
        self,
        items: list[Any],
        processor: Callable[[Any], Any],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BatchResult:
        """执行批量处理"""
        import concurrent.futures

        start_time = time.time()
        results: list[Any] = []
        errors: list[dict[str, Any]] = []
        success_count = 0
        error_count = 0

        def process_with_semaphore(item: Any, index: int) -> tuple[int, Any, Optional[dict]]:
            with self._semaphore:
                try:
                    result = processor(item)
                    if progress_callback:
                        progress_callback(index + 1, len(items))
                    return (index, result, None)
                except Exception as e:
                    return (index, None, {"index": index, "error": str(e)})

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_concurrent) as executor:
            futures = [
                executor.submit(process_with_semaphore, item, i)
                for i, item in enumerate(items)
            ]

            for future in concurrent.futures.as_completed(futures, timeout=self._timeout):
                index, result, error = future.result()
                if error:
                    errors.append(error)
                    error_count += 1
                else:
                    results.append((index, result))
                    success_count += 1

        # 按原始顺序排序
        results.sort(key=lambda x: x[0])
        results = [r[1] for r in results]

        total_time = time.time() - start_time

        return BatchResult(
            results=results,
            total_time=total_time,
            average_time=total_time / len(items) if items else 0,
            success_count=success_count,
            error_count=error_count,
            errors=errors,
        )

    def execute_batch_with_cache(
        self,
        items: list[dict[str, Any]],
        processor: Callable[[Any], Any],
        cache: LLMAcceleratorCache,
    ) -> BatchResult:
        """带缓存的批量处理"""
        start_time = time.time()
        results: list[Any] = []
        errors: list[dict[str, Any]] = []
        cache_hits = 0
        cache_misses = 0

        for i, item in enumerate(items):
            prompt = item.get("prompt", "")
            config = item.get("config")

            # 尝试从缓存获取
            cached = cache.get(prompt, config)
            if cached is not None:
                results.append(cached)
                cache_hits += 1
            else:
                # 调用处理器
                try:
                    result = processor(item)
                    cache.set(prompt, config, result)
                    results.append(result)
                    cache_misses += 1
                except Exception as e:
                    errors.append({"index": i, "error": str(e)})
                    results.append(None)

        total_time = time.time() - start_time

        return BatchResult(
            results=results,
            total_time=total_time,
            average_time=total_time / len(items) if items else 0,
            success_count=len(items) - len(errors),
            error_count=len(errors),
            errors=errors,
        )


class MemoryMonitor:
    """内存监控器

    监控内存使用情况。

    使用示例:
        monitor = MemoryMonitor()
        stats = monitor.get_stats()
    """

    def __init__(self) -> None:
        """初始化监控器"""
        self._history: list[MemoryStats] = []
        self._max_history = 100
        self._lock = threading.Lock()

    def get_stats(self) -> MemoryStats:
        """获取内存统计"""
        import sys

        stats = MemoryStats()

        try:
            # 尝试使用 psutil
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()

            stats.used_memory_mb = mem_info.rss / (1024 * 1024)
            stats.total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)
            stats.available_memory_mb = psutil.virtual_memory().available / (1024 * 1024)
        except ImportError:
            # 降级方案
            stats.used_memory_mb = sys.getsizeof(sys.modules) / (1024 * 1024)
            stats.total_memory_mb = 1024.0  # 假设 1GB
            stats.available_memory_mb = stats.total_memory_mb - stats.used_memory_mb

        # 估算对象数量
        stats.object_count = len(gc.get_objects()) if 'gc' in globals() else 0

        # 记录历史
        with self._lock:
            self._history.append(stats)
            if len(self._history) > self._max_history:
                self._history.pop(0)

        return stats

    def get_trend(self) -> dict[str, Any]:
        """获取内存趋势"""
        with self._lock:
            if len(self._history) < 2:
                return {"trend": "stable", "change_percent": 0}

            first = self._history[0].used_memory_mb
            last = self._history[-1].used_memory_mb
            change = last - first
            change_percent = (change / first * 100) if first > 0 else 0

            if change_percent > 10:
                trend = "increasing"
            elif change_percent < -10:
                trend = "decreasing"
            else:
                trend = "stable"

            return {
                "trend": trend,
                "change_percent": change_percent,
                "samples": len(self._history),
            }

    def check_threshold(self, threshold_percent: float = 80.0) -> bool:
        """检查是否超过阈值"""
        stats = self.get_stats()
        return stats.usage_percent > threshold_percent


class PerformanceOptimizer:
    """性能优化器

    整合各种优化功能。

    使用示例:
        optimizer = PerformanceOptimizer()
        report = optimizer.analyze_and_optimize(context)
    """

    def __init__(
        self,
        cache_max_size: int = 1000,
        cache_max_memory_mb: float = 100.0,
    ) -> None:
        """初始化优化器"""
        self._cache = LLMAcceleratorCache(
            max_size=cache_max_size,
            max_memory_mb=cache_max_memory_mb,
        )
        self._compiler = PromptTemplateCompiler()
        self._batch_optimizer = BatchOptimizer()
        self._memory_monitor = MemoryMonitor()
        self._optimization_history: list[OptimizationReport] = []
        self._lock = threading.Lock()

    def get_cache(self) -> LLMAcceleratorCache:
        """获取缓存实例"""
        return self._cache

    def get_compiler(self) -> PromptTemplateCompiler:
        """获取编译器实例"""
        return self._compiler

    def get_batch_optimizer(self) -> BatchOptimizer:
        """获取批量优化器实例"""
        return self._batch_optimizer

    def get_memory_monitor(self) -> MemoryMonitor:
        """获取内存监控器实例"""
        return self._memory_monitor

    def analyze_and_optimize(
        self,
        context: dict[str, Any],
    ) -> OptimizationReport:
        """分析并优化"""
        before_stats = self._gather_stats()

        # 自动优化建议
        recommendations = self._generate_recommendations(context, before_stats)

        after_stats = self._gather_stats()

        # 计算改进
        improvement = self._calculate_improvement(before_stats, after_stats)

        report = OptimizationReport(
            optimization_type=OptimizationType.CACHE,
            before_metrics=before_stats,
            after_metrics=after_stats,
            improvement_percent=improvement,
            recommendations=recommendations,
        )

        with self._lock:
            self._optimization_history.append(report)

        return report

    def _gather_stats(self) -> dict[str, Any]:
        """收集统计"""
        return {
            "cache": self._cache.get_stats().to_dict(),
            "compiler": self._compiler.get_stats(),
            "memory": self._memory_monitor.get_stats().to_dict(),
        }

    def _generate_recommendations(
        self,
        context: dict[str, Any],
        stats: dict[str, Any],
    ) -> list[str]:
        """生成优化建议"""
        recommendations = []

        cache_stats = stats.get("cache", {})
        if cache_stats.get("hit_rate", 0) < 0.5:
            recommendations.append("缓存命中率较低，考虑增加缓存大小或调整 TTL")

        memory_stats = stats.get("memory", {})
        if memory_stats.get("usage_percent", 0) > 80:
            recommendations.append("内存使用率较高，考虑清理缓存或优化数据结构")

        if context.get("batch_size", 0) > 20:
            recommendations.append("批量较大，考虑分批处理以减少内存压力")

        return recommendations

    def _calculate_improvement(
        self,
        before: dict[str, Any],
        after: dict[str, Any],
    ) -> float:
        """计算改进百分比"""
        # 简化计算
        before_cache_hit = before.get("cache", {}).get("hit_rate", 0)
        after_cache_hit = after.get("cache", {}).get("hit_rate", 0)

        if before_cache_hit == 0:
            return 0.0

        return ((after_cache_hit - before_cache_hit) / before_cache_hit) * 100

    def get_optimization_history(self) -> list[dict[str, Any]]:
        """获取优化历史"""
        with self._lock:
            return [r.to_dict() for r in self._optimization_history[-10:]]


# 全局实例
_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """获取全局性能优化器"""
    global _optimizer
    if _optimizer is None:
        _optimizer = PerformanceOptimizer()
    return _optimizer


def get_cache() -> LLMAcceleratorCache:
    """便捷函数：获取缓存"""
    return get_performance_optimizer().get_cache()


def compile_template(template: str) -> Callable[[dict[str, Any]], str]:
    """便捷函数：编译模板"""
    return get_performance_optimizer().get_compiler().compile(template)