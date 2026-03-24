"""
性能分析模块

提供代码性能分析、内存监控和性能报告功能。
"""

from __future__ import annotations
import cProfile
import io
import logging
import pstats
import threading
import time
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class ProfilingStatus(Enum):
    """分析状态"""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class PerformanceConfig:
    """性能分析配置"""

    enable_memory_profiling: bool = True  # 启用内存分析
    enable_cpu_profiling: bool = True  # 启用 CPU 分析
    sample_interval: float = 0.01  # 采样间隔（秒）
    max_snapshots: int = 100  # 最大快照数
    memory_threshold_mb: float = 100.0  # 内存阈值（MB）
    time_threshold_ms: float = 1000.0  # 时间阈值（毫秒）
    sort_by: str = "cumulative"  # 排序方式


@dataclass
class ProfilingResult:
    """分析结果"""

    function_name: str
    calls: int
    total_time: float  # 总时间（秒）
    cumulative_time: float  # 累计时间（秒）
    avg_time: float  # 平均时间（秒）
    min_time: float  # 最小时间（秒）
    max_time: float  # 最大时间（秒）
    file_name: str | None = None
    line_number: int | None = None


@dataclass
class MemorySnapshot:
    """内存快照"""

    timestamp: datetime
    current_size: int  # 当前内存大小（字节）
    peak_size: int  # 峰值内存大小（字节）
    allocated_blocks: int  # 分配的内存块数
    freed_blocks: int  # 释放的内存块数
    top_allocations: list[tuple[str, int]] = field(default_factory=list)  # 最大的分配


@dataclass
class PerformanceReport:
    """性能报告"""

    start_time: datetime
    end_time: datetime
    total_time: float  # 总时间（秒）
    total_calls: int
    cpu_time: float  # CPU 时间（秒）
    peak_memory_mb: float  # 峰值内存（MB）
    avg_memory_mb: float  # 平均内存（MB）
    hotspots: list[ProfilingResult]  # 热点函数
    memory_timeline: list[MemorySnapshot]  # 内存时间线
    recommendations: list[str]  # 优化建议
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TimingResult:
    """计时结果"""

    name: str
    elapsed_ms: float
    start_time: datetime
    end_time: datetime
    success: bool = True
    error: str | None = None


class Timer:
    """
    简单计时器。

    使用示例:
        timer = Timer()
        timer.start()
        # ... 执行代码 ...
        elapsed = timer.stop()
        print(f"耗时: {elapsed:.2f} 秒")
    """

    def __init__(self, name: str = ""):
        self.name = name
        self._start_time: float | None = None
        self._end_time: float | None = None
        self._elapsed: float = 0.0

    def start(self) -> "Timer":
        """开始计时"""
        self._start_time = time.perf_counter()
        self._end_time = None
        return self

    def stop(self) -> float:
        """停止计时并返回耗时"""
        self._end_time = time.perf_counter()
        if self._start_time:
            self._elapsed = self._end_time - self._start_time
        return self._elapsed

    def elapsed_ms(self) -> float:
        """获取耗时（毫秒）"""
        return self._elapsed * 1000

    def elapsed(self) -> float:
        """获取耗时（秒）"""
        return self._elapsed

    def reset(self) -> None:
        """重置计时器"""
        self._start_time = None
        self._end_time = None
        self._elapsed = 0.0

    def __enter__(self) -> "Timer":
        self.start()
        return self

    def __exit__(self, *args) -> None:
        self.stop()


