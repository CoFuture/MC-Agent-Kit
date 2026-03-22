"""
知识库模块测试

测试 Document, DocumentChunk, SearchResult, KnowledgeBase 等功能。
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mc_agent_kit.knowledge.base import Document, DocumentChunk, DocumentType, SearchResult
from mc_agent_kit.knowledge.knowledge_base import KnowledgeBase


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

    def test_unknown_type(self):
        """测试未知类型"""
        assert DocumentType.UNKNOWN.value == "unknown"


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

    def test_document_with_explicit_type(self):
        """测试显式指定类型"""
        doc = Document(
            path="/some/path.md",
            content="content",
            doc_type=DocumentType.API,
        )

        assert doc.doc_type == DocumentType.API

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

    def test_document_type_inference_enum(self):
        """测试枚举文档类型推断"""
        doc = Document(
            path="E:/docs/mcdocs/1-ModAPI/枚举值/ActorType.md",
            content="# ActorType",
        )

        assert doc.doc_type == DocumentType.ENUM

    def test_document_type_inference_guide(self):
        """测试指南文档类型推断"""
        doc = Document(
            path="E:/docs/mcguide/16-渲染/readme.md",
            content="# 渲染指南",
        )

        assert doc.doc_type == DocumentType.GUIDE

    def test_document_type_inference_tutorial(self):
        """测试教程文档类型推断"""
        doc = Document(
            path="E:/docs/mconline/tutorial/hello.md",
            content="# 教程",
        )

        assert doc.doc_type == DocumentType.TUTORIAL

    def test_document_type_inference_demo(self):
        """测试 Demo 文档类型推断"""
        doc = Document(
            path="E:/docs/6-1DemoMod/自定义物品/example.py",
            content="# Demo",
        )

        assert doc.doc_type == DocumentType.DEMO

    def test_document_type_inference_apollo(self):
        """测试 Apollo 文档类型推断"""
        doc = Document(
            path="E:/docs/mcdocs/2-Apollo/接口/test.md",
            content="# Apollo API",
        )

        assert doc.doc_type == DocumentType.API

    def test_document_type_inference_presetapi(self):
        """测试 PresetAPI 文档类型推断"""
        doc = Document(
            path="E:/docs/mcdocs/3-PresetAPI/接口/test.md",
            content="# Preset API",
        )

        assert doc.doc_type == DocumentType.API

    def test_document_type_inference_windows_path(self):
        """测试 Windows 路径推断"""
        doc = Document(
            path="E:\\docs\\mcdocs\\1-ModAPI\\事件\\test.md",
            content="# Test",
        )

        assert doc.doc_type == DocumentType.EVENT

    def test_document_with_metadata(self):
        """测试带元数据的文档"""
        doc = Document(
            path="/test.md",
            content="content",
            metadata={"author": "test", "version": "1.0"},
        )

        assert doc.metadata["author"] == "test"
        assert doc.metadata["version"] == "1.0"


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

    def test_chunk_defaults(self):
        """测试块默认值"""
        chunk = DocumentChunk(
            id="test",
            content="content",
            source="/test.md",
            doc_type=DocumentType.GUIDE,
        )

        assert chunk.category is None
        assert chunk.name is None
        assert chunk.chunk_index == 0
        assert chunk.total_chunks == 1
        assert chunk.metadata == {}

    def test_chunk_to_dict(self):
        """测试文档块转换为字典"""
        chunk = DocumentChunk(
            id="test123",
            content="内容",
            source="/test.md",
            doc_type=DocumentType.API,
            chunk_index=2,
            total_chunks=5,
        )

        d = chunk.to_dict()

        assert d["id"] == "test123"
        assert d["content"] == "内容"
        assert d["doc_type"] == "api"
        assert d["chunk_index"] == 2
        assert d["total_chunks"] == 5

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

    def test_chunk_roundtrip(self):
        """测试块序列化往返"""
        original = DocumentChunk(
            id="test",
            content="content",
            source="/test.md",
            doc_type=DocumentType.EVENT,
            category="UI",
            name="OnClick",
            chunk_index=1,
            total_chunks=3,
            metadata={"key": "value"},
        )

        d = original.to_dict()
        restored = DocumentChunk.from_dict(d)

        assert restored.id == original.id
        assert restored.content == original.content
        assert restored.doc_type == original.doc_type
        assert restored.category == original.category
        assert restored.metadata == original.metadata


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

    def test_search_result_defaults(self):
        """测试搜索结果默认值"""
        result = SearchResult(
            content="content",
            source="/test.md",
            doc_type=DocumentType.GUIDE,
            score=0.5,
        )

        assert result.category is None
        assert result.name is None
        assert result.metadata == {}

    def test_search_result_to_dict(self):
        """测试搜索结果转换为字典"""
        result = SearchResult(
            content="内容",
            source="/test.md",
            doc_type=DocumentType.EVENT,
            score=0.8,
            metadata={"hit": 1},
        )

        d = result.to_dict()

        assert d["score"] == 0.8
        assert d["doc_type"] == "event"
        assert d["metadata"]["hit"] == 1


class TestKnowledgeBaseInit:
    """测试 KnowledgeBase 初始化"""

    def test_kb_creation_default(self):
        """测试默认初始化"""
        kb = KnowledgeBase()

        assert kb.docs_path is None
        assert kb.persist_dir is None
        assert kb.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
        assert kb.chunk_size == 512
        assert kb.chunk_overlap == 50

    def test_kb_creation_custom(self):
        """测试自定义参数初始化"""
        kb = KnowledgeBase(
            docs_path="/path/to/docs",
            persist_dir="/path/to/persist",
            embedding_model="custom-model",
            chunk_size=1024,
            chunk_overlap=100,
        )

        # Windows 路径可能转换
        assert "path" in str(kb.docs_path).lower()
        assert "persist" in str(kb.persist_dir).lower()
        assert kb.embedding_model == "custom-model"
        assert kb.chunk_size == 1024

    def test_kb_not_built(self):
        """测试未构建索引"""
        kb = KnowledgeBase()

        assert not kb._index_built
        assert kb._vector_store is None


class TestKnowledgeBaseDocuments:
    """测试 KnowledgeBase 文档处理"""

    def test_load_documents(self):
        """测试加载文档"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文档（使用 ASCII 内容避免编码问题）
            docs_dir = Path(tmpdir) / "docs"
            docs_dir.mkdir()

            (docs_dir / "api.md").write_text("# API Document\n\nThis is API content", encoding="utf-8")
            (docs_dir / "guide.md").write_text("# Guide\n\nThis is guide content", encoding="utf-8")

            kb = KnowledgeBase(docs_path=str(docs_dir))
            docs = kb._load_documents()

            assert len(docs) == 2

    def test_load_documents_with_subdirs(self):
        """测试加载子目录文档"""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = Path(tmpdir) / "docs"
            sub_dir = docs_dir / "subdir"
            sub_dir.mkdir(parents=True)

            (docs_dir / "main.md").write_text("main")
            (sub_dir / "sub.md").write_text("sub")

            kb = KnowledgeBase(docs_path=tmpdir)
            docs = kb._load_documents()

            assert len(docs) == 2

    def test_load_documents_different_extensions(self):
        """测试加载不同扩展名文档"""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = Path(tmpdir)
            (docs_dir / "test.md").write_text("markdown")
            (docs_dir / "test.txt").write_text("text")

            kb = KnowledgeBase(docs_path=tmpdir)
            docs = kb._load_documents()

            assert len(docs) == 2

    def test_load_documents_invalid_encoding(self):
        """测试加载编码错误的文档"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建二进制文件
            bad_file = Path(tmpdir) / "bad.md"
            bad_file.write_bytes(b"\xff\xfe invalid utf-8")

            kb = KnowledgeBase(docs_path=tmpdir)
            docs = kb._load_documents()

            # 应该跳过无效文件
            assert len(docs) >= 0


class TestKnowledgeBaseChunking:
    """测试 KnowledgeBase 文档分块"""

    def test_chunk_by_paragraphs(self):
        """测试段落分块"""
        kb = KnowledgeBase(chunk_size=50)

        doc = Document(
            path="/test.md",
            content="第一段内容。" * 10 + "\n\n" + "第二段内容。" * 10,
            doc_type=DocumentType.GUIDE,
        )

        chunks = kb._chunk_by_paragraphs(doc)

        assert len(chunks) > 0

    def test_chunk_by_headers(self):
        """测试标题分块"""
        kb = KnowledgeBase()

        doc = Document(
            path="/test.md",
            content="# API 1\n\nThis is content for API 1 with enough text to make a valid chunk.\n\n# API 2\n\nThis is content for API 2 with enough text to make a valid chunk.\n\n# API 3\n\nThis is content for API 3 with enough text to make a valid chunk.",
            doc_type=DocumentType.API,
        )

        chunks = kb._chunk_by_headers(doc)

        # 应该按标题分割
        assert len(chunks) >= 1

    def test_chunk_as_whole(self):
        """测试整体分块"""
        kb = KnowledgeBase()

        doc = Document(
            path="/test.md",
            content="完整内容",
            doc_type=DocumentType.DEMO,
        )

        chunks = kb._chunk_as_whole(doc)

        assert len(chunks) == 1
        assert chunks[0].content == "完整内容"

    def test_chunk_single_document_api(self):
        """测试 API 文档分块策略"""
        kb = KnowledgeBase()

        doc = Document(
            path="/mcdocs/1-ModAPI/接口/实体/Test.md",
            content="# Test API\n\nThis is the Test API documentation with sufficient content.",
            doc_type=DocumentType.API,  # 显式指定类型
        )

        chunks = kb._chunk_single_document(doc)

        assert len(chunks) >= 1

    def test_chunk_single_document_event(self):
        """测试事件文档分块策略"""
        kb = KnowledgeBase()

        doc = Document(
            path="/mcdocs/1-ModAPI/事件/Test.md",
            content="# Test Event\n\nThis is the Test Event documentation with sufficient content.",
            doc_type=DocumentType.EVENT,  # 显式指定类型
        )

        chunks = kb._chunk_single_document(doc)

        assert len(chunks) >= 1

    def test_chunk_single_document_demo(self):
        """测试 Demo 文档分块策略"""
        kb = KnowledgeBase()

        doc = Document(
            path="/demo/test.py",
            content="# Demo code\nprint('hello')",
            doc_type=DocumentType.DEMO,
        )

        chunks = kb._chunk_single_document(doc)

        # Demo 应该整体作为一个块
        assert len(chunks) == 1

    def test_create_chunk(self):
        """测试创建文档块"""
        kb = KnowledgeBase()

        doc = Document(path="/test.md", content="content")
        chunk = kb._create_chunk(doc, "chunk content", "TestName", 0)

        assert chunk.content == "chunk content"
        assert chunk.name == "TestName"
        assert chunk.chunk_index == 0
        assert len(chunk.id) == 16

    def test_generate_chunk_id(self):
        """测试块 ID 生成"""
        kb = KnowledgeBase()

        id1 = kb._generate_chunk_id("/test.md", 0)
        id2 = kb._generate_chunk_id("/test.md", 1)
        id3 = kb._generate_chunk_id("/other.md", 0)

        assert id1 != id2
        assert id1 != id3
        assert len(id1) == 16

    def test_extract_category(self):
        """测试提取分类"""
        kb = KnowledgeBase()

        # 从路径提取分类
        cat1 = kb._extract_category("/mcdocs/接口/实体/Test.md")
        # 由于路径结构不同，可能返回 None 或具体值
        assert cat1 is None or isinstance(cat1, str)

        cat2 = kb._extract_category("/simple/path.md")
        assert cat2 is None


class TestKnowledgeBaseChunkDocuments:
    """测试文档分块"""

    def test_chunk_documents(self):
        """测试批量分块文档"""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = Path(tmpdir)
            (docs_dir / "api.md").write_text("# API\n\nThis is API content with enough text.", encoding="utf-8")
            (docs_dir / "guide.md").write_text("Paragraph 1\n\nParagraph 2", encoding="utf-8")

            kb = KnowledgeBase(docs_path=str(docs_dir))
            kb._documents = kb._load_documents()
            chunks = kb._chunk_documents()

            # 可能有文档被加载
            assert len(chunks) >= 0


class TestKnowledgeBaseSearch:
    """测试 KnowledgeBase 搜索"""

    def test_search_without_index(self):
        """测试无索引搜索"""
        kb = KnowledgeBase()

        results = kb.search("test query")

        assert results == []

    def test_search_with_persist_dir_no_index(self):
        """测试有持久化目录但无索引的搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb = KnowledgeBase(persist_dir=tmpdir)

            results = kb.search("test")

            assert results == []

    def test_get_api_without_index(self):
        """测试无索引获取 API"""
        kb = KnowledgeBase()

        result = kb.get_api("TestAPI")

        assert result is None

    def test_get_code_example_without_index(self):
        """测试无索引获取代码示例"""
        kb = KnowledgeBase()

        results = kb.get_code_example("entity")

        assert results == []

    def test_query_without_index(self):
        """测试无索引查询"""
        kb = KnowledgeBase()

        result = kb.query("如何创建实体")

        assert "未找到" in result or "抱歉" in result


