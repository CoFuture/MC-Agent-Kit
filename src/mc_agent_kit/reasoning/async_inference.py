"""
异步推理引擎模块

提供异步推理接口、推理任务队列和回调机制。
"""

from __future__ import annotations

import asyncio
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .enhanced_inference_engine import (
    EnhancedInferenceEngine,
    EnhancedInferenceResult,
    ReasoningContext,
    ReasoningStatus,
    get_enhanced_inference_engine,
)
from .enhanced_causal_engine import (
    EnhancedCausalEngine,
    DiagnosticResult,
    get_enhanced_causal_engine,
)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    """任务优先级"""
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class InferenceTask:
    """推理任务"""
    id: str
    context: ReasoningContext
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[EnhancedInferenceResult] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    callback: Optional[InferenceCallback] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "priority": self.priority.value,
            "status": self.status.value,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "context_summary": self.context.query[:50] if self.context else None,
        }

    @property
    def duration(self) -> Optional[float]:
        """计算任务持续时间"""
        if self.started_at is None:
            return None
        end = self.completed_at or time.time()
        return end - self.started_at


@dataclass
class InferenceCallback:
    """推理回调"""
    on_complete: Optional[Callable[[EnhancedInferenceResult], None]] = None
    on_error: Optional[Callable[[str], None]] = None
    on_timeout: Optional[Callable[[], None]] = None

    def complete(self, result: EnhancedInferenceResult) -> None:
        """完成回调"""
        if self.on_complete:
            try:
                self.on_complete(result)
            except Exception:
                pass

    def error(self, error_msg: str) -> None:
        """错误回调"""
        if self.on_error:
            try:
                self.on_error(error_msg)
            except Exception:
                pass

    def timeout(self) -> None:
        """超时回调"""
        if self.on_timeout:
            try:
                self.on_timeout()
            except Exception:
                pass


class InferenceQueue:
    """
    推理任务队列

    支持优先级队列、任务调度和结果回调。

    使用示例:
        queue = InferenceQueue()
        queue.start()
        task_id = queue.submit(context, callback)
        result = queue.get_result(task_id)
    """

    def __init__(
        self,
        max_workers: int = 4,
        max_queue_size: int = 100,
    ) -> None:
        self._max_workers = max_workers
        self._max_queue_size = max_queue_size
        self._queue: list[InferenceTask] = []
        self._pending: dict[str, InferenceTask] = {}
        self._completed: dict[str, InferenceTask] = {}
        self._running: dict[str, InferenceTask] = {}
        self._workers: list[threading.Thread] = []
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._running_flag = False
        self._engine: Optional[EnhancedInferenceEngine] = None

    def start(self) -> None:
        """启动工作线程"""
        with self._lock:
            if self._running_flag:
                return

            self._running_flag = True
            self._engine = get_enhanced_inference_engine()

            for i in range(self._max_workers):
                worker = threading.Thread(
                    target=self._worker_loop,
                    name=f"InferenceWorker-{i}",
                    daemon=True,
                )
                worker.start()
                self._workers.append(worker)

    def stop(self, wait: bool = True) -> None:
        """停止工作线程"""
        with self._condition:
            self._running_flag = False
            self._condition.notify_all()

        if wait:
            for worker in self._workers:
                worker.join(timeout=5.0)

        self._workers.clear()

    def submit(
        self,
        context: ReasoningContext,
        priority: TaskPriority = TaskPriority.NORMAL,
        callback: Optional[InferenceCallback] = None,
    ) -> str:
        """
        提交推理任务

        Args:
            context: 推理上下文
            priority: 任务优先级
            callback: 回调函数

        Returns:
            任务 ID
        """
        with self._condition:
            if len(self._queue) >= self._max_queue_size:
                raise RuntimeError("Queue is full")

            task_id = str(uuid.uuid4())
            task = InferenceTask(
                id=task_id,
                context=context,
                priority=priority,
                callback=callback,
            )

            self._pending[task_id] = task
            self._queue.append(task)

            # 按优先级排序
            self._queue.sort(key=lambda t: t.priority.value)

            self._condition.notify()
            return task_id

    def get_task(self, task_id: str) -> Optional[InferenceTask]:
        """获取任务"""
        with self._lock:
            if task_id in self._running:
                return self._running[task_id]
            if task_id in self._completed:
                return self._completed[task_id]
            if task_id in self._pending:
                return self._pending[task_id]
            return None

    def get_result(self, task_id: str) -> Optional[EnhancedInferenceResult]:
        """获取任务结果"""
        task = self.get_task(task_id)
        if task and task.status == TaskStatus.COMPLETED:
            return task.result
        return None

    def cancel(self, task_id: str) -> bool:
        """取消任务"""
        with self._lock:
            if task_id in self._pending:
                task = self._pending.pop(task_id)
                task.status = TaskStatus.CANCELLED
                if task in self._queue:
                    self._queue.remove(task)
                return True
            return False

    def get_stats(self) -> dict[str, Any]:
        """获取队列统计"""
        with self._lock:
            return {
                "queue_size": len(self._queue),
                "pending": len(self._pending),
                "running": len(self._running),
                "completed": len(self._completed),
                "max_workers": self._max_workers,
                "max_queue_size": self._max_queue_size,
                "is_running": self._running_flag,
            }

    def clear_completed(self, max_age: float = 3600) -> int:
        """清理已完成的任务"""
        count = 0
        with self._lock:
            current_time = time.time()
            to_remove = [
                task_id for task_id, task in self._completed.items()
                if task.completed_at and current_time - task.completed_at > max_age
            ]
            for task_id in to_remove:
                del self._completed[task_id]
                count += 1
        return count

    def _worker_loop(self) -> None:
        """工作线程主循环"""
        while True:
            task = None

            with self._condition:
                while self._running_flag and not self._queue:
                    self._condition.wait(timeout=1.0)

                if not self._running_flag:
                    break

                if self._queue:
                    task = self._queue.pop(0)
                    if task.id in self._pending:
                        self._pending.pop(task.id)
                    task.status = TaskStatus.RUNNING
                    task.started_at = time.time()
                    self._running[task.id] = task

            if task:
                try:
                    self._process_task(task)
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    if task.callback:
                        task.callback.error(str(e))

                with self._lock:
                    self._running.pop(task.id, None)
                    self._completed[task.id] = task

    def _process_task(self, task: InferenceTask) -> None:
        """处理任务"""
        if self._engine is None:
            raise RuntimeError("Engine not initialized")

        result = self._engine.infer(task.context)

        task.result = result
        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()

        if task.callback:
            task.callback.complete(result)


