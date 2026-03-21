"""
向量存储模块

基于 ChromaDB 实现向量存储和检索功能。
"""

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VectorStoreConfig:
    """向量存储配置"""

    persist_dir: str | None = None
    collection_name: str = "mc_knowledge"
    embedding_model: str = "all-MiniLM-L6-v2"
    distance_metric: str = "cosine"  # cosine, l2, ip
    batch_size: int = 100

    # 增量更新配置
    enable_incremental: bool = True
    hash_algorithm: str = "md5"


@dataclass
class Document:
    """文档数据结构"""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
        }


@dataclass
class SearchResult:
    """搜索结果"""

    id: str
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
        }


class VectorStore:
    """
    向量存储

    基于 ChromaDB 实现文档的向量化存储和语义检索。

    使用示例:
        store = VectorStore(persist_dir="./data/vectors")

        # 添加文档
        docs = [
            Document(id="1", content="如何创建自定义实体", metadata={"type": "guide"}),
            Document(id="2", content="GetEngineType API 说明", metadata={"type": "api"}),
        ]
        store.add_documents(docs)

        # 搜索
        results = store.search("创建实体", top_k=5)
    """

    def __init__(self, config: VectorStoreConfig | None = None):
        """
        初始化向量存储

        Args:
            config: 存储配置，为 None 时使用默认配置
        """
        self.config = config or VectorStoreConfig()
        self._client = None
        self._collection = None
        self._embedding_fn = None
        self._document_hashes: dict[str, str] = {}
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """确保存储已初始化"""
        if self._initialized:
            return

        try:
            import chromadb
            from chromadb.config import Settings

            # 创建客户端
            if self.config.persist_dir:
                persist_path = Path(self.config.persist_dir)
                persist_path.mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(
                    path=str(persist_path),
                    settings=Settings(anonymized_telemetry=False)
                )
            else:
                self._client = chromadb.Client()

            # 获取或创建集合
            self._collection = self._client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": self.config.distance_metric}
            )

            # 初始化 embedding 函数
            self._init_embedding_function()

            # 加载已有文档的哈希（用于增量更新）
            self._load_document_hashes()

            self._initialized = True
            logger.info(f"向量存储初始化完成，集合: {self.config.collection_name}")

        except ImportError as e:
            logger.warning(f"ChromaDB 未安装: {e}")
            self._initialized = True  # 允许在没有 ChromaDB 时运行

    def _init_embedding_function(self) -> None:
        """初始化嵌入函数"""
        try:
            from chromadb.utils import embedding_functions

            # 使用 Sentence Transformers
            self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.config.embedding_model
            )
            logger.info(f"Embedding 模型加载完成: {self.config.embedding_model}")

        except ImportError:
            logger.warning("sentence-transformers 未安装，将使用默认嵌入")
            self._embedding_fn = None

    def _load_document_hashes(self) -> None:
        """加载已有文档的哈希值"""
        if not self._collection:
            return

        try:
            # 获取所有文档的元数据
            result = self._collection.get(include=["metadatas"])

            if result and result["metadatas"]:
                for i, meta in enumerate(result["metadatas"]):
                    if meta and "content_hash" in meta:
                        doc_id = result["ids"][i]
                        self._document_hashes[doc_id] = meta["content_hash"]

            logger.info(f"加载了 {len(self._document_hashes)} 个文档哈希")

        except Exception as e:
            logger.warning(f"加载文档哈希失败: {e}")

    def _compute_hash(self, content: str) -> str:
        """计算内容哈希"""
        if self.config.hash_algorithm == "md5":
            return hashlib.md5(content.encode()).hexdigest()
        elif self.config.hash_algorithm == "sha256":
            return hashlib.sha256(content.encode()).hexdigest()
        else:
            return hashlib.md5(content.encode()).hexdigest()

    def add_documents(self, documents: list[Document]) -> int:
        """
        添加文档到向量存储

        Args:
            documents: 文档列表

        Returns:
            实际添加的文档数量
        """
        self._ensure_initialized()

        if not self._collection:
            logger.warning("集合未初始化，跳过添加文档")
            return 0

        added_count = 0
        docs_to_add: list[Document] = []

        for doc in documents:
            # 检查是否需要更新
            if self.config.enable_incremental:
                content_hash = self._compute_hash(doc.content)
                existing_hash = self._document_hashes.get(doc.id)

                if existing_hash == content_hash:
                    # 内容未变化，跳过
                    continue

                # 更新哈希
                doc.metadata["content_hash"] = content_hash
                self._document_hashes[doc.id] = content_hash

            docs_to_add.append(doc)

        if not docs_to_add:
            logger.info("所有文档已是最新，无需更新")
            return 0

        # 批量添加
        for i in range(0, len(docs_to_add), self.config.batch_size):
            batch = docs_to_add[i:i + self.config.batch_size]

            ids = [d.id for d in batch]
            contents = [d.content for d in batch]
            metadatas = [d.metadata for d in batch]

            # 如果已有同 ID 文档，先删除
            try:
                self._collection.delete(ids=ids)
            except Exception:
                pass

            # 添加新文档
            self._collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas,
            )

            added_count += len(batch)

        logger.info(f"添加了 {added_count} 个文档到向量存储")
        return added_count

    def delete_documents(self, ids: list[str]) -> None:
        """
        删除文档

        Args:
            ids: 要删除的文档 ID 列表
        """
        self._ensure_initialized()

        if not self._collection:
            return

        try:
            self._collection.delete(ids=ids)

            # 更新哈希记录
            for doc_id in ids:
                self._document_hashes.pop(doc_id, None)

            logger.info(f"删除了 {len(ids)} 个文档")

        except Exception as e:
            logger.warning(f"删除文档失败: {e}")

    def search(
        self,
        query: str,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        语义搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            where: 元数据过滤条件
            where_document: 文档内容过滤条件

        Returns:
            搜索结果列表
        """
        self._ensure_initialized()

        if not self._collection:
            return []

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where,
                where_document=where_document,
            )

            search_results = []

            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0

                    # 转换距离为相似度分数
                    score = 1 - distance if self.config.distance_metric == "cosine" else 1 / (1 + distance)

                    search_results.append(SearchResult(
                        id=results["ids"][0][i],
                        content=doc,
                        score=score,
                        metadata=metadata,
                    ))

            return search_results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def get_document(self, doc_id: str) -> Document | None:
        """
        获取单个文档

        Args:
            doc_id: 文档 ID

        Returns:
            文档对象，不存在则返回 None
        """
        self._ensure_initialized()

        if not self._collection:
            return None

        try:
            result = self._collection.get(
                ids=[doc_id],
                include=["documents", "metadatas"]
            )

            if result and result["documents"]:
                return Document(
                    id=doc_id,
                    content=result["documents"][0],
                    metadata=result["metadatas"][0] if result["metadatas"] else {},
                )

        except Exception as e:
            logger.warning(f"获取文档失败: {e}")

        return None

    def count(self) -> int:
        """获取文档数量"""
        self._ensure_initialized()

        if not self._collection:
            return 0

        try:
            return self._collection.count()
        except Exception:
            return 0

    def clear(self) -> None:
        """清空所有文档"""
        self._ensure_initialized()

        if not self._client or not self._collection:
            return

        try:
            self._client.delete_collection(self.config.collection_name)
            self._collection = self._client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": self.config.distance_metric}
            )
            self._document_hashes.clear()
            logger.info("向量存储已清空")

        except Exception as e:
            logger.warning(f"清空存储失败: {e}")

    def get_stats(self) -> dict[str, Any]:
        """获取存储统计信息"""
        self._ensure_initialized()

        return {
            "collection_name": self.config.collection_name,
            "document_count": self.count(),
            "embedding_model": self.config.embedding_model,
            "distance_metric": self.config.distance_metric,
            "persist_dir": self.config.persist_dir,
            "incremental_enabled": self.config.enable_incremental,
        }


def create_vector_store(
    persist_dir: str | None = None,
    collection_name: str = "mc_knowledge",
    embedding_model: str = "all-MiniLM-L6-v2",
) -> VectorStore:
    """
    创建向量存储的便捷函数

    Args:
        persist_dir: 持久化目录
        collection_name: 集合名称
        embedding_model: Embedding 模型名称

    Returns:
        初始化好的向量存储
    """
    config = VectorStoreConfig(
        persist_dir=persist_dir,
        collection_name=collection_name,
        embedding_model=embedding_model,
    )
    return VectorStore(config)
