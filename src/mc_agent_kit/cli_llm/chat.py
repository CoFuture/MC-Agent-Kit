"""Chat session management for LLM CLI.

Provides interactive chat capabilities with history management.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from mc_agent_kit.llm import (
    ChatMessage,
    ChatRole,
    CompletionResult,
    LLMConfig,
    get_llm_manager,
)

from .config import LLMCliConfig


@dataclass
class SessionMessage:
    """A message in the chat session."""

    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionMessage":
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()

        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=timestamp,
            metadata=data.get("metadata", {}),
        )

    def to_llm_message(self) -> ChatMessage:
        """Convert to LLM ChatMessage."""
        role_map = {
            "user": ChatRole.USER,
            "assistant": ChatRole.ASSISTANT,
            "system": ChatRole.SYSTEM,
        }
        return ChatMessage(
            role=role_map.get(self.role, ChatRole.USER),
            content=self.content,
        )


@dataclass
class ChatSessionConfig:
    """Configuration for chat session."""

    max_history: int = 100
    system_prompt: str = ""
    context_window: int = 10
    save_history: bool = True
    history_file: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "max_history": self.max_history,
            "system_prompt": self.system_prompt,
            "context_window": self.context_window,
            "save_history": self.save_history,
            "history_file": self.history_file,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatSessionConfig":
        """Create from dictionary."""
        return cls(
            max_history=data.get("max_history", 100),
            system_prompt=data.get("system_prompt", ""),
            context_window=data.get("context_window", 10),
            save_history=data.get("save_history", True),
            history_file=data.get("history_file", ""),
        )


class ChatSession:
    """Interactive chat session with LLM."""

    DEFAULT_SYSTEM_PROMPT = """你是 MC-Agent-Kit 的 AI 助手，专门帮助开发者进行 Minecraft 网易版 ModSDK 开发。

你可以帮助用户：
1. 查询 ModSDK API 和事件
2. 生成 ModSDK 代码
3. 分析和修复代码错误
4. 提供开发建议和最佳实践

