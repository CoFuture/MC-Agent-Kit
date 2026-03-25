"""
流式输出增强模块

提供流式输出性能优化、断点续传和错误处理。
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Generator, Generic, Iterator, TypeVar

T = TypeVar("T")


class StreamState(Enum):
    """流式输出状态"""
    PENDING = "pending"
    STREAMING = "streaming"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StreamErrorType(Enum):
    """流式错误类型"""
    NETWORK = "network"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    AUTH = "auth"
    CONTENT_FILTER = "content_filter"
    UNKNOWN = "unknown"


@dataclass
class StreamError:
    """流式错误"""
    error_type: StreamErrorType
    message: str
    retryable: bool = False
    retry_after: float | None = None
    raw_error: Exception | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "retryable": self.retryable,
            "retry_after": self.retry_after,
        }


@dataclass
class StreamCheckpoint:
    """流式检查点"""
    id: str
    position: int
    timestamp: float
    data: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "position": self.position,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StreamCheckpoint:
        return cls(
            id=data["id"],
            position=data["position"],
            timestamp=data["timestamp"],
            data=data.get("data", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class StreamProgress:
    """流式进度"""
    total_chunks: int = 0
    total_bytes: int = 0
    total_tokens: int = 0
    elapsed_time: float = 0.0
    chunks_per_second: float = 0.0
    bytes_per_second: float = 0.0

    @property
    def tokens_per_second(self) -> float:
        return self.total_tokens / self.elapsed_time if self.elapsed_time > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_chunks": self.total_chunks,
            "total_bytes": self.total_bytes,
            "total_tokens": self.total_tokens,
            "elapsed_time": self.elapsed_time,
            "chunks_per_second": self.chunks_per_second,
            "bytes_per_second": self.bytes_per_second,
            "tokens_per_second": self.tokens_per_second,
        }


@dataclass
class StreamResult(Generic[T]):
    """流式结果"""
    state: StreamState = StreamState.PENDING
    content: str = ""
    chunks: list[Any] = field(default_factory=list)
    error: StreamError | None = None
    checkpoint: StreamCheckpoint | None = None
    progress: StreamProgress = field(default_factory=StreamProgress)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.state == StreamState.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.state == StreamState.FAILED

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "content": self.content,
            "chunks": self.chunks,
            "error": self.error.to_dict() if self.error else None,
            "checkpoint": self.checkpoint.to_dict() if self.checkpoint else None,
            "progress": self.progress.to_dict(),
            "metadata": self.metadata,
        }


class StreamBuffer:
    """
    流式缓冲区

    管理流式数据的缓冲和合并。
    """

    def __init__(
        self,
        max_size: int = 1024 * 1024,  # 1MB
        chunk_size: int = 4096,
    ) -> None:
        self.max_size = max_size
        self.chunk_size = chunk_size
        self._buffer: list[str] = []
        self._size = 0
        self._lock = threading.Lock()

    def append(self, data: str) -> bool:
        """
        追加数据到缓冲区

        Args:
            data: 数据字符串

        Returns:
            bool: 是否成功（缓冲区未满）
        """
        with self._lock:
            if self._size + len(data) > self.max_size:
                return False

            self._buffer.append(data)
            self._size += len(data)
            return True

    def get_content(self) -> str:
        """获取完整内容"""
        with self._lock:
            return "".join(self._buffer)

    def get_chunks(self) -> list[str]:
        """获取所有块"""
        with self._lock:
            return list(self._buffer)

    def clear(self) -> None:
        """清空缓冲区"""
        with self._lock:
            self._buffer.clear()
            self._size = 0

    @property
    def size(self) -> int:
        """缓冲区大小"""
        return self._size

    @property
    def is_full(self) -> bool:
        """缓冲区是否已满"""
        return self._size >= self.max_size


class StreamErrorHandler:
    """
    流式错误处理器

    处理流式输出中的各种错误。
    """

    # 错误类型识别模式
    ERROR_PATTERNS: dict[StreamErrorType, list[str]] = {
        StreamErrorType.NETWORK: [
            "connection reset",
            "connection refused",
            "network unreachable",
            "ECONNRESET",
            "ECONNREFUSED",
        ],
        StreamErrorType.TIMEOUT: [
            "timeout",
            "timed out",
            "deadline exceeded",
        ],
        StreamErrorType.RATE_LIMIT: [
            "rate limit",
            "too many requests",
            "429",
            "quota exceeded",
        ],
        StreamErrorType.AUTH: [
            "unauthorized",
            "invalid api key",
            "authentication failed",
            "401",
            "403",
        ],
        StreamErrorType.CONTENT_FILTER: [
            "content filter",
            "content policy",
            "safety",
            "harmful content",
        ],
    }

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._retry_counts: dict[str, int] = {}

    def classify_error(self, error: Exception) -> StreamError:
        """
        分类错误

        Args:
            error: 原始异常

        Returns:
            StreamError: 分类后的错误
        """
        error_str = str(error).lower()

        for error_type, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in error_str:
                    return StreamError(
                        error_type=error_type,
                        message=str(error),
                        retryable=self._is_retryable(error_type),
                        retry_after=self._get_retry_after(error, error_type),
                        raw_error=error,
                    )

        return StreamError(
            error_type=StreamErrorType.UNKNOWN,
            message=str(error),
            retryable=False,
            raw_error=error,
        )

    def _is_retryable(self, error_type: StreamErrorType) -> bool:
        """判断错误是否可重试"""
        retryable_types = {
            StreamErrorType.NETWORK,
            StreamErrorType.TIMEOUT,
            StreamErrorType.RATE_LIMIT,
        }
        return error_type in retryable_types

    def _get_retry_after(self, error: Exception, error_type: StreamErrorType) -> float | None:
        """获取重试等待时间"""
        if error_type == StreamErrorType.RATE_LIMIT:
            # 尝试从错误信息中提取 retry-after
            error_str = str(error)
            if "retry-after" in error_str.lower():
                try:
                    # 简单提取数字
                    import re
                    match = re.search(r"retry-after[:\s]+(\d+)", error_str, re.IGNORECASE)
                    if match:
                        return float(match.group(1))
                except (ValueError, AttributeError):
                    pass
            return self.base_delay * 2

        if error_type in (StreamErrorType.NETWORK, StreamErrorType.TIMEOUT):
            return self.base_delay

        return None

    def should_retry(self, stream_id: str, error: StreamError) -> bool:
        """
        判断是否应该重试

        Args:
            stream_id: 流 ID
            error: 流式错误

        Returns:
            bool: 是否应该重试
        """
        if not error.retryable:
            return False

        current_retries = self._retry_counts.get(stream_id, 0)
        return current_retries < self.max_retries

    def record_retry(self, stream_id: str) -> None:
        """记录重试"""
        self._retry_counts[stream_id] = self._retry_counts.get(stream_id, 0) + 1

    def reset_retries(self, stream_id: str) -> None:
        """重置重试计数"""
        self._retry_counts.pop(stream_id, None)

    def get_retry_delay(self, stream_id: str, error: StreamError) -> float:
        """
        获取重试延迟

        Args:
            stream_id: 流 ID
            error: 流式错误

        Returns:
            float: 重试延迟（秒）
        """
        if error.retry_after:
            return error.retry_after

        current_retries = self._retry_counts.get(stream_id, 0)
        # 指数退避
        return self.base_delay * (2 ** current_retries)


class StreamCheckpointManager:
    """
    流式检查点管理器

    管理流式输出的检查点，支持断点续传。
    """

    def __init__(self, checkpoint_dir: str | None = None) -> None:
        self.checkpoint_dir = checkpoint_dir or os.path.join(os.getcwd(), ".stream_checkpoints")
        self._checkpoints: dict[str, StreamCheckpoint] = {}
        self._lock = threading.Lock()

        # 确保目录存在
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def create_checkpoint(
        self,
        stream_id: str,
        position: int,
        data: str,
        metadata: dict[str, Any] | None = None,
    ) -> StreamCheckpoint:
        """
        创建检查点

        Args:
            stream_id: 流 ID
            position: 位置
            data: 数据
            metadata: 元数据

        Returns:
            StreamCheckpoint: 检查点
        """
        checkpoint = StreamCheckpoint(
            id=stream_id,
            position=position,
            timestamp=time.time(),
            data=data,
            metadata=metadata or {},
        )

        with self._lock:
            self._checkpoints[stream_id] = checkpoint

        return checkpoint

    def get_checkpoint(self, stream_id: str) -> StreamCheckpoint | None:
        """获取检查点"""
        with self._lock:
            return self._checkpoints.get(stream_id)

    def load_checkpoint(self, stream_id: str) -> StreamCheckpoint | None:
        """从文件加载检查点"""
        checkpoint_path = os.path.join(self.checkpoint_dir, f"{stream_id}.json")

        if not os.path.exists(checkpoint_path):
            return None

        try:
            with open(checkpoint_path, encoding="utf-8") as f:
                data = json.load(f)

            checkpoint = StreamCheckpoint.from_dict(data)
            with self._lock:
                self._checkpoints[stream_id] = checkpoint

            return checkpoint
        except (json.JSONDecodeError, IOError):
            return None

    def save_checkpoint(self, stream_id: str) -> bool:
        """保存检查点到文件"""
        with self._lock:
            checkpoint = self._checkpoints.get(stream_id)

        if not checkpoint:
            return False

        checkpoint_path = os.path.join(self.checkpoint_dir, f"{stream_id}.json")

        try:
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(checkpoint.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except IOError:
            return False

    def delete_checkpoint(self, stream_id: str) -> None:
        """删除检查点"""
        with self._lock:
            self._checkpoints.pop(stream_id, None)

        checkpoint_path = os.path.join(self.checkpoint_dir, f"{stream_id}.json")
        if os.path.exists(checkpoint_path):
            try:
                os.remove(checkpoint_path)
            except OSError:
                pass

    def list_checkpoints(self) -> list[str]:
        """列出所有检查点 ID"""
        with self._lock:
            return list(self._checkpoints.keys())


class StreamManager:
    """
    流式输出管理器

    提供流式输出的完整管理，包括缓冲、检查点、错误处理。
    """

    def __init__(
        self,
        buffer_size: int = 1024 * 1024,
        checkpoint_dir: str | None = None,
        max_retries: int = 3,
    ) -> None:
        self.buffer = StreamBuffer(max_size=buffer_size)
        self.checkpoint_manager = StreamCheckpointManager(checkpoint_dir)
        self.error_handler = StreamErrorHandler(max_retries=max_retries)
        self._active_streams: dict[str, StreamResult] = {}
        self._lock = threading.Lock()

    def create_stream(self, stream_id: str) -> StreamResult:
        """创建新流"""
        result = StreamResult(state=StreamState.PENDING)
        with self._lock:
            self._active_streams[stream_id] = result
        return result

    def process_stream(
        self,
        stream_id: str,
        stream_generator: Iterator[str],
        on_chunk: Callable[[str], None] | None = None,
        on_complete: Callable[[StreamResult], None] | None = None,
        on_error: Callable[[StreamError], None] | None = None,
        checkpoint_interval: int = 100,
    ) -> StreamResult:
        """
        处理流式输出

        Args:
            stream_id: 流 ID
            stream_generator: 流生成器
            on_chunk: 块回调
            on_complete: 完成回调
            on_error: 错误回调
            checkpoint_interval: 检查点间隔（块数）

        Returns:
            StreamResult: 流结果
        """
        result = self.create_stream(stream_id)
        result.state = StreamState.STREAMING
        start_time = time.time()
        chunk_count = 0

        try:
            for chunk in stream_generator:
                # 检查是否已取消
                if result.state == StreamState.CANCELLED:
                    break

                # 添加到缓冲区
                if not self.buffer.append(chunk):
                    result.state = StreamState.FAILED
                    result.error = StreamError(
                        error_type=StreamErrorType.UNKNOWN,
                        message="Buffer overflow",
                        retryable=True,
                    )
                    break

                result.content += chunk
                result.chunks.append(chunk)
                chunk_count += 1

                # 更新进度
                result.progress.total_chunks = chunk_count
                result.progress.total_bytes = len(result.content)
                result.progress.elapsed_time = time.time() - start_time
                result.progress.chunks_per_second = (
                    chunk_count / result.progress.elapsed_time
                    if result.progress.elapsed_time > 0 else 0
                )
                result.progress.bytes_per_second = (
                    result.progress.total_bytes / result.progress.elapsed_time
                    if result.progress.elapsed_time > 0 else 0
                )

                # 回调
                if on_chunk:
                    on_chunk(chunk)

                # 创建检查点
                if chunk_count % checkpoint_interval == 0:
                    self.checkpoint_manager.create_checkpoint(
                        stream_id=stream_id,
                        position=chunk_count,
                        data=result.content,
                    )

            # 完成
            if result.state not in (StreamState.FAILED, StreamState.CANCELLED):
                result.state = StreamState.COMPLETED
                self.checkpoint_manager.delete_checkpoint(stream_id)

        except Exception as e:
            result.state = StreamState.FAILED
            result.error = self.error_handler.classify_error(e)

            if on_error:
                on_error(result.error)

        # 回调
        if on_complete:
            on_complete(result)

        return result

    def resume_stream(
        self,
        stream_id: str,
        resume_generator_factory: Callable[[StreamCheckpoint], Iterator[str]],
        **kwargs: Any,
    ) -> StreamResult:
        """
        从检查点恢复流

        Args:
            stream_id: 流 ID
            resume_generator_factory: 恢复生成器工厂
            **kwargs: 其他参数

        Returns:
            StreamResult: 流结果
        """
        # 加载检查点
        checkpoint = self.checkpoint_manager.load_checkpoint(stream_id)

        if not checkpoint:
            raise ValueError(f"No checkpoint found for stream: {stream_id}")

        # 创建恢复生成器
        generator = resume_generator_factory(checkpoint)

        # 处理流
        return self.process_stream(stream_id, generator, **kwargs)

    def cancel_stream(self, stream_id: str) -> bool:
        """取消流"""
        with self._lock:
            result = self._active_streams.get(stream_id)
            if result and result.state == StreamState.STREAMING:
                result.state = StreamState.CANCELLED
                return True
        return False

    def get_stream_result(self, stream_id: str) -> StreamResult | None:
        """获取流结果"""
        with self._lock:
            return self._active_streams.get(stream_id)

    def pause_stream(self, stream_id: str) -> bool:
        """暂停流"""
        with self._lock:
            result = self._active_streams.get(stream_id)
            if result and result.state == StreamState.STREAMING:
                result.state = StreamState.PAUSED
                # 保存检查点
                self.checkpoint_manager.create_checkpoint(
                    stream_id=stream_id,
                    position=len(result.chunks),
                    data=result.content,
                )
                self.checkpoint_manager.save_checkpoint(stream_id)
                return True
        return False

    def resume_paused_stream(
        self,
        stream_id: str,
        resume_generator_factory: Callable[[StreamCheckpoint], Iterator[str]],
        **kwargs: Any,
    ) -> StreamResult:
        """恢复暂停的流"""
        with self._lock:
            result = self._active_streams.get(stream_id)
            if result and result.state == StreamState.PAUSED:
                result.state = StreamState.STREAMING

        return self.resume_stream(stream_id, resume_generator_factory, **kwargs)

    def get_active_streams(self) -> list[str]:
        """获取活跃流 ID"""
        with self._lock:
            return [
                stream_id
                for stream_id, result in self._active_streams.items()
                if result.state == StreamState.STREAMING
            ]

    def cleanup_completed_streams(self, max_age: float = 3600) -> int:
        """
        清理已完成的流

        Args:
            max_age: 最大保留时间（秒）

        Returns:
            int: 清理的流数量
        """
        current_time = time.time()
        cleaned = 0

        with self._lock:
            streams_to_remove = []

            for stream_id, result in self._active_streams.items():
                if result.state in (StreamState.COMPLETED, StreamState.FAILED, StreamState.CANCELLED):
                    if result.progress.elapsed_time > max_age:
                        streams_to_remove.append(stream_id)

            for stream_id in streams_to_remove:
                del self._active_streams[stream_id]
                self.checkpoint_manager.delete_checkpoint(stream_id)
                cleaned += 1

        return cleaned


class LargeFileStreamer:
    """
    大文件流式处理器

    优化大文件的流式处理。
    """

    def __init__(
        self,
        chunk_size: int = 8192,
        max_memory: int = 100 * 1024 * 1024,  # 100MB
    ) -> None:
        self.chunk_size = chunk_size
        self.max_memory = max_memory
        self._temp_files: list[str] = []

    def stream_file(
        self,
        file_path: str,
        encoding: str = "utf-8",
    ) -> Generator[str, None, None]:
        """
        流式读取文件

        Args:
            file_path: 文件路径
            encoding: 编码

        Yields:
            str: 文件块
        """
        with open(file_path, encoding=encoding) as f:
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                yield chunk

    def stream_large_text(
        self,
        text: str,
    ) -> Generator[str, None, None]:
        """
        流式处理大文本

        Args:
            text: 大文本

        Yields:
            str: 文本块
        """
        for i in range(0, len(text), self.chunk_size):
            yield text[i:i + self.chunk_size]

    def stream_with_overlap(
        self,
        text: str,
        overlap: int = 100,
    ) -> Generator[str, None, None]:
        """
        带重叠的流式处理（保持上下文连续性）

        Args:
            text: 文本
            overlap: 重叠字符数

        Yields:
            str: 文本块
        """
        if overlap >= self.chunk_size:
            overlap = self.chunk_size // 10

        position = 0
        while position < len(text):
            chunk = text[position:position + self.chunk_size]
            if not chunk:
                break
            yield chunk
            position += self.chunk_size - overlap

    def cleanup(self) -> None:
        """清理临时文件"""
        import os

        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except OSError:
                pass
        self._temp_files.clear()


# 便捷函数
_stream_manager: StreamManager | None = None


def get_stream_manager() -> StreamManager:
    """获取流管理器单例"""
    global _stream_manager
    if _stream_manager is None:
        _stream_manager = StreamManager()
    return _stream_manager


def process_stream(
    stream_id: str,
    stream_generator: Iterator[str],
    **kwargs: Any,
) -> StreamResult:
    """
    处理流式输出

    Args:
        stream_id: 流 ID
        stream_generator: 流生成器
        **kwargs: 其他参数

    Returns:
        StreamResult: 流结果
    """
    return get_stream_manager().process_stream(stream_id, stream_generator, **kwargs)