class AsyncInferenceEngine:
    """
    异步推理引擎

    提供异步推理接口和并发搜索支持。

    使用示例:
        engine = AsyncInferenceEngine()
        await engine.start()

        # 异步推理
        result = await engine.infer_async(context)

        # 并发推理
        results = await engine.infer_batch([ctx1, ctx2, ctx3])

        # 流式结果
        async for result in engine.infer_stream(contexts):
            print(result)
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        timeout: float = 30.0,
    ) -> None:
        self._max_concurrent = max_concurrent
        self._timeout = timeout
        self._queue = InferenceQueue(max_workers=max_concurrent)
        self._engine: Optional[EnhancedInferenceEngine] = None
        self._causal_engine: Optional[EnhancedCausalEngine] = None
        self._started = False
        self._lock = threading.RLock()

    async def start(self) -> None:
        """启动引擎"""
        with self._lock:
            if self._started:
                return

            self._queue.start()
            self._engine = get_enhanced_inference_engine()
            self._causal_engine = get_enhanced_causal_engine()
            self._started = True

    async def stop(self) -> None:
        """停止引擎"""
        with self._lock:
            self._queue.stop()
            self._started = False

    async def infer_async(
        self,
        context: ReasoningContext,
    ) -> EnhancedInferenceResult:
        """
        异步推理

        Args:
            context: 推理上下文

        Returns:
            推理结果
        """
        if not self._started:
            await self.start()

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._sync_infer,
            context,
        )
        return result

    def _sync_infer(self, context: ReasoningContext) -> EnhancedInferenceResult:
        """同步推理（在线程池中执行）"""
        if self._engine is None:
            raise RuntimeError("Engine not initialized")
        return self._engine.infer(context)

    async def infer_batch(
        self,
        contexts: list[ReasoningContext],
    ) -> list[EnhancedInferenceResult]:
        """
        并发推理

        Args:
            contexts: 推理上下文列表

        Returns:
            推理结果列表
        """
        if not self._started:
            await self.start()

        # 创建并发任务
        tasks = [
            asyncio.create_task(self.infer_async(ctx))
            for ctx in contexts
        ]

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed: list[EnhancedInferenceResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed.append(EnhancedInferenceResult(
                    reasoning_type=getattr(contexts[i], 'reasoning_type', None) or 'deductive',
                    conclusions=[],
                    confidence=0.0,
                    reasoning_chain=[],
                    evidence=[],
                    execution_time=0.0,
                    status=ReasoningStatus.FAILED,
                ))
            else:
                processed.append(result)

        return processed

    async def infer_stream(
        self,
        contexts: list[ReasoningContext],
    ):
        """
        流式推理结果

        Yields:
            推理结果
        """
        if not self._started:
            await self.start()

        for context in contexts:
            result = await self.infer_async(context)
            yield result

    async def diagnose_async(
        self,
        error_message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> DiagnosticResult:
        """
        异步错误诊断

        Args:
            error_message: 错误信息
            context: 上下文

        Returns:
            诊断结果
        """
        if not self._started:
            await self.start()

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._sync_diagnose,
            error_message,
            context,
        )
        return result

    def _sync_diagnose(
        self,
        error_message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> DiagnosticResult:
        """同步诊断"""
        if self._causal_engine is None:
            raise RuntimeError("Causal engine not initialized")
        return self._causal_engine.diagnose_error(error_message, context)

    def submit_task(
        self,
        context: ReasoningContext,
        priority: TaskPriority = TaskPriority.NORMAL,
        callback: Optional[InferenceCallback] = None,
    ) -> str:
        """
        提交任务到队列

        Args:
            context: 推理上下文
            priority: 优先级
            callback: 回调

        Returns:
            任务 ID
        """
        return self._queue.submit(context, priority, callback)

    def get_task_result(self, task_id: str) -> Optional[EnhancedInferenceResult]:
        """获取任务结果"""
        return self._queue.get_result(task_id)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return self._queue.get_stats()


# 全局实例
_async_engine: Optional[AsyncInferenceEngine] = None


def get_async_inference_engine() -> AsyncInferenceEngine:
    """获取全局异步推理引擎"""
    global _async_engine
    if _async_engine is None:
        _async_engine = AsyncInferenceEngine()
    return _async_engine