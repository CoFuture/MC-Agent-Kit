"""
向量存储测试

测试 VectorStore 类的各项功能。
"""

from unittest import mock

import pytest

from mc_agent_kit.retrieval.vector_store import (
    Document,
    SearchResult,
    VectorStore,
    VectorStoreConfig,
    create_vector_store,
)


class TestVectorStoreConfig:
    """测试 VectorStoreConfig"""

    def test_default_config(self):
        """测试默认配置"""
        config = VectorStoreConfig()
        assert config.persist_dir is None
        assert config.collection_name == "mc_knowledge"
        assert config.embedding_model == "all-MiniLM-L6-v2"
        assert config.distance_metric == "cosine"
        assert config.batch_size == 100
        assert config.enable_incremental is True
        assert config.hash_algorithm == "md5"

    def test_custom_config(self):
        """测试自定义配置"""
        config = VectorStoreConfig(
            persist_dir="/data/vectors",
            collection_name="custom_collection",
            embedding_model="custom-model",
            distance_metric="l2",
            batch_size=50,
            enable_incremental=False,
            hash_algorithm="sha256",
        )
        assert config.persist_dir == "/data/vectors"
        assert config.collection_name == "custom_collection"
        assert config.embedding_model == "custom-model"
        assert config.distance_metric == "l2"
        assert config.batch_size == 50
        assert config.enable_incremental is False
        assert config.hash_algorithm == "sha256"


class TestDocument:
    """测试 Document 数据类"""

    def test_create_document(self):
        """测试创建文档"""
        doc = Document(
            id="test-1",
            content="Test content",
            metadata={"type": "test"},
        )
        assert doc.id == "test-1"
        assert doc.content == "Test content"
        assert doc.metadata == {"type": "test"}
        assert doc.embedding is None

    def test_document_to_dict(self):
        """测试文档转字典"""
        doc = Document(
            id="test-1",
            content="Test content",
            metadata={"type": "test"},
        )
        result = doc.to_dict()
        assert result["id"] == "test-1"
        assert result["content"] == "Test content"
        assert result["metadata"] == {"type": "test"}
        assert "embedding" not in result

    def test_document_with_embedding(self):
        """测试带嵌入的文档"""
        doc = Document(
            id="test-1",
            content="Test content",
            embedding=[0.1, 0.2, 0.3],
        )
        assert doc.embedding == [0.1, 0.2, 0.3]


class TestSearchResult:
    """测试 SearchResult 数据类"""

    def test_create_search_result(self):
        """测试创建搜索结果"""
        result = SearchResult(
            id="test-1",
            content="Test content",
            score=0.95,
            metadata={"type": "test"},
        )
        assert result.id == "test-1"
        assert result.content == "Test content"
        assert result.score == 0.95
        assert result.metadata == {"type": "test"}

    def test_search_result_to_dict(self):
        """测试搜索结果转字典"""
        result = SearchResult(
            id="test-1",
            content="Test content",
            score=0.95,
            metadata={"type": "test"},
        )
        data = result.to_dict()
        assert data["id"] == "test-1"
        assert data["content"] == "Test content"
        assert data["score"] == 0.95
        assert data["metadata"] == {"type": "test"}