请用中文回复，并提供简洁、准确的帮助。"""

    def __init__(
        self,
        config: LLMCliConfig,
        session_config: ChatSessionConfig | None = None,
    ):
        """Initialize chat session.

        Args:
            config: LLM CLI configuration
            session_config: Session configuration
        """
        self.config = config
        self.session_config = session_config or ChatSessionConfig()
        self.messages: list[SessionMessage] = []
        self._llm_manager = get_llm_manager()
        self._initialized = False

        # Set up LLM config
        provider_config = config.get_provider_config(config.default_provider)
        self._llm_config = LLMConfig(
            provider=config.default_provider,
            model=provider_config.model or "default",
            api_key=provider_config.api_key,
            base_url=provider_config.base_url,
            temperature=provider_config.temperature,
            max_tokens=provider_config.max_tokens,
        )

    def initialize(self) -> None:
        """Initialize the session."""
        if self._initialized:
            return

        # Set default provider
        self._llm_manager.set_default_provider(self.config.default_provider)

        # Load history if enabled
        if self.session_config.save_history and self.session_config.history_file:
            self._load_history()

        self._initialized = True

    def send(
        self,
        message: str,
        stream: bool = False,
    ) -> Iterator[str] | str:
        """Send a message and get response.

        Args:
            message: User message
            stream: Whether to stream response

        Returns:
            Response string or iterator of chunks
        """
        self.initialize()

        # Add user message
        user_msg = SessionMessage(role="user", content=message)
        self.messages.append(user_msg)

        # Build messages for LLM
        llm_messages = self._build_llm_messages()

        if stream:
            return self._stream_response(llm_messages)
        else:
            return self._get_response(llm_messages)

    def _build_llm_messages(self) -> list[ChatMessage]:
        """Build messages for LLM from session history."""
        messages = []

        # Add system prompt
        system_prompt = self.session_config.system_prompt or self.DEFAULT_SYSTEM_PROMPT
        messages.append(ChatMessage(role=ChatRole.SYSTEM, content=system_prompt))

        # Add recent messages within context window
        recent_messages = self.messages[-self.session_config.context_window :]
        for msg in recent_messages:
            messages.append(msg.to_llm_message())

        return messages

    def _get_response(self, messages: list[ChatMessage]) -> str:
        """Get non-streaming response.

        Args:
            messages: Messages to send

        Returns:
            Response content
        """
        result = self._llm_manager.complete(messages, self._llm_config)

        # Add assistant message
        assistant_msg = SessionMessage(role="assistant", content=result.content)
        self.messages.append(assistant_msg)

        # Save history
        if self.session_config.save_history:
            self._save_history()

        return result.content

    def _stream_response(self, messages: list[ChatMessage]) -> Iterator[str]:
        """Stream response from LLM.

        Args:
            messages: Messages to send

        Yields:
            Response chunks
        """
        full_content = []

        for chunk in self._llm_manager.stream(messages, self._llm_config):
            full_content.append(chunk.content)
            yield chunk.content

        # Add assistant message
        assistant_msg = SessionMessage(
            role="assistant",
            content="".join(full_content),
        )
        self.messages.append(assistant_msg)

        # Save history
        if self.session_config.save_history:
            self._save_history()

    def clear_history(self) -> None:
        """Clear chat history."""
        self.messages = []
        if self.session_config.save_history and self.session_config.history_file:
            self._save_history()

    def get_history(self) -> list[SessionMessage]:
        """Get chat history.

        Returns:
            List of messages
        """
        return self.messages.copy()

    def set_system_prompt(self, prompt: str) -> None:
        """Set system prompt.

        Args:
            prompt: New system prompt
        """
        self.session_config.system_prompt = prompt

    def _load_history(self) -> None:
        """Load history from file."""
        history_file = Path(self.session_config.history_file).expanduser()
        if not history_file.exists():
            return

        try:
            content = history_file.read_text(encoding="utf-8")
            data = json.loads(content)
            self.messages = [
                SessionMessage.from_dict(m)
                for m in data.get("messages", [])
            ][-self.session_config.max_history :]
        except Exception:
            pass

    def _save_history(self) -> None:
        """Save history to file."""
        if not self.session_config.history_file:
            return

        history_file = Path(self.session_config.history_file).expanduser()
        history_file.parent.mkdir(parents=True, exist_ok=True)

        # Keep only recent messages
        messages_to_save = self.messages[-self.session_config.max_history :]

        data = {
            "messages": [m.to_dict() for m in messages_to_save],
            "updated_at": datetime.now().isoformat(),
        }

        history_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def create_chat_session(
    config: LLMCliConfig | None = None,
    session_config: ChatSessionConfig | None = None,
) -> ChatSession:
    """Create a chat session.

    Args:
        config: LLM CLI configuration
        session_config: Session configuration

    Returns:
        ChatSession instance
    """
    from .config import create_llm_cli_config

    if config is None:
        config = create_llm_cli_config()

    return ChatSession(config, session_config)


def chat_interactive(
    session: ChatSession,
    prompt: str = "mc-llm> ",
    welcome: str | None = None,
) -> None:
    """Run interactive chat session.

    Args:
        session: Chat session
        prompt: Input prompt
        welcome: Welcome message
    """
    import sys

    session.initialize()

    if welcome:
        print(welcome)
        print()

    while True:
        try:
            # Get user input
            user_input = input(prompt).strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                cmd = user_input[1:].lower().strip()

                if cmd in ("exit", "quit", "q"):
                    print("Goodbye!")
                    break
                elif cmd in ("clear", "c"):
                    session.clear_history()
                    print("History cleared.")
                    continue
                elif cmd in ("help", "h", "?"):
                    print("Commands:")
                    print("  /exit, /quit, /q  - Exit chat")
                    print("  /clear, /c        - Clear history")
                    print("  /help, /h, ?      - Show help")
                    continue

            # Send message and get response
            if session.config.stream_output:
                print()
                for chunk in session.send(user_input, stream=True):
                    print(chunk, end="", flush=True)
                print("\n")
            else:
                response = session.send(user_input, stream=False)
                print(f"\n{response}\n")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Use /exit to quit.")
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)