"""
LLM 提供商实现

提供多种 LLM 提供商的具体实现。
"""

from __future__ import annotations

import time
from typing import Any

from .base import (
    ChatMessage,
    ChatRole,
    CompletionResult,
    LLMConfig,
    LLMProvider,
    StreamChunk,
)


class MockProvider(LLMProvider):
    """
    Mock LLM 提供商

    用于测试和开发环境，不需要实际 API 调用。
    """

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._call_count = 0

    @property
    def name(self) -> str:
        return "mock"

    @property
    def models(self) -> list[str]:
        return ["mock-default", "mock-code", "mock-chat"]

    def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> CompletionResult:
        start_time = time.time()
        self._call_count += 1

        # 生成模拟响应
        content = self._generate_mock_response(messages)

        latency = (time.time() - start_time) * 1000

        return CompletionResult(
            content=content,
            model=self.config.model,
            provider=self.name,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            finish_reason="stop",
            latency_ms=latency,
        )

    async def complete_async(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> CompletionResult:
        return self.complete(messages, **kwargs)

    def count_tokens(self, text: str) -> int:
        # 简单估算：每 4 个字符约 1 个 token
        return len(text) // 4 + 1

    def _generate_mock_response(self, messages: list[ChatMessage]) -> str:
        """生成模拟响应"""
        if not messages:
            return "Mock response: no input provided"

        last_message = messages[-1]
        content = last_message.content

        # 根据内容生成不同的模拟响应
        if "创建实体" in content or "create entity" in content.lower():
            return '''# 创建实体的示例代码
import mod.server.extraServerApi as serverApi

def create_custom_entity(pos, entity_type="custom:entity"):
    """创建自定义实体"""
    comp_factory = serverApi.GetEngineCompFactory()
    create_comp = comp_factory.CreateEngineEntity
    entity_id = create_comp.CreateEntity(pos, entity_type)
    return entity_id

# 使用示例
entity_id = create_custom_entity((0, 64, 0))
print(f"Created entity: {entity_id}")'''

        elif "事件" in content or "event" in content.lower():
            return '''# 事件监听示例代码
import mod.server.extraServerApi as serverApi

def on_player_join(args):
    """玩家加入事件处理"""
    player_id = args["id"]
    print(f"Player joined: {player_id}")

# 注册事件监听
serverApi.ListenEvent("OnServerChat", on_player_join)'''

        elif "ui" in content.lower() or "界面" in content:
            return '''# UI 创建示例代码
import mod.client.extraClientApi as clientApi

def create_ui_screen():
    """创建 UI 界面"""
    ui_comp = clientApi.GetEngineCompFactory().CreateUIModule
    screen = ui_comp.CreateScreen("custom_screen")
    return screen'''

        elif "移动" in content or "movement" in content.lower():
            return '''# 实体移动示例代码
import mod.server.extraServerApi as serverApi

def move_entity(entity_id, pos):
    """移动实体到新位置"""
    comp_factory = serverApi.GetEngineCompFactory()
    entity_comp = comp_factory.InitializeComponent(entity_id, "minecraft:position")
    entity_comp.SetPos(pos)
    return True

# 使用示例
move_entity(entity_id, (10, 64, 10))'''

        else:
            return f"Mock response for: {content[:100]}"


class OpenAIProvider(LLMProvider):
    """
    OpenAI GPT 提供商

    支持 GPT-4, GPT-3.5 等模型。
    """

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._client: Any = None

    @property
    def name(self) -> str:
        return "openai"

    @property
    def models(self) -> list[str]:
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]

    def initialize(self) -> None:
        """初始化 OpenAI 客户端"""
        if self._initialized:
            return

        try:
            import openai
            self._client = openai.OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )
            super().initialize()
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

    def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> CompletionResult:
        if not self._initialized:
            self.initialize()

        start_time = time.time()

        response = self._client.chat.completions.create(
            model=self.config.model,
            messages=[m.to_dict() for m in messages],
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            **self.config.extra,
        )

        latency = (time.time() - start_time) * 1000

        choice = response.choices[0]
        return CompletionResult(
            content=choice.message.content or "",
            model=response.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            finish_reason=choice.finish_reason,
            latency_ms=latency,
        )

    async def complete_async(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> CompletionResult:
        if not self._initialized:
            self.initialize()

        start_time = time.time()

        client = self._client
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=[m.to_dict() for m in messages],
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            **self.config.extra,
        )

        latency = (time.time() - start_time) * 1000

        choice = response.choices[0]
        return CompletionResult(
            content=choice.message.content or "",
            model=response.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            finish_reason=choice.finish_reason,
            latency_ms=latency,
        )

    def count_tokens(self, text: str) -> int:
        try:
            import tiktoken
            enc = tiktoken.encoding_for_model(self.config.model)
            return len(enc.encode(text))
        except ImportError:
            # 如果没有安装 tiktoken，使用简单估算
            return len(text) // 4 + 1

    def validate_config(self) -> bool:
        return bool(self.config.api_key)


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude 提供商

    支持 Claude 3 系列模型。
    """

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._client: Any = None

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def models(self) -> list[str]:
        return [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    def initialize(self) -> None:
        """初始化 Anthropic 客户端"""
        if self._initialized:
            return

        try:
            import anthropic
            self._client = anthropic.Anthropic(
                api_key=self.config.api_key,
                timeout=self.config.timeout,
            )
            super().initialize()
        except ImportError:
            raise RuntimeError(
                "anthropic package not installed. Run: pip install anthropic"
            )

    def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> CompletionResult:
        if not self._initialized:
            self.initialize()

        start_time = time.time()

        # 转换消息格式
        system_message = ""
        chat_messages = []
        for m in messages:
            if m.role == ChatRole.SYSTEM:
                system_message = m.content
            else:
                chat_messages.append({"role": m.role.value, "content": m.content})

        response = self._client.messages.create(
            model=self.config.model,
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            system=system_message,
            messages=chat_messages,
            **self.config.extra,
        )

        latency = (time.time() - start_time) * 1000

        return CompletionResult(
            content=response.content[0].text,
            model=response.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
            latency_ms=latency,
        )

    async def complete_async(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> CompletionResult:
        if not self._initialized:
            self.initialize()

        start_time = time.time()

        # 转换消息格式
        system_message = ""
        chat_messages = []
        for m in messages:
            if m.role == ChatRole.SYSTEM:
                system_message = m.content
            else:
                chat_messages.append({"role": m.role.value, "content": m.content})

        client = anthropic.AsyncAnthropic(api_key=self.config.api_key)
        response = await client.messages.create(
            model=self.config.model,
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            system=system_message,
            messages=chat_messages,
            **self.config.extra,
        )

        latency = (time.time() - start_time) * 1000

        return CompletionResult(
            content=response.content[0].text,
            model=response.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
            latency_ms=latency,
        )

    def count_tokens(self, text: str) -> int:
        # Claude 使用自己的 tokenizer，这里简单估算
        return len(text) // 3 + 1

    def validate_config(self) -> bool:
        return bool(self.config.api_key)


class GeminiProvider(LLMProvider):
    """
    Google Gemini 提供商

    支持 Gemini Pro 等模型。
    """

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._client: Any = None

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def models(self) -> list[str]:
        return [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-pro",
            "gemini-pro-vision",
        ]

    def initialize(self) -> None:
        """初始化 Gemini 客户端"""
        if self._initialized:
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.config.api_key)
            self._client = genai
            super().initialize()
        except ImportError:
            raise RuntimeError(
                "google-generativeai package not installed. "
                "Run: pip install google-generativeai"
            )

    def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> CompletionResult:
        if not self._initialized:
            self.initialize()

        start_time = time.time()

        # 转换消息格式
        history = []
        for m in messages[:-1]:  # 最后一条是当前输入
            if m.role != ChatRole.SYSTEM:
                history.append({
                    "role": "user" if m.role == ChatRole.USER else "model",
                    "parts": [m.content],
                })

        model = self._client.GenerativeModel(
            self.config.model,
            generation_config={
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_output_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            },
        )

        chat = model.start_chat(history=history)
        response = chat.send_message(messages[-1].content)

        latency = (time.time() - start_time) * 1000

        return CompletionResult(
            content=response.text,
            model=self.config.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            },
            finish_reason="stop",
            latency_ms=latency,
        )

    async def complete_async(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> CompletionResult:
        # Gemini 的异步 API 与同步 API 类似
        return self.complete(messages, **kwargs)

    def count_tokens(self, text: str) -> int:
        if self._initialized:
            model = self._client.GenerativeModel(self.config.model)
            result = model.count_tokens(text)
            return result.total_tokens
        return len(text) // 4 + 1

    def validate_config(self) -> bool:
        return bool(self.config.api_key)


class OllamaProvider(LLMProvider):
    """
    Ollama 本地模型提供商

    支持本地部署的开源模型。
    """

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        # 默认 Ollama 地址
        if not self.config.base_url:
            self.config.base_url = "http://localhost:11434"

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def models(self) -> list[str]:
        return [
            "llama3.1",
            "llama3",
            "llama2",
            "mistral",
            "codellama",
            "deepseek-coder",
            "qwen2.5",
            "qwen2",
        ]

    def initialize(self) -> None:
        """初始化 Ollama 客户端"""
        if self._initialized:
            return

        try:
            import ollama
            self._client = ollama
            super().initialize()
        except ImportError:
            raise RuntimeError("ollama package not installed. Run: pip install ollama")

    def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> CompletionResult:
        if not self._initialized:
            self.initialize()

        start_time = time.time()

        response = self._client.chat(
            model=self.config.model,
            messages=[m.to_dict() for m in messages],
            options={
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        )

        latency = (time.time() - start_time) * 1000

        return CompletionResult(
            content=response["message"]["content"],
            model=self.config.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0),
                "total_tokens": response.get("prompt_eval_count", 0) + response.get("eval_count", 0),
            },
            finish_reason="stop",
            latency_ms=latency,
        )

    async def complete_async(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> CompletionResult:
        if not self._initialized:
            self.initialize()

        start_time = time.time()

        response = await self._client.AsyncClient().chat(
            model=self.config.model,
            messages=[m.to_dict() for m in messages],
            options={
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        )

        latency = (time.time() - start_time) * 1000

        return CompletionResult(
            content=response["message"]["content"],
            model=self.config.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0),
                "total_tokens": response.get("prompt_eval_count", 0) + response.get("eval_count", 0),
            },
            finish_reason="stop",
            latency_ms=latency,
        )

    def count_tokens(self, text: str) -> int:
        # Ollama 的 tokenizer 取决于模型
        return len(text) // 4 + 1

    def validate_config(self) -> bool:
        # Ollama 不需要 API key，只需要本地服务运行
        return True