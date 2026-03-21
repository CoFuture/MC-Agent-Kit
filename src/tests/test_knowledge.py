"""
知识库模块测试
"""

import os
import sys

import pytest

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mc_agent_kit.knowledge.base import Document, DocumentChunk, DocumentType, SearchResult


class TestDocumentType:
    """测试文档类型枚举"""

    def test_document_types(self):
        """测试文档类型值"""
        assert DocumentType.API.value == "api"
        assert DocumentType.EVENT.value == "event"
        assert DocumentType.ENUM.value == "enum"
        assert DocumentType.GUIDE.value == "guide"
        assert DocumentType.TUTORIAL.value == "tutorial"
        assert DocumentType.DEMO.value == "demo"


class TestDocument:
    """测试 Document 类"""

    def test_document_creation(self):
        """测试文档创建"""
        doc = Document(
            path="/test/api/GetEngineType.md",
            content="# GetEngineType\n\n这是测试内容",
        )

        assert doc.path == "/test/api/GetEngineType.md"
        assert "GetEngineType" in doc.content
        assert doc.doc_type == DocumentType.UNKNOWN  # 默认值

    def test_document_type_inference_api(self):
        """测试 API 文档类型推断"""
        doc = Document(
            path="E:/docs/mcdocs/1-ModAPI/接口/实体/GetEngineType.md",
            content="# GetEngineType",
        )

        assert doc.doc_type == DocumentType.API

    def test_document_type_inference_event(self):
        """测试事件文档类型推断"""
        doc = Document(
            path="E:/docs/mcdocs/1-ModAPI/事件/UI.md",
            content="# UI 事件",
        )

        assert doc.doc_type == DocumentType.EVENT

    def test_document_type_inference_guide(self):
        """测试指南文档类型推断"""
        doc = Document(
            path="E:/docs/mcguide/16-渲染/readme.md",
            content="# 渲染指南",
        )

        assert doc.doc_type == DocumentType.GUIDE

    def test_document_type_inference_demo(self):
        """测试 Demo 文档类型推断"""
        doc = Document(
            path="E:/docs/6-1DemoMod/自定义物品/example.py",
            content="# Demo",
        )

        assert doc.doc_type == DocumentType.DEMO


class TestDocumentChunk:
    """测试 DocumentChunk 类"""

    def test_chunk_creation(self):
        """测试文档块创建"""
        chunk = DocumentChunk(
            id="abc123",
            content="这是测试内容",
            source="/test/api.md",
            doc_type=DocumentType.API,
            category="实体",
            name="GetEngineType",
        )

        assert chunk.id == "abc123"
        assert chunk.content == "这是测试内容"
        assert chunk.doc_type == DocumentType.API
        assert chunk.category == "实体"
        assert chunk.name == "GetEngineType"

    def test_chunk_to_dict(self):
        """测试文档块转换为字典"""
        chunk = DocumentChunk(
            id="test123",
            content="内容",
            source="/test.md",
            doc_type=DocumentType.API,
        )

        d = chunk.to_dict()

        assert d["id"] == "test123"
        assert d["content"] == "内容"
        assert d["doc_type"] == "api"

    def test_chunk_from_dict(self):
        """测试从字典创建文档块"""
        d = {
            "id": "xyz789",
            "content": "测试内容",
            "source": "/test.md",
            "doc_type": "guide",
            "category": "教程",
            "name": "测试",
            "chunk_index": 0,
            "total_chunks": 1,
        }

        chunk = DocumentChunk.from_dict(d)

        assert chunk.id == "xyz789"
        assert chunk.doc_type == DocumentType.GUIDE
        assert chunk.category == "教程"


class TestSearchResult:
    """测试 SearchResult 类"""

    def test_search_result_creation(self):
        """测试搜索结果创建"""
        result = SearchResult(
            content="结果内容",
            source="/test.md",
            doc_type=DocumentType.API,
            score=0.95,
            category="实体",
            name="GetEngineType",
        )

        assert result.score == 0.95
        assert result.doc_type == DocumentType.API

    def test_search_result_to_dict(self):
        """测试搜索结果转换为字典"""
        result = SearchResult(
            content="内容",
            source="/test.md",
            doc_type=DocumentType.EVENT,
            score=0.8,
        )

        d = result.to_dict()

        assert d["score"] == 0.8
        assert d["doc_type"] == "event"


# 以下测试需要 ChromaDB，标记为可选
@pytest.mark.skip(reason="需要安装 chromadb 和构建索引")
class TestKnowledgeBase:
    """测试 KnowledgeBase 类"""

    def test_knowledge_base_init(self):
        """测试知识库初始化"""
        from mc_agent_kit.knowledge import KnowledgeBase

        kb = KnowledgeBase(
            docs_path="/tmp/docs",
            persist_dir="/tmp/kb",
        )

        assert kb.docs_path == "/tmp/docs"
        assert kb.persist_dir == "/tmp/kb"

    def test_search(self):
        """测试搜索功能"""
        # 需要 ChromaDB 和预先构建的索引
        pass
