"""
检索模块测试 (v0.5.0)

测试向量存储、语义搜索、混合搜索和 LlamaIndex 集成。
"""

import os
import sys

import pytest

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mc_agent_kit.retrieval.vector_store import (
    Document,
    SearchResult,
    VectorStore,
    VectorStoreConfig,
)
from mc_agent_kit.retrieval.semantic_search import (
    IndexStats,
    SemanticSearchConfig,
    SemanticSearchEngine,
)
from mc_agent_kit.retrieval.hybrid_search import (
    HybridSearchConfig,
    HybridSearchEngine,
    HybridSearchResult,
    KeywordSearchEngine,
)
from mc_agent_kit.retrieval.llama_index import (
    LlamaIndexConfig,
    LlamaIndexRetriever,
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

    def test_custom_config(self):
        """测试自定义配置"""
        config = VectorStoreConfig(
            persist_dir="./data/test",
            collection_name="test_collection",
            embedding_model="text2vec-chinese",
            distance_metric="l2",
            batch_size=50,
        )

        assert config.persist_dir == "./data/test"
        assert config.collection_name == "test_collection"
        assert config.embedding_model == "text2vec-chinese"
        assert config.distance_metric == "l2"
        assert config.batch_size == 50


class TestDocument:
    """测试 Document"""

    def test_document_creation(self):
        """测试文档创建"""
        doc = Document(
            id="test_doc",
            content="这是测试内容",
            metadata={"type": "test"},
        )

        assert doc.id == "test_doc"
        assert doc.content == "这是测试内容"
        assert doc.metadata["type"] == "test"
        assert doc.embedding is None

    def test_document_to_dict(self):
        """测试文档转字典"""
        doc = Document(
            id="doc1",
            content="内容",
            metadata={"key": "value"},
        )

        d = doc.to_dict()

        assert d["id"] == "doc1"
        assert d["content"] == "内容"
        assert d["metadata"]["key"] == "value"


class TestSearchResult:
    """测试 SearchResult"""

    def test_search_result_creation(self):
        """测试搜索结果创建"""
        result = SearchResult(
            id="result1",
            content="结果内容",
            score=0.95,
            metadata={"source": "test"},
        )

        assert result.id == "result1"
        assert result.score == 0.95

    def test_search_result_to_dict(self):
        """测试搜索结果转字典"""
        result = SearchResult(
            id="r1",
            content="内容",
            score=0.8,
        )

        d = result.to_dict()

        assert d["score"] == 0.8


class TestVectorStore:
    """测试 VectorStore"""

    def test_vector_store_init(self):
        """测试向量存储初始化"""
        config = VectorStoreConfig(collection_name="test_init")
        store = VectorStore(config)

        assert store.config.collection_name == "test_init"

    def test_vector_store_without_chromadb(self):
        """测试没有 ChromaDB 时的行为"""
        config = VectorStoreConfig(collection_name="test_no_chroma")
        store = VectorStore(config)

        # 应该不会抛出异常
        stats = store.get_stats()
        assert stats["collection_name"] == "test_no_chroma"


class TestSemanticSearchConfig:
    """测试 SemanticSearchConfig"""

    def test_default_config(self):
        """测试默认配置"""
        config = SemanticSearchConfig()

        assert config.chunk_size == 512
        assert config.chunk_overlap == 50
        assert config.default_top_k == 5
        assert config.min_score == 0.0

    def test_custom_config(self):
        """测试自定义配置"""
        config = SemanticSearchConfig(
            persist_dir="./data/semantic",
            chunk_size=256,
            chunk_overlap=30,
        )

        assert config.chunk_size == 256
        assert config.chunk_overlap == 30


class TestIndexStats:
    """测试 IndexStats"""

    def test_index_stats_creation(self):
        """测试索引统计创建"""
        stats = IndexStats(
            total_documents=100,
            total_chunks=500,
            embedding_model="test-model",
        )

        assert stats.total_documents == 100
        assert stats.total_chunks == 500

    def test_index_stats_to_dict(self):
        """测试索引统计转字典"""
        stats = IndexStats(
            total_documents=50,
            total_chunks=200,
            embedding_model="model",
            collection_name="test",
        )

        d = stats.to_dict()

        assert d["total_documents"] == 50
        assert d["total_chunks"] == 200


class TestSemanticSearchEngine:
    """测试 SemanticSearchEngine"""

    def test_engine_init(self):
        """测试引擎初始化"""
        config = SemanticSearchConfig(collection_name="test_semantic")
        engine = SemanticSearchEngine(config)

        assert engine.config.collection_name == "test_semantic"

    def test_chunk_text(self):
        """测试文本分块"""
        config = SemanticSearchConfig(chunk_size=100, chunk_overlap=20)
        engine = SemanticSearchEngine(config)

        # 短文本
        short_text = "这是短文本"
        chunks = engine._chunk_text(short_text)
        assert len(chunks) == 1
        assert chunks[0] == short_text

        # 长文本
        long_text = "这是第一句话。这是第二句话。这是第三句话。" * 20
        chunks = engine._chunk_text(long_text)
        assert len(chunks) > 1

    def test_generate_doc_id(self):
        """测试文档 ID 生成"""
        config = SemanticSearchConfig()
        engine = SemanticSearchEngine(config)

        id1 = engine._generate_doc_id("内容1", 0)
        id2 = engine._generate_doc_id("内容2", 0)
        id3 = engine._generate_doc_id("内容1", 1)

        assert id1 != id2
        assert id1 != id3


class TestKeywordSearchEngine:
    """测试 KeywordSearchEngine"""

    def test_keyword_engine_init(self):
        """测试关键词引擎初始化"""
        engine = KeywordSearchEngine()

        assert engine._documents == {}
        assert engine._inverted_index == {}

    def test_tokenize(self):
        """测试分词"""
        engine = KeywordSearchEngine()

        # 英文分词
        terms = engine._tokenize("Hello World Test")
        assert "hello" in terms
        assert "world" in terms
        assert "test" in terms

        # 中文分词
        terms = engine._tokenize("测试中文分词")
        # 应该有双字词
        assert any(len(t) == 2 for t in terms if all('\u4e00' <= c <= '\u9fff' for c in t))

    def test_index_and_search(self):
        """测试索引和搜索"""
        engine = KeywordSearchEngine()

        documents = {
            "doc1": "如何创建自定义实体",
            "doc2": "实体碰撞检测方法",
            "doc3": "获取玩家坐标 API",
        }

        engine.index(documents)

        # 搜索
        results = engine.search("实体", top_k=2)

        assert len(results) <= 2
        assert len(results) > 0
        # doc1 和 doc2 应该包含"实体"
        result_ids = [r[0] for r in results]
        assert "doc1" in result_ids or "doc2" in result_ids


class TestHybridSearchConfig:
    """测试 HybridSearchConfig"""

    def test_default_config(self):
        """测试默认配置"""
        config = HybridSearchConfig()

        assert config.keyword_weight == 0.4
        assert config.semantic_weight == 0.6
        assert config.default_top_k == 10

    def test_custom_config(self):
        """测试自定义配置"""
        config = HybridSearchConfig(
            keyword_weight=0.3,
            semantic_weight=0.7,
            default_top_k=5,
        )

        assert config.keyword_weight == 0.3
        assert config.semantic_weight == 0.7


class TestHybridSearchResult:
    """测试 HybridSearchResult"""

    def test_result_creation(self):
        """测试结果创建"""
        result = HybridSearchResult(
            id="result1",
            content="内容",
            score=0.9,
            keyword_score=0.8,
            semantic_score=0.95,
        )

        assert result.score == 0.9
        assert result.keyword_score == 0.8
        assert result.semantic_score == 0.95

    def test_result_to_dict(self):
        """测试结果转字典"""
        result = HybridSearchResult(
            id="r1",
            content="内容",
            score=0.8,
            keyword_score=0.6,
            semantic_score=0.9,
        )

        d = result.to_dict()

        assert d["score"] == 0.8
        assert d["keyword_score"] == 0.6
        assert d["semantic_score"] == 0.9


class TestHybridSearchEngine:
    """测试 HybridSearchEngine"""

    def test_engine_init(self):
        """测试引擎初始化"""
        config = HybridSearchConfig()
        engine = HybridSearchEngine(config)

        assert engine.config.keyword_weight == 0.4
        assert engine.config.semantic_weight == 0.6

    def test_keyword_only_search(self):
        """测试仅关键词搜索"""
        engine = HybridSearchEngine()

        documents = {
            "doc1": "如何创建自定义实体",
            "doc2": "实体碰撞检测方法",
        }

        engine.index(documents)

        results = engine.keyword_only_search("实体", top_k=2)

        assert len(results) <= 2


class TestLlamaIndexConfig:
    """测试 LlamaIndexConfig"""

    def test_default_config(self):
        """测试默认配置"""
        config = LlamaIndexConfig()

        assert config.similarity_top_k == 5
        assert config.response_mode == "compact"
        assert config.streaming is False


class TestLlamaIndexRetriever:
    """测试 LlamaIndexRetriever"""

    def test_retriever_init(self):
        """测试检索器初始化"""
        config = LlamaIndexConfig()
        retriever = LlamaIndexRetriever(config)

        # 检查是否正确检测了 LlamaIndex 可用性
        assert isinstance(retriever.is_available(), bool)

    def test_get_stats(self):
        """测试获取统计信息"""
        retriever = LlamaIndexRetriever()

        stats = retriever.get_stats()

        assert "llama_available" in stats
        assert "index_loaded" in stats


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        # 创建混合搜索引擎
        engine = HybridSearchEngine()

        # 索引文档
        documents = {
            "doc1": "GetEngineType API 用于获取引擎类型",
            "doc2": "创建自定义实体需要注册实体定义",
            "doc3": "实体碰撞事件在服务端触发",
        }

        engine.index(documents)

        # 执行搜索
        results = engine.search("实体", top_k=3)

        assert len(results) <= 3
        # 应该返回相关结果
        assert any("实体" in r.content for r in results)

    def test_weight_adjustment(self):
        """测试权重调整"""
        engine = HybridSearchEngine()

        documents = {
            "doc1": "API 文档说明",
            "doc2": "事件处理方法",
        }

        engine.index(documents)

        # 使用不同的权重
        results1 = engine.search("API", keyword_weight=0.8, semantic_weight=0.2)
        results2 = engine.search("API", keyword_weight=0.2, semantic_weight=0.8)

        # 两种搜索都应该返回结果
        assert len(results1) > 0 or len(results2) > 0


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_create_vector_store(self):
        """测试创建向量存储"""
        from mc_agent_kit.retrieval.vector_store import create_vector_store

        store = create_vector_store(collection_name="test_convenience")
        assert store.config.collection_name == "test_convenience"

    def test_create_semantic_search_engine(self):
        """测试创建语义搜索引擎"""
        from mc_agent_kit.retrieval.semantic_search import create_semantic_search_engine

        engine = create_semantic_search_engine()
        assert engine.config.embedding_model == "all-MiniLM-L6-v2"

    def test_create_hybrid_search_engine(self):
        """测试创建混合搜索引擎"""
        from mc_agent_kit.retrieval.hybrid_search import create_hybrid_search_engine

        engine = create_hybrid_search_engine(
            keyword_weight=0.3,
            semantic_weight=0.7,
        )
        assert engine.config.keyword_weight == 0.3
        assert engine.config.semantic_weight == 0.7

    def test_create_llama_index_retriever(self):
        """测试创建 LlamaIndex 检索器"""
        from mc_agent_kit.retrieval.llama_index import create_llama_index_retriever

        retriever = create_llama_index_retriever()
        assert isinstance(retriever.is_available(), bool)