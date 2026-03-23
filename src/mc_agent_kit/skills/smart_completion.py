"""
智能补全模块

提供 API 调用补全、代码片段补全、参数智能推荐、错误修复建议补全和文档引用补全。
"""

from __future__ import annotations

import re
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class CompletionType(Enum):
    """补全类型"""
    API_NAME = "api_name"             # API 名称
    API_CALL = "api_call"             # API 调用
    EVENT_NAME = "event_name"         # 事件名称
    PARAMETER = "parameter"           # 参数
    PARAMETER_VALUE = "param_value"   # 参数值
    CODE_SNIPPET = "code_snippet"     # 代码片段
    IMPORT = "import"                 # 导入语句
    VARIABLE = "variable"             # 变量
    ERROR_FIX = "error_fix"           # 错误修复
    DOC_REFERENCE = "doc_ref"         # 文档引用
    MODULE_NAME = "module_name"       # 模块名称


class CompletionSource(Enum):
    """补全来源"""
    KNOWLEDGE_BASE = "kb"             # 知识库
    CONTEXT = "context"               # 上下文
    HISTORY = "history"               # 历史记录
    TEMPLATE = "template"             # 模板
    INFERENCE = "inference"           # 推断


@dataclass
class CompletionItem:
    """补全项"""
    text: str
    display_text: str
    completion_type: CompletionType
    source: CompletionSource
    confidence: float = 1.0
    insert_text: str = ""            # 实际插入的文本
    documentation: str = ""          # 文档说明
    detail: str = ""                 # 详细信息
    sort_text: str = ""              # 排序文本
    filter_text: str = ""            # 过滤文本
    commit_characters: list[str] = field(default_factory=list)
    additional_edits: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """后处理"""
        if not self.insert_text:
            self.insert_text = self.text
        if not self.sort_text:
            self.sort_text = f"{1 - self.confidence:.2f}_{self.text}"
        if not self.filter_text:
            self.filter_text = self.text.lower()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "text": self.text,
            "display_text": self.display_text,
            "completion_type": self.completion_type.value,
            "source": self.source.value,
            "confidence": self.confidence,
            "insert_text": self.insert_text,
            "documentation": self.documentation,
            "detail": self.detail,
            "sort_text": self.sort_text,
            "filter_text": self.filter_text,
            "commit_characters": self.commit_characters,
            "additional_edits": self.additional_edits,
            "metadata": self.metadata,
        }


@dataclass
class CompletionContext:
    """补全上下文"""
    text_before_cursor: str
    text_after_cursor: str = ""
    file_path: str = ""
    line_number: int = 0
    column_number: int = 0
    language: str = "python"
    scope: str = ""                  # server/client
    imports: list[str] = field(default_factory=list)
    variables: dict[str, str] = field(default_factory=dict)
    recent_apis: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "text_before_cursor": self.text_before_cursor,
            "text_after_cursor": self.text_after_cursor,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "language": self.language,
            "scope": self.scope,
            "imports": self.imports,
            "variables": self.variables,
            "recent_apis": self.recent_apis,
        }


@dataclass
class CompletionResult:
    """补全结果"""
    items: list[CompletionItem]
    is_incomplete: bool = False
    execution_time: float = 0.0
    context_used: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "items": [i.to_dict() for i in self.items],
            "is_incomplete": self.is_incomplete,
            "execution_time": self.execution_time,
            "context_used": self.context_used,
        }


@dataclass
class CompletionStats:
    """补全统计"""
    total_requests: int = 0
    successful_completions: int = 0
    average_items: float = 0.0
    average_time: float = 0.0
    type_distribution: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_requests": self.total_requests,
            "successful_completions": self.successful_completions,
            "average_items": self.average_items,
            "average_time": self.average_time,
            "type_distribution": self.type_distribution,
        }


