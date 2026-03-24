"""
重排序模块

提供多种重排序算法，提升检索结果的准确性和相关性。
"""

from __future__ import annotations

import logging
import math
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RerankStrategy(Enum):
    """重排序策略"""
    SCORE_BASED = "score_based"         # 基于分数的重排序
    DIVERSITY = "diversity"             # 多样性重排序
    RECENCY = "recency"                 # 时效性重排序
    RELEVANCE = "relevance"             # 相关性重排序
    HYBRID = "hybrid"                   # 混合重排序
    CROSS_ENCODER = "cross_encoder"     # 交叉编码器重排序
    LLM_RERANK = "llm_rerank"           # LLM 重排序


@dataclass
class RerankConfig:
    """重排序配置"""
    strategy: RerankStrategy = RerankStrategy.HYBRID
    top_k: int = 10                     # 重排序后保留的结果数
    diversity_threshold: float = 0.8    # 多样性阈值
    recency_weight: float = 0.2         # 时效性权重
    relevance_weight: float = 0.5       # 相关性权重
    diversity_weight: float = 0.3       # 多样性权重
    min_score_threshold: float = 0.1    # 最低分数阈值


@dataclass
class RerankResult:
    """重排序结果"""
    id: str
    content: str
    original_score: float
    rerank_score: float
    rank_change: int                    # 排名变化（正数上升，负数下降）
    score_factors: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "original_score": self.original_score,
            "rerank_score": self.rerank_score,
            "rank_change": self.rank_change,
            "score_factors": self.score_factors,
            "metadata": self.metadata,
        }


@dataclass
class RerankReport:
    """重排序报告"""
    original_order: list[str]
    reranked_order: list[str]
    strategy: RerankStrategy
    execution_time: float
    avg_score_change: float
    score_improvement: int              # 分数提升的结果数
    score_degradation: int              # 分数下降的结果数

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "original_order": self.original_order,
            "reranked_order": self.reranked_order,
            "strategy": self.strategy.value,
            "execution_time": self.execution_time,
            "avg_score_change": self.avg_score_change,
            "score_improvement": self.score_improvement,
            "score_degradation": self.score_degradation,
        }


class Reranker:
    """重排序器基类"""

    def __init__(self, config: RerankConfig | None = None) -> None:
        """初始化重排序器"""
        self.config = config or RerankConfig()

    def rerank(
        self,
        query: str,
        results: list[tuple[str, str, float, dict[str, Any]]],
    ) -> list[RerankResult]:
        """
        重排序结果

        Args:
            query: 查询文本
            results: [(id, content, score, metadata), ...]

        Returns:
            重排序后的结果列表
        """
        raise NotImplementedError


class ScoreBasedReranker(Reranker):
    """基于分数的重排序器"""

    def rerank(
        self,
        query: str,
        results: list[tuple[str, str, float, dict[str, Any]]],
    ) -> list[RerankResult]:
        """基于原始分数重排序"""
        if not results:
            return []

        # 归一化分数
        max_score = max(r[2] for r in results)
        min_score = min(r[2] for r in results)
        score_range = max_score - min_score if max_score != min_score else 1.0

        reranked: list[RerankResult] = []
        for id, content, score, metadata in results:
            normalized_score = (score - min_score) / score_range
            reranked.append(RerankResult(
                id=id,
                content=content,
                original_score=score,
                rerank_score=normalized_score,
                rank_change=0,
                score_factors={"normalized": normalized_score},
                metadata=metadata,
            ))

        # 按重排序分数排序
        reranked.sort(key=lambda x: x.rerank_score, reverse=True)

        # 计算排名变化
        original_ranks = {r[0]: i for i, r in enumerate(results)}
        for i, result in enumerate(reranked):
            original_rank = original_ranks.get(result.id, i)
            result.rank_change = original_rank - i

        return reranked[:self.config.top_k]


class DiversityReranker(Reranker):
    """多样性重排序器

    确保结果多样性，避免过于相似的结果排在前面。
    """

    def __init__(
        self,
        config: RerankConfig | None = None,
        similarity_threshold: float = 0.85,
    ) -> None:
        """初始化多样性重排序器"""
        super().__init__(config)
        self._similarity_threshold = similarity_threshold

    def rerank(
        self,
        query: str,
        results: list[tuple[str, str, float, dict[str, Any]]],
    ) -> list[RerankResult]:
        """多样性重排序"""
        if not results:
            return []

        selected: list[RerankResult] = []
        remaining = list(results)

        while remaining and len(selected) < self.config.top_k:
            # 找到与已选结果最不相似的结果
            best_idx = 0
            best_score = -1

            for i, (id, content, score, metadata) in enumerate(remaining):
                # 检查与已选结果的相似度
                max_similarity = 0.0
                for selected_result in selected:
                    similarity = self._calculate_similarity(content, selected_result.content)
                    max_similarity = max(max_similarity, similarity)

                # 多样性得分 = 原始分数 * (1 - 最大相似度)
                diversity_score = score * (1 - max_similarity)

                if diversity_score > best_score:
                    best_score = diversity_score
                    best_idx = i

            id, content, score, metadata = remaining.pop(best_idx)

            selected.append(RerankResult(
                id=id,
                content=content,
                original_score=score,
                rerank_score=best_score,
                rank_change=0,
                score_factors={"diversity": best_score},
                metadata=metadata,
            ))

        # 计算排名变化
        original_ranks = {r[0]: i for i, r in enumerate(results)}
        for i, result in enumerate(selected):
            original_rank = original_ranks.get(result.id, i)
            result.rank_change = original_rank - i

        return selected

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（Jaccard 相似度）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0


