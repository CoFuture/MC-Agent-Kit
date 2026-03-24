"""
LLM 基础接口定义

定义 LLM 提供商的统一接口和数据结构。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Iterator


class ChatRole(Enum):
    """聊天消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class ChatMessage:
    """聊天消息"""
    role: ChatRole
    content: str
    name: str | None = None
    function_call: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"role": self.role.value, "content": self.content}
        if self.name:
            result["name"] = self.name
        if self.function_call:
            result["function_call"] = self.function_call
        return result

    @classmethod
    def system(cls, content: str) -> ChatMessage:
        """创建系统消息"""
        return cls(role=ChatRole.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> ChatMessage:
        """创建用户消息"""
        return cls(role=ChatRole.USER, content=content)

    @classmethod
    def assistant(cls, content: str) -> ChatMessage:
        """创建助手消息"""
        return cls(role=ChatRole.ASSISTANT, content=content)


@dataclass
class StreamChunk:
    """流式响应块"""
    content: str
    finished: bool = False
    token_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "finished": self.finished,
            "token_count": self.token_count,
        }


@dataclass
class CompletionResult:
    """补全结果"""
    content: str
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata,
        }


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "mock"
    model: str = "default"
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: float = 60.0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "api_key": "***" if self.api_key else None,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "extra": self.extra,
        }


class LLMProvider(ABC):
    """
    LLM 提供商基类

    所有 LLM 提供商必须实现此接口。
    """

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._initialized = False

    @property
    @abstractmethod
    def name(self) -> str:
        """提供商名称"""
        pass

    @property
    @abstractmethod
    def models(self) -> list[str]:
        """支持的模型列表"""
        pass

    @abstractmethod
    def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> CompletionResult:
        """
        同步补全

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            CompletionResult: 补全结果
        """
        pass

    @abstractmethod
    async def complete_async(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> CompletionResult:
        """
        异步补全

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            CompletionResult: 补全结果
        """
        pass

    def stream(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> Iterator[StreamChunk]:
        """
        流式补全

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Yields:
            StreamChunk: 流式响应块
        """
        # 默认实现：调用同步方法并一次性返回
        result = self.complete(messages, **kwargs)
        yield StreamChunk(content=result.content, finished=True)

    async def stream_async(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        异步流式补全

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Yields:
            StreamChunk: 流式响应块
        """
        # 默认实现：调用异步方法并一次性返回
        result = await self.complete_async(messages, **kwargs)
        yield StreamChunk(content=result.content, finished=True)

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        计算 token 数量

        Args:
            text: 文本内容

        Returns:
            int: token 数量
        """
        pass

    def validate_config(self) -> bool:
        """
        验证配置

        Returns:
            bool: 配置是否有效
        """
        return True

    def initialize(self) -> None:
        """初始化提供商"""
        self._initialized = True

    def shutdown(self) -> None:
        """关闭提供商"""
        self._initialized = False