class APICompletionProvider:
    """API 补全提供者

    提供 ModSDK API 名称和调用补全。
    """

    def __init__(self) -> None:
        """初始化 API 补全提供者"""
        self._apis: dict[str, dict[str, Any]] = {}
        self._api_prefixes: dict[str, list[str]] = defaultdict(list)
        self._module_apis: dict[str, list[str]] = defaultdict(list)
        self._lock = threading.RLock()

        # 加载内置 API
        self._load_builtin_apis()

    def register_api(
        self,
        name: str,
        module: str = "",
        scope: str = "both",
        parameters: Optional[list[dict[str, Any]]] = None,
        return_type: str = "",
        description: str = "",
    ) -> None:
        """注册 API"""
        with self._lock:
            self._apis[name] = {
                "name": name,
                "module": module,
                "scope": scope,
                "parameters": parameters or [],
                "return_type": return_type,
                "description": description,
            }

            # 建立前缀索引
            for i in range(1, min(len(name) + 1, 5)):
                prefix = name[:i]
                self._api_prefixes[prefix].append(name)

            # 建立模块索引
            if module:
                self._module_apis[module].append(name)

    def complete(
        self,
        context: CompletionContext,
        max_items: int = 20,
    ) -> list[CompletionItem]:
        """提供补全"""
        text = context.text_before_cursor
        items: list[CompletionItem] = []

        # 提取当前输入的前缀
        prefix = self._extract_prefix(text)
        if not prefix:
            return items

        with self._lock:
            # 查找匹配的 API
            candidates: list[str] = []

            # 精确前缀匹配
            if prefix in self._api_prefixes:
                candidates.extend(self._api_prefixes[prefix])

            # 模糊匹配
            prefix_lower = prefix.lower()
            for api_name in self._apis:
                if prefix_lower in api_name.lower() and api_name not in candidates:
                    candidates.append(api_name)

            # 过滤作用域
            if context.scope:
                candidates = [
                    name for name in candidates
                    if self._apis[name].get("scope") in (context.scope, "both", "")
                ]

            # 生成补全项
            for name in candidates[:max_items]:
                api_info = self._apis[name]
                parameters = api_info.get("parameters", [])

                # 构建参数提示
                param_str = ", ".join(p.get("name", "") for p in parameters)
                call_snippet = f"{name}({param_str})"

                item = CompletionItem(
                    text=name,
                    display_text=name,
                    completion_type=CompletionType.API_NAME,
                    source=CompletionSource.KNOWLEDGE_BASE,
                    confidence=0.9 if name.startswith(prefix) else 0.7,
                    insert_text=call_snippet,
                    documentation=api_info.get("description", ""),
                    detail=f"模块: {api_info.get('module', 'unknown')}",
                    metadata={
                        "module": api_info.get("module"),
                        "scope": api_info.get("scope"),
                        "parameters": parameters,
                    },
                )
                items.append(item)

        return items

    def complete_api_call(
        self,
        api_name: str,
        current_params: list[str],
        context: CompletionContext,
    ) -> list[CompletionItem]:
        """补全 API 调用参数"""
        items: list[CompletionItem] = []

        with self._lock:
            api_info = self._apis.get(api_name)
            if not api_info:
                return items

            parameters = api_info.get("parameters", [])
            provided_names = set(current_params)

            for param in parameters:
                param_name = param.get("name", "")
                if param_name in provided_names:
                    continue

                param_type = param.get("type", "")
                description = param.get("description", "")

                # 根据参数类型提供值建议
                value_suggestions = self._suggest_param_values(
                    param_name,
                    param_type,
                    context,
                )

                if value_suggestions:
                    for value, desc in value_suggestions:
                        items.append(CompletionItem(
                            text=value,
                            display_text=f"{param_name}={value}",
                            completion_type=CompletionType.PARAMETER_VALUE,
                            source=CompletionSource.KNOWLEDGE_BASE,
                            confidence=0.8,
                            documentation=f"{description}\n{desc}",
                        ))
                else:
                    items.append(CompletionItem(
                        text=param_name,
                        display_text=param_name,
                        completion_type=CompletionType.PARAMETER,
                        source=CompletionSource.KNOWLEDGE_BASE,
                        confidence=0.9,
                        documentation=description,
                        detail=f"类型: {param_type}",
                    ))

        return items

    def _extract_prefix(self, text: str) -> str:
        """提取前缀"""
        # 匹配最后一个标识符
        match = re.search(r'([A-Za-z_][A-Za-z0-9_]*)$', text)
        return match.group(1) if match else ""

    def _suggest_param_values(
        self,
        param_name: str,
        param_type: str,
        context: CompletionContext,
    ) -> list[tuple[str, str]]:
        """建议参数值"""
        suggestions: list[tuple[str, str]] = []

        # 常见参数值建议
        common_values: dict[str, list[tuple[str, str]]] = {
            "scope": [
                ("'server'", "服务端作用域"),
                ("'client'", "客户端作用域"),
            ],
            "type": [
                ("'entity'", "实体类型"),
                ("'item'", "物品类型"),
                ("'block'", "方块类型"),
            ],
            "sync": [
                ("True", "同步执行"),
                ("False", "异步执行"),
            ],
        }

        if param_name.lower() in common_values:
            suggestions.extend(common_values[param_name.lower()])

        # 根据类型建议
        if param_type == "bool":
            suggestions.extend([("True", "布尔真"), ("False", "布尔假")])
        elif param_type == "int":
            suggestions.append(("0", "整数默认值"))

        return suggestions

    def _load_builtin_apis(self) -> None:
        """加载内置 API"""
        # 实体相关
        self.register_api(
            "CreateEngineEntity",
            module="entity",
            scope="server",
            parameters=[
                {"name": "engineType", "type": "str", "description": "实体引擎类型"},
                {"name": "identifier", "type": "str", "description": "实体标识符"},
            ],
            return_type="Entity",
            description="创建引擎实体",
        )

        self.register_api(
            "DestroyEntity",
            module="entity",
            scope="server",
            parameters=[
                {"name": "entityId", "type": "str", "description": "实体 ID"},
            ],
            description="销毁实体",
        )

        self.register_api(
            "GetEngineEntity",
            module="entity",
            scope="both",
            parameters=[
                {"name": "entityId", "type": "str", "description": "实体 ID"},
            ],
            return_type="Entity",
            description="获取引擎实体",
        )

        # 事件相关
        self.register_api(
            "ListenEvent",
            module="event",
            scope="both",
            parameters=[
                {"name": "namespace", "type": "str", "description": "命名空间"},
                {"name": "eventName", "type": "str", "description": "事件名称"},
                {"name": "callback", "type": "callable", "description": "回调函数"},
            ],
            description="监听事件",
        )

        self.register_api(
            "UnListenEvent",
            module="event",
            scope="both",
            parameters=[
                {"name": "namespace", "type": "str", "description": "命名空间"},
                {"name": "eventName", "type": "str", "description": "事件名称"},
            ],
            description="取消监听事件",
        )

        # 物品相关
        self.register_api(
            "CreateEngineItem",
            module="item",
            scope="server",
            parameters=[
                {"name": "engineType", "type": "str", "description": "物品引擎类型"},
                {"name": "identifier", "type": "str", "description": "物品标识符"},
            ],
            return_type="Item",
            description="创建引擎物品",
        )

        # 方块相关
        self.register_api(
            "CreateEngineBlock",
            module="block",
            scope="server",
            parameters=[
                {"name": "engineType", "type": "str", "description": "方块引擎类型"},
            ],
            return_type="Block",
            description="创建引擎方块",
        )