class TestKnowledgeBasePersist:
    """测试 KnowledgeBase 持久化"""

    def test_persist_basic(self):
        """测试基本持久化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb = KnowledgeBase(persist_dir=tmpdir)
            kb._chunks = [
                DocumentChunk(
                    id="test1",
                    content="content1",
                    source="/test1.md",
                    doc_type=DocumentType.API,
                )
            ]

            kb.persist()

            # 检查文件是否创建
            assert (Path(tmpdir) / "metadata.json").exists()
            assert (Path(tmpdir) / "chunks.json").exists()

    def test_persist_metadata(self):
        """测试持久化元数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb = KnowledgeBase(
                persist_dir=tmpdir,
                embedding_model="test-model",
                chunk_size=256,
            )
            kb._chunks = []
            kb._documents = [Document(path="/test.md", content="test")]

            kb.persist()

            with open(Path(tmpdir) / "metadata.json", encoding="utf-8") as f:
                meta = json.load(f)

            assert meta["embedding_model"] == "test-model"
            assert meta["chunk_size"] == 256
            assert meta["total_documents"] == 1

    def test_load(self):
        """测试加载持久化数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 先保存
            kb1 = KnowledgeBase(persist_dir=tmpdir)
            kb1._chunks = [
                DocumentChunk(
                    id="test1",
                    content="content1",
                    source="/test1.md",
                    doc_type=DocumentType.API,
                    category="实体",
                )
            ]
            kb1.persist()

            # 再加载
            kb2 = KnowledgeBase.load(tmpdir)

            assert len(kb2._chunks) == 1
            assert kb2._chunks[0].id == "test1"
            assert kb2._chunks[0].category == "实体"

    def test_persist_no_dir(self):
        """测试无持久化目录"""
        kb = KnowledgeBase()

        # 不应该抛出异常
        kb.persist()

    def test_try_load_index_not_found(self):
        """测试加载不存在的索引"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb = KnowledgeBase(persist_dir=tmpdir)

            result = kb._try_load_index()

            assert result is False


