"""
Anthropic Claude 客户端

支持 Claude 3 Opus、Sonnet、Haiku 等模型的调用。
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from mc_agent_kit.skills.llm_integration import (
    BaseLLMClient,
    ChatMessage,
    LLMConfig,
    LLMResponse,
    MessageRole,
    StreamChunk,
    TokenUsage,
)


@dataclass
class AnthropicConfig:
    """Anthropic 配置"""
    api_key: str
    model: str = "claude-3-sonnet-20240229"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: float = 120.0
    max_retries: int = 3
    retry_delay: float = 1.0
    base_url: str = "https://api.anthropic.com"
    
    # Claude 特定参数
    top_k: int = 40
    top_p: float | None = None
    
    # 系统提示
    system_prompt: str | None = None
    
    # 定价 (每 1K tokens, USD)
    pricing: dict[str, dict[str, float]] = field(default_factory=lambda: {
        "claude-3-opus-20240229": {"prompt": 0.015, "completion": 0.075},
        "claude-3-sonnet-20240229": {"prompt": 0.003, "completion": 0.015},
        "claude-3-haiku-20240307": {"prompt": 0.00025, "completion": 0.00125},
        "claude-3-5-sonnet-20241022": {"prompt": 0.003, "completion": 0.015},
        "claude-3-5-haiku-20241022": {"prompt": 0.001, "completion": 0.005},
        "default": {"prompt": 0.003, "completion": 0.015},
    })


@dataclass
class AnthropicUsage:
    """Anthropic 使用统计"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude 客户端
    
    支持的模型:
    - claude-3-opus-20240229 (最智能)
    - claude-3-sonnet-20240229 (平衡)
    - claude-3-haiku-20240307 (最快)
    - claude-3-5-sonnet-20241022 (最新 Sonnet)
    - claude-3-5-haiku-20241022 (最新 Haiku)
    
    使用示例:
        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-sonnet-20240229",
            api_key="your-api-key",
        )
        client = AnthropicClient(config)
        
        messages = [ChatMessage(role=MessageRole.USER, content="Hello")]
        response = client.complete(messages)
    """
    
    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._client: Any = None
        self._anthropic_config = AnthropicConfig(
            api_key=config.api_key or "",
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
        )
        self._total_usage = AnthropicUsage()
        self._lock = threading.Lock()
    
    def _get_client(self) -> Any:
        """获取 Anthropic 客户端"""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(
                    api_key=self._anthropic_config.api_key,
                    base_url=self._anthropic_config.base_url,
                    timeout=self._anthropic_config.timeout,
                )
            except ImportError:
                raise ImportError(
                    "请安装 anthropic: pip install anthropic"
                ) from None
        return self._client
    
    def _convert_messages(
        self,
        messages: list[ChatMessage],
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """转换消息格式
        
        Anthropic API 使用单独的 system 参数，而不是 system 消息。
        """
        system_prompt = None
        converted: list[dict[str, Any]] = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_prompt = msg.content
            else:
                role = "user" if msg.role == MessageRole.USER else "assistant"
                converted.append({
                    "role": role,
                    "content": msg.content,
                })
        
        return system_prompt, converted
    
    def _calculate_cost(self, model: str, usage: TokenUsage) -> float:
        """计算成本"""
        pricing = self._anthropic_config.pricing.get(
            model,
            self._anthropic_config.pricing["default"]
        )
        prompt_cost = (usage.prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (usage.completion_tokens / 1000) * pricing["completion"]
        return prompt_cost + completion_cost
    
    def _record_usage(self, model: str, usage: TokenUsage) -> float:
        """记录使用量"""
        cost = self._calculate_cost(model, usage)
        with self._lock:
            self._total_usage.input_tokens += usage.prompt_tokens
            self._total_usage.output_tokens += usage.completion_tokens
            self._total_usage.total_tokens += usage.total_tokens
            self._total_usage.cost += cost
        return cost
    
    def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """完成对话"""
        client = self._get_client()
        start_time = time.time()
        
        system_prompt, converted_messages = self._convert_messages(messages)
        
        # 合并配置和 kwargs
        model = kwargs.get("model", self._anthropic_config.model)
        max_tokens = kwargs.get("max_tokens", self._anthropic_config.max_tokens)
        temperature = kwargs.get("temperature", self._anthropic_config.temperature)
        top_k = kwargs.get("top_k", self._anthropic_config.top_k)
        
        for attempt in range(1, self._anthropic_config.max_retries + 1):
            try:
                params: dict[str, Any] = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": converted_messages,
                    "temperature": temperature,
                    "top_k": top_k,
                }
                
                if system_prompt:
                    params["system"] = system_prompt
                
                response = client.messages.create(**params)
                
                usage = TokenUsage(
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens,
                )
                
                cost = self._record_usage(model, usage)
                
                content = ""
                if response.content:
                    for block in response.content:
                        if hasattr(block, "text"):
                            content += block.text
                
                return LLMResponse(
                    content=content,
                    model=response.model,
                    usage=usage,
                    finish_reason=response.stop_reason or "end_turn",
                    cost=cost,
                    latency=time.time() - start_time,
                    metadata={
                        "id": response.id,
                        "type": response.type,
                    },
                )
            
            except Exception as e:
                if attempt >= self._anthropic_config.max_retries:
                    raise
                time.sleep(self._anthropic_config.retry_delay * attempt)
        
        raise RuntimeError("Max retries exceeded")
    
    async def complete_async(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """异步完成对话"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.complete(messages, **kwargs),
        )
    
    def stream(
        self,
        messages: list[ChatMessage],
        callback: Callable[[StreamChunk], None],
        **kwargs: Any,
    ) -> LLMResponse:
        """流式响应"""
        client = self._get_client()
        start_time = time.time()
        
        system_prompt, converted_messages = self._convert_messages(messages)
        
        model = kwargs.get("model", self._anthropic_config.model)
        max_tokens = kwargs.get("max_tokens", self._anthropic_config.max_tokens)
        temperature = kwargs.get("temperature", self._anthropic_config.temperature)
        
        content_parts: list[str] = []
        usage = TokenUsage()
        finish_reason = "end_turn"
        
        for attempt in range(1, self._anthropic_config.max_retries + 1):
            try:
                params: dict[str, Any] = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": converted_messages,
                    "temperature": temperature,
                    "stream": True,
                }
                
                if system_prompt:
                    params["system"] = system_prompt
                
                with client.messages.stream(**params) as stream:
                    for text in stream.text_stream:
                        content_parts.append(text)
                        callback(StreamChunk(
                            content="".join(content_parts),
                            delta=text,
                        ))
                    
                    # 获取最终响应
                    final_response = stream.get_final_message()
                    usage = TokenUsage(
                        prompt_tokens=final_response.usage.input_tokens,
                        completion_tokens=final_response.usage.output_tokens,
                        total_tokens=(
                            final_response.usage.input_tokens +
                            final_response.usage.output_tokens
                        ),
                    )
                    finish_reason = final_response.stop_reason or "end_turn"
                
                break
            
            except Exception as e:
                if attempt >= self._anthropic_config.max_retries:
                    raise
                time.sleep(self._anthropic_config.retry_delay * attempt)
        
        content = "".join(content_parts)
        cost = self._record_usage(model, usage)
        
        return LLMResponse(
            content=content,
            model=model,
            usage=usage,
            finish_reason=finish_reason,
            cost=cost,
            latency=time.time() - start_time,
        )
    
    def get_usage_stats(self) -> dict[str, Any]:
        """获取使用统计"""
        with self._lock:
            return {
                "input_tokens": self._total_usage.input_tokens,
                "output_tokens": self._total_usage.output_tokens,
                "total_tokens": self._total_usage.total_tokens,
                "total_cost": self._total_usage.cost,
            }


