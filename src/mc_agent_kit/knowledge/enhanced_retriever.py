"""
增强知识检索模块

提供统一的知识检索接口，整合 API、事件、示例代码等。
迭代 #71: 知识库增强与检索优化
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .unified_index import (
    DifficultyLevel,
    EntryScope,
    EntryType,
    ExampleCategory,
    UnifiedEntry,
)
from .example_library import ExampleCode, ExampleLibrary, get_example_library

logger = logging.getLogger(__name__)


@dataclass
class SearchFilter:
    """搜索过滤器"""
    entry_type: EntryType | None = None
    scope: EntryScope | None = None
    module: str | None = None
    category: ExampleCategory | None = None
    difficulty: DifficultyLevel | None = None
    tags: list[str] = field(default_factory=list)
    min_popularity: int = 0

    def matches(self, entry: UnifiedEntry) -> bool:
        """检查条目是否匹配过滤器"""
        if self.entry_type and entry.type != self.entry_type:
            return False
        if self.scope and entry.scope != self.scope:
            return False
        if self.module and entry.module != self.module:
            return False
        if self.category and entry.example_category != self.category:
            return False
        if self.difficulty and entry.difficulty != self.difficulty:
            return False
        if self.tags and not any(tag in entry.tags for tag in self.tags):
            return False
        if self.min_popularity > 0 and entry.popularity < self.min_popularity:
            return False
        return True


@dataclass
class SearchResult:
    """搜索结果"""
    entry: UnifiedEntry
    score: float
    matched_keywords: list[str] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry": self.entry.to_dict(),
            "score": self.score,
            "matched_keywords": self.matched_keywords,
            "highlights": self.highlights,
        }


@dataclass
class SearchReport:
    """搜索报告"""
    query: str
    total_results: int
    results: list[SearchResult]
    filters: SearchFilter | None = None
    duration_ms: float = 0.0
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "total_results": self.total_results,
            "results": [r.to_dict() for r in self.results],
            "filters": {
                "entry_type": self.filters.entry_type.value if self.filters and self.filters.entry_type else None,
                "scope": self.filters.scope.value if self.filters and self.filters.scope else None,
                "module": self.filters.module if self.filters else None,
            } if self.filters else None,
            "duration_ms": self.duration_ms,
            "suggestions": self.suggestions,
        }


class EnhancedKnowledgeRetriever:
    """
    增强知识检索器
    
    提供统一的知识检索接口，支持 API、事件、示例代码等多种类型的检索。
    """

    def __init__(
        self,
        index_path: str | None = None,
        example_library_path: str | None = None,
    ):
        """
        初始化检索器
        
        Args:
            index_path: 索引文件路径
            example_library_path: 示例库路径
        """
        self.index_path = Path(index_path) if index_path else None
        self._entries: dict[str, UnifiedEntry] = {}
        self._by_type: dict[EntryType, list[str]] = {}
        self._by_name: dict[str, str] = {}
        self._by_module: dict[str, list[str]] = {}
        self._example_library: ExampleLibrary | None = None
        self._loaded = False

        # 初始化类型索引
        for entry_type in EntryType:
            self._by_type[entry_type] = []

        # 设置示例库路径
        if example_library_path:
            self._example_library = ExampleLibrary(example_library_path)

    def load(self) -> None:
        """加载索引"""
        if self._loaded:
            return

        start_time = datetime.now()

        # 加载索引文件
        if self.index_path and self.index_path.exists():
            self._load_from_file(self.index_path)

        # 加载示例库
        if self._example_library:
            self._example_library.load()
            # 将示例转换为统一条目
            for example in self._example_library.list_examples(limit=1000):
                entry = example.to_unified_entry()
                self._add_entry(entry)

        self._loaded = True
        duration = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"索引加载完成: {len(self._entries)} 条目, 耗时 {duration:.2f}ms")

    def search(
        self,
        query: str,
        filters: SearchFilter | None = None,
        limit: int = 10,
    ) -> SearchReport:
        """
        搜索知识库
        
        Args:
            query: 搜索查询
            filters: 搜索过滤器
            limit: 返回结果数量限制
        
        Returns:
            搜索报告
        """
        if not self._loaded:
            self.load()

        start_time = datetime.now()
        results: list[SearchResult] = []

        # 预处理查询
        query_lower = query.lower().strip()
        keywords = query_lower.split()

        # 搜索匹配
        for entry in self._entries.values():
            # 应用过滤器
            if filters and not filters.matches(entry):
                continue

            # 计算匹配分数
            score, matched_keywords, highlights = self._compute_score(entry, query_lower, keywords)

            if score > 0:
                results.append(SearchResult(
                    entry=entry,
                    score=score,
                    matched_keywords=matched_keywords,
                    highlights=highlights,
                ))

        # 排序
        results.sort(key=lambda r: r.score, reverse=True)

        # 限制数量
        results = results[:limit]

        # 生成建议
        suggestions = self._generate_suggestions(query, results)

        duration = (datetime.now() - start_time).total_seconds() * 1000

        return SearchReport(
            query=query,
            total_results=len(results),
            results=results,
            filters=filters,
            duration_ms=duration,
            suggestions=suggestions,
        )

    def get_api(self, name: str) -> UnifiedEntry | None:
        """获取 API 信息"""
        if not self._loaded:
            self.load()

        # 直接查找
        if name in self._by_name:
            return self._entries.get(self._by_name[name])

        # 模糊匹配
        for entry_id, entry in self._entries.items():
            if entry.type == EntryType.API and entry.name.lower() == name.lower():
                return entry

        return None

    def get_event(self, name: str) -> UnifiedEntry | None:
        """获取事件信息"""
        if not self._loaded:
            self.load()

        if name in self._by_name:
            return self._entries.get(self._by_name[name])

        for entry_id, entry in self._entries.items():
            if entry.type == EntryType.EVENT and entry.name.lower() == name.lower():
                return entry

        return None

    def get_example(self, name: str) -> ExampleCode | None:
        """获取示例代码"""
        if not self._loaded:
            self.load()

        if self._example_library:
            return self._example_library.get_example(name)
        return None

    def list_apis(self, module: str | None = None, limit: int = 50) -> list[UnifiedEntry]:
        """列出 API"""
        if not self._loaded:
            self.load()

        apis = [self._entries[eid] for eid in self._by_type.get(EntryType.API, [])]

        if module:
            apis = [api for api in apis if api.module == module]

        return apis[:limit]

    def list_events(self, module: str | None = None, limit: int = 50) -> list[UnifiedEntry]:
        """列出事件"""
        if not self._loaded:
            self.load()

        events = [self._entries[eid] for eid in self._by_type.get(EntryType.EVENT, [])]

        if module:
            events = [e for e in events if e.module == module]

        return events[:limit]

    def list_examples(
        self,
        category: ExampleCategory | None = None,
        difficulty: DifficultyLevel | None = None,
        limit: int = 20,
    ) -> list[ExampleCode]:
        """列出示例"""
        if not self._loaded:
            self.load()

        if self._example_library:
            return self._example_library.list_examples(
                category=category,
                difficulty=difficulty,
                limit=limit,
            )
        return []

    def get_examples_by_api(self, api_name: str) -> list[ExampleCode]:
        """获取使用指定 API 的示例"""
        if not self._loaded:
            self.load()

        if self._example_library:
            return self._example_library.get_examples_by_api(api_name)
        return []

    def get_examples_by_event(self, event_name: str) -> list[ExampleCode]:
        """获取使用指定事件的示例"""
        if not self._loaded:
            self.load()

        if self._example_library:
            return self._example_library.get_examples_by_event(event_name)
        return []

    def get_related(self, entry_name: str, limit: int = 5) -> list[UnifiedEntry]:
        """获取相关条目"""
        if not self._loaded:
            self.load()

        entry = self.get_api(entry_name) or self.get_event(entry_name)
        if not entry:
            return []

        related: list[UnifiedEntry] = []

        # 通过关联 API 获取
        for related_api in entry.related_apis:
            related_entry = self.get_api(related_api.name)
            if related_entry and related_entry not in related:
                related.append(related_entry)

        # 通过关联事件获取
        for event_name in entry.related_events:
            related_entry = self.get_event(event_name)
            if related_entry and related_entry not in related:
                related.append(related_entry)

        return related[:limit]

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        if not self._loaded:
            self.load()

        by_type = {
            entry_type.value: len(entries)
            for entry_type, entries in self._by_type.items()
            if entries
        }

        by_module = {
            module: len(entries)
            for module, entries in self._by_module.items()
        }

        example_stats = {}
        if self._example_library:
            example_stats = self._example_library.get_stats()

        return {
            "total_entries": len(self._entries),
            "by_type": by_type,
            "by_module": by_module,
            "example_library": example_stats,
        }

    def add_entry(self, entry: UnifiedEntry) -> None:
        """添加条目"""
        self._add_entry(entry)

    def _add_entry(self, entry: UnifiedEntry) -> None:
        """内部添加条目"""
        self._entries[entry.id] = entry

        # 更新类型索引
        if entry.type not in self._by_type:
            self._by_type[entry.type] = []
        if entry.id not in self._by_type[entry.type]:
            self._by_type[entry.type].append(entry.id)

        # 更新名称索引
        self._by_name[entry.name.lower()] = entry.id
        for alias in entry.aliases:
            self._by_name[alias.lower()] = entry.id

        # 更新模块索引
        if entry.module:
            if entry.module not in self._by_module:
                self._by_module[entry.module] = []
            if entry.id not in self._by_module[entry.module]:
                self._by_module[entry.module].append(entry.id)

    def _compute_score(
        self,
        entry: UnifiedEntry,
        query_lower: str,
        keywords: list[str],
    ) -> tuple[float, list[str], list[str]]:
        """计算匹配分数"""
        score = 0.0
        matched_keywords: list[str] = []
        highlights: list[str] = []

        # 名称精确匹配
        if entry.name.lower() == query_lower:
            score += 100.0
            highlights.append(f"名称匹配: {entry.name}")

        # 名称包含
        elif query_lower in entry.name.lower():
            score += 50.0
            highlights.append(f"名称包含: {entry.name}")

        # 别名匹配
        for alias in entry.aliases:
            if query_lower == alias.lower():
                score += 40.0
                matched_keywords.append(alias)
                break

        # 关键词匹配
        for keyword in keywords:
            if keyword in entry.name.lower():
                score += 10.0
                matched_keywords.append(keyword)
            elif keyword in entry.description.lower():
                score += 5.0
                matched_keywords.append(keyword)
            elif keyword in entry.keywords:
                score += 8.0
                matched_keywords.append(keyword)
            elif any(keyword in tag.lower() for tag in entry.tags):
                score += 3.0
                matched_keywords.append(keyword)

        # 模块匹配
        if entry.module and entry.module.lower() in query_lower:
            score += 15.0

        # 热度加成
        score += min(entry.popularity * 0.1, 10.0)

        return score, matched_keywords, highlights

    def _generate_suggestions(self, query: str, results: list[SearchResult]) -> list[str]:
        """生成搜索建议"""
        suggestions: list[str] = []

        if not results:
            suggestions.append("尝试使用更通用的关键词")
            suggestions.append("检查拼写是否正确")

            # 推荐相关 API/事件
            if "create" in query.lower() or "创建" in query:
                suggestions.append("搜索建议: 实体创建可搜索 'CreateEngineEntity'")
            if "event" in query.lower() or "事件" in query:
                suggestions.append("搜索建议: 使用 --type event 过滤事件")
        else:
            # 基于结果生成建议
            top_entry = results[0].entry
            if top_entry.related_apis:
                suggestions.append(f"相关 API: {', '.join([a.name for a in top_entry.related_apis[:3]])}")
            if top_entry.related_events:
                suggestions.append(f"相关事件: {', '.join(top_entry.related_events[:3])}")

        return suggestions

    def _load_from_file(self, path: Path) -> None:
        """从文件加载索引"""
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            entries_data = data.get("entries", [])
            for entry_data in entries_data:
                entry = UnifiedEntry.from_dict(entry_data)
                self._add_entry(entry)

            logger.info(f"从 {path} 加载了 {len(entries_data)} 个条目")

        except Exception as e:
            logger.warning(f"加载索引文件失败: {e}")

    def save_to_file(self, path: Path | None = None) -> None:
        """保存索引到文件"""
        save_path = path or self.index_path
        if not save_path:
            return

        save_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "1.0.0",
            "entries": [entry.to_dict() for entry in self._entries.values()],
            "stats": self.get_stats(),
        }

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"索引已保存到 {save_path}")


# 全局检索器实例
_retriever: EnhancedKnowledgeRetriever | None = None


def get_retriever(
    index_path: str | None = None,
    example_library_path: str | None = None,
) -> EnhancedKnowledgeRetriever:
    """获取全局检索器实例"""
    global _retriever
    if _retriever is None:
        _retriever = EnhancedKnowledgeRetriever(index_path, example_library_path)
    return _retriever


def search_knowledge(
    query: str,
    entry_type: str | None = None,
    module: str | None = None,
    limit: int = 10,
) -> SearchReport:
    """搜索知识库（便捷函数）"""
    retriever = get_retriever()

    filters = None
    if entry_type or module:
        filters = SearchFilter(
            entry_type=EntryType(entry_type) if entry_type else None,
            module=module,
        )

    return retriever.search(query, filters=filters, limit=limit)


def get_api_info(name: str) -> UnifiedEntry | None:
    """获取 API 信息（便捷函数）"""
    return get_retriever().get_api(name)


def get_event_info(name: str) -> UnifiedEntry | None:
    """获取事件信息（便捷函数）"""
    return get_retriever().get_event(name)