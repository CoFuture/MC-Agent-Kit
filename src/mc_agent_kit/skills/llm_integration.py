"""
LLM 集成模块

提供 OpenAI、Azure OpenAI、本地 LLM (Ollama/LM Studio) 的集成支持。
支持流式响应、Token 计数、成本追踪等功能。
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Union


class LLMProvider(Enum):
    """LLM 提供者"""
    OPENAI = "openai"
    AZURE = "azure"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    MOCK = "mock"


class MessageRole(Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class ChatMessage:
    """聊天消息"""
    role: MessageRole
    content: str
    name: Optional[str] = None
    function_call: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        result = {"role": self.role.value, "content": self.content}
        if self.name:
            result["name"] = self.name
        if self.function_call:
            result["function_call"] = self.function_call
        return result


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 1.0
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0
    stream: bool = False

    # 本地 LLM 配置
    local_host: str = "localhost"
    local_port: int = 11434

    def __post_init__(self) -> None:
        # 设置默认 base_url
        if self.base_url is None:
            if self.provider == LLMProvider.OLLAMA:
                self.base_url = f"http://{self.local_host}:{self.local_port}"
            elif self.provider == LLMProvider.LM_STUDIO:
                self.base_url = f"http://{self.local_host}:1234/v1"
            elif self.provider == LLMProvider.AZURE:
                # Azure 需要 deployment-endpoint 格式
                pass


@dataclass
class TokenUsage:
    """Token 使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


@dataclass
class CostTracker:
    """成本追踪器"""
    # 每 1K tokens 价格 (USD)
    pricing: dict[str, dict[str, float]] = field(default_factory=lambda: {
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
        "gpt-3.5-turbo-16k": {"prompt": 0.003, "completion": 0.004},
        "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
        "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
        "default": {"prompt": 0.001, "completion": 0.002},
    })

    total_usage: TokenUsage = field(default_factory=TokenUsage)
    total_cost: float = 0.0
    request_count: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def calculate_cost(self, model: str, usage: TokenUsage) -> float:
        """计算成本"""
        model_pricing = self.pricing.get(model, self.pricing["default"])
        prompt_cost = (usage.prompt_tokens / 1000) * model_pricing["prompt"]
        completion_cost = (usage.completion_tokens / 1000) * model_pricing["completion"]
        return prompt_cost + completion_cost

    def record_usage(self, model: str, usage: TokenUsage) -> float:
        """记录使用量和成本"""
        cost = self.calculate_cost(model, usage)
        with self._lock:
            self.total_usage = self.total_usage + usage
            self.total_cost += cost
            self.request_count += 1
        return cost

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "total_tokens": self.total_usage.total_tokens,
                "prompt_tokens": self.total_usage.prompt_tokens,
                "completion_tokens": self.total_usage.completion_tokens,
                "total_cost": self.total_cost,
                "request_count": self.request_count,
            }


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    usage: TokenUsage
    finish_reason: str
    cost: float = 0.0
    latency: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamChunk:
    """流式响应块"""
    content: str
    delta: str
    finish_reason: Optional[str] = None
    usage: Optional[TokenUsage] = None


