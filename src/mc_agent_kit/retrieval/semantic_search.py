"""
语义搜索模块

基于向量嵌入实现语义搜索功能。
"""

import logging
from dataclasses import dataclass
from typing import Any

from .vector_store import Document, SearchResult, VectorStore, VectorStoreConfig

logger = logging.getLogger(__name__)


@dataclass
class SemanticSearchConfig:
    """语义搜索配置"""

    # 向量存储配置
    persist_dir: str | None = None
    collection_name: str = "mc_knowledge"
    embedding_model: str = "all-MiniLM-L6-v2"

    # 分块配置
    chunk_size: int = 512
    chunk_overlap: int = 50

    # 搜索配置
    default_top_k: int = 5
    min_score: float = 0.0

    # 重排序配置
    enable_rerank: bool = False
    rerank_top_n: int = 10


@dataclass
class IndexStats:
    """索引统计信息"""

    total_documents: int = 0
    total_chunks: int = 0
    embedding_model: str = ""
    collection_name: str = ""
    persist_dir: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_documents": self.total_documents,
            "total_chunks": self.total_chunks,
            "embedding_model": self.embedding_model,
            "collection_name": self.collection_name,
            "persist_dir": self.persist_dir,
        }


class SemanticSearchEngine:
    """
    语义搜索引擎

    提供文档索引构建和语义搜索功能。

    使用示例:
        engine = SemanticSearchEngine(persist_dir="./data/semantic_index")

        # 索引文档
        docs = ["如何创建自定义实体", "GetEngineType API 说明"]
        engine.index_documents(docs)

        # 搜索
        results = engine.search("创建实体")
    """

    def __init__(self, config: SemanticSearchConfig | None = None):
        """
        初始化语义搜索引擎

        Args:
            config: 搜索配置，为 None 时使用默认配置
        """
        self.config = config or SemanticSearchConfig()

        # 初始化向量存储
        store_config = VectorStoreConfig(
            persist_dir=self.config.persist_dir,
            collection_name=self.config.collection_name,
            embedding_model=self.config.embedding_model,
        )
        self._vector_store = VectorStore(store_config)

        # 文档计数
        self._document_count = 0
        self._chunk_count = 0

    def index_documents(
        self,
        documents: list[str | Document],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> int:
        """
        索引文档

        Args:
            documents: 文档列表（字符串或 Document 对象）
            metadatas: 可选的元数据列表

        Returns:
            添加的文档块数量
        """
        # 转换为 Document 对象
        docs: list[Document] = []

        for i, doc in enumerate(documents):
            if isinstance(doc, str):
                metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
                docs.append(Document(
                    id=self._generate_doc_id(doc, i),
                    content=doc,
                    metadata=metadata,
                ))
            else:
                docs.append(doc)

        # 分块处理
        chunked_docs = self._chunk_documents(docs)

        # 添加到向量存储
        added = self._vector_store.add_documents(chunked_docs)

        self._document_count += len(docs)
        self._chunk_count += added

        logger.info(f"索引了 {len(docs)} 个文档，生成了 {len(chunked_docs)} 个块，添加了 {added} 个新块")

        return added

    def _generate_doc_id(self, content: str, index: int) -> str:
        """生成文档 ID"""
        import hashlib
        hash_input = f"{content[:100]}:{index}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]

    def _chunk_documents(self, documents: list[Document]) -> list[Document]:
        """
        文档分块

        Args:
            documents: 原始文档列表

        Returns:
            分块后的文档列表
        """
        chunked_docs: list[Document] = []

        for doc in documents:
            chunks = self._chunk_text(doc.content)

            for i, chunk_content in enumerate(chunks):
                chunk_id = f"{doc.id}_chunk_{i}"
                chunk_metadata = {
                    **doc.metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "source_id": doc.id,
                }

                chunked_docs.append(Document(
                    id=chunk_id,
                    content=chunk_content,
                    metadata=chunk_metadata,
                ))

        return chunked_docs

    def _chunk_text(self, text: str) -> list[str]:
        """
        文本分块

        Args:
            text: 原始文本

        Returns:
            分块后的文本列表
        """
        if len(text) <= self.config.chunk_size:
            return [text]

        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = start + self.config.chunk_size

            # 尝试在句子边界分割
            if end < len(text):
                # 查找最近的句号、问号、感叹号或换行
                for sep in ["。", "！", "？", "\n\n", ".", "!", "?"]:
                    last_sep = text.rfind(sep, start, end + self.config.chunk_overlap)
                    if last_sep > start:
                        end = last_sep + 1
                        break

            chunks.append(text[start:end].strip())
            start = end - self.config.chunk_overlap

            if start < 0:
                start = 0

        return chunks

    def search(
        self,
        query: str,
        top_k: int | None = None,
        min_score: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        语义搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量，为 None 时使用默认值
            min_score: 最小相似度分数，为 None 时使用默认值
            filters: 元数据过滤条件

        Returns:
            搜索结果列表
        """
        top_k = top_k or self.config.default_top_k
        min_score = min_score if min_score is not None else self.config.min_score

        # 执行向量搜索
        results = self._vector_store.search(
            query=query,
            top_k=top_k * 2 if self.config.enable_rerank else top_k,
            where=filters,
        )

        # 过滤低分结果
        results = [r for r in results if r.score >= min_score]

        # 重排序（如果启用）
        if self.config.enable_rerank and len(results) > top_k:
            results = self._rerank(query, results, top_k)

        return results[:top_k]

    def _rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int,
    ) -> list[SearchResult]:
        """
        重排序搜索结果

        Args:
            query: 查询文本
            results: 原始搜索结果
            top_k: 返回数量

        Returns:
            重排序后的结果
        """
        # 简单的重排序策略：结合向量分数和关键词匹配
        query_terms = set(query.lower().split())

        for result in results:
            content_terms = set(result.content.lower().split())
            keyword_overlap = len(query_terms & content_terms) / max(len(query_terms), 1)

            # 综合分数：向量分数 * 0.7 + 关键词重叠 * 0.3
            result.score = result.score * 0.7 + keyword_overlap * 0.3

        # 重新排序
        results.sort(key=lambda r: r.score, reverse=True)

        return results[:top_k]

    def delete_document(self, doc_id: str) -> None:
        """
        删除文档及其所有分块

        Args:
            doc_id: 文档 ID
        """
        # ChromaDB 不支持前缀删除，需要逐个删除
        # 这里简化处理，假设文档 ID 即为块 ID
        self._vector_store.delete_documents([doc_id])

    def clear(self) -> None:
        """清空索引"""
        self._vector_store.clear()
        self._document_count = 0
        self._chunk_count = 0

    def get_stats(self) -> IndexStats:
        """获取索引统计信息"""
        return IndexStats(
            total_documents=self._document_count,
            total_chunks=self._chunk_count,
            embedding_model=self.config.embedding_model,
            collection_name=self.config.collection_name,
            persist_dir=self.config.persist_dir,
        )

    def count(self) -> int:
        """获取索引中的文档块数量"""
        return self._vector_store.count()


def create_semantic_search_engine(
    persist_dir: str | None = None,
    embedding_model: str = "all-MiniLM-L6-v2",
) -> SemanticSearchEngine:
    """
    创建语义搜索引擎的便捷函数

    Args:
        persist_dir: 持久化目录
        embedding_model: Embedding 模型名称

    Returns:
        初始化好的搜索引擎
    """
    config = SemanticSearchConfig(
        persist_dir=persist_dir,
        embedding_model=embedding_model,
    )
    return SemanticSearchEngine(config)
