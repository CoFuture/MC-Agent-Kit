"""
知识库数据模型

定义 ModSDK 文档的结构化数据模型，包括 API、事件、枚举等。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


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


# ============================================================
# Iteration #32: Enhanced Code Example with Difficulty
# ============================================================

class DifficultyLevel(Enum):
    """代码示例难度等级"""
    BEGINNER = "beginner"      # 初级：基础用法
    INTERMEDIATE = "intermediate"  # 中级：组合使用
    ADVANCED = "advanced"      # 高级：复杂场景
    EXPERT = "expert"          # 专家：性能优化/高级特性


class ExampleCategory(Enum):
    """代码示例类别"""
    BASIC = "basic"            # 基础示例
    ENTITY = "entity"          # 实体相关
    ITEM = "item"              # 物品相关
    BLOCK = "block"            # 方块相关
    UI = "ui"                  # UI 相关
    NETWORK = "network"        # 网络相关
    PERFORMANCE = "performance"  # 性能优化
    ADVANCED = "advanced"      # 高级用法


@dataclass
class EnhancedCodeExample:
    """
    增强代码示例

    带有难度标记、时间估算、类别等元数据的代码示例。
    """
    id: str
    code: str
    title: str
    description: str
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    category: ExampleCategory = ExampleCategory.BASIC
    estimated_time_minutes: int = 5  # 预估完成时间（分钟）
    prerequisites: list[str] = field(default_factory=list)  # 前置知识
    api_names: list[str] = field(default_factory=list)  # 涉及的 API
    event_names: list[str] = field(default_factory=list)  # 涉及的事件
    tags: list[str] = field(default_factory=list)
    source: str = ""
    author: str = ""
    version_added: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty.value,
            "category": self.category.value,
            "estimated_time_minutes": self.estimated_time_minutes,
            "prerequisites": self.prerequisites,
            "api_names": self.api_names,
            "event_names": self.event_names,
            "tags": self.tags,
            "source": self.source,
            "author": self.author,
            "version_added": self.version_added,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnhancedCodeExample":
        """从字典创建实例"""
        return cls(
            id=data.get("id", ""),
            code=data.get("code", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            difficulty=DifficultyLevel(data.get("difficulty", "beginner")),
            category=ExampleCategory(data.get("category", "basic")),
            estimated_time_minutes=data.get("estimated_time_minutes", 5),
            prerequisites=data.get("prerequisites", []),
            api_names=data.get("api_names", []),
            event_names=data.get("event_names", []),
            tags=data.get("tags", []),
            source=data.get("source", ""),
            author=data.get("author", ""),
            version_added=data.get("version_added", "1.0.0"),
        )


# ============================================================
# Iteration #32: API Usage Statistics
# ============================================================

@dataclass
class ApiUsageStats:
    """API 使用统计"""
    api_name: str
    usage_count: int = 0          # 总使用次数
    success_count: int = 0        # 成功次数
    error_count: int = 0          # 错误次数
    last_used: str | None = None  # 最后使用时间
    common_errors: list[str] = field(default_factory=list)  # 常见错误
    related_apis: list[str] = field(default_factory=list)  # 常一起使用的 API
    example_count: int = 0        # 示例数量

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_name": self.api_name,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": round(self.success_rate, 2),
            "last_used": self.last_used,
            "common_errors": self.common_errors,
            "related_apis": self.related_apis,
            "example_count": self.example_count,
        }


class ApiUsageTracker:
    """
    API 使用追踪器

    追踪 API 的使用情况，提供统计和推荐功能。
    """

    def __init__(self) -> None:
        self._stats: dict[str, ApiUsageStats] = {}
        self._total_queries: int = 0

    def record_usage(
        self,
        api_name: str,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        """
        记录 API 使用。

        Args:
            api_name: API 名称
            success: 是否成功
            error: 错误信息（如果有）
        """
        from datetime import datetime

        if api_name not in self._stats:
            self._stats[api_name] = ApiUsageStats(api_name=api_name)

        stats = self._stats[api_name]
        stats.usage_count += 1
        stats.last_used = datetime.now().isoformat()

        if success:
            stats.success_count += 1
        else:
            stats.error_count += 1
            if error and error not in stats.common_errors:
                stats.common_errors.append(error)
                # 保留最近的 10 个错误
                stats.common_errors = stats.common_errors[-10:]

        self._total_queries += 1

    def record_related_apis(self, api_name: str, related: list[str]) -> None:
        """
        记录相关 API。

        Args:
            api_name: API 名称
            related: 相关 API 列表
        """
        if api_name not in self._stats:
            self._stats[api_name] = ApiUsageStats(api_name=api_name)

        stats = self._stats[api_name]
        for api in related:
            if api != api_name and api not in stats.related_apis:
                stats.related_apis.append(api)
                # 保留最近的 20 个相关 API
                stats.related_apis = stats.related_apis[-20:]

    def get_stats(self, api_name: str) -> ApiUsageStats | None:
        """获取 API 统计信息"""
        return self._stats.get(api_name)

    def get_popular_apis(self, limit: int = 10) -> list[tuple[str, int]]:
        """
        获取热门 API。

        Args:
            limit: 返回数量

        Returns:
            (API 名称, 使用次数) 列表
        """
        sorted_apis = sorted(
            self._stats.items(),
            key=lambda x: x[1].usage_count,
            reverse=True,
        )
        return [(api, stats.usage_count) for api, stats in sorted_apis[:limit]]

    def get_problematic_apis(self, limit: int = 10) -> list[tuple[str, float]]:
        """
        获取问题较多的 API（低成功率）。

        Args:
            limit: 返回数量

        Returns:
            (API 名称, 成功率) 列表
        """
        # 只考虑使用次数 >= 5 的 API
        filtered = {
            api: stats for api, stats in self._stats.items()
            if stats.usage_count >= 5
        }

        sorted_apis = sorted(
            filtered.items(),
            key=lambda x: x[1].success_rate,
        )
        return [(api, stats.success_rate) for api, stats in sorted_apis[:limit]]

    def get_recommendations(self, api_name: str, limit: int = 5) -> list[str]:
        """
        获取相关 API 推荐。

        Args:
            api_name: API 名称
            limit: 返回数量

        Returns:
            推荐 API 列表
        """
        stats = self._stats.get(api_name)
        if not stats:
            return []

        # 按使用次数排序相关 API
        related_with_count = [
            (api, self._stats.get(api, ApiUsageStats(api_name=api)).usage_count)
            for api in stats.related_apis
        ]
        related_with_count.sort(key=lambda x: x[1], reverse=True)

        return [api for api, _ in related_with_count[:limit]]

    def save(self, path: str) -> None:
        """保存统计数据到文件"""
        import json

        data = {
            "total_queries": self._total_queries,
            "stats": {api: s.to_dict() for api, s in self._stats.items()},
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path: str) -> None:
        """从文件加载统计数据"""
        import json
        import os

        if not os.path.exists(path):
            return

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        self._total_queries = data.get("total_queries", 0)
        self._stats = {
            api: ApiUsageStats(
                api_name=s.get("api_name", api),
                usage_count=s.get("usage_count", 0),
                success_count=s.get("success_count", 0),
                error_count=s.get("error_count", 0),
                last_used=s.get("last_used"),
                common_errors=s.get("common_errors", []),
                related_apis=s.get("related_apis", []),
                example_count=s.get("example_count", 0),
            )
            for api, s in data.get("stats", {}).items()
        }

    @property
    def total_queries(self) -> int:
        return self._total_queries

    @property
    def tracked_apis(self) -> int:
        return len(self._stats)