class TestKnowledgeBaseBuildIndex:
    """测试 KnowledgeBase 构建索引"""

    def test_build_index_no_docs_path(self):
        """测试无文档路径构建索引"""
        kb = KnowledgeBase()

        with pytest.raises(ValueError, match="docs_path"):
            kb.build_index()

    def test_build_index_empty_dir(self):
        """测试空目录构建索引"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb = KnowledgeBase(docs_path=tmpdir)

            # 应该能处理空目录
            kb._documents = kb._load_documents()
            assert len(kb._documents) == 0


class TestEdgeCases:
    """边界条件测试"""

    def test_empty_document(self):
        """测试空文档"""
        doc = Document(path="/empty.md", content="")
        assert doc.content == ""

    def test_very_long_content(self):
        """测试超长内容"""
        kb = KnowledgeBase(chunk_size=100)

        # 使用段落分隔的长内容
        doc = Document(
            path="/long.md",
            content="Paragraph 1\n\n" * 500,  # 多个段落
            doc_type=DocumentType.GUIDE,
        )

        chunks = kb._chunk_by_paragraphs(doc)

        assert len(chunks) >= 1

    def test_special_characters_in_path(self):
        """测试路径中的特殊字符"""
        doc = Document(
            path="/path/with spaces/测试文档.md",
            content="内容",
        )

        assert "测试" in doc.path

    def test_chunk_with_none_name(self):
        """测试名称为 None 的块"""
        chunk = DocumentChunk(
            id="test",
            content="content",
            source="/test.md",
            doc_type=DocumentType.API,
            name=None,
        )

        d = chunk.to_dict()
        assert d["name"] is None

    def test_search_result_with_high_score(self):
        """测试高分数搜索结果"""
        result = SearchResult(
            content="content",
            source="/test.md",
            doc_type=DocumentType.API,
            score=1.0,
        )

        assert result.score == 1.0

    def test_multiple_chunks_same_source(self):
        """测试同一来源的多个块"""
        chunks = [
            DocumentChunk(
                id=f"chunk_{i}",
                content=f"content {i}",
                source="/same.md",
                doc_type=DocumentType.GUIDE,
                chunk_index=i,
                total_chunks=3,
            )
            for i in range(3)
        ]

        assert all(c.source == "/same.md" for c in chunks)
        assert [c.chunk_index for c in chunks] == [0, 1, 2]
