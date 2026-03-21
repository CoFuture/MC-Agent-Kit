"""
智能代码补全器

提供基于知识库的代码补全功能，支持 API、事件、参数提示等。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mc_agent_kit.knowledge_base import KnowledgeBase


class CompletionKind(Enum):
    """补全类型"""

    API = "api"
    EVENT = "event"
    PARAMETER = "parameter"
    VARIABLE = "variable"
    KEYWORD = "keyword"
    SNIPPET = "snippet"
    MODULE = "module"
    CONSTANT = "constant"


@dataclass
class Completion:
    """补全项"""

    label: str  # 显示文本
    kind: CompletionKind  # 类型
    detail: str = ""  # 详细信息
    documentation: str = ""  # 文档说明
    insert_text: str = ""  # 插入文本（可含占位符）
    sort_text: str = ""  # 排序文本
    filter_text: str = ""  # 过滤文本
    priority: int = 0  # 优先级（越高越靠前）
    parameters: list[str] = field(default_factory=list)  # 参数列表
    return_type: str = ""  # 返回类型

    def __post_init__(self) -> None:
        if not self.sort_text:
            self.sort_text = self.label
        if not self.filter_text:
            self.filter_text = self.label.lower()
        if not self.insert_text:
            self.insert_text = self.label


@dataclass
class CompletionContext:
    """补全上下文"""

    code: str  # 当前代码
    cursor_line: int  # 光标所在行（0-based）
    cursor_column: int  # 光标所在列（0-based）
    line_prefix: str = ""  # 当前行前缀
    line_suffix: str = ""  # 当前行后缀
    preceding_lines: list[str] = field(default_factory=list)  # 前面的行
    following_lines: list[str] = field(default_factory=list)  # 后面的行
    current_scope: str = "module"  # 当前作用域
    indent_level: int = 0  # 缩进级别

    @classmethod
    def from_code(cls, code: str, cursor_line: int, cursor_column: int) -> CompletionContext:
        """从代码创建上下文"""
        lines = code.split("\n")

        if cursor_line < 0 or cursor_line >= len(lines):
            cursor_line = 0
        if cursor_column < 0:
            cursor_column = 0

        current_line = lines[cursor_line] if cursor_line < len(lines) else ""
        line_prefix = current_line[:cursor_column]
        line_suffix = current_line[cursor_column:]

        preceding = lines[:cursor_line]
        following = lines[cursor_line + 1 :] if cursor_line + 1 < len(lines) else []

        # 计算缩进级别
        indent_match = re.match(r"^(\s*)", line_prefix)
        indent_level = len(indent_match.group(1)) // 4 if indent_match else 0

        return cls(
            code=code,
            cursor_line=cursor_line,
            cursor_column=cursor_column,
            line_prefix=line_prefix,
            line_suffix=line_suffix,
            preceding_lines=preceding,
            following_lines=following,
            indent_level=indent_level,
        )

    def get_prefix_before_dot(self) -> str | None:
        """获取点号前的前缀（用于成员补全）"""
        match = re.search(r"([a-zA-Z_][a-zA-Z0-9_]*)\.$", self.line_prefix)
        if match:
            return match.group(1)
        return None

    def get_call_context(self) -> tuple[str, int] | None:
        """获取函数调用上下文（函数名和参数位置）"""
        # 匹配函数调用模式
        match = re.search(r"([a-zA-Z_][a-zA-Z0-9_]*)\(([^)]*)$", self.line_prefix)
        if match:
            func_name = match.group(1)
            args_str = match.group(2)
            # 计算参数位置
            arg_count = len([a.strip() for a in args_str.split(",") if a.strip()])
            return (func_name, arg_count)
        return None


@dataclass
class CompletionResult:
    """补全结果"""

    completions: list[Completion]  # 补全列表
    context: CompletionContext  # 补全上下文
    is_incomplete: bool = False  # 是否为部分结果
    trigger_kind: str = "invoked"  # 触发方式：invoked, trigger_character, trigger_for_incomplete

    def get_top_n(self, n: int = 10) -> list[Completion]:
        """获取前 N 个补全项"""
        sorted_items = sorted(self.completions, key=lambda c: (-c.priority, c.sort_text))
        return sorted_items[:n]


class CodeCompleter:
    """智能代码补全器

    基于知识库提供代码补全建议。

    Attributes:
        knowledge_base: 知识库实例
        trigger_characters: 触发补全的字符

    Example:
        >>> completer = CodeCompleter(kb)
        >>> ctx = CompletionContext.from_code("GetEngine", 0, 10)
        >>> result = completer.complete(ctx)
        >>> for c in result.get_top_n(5):
        ...     print(c.label)
    """

    # 触发补全的字符
    trigger_characters = [".", "(", ","]

    def __init__(self, knowledge_base: KnowledgeBase | None = None) -> None:
        """初始化补全器

        Args:
            knowledge_base: 可选的知识库实例
        """
        self._kb = knowledge_base
        self._api_cache: dict[str, list[Completion]] = {}
        self._event_cache: dict[str, list[Completion]] = {}

    def set_knowledge_base(self, kb: KnowledgeBase) -> None:
        """设置知识库"""
        self._kb = kb
        self._api_cache.clear()
        self._event_cache.clear()

    def complete(self, context: CompletionContext) -> CompletionResult:
        """执行代码补全

        Args:
            context: 补全上下文

        Returns:
            补全结果
        """
        completions: list[Completion] = []

        # 检测补全场景
        prefix_before_dot = context.get_prefix_before_dot()
        call_context = context.get_call_context()

        if prefix_before_dot:
            # 成员补全（如 GetConfig.）
            completions.extend(self._complete_member(prefix_before_dot, context))
        elif call_context:
            # 参数补全
            completions.extend(self._complete_parameter(call_context, context))
        else:
            # 标识符补全
            completions.extend(self._complete_identifier(context))

        return CompletionResult(
            completions=completions,
            context=context,
            is_incomplete=False,
        )

    def _complete_identifier(self, context: CompletionContext) -> list[Completion]:
        """标识符补全"""
        completions: list[Completion] = []

        # 获取当前输入的前缀
        match = re.search(r"([a-zA-Z_][a-zA-Z0-9_]*)$", context.line_prefix)
        prefix = match.group(1) if match else ""

        # API 补全
        api_completions = self._get_api_completions(prefix)
        completions.extend(api_completions)

        # 事件补全
        event_completions = self._get_event_completions(prefix)
        completions.extend(event_completions)

        # 常量补全
        constant_completions = self._get_constant_completions(prefix)
        completions.extend(constant_completions)

        # 关键字补全
        keyword_completions = self._get_keyword_completions(prefix, context)
        completions.extend(keyword_completions)

        return completions

    def _complete_member(self, obj_name: str, context: CompletionContext) -> list[Completion]:
        """成员补全"""
        completions: list[Completion] = []

        # 获取当前输入的前缀
        match = re.search(r"\.([a-zA-Z_][a-zA-Z0-9_]*)$", context.line_prefix)
        prefix = match.group(1) if match else ""

        # 根据对象名提供成员补全
        if obj_name == "GetConfig":
            completions.extend(
                [
                    self._make_api_completion("GetGameType", prefix),
                    self._make_api_completion("GetEngineType", prefix),
                    self._make_api_completion("GetMinecraftEnum", prefix),
                ]
            )
        elif obj_name == "GetEngine":
            completions.extend(
                [
                    self._make_api_completion("GetVersion", prefix),
                    self._make_api_completion("GetFrame", prefix),
                ]
            )
        elif obj_name == "serverApi":
            completions.extend(
                [
                    self._make_api_completion("GetPlayerList", prefix),
                    self._make_api_completion("GetPlayerByUid", prefix),
                    self._make_api_completion("GetPlayerByOffLineUid", prefix),
                    self._make_api_completion("GetLevelId", prefix),
                ]
            )
        elif obj_name == "clientApi":
            completions.extend(
                [
                    self._make_api_completion("GetPlayerUid", prefix),
                    self._make_api_completion("GetLocalPlayerId", prefix),
                    self._make_api_completion("GetCameraId", prefix),
                ]
            )

        return completions

    def _complete_parameter(
        self, call_context: tuple[str, int], context: CompletionContext
    ) -> list[Completion]:
        """参数补全"""
        func_name, arg_pos = call_context
        completions: list[Completion] = []

        # 根据函数名和参数位置提供补全
        if func_name in ("CreateEngineEntityByType", "CreateEngineEntity"):
            if arg_pos == 0:
                # 第一个参数是实体类型
                completions.append(
                    Completion(
                        label='"minecraft:entity_type"',
                        kind=CompletionKind.SNIPPET,
                        detail="实体类型标识符",
                        insert_text='"${1:minecraft:entity_type}"',
                        priority=10,
                    )
                )
        elif func_name in ("SetEntityPos", "GetEntityPos"):
            if arg_pos in (1, 2, 3):
                # 坐标参数
                completions.append(
                    Completion(
                        label="x, y, z",
                        kind=CompletionKind.SNIPPET,
                        detail="坐标值",
                        insert_text="${1:0.0}",
                        priority=10,
                    )
                )
        elif func_name == "RegisterEntityEventListener":
            if arg_pos == 1:
                # 事件名
                completions.extend(self._get_event_completions("", "entity"))

        return completions

    def _get_api_completions(self, prefix: str) -> list[Completion]:
        """获取 API 补全"""
        if prefix in self._api_cache:
            return self._api_cache[prefix]

        completions: list[Completion] = []

        # ModSDK 常用 API
        common_apis = [
            ("GetConfig", "获取配置对象", "GetConfig()"),
            ("GetEngine", "获取引擎对象", "GetEngine()"),
            ("GetGameType", "获取游戏类型", "GetGameType()"),
            ("GetEngineType", "获取引擎类型", "GetEngineType()"),
            ("CreateEngineEntity", "创建引擎实体", "CreateEngineEntity(${1:engineType})"),
            ("CreateEngineEntityByType", "按类型创建引擎实体", 'CreateEngineEntityByType("${1:minecraft:entity_type}")'),
            ("DestroyEntity", "销毁实体", "DestroyEntity(${1:entityId})"),
            ("GetEntityPos", "获取实体位置", "GetEntityPos(${1:entityId})"),
            ("SetEntityPos", "设置实体位置", "SetEntityPos(${1:entityId}, ${2:x}, ${3:y}, ${4:z})"),
            ("GetPlayerList", "获取玩家列表", "GetPlayerList()"),
            ("GetPlayerByUid", "通过 UID 获取玩家", "GetPlayerByUid(${1:uid})"),
            ("BroadcastToAllClient", "广播消息到所有客户端", "BroadcastToAllClient(${1:eventName}, ${2:data})"),
            ("NotifyToClient", "通知指定客户端", "NotifyToClient(${1:uid}, ${2:eventName}, ${3:data})"),
            ("NotifyToServer", "通知服务端", "NotifyToServer(${1:eventName}, ${2:data})"),
            ("RegisterEntityEventListener", "注册实体事件监听", "RegisterEntityEventListener(${1:entityId}, ${2:eventName})"),
            ("ListenForEvent", "监听事件", "ListenForEvent(${1:eventName}, ${2:callback})"),
            ("UnListenForEvent", "取消监听事件", "UnListenForEvent(${1:eventName})"),
        ]

        for name, detail, insert_text in common_apis:
            if name.lower().startswith(prefix.lower()):
                completions.append(
                    Completion(
                        label=name,
                        kind=CompletionKind.API,
                        detail=detail,
                        insert_text=insert_text,
                        documentation=f"ModSDK API: {name}",
                        priority=20,
                    )
                )

        # 如果有知识库，从知识库获取更多 API
        if self._kb:
            try:
                results = self._kb.search_apis(prefix, limit=20)
                for entry in results:
                    completions.append(
                        Completion(
                            label=entry.name,
                            kind=CompletionKind.API,
                            detail=entry.description[:100] if entry.description else "",
                            documentation=entry.description or "",
                            priority=15,
                        )
                    )
            except Exception:
                pass

        self._api_cache[prefix] = completions
        return completions

    def _get_event_completions(self, prefix: str, category: str = "") -> list[Completion]:
        """获取事件补全"""
        cache_key = f"{prefix}:{category}"
        if cache_key in self._event_cache:
            return self._event_cache[cache_key]

        completions: list[Completion] = []

        # ModSDK 常用事件
        common_events = [
            ("AddServerPlayerEvent", "服务端玩家加入事件"),
            ("RemoveServerPlayerEvent", "服务端玩家离开事件"),
            ("AddClientPlayerEvent", "客户端玩家加入事件"),
            ("RemoveClientPlayerEvent", "客户端玩家离开事件"),
            ("OnScriptTickClientEvent", "客户端脚本 Tick 事件"),
            ("OnScriptTickServerEvent", "服务端脚本 Tick 事件"),
            ("OnCustomCommandClientEvent", "客户端自定义命令事件"),
            ("OnCustomCommandServerEvent", "服务端自定义命令事件"),
            ("EntityHurtEvent", "实体受伤事件"),
            ("EntityDieEvent", "实体死亡事件"),
            ("EntityStepOnBlockEvent", "实体踩方块事件"),
            ("OnTouchBlockEvent", "触碰方块事件"),
            ("OnPlaceBlockEvent", "放置方块事件"),
            ("OnDestroyBlockEvent", "破坏方块事件"),
            ("OnUseItemEvent", "使用物品事件"),
            ("OnCarriedNewItemEvent", "手持新物品事件"),
            ("OnNewClientCheckEvent", "新客户端检查事件"),
            ("OnResourceLoadFinishedClientEvent", "客户端资源加载完成事件"),
            ("OnResourceLoadFinishedServerEvent", "服务端资源加载完成事件"),
            ("UiInitFinishedEvent", "UI 初始化完成事件"),
            ("LevelGeneratedEvent", "维度生成完成事件"),
            ("ServerChatEvent", "服务端聊天事件"),
            ("ClientChatEvent", "客户端聊天事件"),
        ]

        for name, detail in common_events:
            if name.lower().startswith(prefix.lower()):
                completions.append(
                    Completion(
                        label=name,
                        kind=CompletionKind.EVENT,
                        detail=detail,
                        insert_text=f'"{name}"',
                        documentation=f"ModSDK 事件: {name}\n{detail}",
                        priority=20,
                    )
                )

        self._event_cache[cache_key] = completions
        return completions

    def _get_constant_completions(self, prefix: str) -> list[Completion]:
        """获取常量补全"""
        completions: list[Completion] = []

        # ModSDK 常量
        constants = [
            ("SERVER_TYPE", "服务端类型标识"),
            ("CLIENT_TYPE", "客户端类型标识"),
            ("MINECRAFT", "Minecraft 游戏标识"),
        ]

        for name, detail in constants:
            if name.lower().startswith(prefix.lower()):
                completions.append(
                    Completion(
                        label=name,
                        kind=CompletionKind.CONSTANT,
                        detail=detail,
                        insert_text=name,
                        priority=10,
                    )
                )

        return completions

    def _get_keyword_completions(self, prefix: str, context: CompletionContext) -> list[Completion]:
        """获取关键字补全"""
        completions: list[Completion] = []

        # 常用代码片段
        snippets = [
            (
                "def",
                "定义函数",
                "def ${1:function_name}(${2:params}):\n    ${3:pass}",
            ),
            (
                "class",
                "定义类",
                "class ${1:ClassName}:\n    def __init__(self):\n        ${2:pass}",
            ),
            (
                "for",
                "for 循环",
                "for ${1:item} in ${2:items}:\n    ${3:pass}",
            ),
            (
                "if",
                "if 条件",
                "if ${1:condition}:\n    ${2:pass}",
            ),
            ("try", "try-except", "try:\n    ${1:pass}\nexcept Exception as e:\n    ${2:print(e)}"),
            (
                "with",
                "with 语句",
                "with ${1:resource} as ${2:alias}:\n    ${3:pass}",
            ),
            ("import", "import 语句", "import ${1:module}"),
            ("from", "from import", "from ${1:module} import ${2:name}"),
        ]

        for name, detail, insert_text in snippets:
            if name.lower().startswith(prefix.lower()):
                completions.append(
                    Completion(
                        label=name,
                        kind=CompletionKind.SNIPPET,
                        detail=detail,
                        insert_text=insert_text,
                        priority=5,
                    )
                )

        return completions

    def _make_api_completion(self, name: str, prefix: str = "") -> Completion:
        """创建 API 补全项"""
        return Completion(
            label=name,
            kind=CompletionKind.API,
            detail="ModSDK API",
            insert_text=f"{name}(${{1}})",
            priority=20,
        )

    def complete_api(self, prefix: str, limit: int = 20) -> list[str]:
        """API 名称自动补全

        Args:
            prefix: API 名称前缀
            limit: 返回数量限制

        Returns:
            匹配的 API 名称列表
        """
        completions = self._get_api_completions(prefix)
        return [c.label for c in completions[:limit]]

    def complete_event(self, prefix: str, limit: int = 20) -> list[str]:
        """事件名称自动补全

        Args:
            prefix: 事件名称前缀
            limit: 返回数量限制

        Returns:
            匹配的事件名称列表
        """
        completions = self._get_event_completions(prefix)
        return [c.label for c in completions[:limit]]
