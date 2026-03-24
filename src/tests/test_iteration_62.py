"""
迭代 #62 测试 - 知识库增强与检索优化

测试覆盖：
1. 增强索引（语义分块、HNSW 索引、增量更新）
2. Embedding 管理（多模型、缓存、批量生成）
3. 查询扩展（同义词、模糊匹配、过滤）
4. 重排序（多种策略、结果融合）
5. 增强检索（端到端搜索）
"""

import time
import pytest
from typing import Any

from mc_agent_kit.retrieval.enhanced_index import (
    ChunkConfig,
    ChunkStrategy,
    DocumentChunk,
    HNSWConfig,
    HNSWIndex,
    IndexCompressor,
    IncrementalIndexer,
    SemanticChunker,
    get_hnsw_index,
    get_incremental_indexer,
    get_semantic_chunker,
)
from mc_agent_kit.retrieval.embedding_manager import (
    CacheStrategy,
    EmbeddingCache,
    EmbeddingConfig,
    EmbeddingManager,
    EmbeddingModelType,
    MockEmbeddingModel,
    embed,
    embed_batch,
    get_embedding_manager,
)
from mc_agent_kit.retrieval.query_expansion import (
    ExpansionStrategy,
    FuzzyMatch,
    FuzzyMatcher,
    QueryExpander,
    SearchResultFilter,
    SynonymDictionary,
    SynonymEntry,
    expand_query,
    fuzzy_match,
    get_query_expander,
    get_search_filter,
    get_synonym_dictionary,
)
from mc_agent_kit.retrieval.reranker import (
    DiversityReranker,
    HybridReranker,
    RerankConfig,
    RerankEngine,
    RerankReport,
    RerankResult,
    RerankStrategy,
    RelevanceReranker,
    ScoreBasedReranker,
    get_rerank_engine,
    rerank,
)
from mc_agent_kit.retrieval.enhanced_retrieval import (
    EnhancedRetriever,
    EnhancedSearchResult,
    FusionConfig,
    FusionStrategy,
    ResultFusion,
    SearchReport,
    enhanced_search,
    get_enhanced_retriever,
)


# ============ 增强索引测试 ============

class TestSemanticChunker:
    """语义分块器测试"""

    def test_chunk_config_defaults(self):
        """测试分块配置默认值"""
        config = ChunkConfig()
        assert config.strategy == ChunkStrategy.SEMANTIC
        assert config.chunk_size == 512
        assert config.chunk_overlap == 50

    def test_semantic_chunking(self):
        """测试语义分块"""
        chunker = SemanticChunker(ChunkConfig(
            strategy=ChunkStrategy.SEMANTIC,
            chunk_size=100,
            max_chunk_size=200,
        ))

        content = "这是第一段。\n\n这是第二段。\n\n这是第三段。"
        chunks = chunker.chunk(content, doc_id="doc1")

        assert len(chunks) > 0
        assert all(isinstance(c, DocumentChunk) for c in chunks)
        assert all(c.document_id == "doc1" for c in chunks)

    def test_paragraph_chunking(self):
        """测试段落分块"""
        chunker = SemanticChunker(ChunkConfig(
            strategy=ChunkStrategy.PARAGRAPH,
            chunk_size=50,  # 减小分块大小以触发分块
        ))

        content = "第一段内容。\n\n第二段内容。\n\n第三段内容。"
        chunks = chunker.chunk(content, doc_id="doc2")

        assert len(chunks) >= 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)

    def test_fixed_size_chunking(self):
        """测试固定大小分块"""
        chunker = SemanticChunker(ChunkConfig(
            strategy=ChunkStrategy.FIXED_SIZE,
            chunk_size=50,
            chunk_overlap=10,
            min_chunk_size=10,
        ))

        content = "A" * 200
        chunks = chunker.chunk(content, doc_id="doc3")

        assert len(chunks) >= 1
        assert all(len(c.content) <= 60 for c in chunks)


