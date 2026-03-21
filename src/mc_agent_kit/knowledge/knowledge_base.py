"""
MC-Agent-Kit 知识库主类

基于 LlamaIndex + ChromaDB 实现的知识检索系统。
"""

import hashlib
import json
import logging
from pathlib import Path

from .base import Document, DocumentChunk, DocumentType, SearchResult

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    MC ModSDK 知识库
    
    提供文档索引、语义搜索、API 查询等功能。
    
    使用示例:
        # 初始化并构建索引
        kb = KnowledgeBase(
            docs_path="resources/docs",
            persist_dir="data/knowledge_db"
        )
        kb.build_index()
        
        # 搜索
        results = kb.search("如何创建自定义实体")
        
        # 加载已有索引
        kb = KnowledgeBase.load("data/knowledge_db")
    """

    def __init__(
        self,
        docs_path: str | None = None,
        persist_dir: str | None = None,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        """
        初始化知识库
        
        Args:
            docs_path: 文档目录路径
            persist_dir: 索引持久化目录
            embedding_model: Embedding 模型名称
            chunk_size: 分块大小（tokens）
            chunk_overlap: 分块重叠（tokens）
        """
        self.docs_path = Path(docs_path) if docs_path else None
        self.persist_dir = Path(persist_dir) if persist_dir else None
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 延迟加载的组件
        self._vector_store = None
        self._embedding_fn = None
        self._documents: list[Document] = []
        self._chunks: list[DocumentChunk] = []
        self._index_built = False

    def build_index(self, force: bool = False) -> None:
        """
        构建知识库索引
        
        Args:
            force: 是否强制重建
        """
        if not self.docs_path:
            raise ValueError("docs_path 未设置")

        logger.info(f"开始构建索引，文档目录: {self.docs_path}")

        # 1. 加载文档
        self._documents = self._load_documents()
        logger.info(f"加载了 {len(self._documents)} 个文档")

        # 2. 文档分块
        self._chunks = self._chunk_documents()
        logger.info(f"生成了 {len(self._chunks)} 个文档块")

        # 3. 创建向量索引
        self._create_vector_index(force)

        self._index_built = True
        logger.info("索引构建完成")

        # 4. 持久化
        if self.persist_dir:
            self.persist()

    def search(
        self,
        query: str,
        doc_type: str = "all",
        top_k: int = 5,
    ) -> list[SearchResult]:
        """
        语义搜索
        
        Args:
            query: 搜索查询
            doc_type: 文档类型过滤 (api/guide/demo/all)
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        if not self._index_built and self.persist_dir:
            self._try_load_index()

        if not self._vector_store:
            logger.warning("索引未构建，返回空结果")
            return []

        # 构建过滤条件
        where_filter = None
        if doc_type != "all":
            where_filter = {"doc_type": doc_type}

        # 执行向量搜索
        results = self._vector_search(query, where_filter, top_k)

        return results

    def get_api(self, api_name: str) -> SearchResult | None:
        """
        获取 API 信息
        
        Args:
            api_name: API 名称
            
        Returns:
            API 信息，未找到返回 None
        """
        results = self.search(api_name, doc_type="api", top_k=3)

        for r in results:
            if r.name and r.name.lower() == api_name.lower():
                return r

        return results[0] if results else None

    def get_code_example(
        self,
        topic: str,
        language: str = "python",
        top_k: int = 3,
    ) -> list[SearchResult]:
        """
        获取代码示例
        
        Args:
            topic: 主题关键词
            language: 代码语言
            top_k: 返回结果数量
            
        Returns:
            代码示例列表
        """
        results = self.search(f"{topic} 示例代码", doc_type="demo", top_k=top_k)
        return results

    def query(self, question: str) -> str:
        """
        问答查询（供 Agent 调用）
        
        Args:
            question: 问题
            
        Returns:
            回答文本
        """
        results = self.search(question, top_k=5)

        if not results:
            return "抱歉，未找到相关知识。请尝试使用更具体的关键词搜索。"

        # 组装上下文
        context_parts = []
        for i, r in enumerate(results, 1):
            context_parts.append(f"### 参考 {i}: {r.source}")
            context_parts.append(r.content[:800])
            context_parts.append("")

        return "\n".join(context_parts)

    def persist(self) -> None:
        """持久化索引"""
        if not self.persist_dir:
            return

        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # 保存元数据
        meta = {
            "embedding_model": self.embedding_model,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "total_documents": len(self._documents),
            "total_chunks": len(self._chunks),
        }

        meta_path = self.persist_dir / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # 保存文档块（用于后续加载）
        chunks_path = self.persist_dir / "chunks.json"
        with open(chunks_path, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in self._chunks], f, ensure_ascii=False)

        logger.info(f"索引已持久化到 {self.persist_dir}")

    @classmethod
    def load(cls, persist_dir: str) -> "KnowledgeBase":
        """
        加载已有索引
        
        Args:
            persist_dir: 持久化目录
            
        Returns:
            KnowledgeBase 实例
        """
        persist_path = Path(persist_dir)

        # 加载元数据
        meta_path = persist_path / "metadata.json"
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        kb = cls(
            persist_dir=persist_dir,
            embedding_model=meta.get("embedding_model"),
            chunk_size=meta.get("chunk_size", 512),
            chunk_overlap=meta.get("chunk_overlap", 50),
        )

        # 加载文档块
        chunks_path = persist_path / "chunks.json"
        with open(chunks_path, encoding="utf-8") as f:
            chunks_data = json.load(f)

        kb._chunks = [DocumentChunk.from_dict(c) for c in chunks_data]
        kb._index_built = True

        logger.info(f"从 {persist_dir} 加载了 {len(kb._chunks)} 个文档块")

        return kb

    def _load_documents(self) -> list[Document]:
        """加载所有文档"""
        documents = []

        for ext in ["*.md", "*.txt"]:
            for fp in self.docs_path.rglob(ext):
                try:
                    content = fp.read_text(encoding="utf-8")
                    doc = Document(
                        path=str(fp),
                        content=content,
                    )
                    documents.append(doc)
                except Exception as e:
                    logger.warning(f"加载文档失败: {fp}, 错误: {e}")

        return documents

    def _chunk_documents(self) -> list[DocumentChunk]:
        """文档分块"""
        chunks = []

        for doc in self._documents:
            doc_chunks = self._chunk_single_document(doc)
            chunks.extend(doc_chunks)

        return chunks

    def _chunk_single_document(self, doc: Document) -> list[DocumentChunk]:
        """
        单文档分块
        
        策略：
        - API 文档：按接口/事件分块
        - 教程文档：按段落分块
        - 代码示例：保持完整
        """
        chunks = []

        # 根据文档类型选择分块策略
        if doc.doc_type in (DocumentType.API, DocumentType.EVENT):
            # API 文档按标题分块
            doc_chunks = self._chunk_by_headers(doc)
        elif doc.doc_type == DocumentType.DEMO:
            # Demo 文档保持完整
            doc_chunks = self._chunk_as_whole(doc)
        else:
            # 其他文档按段落分块
            doc_chunks = self._chunk_by_paragraphs(doc)

        chunks.extend(doc_chunks)
        return chunks

    def _chunk_by_headers(self, doc: Document) -> list[DocumentChunk]:
        """按标题分块（适用于 API 文档）"""
        chunks = []
        content = doc.content

        # 简单的标题分割
        lines = content.split("\n")
        current_section = []
        current_title = ""

        for line in lines:
            if line.startswith("# "):
                if current_section:
                    chunk_content = "\n".join(current_section)
                    if len(chunk_content.strip()) > 50:
                        chunks.append(self._create_chunk(
                            doc, chunk_content, current_title, len(chunks)
                        ))
                current_title = line[2:].strip()
                current_section = [line]
            else:
                current_section.append(line)

        # 最后一节
        if current_section:
            chunk_content = "\n".join(current_section)
            if len(chunk_content.strip()) > 50:
                chunks.append(self._create_chunk(
                    doc, chunk_content, current_title, len(chunks)
                ))

        return chunks

    def _chunk_by_paragraphs(self, doc: Document) -> list[DocumentChunk]:
        """按段落分块"""
        chunks = []
        paragraphs = doc.content.split("\n\n")

        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para.split())

            if current_size + para_size > self.chunk_size and current_chunk:
                chunk_content = "\n\n".join(current_chunk)
                chunks.append(self._create_chunk(
                    doc, chunk_content, None, len(chunks)
                ))
                current_chunk = []
                current_size = 0

            current_chunk.append(para)
            current_size += para_size

        if current_chunk:
            chunk_content = "\n\n".join(current_chunk)
            chunks.append(self._create_chunk(
                doc, chunk_content, None, len(chunks)
            ))

        return chunks

    def _chunk_as_whole(self, doc: Document) -> list[DocumentChunk]:
        """整体作为一个块"""
        return [self._create_chunk(doc, doc.content, None, 0)]

    def _create_chunk(
        self,
        doc: Document,
        content: str,
        name: str | None,
        index: int,
    ) -> DocumentChunk:
        """创建文档块"""
        chunk_id = self._generate_chunk_id(doc.path, index)

        return DocumentChunk(
            id=chunk_id,
            content=content,
            source=doc.path,
            doc_type=doc.doc_type,
            category=self._extract_category(doc.path),
            name=name,
            chunk_index=index,
        )

    def _generate_chunk_id(self, source: str, index: int) -> str:
        """生成块 ID"""
        hash_input = f"{source}:{index}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]

    def _extract_category(self, path: str) -> str | None:
        """从路径提取分类"""
        parts = Path(path).parts

        # 尝试从路径中提取分类
        for i, part in enumerate(parts):
            if part in ["接口", "事件", "枚举值"] and i + 1 < len(parts):
                return parts[i + 1]

        return None

    def _create_vector_index(self, force: bool) -> None:
        """创建向量索引"""
        try:
            # 尝试导入 ChromaDB
            import chromadb
            from chromadb.config import Settings

            # 创建/加载向量存储
            if self.persist_dir:
                chroma_path = self.persist_dir / "chroma"
                client = chromadb.PersistentClient(path=str(chroma_path))
            else:
                client = chromadb.Client()

            # 创建集合
            collection_name = "mc_knowledge"
            if force:
                try:
                    client.delete_collection(collection_name)
                except:
                    pass

            self._vector_store = client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            # 添加文档块
            self._add_chunks_to_store()

        except ImportError:
            logger.warning("ChromaDB 未安装，使用简单内存索引")
            self._vector_store = None

    def _add_chunks_to_store(self) -> None:
        """将文档块添加到向量存储"""
        if not self._vector_store or not self._chunks:
            return

        # 批量添加
        batch_size = 100

        for i in range(0, len(self._chunks), batch_size):
            batch = self._chunks[i:i + batch_size]

            ids = [c.id for c in batch]
            documents = [c.content for c in batch]
            metadatas = [c.to_dict() for c in batch]

            self._vector_store.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )

    def _vector_search(
        self,
        query: str,
        where_filter: dict | None,
        top_k: int,
    ) -> list[SearchResult]:
        """向量搜索"""
        if not self._vector_store:
            return []

        results = self._vector_store.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter,
        )

        search_results = []

        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0

                search_results.append(SearchResult(
                    content=doc,
                    source=metadata.get("source", ""),
                    doc_type=DocumentType(metadata.get("doc_type", "unknown")),
                    score=1 - distance,  # 转换为相似度
                    category=metadata.get("category"),
                    name=metadata.get("name"),
                    metadata=metadata,
                ))

        return search_results

    def _try_load_index(self) -> bool:
        """尝试加载已有索引"""
        if self.persist_dir and (self.persist_dir / "metadata.json").exists():
            try:
                loaded = KnowledgeBase.load(str(self.persist_dir))
                self._chunks = loaded._chunks
                self._index_built = True
                return True
            except Exception as e:
                logger.warning(f"加载索引失败: {e}")
        return False