class RecencyReranker(Reranker):
    """时效性重排序器

    优先显示最新的结果。
    """

    def rerank(
        self,
        query: str,
        results: list[tuple[str, str, float, dict[str, Any]]],
    ) -> list[RerankResult]:
        """时效性重排序"""
        if not results:
            return []

        current_time = time.time()
        reranked: list[RerankResult] = []

        for id, content, score, metadata in results:
            # 获取时间戳（从 metadata 或使用当前时间）
            timestamp = metadata.get("timestamp", metadata.get("created_at", current_time))

            # 计算时效性分数（越新越高）
            age_days = (current_time - timestamp) / 86400 if isinstance(timestamp, (int, float)) else 0
            recency_factor = math.exp(-age_days / 30)  # 30 天衰减

            # 综合分数
            rerank_score = score * (1 - self.config.recency_weight) + recency_factor * self.config.recency_weight

            reranked.append(RerankResult(
                id=id,
                content=content,
                original_score=score,
                rerank_score=rerank_score,
                rank_change=0,
                score_factors={
                    "original": score,
                    "recency": recency_factor,
                },
                metadata=metadata,
            ))

        # 按重排序分数排序
        reranked.sort(key=lambda x: x.rerank_score, reverse=True)

        # 计算排名变化
        original_ranks = {r[0]: i for i, r in enumerate(results)}
        for i, result in enumerate(reranked):
            original_rank = original_ranks.get(result.id, i)
            result.rank_change = original_rank - i

        return reranked[:self.config.top_k]


class RelevanceReranker(Reranker):
    """相关性重排序器

    基于查询相关性重新计算分数。
    """

    def rerank(
        self,
        query: str,
        results: list[tuple[str, str, float, dict[str, Any]]],
    ) -> list[RerankResult]:
        """相关性重排序"""
        if not results:
            return []

        query_terms = set(query.lower().split())
        reranked: list[RerankResult] = []

        for id, content, score, metadata in results:
            content_terms = set(content.lower().split())

            # 计算查询覆盖率
            coverage = len(query_terms & content_terms) / len(query_terms) if query_terms else 0

            # 计算 TF-IDF 风格的相关性
            tf = sum(1 for term in query_terms if term in content_terms) / len(query_terms) if query_terms else 0

            # 综合相关性分数
            relevance_score = coverage * 0.5 + tf * 0.5

            # 综合原始分数
            rerank_score = score * (1 - self.config.relevance_weight) + relevance_score * self.config.relevance_weight

            reranked.append(RerankResult(
                id=id,
                content=content,
                original_score=score,
                rerank_score=rerank_score,
                rank_change=0,
                score_factors={
                    "original": score,
                    "coverage": coverage,
                    "tf": tf,
                    "relevance": relevance_score,
                },
                metadata=metadata,
            ))

        # 按重排序分数排序
        reranked.sort(key=lambda x: x.rerank_score, reverse=True)

        # 计算排名变化
        original_ranks = {r[0]: i for i, r in enumerate(results)}
        for i, result in enumerate(reranked):
            original_rank = original_ranks.get(result.id, i)
            result.rank_change = original_rank - i

        return reranked[:self.config.top_k]