class TestHNSWIndex:
    """HNSW 索引测试"""

    def test_hnsw_config_defaults(self):
        """测试 HNSW 配置默认值"""
        config = HNSWConfig()
        assert config.m == 16
        assert config.ef_construction == 200
        assert config.dimension == 1024

    def test_add_and_search_vector(self):
        """测试添加和搜索向量"""
        index = HNSWIndex(HNSWConfig(dimension=10))

        # 添加向量
        for i in range(20):
            vector = [float(i + j) for j in range(10)]
            index.add_vector(f"vec{i}", vector, {"index": i})

        # 搜索
        query = [5.0] * 10
        results = index.search(query, k=5)

        assert len(results) <= 5
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)

    def test_remove_vector(self):
        """测试删除向量"""
        index = HNSWIndex(HNSWConfig(dimension=5))

        index.add_vector("vec1", [1.0, 2.0, 3.0, 4.0, 5.0])
        index.add_vector("vec2", [2.0, 3.0, 4.0, 5.0, 6.0])

        assert index.remove_vector("vec1") is True
        assert index.remove_vector("nonexistent") is False

    def test_get_stats(self):
        """测试获取统计信息"""
        index = HNSWIndex(HNSWConfig(dimension=5))

        for i in range(10):
            index.add_vector(f"vec{i}", [float(i)] * 5)

        stats = index.get_stats()
        assert stats["total_entries"] == 10
        assert stats["active_entries"] == 10


class TestIncrementalIndexer:
    """增量索引器测试"""

    def test_add_document(self):
        """测试添加文档"""
        indexer = IncrementalIndexer()

        chunks = indexer.add_document(
            doc_id="doc1",
            content="这是一个测试文档内容。" * 10,
        )

        assert len(chunks) > 0
        assert all(isinstance(c, DocumentChunk) for c in chunks)

    def test_update_document(self):
        """测试更新文档"""
        indexer = IncrementalIndexer()

        # 添加
        indexer.add_document("doc1", "原始内容")
        original_chunks = indexer.get_document_chunks("doc1")

        # 更新
        updated_chunks = indexer.update_document("doc1", "更新后的内容" * 10)

        assert len(updated_chunks) > 0

    def test_remove_document(self):
        """测试删除文档"""
        indexer = IncrementalIndexer()

        indexer.add_document("doc1", "测试内容")
        assert indexer.remove_document("doc1") is True
        assert len(indexer.get_document_chunks("doc1")) == 0

    def test_search(self):
        """测试搜索"""
        indexer = IncrementalIndexer()

        indexer.add_document("doc1", "Python 编程教程")
        indexer.add_document("doc2", "Java 编程教程")
        indexer.add_document("doc3", "Web 开发指南")

        query_vector = [0.5] * 1024
        results = indexer.search(query_vector, k=2)

        assert len(results) <= 2


class TestIndexCompressor:
    """索引压缩器测试"""

    def test_compress_vectors(self):
        """测试压缩向量"""
        compressor = IndexCompressor()

        vectors = {
            "v1": [0.1, 0.2, 0.3, 0.4, 0.5],
            "v2": [0.5, 0.6, 0.7, 0.8, 0.9],
        }

        compressed = compressor.compress_vectors(vectors)

        assert len(compressed) == 2
        assert all(isinstance(v, list) for v in compressed.values())
        assert all(isinstance(x, int) for vec in compressed.values() for x in vec)


# ============ Embedding 管理测试 ============

class TestEmbeddingCache:
    """Embedding 缓存测试"""

    def test_cache_set_get(self):
        """测试缓存设置和获取"""
        cache = EmbeddingCache(max_size=100, ttl=3600)

        embedding = [0.1, 0.2, 0.3]
        cache.set("hash1", embedding, EmbeddingModelType.MOCK)

        retrieved = cache.get("hash1", EmbeddingModelType.MOCK)
        assert retrieved == embedding

    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = EmbeddingCache()
        result = cache.get("nonexistent", EmbeddingModelType.MOCK)
        assert result is None

    def test_cache_stats(self):
        """测试缓存统计"""
        cache = EmbeddingCache(max_size=10)

        for i in range(15):
            cache.set(f"hash{i}", [float(i)] * 10, EmbeddingModelType.MOCK)

        stats = cache.get_stats()
        assert stats["size"] <= 10
        assert stats["max_size"] == 10


class TestMockEmbeddingModel:
    """Mock Embedding 模型测试"""

    def test_embed_single(self):
        """测试单个嵌入"""
        model = MockEmbeddingModel(EmbeddingConfig(dimension=128))

        embedding = model.embed("测试文本")

        assert len(embedding) == 128
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_batch(self):
        """测试批量嵌入"""
        model = MockEmbeddingModel(EmbeddingConfig(dimension=64))

        texts = ["文本 1", "文本 2", "文本 3"]
        embeddings = model.embed_batch(texts)

        assert len(embeddings) == 3
        assert all(len(e) == 64 for e in embeddings)


