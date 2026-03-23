"""
Tool Registry Module

工具注册中心，提供工具的注册、发现和分类管理。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

__all__ = [
    "ToolRegistry",
    "ToolMetadata",
    "ToolCategory",
    "ToolStatus",
    "ToolRegistrationError",
    "create_tool_registry",
]


class ToolCategory(Enum):
    """工具类别"""

    FILE = "file"
    WEB = "web"
    CODE = "code"
    GIT = "git"
    SEARCH = "search"
    SYSTEM = "system"
    KNOWLEDGE = "knowledge"
    UTILITY = "utility"
    CUSTOM = "custom"


class ToolStatus(Enum):
    """工具状态"""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"
    ERROR = "error"


class ToolRegistrationError(Exception):
    """工具注册错误"""

    pass


@dataclass
class ToolMetadata:
    """
    工具元数据

    Attributes:
        name: 工具名称
        description: 工具描述
        version: 版本号
        category: 类别
        tags: 标签列表
        author: 作者
        created_at: 创建时间
        updated_at: 更新时间
        status: 状态
        input_schema: 输入参数 Schema
        output_schema: 输出结果 Schema
        examples: 使用示例
        dependencies: 依赖的工具
        config: 配置项
        stats: 统计信息
    """

    name: str
    description: str = ""
    version: str = "1.0.0"
    category: ToolCategory = ToolCategory.UTILITY
    tags: list[str] = field(default_factory=list)
    author: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: ToolStatus = ToolStatus.ACTIVE
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    examples: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category.value,
            "tags": self.tags,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "examples": self.examples,
            "dependencies": self.dependencies,
            "config": self.config,
            "stats": self.stats,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolMetadata:
        """从字典创建"""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            category=ToolCategory(data.get("category", "utility")),
            tags=data.get("tags", []),
            author=data.get("author", ""),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.now(),
            status=ToolStatus(data.get("status", "active")),
            input_schema=data.get("input_schema", {}),
            output_schema=data.get("output_schema", {}),
            examples=data.get("examples", []),
            dependencies=data.get("dependencies", []),
            config=data.get("config", {}),
            stats=data.get("stats", {}),
        )

    def update_stats(self, key: str, value: Any) -> None:
        """更新统计信息"""
        self.stats[key] = value
        self.updated_at = datetime.now()


class ToolRegistry:
    """
    工具注册中心

    管理工具的注册、发现、分类和生命周期。

    Example:
        >>> registry = ToolRegistry()
        >>> registry.register("read_file", handler=read_file, category=ToolCategory.FILE)
        >>> tool = registry.get("read_file")
        >>> tools = registry.list_tools(category=ToolCategory.FILE)
    """

    def __init__(self, name: str = "default"):
        """
        初始化工具注册中心

        Args:
            name: 注册中心名称
        """
        self.name = name
        self._tools: dict[str, tuple[ToolMetadata, Callable[..., Any]]] = {}
        self._categories: dict[ToolCategory, set[str]] = {
            cat: set() for cat in ToolCategory
        }
        self._tags: dict[str, set[str]] = {}

    @property
    def tool_count(self) -> int:
        """获取工具数量"""
        return len(self._tools)

    def register(
        self,
        name: str,
        handler: Callable[..., Any],
        description: str = "",
        version: str = "1.0.0",
        category: ToolCategory = ToolCategory.UTILITY,
        tags: list[str] | None = None,
        author: str = "",
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
        examples: list[dict[str, Any]] | None = None,
        dependencies: list[str] | None = None,
        config: dict[str, Any] | None = None,
        overwrite: bool = False,
    ) -> ToolMetadata:
        """
        注册工具

        Args:
            name: 工具名称
            handler: 处理函数
            description: 描述
            version: 版本
            category: 类别
            tags: 标签
            author: 作者
            input_schema: 输入 Schema
            output_schema: 输出 Schema
            examples: 示例
            dependencies: 依赖
            config: 配置
            overwrite: 是否覆盖已存在的工具

        Returns:
            工具元数据

        Raises:
            ToolRegistrationError: 注册失败
        """
        if not name:
            raise ToolRegistrationError("Tool name cannot be empty")

        if not callable(handler):
            raise ToolRegistrationError("Handler must be callable")

        if name in self._tools and not overwrite:
            raise ToolRegistrationError(f"Tool '{name}' already registered")

        # 检查依赖
        if dependencies:
            missing = [d for d in dependencies if d not in self._tools]
            if missing:
                raise ToolRegistrationError(f"Missing dependencies: {missing}")

        metadata = ToolMetadata(
            name=name,
            description=description,
            version=version,
            category=category,
            tags=tags or [],
            author=author,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
            examples=examples or [],
            dependencies=dependencies or [],
            config=config or {},
        )

        self._tools[name] = (metadata, handler)

        # 更新类别索引
        self._categories[category].add(name)

        # 更新标签索引
        for tag in tags or []:
            if tag not in self._tags:
                self._tags[tag] = set()
            self._tags[tag].add(name)

        return metadata

    def unregister(self, name: str) -> bool:
        """
        注销工具

        Args:
            name: 工具名称

        Returns:
            是否注销成功
        """
        if name not in self._tools:
            return False

        metadata, _ = self._tools[name]

        # 从类别索引中移除
        self._categories[metadata.category].discard(name)

        # 从标签索引中移除
        for tag in metadata.tags:
            if tag in self._tags:
                self._tags[tag].discard(name)
                if not self._tags[tag]:
                    del self._tags[tag]

        del self._tools[name]
        return True

    def get(self, name: str) -> tuple[ToolMetadata, Callable[..., Any]] | None:
        """
        获取工具

        Args:
            name: 工具名称

        Returns:
            工具元数据和处理函数，或 None
        """
        return self._tools.get(name)

    def get_metadata(self, name: str) -> ToolMetadata | None:
        """
        获取工具元数据

        Args:
            name: 工具名称

        Returns:
            工具元数据或 None
        """
        result = self._tools.get(name)
        return result[0] if result else None

    def get_handler(self, name: str) -> Callable[..., Any] | None:
        """
        获取工具处理函数

        Args:
            name: 工具名称

        Returns:
            处理函数或 None
        """
        result = self._tools.get(name)
        return result[1] if result else None

    def list_tools(
        self,
        category: ToolCategory | None = None,
        status: ToolStatus | None = None,
        tags: list[str] | None = None,
    ) -> list[ToolMetadata]:
        """
        列出工具

        Args:
            category: 按类别过滤
            status: 按状态过滤
            tags: 按标签过滤

        Returns:
            工具元数据列表
        """
        results = []

        # 获取候选工具名称
        if category:
            candidate_names = self._categories.get(category, set())
        elif tags:
            candidate_names = set()
            for tag in tags:
                candidate_names.update(self._tags.get(tag, set()))
        else:
            candidate_names = set(self._tools.keys())

        for name in candidate_names:
            metadata, _ = self._tools[name]

            # 状态过滤
            if status and metadata.status != status:
                continue

            # 标签过滤（AND 逻辑）
            if tags and not all(tag in metadata.tags for tag in tags):
                continue

            results.append(metadata)

        return results

    def search(self, query: str) -> list[ToolMetadata]:
        """
        搜索工具

        Args:
            query: 搜索关键词

        Returns:
            匹配的工具列表
        """
        query_lower = query.lower()
        results = []

        for metadata, _ in self._tools.values():
            # 搜索名称、描述、标签
            if (
                query_lower in metadata.name.lower()
                or query_lower in metadata.description.lower()
                or any(query_lower in tag.lower() for tag in metadata.tags)
            ):
                results.append(metadata)

        return results

    def update_status(self, name: str, status: ToolStatus) -> bool:
        """
        更新工具状态

        Args:
            name: 工具名称
            status: 新状态

        Returns:
            是否更新成功
        """
        if name not in self._tools:
            return False

        metadata, handler = self._tools[name]
        metadata.status = status
        metadata.updated_at = datetime.now()
        self._tools[name] = (metadata, handler)
        return True

    def update_metadata(self, name: str, **kwargs: Any) -> bool:
        """
        更新工具元数据

        Args:
            name: 工具名称
            **kwargs: 要更新的字段

        Returns:
            是否更新成功
        """
        if name not in self._tools:
            return False

        metadata, handler = self._tools[name]

        for key, value in kwargs.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)

        metadata.updated_at = datetime.now()
        self._tools[name] = (metadata, handler)
        return True

    def record_call(self, name: str, success: bool, execution_time: float) -> bool:
        """
        记录工具调用

        Args:
            name: 工具名称
            success: 是否成功
            execution_time: 执行时间

        Returns:
            是否记录成功
        """
        if name not in self._tools:
            return False

        metadata, handler = self._tools[name]

        if "call_count" not in metadata.stats:
            metadata.stats["call_count"] = 0
        if "success_count" not in metadata.stats:
            metadata.stats["success_count"] = 0
        if "error_count" not in metadata.stats:
            metadata.stats["error_count"] = 0
        if "total_time" not in metadata.stats:
            metadata.stats["total_time"] = 0.0

        metadata.stats["call_count"] += 1
        metadata.stats["total_time"] += execution_time

        if success:
            metadata.stats["success_count"] += 1
        else:
            metadata.stats["error_count"] += 1

        metadata.updated_at = datetime.now()
        self._tools[name] = (metadata, handler)
        return True

    def get_categories(self) -> list[ToolCategory]:
        """
        获取所有使用的类别

        Returns:
            类别列表
        """
        return [cat for cat, tools in self._categories.items() if tools]

    def get_tags(self) -> list[str]:
        """
        获取所有使用的标签

        Returns:
            标签列表
        """
        return list(self._tags.keys())

    def export_registry(self) -> dict[str, Any]:
        """
        导出注册中心数据

        Returns:
            注册中心数据字典
        """
        return {
            "name": self.name,
            "tools": {
                name: metadata.to_dict()
                for name, (metadata, _) in self._tools.items()
            },
            "exported_at": datetime.now().isoformat(),
        }

    def import_registry(
        self,
        data: dict[str, Any],
        handlers: dict[str, Callable[..., Any]] | None = None,
    ) -> int:
        """
        导入注册中心数据

        Args:
            data: 注册中心数据
            handlers: 处理函数映射

        Returns:
            导入的工具数量
        """
        count = 0
        handlers = handlers or {}

        for name, tool_data in data.get("tools", {}).items():
            handler = handlers.get(name)
            if not handler:
                continue

            metadata = ToolMetadata.from_dict(tool_data)
            self._tools[name] = (metadata, handler)
            self._categories[metadata.category].add(name)

            for tag in metadata.tags:
                if tag not in self._tags:
                    self._tags[tag] = set()
                self._tags[tag].add(name)

            count += 1

        return count

    def save_to_file(self, path: str | Path) -> bool:
        """
        保存到文件

        Args:
            path: 文件路径

        Returns:
            是否保存成功
        """
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.export_registry(), f, ensure_ascii=False, indent=2)

            return True
        except Exception:
            return False

    def load_from_file(
        self,
        path: str | Path,
        handlers: dict[str, Callable[..., Any]] | None = None,
    ) -> int:
        """
        从文件加载

        Args:
            path: 文件路径
            handlers: 处理函数映射

        Returns:
            加载的工具数量
        """
        try:
            path = Path(path)
            if not path.exists():
                return 0

            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            return self.import_registry(data, handlers)
        except Exception:
            return 0

    def clear(self) -> None:
        """清空所有工具"""
        self._tools.clear()
        for cat in self._categories:
            self._categories[cat].clear()
        self._tags.clear()


def create_tool_registry(name: str = "default") -> ToolRegistry:
    """
    创建工具注册中心

    Args:
        name: 注册中心名称

    Returns:
        工具注册中心实例
    """
    return ToolRegistry(name=name)