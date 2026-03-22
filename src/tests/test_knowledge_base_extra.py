"""
Knowledge base extra tests for better coverage.

Tests for uncovered lines in knowledge_base.py.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from mc_agent_kit.knowledge.base import Document, DocumentChunk, DocumentType, SearchResult
from mc_agent_kit.knowledge.knowledge_base import KnowledgeBase


class TestKnowledgeBaseAddChunksToStore:
    """Tests for adding chunks to vector store"""

    def test_add_chunks_to_store_no_store(self):
        """Test adding chunks without vector store"""
        kb = KnowledgeBase()
        kb._vector_store = None
        kb._chunks = [DocumentChunk(id="test", content="c", source="/t.md", doc_type=DocumentType.API)]

        # Should not raise exception
        kb._add_chunks_to_store()

    def test_add_chunks_to_store_no_chunks(self):
        """Test adding empty chunks list"""
        kb = KnowledgeBase()
        kb._vector_store = mock.MagicMock()
        kb._chunks = []

        kb._add_chunks_to_store()

        kb._vector_store.add.assert_not_called()

    def test_add_chunks_to_store_success(self):
        """Test adding chunks to store successfully"""
        kb = KnowledgeBase()
        kb._vector_store = mock.MagicMock()
        kb._chunks = [
            DocumentChunk(
                id=f"chunk_{i}",
                content=f"content {i}",
                source=f"/test{i}.md",
                doc_type=DocumentType.API,
                category="test",
            )
            for i in range(5)
        ]

        kb._add_chunks_to_store()

        kb._vector_store.add.assert_called()

    def test_add_chunks_to_store_large_batch(self):
        """Test adding large batch of chunks"""
        kb = KnowledgeBase()
        kb._vector_store = mock.MagicMock()
        kb._chunks = [
            DocumentChunk(
                id=f"chunk_{i}",
                content=f"content {i}",
                source=f"/test{i}.md",
                doc_type=DocumentType.API,
            )
            for i in range(250)  # More than batch size of 100
        ]

        kb._add_chunks_to_store()

        # Should be called multiple times
        assert kb._vector_store.add.call_count >= 2


class TestKnowledgeBaseVectorSearch:
    """Tests for vector search"""

    def test_vector_search_no_store(self):
        """Test vector search without vector store"""
        kb = KnowledgeBase()
        kb._vector_store = None

        results = kb._vector_search("query", None, 5)

        assert results == []

    def test_vector_search_with_results(self):
        """Test vector search with results"""
        kb = KnowledgeBase()

        mock_store = mock.MagicMock()
        mock_store.query.return_value = {
            "documents": [["doc1 content", "doc2 content"]],
            "metadatas": [[
                {"source": "/test1.md", "doc_type": "api"},
                {"source": "/test2.md", "doc_type": "event"},
            ]],
            "distances": [[0.1, 0.2]],
        }
        kb._vector_store = mock_store

        results = kb._vector_search("test query", None, 5)

        assert len(results) == 2
        assert results[0].content == "doc1 content"
        assert results[0].score == 0.9  # 1 - distance

    def test_vector_search_with_filter(self):
        """Test vector search with filter"""
        kb = KnowledgeBase()

        mock_store = mock.MagicMock()
        mock_store.query.return_value = {
            "documents": [["api doc"]],
            "metadatas": [[{"source": "/api.md", "doc_type": "api"}]],
            "distances": [[0.05]],
        }
        kb._vector_store = mock_store

        results = kb._vector_search("query", {"doc_type": "api"}, 3)

        mock_store.query.assert_called_once_with(
            query_texts=["query"],
            n_results=3,
            where={"doc_type": "api"},
        )

    def test_vector_search_no_results(self):
        """Test vector search with no results"""
        kb = KnowledgeBase()

        mock_store = mock.MagicMock()
        mock_store.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        kb._vector_store = mock_store

        results = kb._vector_search("query", None, 5)

        assert len(results) == 0

    def test_vector_search_with_category(self):
        """Test vector search results with category"""
        kb = KnowledgeBase()

        mock_store = mock.MagicMock()
        mock_store.query.return_value = {
            "documents": [["content"]],
            "metadatas": [[{
                "source": "/test.md",
                "doc_type": "api",
                "category": "entity",
            }]],
            "distances": [[0.1]],
        }
        kb._vector_store = mock_store

        results = kb._vector_search("query", None, 1)

        assert results[0].category == "entity"


class TestKnowledgeBaseTryLoadIndex:
    """Tests for _try_load_index method"""

    def test_try_load_index_success(self):
        """Test successfully loading existing index"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create metadata file
            meta_path = Path(tmpdir) / "metadata.json"
            meta_path.write_text(json.dumps({
                "embedding_model": "test-model",
                "chunk_size": 512,
            }))

            # Create chunks file
            chunks_path = Path(tmpdir) / "chunks.json"
            chunks_path.write_text(json.dumps([{
                "id": "test",
                "content": "content",
                "source": "/test.md",
                "doc_type": "api",
            }]))

            kb = KnowledgeBase(persist_dir=tmpdir)
            result = kb._try_load_index()

            assert result is True
            assert kb._index_built is True

    def test_try_load_index_no_metadata(self):
        """Test loading index without metadata"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb = KnowledgeBase(persist_dir=tmpdir)
            result = kb._try_load_index()

            assert result is False

    def test_try_load_index_exception(self):
        """Test loading index with exception"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid metadata file
            meta_path = Path(tmpdir) / "metadata.json"
            meta_path.write_text("invalid json")

            kb = KnowledgeBase(persist_dir=tmpdir)
            result = kb._try_load_index()

            assert result is False