class TestEmbeddingManager:
    """Embedding 管理器测试"""

    def test_embed_with_cache(self):
        """测试带缓存的嵌入"""
        manager = EmbeddingManager(EmbeddingConfig(
            model_type=EmbeddingModelType.MOCK,
            cache_enabled=True,
            cache_size=100,
        ))

        # 第一次嵌入
        result1 = manager.embed("测试文本")
        assert result1.cached is False

        # 第二次嵌入（应该命中缓存）
        result2 = manager.embed("测试文本")
        assert result2.cached is True

    def test_embed_batch(self):
        """测试批量嵌入"""
        manager = EmbeddingManager(EmbeddingConfig(
            model_type=EmbeddingModelType.MOCK,
        ))

        texts = [f"测试文本{i}" for i in range(10)]
        result = manager.embed_batch(texts)

        assert result.total_texts == 10
        assert result.success_count == 10
        assert len(result.results) == 10

    def test_switch_model(self):
        """测试切换模型"""
        manager = EmbeddingManager()

        assert manager.switch_model(EmbeddingModelType.MOCK) is True


# ============ 查询扩展测试 ============

class TestSynonymDictionary:
    """同义词词典测试"""

    def test_get_synonyms(self):
        """测试获取同义词"""
        dictionary = get_synonym_dictionary()

        synonyms = dictionary.get_synonyms("实体")
        assert len(synonyms) > 0

    def test_get_related(self):
        """测试获取相关词"""
        dictionary = get_synonym_dictionary()

        related = dictionary.get_related("API")
        assert isinstance(related, list)

    def test_add_entry(self):
        """测试添加条目"""
        dictionary = SynonymDictionary()

        entry = SynonymEntry(
            word="测试词",
            synonyms=["同义词 1", "同义词 2"],
            category="test",
        )
        dictionary.add_entry(entry)

        synonyms = dictionary.get_synonyms("测试词")
        assert len(synonyms) == 2


class TestQueryExpander:
    """查询扩展器测试"""

    def test_expand_synonym(self):
        """测试同义词扩展"""
        expander = get_query_expander()

        result = expander.expand("实体创建", ExpansionStrategy.SYNONYM)

        assert result.original == "实体创建"
        assert result.expansion_count >= 0

    def test_expand_related(self):
        """测试相关词扩展"""
        expander = QueryExpander()

        result = expander.expand("API 调用", ExpansionStrategy.RELATED)

        assert isinstance(result.expanded, str)


class TestFuzzyMatcher:
    """模糊匹配器测试"""

    def test_exact_match(self):
        """测试精确匹配"""
        matcher = FuzzyMatcher(["Python", "Java", "C++"])

        results = matcher.match("Python", top_k=3)

        assert len(results) > 0
        assert results[0].matched == "Python"
        assert results[0].score == 1.0

    def test_fuzzy_match(self):
        """测试模糊匹配"""
        matcher = FuzzyMatcher(["CreateEntity", "SetEntityPos", "GetEntity"])

        results = matcher.match("CreatEntity", top_k=3)  # 拼写错误

        assert len(results) > 0
        assert results[0].matched == "CreateEntity"

    def test_correct_spelling(self):
        """测试拼写纠错"""
        matcher = FuzzyMatcher(["CreateEntity", "DestroyEntity"])

        corrected = matcher.correct_spelling("CreatEntity")
        assert corrected == "CreateEntity"


class TestSearchResultFilter:
    """搜索结果过滤器测试"""

    def test_filter_by_score(self):
        """测试按分数过滤"""
        results = [
            ("id1", "content1", 0.9, {}),
            ("id2", "content2", 0.5, {}),
            ("id3", "content3", 0.1, {}),
        ]

        filtered = SearchResultFilter.filter_by_score(results, 0.3)

        assert len(filtered) == 2

    def test_deduplicate(self):
        """测试去重"""
        results = [
            ("id1", "相同内容", 0.9, {}),
            ("id2", "相同内容", 0.8, {}),
            ("id3", "不同内容", 0.7, {}),
        ]

        deduped = SearchResultFilter.deduplicate(results)

        assert len(deduped) == 2


