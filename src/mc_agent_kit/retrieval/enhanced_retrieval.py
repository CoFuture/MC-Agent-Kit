"""
增强检索模块

整合混合检索、重排序、查询扩展和结果融合，提供优化的检索体验。
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .embedding_manager import EmbeddingManager, EmbeddingModelType, get_embedding_manager
from .enhanced_index import (
    ChunkConfig,
    DocumentChunk,
    HNSWConfig,
    HNSWIndex,
    IncrementalIndexer,
    SemanticChunker,
)
from .hybrid_search import HybridSearchEngine, HybridSearchResult
from .query_expansion import (
    ExpansionStrategy,
    FuzzyMatcher,
    QueryExpander,
    SearchResultFilter,
    SynonymDictionary,
    get_query_expander,
    get_search_filter,
)
from .reranker import (
    HybridReranker,
    RerankConfig,
    RerankEngine,
    RerankResult,
    RerankStrategy,
)

logger = logging.getLogger(__name__)


class FusionStrategy(Enum):
    """融合策略"""
    RRF = "rrf"                         # 倒数排名融合
    WEIGHTED = "weighted"               # 加权融合
    RECIPROCAL = "reciprocal"           # 倒数融合
    COMBO = "combo"                     # 组合融合


@dataclass
class FusionConfig:
    """融合配置"""
    strategy: FusionStrategy = FusionStrategy.RRF
    rrf_k: int = 60                     # RRF 参数 k
    weights: dict[str, float] = field(default_factory=lambda: {
        "keyword": 0.3,
        "semantic": 0.7,
    })
    normalize_scores: bool = True


@dataclass
class EnhancedSearchResult:
    """增强搜索结果"""
    id: str
    content: str
    score: float
    keyword_score: float
    semantic_score: float
    rerank_score: float
    rank: int
    metadata: dict[str, Any] = field(default_factory=dict)
    chunk: DocumentChunk | None = None
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "score": self.score,
            "keyword_score": self.keyword_score,
            "semantic_score": self.semantic_score,
            "rerank_score": self.rerank_score,
            "rank": self.rank,
            "metadata": self.metadata,
            "explanation": self.explanation,
        }


@dataclass
class SearchReport:
    """搜索报告"""
    query: str
    expanded_query: str | None
    total_candidates: int
    final_results: int
    keyword_results: int
    semantic_results: int
    rerank_applied: bool
    fusion_strategy: str
    execution_time: float
    cache_hits: int
    cache_misses: int

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "expanded_query": self.expanded_query,
            "total_candidates": self.total_candidates,
            "final_results": self.final_results,
            "keyword_results": self.keyword_results,
            "semantic_results": self.semantic_results,
            "rerank_applied": self.rerank_applied,
            "fusion_strategy": self.fusion_strategy,
            "execution_time": self.execution_time,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
        }


class ResultFusion:
    """结果融合器

    融合多路召回的结果。
    """

    def __init__(self, config: FusionConfig | None = None) -> None:
        """初始化融合器"""
        self.config = config or FusionConfig()

    def fuse(
        self,
        result_lists: list[list[tuple[str, str, float, dict[str, Any]]]],
    ) -> list[tuple[str, str, float, dict[str, Any]]]:
        """
        融合多路结果

        Args:
            result_lists: 多路搜索结果列表

        Returns:
            融合后的结果
        """
        if not result_lists:
            return []

        if self.config.strategy == FusionStrategy.RRF:
            return self._rrf_fuse(result_lists)
        elif self.config.strategy == FusionStrategy.WEIGHTED:
            return self._weighted_fuse(result_lists)
        else:
            return self._combo_fuse(result_lists)

    def _rrf_fuse(
        self,
        result_lists: list[list[tuple[str, str, float, dict[str, Any]]]],
    ) -> list[tuple[str, str, float, dict[str, Any]]]:
        """倒数排名融合 (Reciprocal Rank Fusion)"""
        scores: dict[str, float] = defaultdict(float)
        contents: dict[str, str] = {}
        metadata: dict[str, dict[str, Any]] = {}

        k = self.config.rrf_k

        for result_list in result_lists:
            for rank, (id, content, score, meta) in enumerate(result_list, 1):
                scores[id] += 1.0 / (k + rank)
                contents[id] = content
                metadata[id] = meta

        # 排序
        fused = [
            (id, contents[id], score, metadata[id])
            for id, score in scores.items()
        ]
        fused.sort(key=lambda x: x[2], reverse=True)

        return fused

    def _weighted_fuse(
        self,
        result_lists: list[list[tuple[str, str, float, dict[str, Any]]]],
    ) -> list[tuple[str, str, float, dict[str, Any]]]:
        """加权融合"""
        scores: dict[str, float] = defaultdict(float)
        contents: dict[str, str] = {}
        metadata: dict[str, dict[str, Any]] = {}

        weights = list(self.config.weights.values())[:len(result_lists)]

        for i, result_list in enumerate(result_lists):
            weight = weights[i] if i < len(weights) else 1.0 / len(result_lists)

            # 归一化分数
            if result_list:
                max_score = max(r[2] for r in result_list)
                min_score = min(r[2] for r in result_list)
                score_range = max_score - min_score if max_score != min_score else 1.0

                for id, content, score, meta in result_list:
                    normalized = (score - min_score) / score_range
                    scores[id] += normalized * weight
                    contents[id] = content
                    metadata[id] = meta

        fused = [
            (id, contents[id], score, metadata[id])
            for id, score in scores.items()
        ]
        fused.sort(key=lambda x: x[2], reverse=True)

        return fused

    def _combo_fuse(
        self,
        result_lists: list[list[tuple[str, str, float, dict[str, Any]]]],
    ) -> list[tuple[str, str, float, dict[str, Any]]]:
        """组合融合"""
        # 先 RRF，再加权
        rrf_results = self._rrf_fuse(result_lists)

        if len(result_lists) >= 2:
            # 对前 N 个结果应用加权
            top_n = min(20, len(rrf_results))
            for i in range(top_n):
                id, content, score, meta = rrf_results[i]
                # 提升高置信度结果
                if score > 0.1:
                    rrf_results[i] = (id, content, score * 1.2, meta)

        return rrf_results


class EnhancedRetriever:
    """增强检索器

    整合查询扩展、混合检索、重排序和结果融合。

    使用示例:
        retriever = EnhancedRetriever()
        retriever.index_documents(documents)
        results = retriever.search("查询", top_k=10)
    """

    def __init__(
        self,
        chunk_config: ChunkConfig | None = None,
        hnsw_config: HNSWConfig | None = None,
        embedding_config: dict[str, Any] | None = None,
        rerank_config: RerankConfig | None = None,
        fusion_config: FusionConfig | None = None,
    ) -> None:
        """初始化增强检索器"""
        # 初始化组件
        self._chunker = SemanticChunker(chunk_config)
        self._indexer = IncrementalIndexer(
            chunker=self._chunker,
            index=HNSWIndex(hnsw_config),
        )
        self._embedding_manager = EmbeddingManager(
            embedding_config or {}
        )
        self._hybrid_engine = HybridSearchEngine()
        self._rerank_engine = RerankEngine(rerank_config)
        self._fusion = ResultFusion(fusion_config)
        self._query_expander = get_query_expander()
        self._search_filter = get_search_filter()

        # 注册内置过滤器
        self._register_builtin_filters()

        self._lock = threading.RLock()

    def _register_builtin_filters(self) -> None:
        """注册内置过滤器"""
        self._search_filter.add_filter(
            "min_score",
            lambda r: r[2] >= 0.1,
        )

    def index_documents(
        self,
        documents: dict[str, str],
        metadata: dict[str, dict[str, Any]] | None = None,
    ) -> int:
        """
        索引文档

        Args:
            documents: {doc_id: content, ...}
            metadata: {doc_id: metadata, ...}

        Returns:
            索引的文档数量
        """
        count = 0

        for doc_id, content in documents.items():
            doc_metadata = metadata.get(doc_id, {}) if metadata else {}

            self._indexer.add_document(
                doc_id=doc_id,
                content=content,
                metadata=doc_metadata,
            )
            count += 1

        logger.info(f"索引完成：{count} 个文档")
        return count

    def search(
        self,
        query: str,
        top_k: int = 10,
        use_expansion: bool = True,
        use_rerank: bool = True,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[EnhancedSearchResult], SearchReport]:
        """
        执行增强搜索

        Args:
            query: 查询文本
            top_k: 返回结果数
            use_expansion: 是否使用查询扩展
            use_rerank: 是否使用重排序
            filters: 过滤条件

        Returns:
            (搜索结果, 搜索报告)
        """
        start_time = time.time()

        # 查询扩展
        expanded_query = None
        if use_expansion:
            expanded = self._query_expander.expand(query)
            expanded_query = expanded.expanded
            logger.debug(f"查询扩展：{query} -> {expanded_query}")

        # 生成嵌入向量
        query_embedding = self._embedding_manager.embed(query).embedding

        # 多路召回
        keyword_results = self._keyword_search(query, top_k * 2)
        semantic_results = self._semantic_search(query_embedding, top_k * 2)

        # 过滤
        if filters:
            keyword_results = self._apply_filters(keyword_results, filters)
            semantic_results = self._apply_filters(semantic_results, filters)

        # 融合
        fused_results = self._fusion.fuse([keyword_results, semantic_results])

        # 重排序
        reranked_results = fused_results
        if use_rerank and len(fused_results) > 0:
            reranked, _report = self._rerank_engine.rerank(
                expanded_query or query,
                fused_results,
                top_k=top_k,
            )
            reranked_results = [
                (r.id, r.content, r.rerank_score, r.metadata)
                for r in reranked
            ]

        # 转换为增强结果
        enhanced_results = self._convert_to_enhanced(
            reranked_results[:top_k],
            keyword_results,
            semantic_results,
        )

        # 生成报告
        report = SearchReport(
            query=query,
            expanded_query=expanded_query,
            total_candidates=len(fused_results),
            final_results=len(enhanced_results),
            keyword_results=len(keyword_results),
            semantic_results=len(semantic_results),
            rerank_applied=use_rerank,
            fusion_strategy=self._fusion.config.strategy.value,
            execution_time=time.time() - start_time,
            cache_hits=self._embedding_manager.get_cache_stats().get("hits", 0) if self._embedding_manager.get_cache_stats() else 0,
            cache_misses=self._embedding_manager.get_cache_stats().get("misses", 0) if self._embedding_manager.get_cache_stats() else 0,
        )

        return enhanced_results, report

    def _keyword_search(
        self,
        query: str,
        top_k: int,
    ) -> list[tuple[str, str, float, dict[str, Any]]]:
        """关键词搜索"""
        # 使用混合搜索引擎的关键词搜索
        results = self._hybrid_engine.keyword_only_search(query, top_k)

        return [
            (r.id, r.content, r.score, r.metadata)
            for r in results
        ]

    def _semantic_search(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[tuple[str, str, float, dict[str, Any]]]:
        """语义搜索"""
        # 使用增量索引器搜索
        chunk_results = self._indexer.search(query_embedding, top_k)

        return [
            (chunk.id, chunk.content, 1.0 - distance, {"chunk": chunk})
            for chunk, distance in chunk_results
        ]

    def _apply_filters(
        self,
        results: list[tuple[str, str, float, dict[str, Any]]],
        filters: dict[str, Any],
    ) -> list[tuple[str, str, float, dict[str, Any]]]:
        """应用过滤器"""
        filtered = results

        if "min_score" in filters:
            filtered = SearchResultFilter.filter_by_score(filtered, filters["min_score"])

        if "module" in filters:
            filtered = SearchResultFilter.filter_by_module(filtered, filters["module"])

        if "scope" in filters:
            filtered = SearchResultFilter.filter_by_scope(filtered, filters["scope"])

        if "type" in filters:
            filtered = SearchResultFilter.filter_by_type(filtered, filters["type"])

        # 去重
        filtered = SearchResultFilter.deduplicate(filtered)

        return filtered

    def _convert_to_enhanced(
        self,
        results: list[tuple[str, str, float, dict[str, Any]]],
        keyword_results: list[tuple[str, str, float, dict[str, Any]]],
        semantic_results: list[tuple[str, str, float, dict[str, Any]]],
    ) -> list[EnhancedSearchResult]:
        """转换为增强搜索结果"""
        keyword_scores = {r[0]: r[2] for r in keyword_results}
        semantic_scores = {r[0]: r[2] for r in semantic_results}

        enhanced: list[EnhancedSearchResult] = []

        for i, (id, content, score, metadata) in enumerate(results, 1):
            chunk = metadata.get("chunk")

            # 生成解释
            explanation = self._generate_explanation(
                score,
                keyword_scores.get(id, 0),
                semantic_scores.get(id, 0),
            )

            enhanced.append(EnhancedSearchResult(
                id=id,
                content=content,
                score=score,
                keyword_score=keyword_scores.get(id, 0),
                semantic_score=semantic_scores.get(id, 0),
                rerank_score=score,
                rank=i,
                metadata=metadata,
                chunk=chunk,
                explanation=explanation,
            ))

        return enhanced

    def _generate_explanation(
        self,
        total_score: float,
        keyword_score: float,
        semantic_score: float,
    ) -> str:
        """生成结果解释"""
        explanations = []

        if keyword_score > 0.7:
            explanations.append("关键词高度匹配")
        elif keyword_score > 0.4:
            explanations.append("关键词部分匹配")

        if semantic_score > 0.7:
            explanations.append("语义高度相关")
        elif semantic_score > 0.4:
            explanations.append("语义部分相关")

        if total_score > 0.8:
            explanations.append("综合评分优秀")
        elif total_score > 0.5:
            explanations.append("综合评分良好")

        return "，".join(explanations) if explanations else "匹配结果"

    def get_stats(self) -> dict[str, Any]:
        """获取检索器统计"""
        index_stats = self._indexer.get_stats()

        return {
            "index_stats": index_stats.to_dict(),
            "embedding_stats": self._embedding_manager.get_cache_stats(),
        }

    def clear(self) -> None:
        """清空索引"""
        self._indexer = IncrementalIndexer(
            chunker=self._chunker,
            index=HNSWIndex(),
        )


# 全局实例
_retriever: EnhancedRetriever | None = None


def get_enhanced_retriever() -> EnhancedRetriever:
    """获取全局增强检索器"""
    global _retriever
    if _retriever is None:
        _retriever = EnhancedRetriever()
    return _retriever


def enhanced_search(
    query: str,
    top_k: int = 10,
    use_expansion: bool = True,
    use_rerank: bool = True,
) -> list[EnhancedSearchResult]:
    """便捷函数：执行增强搜索"""
    retriever = get_enhanced_retriever()
    results, _report = retriever.search(query, top_k, use_expansion, use_rerank)
    return results