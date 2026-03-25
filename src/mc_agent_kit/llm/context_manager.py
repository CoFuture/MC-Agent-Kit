"""
上下文增强模块

提供对话上下文管理和代码上下文理解能力。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .base import ChatMessage, ChatRole


class ContextType(Enum):
    """上下文类型"""
    CONVERSATION = "conversation"   # 对话上下文
    CODE = "code"                   # 代码上下文
    PROJECT = "project"             # 项目上下文
    ERROR = "error"                 # 错误上下文


@dataclass
class ContextMessage:
    """上下文消息"""
    role: ChatRole
    content: str
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_chat_message(self) -> ChatMessage:
        """转换为 ChatMessage"""
        return ChatMessage(role=self.role, content=self.content)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextMessage:
        """从字典创建"""
        return cls(
            role=ChatRole(data["role"]),
            content=data["content"],
            timestamp=data.get("timestamp", 0.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ContextSummary:
    """上下文摘要"""
    key_points: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    apis: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key_points": self.key_points,
            "entities": self.entities,
            "apis": self.apis,
            "events": self.events,
            "decisions": self.decisions,
            "issues": self.issues,
        }

    def to_prompt(self) -> str:
        """转换为提示文本"""
        parts = []

        if self.key_points:
            parts.append("关键点:")
            for point in self.key_points:
                parts.append(f"  - {point}")

        if self.entities:
            parts.append(f"涉及的实体: {', '.join(self.entities)}")

        if self.apis:
            parts.append(f"使用的 API: {', '.join(self.apis)}")

        if self.events:
            parts.append(f"监听的事件: {', '.join(self.events)}")

        if self.decisions:
            parts.append("已做出的决策:")
            for decision in self.decisions:
                parts.append(f"  - {decision}")

        if self.issues:
            parts.append("待解决的问题:")
            for issue in self.issues:
                parts.append(f"  - {issue}")

        return "\n".join(parts) if parts else ""


@dataclass
class ContextWindow:
    """上下文窗口"""
    max_messages: int = 20
    max_tokens: int = 4000
    messages: list[ContextMessage] = field(default_factory=list)
    summary: ContextSummary = field(default_factory=ContextSummary)

    def add_message(self, message: ContextMessage) -> None:
        """添加消息"""
        import time
        message.timestamp = time.time()
        self.messages.append(message)

        # 检查是否需要压缩
        if len(self.messages) > self.max_messages:
            self._compress()

    def _compress(self) -> None:
        """压缩上下文"""
        if len(self.messages) <= self.max_messages:
            return

        # 保留最近的消息
        keep_count = self.max_messages // 2
        old_messages = self.messages[:-keep_count]
        self.messages = self.messages[-keep_count:]

        # 更新摘要
        self._update_summary(old_messages)

    def _update_summary(self, messages: list[ContextMessage]) -> None:
        """更新摘要"""
        for msg in messages:
            content = msg.content.lower()

            # 提取实体
            if "实体" in content or "entity" in content:
                self.summary.entities.append("entity")

            # 提取 API
            if "create" in content:
                self.summary.apis.append("Create*")
            if "listen" in content or "监听" in content:
                self.summary.apis.append("ListenEvent")

            # 提取事件
            if "事件" in content or "event" in content:
                self.summary.events.append("OnServer*")

            # 提取决策
            if msg.role == ChatRole.ASSISTANT:
                key_points = self._extract_key_points(msg.content)
                self.summary.key_points.extend(key_points[:2])

        # 去重
        self.summary.entities = list(set(self.summary.entities))
        self.summary.apis = list(set(self.summary.apis))
        self.summary.events = list(set(self.summary.events))
        self.summary.key_points = list(set(self.summary.key_points))[:10]

    def _extract_key_points(self, content: str) -> list[str]:
        """提取关键点"""
        key_points = []
        sentences = content.replace("。", ".").replace("！", "!").replace("？", "?").split(".")
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and len(sentence) < 100:
                key_points.append(sentence)
        return key_points[:3]

    def get_chat_messages(self) -> list[ChatMessage]:
        """获取 ChatMessage 列表"""
        return [msg.to_chat_message() for msg in self.messages]

    def get_context_prompt(self) -> str:
        """获取上下文提示"""
        summary_prompt = self.summary.to_prompt()
        if not summary_prompt:
            return ""

        return f"""## 上下文摘要

{summary_prompt}

## 最近对话

