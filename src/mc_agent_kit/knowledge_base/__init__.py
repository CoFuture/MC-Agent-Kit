"""
MC-Agent-Kit 知识库模块

提供 ModSDK 文档解析、索引构建和检索功能。
"""

from .indexer import KnowledgeIndexer
from .models import (
    APIEntry,
    APIParameter,
    ApiUsageStats,
    ApiUsageTracker,
    ApiVersionTag,
    CodeExample,
    DifficultyLevel,
    EnhancedCodeExample,
    EnumEntry,
    EnumValue,
    EventEntry,
    EventParameter,
    ExampleCategory,
    KnowledgeBase,
    Scope,
)
from .parser import DocumentParser, MarkdownParser
from .retriever import KnowledgeRetriever, create_retriever

__all__ = [
    # Models
    "APIEntry",
    "APIParameter",
    "EventEntry",
    "EventParameter",
    "EnumEntry",
    "EnumValue",
    "CodeExample",
    "KnowledgeBase",
    "Scope",
    # Iteration #31
    "ApiVersionTag",
    # Iteration #32
    "DifficultyLevel",
    "ExampleCategory",
    "EnhancedCodeExample",
    "ApiUsageStats",
    "ApiUsageTracker",
    # Parser
    "MarkdownParser",
    "DocumentParser",
    # Indexer
    "KnowledgeIndexer",
    # Retriever
    "KnowledgeRetriever",
    "create_retriever",
]