class BaseLLMClient(ABC):
    """LLM 客户端基类"""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self.cost_tracker = CostTracker()

    @abstractmethod
    def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """完成对话"""
        pass

    @abstractmethod
    async def complete_async(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """异步完成对话"""
        pass

    @abstractmethod
    def stream(
        self,
        messages: list[ChatMessage],
        callback: Callable[[StreamChunk], None],
        **kwargs: Any,
    ) -> LLMResponse:
        """流式响应"""
        pass

    def _handle_error(self, error: Exception, attempt: int) -> None:
        """处理错误"""
        if attempt >= self.config.max_retries:
            raise error
        time.sleep(self.config.retry_delay * attempt)


class OpenAIClient(BaseLLMClient):
    """OpenAI 客户端"""

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._client: Any = None

    def _get_client(self) -> Any:
        """获取 OpenAI 客户端"""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
                )
            except ImportError:
                raise ImportError("请安装 openai: pip install openai")
        return self._client

    def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """完成对话"""
        client = self._get_client()
        start_time = time.time()

        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=kwargs.get("model", self.config.model),
                    messages=[m.to_dict() for m in messages],
                    max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                    temperature=kwargs.get("temperature", self.config.temperature),
                    top_p=kwargs.get("top_p", self.config.top_p),
                )

                usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )

                cost = self.cost_tracker.record_usage(
                    response.model,
                    usage,
                )

                return LLMResponse(
                    content=response.choices[0].message.content or "",
                    model=response.model,
                    usage=usage,
                    finish_reason=response.choices[0].finish_reason or "stop",
                    cost=cost,
                    latency=time.time() - start_time,
                )

            except Exception as e:
                self._handle_error(e, attempt)

        raise RuntimeError("Max retries exceeded")

    async def complete_async(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """异步完成对话"""
        client = self._get_client()
        start_time = time.time()

        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = await client.chat.completions.create(
                    model=kwargs.get("model", self.config.model),
                    messages=[m.to_dict() for m in messages],
                    max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                    temperature=kwargs.get("temperature", self.config.temperature),
                    top_p=kwargs.get("top_p", self.config.top_p),
                )

                usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )

                cost = self.cost_tracker.record_usage(
                    response.model,
                    usage,
                )

                return LLMResponse(
                    content=response.choices[0].message.content or "",
                    model=response.model,
                    usage=usage,
                    finish_reason=response.choices[0].finish_reason or "stop",
                    cost=cost,
                    latency=time.time() - start_time,
                )

            except Exception as e:
                self._handle_error(e, attempt)

        raise RuntimeError("Max retries exceeded")

    def stream(
        self,
        messages: list[ChatMessage],
        callback: Callable[[StreamChunk], None],
        **kwargs: Any,
    ) -> LLMResponse:
        """流式响应"""
        client = self._get_client()
        start_time = time.time()

        content_parts: list[str] = []
        usage = TokenUsage()
        finish_reason = "stop"

        for attempt in range(1, self.config.max_retries + 1):
            try:
                stream = client.chat.completions.create(
                    model=kwargs.get("model", self.config.model),
                    messages=[m.to_dict() for m in messages],
                    max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                    temperature=kwargs.get("temperature", self.config.temperature),
                    stream=True,
                )

                for chunk in stream:
                    if chunk.choices:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            content_parts.append(delta.content)
                            callback(StreamChunk(
                                content="".join(content_parts),
                                delta=delta.content,
                            ))
                        if chunk.choices[0].finish_reason:
                            finish_reason = chunk.choices[0].finish_reason

                    if hasattr(chunk, "usage") and chunk.usage:
                        usage = TokenUsage(
                            prompt_tokens=chunk.usage.prompt_tokens,
                            completion_tokens=chunk.usage.completion_tokens,
                            total_tokens=chunk.usage.total_tokens,
                        )

                content = "".join(content_parts)

                # 如果没有从流中获取 usage，估算
                if usage.total_tokens == 0:
                    usage = TokenUsage(
                        prompt_tokens=len(str(messages)) // 4,
                        completion_tokens=len(content) // 4,
                        total_tokens=(len(str(messages)) + len(content)) // 4,
                    )

                cost = self.cost_tracker.record_usage(
                    self.config.model,
                    usage,
                )

                return LLMResponse(
                    content=content,
                    model=self.config.model,
                    usage=usage,
                    finish_reason=finish_reason,
                    cost=cost,
                    latency=time.time() - start_time,
                )

            except Exception as e:
                self._handle_error(e, attempt)

        raise RuntimeError("Max retries exceeded")


