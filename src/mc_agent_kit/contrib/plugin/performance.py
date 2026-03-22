"""
插件性能监控

监控插件执行性能，收集性能指标和统计信息。
"""

import logging
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型"""

    EXECUTION_TIME = "execution_time"  # 执行时间
    MEMORY_USAGE = "memory_usage"  # 内存使用
    CPU_USAGE = "cpu_usage"  # CPU 使用
    CALL_COUNT = "call_count"  # 调用次数
    ERROR_COUNT = "error_count"  # 错误次数
    CACHE_HIT = "cache_hit"  # 缓存命中
    CACHE_MISS = "cache_miss"  # 缓存未命中


@dataclass
class PerformanceMetric:
    """性能指标"""

    plugin_id: str
    metric_type: MetricType
    value: float
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class PluginStats:
    """插件统计信息"""

    plugin_id: str
    total_calls: int = 0
    total_errors: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    avg_time: float = 0.0
    last_call_time: float | None = None
    last_error: str | None = None
    metrics: list[PerformanceMetric] = field(default_factory=list)

    # 缓存统计
    cache_hits: int = 0
    cache_misses: int = 0

    @property
    def cache_hit_rate(self) -> float:
        """缓存命中率"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    @property
    def error_rate(self) -> float:
        """错误率"""
        if self.total_calls == 0:
            return 0.0
        return self.total_errors / self.total_calls

    def update_time(self, execution_time: float) -> None:
        """更新执行时间统计"""
        self.total_calls += 1
        self.total_time += execution_time
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.total_calls
        self.last_call_time = execution_time

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "total_calls": self.total_calls,
            "total_errors": self.total_errors,
            "total_time": self.total_time,
            "min_time": self.min_time if self.min_time != float("inf") else 0.0,
            "max_time": self.max_time,
            "avg_time": self.avg_time,
            "last_call_time": self.last_call_time,
            "last_error": self.last_error,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hit_rate,
            "error_rate": self.error_rate,
        }


@dataclass
class PerformanceAlert:
    """性能告警"""

    plugin_id: str
    alert_type: str
    message: str
    value: float
    threshold: float
    timestamp: float
    severity: str = "warning"  # info, warning, error, critical

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "alert_type": self.alert_type,
            "message": self.message,
            "value": self.value,
            "threshold": self.threshold,
            "timestamp": self.timestamp,
            "severity": self.severity,
        }


@dataclass
class PerformanceMonitorConfig:
    """性能监控配置"""

    enabled: bool = True
    slow_call_threshold: float = 1.0  # 慢调用阈值 (秒)
    error_rate_threshold: float = 0.1  # 错误率阈值 (10%)
    memory_threshold: float = 100 * 1024 * 1024  # 内存阈值 (100MB)
    max_metrics_per_plugin: int = 1000  # 每个插件最多保存的指标数
    alert_cooldown: float = 60.0  # 告警冷却时间 (秒)


