"""
多模型支持模块

提供模型能力检测、智能选择和回退机制。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class ModelCapability(Enum):
    """模型能力枚举"""
    CHAT = "chat"                     # 基础对话
    CODE_GENERATION = "code_gen"      # 代码生成
    CODE_REVIEW = "code_review"       # 代码审查
    FUNCTION_CALL = "function_call"   # 函数调用
    VISION = "vision"                 # 图像理解
    STREAMING = "streaming"           # 流式输出
    LONG_CONTEXT = "long_context"     # 长上下文
    REASONING = "reasoning"           # 推理能力


class TaskType(Enum):
    """任务类型枚举"""
    CHAT = "chat"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    ERROR_DIAGNOSIS = "error_diagnosis"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    TESTING = "testing"


@dataclass
class ModelInfo:
    """模型信息"""
    provider: str
    model: str
    capabilities: list[ModelCapability] = field(default_factory=list)
    max_tokens: int = 4096
    context_window: int = 8192
    supports_streaming: bool = True
    supports_vision: bool = False
    cost_per_1k_tokens: float = 0.0
    priority: int = 0  # 优先级，数值越高优先级越高
    tags: list[str] = field(default_factory=list)

    def has_capability(self, capability: ModelCapability) -> bool:
        """检查是否具备某能力"""
        return capability in self.capabilities

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "capabilities": [c.value for c in self.capabilities],
            "max_tokens": self.max_tokens,
            "context_window": self.context_window,
            "supports_streaming": self.supports_streaming,
            "supports_vision": self.supports_vision,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
            "priority": self.priority,
            "tags": self.tags,
        }


@dataclass
class ModelSelectionResult:
    """模型选择结果"""
    selected_model: ModelInfo
    fallback_chain: list[ModelInfo] = field(default_factory=list)
    reason: str = ""
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_model": self.selected_model.to_dict(),
            "fallback_chain": [m.to_dict() for m in self.fallback_chain],
            "reason": self.reason,
            "confidence": self.confidence,
        }


class ModelRegistry:
    """
    模型注册表

    管理所有可用模型的信息和能力。
    """

    def __init__(self) -> None:
        self._models: dict[str, ModelInfo] = {}
        self._provider_models: dict[str, list[str]] = {}
        self._capability_index: dict[ModelCapability, list[str]] = {}
        self._initialize_default_models()

    def _initialize_default_models(self) -> None:
        """初始化默认模型配置"""
        # OpenAI 模型
        self.register(ModelInfo(
            provider="openai",
            model="gpt-4o",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.CODE_GENERATION,
                ModelCapability.CODE_REVIEW,
                ModelCapability.FUNCTION_CALL,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
                ModelCapability.LONG_CONTEXT,
                ModelCapability.REASONING,
            ],
            max_tokens=16384,
            context_window=128000,
            supports_streaming=True,
            supports_vision=True,
            cost_per_1k_tokens=0.005,
            priority=100,
            tags=["premium", "multimodal", "latest"],
        ))

        self.register(ModelInfo(
            provider="openai",
            model="gpt-4o-mini",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.CODE_GENERATION,
                ModelCapability.CODE_REVIEW,
                ModelCapability.FUNCTION_CALL,
                ModelCapability.STREAMING,
            ],
            max_tokens=16384,
            context_window=128000,
            supports_streaming=True,
            supports_vision=False,
            cost_per_1k_tokens=0.00015,
            priority=80,
            tags=["fast", "cost-effective"],
        ))

        self.register(ModelInfo(
            provider="openai",
            model="gpt-4-turbo",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.CODE_GENERATION,
                ModelCapability.CODE_REVIEW,
                ModelCapability.FUNCTION_CALL,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
                ModelCapability.LONG_CONTEXT,
            ],
            max_tokens=4096,
            context_window=128000,
            supports_streaming=True,
            supports_vision=True,
            cost_per_1k_tokens=0.01,
            priority=90,
            tags=["premium", "multimodal"],
        ))

        # Anthropic 模型
        self.register(ModelInfo(
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.CODE_GENERATION,
                ModelCapability.CODE_REVIEW,
                ModelCapability.STREAMING,
                ModelCapability.LONG_CONTEXT,
                ModelCapability.REASONING,
            ],
            max_tokens=8192,
            context_window=200000,
            supports_streaming=True,
            supports_vision=False,
            cost_per_1k_tokens=0.003,
            priority=95,
            tags=["premium", "reasoning", "latest"],
        ))

        self.register(ModelInfo(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.CODE_GENERATION,
                ModelCapability.CODE_REVIEW,
                ModelCapability.STREAMING,
                ModelCapability.LONG_CONTEXT,
            ],
            max_tokens=8192,
            context_window=200000,
            supports_streaming=True,
            supports_vision=False,
            cost_per_1k_tokens=0.003,
            priority=85,
            tags=["premium", "reasoning"],
        ))

        self.register(ModelInfo(
            provider="anthropic",
            model="claude-3-5-haiku-20241022",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.CODE_GENERATION,
                ModelCapability.STREAMING,
            ],
            max_tokens=8192,
            context_window=200000,
            supports_streaming=True,
            supports_vision=False,
            cost_per_1k_tokens=0.00025,
            priority=70,
            tags=["fast", "cost-effective"],
        ))

        # Gemini 模型
        self.register(ModelInfo(
            provider="gemini",
            model="gemini-1.5-pro",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.CODE_GENERATION,
                ModelCapability.CODE_REVIEW,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
                ModelCapability.LONG_CONTEXT,
            ],
            max_tokens=8192,
            context_window=1000000,
            supports_streaming=True,
            supports_vision=True,
            cost_per_1k_tokens=0.00125,
            priority=88,
            tags=["premium", "long-context", "multimodal"],
        ))

        self.register(ModelInfo(
            provider="gemini",
            model="gemini-1.5-flash",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.CODE_GENERATION,
                ModelCapability.STREAMING,
            ],
            max_tokens=8192,
            context_window=1000000,
            supports_streaming=True,
            supports_vision=False,
            cost_per_1k_tokens=0.000075,
            priority=75,
            tags=["fast", "cost-effective", "long-context"],
        ))

        # Ollama 本地模型
        self.register(ModelInfo(
            provider="ollama",
            model="llama3.1",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.CODE_GENERATION,
                ModelCapability.STREAMING,
            ],
            max_tokens=4096,
            context_window=128000,
            supports_streaming=True,
            supports_vision=False,
            cost_per_1k_tokens=0.0,
            priority=60,
            tags=["local", "free"],
        ))

        self.register(ModelInfo(
            provider="ollama",
            model="deepseek-coder",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.CODE_GENERATION,
                ModelCapability.CODE_REVIEW,
                ModelCapability.STREAMING,
            ],
            max_tokens=16384,
            context_window=128000,
            supports_streaming=True,
            supports_vision=False,
            cost_per_1k_tokens=0.0,
            priority=65,
            tags=["local", "free", "code-specialized"],
        ))

        # Mock 模型（测试用）
        self.register(ModelInfo(
            provider="mock",
            model="mock-default",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.CODE_GENERATION,
                ModelCapability.CODE_REVIEW,
                ModelCapability.STREAMING,
            ],
            max_tokens=4096,
            context_window=8192,
            supports_streaming=True,
            supports_vision=False,
            cost_per_1k_tokens=0.0,
            priority=0,
            tags=["test", "mock"],
        ))

    def register(self, model_info: ModelInfo) -> None:
        """
        注册模型

        Args:
            model_info: 模型信息
        """
        key = f"{model_info.provider}:{model_info.model}"
        self._models[key] = model_info

        # 更新提供商索引
        if model_info.provider not in self._provider_models:
            self._provider_models[model_info.provider] = []
        if model_info.model not in self._provider_models[model_info.provider]:
            self._provider_models[model_info.provider].append(model_info.model)

        # 更新能力索引
        for capability in model_info.capabilities:
            if capability not in self._capability_index:
                self._capability_index[capability] = []
            if key not in self._capability_index[capability]:
                self._capability_index[capability].append(key)

    def get_model(self, provider: str, model: str) -> ModelInfo | None:
        """获取模型信息"""
        key = f"{provider}:{model}"
        return self._models.get(key)

    def get_models_by_provider(self, provider: str) -> list[ModelInfo]:
        """获取提供商的所有模型"""
        model_names = self._provider_models.get(provider, [])
        models = []
        for name in model_names:
            model = self.get_model(provider, name)
            if model:
                models.append(model)
        return models

    def get_models_by_capability(self, capability: ModelCapability) -> list[ModelInfo]:
        """获取具备某能力的所有模型"""
        keys = self._capability_index.get(capability, [])
        models = []
        for key in keys:
            if key in self._models:
                models.append(self._models[key])
        # 按优先级排序
        return sorted(models, key=lambda m: m.priority, reverse=True)

    def get_all_models(self) -> list[ModelInfo]:
        """获取所有模型"""
        return list(self._models.values())

    def list_providers(self) -> list[str]:
        """列出所有提供商"""
        return list(self._provider_models.keys())


class ModelSelector:
    """
    智能模型选择器

    根据任务类型和要求智能选择最佳模型。
    """

    # 任务类型到所需能力的映射
    TASK_CAPABILITY_MAP: dict[TaskType, list[ModelCapability]] = {
        TaskType.CHAT: [ModelCapability.CHAT],
        TaskType.CODE_GENERATION: [ModelCapability.CODE_GENERATION, ModelCapability.CHAT],
        TaskType.CODE_REVIEW: [ModelCapability.CODE_REVIEW, ModelCapability.CHAT],
        TaskType.ERROR_DIAGNOSIS: [ModelCapability.REASONING, ModelCapability.CHAT],
        TaskType.DOCUMENTATION: [ModelCapability.CHAT],
        TaskType.REFACTORING: [ModelCapability.CODE_GENERATION, ModelCapability.CHAT],
        TaskType.TESTING: [ModelCapability.CODE_GENERATION, ModelCapability.CHAT],
    }

    def __init__(self, registry: ModelRegistry | None = None) -> None:
        self.registry = registry or ModelRegistry()
        self._custom_rules: list[Callable[[TaskType, dict[str, Any]], str | None]] = []

    def add_custom_rule(
        self,
        rule: Callable[[TaskType, dict[str, Any]], str | None],
    ) -> None:
        """
        添加自定义选择规则

        Args:
            rule: 规则函数，接受任务类型和上下文，返回模型 key 或 None
        """
        self._custom_rules.append(rule)

    def select(
        self,
        task_type: TaskType,
        context: dict[str, Any] | None = None,
        preferred_provider: str | None = None,
        max_cost: float | None = None,
        require_capabilities: list[ModelCapability] | None = None,
    ) -> ModelSelectionResult:
        """
        选择最佳模型

        Args:
            task_type: 任务类型
            context: 任务上下文
            preferred_provider: 首选提供商
            max_cost: 最大成本（每 1k tokens）
            require_capabilities: 必须具备的能力

        Returns:
            ModelSelectionResult: 选择结果
        """
        context = context or {}

        # 尝试自定义规则
        for rule in self._custom_rules:
            result_key = rule(task_type, context)
            if result_key:
                model_info = self.registry._models.get(result_key)
                if model_info:
                    return ModelSelectionResult(
                        selected_model=model_info,
                        reason=f"Custom rule selected: {result_key}",
                        confidence=1.0,
                    )

        # 获取所需能力
        required_caps = self.TASK_CAPABILITY_MAP.get(task_type, [ModelCapability.CHAT])
        if require_capabilities:
            required_caps = list(set(required_caps + require_capabilities))

        # 筛选候选模型
        candidates = self._filter_candidates(
            required_caps=required_caps,
            preferred_provider=preferred_provider,
            max_cost=max_cost,
            context=context,
        )

        if not candidates:
            # 无候选模型，返回默认 mock
            mock_model = self.registry.get_model("mock", "mock-default")
            if mock_model:
                return ModelSelectionResult(
                    selected_model=mock_model,
                    reason="No suitable model found, using mock",
                    confidence=0.0,
                )
            raise ValueError("No suitable model found")

        # 选择最佳模型
        best_model = candidates[0]
        fallback_chain = candidates[1:4] if len(candidates) > 1 else []

        reason = self._build_selection_reason(best_model, task_type, context)

        return ModelSelectionResult(
            selected_model=best_model,
            fallback_chain=fallback_chain,
            reason=reason,
            confidence=self._calculate_confidence(best_model, task_type),
        )

    def _filter_candidates(
        self,
        required_caps: list[ModelCapability],
        preferred_provider: str | None,
        max_cost: float | None,
        context: dict[str, Any],
    ) -> list[ModelInfo]:
        """筛选候选模型"""
        candidates = []

        for model_info in self.registry.get_all_models():
            # 检查能力
            if not all(model_info.has_capability(cap) for cap in required_caps):
                continue

            # 检查提供商偏好
            if preferred_provider and model_info.provider != preferred_provider:
                # 首选提供商的模型优先级提高
                pass  # 仍然加入候选，但排序时优先

            # 检查成本
            if max_cost is not None and model_info.cost_per_1k_tokens > max_cost:
                continue

            # 检查上下文长度
            estimated_tokens = context.get("estimated_tokens", 0)
            if estimated_tokens > model_info.context_window:
                continue

            candidates.append(model_info)

        # 排序：首选提供商 > 优先级 > 成本
        def sort_key(m: ModelInfo) -> tuple[int, int, float]:
            provider_bonus = 1000 if m.provider == preferred_provider else 0
            return (-provider_bonus - m.priority, 0, m.cost_per_1k_tokens)

        candidates.sort(key=sort_key)
        return candidates

    def _build_selection_reason(
        self,
        model: ModelInfo,
        task_type: TaskType,
        context: dict[str, Any],
    ) -> str:
        """构建选择原因"""
        reasons = []

        reasons.append(f"Selected {model.provider}/{model.model}")

        # 能力匹配
        caps = self.TASK_CAPABILITY_MAP.get(task_type, [])
        matched_caps = [c.value for c in caps if model.has_capability(c)]
        if matched_caps:
            reasons.append(f"Capabilities: {', '.join(matched_caps)}")

        # 成本优势
        if model.cost_per_1k_tokens == 0:
            reasons.append("Free to use")
        elif model.cost_per_1k_tokens < 0.001:
            reasons.append("Cost-effective")

        # 上下文优势
        if model.context_window >= 100000:
            reasons.append(f"Large context ({model.context_window // 1000}k)")

        return "; ".join(reasons)

    def _calculate_confidence(
        self,
        model: ModelInfo,
        task_type: TaskType,
    ) -> float:
        """计算选择置信度"""
        base_confidence = 0.5

        # 能力匹配加分
        required_caps = self.TASK_CAPABILITY_MAP.get(task_type, [])
        matched_count = sum(1 for cap in required_caps if model.has_capability(cap))
        if required_caps:
            base_confidence += 0.3 * (matched_count / len(required_caps))

        # 优先级加分
        base_confidence += min(0.2, model.priority / 500)

        return min(1.0, base_confidence)


class ModelFallbackManager:
    """
    模型回退管理器

    处理模型调用失败时的回退逻辑。
    """

    def __init__(
        self,
        selector: ModelSelector | None = None,
        max_retries: int = 3,
    ) -> None:
        self.selector = selector or ModelSelector()
        self.max_retries = max_retries
        self._failure_counts: dict[str, int] = {}
        self._circuit_breaker: dict[str, bool] = {}
        self._circuit_breaker_threshold = 5

    def execute_with_fallback(
        self,
        task_type: TaskType,
        execute_fn: Callable[[ModelInfo], Any],
        context: dict[str, Any] | None = None,
    ) -> tuple[Any, ModelInfo]:
        """
        执行任务，支持回退

        Args:
            task_type: 任务类型
            execute_fn: 执行函数，接受 ModelInfo，返回结果
            context: 任务上下文

        Returns:
            tuple[Any, ModelInfo]: 结果和使用的模型

        Raises:
            Exception: 所有模型都失败时抛出最后一个异常
        """
        selection_result = self.selector.select(task_type, context)
        models_to_try = [selection_result.selected_model] + selection_result.fallback_chain

        last_exception: Exception | None = None

        for model in models_to_try:
            model_key = f"{model.provider}:{model.model}"

            # 检查熔断器
            if self._circuit_breaker.get(model_key, False):
                continue

            try:
                result = execute_fn(model)
                # 成功，重置失败计数
                self._failure_counts[model_key] = 0
                return result, model
            except Exception as e:
                last_exception = e
                self._record_failure(model_key)

        # 所有模型都失败
        if last_exception:
            raise last_exception
        raise RuntimeError("No models available for fallback")

    async def execute_with_fallback_async(
        self,
        task_type: TaskType,
        execute_fn: Callable[[ModelInfo], Any],
        context: dict[str, Any] | None = None,
    ) -> tuple[Any, ModelInfo]:
        """
        异步执行任务，支持回退

        Args:
            task_type: 任务类型
            execute_fn: 异步执行函数
            context: 任务上下文

        Returns:
            tuple[Any, ModelInfo]: 结果和使用的模型
        """
        import asyncio

        selection_result = self.selector.select(task_type, context)
        models_to_try = [selection_result.selected_model] + selection_result.fallback_chain

        last_exception: Exception | None = None

        for model in models_to_try:
            model_key = f"{model.provider}:{model.model}"

            # 检查熔断器
            if self._circuit_breaker.get(model_key, False):
                continue

            try:
                if asyncio.iscoroutinefunction(execute_fn):
                    result = await execute_fn(model)
                else:
                    result = execute_fn(model)
                # 成功，重置失败计数
                self._failure_counts[model_key] = 0
                return result, model
            except Exception as e:
                last_exception = e
                self._record_failure(model_key)

        if last_exception:
            raise last_exception
        raise RuntimeError("No models available for fallback")

    def _record_failure(self, model_key: str) -> None:
        """记录失败"""
        self._failure_counts[model_key] = self._failure_counts.get(model_key, 0) + 1

        # 触发熔断器
        if self._failure_counts[model_key] >= self._circuit_breaker_threshold:
            self._circuit_breaker[model_key] = True

    def reset_circuit_breaker(self, model_key: str | None = None) -> None:
        """重置熔断器"""
        if model_key:
            self._circuit_breaker[model_key] = False
            self._failure_counts[model_key] = 0
        else:
            self._circuit_breaker.clear()
            self._failure_counts.clear()

    def get_failure_stats(self) -> dict[str, int]:
        """获取失败统计"""
        return dict(self._failure_counts)


# 便捷函数
_model_registry: ModelRegistry | None = None
_model_selector: ModelSelector | None = None


def get_model_registry() -> ModelRegistry:
    """获取模型注册表单例"""
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry()
    return _model_registry


def get_model_selector() -> ModelSelector:
    """获取模型选择器单例"""
    global _model_selector
    if _model_selector is None:
        _model_selector = ModelSelector(get_model_registry())
    return _model_selector


def select_model(
    task_type: TaskType,
    context: dict[str, Any] | None = None,
    **kwargs: Any,
) -> ModelSelectionResult:
    """
    选择最佳模型

    Args:
        task_type: 任务类型
        context: 任务上下文
        **kwargs: 其他参数

    Returns:
        ModelSelectionResult: 选择结果
    """
    return get_model_selector().select(task_type, context, **kwargs)