"""
Google Gemini 客户端

支持 Gemini Pro、Gemini Ultra 等模型的调用。
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
class GeminiConfig:
    """Gemini 配置"""
    api_key: str
    model: str = "gemini-1.5-pro"
    max_tokens: int = 8192
    temperature: float = 0.7
    timeout: float = 120.0
    max_retries: int = 3
    retry_delay: float = 1.0
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    
    # Gemini 特定参数
    top_k: int = 40
    top_p: float = 0.95
    
    # 安全设置
    safety_settings: list[dict[str, Any]] = field(default_factory=lambda: [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ])
    
    # 定价 (每 1K tokens, USD)
    pricing: dict[str, dict[str, float]] = field(default_factory=lambda: {
        "gemini-1.5-pro": {"prompt": 0.0035, "completion": 0.0105},
        "gemini-1.5-flash": {"prompt": 0.000075, "completion": 0.0003},
        "gemini-1.0-pro": {"prompt": 0.0005, "completion": 0.0015},
        "gemini-ultra": {"prompt": 0.025, "completion": 0.05},
        "default": {"prompt": 0.001, "completion": 0.002},
    })


@dataclass
class GeminiUsage:
    """Gemini 使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0


class GeminiClient(BaseLLMClient):
    """Google Gemini 客户端
    
    支持的模型:
    - gemini-1.5-pro (推荐，强大且高效)
    - gemini-1.5-flash (最快，适合简单任务)
    - gemini-1.0-pro (经典版本)
    - gemini-ultra (最强大，有限可用)
    
    使用示例:
        config = LLMConfig(
            provider=LLMProvider.GEMINI,
            model="gemini-1.5-pro",
            api_key="your-api-key",
        )
        client = GeminiClient(config)
        
        messages = [ChatMessage(role=MessageRole.USER, content="Hello")]
        response = client.complete(messages)
    """
    
    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._client: Any = None
        self._gemini_config = GeminiConfig(
            api_key=config.api_key or "",
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
        )
        self._total_usage = GeminiUsage()
        self._lock = threading.Lock()
    
    def _get_client(self) -> Any:
        """获取 Gemini 客户端"""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._gemini_config.api_key)
                self._client = genai
            except ImportError:
                raise ImportError(
                    "请安装 google-generativeai: pip install google-generativeai"
                ) from None
        return self._client
    
    def _convert_messages(
        self,
        messages: list[ChatMessage],
    ) -> tuple[str, list[dict[str, Any]]]:
        """转换消息格式
        
        Gemini API 使用 contents 而不是 messages。
        """
        system_parts: list[str] = []
        contents: list[dict[str, Any]] = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_parts.append(msg.content)
            else:
                role = "user" if msg.role == MessageRole.USER else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}],
                })
        
        return "\n".join(system_parts), contents
    
    def _calculate_cost(self, model: str, usage: TokenUsage) -> float:
        """计算成本"""
        pricing = self._gemini_config.pricing.get(
            model,
            self._gemini_config.pricing["default"]
        )
        prompt_cost = (usage.prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (usage.completion_tokens / 1000) * pricing["completion"]
        return prompt_cost + completion_cost
    
    def _record_usage(self, model: str, usage: TokenUsage) -> float:
        """记录使用量"""
        cost = self._calculate_cost(model, usage)
        with self._lock:
            self._total_usage.prompt_tokens += usage.prompt_tokens
            self._total_usage.completion_tokens += usage.completion_tokens
            self._total_usage.total_tokens += usage.total_tokens
            self._total_usage.cost += cost
        return cost
    
    def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """完成对话"""
        genai = self._get_client()
        start_time = time.time()
        
        system_prompt, contents = self._convert_messages(messages)
        
        model = kwargs.get("model", self._gemini_config.model)
        max_tokens = kwargs.get("max_tokens", self._gemini_config.max_tokens)
        temperature = kwargs.get("temperature", self._gemini_config.temperature)
        top_k = kwargs.get("top_k", self._gemini_config.top_k)
        top_p = kwargs.get("top_p", self._gemini_config.top_p)
        
        for attempt in range(1, self._gemini_config.max_retries + 1):
            try:
                # 创建模型实例
                model_instance = genai.GenerativeModel(
                    model_name=model,
                    system_instruction=system_prompt if system_prompt else None,
                    safety_settings=self._gemini_config.safety_settings,
                )
                
                generation_config = {
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                    "top_k": top_k,
                    "top_p": top_p,
                }
                
                response = model_instance.generate_content(
                    contents,
                    generation_config=generation_config,
                )
                
                # 提取使用统计
                usage = TokenUsage()
                if hasattr(response, "usage_metadata"):
                    usage = TokenUsage(
                        prompt_tokens=response.usage_metadata.prompt_token_count,
                        completion_tokens=response.usage_metadata.candidates_token_count,
                        total_tokens=response.usage_metadata.total_token_count,
                    )
                else:
                    # 估算
                    prompt_len = sum(len(str(m.content)) for m in messages)
                    response_len = len(response.text) if response.text else 0
                    usage = TokenUsage(
                        prompt_tokens=prompt_len // 4,
                        completion_tokens=response_len // 4,
                        total_tokens=(prompt_len + response_len) // 4,
                    )
                
                cost = self._record_usage(model, usage)
                
                content = response.text if response.text else ""
                finish_reason = "stop"
                if hasattr(response, "candidates") and response.candidates:
                    finish_reason = response.candidates[0].finish_reason.name.lower()
                
                return LLMResponse(
                    content=content,
                    model=model,
                    usage=usage,
                    finish_reason=finish_reason,
                    cost=cost,
                    latency=time.time() - start_time,
                    metadata={
                        "model": model,
                    },
                )
            
            except Exception as e:
                if attempt >= self._gemini_config.max_retries:
                    raise
                time.sleep(self._gemini_config.retry_delay * attempt)
        
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
        genai = self._get_client()
        start_time = time.time()
        
        system_prompt, contents = self._convert_messages(messages)
        
        model = kwargs.get("model", self._gemini_config.model)
        max_tokens = kwargs.get("max_tokens", self._gemini_config.max_tokens)
        temperature = kwargs.get("temperature", self._gemini_config.temperature)
        
        content_parts: list[str] = []
        usage = TokenUsage()
        finish_reason = "stop"
        
        for attempt in range(1, self._gemini_config.max_retries + 1):
            try:
                model_instance = genai.GenerativeModel(
                    model_name=model,
                    system_instruction=system_prompt if system_prompt else None,
                    safety_settings=self._gemini_config.safety_settings,
                )
                
                generation_config = {
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                }
                
                response_stream = model_instance.generate_content(
                    contents,
                    generation_config=generation_config,
                    stream=True,
                )
                
                for chunk in response_stream:
                    if chunk.text:
                        content_parts.append(chunk.text)
                        callback(StreamChunk(
                            content="".join(content_parts),
                            delta=chunk.text,
                        ))
                
                break
            
            except Exception as e:
                if attempt >= self._gemini_config.max_retries:
                    raise
                time.sleep(self._gemini_config.retry_delay * attempt)
        
        content = "".join(content_parts)
        
        # 估算使用量
        prompt_len = sum(len(str(m.content)) for m in messages)
        usage = TokenUsage(
            prompt_tokens=prompt_len // 4,
            completion_tokens=len(content) // 4,
            total_tokens=(prompt_len + len(content)) // 4,
        )
        
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
                "prompt_tokens": self._total_usage.prompt_tokens,
                "completion_tokens": self._total_usage.completion_tokens,
                "total_tokens": self._total_usage.total_tokens,
                "total_cost": self._total_usage.cost,
            }


