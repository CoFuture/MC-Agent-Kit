"""
增强的 LLM 客户端工厂

整合所有 LLM 提供者，提供统一的创建接口。
"""

from __future__ import annotations

import threading
from enum import Enum
from typing import Any

from mc_agent_kit.skills.llm_integration import (
    BaseLLMClient,
    LLMConfig,
    LLMProvider,
    MockLLMClient,
    OpenAIClient,
    AzureOpenAIClient,
    OllamaClient,
    LMStudioClient,
)
from mc_agent_kit.skills.llm_providers.anthropic_client import AnthropicClient
from mc_agent_kit.skills.llm_providers.gemini_client import GeminiClient


class EnhancedLLMProvider(Enum):
    """增强的 LLM 提供者枚举"""
    OPENAI = "openai"
    AZURE = "azure"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    MOCK = "mock"


class EnhancedLLMClientFactory:
    """增强的 LLM 客户端工厂
    
    支持所有主流 LLM 提供者：
    - OpenAI (GPT-4, GPT-3.5)
    - Azure OpenAI
    - Anthropic (Claude 3)
    - Google (Gemini)
    - Ollama (本地)
    - LM Studio (本地)
    - Mock (测试)
    
    使用示例:
        config = LLMConfig(
            provider=EnhancedLLMProvider.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            api_key="your-api-key",
        )
        client = EnhancedLLMClientFactory.create(config)
    """
    
    _clients: dict[str, BaseLLMClient] = {}
    _lock = threading.Lock()
    
    @classmethod
    def create(cls, config: LLMConfig) -> BaseLLMClient:
        """创建 LLM 客户端
        
        Args:
            config: LLM 配置
        
        Returns:
            BaseLLMClient: LLM 客户端实例
        
        Raises:
            ValueError: 不支持的提供者
            ImportError: 缺少必要的依赖
        """
        # 确定提供者类型
        provider_value = config.provider
        if isinstance(provider_value, str):
            provider_value = provider_value.lower()
        elif isinstance(provider_value, Enum):
            provider_value = provider_value.value.lower()
        
        cache_key = f"{provider_value}:{config.model}"
        
        with cls._lock:
            if cache_key in cls._clients:
                return cls._clients[cache_key]
            
            client = cls._create_client(config, provider_value)
            cls._clients[cache_key] = client
            return client
    
    @classmethod
    def _create_client(cls, config: LLMConfig, provider: str) -> BaseLLMClient:
        """创建客户端实例"""
        if provider in ("openai", "open_ai"):
            return OpenAIClient(config)
        elif provider in ("azure", "azure_openai", "azure-openai"):
            return AzureOpenAIClient(config)
        elif provider in ("anthropic", "claude"):
            return AnthropicClient(config)
        elif provider in ("gemini", "google", "google_gemini"):
            return GeminiClient(config)
        elif provider == "ollama":
            return OllamaClient(config)
        elif provider in ("lm_studio", "lmstudio"):
            return LMStudioClient(config)
        else:
            return MockLLMClient(config)
    
    @classmethod
    def clear(cls) -> None:
        """清空客户端缓存"""
        with cls._lock:
            cls._clients.clear()
    
    @classmethod
    def list_supported_providers(cls) -> list[str]:
        """列出所有支持的提供者"""
        return [
            "openai",
            "azure",
            "anthropic",
            "gemini",
            "ollama",
            "lm_studio",
            "mock",
        ]
    
    @classmethod
    def get_provider_info(cls, provider: str) -> dict[str, Any]:
        """获取提供者信息"""
        info = {
            "openai": {
                "name": "OpenAI",
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "requires_api_key": True,
                "supports_streaming": True,
            },
            "azure": {
                "name": "Azure OpenAI",
                "models": ["gpt-4", "gpt-35-turbo"],
                "requires_api_key": True,
                "requires_endpoint": True,
                "supports_streaming": True,
            },
            "anthropic": {
                "name": "Anthropic",
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-3-5-sonnet"],
                "requires_api_key": True,
                "supports_streaming": True,
            },
            "gemini": {
                "name": "Google Gemini",
                "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
                "requires_api_key": True,
                "supports_streaming": True,
            },
            "ollama": {
                "name": "Ollama",
                "models": ["llama3", "mistral", "mixtral", "custom"],
                "requires_api_key": False,
                "local": True,
                "supports_streaming": True,
            },
            "lm_studio": {
                "name": "LM Studio",
                "models": ["custom"],
                "requires_api_key": False,
                "local": True,
                "supports_streaming": True,
            },
            "mock": {
                "name": "Mock",
                "models": ["mock-model"],
                "requires_api_key": False,
                "for_testing": True,
                "supports_streaming": True,
            },
        }
        return info.get(provider, {
            "name": provider,
            "models": [],
            "requires_api_key": False,
            "supports_streaming": False,
        })


# 便捷函数
def create_llm_client(
    provider: str,
    model: str,
    api_key: str | None = None,
    **kwargs: Any,
) -> BaseLLMClient:
    """创建 LLM 客户端的便捷函数
    
    Args:
        provider: 提供者名称
        model: 模型名称
        api_key: API 密钥（可选）
        **kwargs: 其他配置参数
    
    Returns:
        BaseLLMClient: LLM 客户端实例
    """
    config = LLMConfig(
        provider=provider,  # type: ignore
        model=model,
        api_key=api_key,
        **kwargs,
    )
    return EnhancedLLMClientFactory.create(config)


def get_recommended_model(provider: str, task_type: str = "general") -> str:
    """获取推荐的模型
    
    Args:
        provider: 提供者名称
        task_type: 任务类型 (code_gen, analysis, creative, simple, general)
    
    Returns:
        推荐的模型名称
    """
    recommendations = {
        "openai": {
            "code_gen": "gpt-4-turbo",
            "analysis": "gpt-4",
            "creative": "gpt-4",
            "simple": "gpt-3.5-turbo",
            "general": "gpt-4-turbo",
        },
        "anthropic": {
            "code_gen": "claude-3-5-sonnet-20241022",
            "analysis": "claude-3-5-sonnet-20241022",
            "creative": "claude-3-opus-20240229",
            "simple": "claude-3-5-haiku-20241022",
            "general": "claude-3-5-sonnet-20241022",
        },
        "gemini": {
            "code_gen": "gemini-1.5-pro",
            "analysis": "gemini-1.5-pro",
            "creative": "gemini-1.5-pro",
            "simple": "gemini-1.5-flash",
            "general": "gemini-1.5-pro",
        },
    }
    
    provider_models = recommendations.get(provider.lower(), {})
    return provider_models.get(task_type, provider_models.get("general", "default"))