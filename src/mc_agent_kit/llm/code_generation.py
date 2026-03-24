"""
智能代码生成模块

基于 LLM 的智能代码生成功能。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .base import (
    ChatMessage,
    CompletionResult,
    LLMConfig,
)
from .manager import LLMManager


class CodeGenerationType(Enum):
    """代码生成类型"""
    EVENT_LISTENER = "event_listener"
    ENTITY_BEHAVIOR = "entity_behavior"
    ITEM_LOGIC = "item_logic"
    UI_SCREEN = "ui_screen"
    NETWORK_SYNC = "network_sync"
    CONFIG_HANDLER = "config_handler"
    ERROR_HANDLER = "error_handler"
    CUSTOM = "custom"


@dataclass
class GenerationContext:
    """生成上下文"""
    project_name: str = ""
    module_name: str = ""
    description: str = ""
    imports: list[str] = field(default_factory=list)
    existing_code: str = ""
    style: str = "pep8"  # pep8, google, numpy
    target: str = "server"  # server, client, both

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "module_name": self.module_name,
            "description": self.description,
            "imports": self.imports,
            "existing_code": self.existing_code,
            "style": self.style,
            "target": self.target,
        }


@dataclass
class GeneratedCode:
    """生成的代码"""
    code: str
    language: str = "python"
    imports: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confidence: float = 0.0
    raw_result: CompletionResult | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "language": self.language,
            "imports": self.imports,
            "dependencies": self.dependencies,
            "notes": self.notes,
            "warnings": self.warnings,
            "confidence": self.confidence,
            "raw_result": self.raw_result.to_dict() if self.raw_result else None,
        }


class CodeGenerationPromptBuilder:
    """
    代码生成提示构建器

    构建用于 LLM 的代码生成提示。
    """

    @staticmethod
    def build_system_prompt() -> str:
        """构建系统提示"""
        return '''你是一个 Minecraft 网易版 ModSDK 开发专家。
你的任务是根据用户需求生成高质量的 Python 代码。

## 代码规范
1. 使用 Python 2.7 兼容语法（游戏内运行环境）
2. 遵循 PEP 8 代码风格
3. 添加必要的注释和文档字符串
4. 使用中文注释

## ModSDK 特性
1. 服务端导入: `import mod.server.extraServerApi as serverApi`
2. 客户端导入: `import mod.client.extraClientApi as clientApi`
3. 组件工厂: `comp_factory = serverApi.GetEngineCompFactory()`
4. 事件监听: `serverApi.ListenEvent("事件名", 回调函数)`

## 输出格式
只输出代码，不要有额外的解释。代码应该完整、可运行。'''

    @staticmethod
    def build_prompt(
        request: str,
        generation_type: CodeGenerationType,
        context: GenerationContext | None = None,
    ) -> str:
        """构建用户提示"""
        parts = []

        # 添加上下文
        if context:
            if context.project_name:
                parts.append(f"项目名称: {context.project_name}")
            if context.description:
                parts.append(f"项目描述: {context.description}")
            if context.target:
                parts.append(f"运行环境: {context.target}")
            if context.existing_code:
                parts.append(f"已有代码:\n```python\n{context.existing_code}\n```")

        # 添加具体需求
        parts.append(f"\n需求: {request}")

        # 根据生成类型添加特定提示
        type_hints = {
            CodeGenerationType.EVENT_LISTENER: "请生成事件监听相关代码，包括事件注册和处理函数。",
            CodeGenerationType.ENTITY_BEHAVIOR: "请生成实体行为相关代码，包括实体创建、属性设置和行为逻辑。",
            CodeGenerationType.ITEM_LOGIC: "请生成物品逻辑相关代码，包括物品注册、使用和交互逻辑。",
            CodeGenerationType.UI_SCREEN: "请生成 UI 界面相关代码，包括界面创建、控件绑定和事件处理。",
            CodeGenerationType.NETWORK_SYNC: "请生成网络同步相关代码，包括数据打包、发送和接收处理。",
            CodeGenerationType.CONFIG_HANDLER: "请生成配置处理相关代码，包括配置读取、验证和应用。",
            CodeGenerationType.ERROR_HANDLER: "请生成错误处理相关代码，包括异常捕获和日志记录。",
            CodeGenerationType.CUSTOM: "请根据需求生成相关代码。",
        }

        parts.append(f"\n{type_hints.get(generation_type, '')}")

        return "\n".join(parts)


class IntelligentCodeGenerator:
    """
    智能代码生成器

    基于 LLM 生成 ModSDK 代码。
    """

    def __init__(
        self,
        llm_config: LLMConfig | None = None,
    ) -> None:
        self.llm_config = llm_config or LLMConfig(provider="mock")
        self.llm_manager = LLMManager()
        self.prompt_builder = CodeGenerationPromptBuilder()

    def generate(
        self,
        request: str,
        generation_type: CodeGenerationType = CodeGenerationType.CUSTOM,
        context: GenerationContext | None = None,
        **kwargs: Any,
    ) -> GeneratedCode:
        """
        生成代码

        Args:
            request: 生成请求
            generation_type: 生成类型
            context: 生成上下文
            **kwargs: 额外参数

        Returns:
            GeneratedCode: 生成的代码
        """
        # 构建消息
        messages = [
            ChatMessage.system(self.prompt_builder.build_system_prompt()),
            ChatMessage.user(
                self.prompt_builder.build_prompt(request, generation_type, context)
            ),
        ]

        # 调用 LLM
        result = self.llm_manager.complete(messages, self.llm_config, **kwargs)

        # 解析结果
        code = self._extract_code(result.content)
        imports = self._extract_imports(code)
        dependencies = self._extract_dependencies(code)

        # 计算置信度
        confidence = self._calculate_confidence(code, generation_type)

        return GeneratedCode(
            code=code,
            imports=imports,
            dependencies=dependencies,
            notes=self._generate_notes(code, generation_type),
            warnings=self._generate_warnings(code),
            confidence=confidence,
            raw_result=result,
        )

    async def generate_async(
        self,
        request: str,
        generation_type: CodeGenerationType = CodeGenerationType.CUSTOM,
        context: GenerationContext | None = None,
        **kwargs: Any,
    ) -> GeneratedCode:
        """
        异步生成代码

        Args:
            request: 生成请求
            generation_type: 生成类型
            context: 生成上下文
            **kwargs: 额外参数

        Returns:
            GeneratedCode: 生成的代码
        """
        # 构建消息
        messages = [
            ChatMessage.system(self.prompt_builder.build_system_prompt()),
            ChatMessage.user(
                self.prompt_builder.build_prompt(request, generation_type, context)
            ),
        ]

        # 调用 LLM
        result = await self.llm_manager.complete_async(messages, self.llm_config, **kwargs)

        # 解析结果
        code = self._extract_code(result.content)
        imports = self._extract_imports(code)
        dependencies = self._extract_dependencies(code)

        # 计算置信度
        confidence = self._calculate_confidence(code, generation_type)

        return GeneratedCode(
            code=code,
            imports=imports,
            dependencies=dependencies,
            notes=self._generate_notes(code, generation_type),
            warnings=self._generate_warnings(code),
            confidence=confidence,
            raw_result=result,
        )

    def _extract_code(self, content: str) -> str:
        """从 LLM 响应中提取代码"""
        # 尝试提取代码块
        if "```python" in content:
            start = content.find("```python") + 9
            end = content.find("```", start)
            if end != -1:
                return content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end != -1:
                return content[start:end].strip()

        # 如果没有代码块，直接返回内容
        return content.strip()

    def _extract_imports(self, code: str) -> list[str]:
        """从代码中提取导入语句"""
        imports = []
        for line in code.split("\n"):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                imports.append(stripped)
        return imports

    def _extract_dependencies(self, code: str) -> list[str]:
        """从代码中提取依赖"""
        dependencies = []
        # ModSDK 特定依赖
        if "serverApi" in code:
            dependencies.append("mod.server.extraServerApi")
        if "clientApi" in code:
            dependencies.append("mod.client.extraClientApi")
        if "ListenEvent" in code:
            dependencies.append("事件系统")
        return dependencies

    def _calculate_confidence(
        self,
        code: str,
        generation_type: CodeGenerationType,
    ) -> float:
        """计算生成置信度"""
        if not code:
            return 0.0

        score = 0.5  # 基础分

        # 检查代码结构
        if "def " in code:
            score += 0.1
        if "import " in code or "from " in code:
            score += 0.1

        # 根据类型检查特定特征
        type_checks = {
            CodeGenerationType.EVENT_LISTENER: ["ListenEvent", "def on_", "args"],
            CodeGenerationType.ENTITY_BEHAVIOR: ["CreateEntity", "entity", "def "],
            CodeGenerationType.ITEM_LOGIC: ["item", "register", "use"],
            CodeGenerationType.UI_SCREEN: ["CreateScreen", "UI", "ui"],
            CodeGenerationType.NETWORK_SYNC: ["NotifyToClient", "NotifyToServer", "data"],
            CodeGenerationType.CONFIG_HANDLER: ["config", "load", "save"],
            CodeGenerationType.ERROR_HANDLER: ["try:", "except", "error"],
            CodeGenerationType.CUSTOM: [],
        }

        checks = type_checks.get(generation_type, [])
        for keyword in checks:
            if keyword in code:
                score += 0.05

        return min(1.0, score)

    def _generate_notes(
        self,
        code: str,
        generation_type: CodeGenerationType,
    ) -> list[str]:
        """生成代码说明"""
        notes = []

        if "serverApi" in code:
            notes.append("此代码需要在服务端运行")
        if "clientApi" in code:
            notes.append("此代码需要在客户端运行")

        if generation_type == CodeGenerationType.EVENT_LISTENER:
            notes.append("事件监听器已注册，请确保在合适的时机调用")
        elif generation_type == CodeGenerationType.ENTITY_BEHAVIOR:
            notes.append("实体行为需要在 tick 事件中驱动")
        elif generation_type == CodeGenerationType.UI_SCREEN:
            notes.append("UI 界面需要资源包支持")

        return notes

    def _generate_warnings(self, code: str) -> list[str]:
        """生成警告信息"""
        warnings = []

        # 检查潜在问题
        if "print(" in code:
            warnings.append("生产环境建议使用日志系统替代 print")

        if "global " in code:
            warnings.append("使用全局变量可能导致状态管理问题")

        if "# TODO" in code or "# FIXME" in code:
            warnings.append("代码中存在待完成的标记")

        return warnings


def generate_code(
    request: str,
    generation_type: CodeGenerationType = CodeGenerationType.CUSTOM,
    context: GenerationContext | None = None,
    llm_config: LLMConfig | None = None,
) -> GeneratedCode:
    """
    便捷函数：生成代码

    Args:
        request: 生成请求
        generation_type: 生成类型
        context: 生成上下文
        llm_config: LLM 配置

    Returns:
        GeneratedCode: 生成的代码
    """
    generator = IntelligentCodeGenerator(llm_config)
    return generator.generate(request, generation_type, context)