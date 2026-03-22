"""
插件市场原型

提供插件发现、安装和管理的功能。
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.request import urlopen
from urllib.error import URLError

logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    """插件状态"""

    AVAILABLE = "available"  # 可安装
    INSTALLED = "installed"  # 已安装
    UPDATE_AVAILABLE = "update_available"  # 有更新
    DEPRECATED = "deprecated"  # 已弃用


class PluginCategory(Enum):
    """插件类别"""

    CODE_GEN = "code_gen"  # 代码生成
    DEBUG = "debug"  # 调试工具
    OPTIMIZATION = "optimization"  # 性能优化
    UI = "ui"  # 界面增强
    INTEGRATION = "integration"  # 集成工具
    TEMPLATE = "template"  # 模板扩展
    UTILITY = "utility"  # 实用工具


@dataclass
class PluginMarketInfo:
    """插件市场信息"""

    id: str  # 插件唯一标识
    name: str  # 插件名称
    version: str  # 最新版本
    description: str  # 描述
    author: str  # 作者
    category: PluginCategory  # 类别
    status: PluginStatus = PluginStatus.AVAILABLE
    installed_version: str | None = None
    downloads: int = 0
    rating: float = 0.0
    tags: list[str] = field(default_factory=list)
    homepage: str | None = None
    repository: str | None = None
    dependencies: list[str] = field(default_factory=list)
    compatibility: str = ">=1.0.0"  # 兼容的核心版本
    last_updated: str | None = None
    changelog: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "category": self.category.value,
            "status": self.status.value,
            "installed_version": self.installed_version,
            "downloads": self.downloads,
            "rating": self.rating,
            "tags": self.tags,
            "homepage": self.homepage,
            "repository": self.repository,
            "dependencies": self.dependencies,
            "compatibility": self.compatibility,
            "last_updated": self.last_updated,
            "changelog": self.changelog,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PluginMarketInfo":
        return cls(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            description=data["description"],
            author=data["author"],
            category=PluginCategory(data.get("category", "utility")),
            status=PluginStatus(data.get("status", "available")),
            installed_version=data.get("installed_version"),
            downloads=data.get("downloads", 0),
            rating=data.get("rating", 0.0),
            tags=data.get("tags", []),
            homepage=data.get("homepage"),
            repository=data.get("repository"),
            dependencies=data.get("dependencies", []),
            compatibility=data.get("compatibility", ">=1.0.0"),
            last_updated=data.get("last_updated"),
            changelog=data.get("changelog", []),
        )


@dataclass
class MarketplaceConfig:
    """市场配置"""

    registry_url: str = "https://plugins.mc-agent-kit.dev/registry.json"
    cache_dir: Path = Path(".mc_agent_kit/plugins/cache")
    cache_ttl: int = 3600  # 缓存过期时间 (秒)
    auto_update: bool = False
    include_prerelease: bool = False


@dataclass
class SearchResult:
    """搜索结果"""

    plugins: list[PluginMarketInfo]
    total: int
    query: str
    page: int = 1
    per_page: int = 20

    def to_dict(self) -> dict[str, Any]:
        return {
            "plugins": [p.to_dict() for p in self.plugins],
            "total": self.total,
            "query": self.query,
            "page": self.page,
            "per_page": self.per_page,
        }


class PluginMarketplace:
    """插件市场

    提供插件发现、搜索、安装和更新功能。

    使用示例:
        marketplace = PluginMarketplace()
        results = marketplace.search("code generation")
        for plugin in results.plugins:
            print(f"{plugin.name}: {plugin.description}")
    """

    def __init__(self, config: MarketplaceConfig | None = None):
        """初始化插件市场

        Args:
            config: 市场配置
        """
        self.config = config or MarketplaceConfig()
        self._cache: dict[str, PluginMarketInfo] = {}
        self._cache_time: float = 0
        self._installed: dict[str, str] = {}  # id -> version

    def refresh(self, force: bool = False) -> int:
        """刷新插件索引

        Args:
            force: 是否强制刷新

        Returns:
            刷新的插件数量
        """
        import time

        current_time = time.time()

        # 检查缓存是否过期
        if not force and self._cache and (current_time - self._cache_time) < self.config.cache_ttl:
            return len(self._cache)

        # 尝试从远程获取
        try:
            data = self._fetch_registry()
            self._cache = {
                info["id"]: PluginMarketInfo.from_dict(info) for info in data.get("plugins", [])
            }
            self._cache_time = current_time
            logger.info(f"刷新插件索引: {len(self._cache)} 个插件")
            return len(self._cache)
        except Exception as e:
            logger.warning(f"刷新插件索引失败: {e}")
            # 使用本地缓存或内置插件列表
            if not self._cache:
                self._cache = self._get_builtin_plugins()
                self._cache_time = current_time
            return len(self._cache)

    def _fetch_registry(self) -> dict[str, Any]:
        """从远程获取插件注册表"""
        try:
            with urlopen(self.config.registry_url, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except URLError as e:
            raise RuntimeError(f"无法访问插件注册表: {e}") from e

    def _get_builtin_plugins(self) -> dict[str, PluginMarketInfo]:
        """获取内置插件列表"""
        return {
            "modsdk-codegen": PluginMarketInfo(
                id="modsdk-codegen",
                name="ModSDK Code Generator",
                version="1.0.0",
                description="增强的代码生成工具，提供更多模板和自定义选项",
                author="MC-Agent-Kit",
                category=PluginCategory.CODE_GEN,
                tags=["code", "generation", "template"],
            ),
            "modsdk-debugger": PluginMarketInfo(
                id="modsdk-debugger",
                name="ModSDK Debugger",
                version="1.0.0",
                description="高级调试工具，支持断点、变量监视和调用栈追踪",
                author="MC-Agent-Kit",
                category=PluginCategory.DEBUG,
                tags=["debug", "trace", "breakpoint"],
            ),
            "modsdk-optimizer": PluginMarketInfo(
                id="modsdk-optimizer",
                name="ModSDK Optimizer",
                version="1.0.0",
                description="代码优化工具，分析和优化 ModSDK 代码性能",
                author="MC-Agent-Kit",
                category=PluginCategory.OPTIMIZATION,
                tags=["performance", "optimization"],
            ),
            "modsdk-linter": PluginMarketInfo(
                id="modsdk-linter",
                name="ModSDK Linter",
                version="1.0.0",
                description="代码检查工具，检查代码质量和 ModSDK 最佳实践",
                author="MC-Agent-Kit",
                category=PluginCategory.UTILITY,
                tags=["lint", "quality", "best-practices"],
            ),
        }

    def search(
        self,
        query: str,
        category: PluginCategory | None = None,
        tags: list[str] | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> SearchResult:
        """搜索插件

        Args:
            query: 搜索关键词
            category: 可选的类别过滤
            tags: 可选的标签过滤
            page: 页码
            per_page: 每页数量

        Returns:
            搜索结果
        """
        self.refresh()

        query_lower = query.lower()
        results = []

        for plugin in self._cache.values():
            # 检查类别
            if category and plugin.category != category:
                continue

            # 检查标签
            if tags and not any(tag in plugin.tags for tag in tags):
                continue

            # 检查关键词
            if query_lower:
                if (
                    query_lower not in plugin.name.lower()
                    and query_lower not in plugin.description.lower()
                    and query_lower not in plugin.author.lower()
                    and not any(query_lower in tag.lower() for tag in plugin.tags)
                ):
                    continue

            # 更新安装状态
            if plugin.id in self._installed:
                plugin.status = PluginStatus.INSTALLED
                plugin.installed_version = self._installed[plugin.id]

            results.append(plugin)

        # 按评分和下载量排序
        results.sort(key=lambda p: (p.rating, p.downloads), reverse=True)

        # 分页
        start = (page - 1) * per_page
        end = start + per_page
        paged_results = results[start:end]

        return SearchResult(
            plugins=paged_results,
            total=len(results),
            query=query,
            page=page,
            per_page=per_page,
        )

    def get_plugin(self, plugin_id: str) -> PluginMarketInfo | None:
        """获取插件详情

        Args:
            plugin_id: 插件 ID

        Returns:
            插件信息，不存在则返回 None
        """
        self.refresh()
        plugin = self._cache.get(plugin_id)
        if plugin and plugin_id in self._installed:
            plugin.status = PluginStatus.INSTALLED
            plugin.installed_version = self._installed[plugin_id]
        return plugin

    def list_plugins(
        self,
        category: PluginCategory | None = None,
        installed_only: bool = False,
    ) -> list[PluginMarketInfo]:
        """列出插件

        Args:
            category: 可选的类别过滤
            installed_only: 是否只列出已安装的

        Returns:
            插件列表
        """
        self.refresh()

        results = []
        for plugin in self._cache.values():
            if category and plugin.category != category:
                continue
            if installed_only and plugin.id not in self._installed:
                continue

            if plugin.id in self._installed:
                plugin.status = PluginStatus.INSTALLED
                plugin.installed_version = self._installed[plugin.id]

            results.append(plugin)

        return results

    def install(self, plugin_id: str, version: str | None = None) -> tuple[bool, str]:
        """安装插件

        Args:
            plugin_id: 插件 ID
            version: 可选的版本号

        Returns:
            (是否成功, 消息)
        """
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return False, f"插件不存在: {plugin_id}"

        if plugin_id in self._installed:
            return False, f"插件已安装: {plugin_id}"

        # 模拟安装过程
        target_version = version or plugin.version

        # 检查兼容性
        if not self._check_compatibility(plugin):
            return False, f"插件与当前版本不兼容: {plugin.compatibility}"

        # 检查依赖
        missing_deps = self._check_dependencies(plugin)
        if missing_deps:
            return False, f"缺少依赖: {', '.join(missing_deps)}"

        # 安装
        self._installed[plugin_id] = target_version
        plugin.status = PluginStatus.INSTALLED
        plugin.installed_version = target_version

        logger.info(f"安装插件: {plugin_id}@{target_version}")
        return True, f"成功安装 {plugin.name}@{target_version}"

    def uninstall(self, plugin_id: str) -> tuple[bool, str]:
        """卸载插件

        Args:
            plugin_id: 插件 ID

        Returns:
            (是否成功, 消息)
        """
        if plugin_id not in self._installed:
            return False, f"插件未安装: {plugin_id}"

        # 检查是否有其他插件依赖
        for plugin in self._cache.values():
            if plugin_id in plugin.dependencies and plugin.id in self._installed:
                return False, f"插件 {plugin.id} 依赖此插件"

        del self._installed[plugin_id]

        plugin = self._cache.get(plugin_id)
        if plugin:
            plugin.status = PluginStatus.AVAILABLE
            plugin.installed_version = None

        logger.info(f"卸载插件: {plugin_id}")
        return True, f"成功卸载 {plugin_id}"

    def update(self, plugin_id: str) -> tuple[bool, str]:
        """更新插件

        Args:
            plugin_id: 插件 ID

        Returns:
            (是否成功, 消息)
        """
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            return False, f"插件不存在: {plugin_id}"

        if plugin_id not in self._installed:
            return False, f"插件未安装: {plugin_id}"

        current_version = self._installed[plugin_id]
        if current_version == plugin.version:
            return True, "插件已是最新版本"

        # 更新
        self._installed[plugin_id] = plugin.version
        plugin.installed_version = plugin.version

        logger.info(f"更新插件: {plugin_id} {current_version} -> {plugin.version}")
        return True, f"成功更新 {plugin.name} 到 {plugin.version}"

    def _check_compatibility(self, plugin: PluginMarketInfo) -> bool:
        """检查插件兼容性"""
        # 简化实现：假设都兼容
        return True

    def _check_dependencies(self, plugin: PluginMarketInfo) -> list[str]:
        """检查依赖是否满足

        Returns:
            缺失的依赖列表
        """
        missing = []
        for dep in plugin.dependencies:
            if dep not in self._installed:
                missing.append(dep)
        return missing

    def get_categories(self) -> list[dict[str, str]]:
        """获取所有类别"""
        return [
            {"id": cat.value, "name": self._get_category_name(cat)}
            for cat in PluginCategory
        ]

    def _get_category_name(self, category: PluginCategory) -> str:
        """获取类别显示名称"""
        names = {
            PluginCategory.CODE_GEN: "代码生成",
            PluginCategory.DEBUG: "调试工具",
            PluginCategory.OPTIMIZATION: "性能优化",
            PluginCategory.UI: "界面增强",
            PluginCategory.INTEGRATION: "集成工具",
            PluginCategory.TEMPLATE: "模板扩展",
            PluginCategory.UTILITY: "实用工具",
        }
        return names.get(category, category.value)


def create_marketplace(config: MarketplaceConfig | None = None) -> PluginMarketplace:
    """创建插件市场的便捷函数"""
    return PluginMarketplace(config)