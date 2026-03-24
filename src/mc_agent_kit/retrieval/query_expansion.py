"""
同义词扩展模块

提供查询扩展、同义词匹配和模糊搜索功能。
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ExpansionStrategy(Enum):
    """扩展策略"""
    SYNONYM = "synonym"                 # 同义词扩展
    HYPONYM = "hyponym"                 # 下位词扩展
    HYPERNYM = "hypernym"               # 上位词扩展
    RELATED = "related"                 # 相关词扩展
    SPELLING = "spelling"               # 拼写纠错
    ABBREVIATION = "abbreviation"       # 缩写扩展
    CHINESE_ENGLISH = "chinese_english" # 中英文互译


@dataclass
class SynonymEntry:
    """同义词条目"""
    word: str
    synonyms: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)
    abbreviations: list[str] = field(default_factory=list)
    category: str = ""
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "word": self.word,
            "synonyms": self.synonyms,
            "related": self.related,
            "abbreviations": self.abbreviations,
            "category": self.category,
            "weight": self.weight,
        }


@dataclass
class ExpandedQuery:
    """扩展后的查询"""
    original: str
    expanded: str
    terms: list[str]
    synonyms_added: list[str]
    strategy: ExpansionStrategy
    expansion_count: int

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "original": self.original,
            "expanded": self.expanded,
            "terms": self.terms,
            "synonyms_added": self.synonyms_added,
            "strategy": self.strategy.value,
            "expansion_count": self.expansion_count,
        }


@dataclass
class FuzzyMatch:
    """模糊匹配结果"""
    query: str
    matched: str
    score: float
    match_type: str
    edit_distance: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "matched": self.matched,
            "score": self.score,
            "match_type": self.match_type,
            "edit_distance": self.edit_distance,
        }


class SynonymDictionary:
    """同义词词典

    提供同义词查询和扩展功能。
    """

    def __init__(self) -> None:
        """初始化词典"""
        self._entries: dict[str, SynonymEntry] = {}
        self._synonym_index: dict[str, list[str]] = defaultdict(list)
        self._category_index: dict[str, list[str]] = defaultdict(list)
        self._lock = threading.RLock()

        # 加载内置同义词
        self._load_builtin_synonyms()

    def _load_builtin_synonyms(self) -> None:
        """加载内置同义词（针对 ModSDK 和 Minecraft）"""
        builtin_synonyms = [
            # API 相关
            SynonymEntry(
                word="实体",
                synonyms=["Entity", "生物", "怪物", "生物实体"],
                category="modsdk",
            ),
            SynonymEntry(
                word="物品",
                synonyms=["Item", "道具", "器材"],
                category="modsdk",
            ),
            SynonymEntry(
                word="方块",
                synonyms=["Block", "方块实体"],
                category="modsdk",
            ),
            SynonymEntry(
                word="事件",
                synonyms=["Event", "监听器", "回调"],
                category="modsdk",
            ),
            SynonymEntry(
                word="API",
                synonyms=["接口", "函数", "方法", "调用"],
                category="modsdk",
            ),
            SynonymEntry(
                word="创建",
                synonyms=["生成", "实例化", "新建", "Create"],
                category="modsdk",
            ),
            SynonymEntry(
                word="删除",
                synonyms=["移除", "销毁", "Delete", "Destroy"],
                category="modsdk",
            ),
            SynonymEntry(
                word="获取",
                synonyms=["得到", "取得", "Get", "Fetch"],
                category="modsdk",
            ),
            SynonymEntry(
                word="设置",
                synonyms=["设定", "配置", "Set", "Configure"],
                category="modsdk",
            ),
            SynonymEntry(
                word="玩家",
                synonyms=["Player", "用户", "操作者"],
                category="modsdk",
            ),
            SynonymEntry(
                word="服务端",
                synonyms=["Server", "服务器端", "服务端脚本"],
                category="modsdk",
            ),
            SynonymEntry(
                word="客户端",
                synonyms=["Client", "客户端脚本"],
                category="modsdk",
            ),
            SynonymEntry(
                word="监听",
                synonyms=["Listen", "监听器", "订阅", "注册"],
                category="modsdk",
            ),
            SynonymEntry(
                word="触发",
                synonyms=["Trigger", "激发", "调用"],
                category="modsdk",
            ),
            # 通用编程
            SynonymEntry(
                word="函数",
                synonyms=["方法", "Function", "Method", "子程序"],
                category="programming",
            ),
            SynonymEntry(
                word="变量",
                synonyms=["Variable", "参数", "值"],
                category="programming",
            ),
            SynonymEntry(
                word="类",
                synonyms=["Class", "类型", "对象类型"],
                category="programming",
            ),
            SynonymEntry(
                word="错误",
                synonyms=["Error", "异常", "Exception", "Bug", "问题"],
                category="programming",
            ),
        ]

        for entry in builtin_synonyms:
            self.add_entry(entry)

    def add_entry(self, entry: SynonymEntry) -> None:
        """添加同义词条目"""
        with self._lock:
            word_lower = entry.word.lower()
            self._entries[word_lower] = entry

            # 建立同义词索引
            for synonym in entry.synonyms:
                self._synonym_index[synonym.lower()].append(word_lower)

            # 建立分类索引
            if entry.category:
                self._category_index[entry.category].append(word_lower)

    def get_synonyms(self, word: str, category: str | None = None) -> list[str]:
        """获取同义词"""
        word_lower = word.lower()

        with self._lock:
            entry = self._entries.get(word_lower)
            if entry:
                if category and entry.category != category:
                    return entry.synonyms[:3]  # 只返回部分
                return entry.synonyms

            # 反向查找
            synonyms = self._synonym_index.get(word_lower, [])
            result = []
            for syn in synonyms:
                entry = self._entries.get(syn)
                if entry:
                    result.append(entry.word)
            return result

    def get_related(self, word: str) -> list[str]:
        """获取相关词"""
        word_lower = word.lower()

        with self._lock:
            entry = self._entries.get(word_lower)
            if entry:
                return entry.related
            return []

    def get_abbreviations(self, word: str) -> list[str]:
        """获取缩写"""
        word_lower = word.lower()

        with self._lock:
            entry = self._entries.get(word_lower)
            if entry:
                return entry.abbreviations
            return []

    def search_by_category(self, category: str) -> list[SynonymEntry]:
        """按分类搜索"""
        with self._lock:
            words = self._category_index.get(category, [])
            return [self._entries[w] for w in words if w in self._entries]

    def get_all_categories(self) -> list[str]:
        """获取所有分类"""
        return list(self._category_index.keys())

    def export_to_file(self, path: str) -> None:
        """导出到文件"""
        with self._lock:
            data = {
                word: entry.to_dict()
                for word, entry in self._entries.items()
            }

            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def import_from_file(self, path: str) -> int:
        """从文件导入"""
        if not Path(path).exists():
            return 0

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        with self._lock:
            for word, entry_data in data.items():
                entry = SynonymEntry(
                    word=entry_data["word"],
                    synonyms=entry_data.get("synonyms", []),
                    related=entry_data.get("related", []),
                    abbreviations=entry_data.get("abbreviations", []),
                    category=entry_data.get("category", ""),
                    weight=entry_data.get("weight", 1.0),
                )
                self.add_entry(entry)
                count += 1

        return count


class QueryExpander:
    """查询扩展器

    扩展用户查询以提高检索召回率。
    """

    def __init__(
        self,
        dictionary: SynonymDictionary | None = None,
    ) -> None:
        """初始化扩展器"""
        self._dictionary = dictionary or SynonymDictionary()

    def expand(
        self,
        query: str,
        strategy: ExpansionStrategy = ExpansionStrategy.SYNONYM,
        max_expansions: int = 5,
    ) -> ExpandedQuery:
        """扩展查询"""
        terms = self._tokenize(query)
        expanded_terms = []
        synonyms_added = []

        for term in terms:
            if strategy == ExpansionStrategy.SYNONYM:
                synonyms = self._dictionary.get_synonyms(term)
                if synonyms and len(synonyms_added) < max_expansions:
                    expanded_terms.extend(synonyms[:2])
                    synonyms_added.extend(synonyms[:2])

            elif strategy == ExpansionStrategy.RELATED:
                related = self._dictionary.get_related(term)
                if related and len(synonyms_added) < max_expansions:
                    expanded_terms.extend(related[:2])
                    synonyms_added.extend(related[:2])

            elif strategy == ExpansionStrategy.ABBREVIATION:
                abbreviations = self._dictionary.get_abbreviations(term)
                if abbreviations and len(synonyms_added) < max_expansions:
                    expanded_terms.extend(abbreviations)
                    synonyms_added.extend(abbreviations)

            # 始终保留原词
            if term not in expanded_terms:
                expanded_terms.append(term)

        expanded_query = " ".join(expanded_terms)

        return ExpandedQuery(
            original=query,
            expanded=expanded_query,
            terms=expanded_terms,
            synonyms_added=synonyms_added,
            strategy=strategy,
            expansion_count=len(synonyms_added),
        )

    def _tokenize(self, text: str) -> list[str]:
        """分词"""
        # 简单的分词：按空格和标点分割
        import re
        # 保留中英文
        tokens = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', text)
        return tokens


class FuzzyMatcher:
    """模糊匹配器

    提供拼写纠错和模糊搜索功能。
    """

    def __init__(
        self,
        candidates: list[str] | None = None,
        threshold: float = 0.6,
    ) -> None:
        """初始化模糊匹配器"""
        self._candidates: set[str] = set(candidates or [])
        self._threshold = threshold
        self._lock = threading.RLock()

    def add_candidates(self, candidates: list[str]) -> None:
        """添加候选词"""
        with self._lock:
            self._candidates.update(candidates)

    def remove_candidates(self, candidates: list[str]) -> None:
        """移除候选词"""
        with self._lock:
            for c in candidates:
                self._candidates.discard(c)

    def match(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[FuzzyMatch]:
        """模糊匹配"""
        if not self._candidates:
            return []

        results: list[FuzzyMatch] = []

        for candidate in self._candidates:
            score = self._calculate_similarity(query, candidate)

            if score >= self._threshold:
                edit_distance = self._levenshtein_distance(query.lower(), candidate.lower())
                results.append(FuzzyMatch(
                    query=query,
                    matched=candidate,
                    score=score,
                    match_type=self._get_match_type(score),
                    edit_distance=edit_distance,
                ))

        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def correct_spelling(self, query: str) -> str:
        """拼写纠错"""
        matches = self.match(query, top_k=1)

        if matches and matches[0].score > 0.7:
            return matches[0].matched

        return query

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """计算相似度"""
        s1_lower = s1.lower()
        s2_lower = s2.lower()

        # 完全匹配
        if s1_lower == s2_lower:
            return 1.0

        # 包含匹配
        if s1_lower in s2_lower or s2_lower in s1_lower:
            return 0.8

        # 编辑距离相似度
        distance = self._levenshtein_distance(s1_lower, s2_lower)
        max_len = max(len(s1_lower), len(s2_lower))

        if max_len == 0:
            return 1.0

        similarity = 1.0 - distance / max_len
        return similarity

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算编辑距离"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))

        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _get_match_type(self, score: float) -> str:
        """获取匹配类型"""
        if score >= 0.95:
            return "exact"
        elif score >= 0.85:
            return "high"
        elif score >= 0.7:
            return "medium"
        else:
            return "low"


class SearchResultFilter:
    """搜索结果过滤器

    过滤和精炼搜索结果。
    """

    def __init__(self) -> None:
        """初始化过滤器"""
        self._filters: dict[str, callable] = {}
        self._lock = threading.RLock()

    def add_filter(
        self,
        name: str,
        filter_func: callable,
    ) -> None:
        """添加过滤器"""
        with self._lock:
            self._filters[name] = filter_func

    def remove_filter(self, name: str) -> bool:
        """移除过滤器"""
        with self._lock:
            if name in self._filters:
                del self._filters[name]
                return True
            return False

    def filter(
        self,
        results: list[tuple[str, str, float, dict[str, Any]]],
        enabled_filters: list[str] | None = None,
    ) -> list[tuple[str, str, float, dict[str, Any]]]:
        """过滤结果"""
        with self._lock:
            filtered = results

            filter_names = enabled_filters or list(self._filters.keys())

            for filter_name in filter_names:
                filter_func = self._filters.get(filter_name)
                if filter_func:
                    filtered = [r for r in filtered if filter_func(r)]

            return filtered

    # 内置过滤器
    @staticmethod
    def filter_by_score(results: list[tuple[str, str, float, dict[str, Any]]], min_score: float) -> list[tuple[str, str, float, dict[str, Any]]]:
        """按分数过滤"""
        return [r for r in results if r[2] >= min_score]

    @staticmethod
    def filter_by_module(results: list[tuple[str, str, float, dict[str, Any]]], module: str) -> list[tuple[str, str, float, dict[str, Any]]]:
        """按模块过滤"""
        return [r for r in results if r[3].get("module") == module]

    @staticmethod
    def filter_by_scope(results: list[tuple[str, str, float, dict[str, Any]]], scope: str) -> list[tuple[str, str, float, dict[str, Any]]]:
        """按作用域过滤"""
        return [r for r in results if r[3].get("scope") == scope or r[3].get("scope") == "both"]

    @staticmethod
    def filter_by_type(results: list[tuple[str, str, float, dict[str, Any]]], entry_type: str) -> list[tuple[str, str, float, dict[str, Any]]]:
        """按类型过滤"""
        return [r for r in results if r[3].get("type") == entry_type]

    @staticmethod
    def deduplicate(results: list[tuple[str, str, float, dict[str, Any]]], threshold: float = 0.95) -> list[tuple[str, str, float, dict[str, Any]]]:
        """去重（基于内容相似度）"""
        if not results:
            return []

        unique: list[tuple[str, str, float, dict[str, Any]]] = []
        seen_hashes: set[str] = set()

        for result in results:
            id, content, score, metadata = result

            # 使用内容哈希去重
            content_hash = hash(content.lower().strip())

            if content_hash not in seen_hashes:
                unique.append(result)
                seen_hashes.add(content_hash)

        return unique


# 全局实例
_dictionary: SynonymDictionary | None = None
_expander: QueryExpander | None = None
_filter: SearchResultFilter | None = None


def get_synonym_dictionary() -> SynonymDictionary:
    """获取全局同义词词典"""
    global _dictionary
    if _dictionary is None:
        _dictionary = SynonymDictionary()
    return _dictionary


def get_query_expander() -> QueryExpander:
    """获取全局查询扩展器"""
    global _expander
    if _expander is None:
        _expander = QueryExpander()
    return _expander


def get_search_filter() -> SearchResultFilter:
    """获取全局搜索结果过滤器"""
    global _filter
    if _filter is None:
        _filter = SearchResultFilter()
    return _filter


def expand_query(query: str, strategy: ExpansionStrategy = ExpansionStrategy.SYNONYM) -> ExpandedQuery:
    """便捷函数：扩展查询"""
    return get_query_expander().expand(query, strategy)


def fuzzy_match(query: str, candidates: list[str], top_k: int = 5) -> list[FuzzyMatch]:
    """便捷函数：模糊匹配"""
    matcher = FuzzyMatcher(candidates)
    return matcher.match(query, top_k)