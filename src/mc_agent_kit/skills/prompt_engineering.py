"""
提示工程优化模块

提供提示模板系统、Few-shot Learning、Chain-of-Thought 提示等功能。
"""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# 导入 LLM 集成模块
from mc_agent_kit.skills.llm_integration import (
    ChatMessage,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    LLMService,
    MessageRole,
)


class PromptTemplateType(Enum):
    """提示模板类型"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    CHAT = "chat"
    COMPLETION = "completion"


class ReasoningType(Enum):
    """推理类型"""
    NONE = "none"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHT = "tree_of_thought"
    STEP_BY_STEP = "step_by_step"


@dataclass
class PromptTemplate:
    """提示模板"""
    name: str
    template: str
    description: str
    template_type: PromptTemplateType
    variables: list[str] = field(default_factory=list)
    examples: list[dict[str, str]] = field(default_factory=list)
    reasoning_type: ReasoningType = ReasoningType.NONE
    metadata: dict[str, Any] = field(default_factory=dict)

    def render(self, **kwargs: Any) -> str:
        """渲染模板"""
        result = self.template
        for key, value in kwargs.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result


@dataclass
class FewShotExample:
    """Few-shot 示例"""
    input: str
    output: str
    explanation: Optional[str] = None

    def format(self, include_explanation: bool = True) -> str:
        """格式化示例"""
        result = f"输入: {self.input}\n输出: {self.output}"
        if include_explanation and self.explanation:
            result = f"{result}\n解释: {self.explanation}"
        return result


@dataclass
class FewShotConfig:
    """Few-shot 配置"""
    examples: list[FewShotExample] = field(default_factory=list)
    max_examples: int = 5
    include_explanations: bool = True
    example_separator: str = "\n\n"

    def build_prompt_section(self) -> str:
        """构建示例部分"""
        if not self.examples:
            return ""

        formatted_examples = []
        for example in self.examples[:self.max_examples]:
            formatted_examples.append(example.format(self.include_explanations))

        return self.example_separator.join(formatted_examples)


@dataclass
class ChainOfThoughtConfig:
    """Chain-of-Thought 配置"""
    enabled: bool = True
    show_reasoning: bool = True
    reasoning_prompt: str = "让我们一步步思考："
    final_answer_prompt: str = "因此，最终答案是："


@dataclass
class PromptOptimizationResult:
    """提示优化结果"""
    optimized_prompt: str
    original_length: int
    optimized_length: int
    compression_ratio: float
    techniques_applied: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


class PromptTemplateRegistry:
    """提示模板注册表"""

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}
        self._lock = threading.Lock()
        self._init_default_templates()

    def _init_default_templates(self) -> None:
        """初始化默认模板"""
        templates = [
            # ModSDK 代码生成模板
            PromptTemplate(
                name="modsdk_entity_create",
                template="""你是一个 Minecraft 网易版 ModSDK 开发专家。

请根据以下需求创建一个自定义实体：

实体名称: {{entity_name}}
实体类型: {{entity_type}}
行为模式: {{behavior}}

请生成：
1. 实体定义代码
2. 实体行为逻辑
3. 事件监听器

确保代码符合 ModSDK Python 2.7 语法规范。""",
                description="创建 ModSDK 自定义实体",
                template_type=PromptTemplateType.USER,
                variables=["entity_name", "entity_type", "behavior"],
            ),
            PromptTemplate(
                name="modsdk_item_create",
                template="""你是一个 Minecraft 网易版 ModSDK 开发专家。

请根据以下需求创建一个自定义物品：

物品名称: {{item_name}}
物品类型: {{item_type}}
特殊效果: {{effect}}

请生成：
1. 物品注册代码
2. 物品使用逻辑
3. 相关事件处理

确保代码符合 ModSDK Python 2.7 语法规范。""",
                description="创建 ModSDK 自定义物品",
                template_type=PromptTemplateType.USER,
                variables=["item_name", "item_type", "effect"],
            ),
            PromptTemplate(
                name="modsdk_block_create",
                template="""你是一个 Minecraft 网易版 ModSDK 开发专家。

请根据以下需求创建一个自定义方块：

方块名称: {{block_name}}
方块类型: {{block_type}}
交互行为: {{interaction}}

请生成：
1. 方块定义代码
2. 方块交互逻辑
3. 相关事件处理

确保代码符合 ModSDK Python 2.7 语法规范。""",
                description="创建 ModSDK 自定义方块",
                template_type=PromptTemplateType.USER,
                variables=["block_name", "block_type", "interaction"],
            ),
            PromptTemplate(
                name="modsdk_event_listener",
                template="""你是一个 Minecraft 网易版 ModSDK 开发专家。

