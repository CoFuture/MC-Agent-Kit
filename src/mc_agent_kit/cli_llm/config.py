"""LLM CLI configuration management.

Provides configuration file and environment variable support for LLM CLI.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProviderConfig:
    """Configuration for a specific LLM provider."""

    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "api_key": self.api_key,
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderConfig":
        """Create from dictionary."""
        return cls(
            api_key=data.get("api_key"),
            model=data.get("model"),
            base_url=data.get("base_url"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 4096),
        )


@dataclass
class CodeGenerationConfig:
    """Configuration for code generation."""

    default_type: str = "custom"
    default_target: str = "server"
    style: str = "pep8"
    include_docstrings: bool = True
    include_type_hints: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "default_type": self.default_type,
            "default_target": self.default_target,
            "style": self.style,
            "include_docstrings": self.include_docstrings,
            "include_type_hints": self.include_type_hints,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CodeGenerationConfig":
        """Create from dictionary."""
        return cls(
            default_type=data.get("default_type", "custom"),
            default_target=data.get("default_target", "server"),
            style=data.get("style", "pep8"),
            include_docstrings=data.get("include_docstrings", True),
            include_type_hints=data.get("include_type_hints", True),
        )


@dataclass
class CodeReviewConfig:
    """Configuration for code review."""

    min_score: int = 60
    categories: list[str] = field(
        default_factory=lambda: ["security", "performance", "modsdk"]
    )
    max_suggestions: int = 10

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "min_score": self.min_score,
            "categories": self.categories,
            "max_suggestions": self.max_suggestions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CodeReviewConfig":
        """Create from dictionary."""
        return cls(
            min_score=data.get("min_score", 60),
            categories=data.get("categories", ["security", "performance", "modsdk"]),
            max_suggestions=data.get("max_suggestions", 10),
        )


@dataclass
class LLMCliConfig:
    """Complete LLM CLI configuration."""

    default_provider: str = "mock"
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    code_generation: CodeGenerationConfig = field(
        default_factory=CodeGenerationConfig
    )
    code_review: CodeReviewConfig = field(default_factory=CodeReviewConfig)
    history_file: str = "~/.mc-agent-kit/chat_history.json"
    max_history_entries: int = 100
    stream_output: bool = True
    verbose: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "default_provider": self.default_provider,
            "providers": {k: v.to_dict() for k, v in self.providers.items()},
            "code_generation": self.code_generation.to_dict(),
            "code_review": self.code_review.to_dict(),
            "history_file": self.history_file,
            "max_history_entries": self.max_history_entries,
            "stream_output": self.stream_output,
            "verbose": self.verbose,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LLMCliConfig":
        """Create from dictionary."""
        providers = {}
        for name, config in data.get("providers", {}).items():
            providers[name] = ProviderConfig.from_dict(config)

        return cls(
            default_provider=data.get("default_provider", "mock"),
            providers=providers,
            code_generation=CodeGenerationConfig.from_dict(
                data.get("code_generation", {})
            ),
            code_review=CodeReviewConfig.from_dict(data.get("code_review", {})),
            history_file=data.get("history_file", "~/.mc-agent-kit/chat_history.json"),
            max_history_entries=data.get("max_history_entries", 100),
            stream_output=data.get("stream_output", True),
            verbose=data.get("verbose", False),
        )

    def get_provider_config(self, provider: str) -> ProviderConfig:
        """Get configuration for a specific provider."""
        if provider in self.providers:
            return self.providers[provider]
        return ProviderConfig()


class LLMCliConfigManager:
    """Manager for LLM CLI configuration."""

    DEFAULT_CONFIG_PATH = "~/.mc-agent-kit/config.yaml"
    ENV_PREFIX = "MC_AGENT_KIT_"

    def __init__(self, config_path: str | None = None):
        """Initialize the config manager.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(
            config_path or os.environ.get(
                f"{self.ENV_PREFIX}CONFIG_PATH",
                self.DEFAULT_CONFIG_PATH
            )
        ).expanduser()
        self._config: LLMCliConfig | None = None

    def load(self) -> LLMCliConfig:
        """Load configuration from file and environment variables.

        Returns:
            LLMCliConfig: Loaded configuration
        """
        # Start with default config
        config_data: dict[str, Any] = {}

        # Load from file if exists
        if self.config_path.exists():
            try:
                content = self.config_path.read_text(encoding="utf-8")
                if self.config_path.suffix in (".yaml", ".yml"):
                    import yaml
                    config_data = yaml.safe_load(content) or {}
                else:
                    config_data = json.loads(content)
            except Exception:
                pass

        # Override with environment variables
        config_data = self._apply_env_overrides(config_data)

        # Create config object
        self._config = LLMCliConfig.from_dict(config_data)
        return self._config

    def _apply_env_overrides(self, config_data: dict[str, Any]) -> dict[str, Any]:
        """Apply environment variable overrides.

        Args:
            config_data: Base configuration data

        Returns:
            Updated configuration data
        """
        # Default provider
        if env_provider := os.environ.get(f"{self.ENV_PREFIX}LLM_PROVIDER"):
            config_data["default_provider"] = env_provider

        # API keys from environment
        env_keys = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
        }

        providers = config_data.setdefault("providers", {})
        for provider, env_var in env_keys.items():
            if api_key := os.environ.get(env_var):
                provider_config = providers.setdefault(provider, {})
                provider_config["api_key"] = api_key

        # Ollama base URL
        if ollama_url := os.environ.get("OLLAMA_BASE_URL"):
            ollama_config = providers.setdefault("ollama", {})
            ollama_config["base_url"] = ollama_url

        # Stream output
        if stream_env := os.environ.get(f"{self.ENV_PREFIX}STREAM_OUTPUT"):
            config_data["stream_output"] = stream_env.lower() in ("true", "1", "yes")

        # Verbose
        if verbose_env := os.environ.get(f"{self.ENV_PREFIX}VERBOSE"):
            config_data["verbose"] = verbose_env.lower() in ("true", "1", "yes")

        return config_data

    def save(self, config: LLMCliConfig) -> None:
        """Save configuration to file.

        Args:
            config: Configuration to save
        """
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Sanitize - remove sensitive data
        save_data = config.to_dict()
        for provider_config in save_data.get("providers", {}).values():
            if provider_config.get("api_key"):
                provider_config["api_key"] = "***"

        # Write file
        content: str
        if self.config_path.suffix in (".yaml", ".yml"):
            import yaml
            content = yaml.dump(save_data, default_flow_style=False, allow_unicode=True)
        else:
            content = json.dumps(save_data, indent=2, ensure_ascii=False)

        self.config_path.write_text(content, encoding="utf-8")
        self._config = config

    def get(self) -> LLMCliConfig:
        """Get current configuration, loading if necessary.

        Returns:
            LLMCliConfig: Current configuration
        """
        if self._config is None:
            return self.load()
        return self._config

    def set_provider(self, provider: str, config: ProviderConfig) -> None:
        """Set provider configuration.

        Args:
            provider: Provider name
            config: Provider configuration
        """
        current = self.get()
        current.providers[provider] = config
        self._config = current

    def set_default_provider(self, provider: str) -> None:
        """Set default provider.

        Args:
            provider: Provider name
        """
        current = self.get()
        current.default_provider = provider
        self._config = current


def create_llm_cli_config() -> LLMCliConfig:
    """Create default LLM CLI configuration.

    Returns:
        LLMCliConfig: Default configuration
    """
    return LLMCliConfig()


def load_llm_cli_config(config_path: str | None = None) -> LLMCliConfig:
    """Load LLM CLI configuration.

    Args:
        config_path: Optional path to configuration file

    Returns:
        LLMCliConfig: Loaded configuration
    """
    manager = LLMCliConfigManager(config_path)
    return manager.load()