class EventCompletionProvider:
    """事件补全提供者"""

    def __init__(self) -> None:
        """初始化事件补全提供者"""
        self._events: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

        # 加载内置事件
        self._load_builtin_events()

    def register_event(
        self,
        name: str,
        scope: str = "both",
        parameters: Optional[list[dict[str, Any]]] = None,
        description: str = "",
    ) -> None:
        """注册事件"""
        with self._lock:
            self._events[name] = {
                "name": name,
                "scope": scope,
                "parameters": parameters or [],
                "description": description,
            }

    def complete(
        self,
        context: CompletionContext,
        max_items: int = 20,
    ) -> list[CompletionItem]:
        """提供补全"""
        text = context.text_before_cursor
        items: list[CompletionItem] = []

        # 提取前缀
        match = re.search(r'(On[A-Za-z]*)$', text)
        if not match:
            return items

        prefix = match.group(1)
        prefix_lower = prefix.lower()

        with self._lock:
            candidates = [
                name for name in self._events
                if prefix_lower in name.lower()
            ]

            # 过滤作用域
            if context.scope:
                candidates = [
                    name for name in candidates
                    if self._events[name].get("scope") in (context.scope, "both", "")
                ]

            for name in candidates[:max_items]:
                event_info = self._events[name]
                items.append(CompletionItem(
                    text=name,
                    display_text=name,
                    completion_type=CompletionType.EVENT_NAME,
                    source=CompletionSource.KNOWLEDGE_BASE,
                    confidence=0.9 if name.startswith(prefix) else 0.7,
                    documentation=event_info.get("description", ""),
                    detail=f"作用域: {event_info.get('scope', 'both')}",
                    metadata={
                        "scope": event_info.get("scope"),
                        "parameters": event_info.get("parameters", []),
                    },
                ))

        return items

    def _load_builtin_events(self) -> None:
        """加载内置事件"""
        # 服务器事件
        self.register_event(
            "OnServerChat",
            scope="server",
            parameters=[
                {"name": "playerId", "type": "str"},
                {"name": "message", "type": "str"},
            ],
            description="服务器聊天事件",
        )

        self.register_event(
            "OnServerPlayerJoin",
            scope="server",
            parameters=[
                {"name": "playerId", "type": "str"},
            ],
            description="玩家加入服务器事件",
        )

        self.register_event(
            "OnServerPlayerLeave",
            scope="server",
            parameters=[
                {"name": "playerId", "type": "str"},
            ],
            description="玩家离开服务器事件",
        )

        # 客户端事件
        self.register_event(
            "OnClientChat",
            scope="client",
            parameters=[
                {"name": "message", "type": "str"},
            ],
            description="客户端聊天事件",
        )

        self.register_event(
            "OnClientPlayerJoin",
            scope="client",
            parameters=[
                {"name": "playerId", "type": "str"},
            ],
            description="玩家加入客户端事件",
        )