class PerformanceAnalyzer:
    """
    性能分析器。

    提供代码性能分析、内存监控和报告生成功能。

    使用示例:
        analyzer = PerformanceAnalyzer()

        # 分析函数
        @analyzer.profile
        def my_function():
            pass

        # 手动分析
        analyzer.start()
        # ... 执行代码 ...
        report = analyzer.stop()

        # 分析代码块
        with analyzer.profile_block("my_block"):
            # ... 执行代码 ...
            pass
    """

    def __init__(self, config: PerformanceConfig | None = None):
        """
        初始化性能分析器。

        Args:
            config: 分析配置
        """
        self.config = config or PerformanceConfig()
        self._profiler: cProfile.Profile | None = None
        self._status = ProfilingStatus.IDLE
        self._start_time: datetime | None = None
        self._end_time: datetime | None = None
        self._memory_snapshots: list[MemorySnapshot] = []
        self._timings: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def start(self) -> None:
        """开始性能分析"""
        if self._status == ProfilingStatus.RUNNING:
            return

        self._start_time = datetime.now()
        self._status = ProfilingStatus.RUNNING
        self._memory_snapshots.clear()

        # 启动 CPU 分析
        if self.config.enable_cpu_profiling:
            self._profiler = cProfile.Profile()
            self._profiler.enable()

        # 启动内存分析
        if self.config.enable_memory_profiling:
            if not tracemalloc.is_tracing():
                tracemalloc.start()
            self._take_memory_snapshot()

    def stop(self) -> PerformanceReport:
        """停止性能分析并生成报告"""
        if self._status != ProfilingStatus.RUNNING:
            return self._generate_empty_report()

        self._end_time = datetime.now()
        self._status = ProfilingStatus.COMPLETED

        # 停止 CPU 分析
        cpu_stats = None
        if self._profiler:
            self._profiler.disable()
            cpu_stats = self._get_cpu_stats()

        # 停止内存分析并获取最终快照
        if self.config.enable_memory_profiling:
            self._take_memory_snapshot()

        # 生成报告
        return self._generate_report(cpu_stats)

    def pause(self) -> None:
        """暂停分析"""
        if self._profiler:
            self._profiler.disable()
        self._status = ProfilingStatus.PAUSED

    def resume(self) -> None:
        """恢复分析"""
        if self._profiler:
            self._profiler.enable()
        self._status = ProfilingStatus.RUNNING

    def profile(self, func: Callable) -> Callable:
        """
        装饰器：分析函数性能。

        Args:
            func: 要分析的函数

        Returns:
            包装后的函数
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            name = func.__qualname__

            # 计时
            timer = Timer(name)
            timer.start()

            try:
                result = func(*args, **kwargs)
                timer.stop()

                # 记录时间
                with self._lock:
                    if name not in self._timings:
                        self._timings[name] = []
                    self._timings[name].append(timer.elapsed_ms())

                return result

            except Exception as e:
                timer.stop()
                raise e

        return wrapper

    def profile_block(self, name: str) -> Timer:
        """
        分析代码块的上下文管理器。

        Args:
            name: 代码块名称

        Returns:
            Timer 上下文管理器
        """
        timer = Timer(name)
        return timer

    def record_timing(self, name: str, elapsed_ms: float) -> None:
        """
        记录计时数据。

        Args:
            name: 名称
            elapsed_ms: 耗时（毫秒）
        """
        with self._lock:
            if name not in self._timings:
                self._timings[name] = []
            self._timings[name].append(elapsed_ms)

    def get_timing_stats(self, name: str) -> dict[str, float] | None:
        """
        获取计时统计。

        Args:
            name: 名称

        Returns:
            统计数据
        """
        timings = self._timings.get(name)
        if not timings:
            return None

        return {
            "count": len(timings),
            "total": sum(timings),
            "avg": sum(timings) / len(timings),
            "min": min(timings),
            "max": max(timings),
        }

    def take_snapshot(self) -> MemorySnapshot | None:
        """获取内存快照"""
        if not self.config.enable_memory_profiling:
            return None
        return self._take_memory_snapshot()

    def compare_snapshots(
        self, snapshot1: MemorySnapshot, snapshot2: MemorySnapshot
    ) -> dict[str, Any]:
        """
        比较两个快照。

        Args:
            snapshot1: 快照1
            snapshot2: 快照2

        Returns:
            比较结果
        """
        return {
            "memory_diff": snapshot2.current_size - snapshot1.current_size,
            "peak_diff": snapshot2.peak_size - snapshot1.peak_size,
            "blocks_diff": snapshot2.allocated_blocks - snapshot1.allocated_blocks,
        }

    def get_status(self) -> ProfilingStatus:
        """获取分析状态"""
        return self._status

    def reset(self) -> None:
        """重置分析器"""
        self._profiler = None
        self._status = ProfilingStatus.IDLE
        self._start_time = None
        self._end_time = None
        self._memory_snapshots.clear()
        self._timings.clear()

    def _take_memory_snapshot(self) -> MemorySnapshot:
        """获取内存快照"""
        if not tracemalloc.is_tracing():
            return MemorySnapshot(
                timestamp=datetime.now(),
                current_size=0,
                peak_size=0,
                allocated_blocks=0,
                freed_blocks=0,
            )

        snapshot = tracemalloc.take_snapshot()
        current, peak = tracemalloc.get_traced_memory()

        # 获取最大的分配
        top_stats = snapshot.statistics("lineno")[:10]
        top_allocations = [
            (str(stat), stat.size) for stat in top_stats
        ]

        memory_snapshot = MemorySnapshot(
            timestamp=datetime.now(),
            current_size=current,
            peak_size=peak,
            allocated_blocks=len(snapshot.statistics("lineno")),
            freed_blocks=0,  # tracemalloc 不直接提供
            top_allocations=top_allocations,
        )

        self._memory_snapshots.append(memory_snapshot)

        # 限制快照数量
        if len(self._memory_snapshots) > self.config.max_snapshots:
            self._memory_snapshots.pop(0)

        return memory_snapshot

    def _get_cpu_stats(self) -> pstats.Stats | None:
        """获取 CPU 统计"""
        if not self._profiler:
            return None

        stream = io.StringIO()
        stats = pstats.Stats(self._profiler, stream=stream)
        return stats

    def _generate_report(self, cpu_stats: pstats.Stats | None) -> PerformanceReport:
        """生成性能报告"""
        total_time = 0.0
        if self._start_time and self._end_time:
            total_time = (self._end_time - self._start_time).total_seconds()

        # 解析 CPU 热点
        hotspots = self._extract_hotspots(cpu_stats)

        # 计算内存统计
        peak_memory = 0.0
        avg_memory = 0.0
        if self._memory_snapshots:
            peak_memory = max(s.peak_size for s in self._memory_snapshots) / (1024 * 1024)
            avg_memory = sum(s.current_size for s in self._memory_snapshots) / len(self._memory_snapshots) / (1024 * 1024)

        # 生成优化建议
        recommendations = self._generate_recommendations(hotspots, peak_memory, total_time)

        return PerformanceReport(
            start_time=self._start_time or datetime.now(),
            end_time=self._end_time or datetime.now(),
            total_time=total_time,
            total_calls=sum(h.calls for h in hotspots),
            cpu_time=total_time,  # 简化
            peak_memory_mb=peak_memory,
            avg_memory_mb=avg_memory,
            hotspots=hotspots[:20],  # 只保留前 20 个热点
            memory_timeline=self._memory_snapshots,
            recommendations=recommendations,
        )

    def _extract_hotspots(self, cpu_stats: pstats.Stats | None) -> list[ProfilingResult]:
        """提取热点函数"""
        if not cpu_stats:
            return []

        hotspots = []

        # 获取排序后的统计
        stats_profile = cpu_stats.strip_dirs().get_stats_profile()

        # StatsProfile.func_profiles 是一个字典
        func_profiles = stats_profile.func_profiles

        for func_name, stat in func_profiles.items():
            # ncalls 可能是字符串格式 "1" 或 "1/1" (递归调用)
            ncalls_str = str(stat.ncalls)
            if "/" in ncalls_str:
                # 递归调用格式 "primcalls/total_calls"
                ncalls = int(ncalls_str.split("/")[1])
            else:
                ncalls = int(ncalls_str)

            hotspots.append(
                ProfilingResult(
                    function_name=func_name,
                    calls=ncalls,
                    total_time=stat.tottime,
                    cumulative_time=stat.cumtime,
                    avg_time=stat.tottime / ncalls if ncalls > 0 else 0,
                    min_time=0,  # pstats 不提供
                    max_time=0,
                    file_name=stat.file_name,
                    line_number=stat.line_number,
                )
            )

        # 按累计时间排序
        hotspots.sort(key=lambda x: x.cumulative_time, reverse=True)

        return hotspots

    def _generate_recommendations(
        self, hotspots: list[ProfilingResult], peak_memory: float, total_time: float
    ) -> list[str]:
        """生成优化建议"""
        recommendations = []

        # 检查热点函数
        if hotspots:
            top_hotspot = hotspots[0]
            if top_hotspot.cumulative_time / total_time > 0.3:
                recommendations.append(
                    f"热点函数 '{top_hotspot.function_name}' 占用了 {top_hotspot.cumulative_time / total_time * 100:.1f}% 的时间，考虑优化"
                )

        # 检查内存使用
        if peak_memory > self.config.memory_threshold_mb:
            recommendations.append(
                f"峰值内存 {peak_memory:.1f}MB 超过阈值 {self.config.memory_threshold_mb}MB，检查内存泄漏"
            )

        # 检查调用次数
        high_call_funcs = [h for h in hotspots if h.calls > 10000]
        if high_call_funcs:
            recommendations.append(
                f"发现 {len(high_call_funcs)} 个函数调用次数超过 10000 次，考虑缓存或批量处理"
            )

        if not recommendations:
            recommendations.append("性能表现良好，无需特别优化")

        return recommendations

    def _generate_empty_report(self) -> PerformanceReport:
        """生成空报告"""
        now = datetime.now()
        return PerformanceReport(
            start_time=now,
            end_time=now,
            total_time=0,
            total_calls=0,
            cpu_time=0,
            peak_memory_mb=0,
            avg_memory_mb=0,
            hotspots=[],
            memory_timeline=[],
            recommendations=["未进行性能分析"],
        )


class MemoryMonitor:
    """
    内存监控器。

    持续监控内存使用情况。

    使用示例:
        monitor = MemoryMonitor()
        monitor.start()

        # 获取当前内存使用
        usage = monitor.get_current_usage()

        monitor.stop()
    """

    def __init__(self, threshold_mb: float = 100.0, interval: float = 1.0):
        """
        初始化内存监控器。

        Args:
            threshold_mb: 内存阈值（MB）
            interval: 监控间隔（秒）
        """
        self.threshold_mb = threshold_mb
        self.interval = interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._snapshots: list[MemorySnapshot] = []
        self._on_threshold_exceeded: Callable[[float], None] | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """开始监控"""
        if self._running:
            return

        self._running = True
        tracemalloc.start()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        tracemalloc.stop()

    def get_current_usage(self) -> dict[str, float]:
        """获取当前内存使用"""
        if not tracemalloc.is_tracing():
            return {"current_mb": 0, "peak_mb": 0}

        current, peak = tracemalloc.get_traced_memory()
        return {
            "current_mb": current / (1024 * 1024),
            "peak_mb": peak / (1024 * 1024),
        }

    def get_history(self) -> list[MemorySnapshot]:
        """获取监控历史"""
        with self._lock:
            return self._snapshots.copy()

    def set_on_threshold_exceeded(self, callback: Callable[[float], None]) -> None:
        """设置阈值超标回调"""
        self._on_threshold_exceeded = callback

    def _monitor_loop(self) -> None:
        """监控循环"""
        while self._running:
            try:
                current, peak = tracemalloc.get_traced_memory()
                current_mb = current / (1024 * 1024)

                # 检查阈值
                if current_mb > self.threshold_mb and self._on_threshold_exceeded:
                    self._on_threshold_exceeded(current_mb)

                # 记录快照
                snapshot = tracemalloc.take_snapshot()
                with self._lock:
                    self._snapshots.append(
                        MemorySnapshot(
                            timestamp=datetime.now(),
                            current_size=current,
                            peak_size=peak,
                            allocated_blocks=len(snapshot.statistics("lineno")),
                            freed_blocks=0,
                        )
                    )

                    # 限制历史长度
                    if len(self._snapshots) > 100:
                        self._snapshots.pop(0)

            except Exception as e:
                logger.error(f"内存监控失败: {e}")

            time.sleep(self.interval)


def measure_time(func: Callable) -> Callable:
    """
    装饰器：测量函数执行时间。

    使用示例:
        @measure_time
        def my_function():
            pass
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(f"{func.__qualname__} 耗时: {elapsed:.2f}ms")
            return result
        except Exception:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(f"{func.__qualname__} 失败 (耗时: {elapsed:.2f}ms)")
            raise

    return wrapper


def benchmark(func: Callable, iterations: int = 1000) -> dict[str, float]:
    """
    基准测试函数。

    Args:
        func: 要测试的函数
        iterations: 迭代次数

    Returns:
        测试结果
    """
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        func()
        times.append(time.perf_counter() - start)

    return {
        "iterations": iterations,
        "total_time": sum(times),
        "avg_time": sum(times) / len(times),
        "min_time": min(times),
        "max_time": max(times),
    }
