"""
知识库基础数据类型定义
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DocumentType(Enum):
    """文档类型枚举"""
    API = "api"          # API 接口文档
    EVENT = "event"      # 事件文档
    ENUM = "enum"        # 枚举值文档
    GUIDE = "guide"      # 开发指南
    TUTORIAL = "tutorial"  # 教程
    DEMO = "demo"        # 示例代码
    UNKNOWN = "unknown"


@dataclass
class Document:
    """原始文档"""
    path: str                           # 文件路径
    content: str                        # 文档内容
    doc_type: DocumentType = DocumentType.UNKNOWN
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """根据路径推断文档类型"""
        if self.doc_type == DocumentType.UNKNOWN:
            self.doc_type = self._infer_type()

    def _infer_type(self) -> DocumentType:
        """根据路径推断文档类型"""
        path_lower = self.path.lower().replace("\\", "/")

        if "1-modapi" in path_lower:
            if "/事件/" in path_lower or "event" in path_lower:
                return DocumentType.EVENT
            elif "/枚举值/" in path_lower or "enum" in path_lower:
                return DocumentType.ENUM
            return DocumentType.API
        elif "2-apollo" in path_lower:
            return DocumentType.API
        elif "3-presetapi" in path_lower:
            return DocumentType.API
        elif "mcguide" in path_lower:
            return DocumentType.GUIDE
        elif "mconline" in path_lower:
            return DocumentType.TUTORIAL
        elif "6-1demomod" in path_lower or "demo" in path_lower:
            return DocumentType.DEMO

        return DocumentType.UNKNOWN


@dataclass
class DocumentChunk:
    """文档分块"""
    id: str                             # 块 ID
    content: str                        # 块内容
    source: str                         # 来源文档路径
    doc_type: DocumentType              # 文档类型
    category: str | None = None      # 分类（如：实体、方块、物品）
    name: str | None = None          # 名称（如：API 名称）
    chunk_index: int = 0                # 分块索引
    total_chunks: int = 1               # 总块数
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "doc_type": self.doc_type.value,
            "category": self.category,
            "name": self.name,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentChunk":
        """从字典创建"""
        return cls(
            id=data["id"],
            content=data["content"],
            source=data["source"],
            doc_type=DocumentType(data["doc_type"]),
            category=data.get("category"),
            name=data.get("name"),
            chunk_index=data.get("chunk_index", 0),
            total_chunks=data.get("total_chunks", 1),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SearchResult:
    """搜索结果"""
    content: str                        # 内容
    source: str                         # 来源
    doc_type: DocumentType              # 文档类型
    score: float                        # 相关度分数
    category: str | None = None      # 分类
    name: str | None = None          # 名称
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "source": self.source,
            "doc_type": self.doc_type.value,
            "score": self.score,
            "category": self.category,
            "name": self.name,
            "metadata": self.metadata,
        }