class SnippetCompletionProvider:
    """代码片段补全提供者"""

    def __init__(self) -> None:
        """初始化代码片段补全提供者"""
        self._snippets: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

        # 加载内置片段
        self._load_builtin_snippets()

    def register_snippet(
        self,
        prefix: str,
        body: str,
        description: str = "",
        scope: str = "",
    ) -> None:
        """注册代码片段"""
        with self._lock:
            self._snippets[prefix] = {
                "prefix": prefix,
                "body": body,
                "description": description,
                "scope": scope,
            }

    def complete(
        self,
        context: CompletionContext,
        max_items: int = 10,
    ) -> list[CompletionItem]:
        """提供补全"""
        text = context.text_before_cursor
        items: list[CompletionItem] = []

        # 提取前缀
        match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)$', text)
        if not match:
            return items

        prefix = match.group(1).lower()

        with self._lock:
            for snippet_prefix, snippet in self._snippets.items():
                if prefix in snippet_prefix.lower():
                    # 过滤作用域
                    if context.scope and snippet.get("scope"):
                        if context.scope not in snippet.get("scope", ""):
                            continue

                    items.append(CompletionItem(
                        text=snippet_prefix,
                        display_text=snippet_prefix,
                        completion_type=CompletionType.CODE_SNIPPET,
                        source=CompletionSource.TEMPLATE,
                        confidence=0.8,
                        insert_text=snippet.get("body", ""),
                        documentation=snippet.get("description", ""),
                        metadata={"scope": snippet.get("scope")},
                    ))

        return items[:max_items]

    def _load_builtin_snippets(self) -> None:
        """加载内置代码片段"""
        # 事件监听片段
        self.register_snippet(
            prefix="listen",
            body='''ListenEvent("${1:namespace}", "${2:eventName}", ${3:callback})''',
            description="监听事件",
            scope="both",
        )

        # 实体创建片段
        self.register_snippet(
            prefix="create_entity",
            body='''entity = CreateEngineEntity("${1:engineType}", "${2:identifier}")
if entity:
    SetEngineEntityPos(entity, ${3:x}, ${4:y}, ${5:z})''',
            description="创建并设置实体位置",
            scope="server",
        )

        # 服务器启动事件
        self.register_snippet(
            prefix="on_server_start",
            body='''def OnServerStart():
    """服务器启动事件处理"""
    ${1:# 初始化代码}

ListenEvent("Minecraft", "OnServerStart", OnServerStart)''',
            description="服务器启动事件模板",
            scope="server",
        )

        # 玩家加入事件
        self.register_snippet(
            prefix="on_player_join",
            body='''def OnPlayerJoin(args):
    """玩家加入事件处理"""
    player_id = args.get("playerId")
    ${1:# 处理逻辑}

ListenEvent("Minecraft", "OnServerPlayerJoin", OnPlayerJoin)''',
            description="玩家加入事件模板",
            scope="server",
        )