class TestVectorStore:
    """测试 VectorStore 类"""

    def test_init_default(self):
        """测试默认初始化"""
        store = VectorStore()
        assert store.config is not None
        assert store._client is None
        assert store._collection is None
        assert store._initialized is False

    def test_init_with_config(self):
        """测试带配置初始化"""
        config = VectorStoreConfig(
            persist_dir="/test",
            collection_name="test_collection",
        )
        store = VectorStore(config)
        assert store.config.persist_dir == "/test"
        assert store.config.collection_name == "test_collection"

    def test_compute_hash_md5(self):
        """测试 MD5 哈希计算"""
        config = VectorStoreConfig(hash_algorithm="md5")
        store = VectorStore(config)

        hash1 = store._compute_hash("test content")
        hash2 = store._compute_hash("test content")
        hash3 = store._compute_hash("different content")

        assert hash1 == hash2  # 相同内容相同哈希
        assert hash1 != hash3  # 不同内容不同哈希
        assert len(hash1) == 32  # MD5 哈希长度

    def test_compute_hash_sha256(self):
        """测试 SHA256 哈希计算"""
        config = VectorStoreConfig(hash_algorithm="sha256")
        store = VectorStore(config)

        hash1 = store._compute_hash("test content")
        assert len(hash1) == 64  # SHA256 哈希长度

    def test_ensure_initialized_no_chromadb(self):
        """测试无 ChromaDB 时的初始化"""
        store = VectorStore()
        # 没有 ChromaDB 时应该不抛异常
        store._ensure_initialized()
        assert store._initialized is True

    def test_add_documents_without_collection(self):
        """测试无集合时添加文档"""
        store = VectorStore()
        docs = [Document(id="1", content="test")]

        result = store.add_documents(docs)
        assert result == 0  # 无集合时返回 0

    def test_search_without_collection(self):
        """测试无集合时搜索"""
        store = VectorStore()
        results = store.search("test query")
        assert results == []

    def test_get_document_without_collection(self):
        """测试无集合时获取文档"""
        store = VectorStore()
        result = store.get_document("test-id")
        assert result is None

    def test_count_without_collection(self):
        """测试无集合时计数"""
        store = VectorStore()
        count = store.count()
        assert count == 0

    def test_clear_without_client(self):
        """测试无客户端时清空"""
        store = VectorStore()
        # 应该不会抛异常
        store.clear()

    def test_get_stats(self):
        """测试获取统计信息"""
        store = VectorStore()
        stats = store.get_stats()

        assert "collection_name" in stats
        assert "document_count" in stats
        assert "embedding_model" in stats
        assert "distance_metric" in stats
        assert "persist_dir" in stats
        assert "incremental_enabled" in stats


class TestVectorStoreWithMock:
    """使用 Mock 测试 VectorStore"""

    def test_add_documents_with_mock_collection(self):
        """测试使用 Mock 集合添加文档"""
        store = VectorStore()
        store._initialized = True

        # 创建 Mock 集合
        mock_collection = mock.MagicMock()
        mock_collection.get.return_value = {"ids": [], "metadatas": []}
        mock_collection.add.return_value = None
        store._collection = mock_collection

        docs = [
            Document(id="1", content="test content 1"),
            Document(id="2", content="test content 2"),
        ]

        result = store.add_documents(docs)
        assert result == 2
        mock_collection.add.assert_called_once()

    def test_add_documents_incremental_skip(self):
        """测试增量更新跳过已存在的文档"""
        config = VectorStoreConfig(enable_incremental=True)
        store = VectorStore(config)
        store._initialized = True

        # 设置已存在的哈希
        content = "test content"
        hash_value = store._compute_hash(content)
        store._document_hashes["1"] = hash_value

        mock_collection = mock.MagicMock()
        store._collection = mock_collection

        docs = [Document(id="1", content=content)]
        result = store.add_documents(docs)

        # 内容相同，应该跳过
        assert result == 0

    def test_delete_documents_with_mock(self):
        """测试使用 Mock 集合删除文档"""
        store = VectorStore()
        store._initialized = True

        mock_collection = mock.MagicMock()
        store._collection = mock_collection

        store._document_hashes["1"] = "hash1"
        store._document_hashes["2"] = "hash2"

        store.delete_documents(["1", "2"])

        mock_collection.delete.assert_called_once_with(ids=["1", "2"])
        assert "1" not in store._document_hashes
        assert "2" not in store._document_hashes

    def test_search_with_mock_collection(self):
        """测试使用 Mock 集合搜索"""
        store = VectorStore()
        store._initialized = True

        mock_collection = mock.MagicMock()
        mock_collection.query.return_value = {
            "ids": [["1", "2"]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"type": "test"}, {"type": "api"}]],
            "distances": [[0.1, 0.2]],
        }
        store._collection = mock_collection

        results = store.search("test query", top_k=2)

        assert len(results) == 2
        assert results[0].id == "1"
        assert results[0].content == "doc1"
        assert results[1].id == "2"

    def test_get_document_with_mock(self):
        """测试使用 Mock 集合获取文档"""
        store = VectorStore()
        store._initialized = True

        mock_collection = mock.MagicMock()
        mock_collection.get.return_value = {
            "documents": ["test content"],
            "metadatas": [{"type": "test"}],
        }
        store._collection = mock_collection

        doc = store.get_document("1")

        assert doc is not None
        assert doc.id == "1"
        assert doc.content == "test content"
        assert doc.metadata == {"type": "test"}

    def test_get_document_not_found(self):
        """测试获取不存在的文档"""
        store = VectorStore()
        store._initialized = True

        mock_collection = mock.MagicMock()
        mock_collection.get.return_value = {"documents": []}
        store._collection = mock_collection

        doc = store.get_document("nonexistent")
        assert doc is None

    def test_count_with_mock(self):
        """测试使用 Mock 集合计数"""
        store = VectorStore()
        store._initialized = True

        mock_collection = mock.MagicMock()
        mock_collection.count.return_value = 100
        store._collection = mock_collection

        count = store.count()
        assert count == 100

    def test_clear_with_mock(self):
        """测试使用 Mock 客户端清空"""
        store = VectorStore()
        store._initialized = True

        mock_client = mock.MagicMock()
        mock_collection = mock.MagicMock()
        store._client = mock_client
        store._collection = mock_collection

        store.clear()

        mock_client.delete_collection.assert_called_once()
        assert len(store._document_hashes) == 0

    def test_search_exception_handling(self):
        """测试搜索异常处理"""
        store = VectorStore()
        store._initialized = True

        mock_collection = mock.MagicMock()
        mock_collection.query.side_effect = Exception("Search failed")
        store._collection = mock_collection

        results = store.search("test")
        assert results == []

    def test_get_document_exception_handling(self):
        """测试获取文档异常处理"""
        store = VectorStore()
        store._initialized = True

        mock_collection = mock.MagicMock()
        mock_collection.get.side_effect = Exception("Get failed")
        store._collection = mock_collection

        doc = store.get_document("1")
        assert doc is None