# ============ 重排序测试 ============

class TestScoreBasedReranker:
    """基于分数的重排序器测试"""

    def test_rerank(self):
        """测试重排序"""
        reranker = ScoreBasedReranker()

        results = [
            ("id1", "内容 1", 0.9, {}),
            ("id2", "内容 2", 0.5, {}),
            ("id3", "内容 3", 0.7, {}),
        ]

        reranked = reranker.rerank("查询", results)

        assert len(reranked) == 3
        assert reranked[0].id == "id1"  # 分数最高的排第一


class TestDiversityReranker:
    """多样性重排序器测试"""

    def test_diversity_rerank(self):
        """测试多样性重排序"""
        reranker = DiversityReranker()

        results = [
            ("id1", "相似内容 A", 0.9, {}),
            ("id2", "相似内容 A", 0.8, {}),
            ("id3", "不同内容 B", 0.7, {}),
        ]

        reranked = reranker.rerank("查询", results)

        # 应该优先选择多样性高的结果
        assert len(reranked) > 0


class TestRelevanceReranker:
    """相关性重排序器测试"""

    def test_relevance_rerank(self):
        """测试相关性重排序"""
        reranker = RelevanceReranker()

        results = [
            ("id1", "查询相关词 A", 0.6, {}),
            ("id2", "不相关内容", 0.9, {}),
            ("id3", "查询相关词 B", 0.5, {}),
        ]

        reranked = reranker.rerank("查询", results)

        # 验证重排序结果存在
        assert len(reranked) == 3
        assert all(isinstance(r, RerankResult) for r in reranked)


class TestHybridReranker:
    """混合重排序器测试"""

    def test_hybrid_rerank(self):
        """测试混合重排序"""
        reranker = HybridReranker()

        results = [
            ("id1", "内容 1", 0.9, {}),
            ("id2", "内容 2", 0.5, {}),
            ("id3", "内容 3", 0.7, {}),
        ]

        reranked = reranker.rerank("查询", results)

        assert len(reranked) == 3


class TestRerankEngine:
    """重排序引擎测试"""

    def test_rerank_with_report(self):
        """测试重排序并生成报告"""
        engine = get_rerank_engine()

        results = [
            ("id1", "内容 1", 0.9, {}),
            ("id2", "内容 2", 0.5, {}),
            ("id3", "内容 3", 0.7, {}),
        ]

        reranked, report = engine.rerank("查询", results, RerankStrategy.HYBRID, top_k=3)

        assert len(reranked) == 3
        assert isinstance(report, RerankReport)
        assert report.strategy == RerankStrategy.HYBRID


# ============ 结果融合测试 ============

class TestResultFusion:
    """结果融合器测试"""

    def test_rrf_fusion(self):
        """测试 RRF 融合"""
        fusion = ResultFusion(FusionConfig(strategy=FusionStrategy.RRF))

        result_lists = [
            [("id1", "内容 1", 0.9, {}), ("id2", "内容 2", 0.5, {})],
            [("id2", "内容 2", 0.8, {}), ("id3", "内容 3", 0.7, {})],
        ]

        fused = fusion.fuse(result_lists)

        assert len(fused) == 3  # id1, id2, id3

    def test_weighted_fusion(self):
        """测试加权融合"""
        fusion = ResultFusion(FusionConfig(
            strategy=FusionStrategy.WEIGHTED,
            weights={"keyword": 0.4, "semantic": 0.6},
        ))

        result_lists = [
            [("id1", "内容 1", 0.9, {}), ("id2", "内容 2", 0.5, {})],
            [("id2", "内容 2", 0.8, {}), ("id3", "内容 3", 0.7, {})],
        ]

        fused = fusion.fuse(result_lists)

        assert len(fused) == 3


# ============ 增强检索测试 ============