class AzureOpenAIClient(BaseLLMClient):
    """Azure OpenAI 客户端"""

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._client: Any = None

        if not config.api_key:
            raise ValueError("Azure OpenAI 需要 api_key")
        if not config.base_url:
            raise ValueError("Azure OpenAI 需要 base_url (endpoint)")
        if not config.api_version:
            config.api_version = "2024-02-15-preview"

    def _get_client(self) -> Any:
        """获取 Azure OpenAI 客户端"""
        if self._client is None:
            try:
                import openai
                self._client = openai.AzureOpenAI(
                    api_key=self.config.api_key,
                    azure_endpoint=self.config.base_url,
                    api_version=self.config.api_version,
                    timeout=self.config.timeout,
                )
            except ImportError:
                raise ImportError("请安装 openai: pip install openai")
        return self._client

    def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """完成对话"""
        client = self._get_client()
        start_time = time.time()

        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=kwargs.get("model", self.config.model),
                    messages=[m.to_dict() for m in messages],
                    max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                    temperature=kwargs.get("temperature", self.config.temperature),
                )

                usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )

                cost = self.cost_tracker.record_usage(
                    response.model,
                    usage,
                )

                return LLMResponse(
                    content=response.choices[0].message.content or "",
                    model=response.model,
                    usage=usage,
                    finish_reason=response.choices[0].finish_reason or "stop",
                    cost=cost,
                    latency=time.time() - start_time,
                )

            except Exception as e:
                self._handle_error(e, attempt)

        raise RuntimeError("Max retries exceeded")

    async def complete_async(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """异步完成对话 - 使用线程池实现"""
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

        content_parts: list[str] = []
        usage = TokenUsage()
        finish_reason = "stop"

        for attempt in range(1, self.config.max_retries + 1):
            try:
                stream = client.chat.completions.create(
                    model=kwargs.get("model", self.config.model),
                    messages=[m.to_dict() for m in messages],
                    max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                    temperature=kwargs.get("temperature", self.config.temperature),
                    stream=True,
                )

                for chunk in stream:
                    if chunk.choices:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            content_parts.append(delta.content)
                            callback(StreamChunk(
                                content="".join(content_parts),
                                delta=delta.content,
                            ))
                        if chunk.choices[0].finish_reason:
                            finish_reason = chunk.choices[0].finish_reason

                content = "".join(content_parts)

                # 估算 usage
                usage = TokenUsage(
                    prompt_tokens=len(str(messages)) // 4,
                    completion_tokens=len(content) // 4,
                    total_tokens=(len(str(messages)) + len(content)) // 4,
                )

                cost = self.cost_tracker.record_usage(
                    self.config.model,
                    usage,
                )

                return LLMResponse(
                    content=content,
                    model=self.config.model,
                    usage=usage,
                    finish_reason=finish_reason,
                    cost=cost,
                    latency=time.time() - start_time,
                )

            except Exception as e:
                self._handle_error(e, attempt)

        raise RuntimeError("Max retries exceeded")


class OllamaClient(BaseLLMClient):
    """Ollama 本地 LLM 客户端"""

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._session: Any = None

    def _get_session(self) -> Any:
        """获取 HTTP 会话"""
        if self._session is None:
            import urllib.request
            self._session = urllib.request
        return self._session

    def _make_request(
        self,
        endpoint: str,
        data: dict[str, Any],
    ) -> Any:
        """发送 HTTP 请求"""
        import urllib.request
        import urllib.error

        url = f"{self.config.base_url}/api/{endpoint}"
        json_data = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=json_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """完成对话"""
        start_time = time.time()

        data = {
            "model": kwargs.get("model", self.config.model),
            "messages": [m.to_dict() for m in messages],
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }

        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = self._make_request("chat", data)

                content = response.get("message", {}).get("content", "")

                # Ollama 返回的 token 统计
                eval_count = response.get("eval_count", 0)
                prompt_eval_count = response.get("prompt_eval_count", 0)
                usage = TokenUsage(
                    prompt_tokens=prompt_eval_count,
                    completion_tokens=eval_count,
                    total_tokens=prompt_eval_count + eval_count,
                )

                # 本地模型免费
                cost = 0.0

                return LLMResponse(
                    content=content,
                    model=self.config.model,
                    usage=usage,
                    finish_reason="stop",
                    cost=cost,
                    latency=time.time() - start_time,
                )

            except Exception as e:
                self._handle_error(e, attempt)

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
        import urllib.request
        import urllib.error

        start_time = time.time()

        data = {
            "model": kwargs.get("model", self.config.model),
            "messages": [m.to_dict() for m in messages],
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }

        url = f"{self.config.base_url}/api/chat"
        json_data = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=json_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        content_parts: list[str] = []
        usage = TokenUsage()

        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                for line in response:
                    if line.strip():
                        chunk_data = json.loads(line.decode("utf-8"))
                        if "message" in chunk_data:
                            delta = chunk_data["message"].get("content", "")
                            if delta:
                                content_parts.append(delta)
                                callback(StreamChunk(
                                    content="".join(content_parts),
                                    delta=delta,
                                ))

                        if chunk_data.get("done"):
                            eval_count = chunk_data.get("eval_count", 0)
                            prompt_eval_count = chunk_data.get("prompt_eval_count", 0)
                            usage = TokenUsage(
                                prompt_tokens=prompt_eval_count,
                                completion_tokens=eval_count,
                                total_tokens=prompt_eval_count + eval_count,
                            )

        except Exception as e:
            raise RuntimeError(f"Ollama 流式请求失败: {e}")

        content = "".join(content_parts)

        return LLMResponse(
            content=content,
            model=self.config.model,
            usage=usage,
            finish_reason="stop",
            cost=0.0,
            latency=time.time() - start_time,
        )


class LMStudioClient(BaseLLMClient):
    """LM Studio 本地 LLM 客户端"""

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._openai_client: Optional[OpenAIClient] = None

    def _get_client(self) -> OpenAIClient:
        """获取客户端 (LM Studio 使用 OpenAI 兼容 API)"""
        if self._openai_client is None:
            # LM Studio 使用 OpenAI 兼容 API
            lm_config = LLMConfig(
                provider=LLMProvider.OPENAI,
                model=self.config.model,
                base_url=self.config.base_url or "http://localhost:1234/v1",
                api_key="lm-studio",  # LM Studio 不需要真实 API key
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.timeout,
            )
            self._openai_client = OpenAIClient(lm_config)
        return self._openai_client

    def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """完成对话"""
        response = self._get_client().complete(messages, **kwargs)
        # 本地模型免费
        response.cost = 0.0
        return response

    async def complete_async(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """异步完成对话"""
        response = await self._get_client().complete_async(messages, **kwargs)
        response.cost = 0.0
        return response

    def stream(
        self,
        messages: list[ChatMessage],
        callback: Callable[[StreamChunk], None],
        **kwargs: Any,
    ) -> LLMResponse:
        """流式响应"""
        response = self._get_client().stream(messages, callback, **kwargs)
        response.cost = 0.0
        return response


class MockLLMClient(BaseLLMClient):
    """Mock LLM 客户端 (用于测试)"""

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._responses: dict[str, str] = {
            "create_entity": '''from mod.common import CreateEngineEntity, GetEngineType

def create_custom_entity(entity_type: str, pos: tuple, dimension: int = 0):
    """创建自定义实体"""
    engine_type = GetEngineType()
    entity_id = CreateEngineEntity(engine_type, entity_type, pos, dimension)
    if entity_id:
        print(f"Created entity: {entity_type} with ID: {entity_id}")
        return entity_id
    return None
''',
            "event_listener": '''from mod.common import ListenEvent

def OnCustomEvent(args):
    """自定义事件回调"""
    print("Event received:", args)

ListenEvent("OnCustomEvent", OnCustomEvent)
''',
            "default": '''# Generated code
def main():
    """Main function"""
    pass

if __name__ == "__main__":
    main()
''',
        }

    def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """完成对话"""
        start_time = time.time()

        # 模拟延迟
        time.sleep(0.1)

        # 根据消息内容选择响应
        last_message = messages[-1].content.lower() if messages else ""
        content = self._responses.get("default", "")

        for key, response in self._responses.items():
            if key in last_message:
                content = response
                break

        # 估算 token
        usage = TokenUsage(
            prompt_tokens=len(str(messages)) // 4,
            completion_tokens=len(content) // 4,
            total_tokens=(len(str(messages)) + len(content)) // 4,
        )

        return LLMResponse(
            content=content,
            model=self.config.model,
            usage=usage,
            finish_reason="stop",
            cost=0.0,
            latency=time.time() - start_time,
        )

    async def complete_async(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """异步完成对话"""
        await asyncio.sleep(0.1)
        return self.complete(messages, **kwargs)

    def stream(
        self,
        messages: list[ChatMessage],
        callback: Callable[[StreamChunk], None],
        **kwargs: Any,
    ) -> LLMResponse:
        """流式响应"""
        start_time = time.time()

        response = self.complete(messages, **kwargs)
        content = response.content

        # 模拟流式输出
        for i, char in enumerate(content):
            callback(StreamChunk(
                content=content[:i + 1],
                delta=char,
            ))
            time.sleep(0.01)

        return LLMResponse(
            content=content,
            model=self.config.model,
            usage=response.usage,
            finish_reason="stop",
            cost=0.0,
            latency=time.time() - start_time,
        )


class LLMClientFactory:
    """LLM 客户端工厂"""

    _clients: dict[str, BaseLLMClient] = {}
    _lock = threading.Lock()

    @classmethod
    def create(cls, config: LLMConfig) -> BaseLLMClient:
        """创建 LLM 客户端"""
        cache_key = f"{config.provider.value}:{config.model}"

        with cls._lock:
            if cache_key in cls._clients:
                return cls._clients[cache_key]

            if config.provider == LLMProvider.OPENAI:
                client = OpenAIClient(config)
            elif config.provider == LLMProvider.AZURE:
                client = AzureOpenAIClient(config)
            elif config.provider == LLMProvider.OLLAMA:
                client = OllamaClient(config)
            elif config.provider == LLMProvider.LM_STUDIO:
                client = LMStudioClient(config)
            else:
                client = MockLLMClient(config)

            cls._clients[cache_key] = client
            return client

    @classmethod
    def clear(cls) -> None:
        """清空客户端缓存"""
        with cls._lock:
            cls._clients.clear()


class LLMService:
    """LLM 服务封装

    提供统一的 LLM 调用接口，支持多种提供者。

    使用示例:
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo",
            api_key="your-api-key",
        )
        service = LLMService(config)

        messages = [ChatMessage(role=MessageRole.USER, content="Hello")]
        response = service.chat(messages)
        print(response.content)
    """

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._client = LLMClientFactory.create(config)
        self._prompt_templates: dict[str, str] = {}

    def chat(
        self,
        messages: list[ChatMessage],
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """聊天

        Args:
            messages: 消息列表
            system_prompt: 系统提示
            **kwargs: 其他参数

        Returns:
            LLMResponse: 响应
        """
        all_messages = []

        if system_prompt:
            all_messages.append(ChatMessage(
                role=MessageRole.SYSTEM,
                content=system_prompt,
            ))

        all_messages.extend(messages)

        return self._client.complete(all_messages, **kwargs)

    async def chat_async(
        self,
        messages: list[ChatMessage],
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """异步聊天"""
        all_messages = []

        if system_prompt:
            all_messages.append(ChatMessage(
                role=MessageRole.SYSTEM,
                content=system_prompt,
            ))

        all_messages.extend(messages)

        return await self._client.complete_async(all_messages, **kwargs)

    def chat_stream(
        self,
        messages: list[ChatMessage],
        callback: Callable[[StreamChunk], None],
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """流式聊天"""
        all_messages = []

        if system_prompt:
            all_messages.append(ChatMessage(
                role=MessageRole.SYSTEM,
                content=system_prompt,
            ))

        all_messages.extend(messages)

        return self._client.stream(all_messages, callback, **kwargs)

    def register_prompt_template(self, name: str, template: str) -> None:
        """注册提示模板"""
        self._prompt_templates[name] = template

    def get_prompt_template(self, name: str) -> Optional[str]:
        """获取提示模板"""
        return self._prompt_templates.get(name)

    def apply_prompt_template(
        self,
        name: str,
        variables: dict[str, Any],
    ) -> str:
        """应用提示模板"""
        template = self._prompt_templates.get(name)
        if not template:
            return ""

        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))

        return result

    def get_cost_stats(self) -> dict[str, Any]:
        """获取成本统计"""
        if hasattr(self._client, "cost_tracker"):
            return self._client.cost_tracker.get_stats()
        return {}


# 便捷函数
_service: Optional[LLMService] = None


def get_llm_service(config: Optional[LLMConfig] = None) -> LLMService:
    """获取 LLM 服务实例"""
    global _service
    if config:
        _service = LLMService(config)
    elif _service is None:
        # 默认使用 Mock
        _service = LLMService(LLMConfig(
            provider=LLMProvider.MOCK,
            model="mock-model",
        ))
    return _service


def chat(
    message: str,
    system_prompt: Optional[str] = None,
    config: Optional[LLMConfig] = None,
) -> str:
    """便捷聊天函数"""
    service = get_llm_service(config)
    messages = [ChatMessage(role=MessageRole.USER, content=message)]
    response = service.chat(messages, system_prompt=system_prompt)
    return response.content