class PluginPerformanceMonitor:
    """插件性能监控器

    监控插件执行性能，收集性能指标和统计信息。

    使用示例:
        monitor = PluginPerformanceMonitor()

        # 记录执行
        with monitor.track("my_plugin"):
            # 插件代码执行
            pass

        # 获取统计
        stats = monitor.get_stats("my_plugin")
        print(f"平均执行时间: {stats.avg_time}s")
    """

    def __init__(self, config: PerformanceMonitorConfig | None = None):
        """初始化性能监控器

        Args:
            config: 监控配置
        """
        self.config = config or PerformanceMonitorConfig()
        self._stats: dict[str, PluginStats] = defaultdict(lambda: PluginStats(plugin_id=""))
        self._alerts: list[PerformanceAlert] = []
        self._last_alert_time: dict[str, float] = {}  # plugin_id -> timestamp

    def track(self, plugin_id: str):
        """追踪插件执行时间

        Args:
            plugin_id: 插件 ID

        Returns:
            上下文管理器
        """
        return _ExecutionContext(self, plugin_id)

    def record_execution(
        self,
        plugin_id: str,
        execution_time: float,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        """记录执行信息

        Args:
            plugin_id: 插件 ID
            execution_time: 执行时间 (秒)
            success: 是否成功
            error: 错误消息
        """
        if not self.config.enabled:
            return

        # 初始化或获取统计
        if plugin_id not in self._stats:
            self._stats[plugin_id] = PluginStats(plugin_id=plugin_id)
        stats = self._stats[plugin_id]

        # 更新时间统计
        stats.update_time(execution_time)

        # 更新错误统计
        if not success:
            stats.total_errors += 1
            stats.last_error = error

        # 记录指标
        metric = PerformanceMetric(
            plugin_id=plugin_id,
            metric_type=MetricType.EXECUTION_TIME,
            value=execution_time,
            timestamp=time.time(),
            metadata={"success": success},
        )
        self._add_metric(stats, metric)

        # 检查告警
        self._check_alerts(plugin_id, execution_time, success)

    def record_cache_hit(self, plugin_id: str, hit: bool) -> None:
        """记录缓存命中/未命中

        Args:
            plugin_id: 插件 ID
            hit: 是否命中
        """
        if not self.config.enabled:
            return

        if plugin_id not in self._stats:
            self._stats[plugin_id] = PluginStats(plugin_id=plugin_id)
        stats = self._stats[plugin_id]

        if hit:
            stats.cache_hits += 1
        else:
            stats.cache_misses += 1

    def record_memory_usage(self, plugin_id: str, memory_bytes: float) -> None:
        """记录内存使用

        Args:
            plugin_id: 插件 ID
            memory_bytes: 内存使用量 (字节)
        """
        if not self.config.enabled:
            return

        if plugin_id not in self._stats:
            self._stats[plugin_id] = PluginStats(plugin_id=plugin_id)
        stats = self._stats[plugin_id]

        metric = PerformanceMetric(
            plugin_id=plugin_id,
            metric_type=MetricType.MEMORY_USAGE,
            value=memory_bytes,
            timestamp=time.time(),
        )
        self._add_metric(stats, metric)

        # 检查内存告警
        if memory_bytes > self.config.memory_threshold:
            self._create_alert(
                plugin_id=plugin_id,
                alert_type="memory",
                message=f"内存使用过高: {memory_bytes / 1024 / 1024:.2f}MB",
                value=memory_bytes,
                threshold=self.config.memory_threshold,
            )

    def get_stats(self, plugin_id: str) -> PluginStats | None:
        """获取插件统计信息

        Args:
            plugin_id: 插件 ID

        Returns:
            统计信息
        """
        return self._stats.get(plugin_id)

    def get_all_stats(self) -> dict[str, PluginStats]:
        """获取所有插件统计信息"""
        return dict(self._stats)

    def get_summary(self) -> dict[str, Any]:
        """获取性能摘要"""
        all_stats = self.get_all_stats()

        total_calls = sum(s.total_calls for s in all_stats.values())
        total_errors = sum(s.total_errors for s in all_stats.values())
        total_time = sum(s.total_time for s in all_stats.values())

        # 找出最慢的插件
        slowest = sorted(
            [s for s in all_stats.values() if s.total_calls > 0],
            key=lambda s: s.avg_time,
            reverse=True,
        )[:5]

        # 找出调用最多的插件
        most_called = sorted(
            [s for s in all_stats.values() if s.total_calls > 0],
            key=lambda s: s.total_calls,
            reverse=True,
        )[:5]

        # 找出错误最多的插件
        most_errors = sorted(
            [s for s in all_stats.values() if s.total_errors > 0],
            key=lambda s: s.total_errors,
            reverse=True,
        )[:5]

        return {
            "total_plugins": len(all_stats),
            "total_calls": total_calls,
            "total_errors": total_errors,
            "total_time": total_time,
            "error_rate": total_errors / total_calls if total_calls > 0 else 0.0,
            "slowest_plugins": [s.to_dict() for s in slowest],
            "most_called_plugins": [s.to_dict() for s in most_called],
            "most_errors_plugins": [s.to_dict() for s in most_errors],
            "active_alerts": len(self._alerts),
        }

    def get_alerts(self, limit: int = 100) -> list[PerformanceAlert]:
        """获取告警列表

        Args:
            limit: 最大数量

        Returns:
            告警列表
        """
        return self._alerts[-limit:]

    def clear_alerts(self) -> None:
        """清除所有告警"""
        self._alerts.clear()
        self._last_alert_time.clear()

    def reset_stats(self, plugin_id: str | None = None) -> None:
        """重置统计信息

        Args:
            plugin_id: 可选的插件 ID，为 None 则重置所有
        """
        if plugin_id:
            if plugin_id in self._stats:
                del self._stats[plugin_id]
        else:
            self._stats.clear()

    def _add_metric(self, stats: PluginStats, metric: PerformanceMetric) -> None:
        """添加指标"""
        stats.metrics.append(metric)

        # 限制指标数量
        if len(stats.metrics) > self.config.max_metrics_per_plugin:
            stats.metrics = stats.metrics[-self.config.max_metrics_per_plugin :]

    def _check_alerts(self, plugin_id: str, execution_time: float, success: bool) -> None:
        """检查是否需要生成告警"""
        stats = self._stats.get(plugin_id)
        if not stats:
            return

        # 检查慢调用
        if execution_time > self.config.slow_call_threshold:
            self._create_alert(
                plugin_id=plugin_id,
                alert_type="slow_call",
                message=f"执行时间过长: {execution_time:.3f}s",
                value=execution_time,
                threshold=self.config.slow_call_threshold,
            )

        # 检查错误率
        if stats.total_calls >= 10 and stats.error_rate > self.config.error_rate_threshold:
            self._create_alert(
                plugin_id=plugin_id,
                alert_type="high_error_rate",
                message=f"错误率过高: {stats.error_rate:.1%}",
                value=stats.error_rate,
                threshold=self.config.error_rate_threshold,
                severity="error",
            )

    def _create_alert(
        self,
        plugin_id: str,
        alert_type: str,
        message: str,
        value: float,
        threshold: float,
        severity: str = "warning",
    ) -> None:
        """创建告警"""
        # 检查冷却时间
        alert_key = f"{plugin_id}:{alert_type}"
        current_time = time.time()
        last_time = self._last_alert_time.get(alert_key, 0)

        if current_time - last_time < self.config.alert_cooldown:
            return

        self._last_alert_time[alert_key] = current_time

        alert = PerformanceAlert(
            plugin_id=plugin_id,
            alert_type=alert_type,
            message=message,
            value=value,
            threshold=threshold,
            timestamp=current_time,
            severity=severity,
        )
        self._alerts.append(alert)

        # 限制告警数量
        if len(self._alerts) > 1000:
            self._alerts = self._alerts[-1000:]

        logger.warning(f"[PluginMonitor] {severity.upper()}: {plugin_id} - {message}")


class _ExecutionContext:
    """执行上下文管理器"""

    def __init__(self, monitor: PluginPerformanceMonitor, plugin_id: str):
        self.monitor = monitor
        self.plugin_id = plugin_id
        self.start_time: float | None = None
        self.error: str | None = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is None:
            return False

        execution_time = time.time() - self.start_time
        success = exc_type is None
        error = str(exc_val) if exc_val else None

        self.monitor.record_execution(
            plugin_id=self.plugin_id,
            execution_time=execution_time,
            success=success,
            error=error,
        )

        return False  # 不吞掉异常


def create_performance_monitor(config: PerformanceMonitorConfig | None = None) -> PluginPerformanceMonitor:
    """创建性能监控器的便捷函数"""
    return PluginPerformanceMonitor(config)