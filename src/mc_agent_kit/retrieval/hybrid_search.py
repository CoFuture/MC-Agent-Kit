"""
混合搜索模块

结合关键词搜索和语义搜索，提供更准确的检索结果。
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from .semantic_search import SemanticSearchConfig, SemanticSearchEngine

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchResult:
    """混合搜索结果"""

    id: str
    content: str
    score: float
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "keyword_score": self.keyword_score,
            "semantic_score": self.semantic_score,
            "metadata": self.metadata,
        }


@dataclass
class HybridSearchConfig:
    """混合搜索配置"""

    # 权重配置
    keyword_weight: float = 0.4
    semantic_weight: float = 0.6

    # 搜索配置
    default_top_k: int = 10
    keyword_top_k: int = 20
    semantic_top_k: int = 20

    # 去重配置
    deduplicate: bool = True

    # 语义搜索配置
    semantic_config: SemanticSearchConfig | None = None


class KeywordSearchEngine:
    """
    关键词搜索引擎

    提供简单的关键词搜索功能，支持 BM25 风格的评分。
    """

    def __init__(self):
        self._documents: dict[str, str] = {}
        self._inverted_index: dict[str, set[str]] = {}
        self._doc_lengths: dict[str, int] = {}
        self._avg_doc_length: float = 0

    def index(self, documents: dict[str, str]) -> None:
        """
        索引文档

        Args:
            documents: 文档 ID 到内容的映射
        """
        self._documents = documents
        self._inverted_index.clear()
        self._doc_lengths.clear()

        total_length = 0

        for doc_id, content in documents.items():
            # 分词
            terms = self._tokenize(content)
            self._doc_lengths[doc_id] = len(terms)
            total_length += len(terms)

            # 构建倒排索引
            for term in terms:
                if term not in self._inverted_index:
                    self._inverted_index[term] = set()
                self._inverted_index[term].add(doc_id)

        self._avg_doc_length = total_length / len(documents) if documents else 0
        logger.info(f"关键词索引构建完成: {len(documents)} 个文档, {len(self._inverted_index)} 个词项")

    def _tokenize(self, text: str) -> list[str]:
        """
        分词

        Args:
            text: 输入文本

        Returns:
            词项列表
        """
        import re
        # 简单分词：按非字母数字分割，转小写
        # 对中文，按字符分割
        terms = []

        # 英文单词
        words = re.findall(r"[a-zA-Z0-9]+", text.lower())
        terms.extend(words)

        # 中文字符（每 2 个字符作为一个词）
        chinese = re.findall(r"[\u4e00-\u9fff]+", text)
        for chunk in chinese:
            for i in range(0, len(chunk) - 1):
                terms.append(chunk[i:i + 2])
            if len(chunk) == 1:
                terms.append(chunk)

        return terms

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[tuple[str, float]]:
        """
        关键词搜索

        使用 BM25 风格的评分算法。

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            (文档 ID, 分数) 元组列表
        """
        if not self._documents:
            return []

        query_terms = self._tokenize(query)

        # 计算每个文档的 BM25 分数
        scores: dict[str, float] = {}
        k1 = 1.5  # BM25 参数
        b = 0.75  # BM25 参数
        n = len(self._documents)

        for term in query_terms:
            if term not in self._inverted_index:
                continue

            # 计算 IDF
            df = len(self._inverted_index[term])
            idf = max(0, ((n - df + 0.5) / (df + 0.5) + 1))

            # 对包含该词的每个文档计算 TF 分数
            for doc_id in self._inverted_index[term]:
                doc_content = self._documents.get(doc_id, "")
                tf = self._tokenize(doc_content).count(term)

                doc_length = self._doc_lengths.get(doc_id, 0)

                # BM25 TF 分数
                tf_score = (tf * (k1 + 1)) / (
                    tf + k1 * (1 - b + b * doc_length / self._avg_doc_length)
                )

                if doc_id not in scores:
                    scores[doc_id] = 0
                scores[doc_id] += idf * tf_score

        # 排序并返回 top_k
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]


class HybridSearchEngine:
    """
    混合搜索引擎

    结合关键词搜索和语义搜索，提供更准确的检索结果。

    使用示例:
        engine = HybridSearchEngine()

        # 索引文档
        documents = {
            "doc1": "如何创建自定义实体",
            "doc2": "GetEngineType API 说明",
        }
        engine.index(documents)

        # 搜索
        results = engine.search("创建实体", top_k=5)
    """

    def __init__(self, config: HybridSearchConfig | None = None):
        """
        初始化混合搜索引擎

        Args:
            config: 搜索配置，为 None 时使用默认配置
        """
        self.config = config or HybridSearchConfig()

        # 初始化语义搜索引擎
        semantic_config = self.config.semantic_config or SemanticSearchConfig()
        self._semantic_engine = SemanticSearchEngine(semantic_config)

        # 初始化关键词搜索引擎
        self._keyword_engine = KeywordSearchEngine()

        # 文档存储（用于关键词搜索）
        self._documents: dict[str, str] = {}
        self._document_metadata: dict[str, dict[str, Any]] = {}

    def index(
        self,
        documents: dict[str, str],
        metadatas: dict[str, dict[str, Any]] | None = None,
    ) -> int:
        """
        索引文档

        Args:
            documents: 文档 ID 到内容的映射
            metadatas: 可选的元数据映射

        Returns:
            索引的文档数量
        """
        self._documents = documents
        self._document_metadata = metadatas or {}

        # 索引到关键词引擎
        self._keyword_engine.index(documents)

        # 索引到语义引擎
        from .vector_store import Document

        doc_list: list[Document] = []
        for doc_id, content in documents.items():
            metadata = self._document_metadata.get(doc_id, {})
            doc_list.append(Document(
                id=doc_id,
                content=content,
                metadata=metadata,
            ))

        self._semantic_engine.index_documents(doc_list)

        logger.info(f"混合索引构建完成: {len(documents)} 个文档")
        return len(documents)

    def search(
        self,
        query: str,
        top_k: int | None = None,
        keyword_weight: float | None = None,
        semantic_weight: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[HybridSearchResult]:
        """
        混合搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            keyword_weight: 关键词搜索权重
            semantic_weight: 语义搜索权重
            filters: 元数据过滤条件

        Returns:
            混合搜索结果列表
        """
        top_k = top_k or self.config.default_top_k
        keyword_weight = keyword_weight if keyword_weight is not None else self.config.keyword_weight
        semantic_weight = semantic_weight if semantic_weight is not None else self.config.semantic_weight

        # 归一化权重
        total_weight = keyword_weight + semantic_weight
        keyword_weight /= total_weight
        semantic_weight /= total_weight

        # 关键词搜索
        keyword_results = self._keyword_engine.search(
            query, top_k=self.config.keyword_top_k
        )
        keyword_scores = {doc_id: score for doc_id, score in keyword_results}

        # 归一化关键词分数
        if keyword_scores:
            max_kw_score = max(keyword_scores.values())
            if max_kw_score > 0:
                keyword_scores = {
                    k: v / max_kw_score for k, v in keyword_scores.items()
                }

        # 语义搜索
        semantic_results = self._semantic_engine.search(
            query, top_k=self.config.semantic_top_k, filters=filters
        )
        semantic_scores = {r.id: r.score for r in semantic_results}

        # 合并结果
        all_doc_ids = set(keyword_scores.keys()) | set(semantic_scores.keys())

        results: list[HybridSearchResult] = []

        for doc_id in all_doc_ids:
            kw_score = keyword_scores.get(doc_id, 0.0)
            sem_score = semantic_scores.get(doc_id, 0.0)

            # 加权综合分数
            combined_score = keyword_weight * kw_score + semantic_weight * sem_score

            content = self._documents.get(doc_id, "")
            metadata = self._document_metadata.get(doc_id, {})

            results.append(HybridSearchResult(
                id=doc_id,
                content=content,
                score=combined_score,
                keyword_score=kw_score,
                semantic_score=sem_score,
                metadata=metadata,
            ))

        # 排序
        results.sort(key=lambda r: r.score, reverse=True)

        return results[:top_k]

    def keyword_only_search(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[HybridSearchResult]:
        """
        仅使用关键词搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            搜索结果列表
        """
        keyword_results = self._keyword_engine.search(query, top_k=top_k)

        results = []
        for doc_id, score in keyword_results:
            results.append(HybridSearchResult(
                id=doc_id,
                content=self._documents.get(doc_id, ""),
                score=score,
                keyword_score=score,
                semantic_score=0.0,
                metadata=self._document_metadata.get(doc_id, {}),
            ))

        return results

    def semantic_only_search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[HybridSearchResult]:
        """
        仅使用语义搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 元数据过滤条件

        Returns:
            搜索结果列表
        """
        semantic_results = self._semantic_engine.search(
            query, top_k=top_k, filters=filters
        )

        results = []
        for r in semantic_results:
            results.append(HybridSearchResult(
                id=r.id,
                content=r.content,
                score=r.score,
                keyword_score=0.0,
                semantic_score=r.score,
                metadata=r.metadata,
            ))

        return results

    def get_stats(self) -> dict[str, Any]:
        """获取搜索统计信息"""
        return {
            "document_count": len(self._documents),
            "keyword_weight": self.config.keyword_weight,
            "semantic_weight": self.config.semantic_weight,
            "semantic_stats": self._semantic_engine.get_stats().to_dict(),
        }

    def clear(self) -> None:
        """清空索引"""
        self._documents.clear()
        self._document_metadata.clear()
        self._semantic_engine.clear()


def create_hybrid_search_engine(
    persist_dir: str | None = None,
    keyword_weight: float = 0.4,
    semantic_weight: float = 0.6,
) -> HybridSearchEngine:
    """
    创建混合搜索引擎的便捷函数

    Args:
        persist_dir: 持久化目录
        keyword_weight: 关键词搜索权重
        semantic_weight: 语义搜索权重

    Returns:
        初始化好的混合搜索引擎
    """
    semantic_config = SemanticSearchConfig(persist_dir=persist_dir)
    config = HybridSearchConfig(
        keyword_weight=keyword_weight,
        semantic_weight=semantic_weight,
        semantic_config=semantic_config,
    )
    return HybridSearchEngine(config)
