"""
知识库数据模型

定义 ModSDK 文档的结构化数据模型，包括 API、事件、枚举等。
"""

from dataclasses import dataclass, field
from enum import Enum


class EntryType(Enum):
    """条目类型"""

    API = "api"
    EVENT = "event"
    ENUM = "enum"
    EXAMPLE = "example"


class Scope(Enum):
    """运行范围（客户端/服务端）"""

    CLIENT = "client"
    SERVER = "server"
    BOTH = "both"
    UNKNOWN = "unknown"


@dataclass
class APIParameter:
    """API 参数"""

    name: str
    data_type: str
    description: str
    optional: bool = False
    default_value: str | None = None


@dataclass
class EventParameter:
    """事件参数"""

    name: str
    data_type: str
    description: str
    mutable: bool = False  # 是否可修改


@dataclass
class CodeExample:
    """代码示例"""

    code: str
    language: str = "python"
    description: str | None = None


@dataclass
class APIEntry:
    """API 条目"""

    name: str
    module: str  # 所属模块，如 "物品"、"实体/行为"
    description: str
    method_path: str  # 完整方法路径，如 mod.server.component.itemCompServer.ItemCompServer
    scope: Scope = Scope.UNKNOWN
    parameters: list[APIParameter] = field(default_factory=list)
    return_type: str | None = None
    return_description: str | None = None
    examples: list[CodeExample] = field(default_factory=list)
    remarks: list[str] = field(default_factory=list)
    source_path: str | None = None
    related_apis: list[str] = field(default_factory=list)


@dataclass
class EventEntry:
    """事件条目"""

    name: str
    module: str  # 所属模块，如 "实体"、"玩家"
    description: str
    scope: Scope = Scope.UNKNOWN
    parameters: list[EventParameter] = field(default_factory=list)
    return_value: str | None = None
    examples: list[CodeExample] = field(default_factory=list)
    remarks: list[str] = field(default_factory=list)
    source_path: str | None = None
    related_apis: list[str] = field(default_factory=list)


@dataclass
class EnumValue:
    """枚举值"""

    name: str
    value: str | int
    description: str | None = None


@dataclass
class EnumEntry:
    """枚举条目"""

    name: str
    values: list[EnumValue] = field(default_factory=list)
    description: str | None = None
    source_path: str | None = None


@dataclass
class KnowledgeBase:
    """知识库"""

    # API 索引
    apis: dict[str, APIEntry] = field(default_factory=dict)  # name -> APIEntry

    # 事件索引
    events: dict[str, EventEntry] = field(default_factory=dict)  # name -> EventEntry

    # 枚举索引
    enums: dict[str, EnumEntry] = field(default_factory=dict)  # name -> EnumEntry

    # 模块索引（用于按模块查找）
    api_by_module: dict[str, list[str]] = field(default_factory=dict)  # module -> [api_names]
    event_by_module: dict[str, list[str]] = field(default_factory=dict)  # module -> [event_names]

    # 元数据
    version: str = "1.0.0"
    source_dir: str | None = None

    def add_api(self, api: APIEntry) -> None:
        """添加 API 条目"""
        self.apis[api.name] = api
        if api.module not in self.api_by_module:
            self.api_by_module[api.module] = []
        self.api_by_module[api.module].append(api.name)

    def add_event(self, event: EventEntry) -> None:
        """添加事件条目"""
        self.events[event.name] = event
        if event.module not in self.event_by_module:
            self.event_by_module[event.module] = []
        self.event_by_module[event.module].append(event.name)

    def add_enum(self, enum: EnumEntry) -> None:
        """添加枚举条目"""
        self.enums[enum.name] = enum

    def search_apis(self, keyword: str) -> list[APIEntry]:
        """搜索 API（按名称或描述）"""
        keyword_lower = keyword.lower()
        results = []
        for api in self.apis.values():
            if keyword_lower in api.name.lower() or keyword_lower in api.description.lower():
                results.append(api)
        return results

    def search_events(self, keyword: str) -> list[EventEntry]:
        """搜索事件（按名称或描述）"""
        keyword_lower = keyword.lower()
        results = []
        for event in self.events.values():
            if keyword_lower in event.name.lower() or keyword_lower in event.description.lower():
                results.append(event)
        return results

    def get_api(self, name: str) -> APIEntry | None:
        """获取指定 API"""
        return self.apis.get(name)

    def get_event(self, name: str) -> EventEntry | None:
        """获取指定事件"""
        return self.events.get(name)

    def get_apis_by_module(self, module: str) -> list[APIEntry]:
        """获取指定模块的所有 API"""
        names = self.api_by_module.get(module, [])
        return [self.apis[name] for name in names if name in self.apis]

    def get_events_by_module(self, module: str) -> list[EventEntry]:
        """获取指定模块的所有事件"""
        names = self.event_by_module.get(module, [])
        return [self.events[name] for name in names if name in self.events]

    def stats(self) -> dict:
        """获取知识库统计信息"""
        return {
            "total_apis": len(self.apis),
            "total_events": len(self.events),
            "total_enums": len(self.enums),
            "api_modules": list(self.api_by_module.keys()),
            "event_modules": list(self.event_by_module.keys()),
        }

    def to_dict(self) -> dict:
        """转换为字典（用于序列化）"""
        return {
            "version": self.version,
            "source_dir": self.source_dir,
            "stats": self.stats(),
            "apis": {
                name: {
                    "name": api.name,
                    "module": api.module,
                    "description": api.description,
                    "method_path": api.method_path,
                    "scope": api.scope.value,
                    "parameters": [
                        {
                            "name": p.name,
                            "data_type": p.data_type,
                            "description": p.description,
                            "optional": p.optional,
                        }
                        for p in api.parameters
                    ],
                    "return_type": api.return_type,
                    "return_description": api.return_description,
                    "remarks": api.remarks,
                    "source_path": api.source_path,
                }
                for name, api in self.apis.items()
            },
            "events": {
                name: {
                    "name": event.name,
                    "module": event.module,
                    "description": event.description,
                    "scope": event.scope.value,
                    "parameters": [
                        {
                            "name": p.name,
                            "data_type": p.data_type,
                            "description": p.description,
                            "mutable": p.mutable,
                        }
                        for p in event.parameters
                    ],
                    "return_value": event.return_value,
                    "remarks": event.remarks,
                    "source_path": event.source_path,
                }
                for name, event in self.events.items()
            },
            "enums": {
                name: {
                    "name": enum.name,
                    "description": enum.description,
                    "values": [
                        {"name": v.name, "value": str(v.value), "description": v.description}
                        for v in enum.values
                    ],
                    "source_path": enum.source_path,
                }
                for name, enum in self.enums.items()
            },
        }


# ============================================================
# Iteration #31: API Version Tagging
# ============================================================

@dataclass
class ApiVersionTag:
    """
    API 版本标记

    记录 API 的版本历史信息。
    """
    api_name: str
    introduced_in: str  # 引入版本
    deprecated_in: str | None = None  # 废弃版本
    removed_in: str | None = None  # 移除版本
    notes: list[str] = field(default_factory=list)  # 备注

    def is_deprecated(self) -> bool:
        """是否已废弃"""
        return self.deprecated_in is not None

    def is_removed(self) -> bool:
        """是否已移除"""
        return self.removed_in is not None

    def get_replacement(self) -> str | None:
        """获取替代 API 建议"""
        if self.notes:
            for note in self.notes:
                if "请使用" in note or "use" in note.lower():
                    return note
        return None