请创建一个事件监听器：

事件类型: {{event_type}}
触发条件: {{trigger_condition}}
处理逻辑: {{handler_logic}}

请生成完整的事件监听代码，包括：
1. 事件注册
2. 回调函数
3. 数据处理

确保代码符合 ModSDK Python 2.7 语法规范。""",
                description="创建 ModSDK 事件监听器",
                template_type=PromptTemplateType.USER,
                variables=["event_type", "trigger_condition", "handler_logic"],
            ),
            # 代码修复模板
            PromptTemplate(
                name="code_fix",
                template="""你是一个 Minecraft 网易版 ModSDK 代码专家。

以下代码存在问题：

原始代码:
```python
{{original_code}}
```

错误信息:
{{error_message}}

请分析问题并提供修复后的代码。

修复要求：
1. 保持原有功能
2. 符合 ModSDK Python 2.7 语法
3. 添加必要的错误处理
4. 保持代码风格一致""",
                description="修复 ModSDK 代码",
                template_type=PromptTemplateType.USER,
                variables=["original_code", "error_message"],
            ),
            # 代码解释模板
            PromptTemplate(
                name="code_explain",
                template="""请解释以下 ModSDK 代码的功能：

```python
{{code}}
```

请提供：
1. 代码功能概述
2. 关键函数/方法说明
3. 使用的 ModSDK API 说明
4. 使用示例

解释应当清晰易懂，适合初学者阅读。""",
                description="解释 ModSDK 代码",
                template_type=PromptTemplateType.USER,
                variables=["code"],
            ),
            # 系统提示模板
            PromptTemplate(
                name="system_modsdk_expert",
                template="""你是一个 Minecraft 网易版 ModSDK 开发专家。

你的职责是：
1. 帮助开发者编写 ModSDK Addon 代码
2. 解释 ModSDK API 和事件
3. 调试和修复代码问题
4. 提供最佳实践建议

注意事项：
- ModSDK 使用 Python 2.7 语法
- 代码在游戏进程中运行
- 需要考虑性能和稳定性
- 遵循 ModSDK 开发规范