class SmartCompletionEngine:
    """智能补全引擎

    整合各种补全提供者。
    """

    def __init__(self) -> None:
        """初始化智能补全引擎"""
        self._api_provider = APICompletionProvider()
        self._event_provider = EventCompletionProvider()
        self._snippet_provider = SnippetCompletionProvider()
        self._stats = CompletionStats()
        self._lock = threading.RLock()

    def complete(
        self,
        context: CompletionContext,
        max_items: int = 50,
        timeout_ms: int = 200,
    ) -> CompletionResult:
        """执行补全"""
        start_time = time.time()

        all_items: list[CompletionItem] = []

        # 并行调用各提供者
        api_items = self._api_provider.complete(context, max_items // 3)
        all_items.extend(api_items)

        event_items = self._event_provider.complete(context, max_items // 3)
        all_items.extend(event_items)

        snippet_items = self._snippet_provider.complete(context, max_items // 3)
        all_items.extend(snippet_items)

        # 按置信度排序
        all_items.sort(key=lambda x: x.confidence, reverse=True)
        all_items = all_items[:max_items]

        # 更新统计
        with self._lock:
            self._stats.total_requests += 1
            self._stats.successful_completions += 1 if all_items else 0
            self._stats.average_items = (
                (self._stats.average_items * (self._stats.total_requests - 1) + len(all_items))
                / self._stats.total_requests
            )

            for item in all_items:
                type_name = item.completion_type.value
                self._stats.type_distribution[type_name] = (
                    self._stats.type_distribution.get(type_name, 0) + 1
                )

        execution_time = time.time() - start_time

        return CompletionResult(
            items=all_items,
            is_incomplete=len(all_items) >= max_items,
            execution_time=execution_time,
            context_used={
                "scope": context.scope,
                "language": context.language,
            },
        )

    def complete_api_params(
        self,
        api_name: str,
        current_params: list[str],
        context: CompletionContext,
    ) -> list[CompletionItem]:
        """补全 API 参数"""
        return self._api_provider.complete_api_call(
            api_name,
            current_params,
            context,
        )

    def register_api(
        self,
        name: str,
        module: str = "",
        scope: str = "both",
        parameters: Optional[list[dict[str, Any]]] = None,
        return_type: str = "",
        description: str = "",
    ) -> None:
        """注册 API"""
        self._api_provider.register_api(
            name=name,
            module=module,
            scope=scope,
            parameters=parameters,
            return_type=return_type,
            description=description,
        )

    def register_event(
        self,
        name: str,
        scope: str = "both",
        parameters: Optional[list[dict[str, Any]]] = None,
        description: str = "",
    ) -> None:
        """注册事件"""
        self._event_provider.register_event(
            name=name,
            scope=scope,
            parameters=parameters,
            description=description,
        )

    def register_snippet(
        self,
        prefix: str,
        body: str,
        description: str = "",
        scope: str = "",
    ) -> None:
        """注册代码片段"""
        self._snippet_provider.register_snippet(
            prefix=prefix,
            body=body,
            description=description,
            scope=scope,
        )

    def get_stats(self) -> CompletionStats:
        """获取统计信息"""
        with self._lock:
            return self._stats


# 全局实例
_engine: Optional[SmartCompletionEngine] = None


def get_completion_engine() -> SmartCompletionEngine:
    """获取全局补全引擎"""
    global _engine
    if _engine is None:
        _engine = SmartCompletionEngine()
    return _engine


def complete(context: CompletionContext, max_items: int = 50) -> CompletionResult:
    """便捷函数：执行补全"""
    return get_completion_engine().complete(context, max_items)