class TestKnowledgeBaseSearchWithIndex:
    """Tests for search with loaded index"""

    def test_search_tries_load_index(self):
        """Test search tries to load index"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb = KnowledgeBase(persist_dir=tmpdir)
            kb._index_built = False

            # Mock _try_load_index
            with mock.patch.object(kb, "_try_load_index", return_value=True) as mock_load:
                with mock.patch.object(kb, "_vector_search", return_value=[]):
                    kb.search("query")

                    mock_load.assert_called_once()


class TestKnowledgeBaseQuery:
    """Tests for query method"""

    def test_query_with_results(self):
        """Test query with results"""
        kb = KnowledgeBase()

        with mock.patch.object(kb, "search") as mock_search:
            mock_search.return_value = [
                SearchResult(
                    content="API documentation for GetEngineType",
                    source="/api.md",
                    doc_type=DocumentType.API,
                    score=0.9,
                ),
                SearchResult(
                    content="Event handler example",
                    source="/guide.md",
                    doc_type=DocumentType.GUIDE,
                    score=0.7,
                ),
            ]

            result = kb.query("How to use GetEngineType?")

            assert "参考" in result
            assert "GetEngineType" in result

    def test_query_no_results(self):
        """Test query with no results"""
        kb = KnowledgeBase()

        with mock.patch.object(kb, "search", return_value=[]):
            result = kb.query("Unknown topic")

            assert "未找到" in result or "抱歉" in result


class TestKnowledgeBaseGetApi:
    """Tests for get_api method"""

    def test_get_api_exact_match(self):
        """Test getting API with exact match"""
        kb = KnowledgeBase()

        with mock.patch.object(kb, "search") as mock_search:
            mock_search.return_value = [
                SearchResult(
                    content="GetEngineType returns engine type",
                    source="/api.md",
                    doc_type=DocumentType.API,
                    score=0.95,
                    name="GetEngineType",
                ),
            ]

            result = kb.get_api("GetEngineType")

            assert result is not None
            assert result.name == "GetEngineType"

    def test_get_api_fuzzy_match(self):
        """Test getting API with fuzzy match"""
        kb = KnowledgeBase()

        with mock.patch.object(kb, "search") as mock_search:
            mock_search.return_value = [
                SearchResult(
                    content="Similar API",
                    source="/api.md",
                    doc_type=DocumentType.API,
                    score=0.6,
                    name="GetEngine",
                ),
            ]

            result = kb.get_api("GetEngineType")

            # Returns first result even if not exact match
            assert result is not None

    def test_get_api_not_found(self):
        """Test getting API not found"""
        kb = KnowledgeBase()

        with mock.patch.object(kb, "search", return_value=[]):
            result = kb.get_api("NonExistentAPI")

            assert result is None


class TestKnowledgeBaseGetCodeExample:
    """Tests for get_code_example method"""

    def test_get_code_example_success(self):
        """Test getting code example"""
        kb = KnowledgeBase()

        with mock.patch.object(kb, "search") as mock_search:
            mock_search.return_value = [
                SearchResult(
                    content="def create_entity():\n    return CreateEntity()",
                    source="/demo.py",
                    doc_type=DocumentType.DEMO,
                    score=0.9,
                ),
            ]

            results = kb.get_code_example("create entity")

            assert len(results) == 1
            mock_search.assert_called_once()


class TestKnowledgeBaseBuildIndexFull:
    """Tests for full build_index workflow"""

    def test_build_index_full_workflow(self):
        """Test full build index workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = Path(tmpdir) / "docs"
            docs_dir.mkdir()

            (docs_dir / "api.md").write_text("# API\n\nAPI content", encoding="utf-8")
            (docs_dir / "guide.md").write_text("# Guide\n\nGuide content", encoding="utf-8")

            persist_dir = Path(tmpdir) / "persist"

            kb = KnowledgeBase(
                docs_path=str(docs_dir),
                persist_dir=str(persist_dir),
            )

            with mock.patch.object(kb, "_create_vector_index"):
                kb.build_index()

            assert kb._index_built is True
            assert len(kb._documents) == 2
            assert len(kb._chunks) > 0

            # Check persistence
            assert (persist_dir / "metadata.json").exists()
            assert (persist_dir / "chunks.json").exists()

    def test_build_index_force(self):
        """Test build index with force option"""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = Path(tmpdir) / "docs"
            docs_dir.mkdir()
            (docs_dir / "test.md").write_text("content", encoding="utf-8")

            kb = KnowledgeBase(docs_path=str(docs_dir))

            with mock.patch.object(kb, "_create_vector_index") as mock_create:
                kb.build_index(force=True)

                mock_create.assert_called_once_with(True)


