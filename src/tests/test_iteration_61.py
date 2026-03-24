"""
迭代 #61 测试 - AI 能力增强与智能代码生成

测试新增的 LLM 提供者（Anthropic Claude、Google Gemini）和增强的工厂类。
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock

from mc_agent_kit.skills.llm_integration import (
    LLMConfig,
    ChatMessage,
    MessageRole,
    TokenUsage,
    LLMResponse,
)
from mc_agent_kit.skills.llm_providers.anthropic_client import (
    AnthropicClient,
    AnthropicConfig,
    AnthropicUsage,
    ClaudeModelSelector,
)
from mc_agent_kit.skills.llm_providers.gemini_client import (
    GeminiClient,
    GeminiConfig,
    GeminiUsage,
    GeminiModelSelector,
)
from mc_agent_kit.skills.llm_providers.enhanced_factory import (
    EnhancedLLMClientFactory,
    EnhancedLLMProvider,
    create_llm_client,
    get_recommended_model,
)


class TestAnthropicConfig:
    """测试 Anthropic 配置"""
    
    def test_default_config(self) -> None:
        """测试默认配置"""
        config = AnthropicConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.model == "claude-3-sonnet-20240229"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.timeout == 120.0
    
    def test_pricing(self) -> None:
        """测试定价配置"""
        config = AnthropicConfig(api_key="test-key")
        assert "claude-3-opus-20240229" in config.pricing
        assert "claude-3-sonnet-20240229" in config.pricing
        assert "claude-3-haiku-20240307" in config.pricing


class TestClaudeModelSelector:
    """测试 Claude 模型选择器"""
    
    def test_select_model_code_gen_quality(self) -> None:
        """测试代码生成 - 质量优先"""
        model = ClaudeModelSelector.select_model("code_gen", "quality")
        assert model == "claude-3-opus-20240229"
    
    def test_select_model_code_gen_speed(self) -> None:
        """测试代码生成 - 速度优先"""
        model = ClaudeModelSelector.select_model("code_gen", "speed")
        assert model == "claude-3-5-haiku-20241022"
    
    def test_select_model_code_gen_balanced(self) -> None:
        """测试代码生成 - 平衡"""
        model = ClaudeModelSelector.select_model("code_gen", "balanced")
        assert model == "claude-3-5-sonnet-20241022"
    
    def test_select_model_analysis(self) -> None:
        """测试分析任务"""
        model = ClaudeModelSelector.select_model("analysis", "quality")
        assert model == "claude-3-opus-20240229"
    
    def test_select_model_creative(self) -> None:
        """测试创意任务"""
        model = ClaudeModelSelector.select_model("creative", "quality")
        assert model == "claude-3-opus-20240229"
    
    def test_select_model_simple(self) -> None:
        """测试简单任务"""
        model = ClaudeModelSelector.select_model("simple")
        assert model == "claude-3-5-haiku-20241022"
    
    def test_get_model_info(self) -> None:
        """测试获取模型信息"""
        info = ClaudeModelSelector.get_model_info("claude-3-opus-20240229")
        assert info["reasoning"] == 5
        assert info["creativity"] == 5
        assert info["speed"] == 2


class TestGeminiConfig:
    """测试 Gemini 配置"""
    
    def test_default_config(self) -> None:
        """测试默认配置"""
        config = GeminiConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.model == "gemini-1.5-pro"
        assert config.max_tokens == 8192
        assert config.temperature == 0.7
    
    def test_safety_settings(self) -> None:
        """测试安全设置"""
        config = GeminiConfig(api_key="test-key")
        assert len(config.safety_settings) == 4
        assert any(s["category"] == "HARM_CATEGORY_HARASSMENT" for s in config.safety_settings)
    
    def test_pricing(self) -> None:
        """测试定价配置"""
        config = GeminiConfig(api_key="test-key")
        assert "gemini-1.5-pro" in config.pricing
        assert "gemini-1.5-flash" in config.pricing
        assert "gemini-1.0-pro" in config.pricing


class TestGeminiModelSelector:
    """测试 Gemini 模型选择器"""
    
    def test_select_model_code_gen_quality(self) -> None:
        """测试代码生成 - 质量优先"""
        model = GeminiModelSelector.select_model("code_gen", "quality")
        assert model == "gemini-1.5-pro"
    
    def test_select_model_code_gen_speed(self) -> None:
        """测试代码生成 - 速度优先"""
        model = GeminiModelSelector.select_model("code_gen", "speed")
        assert model == "gemini-1.5-flash"
    
    def test_select_model_analysis(self) -> None:
        """测试分析任务"""
        model = GeminiModelSelector.select_model("analysis", "balanced")
        assert model == "gemini-1.5-pro"
    
    def test_select_model_simple(self) -> None:
        """测试简单任务"""
        model = GeminiModelSelector.select_model("simple")
        assert model == "gemini-1.5-flash"
    
    def test_get_model_info(self) -> None:
        """测试获取模型信息"""
        info = GeminiModelSelector.get_model_info("gemini-1.5-pro")
        assert info["reasoning"] == 5
        assert info["creativity"] == 4
        assert info["speed"] == 4
        assert info["context_length"] == 1000000


class TestEnhancedLLMClientFactory:
    """测试增强的 LLM 客户端工厂"""
    
    def test_list_supported_providers(self) -> None:
        """测试列出支持的提供者"""
        providers = EnhancedLLMClientFactory.list_supported_providers()
        assert "openai" in providers
        assert "anthropic" in providers
        assert "gemini" in providers
        assert "ollama" in providers
        assert "lm_studio" in providers
        assert "mock" in providers
    
    def test_get_provider_info_openai(self) -> None:
        """测试获取 OpenAI 提供者信息"""
        info = EnhancedLLMClientFactory.get_provider_info("openai")
        assert info["name"] == "OpenAI"
        assert info["requires_api_key"] is True
        assert info["supports_streaming"] is True
    
    def test_get_provider_info_anthropic(self) -> None:
        """测试获取 Anthropic 提供者信息"""
        info = EnhancedLLMClientFactory.get_provider_info("anthropic")
        assert info["name"] == "Anthropic"
        assert "claude-3-opus" in info["models"]
        assert info["requires_api_key"] is True
    
    def test_get_provider_info_gemini(self) -> None:
        """测试获取 Gemini 提供者信息"""
        info = EnhancedLLMClientFactory.get_provider_info("gemini")
        assert info["name"] == "Google Gemini"
        assert "gemini-1.5-pro" in info["models"]
        assert info["requires_api_key"] is True
    
    def test_get_provider_info_ollama(self) -> None:
        """测试获取 Ollama 提供者信息"""
        info = EnhancedLLMClientFactory.get_provider_info("ollama")
        assert info["name"] == "Ollama"
        assert info["requires_api_key"] is False
        assert info["local"] is True
    
    def test_get_provider_info_unknown(self) -> None:
        """测试获取未知提供者信息"""
        info = EnhancedLLMClientFactory.get_provider_info("unknown")
        assert info["name"] == "unknown"
        assert info["models"] == []


class TestCreateLLMClient:
    """测试创建 LLM 客户端便捷函数"""
    
    @patch('mc_agent_kit.skills.llm_providers.enhanced_factory.EnhancedLLMClientFactory.create')
    def test_create_llm_client_mock(self, mock_create: Mock) -> None:
        """测试创建 Mock 客户端"""
        mock_client = Mock()
        mock_create.return_value = mock_client
        
        client = create_llm_client("mock", "mock-model")
        
        assert client is mock_client
        mock_create.assert_called_once()
    
    @patch('mc_agent_kit.skills.llm_providers.enhanced_factory.EnhancedLLMClientFactory.create')
    def test_create_llm_client_anthropic(self, mock_create: Mock) -> None:
        """测试创建 Anthropic 客户端"""
        mock_client = Mock()
        mock_create.return_value = mock_client
        
        client = create_llm_client("anthropic", "claude-3-5-sonnet-20241022", api_key="test")
        
        assert client is mock_client
        mock_create.assert_called_once()


class TestGetRecommendedModel:
    """测试获取推荐模型函数"""
    
    def test_openai_code_gen(self) -> None:
        """测试 OpenAI 代码生成推荐"""
        model = get_recommended_model("openai", "code_gen")
        assert model == "gpt-4-turbo"
    
    def test_openai_simple(self) -> None:
        """测试 OpenAI 简单任务推荐"""
        model = get_recommended_model("openai", "simple")
        assert model == "gpt-3.5-turbo"
    
    def test_anthropic_code_gen(self) -> None:
        """测试 Anthropic 代码生成推荐"""
        model = get_recommended_model("anthropic", "code_gen")
        assert model == "claude-3-5-sonnet-20241022"
    
    def test_gemini_code_gen(self) -> None:
        """测试 Gemini 代码生成推荐"""
        model = get_recommended_model("gemini", "code_gen")
        assert model == "gemini-1.5-pro"
    
    def test_gemini_simple(self) -> None:
        """测试 Gemini 简单任务推荐"""
        model = get_recommended_model("gemini", "simple")
        assert model == "gemini-1.5-flash"
    
    def test_unknown_provider(self) -> None:
        """测试未知提供者"""
        model = get_recommended_model("unknown", "code_gen")
        assert model == "default"


class TestAnthropicClient:
    """测试 Anthropic 客户端"""
    
    def test_init(self) -> None:
        """测试初始化"""
        config = LLMConfig(
            provider="anthropic",  # type: ignore
            model="claude-3-5-sonnet-20241022",
            api_key="test-key",
        )
        client = AnthropicClient(config)
        
        assert client._anthropic_config.api_key == "test-key"
        assert client._anthropic_config.model == "claude-3-5-sonnet-20241022"
    
    def test_convert_messages_with_system(self) -> None:
        """测试消息转换（含系统提示）"""
        config = LLMConfig(
            provider="anthropic",  # type: ignore
            model="claude-3-5-sonnet-20241022",
            api_key="test-key",
        )
        client = AnthropicClient(config)
        
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content="You are helpful"),
            ChatMessage(role=MessageRole.USER, content="Hello"),
        ]
        
        system_prompt, converted = client._convert_messages(messages)
        
        assert system_prompt == "You are helpful"
        assert len(converted) == 1
        assert converted[0]["role"] == "user"
        assert converted[0]["content"] == "Hello"
    
    def test_convert_messages_without_system(self) -> None:
        """测试消息转换（无系统提示）"""
        config = LLMConfig(
            provider="anthropic",  # type: ignore
            model="claude-3-5-sonnet-20241022",
            api_key="test-key",
        )
        client = AnthropicClient(config)
        
        messages = [
            ChatMessage(role=MessageRole.USER, content="Hello"),
            ChatMessage(role=MessageRole.ASSISTANT, content="Hi there"),
        ]
        
        system_prompt, converted = client._convert_messages(messages)
        
        assert system_prompt is None
        assert len(converted) == 2


class TestGeminiClient:
    """测试 Gemini 客户端"""
    
    def test_init(self) -> None:
        """测试初始化"""
        config = LLMConfig(
            provider="gemini",  # type: ignore
            model="gemini-1.5-pro",
            api_key="test-key",
        )
        client = GeminiClient(config)
        
        assert client._gemini_config.api_key == "test-key"
        assert client._gemini_config.model == "gemini-1.5-pro"
    
    def test_convert_messages_with_system(self) -> None:
        """测试消息转换（含系统提示）"""
        config = LLMConfig(
            provider="gemini",  # type: ignore
            model="gemini-1.5-pro",
            api_key="test-key",
        )
        client = GeminiClient(config)
        
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content="You are helpful"),
            ChatMessage(role=MessageRole.USER, content="Hello"),
        ]
        
        system_prompt, contents = client._convert_messages(messages)
        
        assert "You are helpful" in system_prompt
        assert len(contents) == 1
        assert contents[0]["role"] == "user"


class TestIteration61Integration:
    """迭代 #61 集成测试"""
    
    def test_all_providers_listed(self) -> None:
        """测试所有提供者已列出"""
        providers = EnhancedLLMClientFactory.list_supported_providers()
        
        expected = ["openai", "azure", "anthropic", "gemini", "ollama", "lm_studio", "mock"]
        for provider in expected:
            assert provider in providers, f"Missing provider: {provider}"
    
    def test_model_selector_claude(self) -> None:
        """测试 Claude 模型选择器"""
        # 测试所有任务类型
        task_types = ["code_gen", "analysis", "creative", "simple"]
        priorities = ["quality", "speed", "balanced"]
        
        for task_type in task_types:
            for priority in priorities:
                model = ClaudeModelSelector.select_model(task_type, priority)
                assert isinstance(model, str)
                assert len(model) > 0
    
    def test_model_selector_gemini(self) -> None:
        """测试 Gemini 模型选择器"""
        task_types = ["code_gen", "analysis", "creative", "simple"]
        priorities = ["quality", "speed", "balanced"]
        
        for task_type in task_types:
            for priority in priorities:
                model = GeminiModelSelector.select_model(task_type, priority)
                assert isinstance(model, str)
                assert len(model) > 0


