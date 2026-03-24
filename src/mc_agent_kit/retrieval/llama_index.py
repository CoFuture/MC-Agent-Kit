"""
LlamaIndex 集成模块

提供与 LlamaIndex 框架的集成，支持高级 RAG 功能。
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LlamaIndexConfig:
    """LlamaIndex 配置"""

    persist_dir: str | None = None
    collection_name: str = "mc_knowledge"
    embedding_model: str = "all-MiniLM-L6-v2"

    # 查询配置
    similarity_top_k: int = 5
    response_mode: str = "compact"  # compact, refine, tree_summarize

    # 流式响应
    streaming: bool = False


class LlamaIndexRetriever:
    """
    LlamaIndex 检索器

    基于 LlamaIndex 框架实现的高级检索功能。

    使用示例:
        retriever = LlamaIndexRetriever(persist_dir="./data/llama_index")

        # 索引文档
        retriever.index_documents(docs)

        # 查询
        response = retriever.query("如何创建自定义实体？")
    """

    def __init__(self, config: LlamaIndexConfig | None = None):
        """
        初始化检索器

        Args:
            config: 配置对象
        """
        self.config = config or LlamaIndexConfig()
        self._index = None
        self._vector_store = None
        self._storage_context = None
        self._llama_available = False

        # 检查 LlamaIndex 是否可用
        self._check_availability()

    def _check_availability(self) -> None:
        """检查 LlamaIndex 是否可用"""
        try:
            import llama_index  # noqa: F401 - 导入用于检查可用性
            self._llama_available = True
            logger.info("LlamaIndex 可用")
        except ImportError:
            self._llama_available = False
            logger.warning("LlamaIndex 未安装，部分功能不可用")

    def index_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> bool:
        """
        索引文档

        Args:
            documents: 文档内容列表
            metadatas: 可选的元数据列表

        Returns:
            是否成功
        """
        if not self._llama_available:
            logger.warning("LlamaIndex 不可用，无法索引文档")
            return False

        try:
            from llama_index.core import Document, VectorStoreIndex
            from llama_index.core.storage import StorageContext

            # 创建 LlamaIndex 文档
            llama_docs = []
            for i, content in enumerate(documents):
                metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
                llama_docs.append(Document(text=content, metadata=metadata))

            # 初始化向量存储
            self._init_vector_store()

            # 创建索引
            if self._vector_store:
                self._storage_context = StorageContext.from_defaults(
                    vector_store=self._vector_store
                )
                self._index = VectorStoreIndex.from_documents(
                    llama_docs,
                    storage_context=self._storage_context,
                )
            else:
                self._index = VectorStoreIndex.from_documents(llama_docs)

            # 持久化
            if self.config.persist_dir:
                self._index.storage_context.persist(persist_dir=self.config.persist_dir)

            logger.info(f"索引了 {len(documents)} 个文档")
            return True

        except Exception as e:
            logger.error(f"索引文档失败: {e}")
            return False

    def _init_vector_store(self) -> None:
        """初始化向量存储"""
        if not self._llama_available:
            return

        try:
            import chromadb
            from llama_index.vector_stores.chroma import ChromaVectorStore

            # 创建 ChromaDB 客户端
            if self.config.persist_dir:
                persist_path = Path(self.config.persist_dir)
                persist_path.mkdir(parents=True, exist_ok=True)
                client = chromadb.PersistentClient(path=str(persist_path / "chroma"))
            else:
                client = chromadb.Client()

            # 获取或创建集合
            collection = client.get_or_create_collection(self.config.collection_name)

            # 创建向量存储
            self._vector_store = ChromaVectorStore(chroma_collection=collection)

            logger.info(f"ChromaDB 向量存储初始化完成: {self.config.collection_name}")

        except ImportError as e:
            logger.warning(f"ChromaDB 或 llama-index-vector-stores-chroma 未安装: {e}")
            self._vector_store = None
        except Exception as e:
            logger.error(f"初始化向量存储失败: {e}")
            self._vector_store = None

    def load_index(self, persist_dir: str | None = None) -> bool:
        """
        加载已有索引

        Args:
            persist_dir: 索引目录，为 None 时使用配置中的目录

        Returns:
            是否成功
        """
        if not self._llama_available:
            return False

        persist_dir = persist_dir or self.config.persist_dir
        if not persist_dir:
            logger.warning("未指定索引目录")
            return False

        try:
            from llama_index.core import StorageContext, load_index_from_storage

            # 加载存储上下文
            self._storage_context = StorageContext.from_defaults(persist_dir=persist_dir)

            # 加载索引
            self._index = load_index_from_storage(self._storage_context)

            logger.info(f"从 {persist_dir} 加载索引成功")
            return True

        except Exception as e:
            logger.error(f"加载索引失败: {e}")
            return False

    def query(self, query_str: str) -> str:
        """
        查询

        Args:
            query_str: 查询字符串

        Returns:
            响应文本
        """
        if not self._llama_available or not self._index:
            return "LlamaIndex 不可用或索引未初始化"

        try:
            # 创建查询引擎
            query_engine = self._index.as_query_engine(
                similarity_top_k=self.config.similarity_top_k,
                response_mode=self.config.response_mode,
                streaming=self.config.streaming,
            )

            # 执行查询
            response = query_engine.query(query_str)

            return str(response)

        except Exception as e:
            logger.error(f"查询失败: {e}")
            return f"查询失败: {e}"

    def retrieve(self, query_str: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        检索相关文档

        Args:
            query_str: 查询字符串
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        if not self._llama_available or not self._index:
            return []

        try:
            # 创建检索器
            retriever = self._index.as_retriever(similarity_top_k=top_k)

            # 检索
            nodes = retriever.retrieve(query_str)

            # 转换为字典
            results = []
            for node in nodes:
                results.append({
                    "content": node.node.text,
                    "score": node.score,
                    "metadata": node.node.metadata,
                })

            return results

        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []

    def is_available(self) -> bool:
        """检查 LlamaIndex 是否可用"""
        return self._llama_available

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "llama_available": self._llama_available,
            "index_loaded": self._index is not None,
            "persist_dir": self.config.persist_dir,
            "collection_name": self.config.collection_name,
            "embedding_model": self.config.embedding_model,
        }


def create_llama_index_retriever(
    persist_dir: str | None = None,
    embedding_model: str = "all-MiniLM-L6-v2",
) -> LlamaIndexRetriever:
    """
    创建 LlamaIndex 检索器的便捷函数

    Args:
        persist_dir: 持久化目录
        embedding_model: Embedding 模型名称

    Returns:
        初始化好的检索器
    """
    config = LlamaIndexConfig(
        persist_dir=persist_dir,
        embedding_model=embedding_model,
    )
    return LlamaIndexRetriever(config)
