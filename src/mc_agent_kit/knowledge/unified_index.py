"""
统一索引模块

提供统一的索引条目结构，支持 API、事件、示例代码等多种类型。
迭代 #71: 知识库增强与检索优化
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EntryType(Enum):
    """索引条目类型"""
    API = "api"
    EVENT = "event"
    EXAMPLE = "example"
    GUIDE = "guide"
    DEMO = "demo"
    ENUM = "enum"
    CONSTANT = "constant"
    TYPE_DEF = "type_def"


class EntryScope(Enum):
    """条目作用域"""
    CLIENT = "client"
    SERVER = "server"
    BOTH = "both"
    UNKNOWN = "unknown"


class ExampleCategory(Enum):
    """示例分类"""
    BASIC = "basic"              # 基础示例
    ENTITY = "entity"            # 实体相关
    ITEM = "item"                # 物品相关
    BLOCK = "block"              # 方块相关
    UI = "ui"                    # UI 相关
    NETWORK = "network"          # 网络同步
    PERFORMANCE = "performance"  # 性能优化
    ADVANCED = "advanced"        # 高级用法


class DifficultyLevel(Enum):
    """难度等级"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class CodeBlock:
    """代码块"""
    language: str
    code: str
    description: str | None = None
    line_start: int | None = None
    line_end: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "code": self.code,
            "description": self.description,
            "line_start": self.line_start,
            "line_end": self.line_end,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CodeBlock":
        return cls(
            language=data.get("language", "python"),
            code=data.get("code", ""),
            description=data.get("description"),
            line_start=data.get("line_start"),
            line_end=data.get("line_end"),
        )


@dataclass
class Parameter:
    """参数信息"""
    name: str
    type: str
    description: str = ""
    required: bool = True
    default: str | None = None
    example: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
            "default": self.default,
            "example": self.example,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Parameter":
        return cls(
            name=data.get("name", ""),
            type=data.get("type", "any"),
            description=data.get("description", ""),
            required=data.get("required", True),
            default=data.get("default"),
            example=data.get("example"),
        )


@dataclass
class RelatedAPI:
    """相关 API"""
    name: str
    relationship: str  # "similar", "related", "requires", "used_by"
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "relationship": self.relationship,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RelatedAPI":
        return cls(
            name=data.get("name", ""),
            relationship=data.get("relationship", "related"),
            description=data.get("description"),
        )