以下是对话历史，请参考这些信息继续对话。"""


class ConversationManager:
    """
    对话管理器

    管理多轮对话的上下文。
    """

    def __init__(
        self,
        max_messages: int = 20,
        max_tokens: int = 4000,
    ) -> None:
        self.window = ContextWindow(
            max_messages=max_messages,
            max_tokens=max_tokens,
        )

    def add_user_message(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """添加用户消息"""
        msg = ContextMessage(
            role=ChatRole.USER,
            content=content,
            metadata=metadata or {},
        )
        self.window.add_message(msg)

    def add_assistant_message(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """添加助手消息"""
        msg = ContextMessage(
            role=ChatRole.ASSISTANT,
            content=content,
            metadata=metadata or {},
        )
        self.window.add_message(msg)

    def add_system_message(self, content: str) -> None:
        """添加系统消息"""
        msg = ContextMessage(
            role=ChatRole.SYSTEM,
            content=content,
        )
        self.window.add_message(msg)

    def get_messages(self) -> list[ChatMessage]:
        """获取消息列表"""
        return self.window.get_chat_messages()

    def get_context_prompt(self) -> str:
        """获取上下文提示"""
        return self.window.get_context_prompt()

    def get_summary(self) -> ContextSummary:
        """获取摘要"""
        return self.window.summary

    def clear(self) -> None:
        """清空对话"""
        self.window = ContextWindow(
            max_messages=self.window.max_messages,
            max_tokens=self.window.max_tokens,
        )

    def save(self, path: str) -> None:
        """保存对话"""
        import json

        data = {
            "messages": [msg.to_dict() for msg in self.window.messages],
            "summary": self.window.summary.to_dict(),
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path: str) -> None:
        """加载对话"""
        import json
        import os

        if not os.path.exists(path):
            return

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        self.window.messages = [
            ContextMessage.from_dict(msg) for msg in data.get("messages", [])
        ]

        summary_data = data.get("summary", {})
        self.window.summary = ContextSummary(
            key_points=summary_data.get("key_points", []),
            entities=summary_data.get("entities", []),
            apis=summary_data.get("apis", []),
            events=summary_data.get("events", []),
            decisions=summary_data.get("decisions", []),
            issues=summary_data.get("issues", []),
        )


@dataclass
class CodeContext:
    """代码上下文"""
    file_path: str = ""
    code: str = ""
    language: str = "python"
    imports: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "code": self.code,
            "language": self.language,
            "imports": self.imports,
            "functions": self.functions,
            "classes": self.classes,
            "variables": self.variables,
            "dependencies": self.dependencies,
        }


class CodeContextAnalyzer:
    """
    代码上下文分析器

    分析代码结构和上下文。
    """

    def analyze(self, code: str, file_path: str = "") -> CodeContext:
        """
        分析代码上下文

        Args:
            code: 代码内容
            file_path: 文件路径

        Returns:
            CodeContext: 代码上下文
        """
        context = CodeContext(
            file_path=file_path,
            code=code,
        )

        lines = code.split("\n")

        for line in lines:
            stripped = line.strip()

            # 提取导入
            if stripped.startswith("import ") or stripped.startswith("from "):
                context.imports.append(stripped)

            # 提取函数定义
            if stripped.startswith("def "):
                func_name = self._extract_name(stripped[4:])
                if func_name:
                    context.functions.append(func_name)

            # 提取类定义
            if stripped.startswith("class "):
                class_name = self._extract_name(stripped[6:])
                if class_name:
                    context.classes.append(class_name)

            # 提取变量赋值
            if "=" in stripped and not stripped.startswith("#"):
                var_name = stripped.split("=")[0].strip()
                if var_name.isidentifier():
                    context.variables.append(var_name)

        # 提取依赖
        context.dependencies = self._extract_dependencies(code)

        return context

    def _extract_name(self, text: str) -> str:
        """提取名称"""
        # 处理函数参数和继承
        for char in "(:":
            if char in text:
                text = text.split(char)[0]
        return text.strip()

    def _extract_dependencies(self, code: str) -> list[str]:
        """提取依赖"""
        dependencies = []

        # ModSDK 特定依赖
        if "serverApi" in code or "ServerApi" in code:
            dependencies.append("mod.server.extraServerApi")
        if "clientApi" in code or "ClientApi" in code:
            dependencies.append("mod.client.extraClientApi")
        if "ListenEvent" in code:
            dependencies.append("事件系统")
        if "GetEngineCompFactory" in code:
            dependencies.append("组件工厂")
        if "CreateEngineEntity" in code:
            dependencies.append("实体系统")
        if "CreateScreen" in code:
            dependencies.append("UI 系统")
        if "NotifyToClient" in code or "NotifyToServer" in code:
            dependencies.append("网络同步")

        return list(set(dependencies))

    def get_context_prompt(self, context: CodeContext) -> str:
        """获取代码上下文提示"""
        parts = []

        if context.file_path:
            parts.append(f"文件: {context.file_path}")

        if context.imports:
            parts.append(f"导入: {len(context.imports)} 个")

        if context.functions:
            parts.append(f"函数: {', '.join(context.functions[:5])}")

        if context.classes:
            parts.append(f"类: {', '.join(context.classes[:5])}")

        if context.dependencies:
            parts.append(f"依赖: {', '.join(context.dependencies)}")

        if not parts:
            return ""

        return "## 代码上下文\n\n" + "\n".join(parts)


@dataclass
class ProjectContext:
    """项目上下文"""
    name: str = ""
    path: str = ""
    structure: dict[str, Any] = field(default_factory=dict)
    behavior_packs: list[str] = field(default_factory=list)
    resource_packs: list[str] = field(default_factory=list)
    scripts: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "structure": self.structure,
            "behavior_packs": self.behavior_packs,
            "resource_packs": self.resource_packs,
            "scripts": self.scripts,
            "config": self.config,
        }


class ProjectContextAnalyzer:
    """
    项目上下文分析器

    分析项目结构和配置。
    """

    def analyze(self, project_path: str) -> ProjectContext:
        """
        分析项目上下文

        Args:
            project_path: 项目路径

        Returns:
            ProjectContext: 项目上下文
        """
        import os

        context = ProjectContext(path=project_path)

        if not os.path.exists(project_path):
            return context

        # 获取项目名称
        context.name = os.path.basename(project_path)

        # 分析目录结构
        for root, dirs, files in os.walk(project_path):
            rel_path = os.path.relpath(root, project_path)

            # 跳过隐藏目录和常见的忽略目录
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "node_modules"]]

            for file in files:
                file_path = os.path.join(rel_path, file) if rel_path != "." else file

                # 识别行为包
                if "behavior_pack" in rel_path.lower() or "behaviorpack" in rel_path.lower():
                    context.behavior_packs.append(file_path)
                    if file.endswith(".py"):
                        context.scripts.append(file_path)

                # 识别资源包
                if "resource_pack" in rel_path.lower() or "resourcepack" in rel_path.lower():
                    context.resource_packs.append(file_path)

                # 读取配置文件
                if file == "manifest.json":
                    self._read_manifest(os.path.join(root, file), context)

        return context

    def _read_manifest(self, manifest_path: str, context: ProjectContext) -> None:
        """读取 manifest.json"""
        import json

        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)

            if "header" in manifest:
                header = manifest["header"]
                if "name" in header:
                    context.config["name"] = header["name"]
                if "description" in header:
                    context.config["description"] = header["description"]
                if "version" in header:
                    context.config["version"] = header["version"]
        except (json.JSONDecodeError, IOError):
            pass

    def get_context_prompt(self, context: ProjectContext) -> str:
        """获取项目上下文提示"""
        parts = []

        if context.name:
            parts.append(f"项目名称: {context.name}")

        if context.behavior_packs:
            parts.append(f"行为包文件: {len(context.behavior_packs)} 个")

        if context.resource_packs:
            parts.append(f"资源包文件: {len(context.resource_packs)} 个")

        if context.scripts:
            parts.append(f"Python 脚本: {len(context.scripts)} 个")
            if len(context.scripts) <= 5:
                parts.append(f"  脚本列表: {', '.join(context.scripts)}")

        if context.config:
            if "name" in context.config:
                parts.append(f"Addon 名称: {context.config['name']}")
            if "description" in context.config:
                parts.append(f"描述: {context.config['description']}")

        if not parts:
            return ""

        return "## 项目上下文\n\n" + "\n".join(parts)


def create_conversation_manager(
    max_messages: int = 20,
    max_tokens: int = 4000,
) -> ConversationManager:
    """创建对话管理器"""
    return ConversationManager(max_messages, max_tokens)


def analyze_code_context(code: str, file_path: str = "") -> CodeContext:
    """分析代码上下文"""
    analyzer = CodeContextAnalyzer()
    return analyzer.analyze(code, file_path)


def analyze_project_context(project_path: str) -> ProjectContext:
    """分析项目上下文"""
    analyzer = ProjectContextAnalyzer()
    return analyzer.analyze(project_path)