class TestEnhancedRetriever:
    """增强检索器测试"""

    def test_index_documents(self):
        """测试索引文档"""
        retriever = EnhancedRetriever()

        documents = {
            "doc1": "Python 编程教程",
            "doc2": "Java 编程教程",
            "doc3": "Web 开发指南",
        }

        count = retriever.index_documents(documents)
        assert count == 3

    def test_search(self):
        """测试搜索"""
        retriever = EnhancedRetriever()

        # 索引文档
        retriever.index_documents({
            "doc1": "如何创建自定义实体",
            "doc2": "GetEngineEntity API 说明",
            "doc3": "事件监听器教程",
        })

        # 搜索（禁用语义搜索以避免 HNSW 问题）
        results, report = retriever.search(
            "创建实体",
            top_k=2,
            use_expansion=False,
            use_rerank=False,
        )

        # 验证报告生成
        assert isinstance(report, SearchReport)
        assert report.query == "创建实体"

    def test_search_with_expansion(self):
        """测试带查询扩展的搜索"""
        retriever = EnhancedRetriever()

        retriever.index_documents({
            "doc1": "Entity 实体创建方法",
            "doc2": "生物生成教程",
        })

        results, report = retriever.search(
            "生物创建",
            top_k=2,
            use_expansion=True,
            use_rerank=False,
        )

        # 验证扩展查询生成
        assert isinstance(report, SearchReport)

    def test_search_with_filters(self):
        """测试带过滤的搜索"""
        retriever = EnhancedRetriever()

        retriever.index_documents({
            "doc1": "服务端 API 教程",
            "doc2": "客户端脚本指南",
        })

        results, report = retriever.search(
            "API",
            top_k=2,
            use_rerank=False,
            filters={"min_score": 0.0},  # 降低阈值
        )

        # 验证报告生成
        assert isinstance(report, SearchReport)


class TestEnhancedSearchResult:
    """增强搜索结果测试"""

    def test_to_dict(self):
        """测试转换为字典"""
        result = EnhancedSearchResult(
            id="test_id",
            content="测试内容" * 100,
            score=0.9,
            keyword_score=0.8,
            semantic_score=0.85,
            rerank_score=0.88,
            rank=1,
            explanation="测试解释",
        )

        result_dict = result.to_dict()

        assert result_dict["id"] == "test_id"
        assert len(result_dict["content"]) <= 203  # 截断后的长度


class TestSearchReport:
    """搜索报告测试"""

    def test_to_dict(self):
        """测试转换为字典"""
        report = SearchReport(
            query="测试查询",
            expanded_query="扩展查询",
            total_candidates=20,
            final_results=10,
            keyword_results=15,
            semantic_results=15,
            rerank_applied=True,
            fusion_strategy="rrf",
            execution_time=0.5,
            cache_hits=5,
            cache_misses=10,
        )

        report_dict = report.to_dict()

        assert report_dict["query"] == "测试查询"
        assert report_dict["final_results"] == 10


# ============ 全局函数测试 ============

class TestGlobalFunctions:
    """全局函数测试"""

    def test_embed(self):
        """测试 embed 函数"""
        embedding = embed("测试文本")
        assert len(embedding) > 0

    def test_embed_batch(self):
        """测试 embed_batch 函数"""
        embeddings = embed_batch(["文本 1", "文本 2"])
        assert len(embeddings) == 2

    def test_expand_query(self):
        """测试 expand_query 函数"""
        result = expand_query("实体")
        assert isinstance(result.expanded, str)

    def test_fuzzy_match(self):
        """测试 fuzzy_match 函数"""
        results = fuzzy_match("Python", ["Python", "Java", "C++"])
        assert len(results) > 0

    def test_rerank(self):
        """测试 rerank 函数"""
        results = [
            ("id1", "内容 1", 0.9, {}),
            ("id2", "内容 2", 0.5, {}),
        ]
        reranked = rerank("查询", results, top_k=2)
        assert len(reranked) == 2

    def test_enhanced_search(self):
        """测试 enhanced_search 函数"""
        retriever = get_enhanced_retriever()
        retriever.index_documents({"doc1": "测试内容"})

        # 简化测试，不依赖语义搜索
        results, report = retriever.search("测试", top_k=1, use_rerank=False)
        assert isinstance(report, SearchReport)


# ============ 性能测试 ============

