"""
Skill 基类定义

定义 Agent Skill 的基础接口和元数据格式。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SkillCategory(Enum):
    """Skill 分类"""

    SEARCH = "search"  # 搜索类
    CODE_GEN = "code_gen"  # 代码生成类
    DEBUG = "debug"  # 调试类
    ANALYSIS = "analysis"  # 分析类
    UTILITY = "utility"  # 工具类


class SkillPriority(Enum):
    """Skill 优先级"""

    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class SkillMetadata:
    """Skill 元数据"""

    name: str  # Skill 名称（唯一标识）
    description: str  # 功能描述
    version: str = "1.0.0"  # 版本号
    author: str = "MC-Agent-Kit"  # 作者
    category: SkillCategory = SkillCategory.UTILITY  # 分类
    priority: SkillPriority = SkillPriority.MEDIUM  # 优先级
    tags: list[str] = field(default_factory=list)  # 标签
    examples: list[str] = field(default_factory=list)  # 使用示例
    dependencies: list[str] = field(default_factory=list)  # 依赖的其他 Skill
    min_kb_version: str | None = None  # 最低知识库版本要求

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "category": self.category.value,
            "priority": self.priority.value,
            "tags": self.tags,
            "examples": self.examples,
            "dependencies": self.dependencies,
            "min_kb_version": self.min_kb_version,
        }


@dataclass
class SkillResult:
    """Skill 执行结果"""

    success: bool  # 是否成功
    data: Any = None  # 返回数据
    message: str = ""  # 结果消息
    error: str | None = None  # 错误信息
    suggestions: list[str] = field(default_factory=list)  # 后续建议
    metadata: dict[str, Any] = field(default_factory=dict)  # 额外元数据

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "error": self.error,
            "suggestions": self.suggestions,
            "metadata": self.metadata,
        }


class BaseSkill(ABC):
    """Skill 基类

    所有 Skill 必须继承此基类并实现 execute 方法。

    使用示例:
        class APISearchSkill(BaseSkill):
            def __init__(self):
                super().__init__(
                    metadata=SkillMetadata(
                        name="modsdk-api-search",
                        description="搜索 ModSDK API 文档",
                        category=SkillCategory.SEARCH,
                    )
                )

            def execute(self, query: str, **kwargs) -> SkillResult:
                # 实现搜索逻辑
                results = self._search_api(query)
                return SkillResult(
                    success=True,
                    data=results,
                    message=f"找到 {len(results)} 个结果"
                )
    """

    def __init__(self, metadata: SkillMetadata):
        """初始化 Skill

        Args:
            metadata: Skill 元数据
        """
        self._metadata = metadata
        self._initialized = False

    @property
    def metadata(self) -> SkillMetadata:
        """获取 Skill 元数据"""
        return self._metadata

    @property
    def name(self) -> str:
        """获取 Skill 名称"""
        return self._metadata.name

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> SkillResult:
        """执行 Skill

        子类必须实现此方法。

        Returns:
            SkillResult: 执行结果
        """
        pass

    def validate(self, *args: Any, **kwargs: Any) -> bool:
        """验证输入参数

        子类可覆盖此方法实现参数验证。

        Returns:
            bool: 参数是否有效
        """
        return True

    def initialize(self) -> bool:
        """初始化 Skill

        子类可覆盖此方法实现延迟初始化（如加载知识库）。

        Returns:
            bool: 初始化是否成功
        """
        self._initialized = True
        return True

    def cleanup(self) -> None:
        """清理资源

        子类可覆盖此方法实现资源清理。
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, version={self._metadata.version})"