class ClaudeModelSelector:
    """Claude 模型选择器
    
    根据任务类型自动选择最合适的模型。
    """
    
    # 模型能力评级
    MODEL_CAPABILITIES = {
        "claude-3-opus-20240229": {
            "reasoning": 5,
            "creativity": 5,
            "speed": 2,
            "cost": 1,
        },
        "claude-3-5-sonnet-20241022": {
            "reasoning": 4,
            "creativity": 4,
            "speed": 4,
            "cost": 3,
        },
        "claude-3-sonnet-20240229": {
            "reasoning": 3,
            "creativity": 3,
            "speed": 3,
            "cost": 4,
        },
        "claude-3-5-haiku-20241022": {
            "reasoning": 3,
            "creativity": 2,
            "speed": 5,
            "cost": 5,
        },
        "claude-3-haiku-20240307": {
            "reasoning": 2,
            "creativity": 2,
            "speed": 5,
            "cost": 5,
        },
    }
    
    @classmethod
    def select_model(
        cls,
        task_type: str,
        priority: str = "balanced",
    ) -> str:
        """选择模型
        
        Args:
            task_type: 任务类型 (code_gen, analysis, creative, simple)
            priority: 优先级 (quality, speed, cost, balanced)
        
        Returns:
            推荐的模型名称
        """
        if task_type == "code_gen":
            # 代码生成需要较强的推理能力
            if priority == "quality":
                return "claude-3-opus-20240229"
            elif priority == "speed":
                return "claude-3-5-haiku-20241022"
            else:
                return "claude-3-5-sonnet-20241022"
        
        elif task_type == "analysis":
            # 分析任务需要推理能力
            if priority == "quality":
                return "claude-3-opus-20240229"
            else:
                return "claude-3-5-sonnet-20241022"
        
        elif task_type == "creative":
            # 创意任务
            if priority == "quality":
                return "claude-3-opus-20240229"
            else:
                return "claude-3-sonnet-20240229"
        
        else:  # simple
            # 简单任务用最快的模型
            return "claude-3-5-haiku-20241022"
    
    @classmethod
    def get_model_info(cls, model: str) -> dict[str, Any]:
        """获取模型信息"""
        return cls.MODEL_CAPABILITIES.get(model, {
            "reasoning": 3,
            "creativity": 3,
            "speed": 3,
            "cost": 3,
        })


# 便捷函数
def create_claude_client(
    api_key: str,
    model: str = "claude-3-5-sonnet-20241022",
    **kwargs: Any,
) -> AnthropicClient:
    """创建 Claude 客户端"""
    config = LLMConfig(
        provider="anthropic",  # type: ignore
        model=model,
        api_key=api_key,
        **kwargs,
    )
    return AnthropicClient(config)