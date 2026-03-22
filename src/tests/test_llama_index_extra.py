"""
LlamaIndex extra tests for better coverage.

Tests for uncovered lines in llama_index.py.
"""

import tempfile
from pathlib import Path
from unittest import mock

import pytest

from mc_agent_kit.retrieval.llama_index import (
    LlamaIndexConfig,
    LlamaIndexRetriever,
    create_llama_index_retriever,
)


class TestLlamaIndexRetrieverVectorStore:
    """Test vector store initialization"""

    def test_init_vector_store_unavailable(self):
        """Test vector store init when LlamaIndex unavailable"""
        retriever = LlamaIndexRetriever()
        retriever._llama_available = False

        retriever._init_vector_store()
        assert retriever._vector_store is None


class TestLlamaIndexRetrieverIndexDocuments:
    """Test index_documents method"""

    def test_index_documents_unavailable(self):
        """Test indexing documents when unavailable"""
        retriever = LlamaIndexRetriever()
        retriever._llama_available = False

        result = retriever.index_documents(["doc1"])

        assert result is False


class TestLlamaIndexRetrieverLoadIndex:
    """Test load_index method"""

    def test_load_index_no_dir(self):
        """Test loading index without directory"""
        config = LlamaIndexConfig(persist_dir=None)
        retriever = LlamaIndexRetriever(config)
        retriever._llama_available = True

        result = retriever.load_index()

        assert result is False

    def test_load_index_unavailable(self):
        """Test loading index when unavailable"""
        retriever = LlamaIndexRetriever()
        retriever._llama_available = False

        result = retriever.load_index("/some/path")

        assert result is False


class TestLlamaIndexRetrieverQuery:
    """Test query method"""

    def test_query_with_streaming(self):
        """Test query with streaming enabled"""
        config = LlamaIndexConfig(streaming=True)
        retriever = LlamaIndexRetriever(config)
        retriever._llama_available = True

        mock_engine = mock.MagicMock()
        mock_engine.query.return_value = "stream response"

        mock_index = mock.MagicMock()
        mock_index.as_query_engine.return_value = mock_engine
        retriever._index = mock_index

        result = retriever.query("test query")

        assert result == "stream response"
        mock_index.as_query_engine.assert_called_once()

    def test_query_with_custom_response_mode(self):
        """Test query with custom response mode"""
        config = LlamaIndexConfig(response_mode="refine")
        retriever = LlamaIndexRetriever(config)
        retriever._llama_available = True

        mock_engine = mock.MagicMock()
        mock_engine.query.return_value = "refine response"

        mock_index = mock.MagicMock()
        mock_index.as_query_engine.return_value = mock_engine
        retriever._index = mock_index

        result = retriever.query("test query")

        assert result == "refine response"


class TestLlamaIndexRetrieverRetrieve:
    """Test retrieve method"""

    def test_retrieve_with_metadata(self):
        """Test retrieve with metadata"""
        retriever = LlamaIndexRetriever()
        retriever._llama_available = True

        # Create mock nodes with metadata
        mock_node1 = mock.MagicMock()
        mock_node1.node.text = "content 1"
        mock_node1.node.metadata = {"source": "test1", "type": "api"}
        mock_node1.score = 0.9

        mock_retriever = mock.MagicMock()
        mock_retriever.retrieve.return_value = [mock_node1]

        mock_index = mock.MagicMock()
        mock_index.as_retriever.return_value = mock_retriever
        retriever._index = mock_index

        results = retriever.retrieve("test query", top_k=3)

        assert len(results) == 1
        assert results[0]["metadata"]["source"] == "test1"

    def test_retrieve_exception(self):
        """Test retrieve with exception"""
        retriever = LlamaIndexRetriever()
        retriever._llama_available = True

        mock_index = mock.MagicMock()
        mock_index.as_retriever.side_effect = Exception("Retrieve error")
        retriever._index = mock_index

        results = retriever.retrieve("test query")

        assert results == []


class TestLlamaIndexCheckAvailability:
    """Test availability checking"""

    def test_check_availability_sets_flag(self):
        """Test check availability sets flag"""
        retriever = LlamaIndexRetriever()
        # The flag should be set based on whether llama_index is installed
        assert isinstance(retriever._llama_available, bool)

    def test_is_available_returns_flag(self):
        """Test is_available returns flag"""
        retriever = LlamaIndexRetriever()
        retriever._llama_available = True

        assert retriever.is_available() is True

        retriever._llama_available = False
        assert retriever.is_available() is False


class TestCreateLlamaIndexRetrieverConfig:
    """Test create_llama_index_retriever config handling"""

    def test_creates_config_correctly(self):
        """Test that config is created with correct params"""
        with tempfile.TemporaryDirectory() as tmpdir:
            retriever = create_llama_index_retriever(
                persist_dir=tmpdir,
                embedding_model="custom-model",
            )

            assert retriever.config.persist_dir == tmpdir
            assert retriever.config.embedding_model == "custom-model"


class TestLlamaIndexGetStats:
    """Test get_stats method"""

    def test_get_stats_returns_info(self):
        """Test get_stats returns correct info"""
        config = LlamaIndexConfig(
            persist_dir="/test",
            collection_name="test_collection",
            embedding_model="test-model",
        )
        retriever = LlamaIndexRetriever(config)

        stats = retriever.get_stats()

        assert stats["persist_dir"] == "/test"
        assert stats["collection_name"] == "test_collection"
        assert stats["embedding_model"] == "test-model"
        assert "llama_available" in stats
        assert "index_loaded" in stats