class TestIteration61AcceptanceCriteria:
    """迭代 #61 验收标准测试"""
    
    def test_anthropic_support(self) -> None:
        """验收标准：Anthropic Claude 支持"""
        # 测试配置
        config = AnthropicConfig(api_key="test")
        assert config.api_key == "test"
        
        # 测试模型选择器
        model = ClaudeModelSelector.select_model("code_gen")
        assert "claude" in model.lower() or "sonnet" in model.lower() or "opus" in model.lower()
        
        # 测试提供者信息
        info = EnhancedLLMClientFactory.get_provider_info("anthropic")
        assert info["name"] == "Anthropic"
    
    def test_gemini_support(self) -> None:
        """验收标准：Google Gemini 支持"""
        # 测试配置
        config = GeminiConfig(api_key="test")
        assert config.api_key == "test"
        
        # 测试模型选择器
        model = GeminiModelSelector.select_model("code_gen")
        assert "gemini" in model.lower()
        
        # 测试提供者信息
        info = EnhancedLLMClientFactory.get_provider_info("gemini")
        assert info["name"] == "Google Gemini"
    
    def test_enhanced_factory(self) -> None:
        """验收标准：增强的工厂类"""
        # 测试支持的提供者数量
        providers = EnhancedLLMClientFactory.list_supported_providers()
        assert len(providers) >= 7  # openai, azure, anthropic, gemini, ollama, lm_studio, mock
        
        # 测试便捷函数
        model = get_recommended_model("anthropic", "code_gen")
        assert isinstance(model, str)
    
    def test_model_recommendations(self) -> None:
        """验收标准：模型推荐功能"""
        # 测试不同提供者的推荐
        assert get_recommended_model("openai", "code_gen") == "gpt-4-turbo"
        assert get_recommended_model("anthropic", "code_gen") == "claude-3-5-sonnet-20241022"
        assert get_recommended_model("gemini", "code_gen") == "gemini-1.5-pro"


class TestIteration61Performance:
    """迭代 #61 性能测试"""
    
    def test_factory_creation_performance(self) -> None:
        """测试工厂创建性能"""
        import time
        
        start = time.time()
        for _ in range(100):
            config = LLMConfig(
                provider="mock",  # type: ignore
                model="mock-model",
            )
            # 不实际创建，只测试配置
        elapsed = time.time() - start
        
        # 100 次配置创建应小于 0.1 秒
        assert elapsed < 0.1, f"Factory creation too slow: {elapsed}s"
    
    def test_model_selector_performance(self) -> None:
        """测试模型选择器性能"""
        import time
        
        start = time.time()
        for _ in range(1000):
            ClaudeModelSelector.select_model("code_gen", "balanced")
            GeminiModelSelector.select_model("code_gen", "balanced")
        elapsed = time.time() - start
        
        # 1000 次选择应小于 0.1 秒
        assert elapsed < 0.1, f"Model selector too slow: {elapsed}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])