class TestCreateVectorStore:
    """测试 create_vector_store 函数"""

    def test_create_default(self):
        """测试默认创建"""
        store = create_vector_store()
        assert isinstance(store, VectorStore)
        assert store.config.persist_dir is None
        assert store.config.collection_name == "mc_knowledge"

    def test_create_with_persist_dir(self):
        """测试带持久化目录创建"""
        store = create_vector_store(persist_dir="/data/vectors")
        assert store.config.persist_dir == "/data/vectors"

    def test_create_with_collection_name(self):
        """测试带集合名称创建"""
        store = create_vector_store(collection_name="custom")
        assert store.config.collection_name == "custom"

    def test_create_with_embedding_model(self):
        """测试带嵌入模型创建"""
        store = create_vector_store(embedding_model="custom-model")
        assert store.config.embedding_model == "custom-model"

    def test_create_with_all_params(self):
        """测试带所有参数创建"""
        store = create_vector_store(
            persist_dir="/data/vectors",
            collection_name="custom",
            embedding_model="custom-model",
        )
        assert store.config.persist_dir == "/data/vectors"
        assert store.config.collection_name == "custom"
        assert store.config.embedding_model == "custom-model"


class TestVectorStoreBatching:
    """测试批量操作"""

    def test_add_documents_batch(self):
        """测试批量添加文档"""
        config = VectorStoreConfig(batch_size=2)
        store = VectorStore(config)
        store._initialized = True

        mock_collection = mock.MagicMock()
        mock_collection.get.return_value = {"ids": [], "metadatas": []}
        store._collection = mock_collection

        # 添加 5 个文档，应该分 3 批
        docs = [
            Document(id=str(i), content=f"content {i}")
            for i in range(5)
        ]

        result = store.add_documents(docs)
        assert result == 5
        # 应该调用了 3 次 add（5 个文档，批次大小为 2）
        assert mock_collection.add.call_count == 3


class TestVectorStoreDistanceMetrics:
    """测试距离度量"""

    def test_cosine_score_conversion(self):
        """测试 cosine 距离转换"""
        config = VectorStoreConfig(distance_metric="cosine")
        store = VectorStore(config)
        store._initialized = True

        mock_collection = mock.MagicMock()
        mock_collection.query.return_value = {
            "ids": [["1"]],
            "documents": [["doc"]],
            "metadatas": [[{}]],
            "distances": [[0.2]],  # cosine 距离 0.2
        }
        store._collection = mock_collection

        results = store.search("test")
        # cosine 分数 = 1 - distance
        assert results[0].score == pytest.approx(0.8, 0.01)

    def test_l2_score_conversion(self):
        """测试 L2 距离转换"""
        config = VectorStoreConfig(distance_metric="l2")
        store = VectorStore(config)
        store._initialized = True

        mock_collection = mock.MagicMock()
        mock_collection.query.return_value = {
            "ids": [["1"]],
            "documents": [["doc"]],
            "metadatas": [[{}]],
            "distances": [[1.0]],  # L2 距离 1.0
        }
        store._collection = mock_collection

        results = store.search("test")
        # L2 分数 = 1 / (1 + distance)
        assert results[0].score == pytest.approx(0.5, 0.01)