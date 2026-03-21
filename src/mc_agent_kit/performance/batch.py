"""
日志批处理优化

提供日志批量处理和聚合功能，减少 I/O 操作。
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class BatchConfig:
    """批处理配置"""
    batch_size: int = 100  # 批次大小
    flush_interval: float = 5.0  # 刷新间隔（秒）
    max_queue_size: int = 10000  # 最大队列大小


@dataclass
class BatchResult:
    """批处理结果"""
    processed_count: int
    dropped_count: int
    processing_time: float


class LogBatchProcessor:
    """
    日志批处理器
    
    批量处理日志，减少 I/O 操作，提高性能。
    
    使用示例:
        config = BatchConfig(batch_size=100, flush_interval=5.0)
        processor = LogBatchProcessor(config)
        
        # 添加日志
        processor.add("日志内容 1")
        processor.add("日志内容 2")
        
        # 批量处理
        result = processor.flush()
    """
    
    def __init__(
        self,
        config: BatchConfig | None = None,
        process_fn: Callable[[list[str]], Any] | None = None,
    ):
        """
        初始化批处理器
        
        Args:
            config: 批处理配置
            process_fn: 处理函数（接收日志列表）
        """
        self.config = config or BatchConfig()
        self.process_fn = process_fn
        self._queue: deque[str] = deque(maxlen=self.config.max_queue_size)
        self._last_flush = time.time()
        self._stats = {
            "total_added": 0,
            "total_processed": 0,
            "total_dropped": 0,
            "flush_count": 0,
        }
        self._dropped_count = 0
    
    def add(self, log: str) -> bool:
        """
        添加日志到队列
        
        Args:
            log: 日志内容
            
        Returns:
            是否添加成功
        """
        if len(self._queue) >= self.config.max_queue_size:
            self._dropped_count += 1
            self._stats["total_dropped"] += 1
            return False
        
        self._queue.append(log)
        self._stats["total_added"] += 1
        
        # 检查是否需要自动刷新
        if len(self._queue) >= self.config.batch_size:
            self.flush()
        
        return True
    
    def flush(self) -> BatchResult | None:
        """
        刷新队列，处理所有日志
        
        Returns:
            批处理结果，如果队列为空返回 None
        """
        if not self._queue:
            return None
        
        start_time = time.time()
        
        # 取出所有日志
        logs = list(self._queue)
        self._queue.clear()
        
        # 调用处理函数
        if self.process_fn:
            try:
                self.process_fn(logs)
            except Exception:
                pass  # 静默处理异常，避免影响主流程
        
        processing_time = time.time() - start_time
        
        self._stats["total_processed"] += len(logs)
        self._stats["flush_count"] += 1
        self._last_flush = time.time()
        
        return BatchResult(
            processed_count=len(logs),
            dropped_count=self._dropped_count,
            processing_time=processing_time,
        )
    
    def should_flush(self) -> bool:
        """
        检查是否应该刷新
        
        Returns:
            是否应该刷新
        """
        # 队列满
        if len(self._queue) >= self.config.batch_size:
            return True
        
        # 时间到
        if (time.time() - self._last_flush) > self.config.flush_interval:
            return True
        
        return False
    
    def auto_flush(self) -> BatchResult | None:
        """
        自动刷新（如果满足条件）
        
        Returns:
            批处理结果
        """
        if self.should_flush():
            return self.flush()
        return None
    
    def stats(self) -> dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            **self._stats,
            "queue_size": len(self._queue),
            "max_queue_size": self.config.max_queue_size,
            "batch_size": self.config.batch_size,
            "flush_interval": self.config.flush_interval,
            "last_flush": self._last_flush,
        }
    
    def clear(self) -> None:
        """清空队列"""
        self._queue.clear()
        self._dropped_count = 0


class LogAggregator:
    """
    日志聚合器
    
    聚合相似日志，减少重复输出。
    
    使用示例:
        aggregator = LogAggregator(window_seconds=10)
        aggregator.add("Error: connection failed")
        aggregator.add("Error: connection failed")  # 会被聚合
        aggregator.add("Error: timeout")  # 不同类型
        
        # 获取聚合结果
        summary = aggregator.get_summary()
    """
    
    def __init__(self, window_seconds: float = 10.0):
        """
        初始化聚合器
        
        Args:
            window_seconds: 聚合时间窗口（秒）
        """
        self.window_seconds = window_seconds
        self._counts: dict[str, int] = {}
        self._first_seen: dict[str, float] = {}
        self._last_seen: dict[str, float] = {}
    
    def add(self, log: str) -> None:
        """
        添加日志
        
        Args:
            log: 日志内容
        """
        now = time.time()
        
        if log in self._counts:
            self._counts[log] += 1
            self._last_seen[log] = now
        else:
            self._counts[log] = 1
            self._first_seen[log] = now
            self._last_seen[log] = now
    
    def get_summary(self) -> list[dict[str, Any]]:
        """
        获取聚合摘要
        
        Returns:
            聚合结果列表
        """
        summary = []
        
        for log, count in self._counts.items():
            summary.append({
                "log": log,
                "count": count,
                "first_seen": self._first_seen[log],
                "last_seen": self._last_seen[log],
                "duration": self._last_seen[log] - self._first_seen[log],
            })
        
        # 按出现次数排序
        summary.sort(key=lambda x: x["count"], reverse=True)
        
        return summary
    
    def clear(self) -> None:
        """清空聚合器"""
        self._counts.clear()
        self._first_seen.clear()
        self._last_seen.clear()
    
    def expire_old(self, max_age_seconds: float | None = None) -> int:
        """
        清除过期的聚合项
        
        Args:
            max_age_seconds: 最大年龄（秒），None 使用 window_seconds
            
        Returns:
            清除的条目数
        """
        max_age = max_age_seconds or self.window_seconds
        now = time.time()
        
        expired = [
            log for log, first_seen in self._first_seen.items()
            if (now - first_seen) > max_age
        ]
        
        for log in expired:
            del self._counts[log]
            del self._first_seen[log]
            del self._last_seen[log]
        
        return len(expired)