class TestKnowledgeBaseLoadClassMethod:
    """Tests for KnowledgeBase.load class method"""

    def test_load_success(self):
        """Test loading persisted knowledge base"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create metadata
            meta = {
                "embedding_model": "test-model",
                "chunk_size": 512,
                "chunk_overlap": 50,
                "total_documents": 1,
                "total_chunks": 1,
            }
            Path(tmpdir, "metadata.json").write_text(json.dumps(meta))

            # Create chunks
            chunks = [{
                "id": "test",
                "content": "test content",
                "source": "/test.md",
                "doc_type": "api",
                "chunk_index": 0,
                "total_chunks": 1,
            }]
            Path(tmpdir, "chunks.json").write_text(json.dumps(chunks))

            kb = KnowledgeBase.load(tmpdir)

            assert len(kb._chunks) == 1
            assert kb._chunks[0].content == "test content"
            assert kb._index_built is True


class TestKnowledgeBaseEdgeCases:
    """Edge case tests"""

    def test_build_index_empty_docs_path(self):
        """Test build index with empty docs path"""
        kb = KnowledgeBase()
        kb.docs_path = None

        with pytest.raises(ValueError):
            kb.build_index()

    def test_search_with_unbuilt_index(self):
        """Test search with unbuilt index and no persist dir"""
        kb = KnowledgeBase()
        kb._index_built = False
        kb.persist_dir = None

        results = kb.search("query")

        assert results == []

    def test_persist_creates_directory(self):
        """Test persist creates directory if not exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            persist_dir = Path(tmpdir) / "new_dir"
            assert not persist_dir.exists()

            kb = KnowledgeBase(persist_dir=str(persist_dir))
            kb._chunks = []

            kb.persist()

            assert persist_dir.exists()

    def test_create_vector_index_no_chunks(self):
        """Test creating vector index without chunks"""
        kb = KnowledgeBase()
        kb._chunks = []

        # Should not raise error, but vector store might remain None
        kb._create_vector_index(force=False)


class TestKnowledgeBasePersistAndLoad:
    """Tests for persistence operations"""

    def test_persist_saves_correct_data(self):
        """Test persist saves correct data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb = KnowledgeBase(persist_dir=tmpdir)
            kb._documents = [
                Document(path="/doc1.md", content="doc1"),
                Document(path="/doc2.md", content="doc2"),
            ]
            kb._chunks = [
                DocumentChunk(
                    id="chunk1",
                    content="chunk content",
                    source="/doc1.md",
                    doc_type=DocumentType.API,
                    category="entity",
                )
            ]

            kb.persist()

            # Verify metadata
            with open(Path(tmpdir) / "metadata.json", encoding="utf-8") as f:
                meta = json.load(f)
            assert meta["total_documents"] == 2
            assert meta["total_chunks"] == 1

            # Verify chunks
            with open(Path(tmpdir) / "chunks.json", encoding="utf-8") as f:
                chunks_data = json.load(f)
            assert len(chunks_data) == 1
            assert chunks_data[0]["category"] == "entity"