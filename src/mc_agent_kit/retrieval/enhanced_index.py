"""
增强索引模块

提供语义分块、HNSW 索引、增量更新和索引压缩功能。
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ChunkStrategy(Enum):
    """分块策略"""
    FIXED_SIZE = "fixed_size"       # 固定大小分块
    SEMANTIC = "semantic"           # 语义分块
    PARAGRAPH = "paragraph"         # 段落分块
    SENTENCE = "sentence"           # 句子分块
    HYBRID = "hybrid"               # 混合分块


class IndexType(Enum):
    """索引类型"""
    FLAT = "flat"                   # 平铺索引
    HNSW = "hnsw"                   # HNSW 索引
    IVF = "ivf"                     # IVF 索引
    PQ = "pq"                       # 乘积量化


@dataclass
class ChunkConfig:
    """分块配置"""
    strategy: ChunkStrategy = ChunkStrategy.SEMANTIC
    chunk_size: int = 512           # 分块大小（字符数）
    chunk_overlap: int = 50         # 分块重叠
    min_chunk_size: int = 100       # 最小分块大小
    max_chunk_size: int = 1024      # 最大分块大小
    respect_boundaries: bool = True # 是否尊重语义边界


@dataclass
class HNSWConfig:
    """HNSW 索引配置"""
    m: int = 16                     # 每层最大连接数
    ef_construction: int = 200      # 构建时的 ef 参数
    ef_search: int = 50             # 搜索时的 ef 参数
    ml: float = 1.0 / math.log(2)   # 层级因子
    max_elements: int = 100000      # 最大元素数
    dimension: int = 1024           # 向量维度


@dataclass
class DocumentChunk:
    """文档分块"""
    id: str
    content: str
    document_id: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    parent_chunk_id: str | None = None
    child_chunk_ids: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "parent_chunk_id": self.parent_chunk_id,
            "child_chunk_ids": self.child_chunk_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class IndexEntry:
    """索引条目"""
    id: str
    chunk_id: str
    vector: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)
    level: int = 0                  # HNSW 层级
    neighbors: dict[int, list[str]] = field(default_factory=dict)  # 层级 -> 邻居 ID
    deleted: bool = False

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "chunk_id": self.chunk_id,
            "vector": self.vector[:10] if self.vector else [],  # 只保存前 10 个元素用于调试
            "metadata": self.metadata,
            "level": self.level,
            "neighbors": {k: v for k, v in self.neighbors.items()},
            "deleted": self.deleted,
        }


@dataclass
class IndexStats:
    """索引统计"""
    total_chunks: int = 0
    total_documents: int = 0
    total_vectors: int = 0
    index_size_bytes: int = 0
    avg_chunk_size: float = 0.0
    last_updated: float = field(default_factory=time.time)
    index_type: str = "hnsw"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_chunks": self.total_chunks,
            "total_documents": self.total_documents,
            "total_vectors": self.total_vectors,
            "index_size_bytes": self.index_size_bytes,
            "avg_chunk_size": self.avg_chunk_size,
            "last_updated": self.last_updated,
            "index_type": self.index_type,
        }


class SemanticChunker:
    """语义分块器

    按语义边界分割文档，保持语义完整性。

    使用示例:
        chunker = SemanticChunker(ChunkConfig())
        chunks = chunker.chunk("长文档内容...", doc_id="doc1")
    """

    def __init__(self, config: ChunkConfig | None = None) -> None:
        """初始化分块器"""
        self.config = config or ChunkConfig()
        self._boundary_patterns = [
            "\n\n",      # 段落边界
            "\n",        # 行边界
            "。",        # 中文句号
            "！",        # 中文感叹号
            "？",        # 中文问号
            ".",         # 英文句号
            "!",         # 英文感叹号
            "?",         # 英文问号
            "；",        # 中文分号
            ";",         # 英文分号
        ]

    def chunk(
        self,
        content: str,
        doc_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """分块文档"""
        if self.config.strategy == ChunkStrategy.SEMANTIC:
            return self._semantic_chunk(content, doc_id, metadata)
        elif self.config.strategy == ChunkStrategy.PARAGRAPH:
            return self._paragraph_chunk(content, doc_id, metadata)
        elif self.config.strategy == ChunkStrategy.SENTENCE:
            return self._sentence_chunk(content, doc_id, metadata)
        else:
            return self._fixed_size_chunk(content, doc_id, metadata)

    def _semantic_chunk(
        self,
        content: str,
        doc_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """语义分块"""
        chunks: list[DocumentChunk] = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0

        # 按段落分割
        paragraphs = self._split_paragraphs(content)

        for para in paragraphs:
            # 检查添加段落后是否超过最大大小
            if len(current_chunk) + len(para) > self.config.max_chunk_size:
                if current_chunk:
                    # 保存当前分块
                    chunk = self._create_chunk(
                        content=current_chunk,
                        doc_id=doc_id,
                        chunk_index=chunk_index,
                        start_char=current_start,
                        end_char=current_start + len(current_chunk),
                        metadata=metadata,
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                    # 处理重叠
                    overlap_text = current_chunk[-self.config.chunk_overlap:] if len(current_chunk) > self.config.chunk_overlap else current_chunk
                    current_chunk = overlap_text
                    current_start = current_start + len(current_chunk) - len(overlap_text)

            current_chunk += para

            # 检查是否达到理想大小且有语义边界
            if len(current_chunk) >= self.config.chunk_size:
                if self._has_semantic_boundary(current_chunk):
                    chunk = self._create_chunk(
                        content=current_chunk.strip(),
                        doc_id=doc_id,
                        chunk_index=chunk_index,
                        start_char=current_start,
                        end_char=current_start + len(current_chunk),
                        metadata=metadata,
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    current_chunk = ""
                    current_start += len(current_chunk)

        # 处理最后一个分块
        if current_chunk.strip():
            chunk = self._create_chunk(
                content=current_chunk.strip(),
                doc_id=doc_id,
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=len(content),
                metadata=metadata,
            )
            chunks.append(chunk)

        return chunks

    def _paragraph_chunk(
        self,
        content: str,
        doc_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """段落分块"""
        chunks: list[DocumentChunk] = []
        paragraphs = self._split_paragraphs(content)
        current_chunk = ""
        current_start = 0
        chunk_index = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) > self.config.max_chunk_size and current_chunk:
                chunk = self._create_chunk(
                    content=current_chunk.strip(),
                    doc_id=doc_id,
                    chunk_index=chunk_index,
                    start_char=current_start,
                    end_char=current_start + len(current_chunk),
                    metadata=metadata,
                )
                chunks.append(chunk)
                chunk_index += 1
                current_chunk = ""
                current_start += len(current_chunk)

            current_chunk += para

        if current_chunk.strip():
            chunk = self._create_chunk(
                content=current_chunk.strip(),
                doc_id=doc_id,
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=len(content),
                metadata=metadata,
            )
            chunks.append(chunk)

        return chunks

    def _sentence_chunk(
        self,
        content: str,
        doc_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """句子分块"""
        sentences = self._split_sentences(content)
        chunks: list[DocumentChunk] = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0

        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.config.chunk_size and current_chunk:
                chunk = self._create_chunk(
                    content=current_chunk.strip(),
                    doc_id=doc_id,
                    chunk_index=chunk_index,
                    start_char=current_start,
                    end_char=current_start + len(current_chunk),
                    metadata=metadata,
                )
                chunks.append(chunk)
                chunk_index += 1
                current_chunk = ""
                current_start += len(current_chunk)

            current_chunk += sentence

        if current_chunk.strip():
            chunk = self._create_chunk(
                content=current_chunk.strip(),
                doc_id=doc_id,
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=len(content),
                metadata=metadata,
            )
            chunks.append(chunk)

        return chunks

    def _fixed_size_chunk(
        self,
        content: str,
        doc_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """固定大小分块"""
        chunks: list[DocumentChunk] = []
        chunk_index = 0
        start = 0

        while start < len(content):
            end = min(start + self.config.chunk_size, len(content))
            chunk_content = content[start:end]

            # 确保最小大小
            if len(chunk_content) >= self.config.min_chunk_size or start + self.config.chunk_size >= len(content):
                chunk = self._create_chunk(
                    content=chunk_content,
                    doc_id=doc_id,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                    metadata=metadata,
                )
                chunks.append(chunk)
                chunk_index += 1

            start += self.config.chunk_size - self.config.chunk_overlap

        return chunks

    def _split_paragraphs(self, content: str) -> list[str]:
        """分割段落"""
        paragraphs = content.split("\n\n")
        result = []
        for para in paragraphs:
            para = para.strip()
            if para:
                result.append(para + "\n\n")
        return result

    def _split_sentences(self, content: str) -> list[str]:
        """分割句子"""
        import re
        # 匹配中英文句子边界
        pattern = r'(?<=[。！？.!?])\s*'
        sentences = re.split(pattern, content)
        return [s.strip() for s in sentences if s.strip()]

    def _has_semantic_boundary(self, text: str) -> bool:
        """检查是否有语义边界"""
        for pattern in self._boundary_patterns:
            if text.rstrip().endswith(pattern):
                return True
        return False

    def _create_chunk(
        self,
        content: str,
        doc_id: str,
        chunk_index: int,
        start_char: int,
        end_char: int,
        metadata: dict[str, Any] | None = None,
    ) -> DocumentChunk:
        """创建分块"""
        chunk_id = self._generate_chunk_id(doc_id, chunk_index, content)
        return DocumentChunk(
            id=chunk_id,
            content=content,
            document_id=doc_id,
            chunk_index=chunk_index,
            start_char=start_char,
            end_char=end_char,
            metadata=metadata or {},
        )

    def _generate_chunk_id(self, doc_id: str, chunk_index: int, content: str) -> str:
        """生成分块 ID"""
        hash_input = f"{doc_id}:{chunk_index}:{content[:50]}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]


class HNSWIndex:
    """HNSW 索引

    实现层次化可导航小世界图索引。

    使用示例:
        index = HNSWIndex(HNSWConfig())
        index.add_vector("vec1", [0.1, 0.2, ...], {"doc_id": "doc1"})
        results = index.search([0.1, 0.2, ...], k=10)
    """

    def __init__(self, config: HNSWConfig | None = None) -> None:
        """初始化 HNSW 索引"""
        self.config = config or HNSWConfig()
        self._entries: dict[str, IndexEntry] = {}
        self._level_entries: dict[int, list[str]] = defaultdict(list)  # 层级 -> 条目 ID
        self._entry_point: str | None = None
        self._max_level: int = 0
        self._lock = threading.RLock()

    def add_vector(
        self,
        id: str,
        vector: list[float],
        metadata: dict[str, Any] | None = None,
        chunk_id: str | None = None,
    ) -> IndexEntry:
        """添加向量"""
        with self._lock:
            # 确定向量层级
            level = self._random_level()

            entry = IndexEntry(
                id=id,
                chunk_id=chunk_id or id,
                vector=vector,
                metadata=metadata or {},
                level=level,
            )

            self._entries[id] = entry
            self._level_entries[level].append(id)

            # 更新入口点
            if self._entry_point is None or level > self._max_level:
                self._entry_point = id
                self._max_level = level

            # 连接邻居
            self._connect_neighbors(entry)

            return entry

    def search(
        self,
        query: list[float],
        k: int = 10,
        ef: int | None = None,
    ) -> list[tuple[str, float]]:
        """搜索最近邻"""
        with self._lock:
            if not self._entry_point:
                return []

            ef = ef or self.config.ef_search

            # 从最高层开始搜索
            current_id = self._entry_point

            # 从最高层向下搜索
            for level in range(self._max_level, 0, -1):
                layer_results = self._search_layer(query, current_id, 1, level)
                if layer_results:
                    current_id = layer_results[0]

            # 在底层进行详细搜索
            candidates = self._search_layer(query, current_id, ef, 0)

            # 计算距离并排序
            results: list[tuple[str, float]] = []
            for cid in candidates:
                entry = self._entries.get(cid)
                if entry and not entry.deleted:
                    dist = self._cosine_distance(query, entry.vector)
                    results.append((cid, dist))

            results.sort(key=lambda x: x[1])
            return results[:k]

    def remove_vector(self, id: str) -> bool:
        """删除向量（标记删除）"""
        with self._lock:
            entry = self._entries.get(id)
            if entry:
                entry.deleted = True
                return True
            return False

    def update_vector(
        self,
        id: str,
        vector: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> IndexEntry | None:
        """更新向量"""
        with self._lock:
            entry = self._entries.get(id)
            if not entry:
                return None

            # 标记旧条目删除
            entry.deleted = True

            # 添加新条目
            return self.add_vector(id, vector, metadata, entry.chunk_id)

    def get_vector(self, id: str) -> list[float] | None:
        """获取向量"""
        entry = self._entries.get(id)
        return entry.vector if entry and not entry.deleted else None

    def get_stats(self) -> dict[str, Any]:
        """获取索引统计"""
        with self._lock:
            total = len(self._entries)
            active = sum(1 for e in self._entries.values() if not e.deleted)

            return {
                "total_entries": total,
                "active_entries": active,
                "max_level": self._max_level,
                "level_distribution": {
                    level: len(ids) for level, ids in self._level_entries.items()
                },
                "dimension": self.config.dimension,
            }

    def _random_level(self) -> int:
        """生成随机层级"""
        import random
        r = random.random()
        level = 0
        while r < 1.0 / self.config.ml and level < self.config.m:
            level += 1
            r = random.random()
        return level

    def _connect_neighbors(self, entry: IndexEntry) -> None:
        """连接邻居节点"""
        if entry.level == 0:
            return

        # 简化实现：使用向量相似度选择邻居
        candidates: list[tuple[str, float]] = []

        for other_id, other in self._entries.items():
            if other_id == entry.id or other.deleted:
                continue

            if other.level >= entry.level:
                dist = self._cosine_distance(entry.vector, other.vector)
                candidates.append((other_id, dist))

        # 选择最近的 M 个邻居
        candidates.sort(key=lambda x: x[1])
        neighbors = [c[0] for c in candidates[:self.config.m]]

        entry.neighbors[entry.level] = neighbors

        # 更新邻居的双向连接
        for neighbor_id in neighbors:
            neighbor = self._entries.get(neighbor_id)
            if neighbor:
                if entry.level not in neighbor.neighbors:
                    neighbor.neighbors[entry.level] = []
                if entry.id not in neighbor.neighbors[entry.level]:
                    neighbor.neighbors[entry.level].append(entry.id)

    def _search_layer(
        self,
        query: list[float],
        entry_point: str,
        ef: int,
        level: int,
    ) -> list[str]:
        """在指定层级搜索"""
        visited: set[str] = {entry_point}
        candidates: list[tuple[str, float]] = []

        entry = self._entries.get(entry_point)
        if not entry or entry.deleted:
            return []

        dist = self._cosine_distance(query, entry.vector)
        candidates = [(entry_point, dist)]

        while candidates:
            current_id, _ = candidates.pop(0)
            current = self._entries.get(current_id)
            if not current:
                continue

            neighbors = current.neighbors.get(level, [])
            for neighbor_id in neighbors:
                if neighbor_id in visited:
                    continue
                visited.add(neighbor_id)

                neighbor = self._entries.get(neighbor_id)
                if not neighbor or neighbor.deleted:
                    continue

                dist = self._cosine_distance(query, neighbor.vector)
                candidates.append((neighbor_id, dist))

            candidates.sort(key=lambda x: x[1])
            candidates = candidates[:ef]

        return [c[0] for c in candidates]

    def _cosine_distance(self, v1: list[float], v2: list[float]) -> float:
        """计算余弦距离"""
        if len(v1) != len(v2):
            return 1.0

        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))

        if norm1 == 0 or norm2 == 0:
            return 1.0

        similarity = dot / (norm1 * norm2)
        return 1.0 - similarity


class IncrementalIndexer:
    """增量索引器

    支持增量更新索引。

    使用示例:
        indexer = IncrementalIndexer()
        indexer.add_document("doc1", "内容...", embeddings)
        indexer.update_document("doc1", "新内容...", new_embeddings)
        indexer.remove_document("doc1")
    """

    def __init__(
        self,
        chunker: SemanticChunker | None = None,
        index: HNSWIndex | None = None,
    ) -> None:
        """初始化增量索引器"""
        self._chunker = chunker or SemanticChunker()
        self._index = index or HNSWIndex()
        self._documents: dict[str, list[str]] = {}  # doc_id -> chunk_ids
        self._chunks: dict[str, DocumentChunk] = {}
        self._document_hashes: dict[str, str] = {}
        self._lock = threading.RLock()

    def add_document(
        self,
        doc_id: str,
        content: str,
        embeddings: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """添加文档"""
        with self._lock:
            # 分块
            chunks = self._chunker.chunk(content, doc_id, metadata)

            # 为每个分块添加向量
            chunk_ids: list[str] = []
            for i, chunk in enumerate(chunks):
                chunk_id = chunk.id

                # 如果提供了嵌入向量，使用它；否则创建占位符
                if embeddings:
                    # 将单个嵌入向量分配给所有分块（简化处理）
                    chunk.embedding = embeddings
                else:
                    # 创建零向量占位符（实际使用时应该调用嵌入模型）
                    chunk.embedding = [0.0] * 1024

                # 添加到索引
                self._index.add_vector(
                    id=chunk_id,
                    vector=chunk.embedding,
                    metadata={"doc_id": doc_id, "chunk_index": i},
                    chunk_id=chunk_id,
                )

                self._chunks[chunk_id] = chunk
                chunk_ids.append(chunk_id)

            self._documents[doc_id] = chunk_ids
            self._document_hashes[doc_id] = self._compute_hash(content)

            return chunks

    def update_document(
        self,
        doc_id: str,
        content: str,
        embeddings: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """更新文档"""
        with self._lock:
            # 检查内容是否变化
            new_hash = self._compute_hash(content)
            if self._document_hashes.get(doc_id) == new_hash:
                # 内容未变化，返回现有分块
                chunk_ids = self._documents.get(doc_id, [])
                return [self._chunks[cid] for cid in chunk_ids if cid in self._chunks]

            # 移除旧分块
            self._remove_document_chunks(doc_id)

            # 添加新分块
            return self.add_document(doc_id, content, embeddings, metadata)

    def remove_document(self, doc_id: str) -> bool:
        """删除文档"""
        with self._lock:
            return self._remove_document_chunks(doc_id)

    def _remove_document_chunks(self, doc_id: str) -> bool:
        """删除文档的所有分块"""
        chunk_ids = self._documents.get(doc_id, [])
        if not chunk_ids:
            return False

        for chunk_id in chunk_ids:
            self._index.remove_vector(chunk_id)
            if chunk_id in self._chunks:
                del self._chunks[chunk_id]

        del self._documents[doc_id]
        if doc_id in self._document_hashes:
            del self._document_hashes[doc_id]

        return True

    def get_document_chunks(self, doc_id: str) -> list[DocumentChunk]:
        """获取文档的分块"""
        chunk_ids = self._documents.get(doc_id, [])
        return [self._chunks[cid] for cid in chunk_ids if cid in self._chunks]

    def search(
        self,
        query_vector: list[float],
        k: int = 10,
    ) -> list[tuple[DocumentChunk, float]]:
        """搜索"""
        results = self._index.search(query_vector, k=k)
        chunks_with_score: list[tuple[DocumentChunk, float]] = []

        for chunk_id, distance in results:
            chunk = self._chunks.get(chunk_id)
            if chunk:
                chunks_with_score.append((chunk, distance))

        return chunks_with_score

    def get_stats(self) -> IndexStats:
        """获取索引统计"""
        total_chunks = len(self._chunks)
        total_vectors = len([c for c in self._chunks.values() if c.embedding])

        return IndexStats(
            total_chunks=total_chunks,
            total_documents=len(self._documents),
            total_vectors=total_vectors,
            index_size_bytes=sum(len(c.content.encode()) for c in self._chunks.values()),
            avg_chunk_size=sum(len(c.content) for c in self._chunks.values()) / max(total_chunks, 1),
        )

    def _compute_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.encode()).hexdigest()

    def save(self, path: str) -> None:
        """保存索引"""
        data = {
            "documents": self._documents,
            "chunks": {cid: c.to_dict() for cid, c in self._chunks.items()},
            "document_hashes": self._document_hashes,
            "stats": self.get_stats().to_dict(),
        }

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path: str) -> None:
        """加载索引"""
        if not Path(path).exists():
            return

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        self._documents = data.get("documents", {})
        self._document_hashes = data.get("document_hashes", {})

        for chunk_id, chunk_data in data.get("chunks", {}).items():
            self._chunks[chunk_id] = DocumentChunk(
                id=chunk_data["id"],
                content=chunk_data["content"],
                document_id=chunk_data["document_id"],
                chunk_index=chunk_data["chunk_index"],
                start_char=chunk_data["start_char"],
                end_char=chunk_data["end_char"],
                metadata=chunk_data.get("metadata", {}),
                embedding=chunk_data.get("embedding"),
            )

            # 重建索引
            if self._chunks[chunk_id].embedding:
                self._index.add_vector(
                    id=chunk_id,
                    vector=self._chunks[chunk_id].embedding,
                    metadata={"doc_id": chunk_data["document_id"]},
                )


class IndexCompressor:
    """索引压缩器

    压缩索引以减少内存占用。
    """

    def __init__(
        self,
        compression_ratio: float = 0.5,
        use_quantization: bool = True,
    ) -> None:
        """初始化压缩器"""
        self._compression_ratio = compression_ratio
        self._use_quantization = use_quantization

    def compress_vectors(
        self,
        vectors: dict[str, list[float]],
    ) -> dict[str, list[int]]:
        """压缩向量（量化）"""
        compressed: dict[str, list[int]] = {}

        for vid, vector in vectors.items():
            if self._use_quantization:
                # 简单的 8-bit 量化
                min_val = min(vector)
                max_val = max(vector)
                scale = 255.0 / (max_val - min_val) if max_val != min_val else 1.0

                compressed[vid] = [
                    int((v - min_val) * scale) for v in vector
                ]
            else:
                compressed[vid] = [int(v * 1000) for v in vector]

        return compressed

    def decompress_vectors(
        self,
        compressed: dict[str, list[int]],
        original_stats: dict[str, tuple[float, float]],
    ) -> dict[str, list[float]]:
        """解压向量"""
        vectors: dict[str, list[float]] = {}

        for vid, quantized in compressed.items():
            min_val, max_val = original_stats.get(vid, (0.0, 1.0))
            scale = (max_val - min_val) / 255.0 if max_val != min_val else 1.0

            vectors[vid] = [v * scale + min_val for v in quantized]

        return vectors

    def compress_index(
        self,
        indexer: IncrementalIndexer,
    ) -> dict[str, Any]:
        """压缩整个索引"""
        vectors: dict[str, list[float]] = {}
        original_stats: dict[str, tuple[float, float]] = {}

        for chunk_id, chunk in indexer._chunks.items():
            if chunk.embedding:
                vectors[chunk_id] = chunk.embedding
                original_stats[chunk_id] = (min(chunk.embedding), max(chunk.embedding))

        compressed_vectors = self.compress_vectors(vectors)

        return {
            "compressed_vectors": compressed_vectors,
            "original_stats": original_stats,
            "compression_ratio": self._compression_ratio,
        }


# 全局实例
_chunker: SemanticChunker | None = None
_index: HNSWIndex | None = None
_indexer: IncrementalIndexer | None = None


def get_semantic_chunker() -> SemanticChunker:
    """获取全局语义分块器"""
    global _chunker
    if _chunker is None:
        _chunker = SemanticChunker()
    return _chunker


def get_hnsw_index() -> HNSWIndex:
    """获取全局 HNSW 索引"""
    global _index
    if _index is None:
        _index = HNSWIndex()
    return _index


def get_incremental_indexer() -> IncrementalIndexer:
    """获取全局增量索引器"""
    global _indexer
    if _indexer is None:
        _indexer = IncrementalIndexer()
    return _indexer