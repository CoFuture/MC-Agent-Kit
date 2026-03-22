"""
知识库检索器

提供知识库检索功能，支持关键词搜索、模块过滤、作用域过滤。
"""

import json
import logging
from pathlib import Path

from .models import APIEntry, EnumEntry, EventEntry, KnowledgeBase, Scope

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """知识库检索器

    提供多种检索方式：
    - 关键词搜索：在名称和描述中搜索
    - 模块过滤：按模块筛选结果
    - 作用域过滤：按客户端/服务端筛选
    - 类型过滤：按 API/事件/枚举筛选

    使用示例:
        retriever = KnowledgeRetriever()
        retriever.load("data/knowledge_base.json")

        # 搜索 API
        apis = retriever.search_api("entity", scope=Scope.SERVER)

        # 搜索事件
        events = retriever.search_event("hurt")

        # 通用搜索
        results = retriever.search("player", entry_type="api")
    """

    def __init__(self, kb: KnowledgeBase | None = None):
        """初始化检索器

        Args:
            kb: 可选的知识库对象，如不提供需要后续加载
        """
        self.kb = kb or KnowledgeBase()

    def load(self, path: str) -> None:
        """从 JSON 文件加载知识库

        Args:
            path: JSON 文件路径
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        self.kb = KnowledgeBase(
            version=data.get("version", "1.0.0"),
            source_dir=data.get("source_dir"),
        )

        # 加载 API
        for name, api_data in data.get("apis", {}).items():
            from .models import APIParameter

            api = APIEntry(
                name=api_data["name"],
                module=api_data["module"],
                description=api_data["description"],
                method_path=api_data.get("method_path", ""),
                scope=Scope(api_data.get("scope", "unknown")),
                parameters=[
                    APIParameter(
                        name=p["name"],
                        data_type=p["data_type"],
                        description=p["description"],
                        optional=p.get("optional", False),
                    )
                    for p in api_data.get("parameters", [])
                ],
                return_type=api_data.get("return_type"),
                return_description=api_data.get("return_description"),
                remarks=api_data.get("remarks", []),
                source_path=api_data.get("source_path"),
            )
            self.kb.add_api(api)

        # 加载事件
        for name, event_data in data.get("events", {}).items():
            from .models import EventParameter

            event = EventEntry(
                name=event_data["name"],
                module=event_data["module"],
                description=event_data["description"],
                scope=Scope(event_data.get("scope", "unknown")),
                parameters=[
                    EventParameter(
                        name=p["name"],
                        data_type=p["data_type"],
                        description=p["description"],
                        mutable=p.get("mutable", False),
                    )
                    for p in event_data.get("parameters", [])
                ],
                return_value=event_data.get("return_value"),
                remarks=event_data.get("remarks", []),
                source_path=event_data.get("source_path"),
            )
            self.kb.add_event(event)

        # 加载枚举
        for name, enum_data in data.get("enums", {}).items():
            from .models import EnumValue

            enum = EnumEntry(
                name=enum_data["name"],
                description=enum_data.get("description"),
                values=[
                    EnumValue(
                        name=v["name"],
                        value=v["value"],
                        description=v.get("description"),
                    )
                    for v in enum_data.get("values", [])
                ],
                source_path=enum_data.get("source_path"),
            )
            self.kb.add_enum(enum)

        logger.info(f"知识库加载完成: {self.kb.stats()}")

    def save(self, path: str) -> None:
        """保存知识库到 JSON 文件

        Args:
            path: JSON 文件路径
        """
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "w", encoding="utf-8") as f:
            json.dump(self.kb.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"知识库已保存到: {path}")

    def search(
        self,
        query: str,
        entry_type: str = "all",
        module: str | None = None,
        scope: Scope | None = None,
        limit: int = 20,
    ) -> list[APIEntry | EventEntry | EnumEntry]:
        """通用搜索

        在名称和描述中搜索关键词。

        Args:
            query: 搜索关键词
            entry_type: 条目类型 ("api", "event", "enum", "all")
            module: 可选的模块过滤
            scope: 可选的作用域过滤
            limit: 返回结果数量限制

        Returns:
            匹配的条目列表
        """
        results: list[APIEntry | EventEntry | EnumEntry] = []

        # 搜索 API
        if entry_type in ("api", "all"):
            results.extend(self.search_api(query, module, scope))

        # 搜索事件
        if entry_type in ("event", "all"):
            results.extend(self.search_event(query, module, scope))

        # 搜索枚举
        if entry_type in ("enum", "all"):
            results.extend(self.search_enum(query))

        # 按相关度排序（名称匹配优先）
        results = self._sort_by_relevance(results, query)

        return results[:limit]

    def search_api(
        self,
        keyword: str,
        module: str | None = None,
        scope: Scope | None = None,
    ) -> list[APIEntry]:
        """搜索 API

        Args:
            keyword: 搜索关键词
            module: 可选的模块过滤
            scope: 可选的作用域过滤

        Returns:
            匹配的 API 列表
        """
        results = []
        keyword_lower = keyword.lower()

        # 如果指定了模块，只在该模块中搜索
        if module:
            apis = self.kb.get_apis_by_module(module)
        else:
            apis = list(self.kb.apis.values())

        for api in apis:
            # 关键词匹配
            if not self._match_keyword(api, keyword_lower):
                continue

            # 作用域过滤
            if scope and api.scope != scope and api.scope != Scope.BOTH:
                continue

            results.append(api)

        return results

    def search_event(
        self,
        keyword: str,
        module: str | None = None,
        scope: Scope | None = None,
    ) -> list[EventEntry]:
        """搜索事件

        Args:
            keyword: 搜索关键词
            module: 可选的模块过滤
            scope: 可选的作用域过滤

        Returns:
            匹配的事件列表
        """
        results = []
        keyword_lower = keyword.lower()

        # 如果指定了模块，只在该模块中搜索
        if module:
            events = self.kb.get_events_by_module(module)
        else:
            events = list(self.kb.events.values())

        for event in events:
            # 关键词匹配
            if not self._match_keyword(event, keyword_lower):
                continue

            # 作用域过滤
            if scope and event.scope != scope and event.scope != Scope.BOTH:
                continue

            results.append(event)

        return results

    def search_enum(self, keyword: str) -> list[EnumEntry]:
        """搜索枚举

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的枚举列表
        """
        results = []
        keyword_lower = keyword.lower()

        for enum in self.kb.enums.values():
            if self._match_keyword(enum, keyword_lower):
                results.append(enum)

        return results

    def get_api(self, name: str) -> APIEntry | None:
        """获取指定名称的 API

        Args:
            name: API 名称

        Returns:
            API 条目，不存在则返回 None
        """
        return self.kb.get_api(name)

    def get_event(self, name: str) -> EventEntry | None:
        """获取指定名称的事件

        Args:
            name: 事件名称

        Returns:
            事件条目，不存在则返回 None
        """
        return self.kb.get_event(name)

    def get_enum(self, name: str) -> EnumEntry | None:
        """获取指定名称的枚举

        Args:
            name: 枚举名称

        Returns:
            枚举条目，不存在则返回 None
        """
        return self.kb.enums.get(name)

    def list_modules(self, entry_type: str = "all") -> list[str]:
        """列出所有模块

        Args:
            entry_type: 条目类型 ("api", "event", "all")

        Returns:
            模块名称列表
        """
        modules: set[str] = set()

        if entry_type in ("api", "all"):
            modules.update(self.kb.api_by_module.keys())

        if entry_type in ("event", "all"):
            modules.update(self.kb.event_by_module.keys())

        return sorted(modules)

    def list_apis_by_module(self, module: str) -> list[APIEntry]:
        """获取指定模块的所有 API

        Args:
            module: 模块名称

        Returns:
            API 列表
        """
        return self.kb.get_apis_by_module(module)

    def list_events_by_module(self, module: str) -> list[EventEntry]:
        """获取指定模块的所有事件

        Args:
            module: 模块名称

        Returns:
            事件列表
        """
        return self.kb.get_events_by_module(module)

    def search_by_parameter(
        self,
        param_name: str,
        entry_type: str = "api",
    ) -> list[APIEntry | EventEntry]:
        """按参数名搜索

        查找包含指定参数名的 API 或事件。

        Args:
            param_name: 参数名
            entry_type: 条目类型 ("api", "event")

        Returns:
            匹配的条目列表
        """
        results: list[APIEntry | EventEntry] = []

        if entry_type == "api":
            for api in self.kb.apis.values():
                for param in api.parameters:
                    if param.name == param_name:
                        results.append(api)
                        break
        elif entry_type == "event":
            for event in self.kb.events.values():
                for param in event.parameters:  # type: ignore[assignment]
                    if param.name == param_name:
                        results.append(event)
                        break

        return results

    def search_by_return_type(self, return_type: str) -> list[APIEntry]:
        """按返回类型搜索 API

        Args:
            return_type: 返回类型

        Returns:
            匹配的 API 列表
        """
        results: list[APIEntry] = []

        for api in self.kb.apis.values():
            if api.return_type and return_type.lower() in api.return_type.lower():
                results.append(api)

        return results

    def get_stats(self) -> dict:
        """获取知识库统计信息"""
        return self.kb.stats()

    def _match_keyword(
        self, entry: APIEntry | EventEntry | EnumEntry, keyword_lower: str
    ) -> bool:
        """检查条目是否匹配关键词

        匹配范围：
        - 名称
        - 描述
        - 模块（API/事件）
        - 参数名（API/事件）
        """
        # 名称匹配
        if keyword_lower in entry.name.lower():
            return True

        # 描述匹配
        if entry.description and keyword_lower in entry.description.lower():
            return True

        # 模块匹配
        if hasattr(entry, "module") and keyword_lower in entry.module.lower():
            return True

        # 参数名匹配
        if hasattr(entry, "parameters"):
            for param in entry.parameters:
                if keyword_lower in param.name.lower():
                    return True
                if keyword_lower in param.description.lower():
                    return True

        return False

    def _sort_by_relevance(
        self,
        entries: list[APIEntry | EventEntry | EnumEntry],
        query: str,
    ) -> list[APIEntry | EventEntry | EnumEntry]:
        """按相关度排序

        名称匹配优先于描述匹配。
        名称完全匹配最优先。
        """

        def get_score(entry: APIEntry | EventEntry | EnumEntry) -> int:
            query_lower = query.lower()
            name_lower = entry.name.lower()

            # 名称完全匹配
            if name_lower == query_lower:
                return 0
            # 名称开头匹配
            if name_lower.startswith(query_lower):
                return 1
            # 名称包含匹配
            if query_lower in name_lower:
                return 2
            # 描述包含匹配
            if entry.description and query_lower in entry.description.lower():
                return 3
            # 其他
            return 4

        return sorted(entries, key=get_score)

    def fuzzy_search(
        self,
        query: str,
        entry_type: str = "all",
        threshold: int = 2,
        limit: int = 10,
    ) -> list[tuple[APIEntry | EventEntry | EnumEntry, int]]:
        """模糊搜索

        使用编辑距离进行模糊匹配。

        Args:
            query: 搜索关键词
            entry_type: 条目类型
            threshold: 最大编辑距离阈值
            limit: 返回结果数量限制

        Returns:
            (条目, 编辑距离) 元组列表
        """
        results: list[tuple[APIEntry | EventEntry | EnumEntry, int]] = []

        entries: list[APIEntry | EventEntry | EnumEntry] = []
        if entry_type in ("api", "all"):
            entries.extend(self.kb.apis.values())
        if entry_type in ("event", "all"):
            entries.extend(self.kb.events.values())
        if entry_type in ("enum", "all"):
            entries.extend(self.kb.enums.values())

        query_lower = query.lower()

        for entry in entries:
            name_lower = entry.name.lower()
            distance = self._levenshtein_distance(query_lower, name_lower)

            if distance <= threshold:
                results.append((entry, distance))

        # 按编辑距离排序
        results.sort(key=lambda x: x[1])

        return results[:limit]

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算编辑距离"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row: list[int] = list(range(len(s2) + 1))

        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def suggest(self, query: str, limit: int = 5) -> list[str]:
        """搜索建议

        根据输入提供可能的条目名称建议。

        Args:
            query: 输入的前缀
            limit: 返回建议数量

        Returns:
            建议的条目名称列表
        """
        suggestions = []
        query_lower = query.lower()

        # 收集所有名称
        all_names: list[str] = []
        all_names.extend(self.kb.apis.keys())
        all_names.extend(self.kb.events.keys())
        all_names.extend(self.kb.enums.keys())

        # 前缀匹配
        for name in all_names:
            if name.lower().startswith(query_lower):
                suggestions.append(name)

        # 如果前缀匹配不足，尝试包含匹配
        if len(suggestions) < limit:
            for name in all_names:
                if name not in suggestions and query_lower in name.lower():
                    suggestions.append(name)

        return suggestions[:limit]


def create_retriever(kb_path: str | None = None) -> KnowledgeRetriever:
    """创建检索器的便捷函数

    Args:
        kb_path: 可选的知识库文件路径

    Returns:
        初始化好的检索器
    """
    retriever = KnowledgeRetriever()
    if kb_path and Path(kb_path).exists():
        retriever.load(kb_path)
    return retriever