class HybridReranker(Reranker):
    """混合重排序器

    结合多种重排序策略。
    """

    def __init__(
        self,
        config: RerankConfig | None = None,
        strategies: list[RerankStrategy] | None = None,
        weights: dict[RerankStrategy, float] | None = None,
    ) -> None:
        """初始化混合重排序器"""
        super().__init__(config)
        self._strategies = strategies or [
            RerankStrategy.SCORE_BASED,
            RerankStrategy.DIVERSITY,
            RerankStrategy.RELEVANCE,
        ]
        self._weights = weights or {
            RerankStrategy.SCORE_BASED: 0.3,
            RerankStrategy.DIVERSITY: 0.3,
            RerankStrategy.RELEVANCE: 0.4,
        }

        # 初始化子重排序器
        self._rerankers: dict[RerankStrategy, Reranker] = {
            RerankStrategy.SCORE_BASED: ScoreBasedReranker(config),
            RerankStrategy.DIVERSITY: DiversityReranker(config),
            RerankStrategy.RECENCY: RecencyReranker(config),
            RerankStrategy.RELEVANCE: RelevanceReranker(config),
        }

    def rerank(
        self,
        query: str,
        results: list[tuple[str, str, float, dict[str, Any]]],
    ) -> list[RerankResult]:
        """混合重排序"""
        if not results:
            return []

        # 收集各策略的分数
        all_scores: dict[str, dict[RerankStrategy, float]] = defaultdict(dict)

        for strategy in self._strategies:
            reranker = self._rerankers.get(strategy)
            if not reranker:
                continue

            reranked = reranker.rerank(query, results)

            for result in reranked:
                all_scores[result.id][strategy] = result.rerank_score

        # 计算加权综合分数
        final_results: list[RerankResult] = []
        original_ranks = {r[0]: (i, r[2]) for i, r in enumerate(results)}

        for id, content, score, metadata in results:
            strategy_scores = all_scores.get(id, {})

            # 计算加权分数
            weighted_score = 0.0
            total_weight = 0.0
            score_factors: dict[str, float] = {}

            for strategy, s_score in strategy_scores.items():
                weight = self._weights.get(strategy, 0.0)
                weighted_score += s_score * weight
                total_weight += weight
                score_factors[strategy.value] = s_score

            if total_weight > 0:
                weighted_score /= total_weight

            original_rank, original_score = original_ranks.get(id, (0, score))

            final_results.append(RerankResult(
                id=id,
                content=content,
                original_score=original_score,
                rerank_score=weighted_score,
                rank_change=0,
                score_factors=score_factors,
                metadata=metadata,
            ))

        # 按综合分数排序
        final_results.sort(key=lambda x: x.rerank_score, reverse=True)

        # 计算排名变化
        for i, result in enumerate(final_results):
            original_rank = original_ranks.get(result.id, (i, 0))[0]
            result.rank_change = original_rank - i

        return final_results[:self.config.top_k]


class RerankEngine:
    """重排序引擎

    整合多种重排序策略。

    使用示例:
        engine = RerankEngine()
        engine.add_reranker("score", ScoreBasedReranker())
        results = engine.rerank(query, search_results, strategy=RerankStrategy.HYBRID)
    """

    def __init__(self, config: RerankConfig | None = None) -> None:
        """初始化重排序引擎"""
        self.config = config or RerankConfig()
        self._rerankers: dict[str, Reranker] = {}
        self._lock = threading.RLock()

        # 注册默认重排序器
        self._register_default_rerankers()

    def _register_default_rerankers(self) -> None:
        """注册默认重排序器"""
        self._rerankers["score"] = ScoreBasedReranker(self.config)
        self._rerankers["diversity"] = DiversityReranker(self.config)
        self._rerankers["recency"] = RecencyReranker(self.config)
        self._rerankers["relevance"] = RelevanceReranker(self.config)
        self._rerankers["hybrid"] = HybridReranker(self.config)

    def add_reranker(self, name: str, reranker: Reranker) -> None:
        """添加重排序器"""
        with self._lock:
            self._rerankers[name] = reranker

    def remove_reranker(self, name: str) -> bool:
        """移除重排序器"""
        with self._lock:
            if name in self._rerankers:
                del self._rerankers[name]
                return True
            return False

    def rerank(
        self,
        query: str,
        results: list[tuple[str, str, float, dict[str, Any]]],
        strategy: RerankStrategy | None = None,
        top_k: int | None = None,
    ) -> tuple[list[RerankResult], RerankReport]:
        """
        执行重排序

        Args:
            query: 查询文本
            results: 搜索结果 [(id, content, score, metadata), ...]
            strategy: 重排序策略
            top_k: 返回结果数

        Returns:
            (重排序结果, 重排序报告)
        """
        start_time = time.time()

        strategy = strategy or self.config.strategy
        top_k = top_k or self.config.top_k

        # 选择重排序器
        reranker_name = strategy.value
        reranker = self._rerankers.get(reranker_name)

        if not reranker:
            logger.warning(f"未找到重排序器: {reranker_name}, 使用默认")
            reranker = self._rerankers.get("hybrid", HybridReranker(self.config))

        # 执行重排序
        reranked = reranker.rerank(query, results)

        # 生成报告
        original_order = [r[0] for r in results[:top_k]]
        reranked_order = [r.id for r in reranked]

        score_changes = [r.rerank_score - r.original_score for r in reranked]
        avg_score_change = sum(score_changes) / len(score_changes) if score_changes else 0.0

        report = RerankReport(
            original_order=original_order,
            reranked_order=reranked_order,
            strategy=strategy,
            execution_time=time.time() - start_time,
            avg_score_change=avg_score_change,
            score_improvement=sum(1 for s in score_changes if s > 0),
            score_degradation=sum(1 for s in score_changes if s < 0),
        )

        return reranked, report

    def get_available_strategies(self) -> list[str]:
        """获取可用的重排序策略"""
        return list(self._rerankers.keys())


# 全局实例
_engine: RerankEngine | None = None


def get_rerank_engine() -> RerankEngine:
    """获取全局重排序引擎"""
    global _engine
    if _engine is None:
        _engine = RerankEngine()
    return _engine


def rerank(
    query: str,
    results: list[tuple[str, str, float, dict[str, Any]]],
    strategy: RerankStrategy | None = None,
    top_k: int = 10,
) -> list[RerankResult]:
    """便捷函数：执行重排序"""
    engine = get_rerank_engine()
    reranked, _report = engine.rerank(query, results, strategy, top_k)
    return reranked