class GeminiModelSelector:
    """Gemini 模型选择器
    
    根据任务类型自动选择最合适的模型。
    """
    
    # 模型能力评级
    MODEL_CAPABILITIES = {
        "gemini-1.5-pro": {
            "reasoning": 5,
            "creativity": 4,
            "speed": 4,
            "cost": 3,
            "context_length": 1000000,
        },
        "gemini-1.5-flash": {
            "reasoning": 3,
            "creativity": 3,
            "speed": 5,
            "cost": 5,
            "context_length": 1000000,
        },
        "gemini-1.0-pro": {
            "reasoning": 3,
            "creativity": 3,
            "speed": 4,
            "cost": 4,
            "context_length": 32000,
        },
        "gemini-ultra": {
            "reasoning": 5,
            "creativity": 5,
            "speed": 3,
            "cost": 2,
            "context_length": 32000,
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
            if priority == "quality":
                return "gemini-1.5-pro"
            elif priority == "speed":
                return "gemini-1.5-flash"
            else:
                return "gemini-1.5-pro"
        
        elif task_type == "analysis":
            if priority == "quality":
                return "gemini-1.5-pro"
            elif priority == "speed":
                return "gemini-1.5-flash"
            else:
                return "gemini-1.5-pro"
        
        elif task_type == "creative":
            if priority == "quality":
                return "gemini-1.5-pro"
            else:
                return "gemini-1.5-flash"
        
        else:  # simple
            return "gemini-1.5-flash"
    
    @classmethod
    def get_model_info(cls, model: str) -> dict[str, Any]:
        """获取模型信息"""
        return cls.MODEL_CAPABILITIES.get(model, {
            "reasoning": 3,
            "creativity": 3,
            "speed": 3,
            "cost": 3,
            "context_length": 32000,
        })


# 便捷函数
def create_gemini_client(
    api_key: str,
    model: str = "gemini-1.5-pro",
    **kwargs: Any,
) -> GeminiClient:
    """创建 Gemini 客户端"""
    config = LLMConfig(
        provider="gemini",  # type: ignore
        model=model,
        api_key=api_key,
        **kwargs,
    )
    return GeminiClient(config)