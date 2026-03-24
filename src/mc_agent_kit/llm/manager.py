"""
LLM 管理器

提供统一的 LLM 管理和调用接口。
"""

from __future__ import annotations

import threading
from typing import Any

from .base import (
    ChatMessage,
    CompletionResult,
    LLMConfig,
    LLMProvider,
    StreamChunk,
)
from .providers import (
    AnthropicProvider,
    GeminiProvider,
    MockProvider,
    OllamaProvider,
    OpenAIProvider,
)


class LLMManager:
    """
    LLM 管理器

    管理多个 LLM 提供商，提供统一的调用接口。
    """

    _instance: LLMManager | None = None
    _lock = threading.Lock()

    def __new__(cls) -> LLMManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._providers: dict[str, type[LLMProvider]] = {
            "mock": MockProvider,
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "gemini": GeminiProvider,
            "ollama": OllamaProvider,
        }
        self._instances: dict[str, LLMProvider] = {}
        self._default_provider: str = "mock"
        self._initialized = True

    def register_provider(self, name: str, provider_class: type[LLMProvider]) -> None:
        """
        注册提供商

        Args:
            name: 提供商名称
            provider_class: 提供商类
        """
        self._providers[name] = provider_class

    def get_provider(
        self,
        config: LLMConfig | None = None,
        name: str | None = None,
    ) -> LLMProvider:
        """
        获取提供商实例

        Args:
            config: LLM 配置
            name: 提供商名称（优先使用）

        Returns:
            LLMProvider: 提供商实例
        """
        provider_name = name or (config.provider if config else self._default_provider)
        cache_key = provider_name

        if config:
            cache_key = f"{provider_name}:{config.model}:{config.api_key or 'no-key'}"

        if cache_key not in self._instances:
            provider_class = self._providers.get(provider_name)
            if not provider_class:
                raise ValueError(f"Unknown provider: {provider_name}")

            if config:
                instance = provider_class(config)
            else:
                instance = provider_class(LLMConfig(provider=provider_name))

            instance.initialize()
            self._instances[cache_key] = instance

        return self._instances[cache_key]

    def set_default_provider(self, name: str) -> None:
        """
        设置默认提供商

        Args:
            name: 提供商名称
        """
        if name not in self._providers:
            raise ValueError(f"Unknown provider: {name}")
        self._default_provider = name

    def list_providers(self) -> list[str]:
        """
        列出所有提供商

        Returns:
            list[str]: 提供商名称列表
        """
        return list(self._providers.keys())

    def list_models(self, provider: str | None = None) -> dict[str, list[str]]:
        """
        列出支持的模型

        Args:
            provider: 提供商名称（可选）

        Returns:
            dict[str, list[str]]: 提供商 -> 模型列表
        """
        if provider:
            provider_instance = self.get_provider(name=provider)
            return {provider: provider_instance.models}

        result = {}
        for name in self._providers:
            try:
                instance = self.get_provider(name=name)
                result[name] = instance.models
            except Exception:
                result[name] = []
        return result

    def complete(
        self,
        messages: list[ChatMessage],
        config: LLMConfig | None = None,
        **kwargs: Any,
    ) -> CompletionResult:
        """
        同步补全

        Args:
            messages: 消息列表
            config: LLM 配置
            **kwargs: 额外参数

        Returns:
            CompletionResult: 补全结果
        """
        provider = self.get_provider(config)
        return provider.complete(messages, **kwargs)

    async def complete_async(
        self,
        messages: list[ChatMessage],
        config: LLMConfig | None = None,
        **kwargs: Any,
    ) -> CompletionResult:
        """
        异步补全

        Args:
            messages: 消息列表
            config: LLM 配置
            **kwargs: 额外参数

        Returns:
            CompletionResult: 补全结果
        """
        provider = self.get_provider(config)
        return await provider.complete_async(messages, **kwargs)

    def stream(
        self,
        messages: list[ChatMessage],
        config: LLMConfig | None = None,
        **kwargs: Any,
    ):
        """
        流式补全

        Args:
            messages: 消息列表
            config: LLM 配置
            **kwargs: 额外参数

        Yields:
            StreamChunk: 流式响应块
        """
        provider = self.get_provider(config)
        yield from provider.stream(messages, **kwargs)

    def count_tokens(
        self,
        text: str,
        config: LLMConfig | None = None,
    ) -> int:
        """
        计算 token 数量

        Args:
            text: 文本内容
            config: LLM 配置

        Returns:
            int: token 数量
        """
        provider = self.get_provider(config)
        return provider.count_tokens(text)

    def shutdown(self) -> None:
        """关闭所有提供商"""
        for instance in self._instances.values():
            try:
                instance.shutdown()
            except Exception:
                pass
        self._instances.clear()


def get_llm_manager() -> LLMManager:
    """获取 LLM 管理器单例"""
    return LLMManager()