"""
MC-Agent-Kit 知识库模块

为 AI Agent 提供 MC ModSDK 开发知识的检索能力。
"""

from typing import Any

from .base import Document, DocumentChunk, DocumentType, SearchResult
from .examples_enhanced import (
    CodeExampleEnhanced,
    CodeExampleManager,
    DifficultyLevel,
    ExampleCategory,
    ExampleManagerConfig,
    create_example_manager,
)
from .examples_enhanced import (
    SearchResult as ExampleSearchResult,
)
from .incremental import ChangeReport, DocumentChange, IncrementalUpdater

# Iteration #34: 缓存模块
from .index_cache import (
    CacheMetadata,
    FileState,
    IndexCacheStats,
    KnowledgeIndexCache,
    create_index_cache,
)
from .knowledge_base import KnowledgeBase
from .retrieval import CodeExampleSearchResult, KnowledgeRetrieval, create_retrieval
from .retrieval import SearchResult as RetrievalSearchResult
from .search_cache import (
    SearchCacheEntry,
    SearchCacheStats,
    SearchResultCache,
    create_search_cache,
)

# Iteration #71: 统一索引模块
from .unified_index import (
    CodeBlock,
    EntryScope,
    EntryType,
    IndexStats,
    Parameter,
    RelatedAPI,
    UnifiedEntry,
)

# Iteration #71: 示例代码库
from .example_library import (
    ExampleCode,
    ExampleLibrary,
    ExampleMetadata,
    get_example,
    get_example_library,
    list_examples,
    search_examples,
)

# Iteration #71: 增强检索
from .enhanced_retriever import (
    EnhancedKnowledgeRetriever,
    SearchFilter,
    SearchReport,
    SearchResult as EnhancedSearchResult,
    get_api_info,
    get_event_info,
    get_retriever,
    search_knowledge,
)

__all__ = [
    "KnowledgeBase",
    "Document",
    "DocumentChunk",
    "DocumentType",
    "SearchResult",
    "IncrementalUpdater",
    "DocumentChange",
    "ChangeReport",
    # Retrieval
    "KnowledgeRetrieval",
    "RetrievalSearchResult",
    "CodeExampleSearchResult",
    "create_retrieval",
    # Iteration #34: Index Cache
    "KnowledgeIndexCache",
    "CacheMetadata",
    "FileState",
    "IndexCacheStats",
    "create_index_cache",
    # Iteration #34: Search Cache
    "SearchResultCache",
    "SearchCacheEntry",
    "SearchCacheStats",
    "create_search_cache",
    # Iteration #35: Enhanced Examples
    "CodeExampleEnhanced",
    "CodeExampleManager",
    "DifficultyLevel",
    "ExampleCategory",
    "ExampleManagerConfig",
    "ExampleSearchResult",
    "create_example_manager",
    # Iteration #71: 统一索引
    "CodeBlock",
    "EntryScope",
    "EntryType",
    "IndexStats",
    "Parameter",
    "RelatedAPI",
    "UnifiedEntry",
    # Iteration #71: 示例代码库
    "ExampleCode",
    "ExampleLibrary",
    "ExampleMetadata",
    "get_example",
    "get_example_library",
    "list_examples",
    "search_examples",
    # Iteration #71: 增强检索
    "EnhancedKnowledgeRetriever",
    "SearchFilter",
    "SearchReport",
    "EnhancedSearchResult",
    "get_api_info",
    "get_event_info",
    "get_retriever",
    "search_knowledge",
]


def create_knowledge_tool(kb: KnowledgeBase) -> Any:
    """
    创建 Agent 可调用的知识库工具函数

    Args:
        kb: KnowledgeBase 实例

    Returns:
        可供 Agent 调用的工具函数
    """
    def mc_knowledge_search(
        query: str,
        doc_type: str = "all",
        top_k: int = 5
    ) -> str:
        """
        搜索 MC ModSDK 知识库

        Args:
            query: 搜索关键词或问题
            doc_type: 文档类型 (api/guide/demo/all)
            top_k: 返回结果数量

        Returns:
            搜索结果文本
        """
        results = kb.search(query, doc_type=doc_type, top_k=top_k)

        if not results:
            return "未找到相关内容"

        output = []
        for i, r in enumerate(results, 1):
            output.append(f"## 结果 {i}")
            output.append(f"来源: {r.source}")
            output.append(f"类型: {r.doc_type}")
            output.append(f"相关度: {r.score:.2f}")
            output.append(f"内容:\n{r.content[:500]}...")
            output.append("")

        return "\n".join(output)

    return mc_knowledge_search