@dataclass
class UnifiedEntry:
    """
    统一索引条目
    
    支持 API、事件、示例代码等多种类型的统一索引结构。
    """
    # 基本信息
    id: str
    name: str
    type: EntryType
    description: str
    
    # 分类信息
    module: str | None = None
    scope: EntryScope = EntryScope.UNKNOWN
    category: str | None = None
    tags: list[str] = field(default_factory=list)
    
    # 内容
    content: str = ""
    code_blocks: list[CodeBlock] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    return_type: str | None = None
    return_description: str | None = None
    
    # 关联信息
    related_apis: list[RelatedAPI] = field(default_factory=list)
    related_events: list[str] = field(default_factory=list)
    related_examples: list[str] = field(default_factory=list)
    
    # 示例专用字段
    example_category: ExampleCategory | None = None
    difficulty: DifficultyLevel | None = None
    prerequisites: list[str] = field(default_factory=list)
    
    # 元数据
    source: str = ""
    source_path: str = ""
    version: str = "1.0.0"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    
    # 检索增强
    keywords: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    embedding: list[float] | None = None
    popularity: int = 0
    
    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    @property
    def is_api(self) -> bool:
        return self.type == EntryType.API

    @property
    def is_event(self) -> bool:
        return self.type == EntryType.EVENT

    @property
    def is_example(self) -> bool:
        return self.type == EntryType.EXAMPLE

    def compute_id(self) -> str:
        """计算唯一 ID"""
        hash_input = f"{self.type.value}:{self.name}:{self.module or ''}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]

    def add_keyword(self, keyword: str) -> None:
        """添加关键词"""
        if keyword and keyword not in self.keywords:
            self.keywords.append(keyword)

    def add_tag(self, tag: str) -> None:
        """添加标签"""
        if tag and tag not in self.tags:
            self.tags.append(tag)

    def add_alias(self, alias: str) -> None:
        """添加别名"""
        if alias and alias not in self.aliases:
            self.aliases.append(alias)

    def add_code_block(self, code: str, language: str = "python", description: str | None = None) -> None:
        """添加代码块"""
        self.code_blocks.append(CodeBlock(
            language=language,
            code=code,
            description=description,
        ))

    def add_parameter(self, name: str, type: str, description: str = "", required: bool = True) -> None:
        """添加参数"""
        self.parameters.append(Parameter(
            name=name,
            type=type,
            description=description,
            required=required,
        ))

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "module": self.module,
            "scope": self.scope.value,
            "category": self.category,
            "tags": self.tags,
            "content": self.content,
            "code_blocks": [b.to_dict() for b in self.code_blocks],
            "parameters": [p.to_dict() for p in self.parameters],
            "return_type": self.return_type,
            "return_description": self.return_description,
            "related_apis": [a.to_dict() for a in self.related_apis],
            "related_events": self.related_events,
            "related_examples": self.related_examples,
            "example_category": self.example_category.value if self.example_category else None,
            "difficulty": self.difficulty.value if self.difficulty else None,
            "prerequisites": self.prerequisites,
            "source": self.source,
            "source_path": self.source_path,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "keywords": self.keywords,
            "aliases": self.aliases,
            "popularity": self.popularity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UnifiedEntry":
        """从字典创建"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            type=EntryType(data.get("type", "api")),
            description=data.get("description", ""),
            module=data.get("module"),
            scope=EntryScope(data.get("scope", "unknown")),
            category=data.get("category"),
            tags=data.get("tags", []),
            content=data.get("content", ""),
            code_blocks=[CodeBlock.from_dict(b) for b in data.get("code_blocks", [])],
            parameters=[Parameter.from_dict(p) for p in data.get("parameters", [])],
            return_type=data.get("return_type"),
            return_description=data.get("return_description"),
            related_apis=[RelatedAPI.from_dict(a) for a in data.get("related_apis", [])],
            related_events=data.get("related_events", []),
            related_examples=data.get("related_examples", []),
            example_category=ExampleCategory(data["example_category"]) if data.get("example_category") else None,
            difficulty=DifficultyLevel(data["difficulty"]) if data.get("difficulty") else None,
            prerequisites=data.get("prerequisites", []),
            source=data.get("source", ""),
            source_path=data.get("source_path", ""),
            version=data.get("version", "1.0.0"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            keywords=data.get("keywords", []),
            aliases=data.get("aliases", []),
            popularity=data.get("popularity", 0),
        )

    @classmethod
    def create_api(
        cls,
        name: str,
        description: str,
        module: str | None = None,
        scope: EntryScope = EntryScope.UNKNOWN,
        **kwargs: Any,
    ) -> "UnifiedEntry":
        """创建 API 条目"""
        entry = cls(
            id="",
            name=name,
            type=EntryType.API,
            description=description,
            module=module,
            scope=scope,
            **kwargs,
        )
        entry.id = entry.compute_id()
        return entry

    @classmethod
    def create_event(
        cls,
        name: str,
        description: str,
        module: str | None = None,
        scope: EntryScope = EntryScope.UNKNOWN,
        **kwargs: Any,
    ) -> "UnifiedEntry":
        """创建事件条目"""
        entry = cls(
            id="",
            name=name,
            type=EntryType.EVENT,
            description=description,
            module=module,
            scope=scope,
            **kwargs,
        )
        entry.id = entry.compute_id()
        return entry

    @classmethod
    def create_example(
        cls,
        name: str,
        description: str,
        category: ExampleCategory = ExampleCategory.BASIC,
        difficulty: DifficultyLevel = DifficultyLevel.BEGINNER,
        **kwargs: Any,
    ) -> "UnifiedEntry":
        """创建示例条目"""
        entry = cls(
            id="",
            name=name,
            type=EntryType.EXAMPLE,
            description=description,
            example_category=category,
            difficulty=difficulty,
            **kwargs,
        )
        entry.id = entry.compute_id()
        return entry


@dataclass
class IndexStats:
    """索引统计"""
    total_entries: int = 0
    by_type: dict[str, int] = field(default_factory=dict)
    by_module: dict[str, int] = field(default_factory=dict)
    by_scope: dict[str, int] = field(default_factory=dict)
    last_updated: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_entries": self.total_entries,
            "by_type": self.by_type,
            "by_module": self.by_module,
            "by_scope": self.by_scope,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IndexStats":
        return cls(
            total_entries=data.get("total_entries", 0),
            by_type=data.get("by_type", {}),
            by_module=data.get("by_module", {}),
            by_scope=data.get("by_scope", {}),
            last_updated=datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else None,
        )