class SkillRegistry:
    """Skill 注册表

    管理 Skill 的注册、发现和调用。

    使用示例:
        registry = SkillRegistry()

        # 注册 Skill
        registry.register(APISearchSkill())

        # 获取 Skill
        skill = registry.get("modsdk-api-search")

        # 执行 Skill
        result = skill.execute(query="GetEngineType")
    """

    def __init__(self) -> None:
        """初始化注册表"""
        self._skills: dict[str, BaseSkill] = {}
        self._categories: dict[SkillCategory, list[str]] = {
            cat: [] for cat in SkillCategory
        }

    def register(self, skill: BaseSkill) -> None:
        """注册 Skill

        Args:
            skill: 要注册的 Skill 实例

        Raises:
            ValueError: 如果 Skill 名称已存在
        """
        name = skill.name
        if name in self._skills:
            raise ValueError(f"Skill '{name}' already registered")

        self._skills[name] = skill
        self._categories[skill.metadata.category].append(name)

    def unregister(self, name: str) -> bool:
        """注销 Skill

        Args:
            name: Skill 名称

        Returns:
            bool: 是否成功注销
        """
        if name not in self._skills:
            return False

        skill = self._skills[name]
        del self._skills[name]
        self._categories[skill.metadata.category].remove(name)
        skill.cleanup()
        return True

    def get(self, name: str) -> BaseSkill | None:
        """获取 Skill

        Args:
            name: Skill 名称

        Returns:
            BaseSkill | None: Skill 实例，不存在则返回 None
        """
        return self._skills.get(name)

    def has(self, name: str) -> bool:
        """检查 Skill 是否已注册

        Args:
            name: Skill 名称

        Returns:
            bool: 是否已注册
        """
        return name in self._skills

    def list_all(self) -> list[SkillMetadata]:
        """列出所有 Skill 元数据

        Returns:
            list[SkillMetadata]: 所有 Skill 元数据列表
        """
        return [skill.metadata for skill in self._skills.values()]

    def list_by_category(self, category: SkillCategory) -> list[BaseSkill]:
        """按分类获取 Skill

        Args:
            category: Skill 分类

        Returns:
            list[BaseSkill]: 该分类下的 Skill 列表
        """
        names = self._categories.get(category, [])
        return [self._skills[name] for name in names if name in self._skills]

    def search(self, keyword: str) -> list[BaseSkill]:
        """按关键词搜索 Skill

        搜索范围：名称、描述、标签

        Args:
            keyword: 搜索关键词

        Returns:
            list[BaseSkill]: 匹配的 Skill 列表
        """
        keyword_lower = keyword.lower()
        results = []

        for skill in self._skills.values():
            meta = skill.metadata
            # 名称匹配
            if keyword_lower in meta.name.lower():
                results.append(skill)
                continue
            # 描述匹配
            if keyword_lower in meta.description.lower():
                results.append(skill)
                continue
            # 标签匹配
            for tag in meta.tags:
                if keyword_lower in tag.lower():
                    results.append(skill)
                    break

        return results

    def initialize_all(self) -> dict[str, bool]:
        """初始化所有 Skill

        Returns:
            dict[str, bool]: Skill 名称 -> 初始化结果
        """
        results = {}
        for name, skill in self._skills.items():
            try:
                results[name] = skill.initialize()
            except Exception:
                results[name] = False
        return results

    def cleanup_all(self) -> None:
        """清理所有 Skill 资源"""
        for skill in self._skills.values():
            try:
                skill.cleanup()
            except Exception:
                pass

    def __len__(self) -> int:
        return len(self._skills)

    def __contains__(self, name: str) -> bool:
        return name in self._skills


# 全局注册表实例
_global_registry: SkillRegistry | None = None


def get_registry() -> SkillRegistry:
    """获取全局 Skill 注册表

    Returns:
        SkillRegistry: 全局注册表实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = SkillRegistry()
    return _global_registry


def register_skill(skill: BaseSkill) -> None:
    """注册 Skill 到全局注册表

    Args:
        skill: 要注册的 Skill 实例
    """
    get_registry().register(skill)


def get_skill(name: str) -> BaseSkill | None:
    """从全局注册表获取 Skill

    Args:
        name: Skill 名称

    Returns:
        BaseSkill | None: Skill 实例
    """
    return get_registry().get(name)