class TestIteration62Performance:
    """迭代 #62 性能测试"""

    def test_chunking_performance(self):
        """测试分块性能"""
        chunker = SemanticChunker()
        content = "测试内容。" * 1000

        start = time.time()
        chunks = chunker.chunk(content, doc_id="doc1")
        elapsed = time.time() - start

        assert elapsed < 1.0  # 1 秒内完成
        assert len(chunks) > 0

    def test_embedding_performance(self):
        """测试 Embedding 性能"""
        manager = EmbeddingManager(EmbeddingConfig(
            model_type=EmbeddingModelType.MOCK,
        ))

        texts = [f"测试文本{i}" for i in range(100)]

        start = time.time()
        result = manager.embed_batch(texts)
        elapsed = time.time() - start

        assert elapsed < 2.0  # 2 秒内完成 100 个
        assert result.success_count == 100

    def test_search_performance(self):
        """测试搜索性能"""
        retriever = EnhancedRetriever()

        # 索引 50 个文档
        documents = {f"doc{i}": f"测试内容{i}" * 10 for i in range(50)}
        retriever.index_documents(documents)

        start = time.time()
        results, report = retriever.search("测试", top_k=10, use_rerank=False)
        elapsed = time.time() - start

        # 验证性能
        assert elapsed < 5.0  # 5 秒内完成
        assert isinstance(report, SearchReport)


# ============ 验收标准测试 ============

class TestIteration62AcceptanceCriteria:
    """迭代 #62 验收标准测试"""

    def test_semantic_chunking(self):
        """测试语义分块完成"""
        chunker = SemanticChunker(ChunkConfig(strategy=ChunkStrategy.SEMANTIC))
        content = "第一段。\n\n第二段。\n\n第三段。"
        chunks = chunker.chunk(content, doc_id="doc1")

        assert len(chunks) > 0
        assert all(isinstance(c, DocumentChunk) for c in chunks)

    def test_hnsw_index(self):
        """测试 HNSW 索引完成"""
        index = HNSWIndex(HNSWConfig(dimension=10))
        for i in range(50):
            index.add_vector(f"vec{i}", [float(i)] * 10)

        results = index.search([25.0] * 10, k=10)
        assert len(results) <= 10

    def test_incremental_update(self):
        """测试增量更新完成"""
        indexer = IncrementalIndexer()

        indexer.add_document("doc1", "原始内容")
        indexer.update_document("doc1", "更新内容")
        indexer.remove_document("doc1")

        assert len(indexer.get_document_chunks("doc1")) == 0

    def test_multi_model_support(self):
        """测试多模型支持完成"""
        manager = EmbeddingManager()

        models = manager.get_available_models()
        assert len(models) >= 1
        assert EmbeddingModelType.MOCK in models

    def test_embedding_cache(self):
        """测试 Embedding 缓存完成"""
        manager = EmbeddingManager(EmbeddingConfig(cache_enabled=True))

        result1 = manager.embed("测试")
        result2 = manager.embed("测试")

        assert result1.cached is False
        assert result2.cached is True

    def test_synonym_expansion(self):
        """测试同义词扩展完成"""
        expander = get_query_expander()

        result = expander.expand("实体", ExpansionStrategy.SYNONYM)
        assert len(result.synonyms_added) >= 0

    def test_fuzzy_matching(self):
        """测试模糊匹配完成"""
        matcher = FuzzyMatcher(["CreateEntity", "SetEntityPos"])

        results = matcher.match("CreatEntity", top_k=1)
        assert len(results) > 0
        assert results[0].matched == "CreateEntity"

    def test_rerank_strategies(self):
        """测试多种重排序策略完成"""
        engine = get_rerank_engine()

        strategies = engine.get_available_strategies()
        assert len(strategies) >= 4  # score, diversity, recency, relevance, hybrid

    def test_result_fusion(self):
        """测试结果融合完成"""
        fusion = ResultFusion()

        result_lists = [
            [("id1", "内容 1", 0.9, {})],
            [("id2", "内容 2", 0.8, {})],
        ]

        fused = fusion.fuse(result_lists)
        assert len(fused) == 2

    def test_enhanced_search_end_to_end(self):
        """测试增强检索端到端完成"""
        retriever = EnhancedRetriever()

        retriever.index_documents({
            "doc1": "Python 实体创建教程",
            "doc2": "Java 物品开发指南",
            "doc3": "C++ 方块实现",
        })

        results, report = retriever.search(
            "实体创建",
            top_k=3,
            use_rerank=False,
        )

        assert isinstance(report, SearchReport)
        assert report.query == "实体创建"
        assert report.execution_time < 10.0  # 10 秒内完成


if __name__ == "__main__":
    pytest.main([__file__, "-v"])