回答时请：
1. 提供完整的代码示例
2. 解释关键概念
3. 指出潜在问题
4. 给出改进建议""",
                description="ModSDK 专家系统提示",
                template_type=PromptTemplateType.SYSTEM,
                variables=[],
            ),
        ]

        for template in templates:
            self._templates[template.name] = template

    def register(self, template: PromptTemplate) -> None:
        """注册模板"""
        with self._lock:
            self._templates[template.name] = template

    def get(self, name: str) -> Optional[PromptTemplate]:
        """获取模板"""
        return self._templates.get(name)

    def list_templates(self) -> list[str]:
        """列出所有模板名称"""
        return list(self._templates.keys())

    def render(self, name: str, **kwargs: Any) -> str:
        """渲染模板"""
        template = self.get(name)
        if not template:
            raise ValueError(f"Template not found: {name}")
        return template.render(**kwargs)


class FewShotLearner:
    """Few-shot 学习器"""

    def __init__(self, config: Optional[FewShotConfig] = None) -> None:
        self.config = config or FewShotConfig()
        self._example_bank: dict[str, list[FewShotExample]] = {}

    def add_example(
        self,
        category: str,
        example: FewShotExample,
    ) -> None:
        """添加示例"""
        if category not in self._example_bank:
            self._example_bank[category] = []
        self._example_bank[category].append(example)

    def add_examples(
        self,
        category: str,
        examples: list[FewShotExample],
    ) -> None:
        """批量添加示例"""
        for example in examples:
            self.add_example(category, example)

    def get_examples(
        self,
        category: str,
        max_count: Optional[int] = None,
    ) -> list[FewShotExample]:
        """获取示例"""
        examples = self._example_bank.get(category, [])
        max_count = max_count or self.config.max_examples
        return examples[:max_count]

    def build_few_shot_prompt(
        self,
        category: str,
        task_description: str,
        input_text: str,
    ) -> str:
        """构建 Few-shot 提示"""
        examples = self.get_examples(category)

        parts = [task_description]

        if examples:
            parts.append("\n以下是几个示例：\n")
            for example in examples:
                parts.append(example.format(self.config.include_explanations))
                parts.append(self.config.example_separator)

        parts.append(f"\n现在请处理：\n输入: {input_text}\n输出: ")

        return "".join(parts)

    def _init_default_examples(self) -> None:
        """初始化默认示例"""
        # 实体创建示例
        self.add_examples("entity_create", [
            FewShotExample(
                input="创建一个僵尸实体，在夜晚生成，有10点生命值",
                output='''def create_zombie_entity(pos):
    """创建僵尸实体"""
    entity_id = CreateEngineEntity(GetEngineType(), "minecraft:zombie", pos)
    if entity_id:
        SetEntityHp(entity_id, 10)
    return entity_id''',
                explanation="使用 CreateEngineEntity 创建实体，SetEntityHp 设置生命值",
            ),
        ])

        # 事件监听示例
        self.add_examples("event_listener", [
            FewShotExample(
                input="监听玩家加入事件，发送欢迎消息",
                output='''def OnPlayerJoin(args):
    player_id = args.get("playerId")
    name = GetPlayerName(player_id)
    print(f"欢迎 {name} 加入服务器!")

ListenEvent("OnAddServerPlayer", OnPlayerJoin)''',
                explanation="使用 ListenEvent 注册事件监听器",
            ),
        ])


class ChainOfThoughtPrompter:
    """Chain-of-Thought 提示器"""

    def __init__(self, config: Optional[ChainOfThoughtConfig] = None) -> None:
        self.config = config or ChainOfThoughtConfig()

    def build_cot_prompt(
        self,
        question: str,
        context: Optional[str] = None,
    ) -> str:
        """构建 CoT 提示"""
        parts = []

        if context:
            parts.append(f"背景信息:\n{context}\n")

        parts.append(f"问题: {question}\n")

        if self.config.show_reasoning:
            parts.append(f"\n{self.config.reasoning_prompt}\n")
            parts.append("1. 首先，分析问题的关键要素...\n")
            parts.append("2. 然后，考虑可能的解决方案...\n")
            parts.append("3. 最后，得出结论...\n")

        if self.config.final_answer_prompt:
            parts.append(f"\n{self.config.final_answer_prompt}")

        return "".join(parts)

    def extract_reasoning(self, response: str) -> dict[str, str]:
        """从响应中提取推理过程"""
        result = {
            "reasoning": "",
            "final_answer": "",
        }

        # 尝试分离推理和最终答案
        if self.config.final_answer_prompt in response:
            parts = response.split(self.config.final_answer_prompt)
            if len(parts) == 2:
                result["reasoning"] = parts[0].strip()
                result["final_answer"] = parts[1].strip()
        else:
            result["final_answer"] = response.strip()

        return result


class PromptOptimizer:
    """提示优化器"""

    def __init__(self) -> None:
        self._compression_patterns: list[tuple[str, str]] = [
            # 移除多余空格
            (r"\s+", " "),
            # 移除行首行尾空格
            (r"^\s+|\s+$", ""),
        ]

    def optimize(
        self,
        prompt: str,
        max_length: Optional[int] = None,
        preserve_structure: bool = True,
    ) -> PromptOptimizationResult:
        """优化提示"""
        original_length = len(prompt)
        techniques_applied: list[str] = []

        optimized = prompt

        # 1. 移除多余空白
        if not preserve_structure:
            optimized = re.sub(r"\s+", " ", optimized).strip()
            techniques_applied.append("whitespace_compression")

        # 2. 移除重复内容
        lines = optimized.split("\n")
        seen: set[str] = set()
        unique_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped and stripped not in seen:
                seen.add(stripped)
                unique_lines.append(line)
        if len(unique_lines) < len(lines):
            optimized = "\n".join(unique_lines)
            techniques_applied.append("duplicate_removal")

        # 3. 如果有长度限制，进行截断
        if max_length and len(optimized) > max_length:
            optimized = optimized[:max_length]
            techniques_applied.append("truncation")

        optimized_length = len(optimized)
        compression_ratio = (
            1 - (optimized_length / original_length)
            if original_length > 0 else 0
        )

        return PromptOptimizationResult(
            optimized_prompt=optimized,
            original_length=original_length,
            optimized_length=optimized_length,
            compression_ratio=compression_ratio,
            techniques_applied=techniques_applied,
        )

    def compress_context(
        self,
        context: str,
        target_length: int,
    ) -> str:
        """压缩上下文"""
        if len(context) <= target_length:
            return context

        # 简单截断，保留结尾
        return "..." + context[-(target_length - 3):]


class PromptEngineeringService:
    """提示工程服务

    整合提示模板、Few-shot Learning、CoT 等功能。

    使用示例:
        service = PromptEngineeringService()

        # 使用模板
        prompt = service.render_template("modsdk_entity_create",
            entity_name="FrostGhost",
            entity_type="monster",
            behavior="hostile"
        )

        # 使用 Few-shot
        prompt = service.build_few_shot_prompt("entity_create",
            "创建一个实体",
            "创建一个骷髅实体"
        )

        # 使用 CoT
        prompt = service.build_cot_prompt("如何优化这个代码?")
    """

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        few_shot_config: Optional[FewShotConfig] = None,
        cot_config: Optional[ChainOfThoughtConfig] = None,
    ) -> None:
        self.template_registry = PromptTemplateRegistry()
        self.few_shot_learner = FewShotLearner(few_shot_config)
        self.cot_prompter = ChainOfThoughtPrompter(cot_config)
        self.optimizer = PromptOptimizer()
        self._llm_service: Optional[LLMService] = None
        if llm_config:
            self._llm_service = LLMService(llm_config)

    def set_llm_service(self, llm_service: LLMService) -> None:
        """设置 LLM 服务"""
        self._llm_service = llm_service

    def render_template(self, name: str, **kwargs: Any) -> str:
        """渲染模板"""
        return self.template_registry.render(name, **kwargs)

    def build_few_shot_prompt(
        self,
        category: str,
        task_description: str,
        input_text: str,
    ) -> str:
        """构建 Few-shot 提示"""
        return self.few_shot_learner.build_few_shot_prompt(
            category, task_description, input_text,
        )

    def build_cot_prompt(
        self,
        question: str,
        context: Optional[str] = None,
    ) -> str:
        """构建 Chain-of-Thought 提示"""
        return self.cot_prompter.build_cot_prompt(question, context)

    def optimize_prompt(
        self,
        prompt: str,
        max_length: Optional[int] = None,
    ) -> PromptOptimizationResult:
        """优化提示"""
        return self.optimizer.optimize(prompt, max_length)

    def add_few_shot_example(
        self,
        category: str,
        input_text: str,
        output_text: str,
        explanation: Optional[str] = None,
    ) -> None:
        """添加 Few-shot 示例"""
        example = FewShotExample(
            input=input_text,
            output=output_text,
            explanation=explanation,
        )
        self.few_shot_learner.add_example(category, example)

    def execute_with_template(
        self,
        template_name: str,
        variables: dict[str, Any],
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """使用模板执行 LLM 调用"""
        if not self._llm_service:
            raise ValueError("LLM service not configured")

        prompt = self.render_template(template_name, **variables)

        messages = [ChatMessage(
            role=MessageRole.USER,
            content=prompt,
        )]

        return self._llm_service.chat(messages, system_prompt=system_prompt)

    def execute_with_few_shot(
        self,
        category: str,
        task_description: str,
        input_text: str,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """使用 Few-shot 执行 LLM 调用"""
        if not self._llm_service:
            raise ValueError("LLM service not configured")

        prompt = self.build_few_shot_prompt(
            category, task_description, input_text,
        )

        messages = [ChatMessage(
            role=MessageRole.USER,
            content=prompt,
        )]

        return self._llm_service.chat(messages, system_prompt=system_prompt)

    def execute_with_cot(
        self,
        question: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
        extract_reasoning: bool = True,
    ) -> dict[str, Any]:
        """使用 CoT 执行 LLM 调用"""
        if not self._llm_service:
            raise ValueError("LLM service not configured")

        prompt = self.build_cot_prompt(question, context)

        messages = [ChatMessage(
            role=MessageRole.USER,
            content=prompt,
        )]

        response = self._llm_service.chat(messages, system_prompt=system_prompt)

        result: dict[str, Any] = {
            "response": response,
        }

        if extract_reasoning:
            reasoning_result = self.cot_prompter.extract_reasoning(response.content)
            result["reasoning"] = reasoning_result["reasoning"]
            result["final_answer"] = reasoning_result["final_answer"]

        return result


# 全局实例
_prompt_service: Optional[PromptEngineeringService] = None


def get_prompt_service(
    llm_config: Optional[LLMConfig] = None,
) -> PromptEngineeringService:
    """获取提示工程服务实例"""
    global _prompt_service
    if llm_config or _prompt_service is None:
        _prompt_service = PromptEngineeringService(llm_config)
    return _prompt_service


def render_prompt(template_name: str, **kwargs: Any) -> str:
    """便捷函数：渲染提示模板"""
    return get_prompt_service().render_template(template_name, **kwargs)


def build_cot_prompt(question: str, context: Optional[str] = None) -> str:
    """便捷函数：构建 CoT 提示"""
    return get_prompt_service().build_cot_prompt(question, context)