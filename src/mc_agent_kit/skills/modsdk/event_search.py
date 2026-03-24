"""
ModSDK 事件检索 Skill

提供 ModSDK 事件文档的检索功能。
"""

from __future__ import annotations
import logging

from ...knowledge_base import KnowledgeRetriever, Scope
from ..base import BaseSkill, SkillCategory, SkillMetadata, SkillPriority, SkillResult

logger = logging.getLogger(__name__)


class ModSDKEventSearchSkill(BaseSkill):
    """ModSDK 事件检索 Skill

    提供 ModSDK 事件文档的检索功能，支持：
    - 关键词搜索
    - 模块过滤
    - 作用域过滤（客户端/服务端）
    - 参数名搜索
    - 模糊搜索

    使用示例:
        skill = ModSDKEventSearchSkill()
        skill.initialize()

        # 搜索事件
        result = skill.execute(query="hurt", scope="server")

        # 获取指定事件
        result = skill.execute(name="AddEntityClientEvent")

        # 按模块搜索
        result = skill.execute(query="player", module="玩家")
    """

    def __init__(self, kb_path: str | None = None):
        """初始化 Skill

        Args:
            kb_path: 知识库文件路径，默认使用内置路径
        """
        super().__init__(
            metadata=SkillMetadata(
                name="modsdk-event-search",
                description="搜索 ModSDK 事件文档，支持关键词、模块、作用域过滤",
                version="1.0.0",
                author="MC-Agent-Kit",
                category=SkillCategory.SEARCH,
                priority=SkillPriority.HIGH,
                tags=["modsdk", "event", "search", "documentation"],
                examples=[
                    "搜索包含 hurt 关键词的事件: execute(query='hurt')",
                    "搜索服务端玩家事件: execute(query='player', scope='server')",
                    "获取指定事件详情: execute(name='AddEntityClientEvent')",
                    "按模块搜索: execute(module='实体')",
                ],
            )
        )
        self._kb_path = kb_path
        self._retriever: KnowledgeRetriever | None = None

    def initialize(self) -> bool:
        """初始化知识库检索器

        Returns:
            bool: 初始化是否成功
        """
        if self._initialized:
            return True

        try:
            self._retriever = KnowledgeRetriever()

            # 尝试加载知识库
            if self._kb_path:
                self._retriever.load(self._kb_path)
                logger.info(f"已从 {self._kb_path} 加载知识库")
            else:
                # 尝试默认路径
                from pathlib import Path

                default_path = (
                    Path(__file__).parent.parent.parent.parent.parent
                    / "data"
                    / "knowledge_base.json"
                )
                if default_path.exists():
                    self._retriever.load(str(default_path))
                    logger.info(f"已从默认路径加载知识库: {default_path}")
                else:
                    logger.warning(f"知识库文件不存在: {default_path}")

            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"初始化知识库失败: {e}")
            return False

    def execute(
        self,
        query: str | None = None,
        name: str | None = None,
        module: str | None = None,
        scope: str | None = None,
        param_name: str | None = None,
        fuzzy: bool = False,
        limit: int = 10,
        **kwargs,
    ) -> SkillResult:
        """执行事件搜索

        Args:
            query: 搜索关键词（在名称、描述、参数中搜索）
            name: 精确匹配事件名称（优先级最高）
            module: 按模块过滤
            scope: 按作用域过滤 ("client", "server", "both")
            param_name: 按参数名搜索
            fuzzy: 是否使用模糊搜索
            limit: 返回结果数量限制

        Returns:
            SkillResult: 搜索结果
        """
        if not self._initialized:
            self.initialize()

        if not self._retriever:
            return SkillResult(
                success=False,
                error="知识库未初始化",
                message="请先调用 initialize() 加载知识库",
            )

        try:
            # 精确获取指定事件
            if name:
                event = self._retriever.get_event(name)
                if event:
                    return SkillResult(
                        success=True,
                        data=[self._format_event(event)],
                        message=f"找到事件: {name}",
                    )
                return SkillResult(
                    success=False,
                    error=f"未找到事件: {name}",
                    suggestions=self._retriever.suggest(name, limit=5),
                )

            # 按参数名搜索
            if param_name:
                events = self._retriever.search_by_parameter(param_name, entry_type="event")
                return SkillResult(
                    success=True,
                    data=[self._format_event(event) for event in events[:limit]],
                    message=f"找到 {len(events)} 个包含参数 {param_name} 的事件",
                )

            # 模糊搜索
            if fuzzy and query:
                results = self._retriever.fuzzy_search(
                    query, entry_type="event", limit=limit
                )
                events = [
                    self._format_event(r[0], relevance_score=1.0 - r[1] / 10)
                    for r in results
                ]
                return SkillResult(
                    success=True,
                    data=events,
                    message=f"模糊搜索找到 {len(events)} 个事件",
                )

            # 普通搜索
            if query:
                scope_enum = self._parse_scope(scope) if scope else None
                events = self._retriever.search_event(query, module=module, scope=scope_enum)
                results = [self._format_event(event) for event in events[:limit]]
                return SkillResult(
                    success=True,
                    data=results,
                    message=f"找到 {len(events)} 个匹配的事件",
                    metadata={"query": query, "module": module, "scope": scope},
                )

            # 只按模块过滤
            if module:
                events = self._retriever.list_events_by_module(module)
                return SkillResult(
                    success=True,
                    data=[self._format_event(e) for e in events[:limit]],
                    message=f"模块 {module} 包含 {len(events)} 个事件",
                )

            # 无参数，返回提示
            return SkillResult(
                success=False,
                error="请提供搜索参数",
                message="请提供 query、name、module 或 param_name 参数",
                suggestions=[
                    "使用 query 参数搜索事件",
                    "使用 name 参数精确获取事件",
                    "使用 module 参数按模块过滤",
                    "使用 scope 参数按作用域过滤",
                ],
            )

        except Exception as e:
            logger.error(f"事件搜索失败: {e}")
            return SkillResult(
                success=False,
                error=str(e),
                message="事件搜索失败",
            )

    def _format_event(self, event, relevance_score: float = 1.0) -> dict:
        """格式化事件条目为返回格式

        Args:
            event: EventEntry 对象
            relevance_score: 相关度分数

        Returns:
            dict: 格式化后的事件信息
        """
        return {
            "name": event.name,
            "module": event.module,
            "description": event.description,
            "scope": event.scope.value,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.data_type,
                    "description": p.description,
                    "mutable": p.mutable,
                }
                for p in event.parameters
            ],
            "return_value": event.return_value,
            "examples": [e.code for e in event.examples] if event.examples else [],
            "remarks": event.remarks,
            "relevance_score": relevance_score,
        }

    def _parse_scope(self, scope: str) -> Scope:
        """解析作用域字符串

        Args:
            scope: 作用域字符串

        Returns:
            Scope: 作用域枚举值
        """
        scope_map = {
            "client": Scope.CLIENT,
            "server": Scope.SERVER,
            "both": Scope.BOTH,
            "客户端": Scope.CLIENT,
            "服务端": Scope.SERVER,
            "双端": Scope.BOTH,
        }
        return scope_map.get(scope.lower(), Scope.UNKNOWN)

    def list_modules(self) -> SkillResult:
        """列出所有事件模块

        Returns:
            SkillResult: 模块列表
        """
        if not self._initialized:
            self.initialize()

        if not self._retriever:
            return SkillResult(
                success=False,
                error="知识库未初始化",
            )

        modules = self._retriever.list_modules(entry_type="event")
        return SkillResult(
            success=True,
            data=modules,
            message=f"共 {len(modules)} 个事件模块",
        )

    def get_stats(self) -> SkillResult:
        """获取知识库统计信息

        Returns:
            SkillResult: 统计信息
        """
        if not self._initialized:
            self.initialize()

        if not self._retriever:
            return SkillResult(
                success=False,
                error="知识库未初始化",
            )

        stats = self._retriever.get_stats()
        return SkillResult(
            success=True,
            data=stats,
            message="知识库统计信息",
        )
