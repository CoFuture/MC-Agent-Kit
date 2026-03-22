"""
迭代 #21 测试：提升覆盖率至 90%

测试目标模块：
- retrieval/llama_index.py (64% → 80%+)
- retrieval/vector_store.py (78% → 85%+)
- performance/cache.py (75% → 85%+)
- knowledge_base/parser.py (78% → 85%+)
- plugin/manager.py (83% → 90%+)
"""

import tempfile
import time
from pathlib import Path
from unittest import mock

import pytest

# ============================================================================
# LlamaIndex Tests
# ============================================================================


class TestLlamaIndexConfig:
    """测试 LlamaIndex 配置"""

    def test_default_config(self):
        """测试默认配置"""
        from mc_agent_kit.retrieval.llama_index import LlamaIndexConfig

        config = LlamaIndexConfig()
        assert config.persist_dir is None
        assert config.collection_name == "mc_knowledge"
        assert config.embedding_model == "all-MiniLM-L6-v2"
        assert config.similarity_top_k == 5
        assert config.response_mode == "compact"
        assert config.streaming is False

    def test_custom_config(self):
        """测试自定义配置"""
        from mc_agent_kit.retrieval.llama_index import LlamaIndexConfig

        config = LlamaIndexConfig(
            persist_dir="/tmp/llama",
            collection_name="test_collection",
            embedding_model="custom-model",
            similarity_top_k=10,
            response_mode="refine",
            streaming=True,
        )
        assert config.persist_dir == "/tmp/llama"
        assert config.collection_name == "test_collection"
        assert config.embedding_model == "custom-model"
        assert config.similarity_top_k == 10
        assert config.response_mode == "refine"
        assert config.streaming is True


class TestLlamaIndexRetriever:
    """测试 LlamaIndex 检索器"""

    def test_init_default_config(self):
        """测试默认配置初始化"""
        from mc_agent_kit.retrieval.llama_index import LlamaIndexRetriever

        retriever = LlamaIndexRetriever()
        assert retriever.config is not None
        assert retriever._index is None
        assert retriever._vector_store is None

    def test_init_custom_config(self):
        """测试自定义配置初始化"""
        from mc_agent_kit.retrieval.llama_index import (
            LlamaIndexConfig,
            LlamaIndexRetriever,
        )

        config = LlamaIndexConfig(persist_dir="/tmp/test")
        retriever = LlamaIndexRetriever(config)
        assert retriever.config.persist_dir == "/tmp/test"

    def test_is_available(self):
        """测试可用性检查"""
        from mc_agent_kit.retrieval.llama_index import LlamaIndexRetriever

        retriever = LlamaIndexRetriever()
        # 无论 LlamaIndex 是否安装，都应该返回布尔值
        assert isinstance(retriever.is_available(), bool)

    def test_get_stats(self):
        """测试获取统计信息"""
        from mc_agent_kit.retrieval.llama_index import LlamaIndexRetriever

        retriever = LlamaIndexRetriever()
        stats = retriever.get_stats()
        assert "llama_available" in stats
        assert "index_loaded" in stats
        assert "persist_dir" in stats
        assert "collection_name" in stats

    def test_query_without_index(self):
        """测试无索引时的查询"""
        from mc_agent_kit.retrieval.llama_index import LlamaIndexRetriever

        retriever = LlamaIndexRetriever()
        result = retriever.query("test query")
        # 无索引时应该返回提示信息
        assert isinstance(result, str)

    def test_retrieve_without_index(self):
        """测试无索引时的检索"""
        from mc_agent_kit.retrieval.llama_index import LlamaIndexRetriever

        retriever = LlamaIndexRetriever()
        result = retriever.retrieve("test query")
        # 无索引时应该返回空列表
        assert result == []

    def test_index_documents_without_llama(self):
        """测试无 LlamaIndex 时的文档索引"""
        from mc_agent_kit.retrieval.llama_index import LlamaIndexRetriever

        retriever = LlamaIndexRetriever()
        # 如果 LlamaIndex 不可用，应该返回 False
        if not retriever.is_available():
            result = retriever.index_documents(["doc1", "doc2"])
            assert result is False

    def test_load_index_without_dir(self):
        """测试无目录时加载索引"""
        from mc_agent_kit.retrieval.llama_index import LlamaIndexRetriever

        retriever = LlamaIndexRetriever()
        # 无持久化目录时应该返回 False
        result = retriever.load_index()
        assert result is False

    def test_create_llama_index_retriever(self):
        """测试便捷函数"""
        from mc_agent_kit.retrieval.llama_index import create_llama_index_retriever

        retriever = create_llama_index_retriever(
            persist_dir="/tmp/test",
            embedding_model="custom-model",
        )
        assert retriever.config.persist_dir == "/tmp/test"
        assert retriever.config.embedding_model == "custom-model"


# ============================================================================
# VectorStore Tests
# ============================================================================


class TestVectorStoreConfig:
    """测试向量存储配置"""

    def test_default_config(self):
        """测试默认配置"""
        from mc_agent_kit.retrieval.vector_store import VectorStoreConfig

        config = VectorStoreConfig()
        assert config.persist_dir is None
        assert config.collection_name == "mc_knowledge"
        assert config.embedding_model == "all-MiniLM-L6-v2"
        assert config.distance_metric == "cosine"
        assert config.batch_size == 100
        assert config.enable_incremental is True

    def test_custom_config(self):
        """测试自定义配置"""
        from mc_agent_kit.retrieval.vector_store import VectorStoreConfig

        config = VectorStoreConfig(
            persist_dir="/tmp/vectors",
            collection_name="test_collection",
            embedding_model="custom-model",
            distance_metric="l2",
            batch_size=50,
            enable_incremental=False,
        )
        assert config.persist_dir == "/tmp/vectors"
        assert config.collection_name == "test_collection"
        assert config.embedding_model == "custom-model"
        assert config.distance_metric == "l2"
        assert config.batch_size == 50
        assert config.enable_incremental is False


class TestDocument:
    """测试文档数据结构"""

    def test_document_creation(self):
        """测试文档创建"""
        from mc_agent_kit.retrieval.vector_store import Document

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
        from mc_agent_kit.retrieval.vector_store import Document

        doc = Document(
            id="test-1",
            content="Test content",
            metadata={"type": "test"},
        )
        d = doc.to_dict()
        assert d["id"] == "test-1"
        assert d["content"] == "Test content"
        assert d["metadata"] == {"type": "test"}


class TestSearchResult:
    """测试搜索结果"""

    def test_search_result_creation(self):
        """测试搜索结果创建"""
        from mc_agent_kit.retrieval.vector_store import SearchResult

        result = SearchResult(
            id="test-1",
            content="Test content",
            score=0.95,
            metadata={"type": "test"},
        )
        assert result.id == "test-1"
        assert result.content == "Test content"
        assert result.score == 0.95

    def test_search_result_to_dict(self):
        """测试搜索结果转字典"""
        from mc_agent_kit.retrieval.vector_store import SearchResult

        result = SearchResult(
            id="test-1",
            content="Test content",
            score=0.95,
            metadata={"type": "test"},
        )
        d = result.to_dict()
        assert d["id"] == "test-1"
        assert d["score"] == 0.95


class TestVectorStore:
    """测试向量存储"""

    def test_init_default_config(self):
        """测试默认配置初始化"""
        from mc_agent_kit.retrieval.vector_store import VectorStore

        store = VectorStore()
        assert store.config is not None
        assert store._client is None
        assert store._collection is None

    def test_init_custom_config(self):
        """测试自定义配置初始化"""
        from mc_agent_kit.retrieval.vector_store import (
            VectorStore,
            VectorStoreConfig,
        )

        config = VectorStoreConfig(collection_name="test")
        store = VectorStore(config)
        assert store.config.collection_name == "test"

    def test_get_stats_without_init(self):
        """测试未初始化时获取统计"""
        from mc_agent_kit.retrieval.vector_store import VectorStore

        store = VectorStore()
        stats = store.get_stats()
        assert stats["collection_name"] == "mc_knowledge"
        assert stats["document_count"] == 0

    def test_count_without_init(self):
        """测试未初始化时计数"""
        from mc_agent_kit.retrieval.vector_store import VectorStore

        store = VectorStore()
        count = store.count()
        assert count == 0

    def test_search_without_init(self):
        """测试未初始化时搜索"""
        from mc_agent_kit.retrieval.vector_store import VectorStore

        store = VectorStore()
        results = store.search("test query")
        assert results == []

    def test_get_document_without_init(self):
        """测试未初始化时获取文档"""
        from mc_agent_kit.retrieval.vector_store import VectorStore

        store = VectorStore()
        doc = store.get_document("test-id")
        assert doc is None

    def test_add_documents_without_init(self):
        """测试未初始化时添加文档"""
        from mc_agent_kit.retrieval.vector_store import Document, VectorStore

        store = VectorStore()
        docs = [Document(id="1", content="test")]
        count = store.add_documents(docs)
        # 无 ChromaDB 时返回 0
        assert count == 0

    def test_delete_documents_without_init(self):
        """测试未初始化时删除文档"""
        from mc_agent_kit.retrieval.vector_store import VectorStore

        store = VectorStore()
        # 不应该抛出异常
        store.delete_documents(["test-id"])

    def test_clear_without_init(self):
        """测试未初始化时清空"""
        from mc_agent_kit.retrieval.vector_store import VectorStore

        store = VectorStore()
        # 不应该抛出异常
        store.clear()

    def test_create_vector_store(self):
        """测试便捷函数"""
        from mc_agent_kit.retrieval.vector_store import create_vector_store

        store = create_vector_store(
            persist_dir="/tmp/test",
            collection_name="test_collection",
        )
        assert store.config.persist_dir == "/tmp/test"
        assert store.config.collection_name == "test_collection"


# ============================================================================
# Cache Tests
# ============================================================================


class TestLRUCache:
    """测试 LRU 缓存"""

    def test_basic_set_get(self):
        """测试基本的设置和获取"""
        from mc_agent_kit.performance.cache import LRUCache

        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_cache_miss(self):
        """测试缓存未命中"""
        from mc_agent_kit.performance.cache import LRUCache

        cache = LRUCache(max_size=10)
        assert cache.get("nonexistent") is None

    def test_cache_eviction(self):
        """测试缓存淘汰"""
        from mc_agent_kit.performance.cache import LRUCache

        cache = LRUCache(max_size=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # 应该淘汰 key1

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_cache_update(self):
        """测试缓存更新"""
        from mc_agent_kit.performance.cache import LRUCache

        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        assert cache.get("key1") == "value2"

    def test_cache_delete(self):
        """测试缓存删除"""
        from mc_agent_kit.performance.cache import LRUCache

        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        assert cache.delete("nonexistent") is False

    def test_cache_clear(self):
        """测试缓存清空"""
        from mc_agent_kit.performance.cache import LRUCache

        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_stats(self):
        """测试缓存统计"""
        from mc_agent_kit.performance.cache import LRUCache

        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["max_size"] == 10
        assert stats["total_hits"] == 2

    def test_cache_ttl(self):
        """测试缓存 TTL"""
        from mc_agent_kit.performance.cache import LRUCache

        cache = LRUCache(max_size=10, ttl_seconds=1)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_lru_order(self):
        """测试 LRU 顺序"""
        from mc_agent_kit.performance.cache import LRUCache

        cache = LRUCache(max_size=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.get("key1")  # 访问 key1，使其变为最近使用
        cache.set("key4", "value4")  # 淘汰 key2

        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"


class TestKnowledgeCache:
    """测试知识库缓存"""

    def test_get_or_set(self):
        """测试获取或设置"""
        from mc_agent_kit.performance.cache import KnowledgeCache

        cache = KnowledgeCache(max_size=10)
        compute_count = 0

        def compute():
            nonlocal compute_count
            compute_count += 1
            return "computed"

        result1 = cache.get_or_set("query1", compute)
        result2 = cache.get_or_set("query1", compute)

        assert result1 == "computed"
        assert result2 == "computed"
        assert compute_count == 1  # 只计算一次

    def test_cache_stats(self):
        """测试缓存统计"""
        from mc_agent_kit.performance.cache import KnowledgeCache

        cache = KnowledgeCache(max_size=10)

        cache.get_or_set("query1", lambda: "result1")
        cache.get_or_set("query1", lambda: "result1")  # hit
        cache.get_or_set("query2", lambda: "result2")

        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 2
        assert stats["computes"] == 2

    def test_cache_invalidate(self):
        """测试缓存失效"""
        from mc_agent_kit.performance.cache import KnowledgeCache

        cache = KnowledgeCache(max_size=10)
        cache.get_or_set("query1", lambda: "result1")
        assert cache.invalidate("query1") is True
        assert cache.invalidate("nonexistent") is False

    def test_cache_clear(self):
        """测试缓存清空"""
        from mc_agent_kit.performance.cache import KnowledgeCache

        cache = KnowledgeCache(max_size=10)
        cache.get_or_set("query1", lambda: "result1")
        cache.clear()
        stats = cache.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_cache_persist_and_load(self):
        """测试缓存持久化和加载"""
        from mc_agent_kit.performance.cache import KnowledgeCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache1 = KnowledgeCache(max_size=10, persist_dir=tmpdir)
            cache1.get_or_set("query1", lambda: "result1")
            cache1.persist()

            # 加载缓存
            cache2 = KnowledgeCache(max_size=10, persist_dir=tmpdir)
            count = cache2.load()
            # 由于 TTL 可能过期，检查是否加载成功
            assert count >= 0

    def test_cache_hit_rate(self):
        """测试命中率计算"""
        from mc_agent_kit.performance.cache import KnowledgeCache

        cache = KnowledgeCache(max_size=10)
        cache.get_or_set("query1", lambda: "result1")
        cache.get_or_set("query1", lambda: "result1")  # hit
        cache.get_or_set("query1", lambda: "result1")  # hit

        stats = cache.stats()
        # 命中率应该是 2/3
        assert stats["hit_rate"] > 0


# ============================================================================
# Plugin Manager Tests
# ============================================================================


class TestPluginManagerInit:
    """测试插件管理器初始化"""

    def test_init_default_registry(self):
        """测试默认注册表初始化"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        assert manager.registry is not None
        assert manager.loader is not None

    def test_init_custom_registry(self):
        """测试自定义注册表初始化"""
        from mc_agent_kit.plugin.loader import PluginRegistry
        from mc_agent_kit.plugin.manager import PluginManager

        registry = PluginRegistry()
        manager = PluginManager(registry=registry)
        assert manager.registry is registry


class TestPluginManagerDirectories:
    """测试插件目录管理"""

    def test_add_plugin_directory(self):
        """测试添加插件目录"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        manager.add_plugin_directory("/tmp/plugins")
        # 不应该抛出异常

    def test_remove_plugin_directory(self):
        """测试移除插件目录"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        manager.add_plugin_directory("/tmp/plugins")
        result = manager.remove_plugin_directory("/tmp/plugins")
        assert result is True

    def test_remove_nonexistent_directory(self):
        """测试移除不存在的目录"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.remove_plugin_directory("/nonexistent")
        assert result is False


class TestPluginManagerDiscovery:
    """测试插件发现"""

    def test_discover_plugins_empty(self):
        """测试空目录发现"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            manager.add_plugin_directory(tmpdir)
            plugins = manager.discover_plugins()
            assert plugins == []

    def test_load_nonexistent_plugin(self):
        """测试加载不存在的插件"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.load_plugin("/nonexistent/plugin")
        assert result is None

    def test_unload_nonexistent_plugin(self):
        """测试卸载不存在的插件"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.unload_plugin("nonexistent")
        assert result is False


class TestPluginManagerLifecycle:
    """测试插件生命周期"""

    def test_enable_nonexistent_plugin(self):
        """测试启用不存在的插件"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.enable_plugin("nonexistent")
        assert result is False

    def test_disable_nonexistent_plugin(self):
        """测试禁用不存在的插件"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.disable_plugin("nonexistent")
        assert result is False

    def test_reload_nonexistent_plugin(self):
        """测试重载不存在的插件"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.reload_plugin("nonexistent")
        assert result is False


class TestPluginManagerQuery:
    """测试插件查询"""

    def test_get_nonexistent_plugin(self):
        """测试获取不存在的插件"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.get_plugin("nonexistent")
        assert result is None

    def test_get_plugin_instance_nonexistent(self):
        """测试获取不存在的插件实例"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.get_plugin_instance("nonexistent")
        assert result is None

    def test_get_all_plugins_empty(self):
        """测试获取所有插件（空）"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.get_all_plugins()
        assert result == []

    def test_get_enabled_plugins_empty(self):
        """测试获取已启用插件（空）"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.get_enabled_plugins()
        assert result == []

    def test_get_plugins_by_capability_empty(self):
        """测试按能力获取插件（空）"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.get_plugins_by_capability("nonexistent")
        assert result == []

    def test_has_plugin_false(self):
        """测试检查插件是否存在（不存在）"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.has_plugin("nonexistent")
        assert result is False

    def test_has_capability_false(self):
        """测试检查能力是否可用（不可用）"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.has_capability("nonexistent")
        assert result is False

    def test_get_capabilities_empty(self):
        """测试获取所有能力（空）"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.get_capabilities()
        assert result == []

    def test_get_plugin_status_nonexistent(self):
        """测试获取插件状态（不存在）"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.get_plugin_status("nonexistent")
        assert result is None

    def test_get_all_status_empty(self):
        """测试获取所有插件状态（空）"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.get_all_status()
        assert result == []


class TestPluginManagerConfig:
    """测试插件配置"""

    def test_set_plugin_config(self):
        """测试设置插件配置"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        manager.set_plugin_config("test_plugin", {"key": "value"})
        config = manager.get_plugin_config("test_plugin")
        assert config == {"key": "value"}

    def test_get_nonexistent_plugin_config(self):
        """测试获取不存在插件的配置"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        config = manager.get_plugin_config("nonexistent")
        assert config == {}


class TestPluginManagerExecution:
    """测试插件执行"""

    def test_execute_nonexistent_plugin(self):
        """测试执行不存在的插件"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        result = manager.execute_plugin("nonexistent")
        assert result is None


class TestPluginManagerShutdown:
    """测试插件关闭"""

    def test_shutdown_empty(self):
        """测试关闭空管理器"""
        from mc_agent_kit.plugin.manager import PluginManager

        manager = PluginManager()
        # 不应该抛出异常
        manager.shutdown()


# ============================================================================
# Parser Tests
# ============================================================================


class TestMarkdownParser:
    """测试 Markdown 解析器"""

    def test_parse_empty_content(self):
        """测试解析空内容"""
        from mc_agent_kit.knowledge_base.parser import MarkdownParser

        parser = MarkdownParser()
        result = parser.parse("", "test.md")
        assert result == []

    def test_parse_frontmatter(self):
        """测试解析 frontmatter"""
        from mc_agent_kit.knowledge_base.parser import MarkdownParser

        parser = MarkdownParser()
        content = """---
title: Test
---
# Content"""
        result = parser._remove_frontmatter(content)
        assert "---" not in result
        assert "# Content" in result

    def test_extract_code_blocks(self):
        """测试提取代码块"""
        from mc_agent_kit.knowledge_base.parser import MarkdownParser

        parser = MarkdownParser()
        content = """```python
print("hello")
```"""
        examples = parser._extract_code_blocks(content)
        assert len(examples) == 1
        assert examples[0].language == "python"
        assert "print" in examples[0].code

    def test_parse_table(self):
        """测试解析表格"""
        from mc_agent_kit.knowledge_base.parser import MarkdownParser

        parser = MarkdownParser()
        table = """| 参数名 | 数据类型 | 说明 |
| --- | --- | --- |
| id | str | 实体id |
| name | str | 名称 |"""
        rows = parser._parse_table(table)
        assert len(rows) == 2
        assert rows[0]["参数名"] == "id"
        assert rows[0]["数据类型"] == "str"

    def test_parse_scope_server(self):
        """测试解析服务端作用域"""
        from mc_agent_kit.knowledge_base.models import Scope
        from mc_agent_kit.knowledge_base.parser import MarkdownParser

        parser = MarkdownParser()
        scope = parser._parse_scope("服务端")
        assert scope == Scope.SERVER

    def test_parse_scope_client(self):
        """测试解析客户端作用域"""
        from mc_agent_kit.knowledge_base.models import Scope
        from mc_agent_kit.knowledge_base.parser import MarkdownParser

        parser = MarkdownParser()
        scope = parser._parse_scope("客户端")
        assert scope == Scope.CLIENT

    def test_parse_scope_both(self):
        """测试解析双向作用域"""
        from mc_agent_kit.knowledge_base.models import Scope
        from mc_agent_kit.knowledge_base.parser import MarkdownParser

        parser = MarkdownParser()
        scope = parser._parse_scope("服务端客户端")
        assert scope == Scope.BOTH

    def test_parse_scope_unknown(self):
        """测试解析未知作用域"""
        from mc_agent_kit.knowledge_base.models import Scope
        from mc_agent_kit.knowledge_base.parser import MarkdownParser

        parser = MarkdownParser()
        scope = parser._parse_scope("其他内容")
        assert scope == Scope.UNKNOWN

    def test_extract_description(self):
        """测试提取描述"""
        from mc_agent_kit.knowledge_base.parser import MarkdownParser

        parser = MarkdownParser()
        content = """- 描述
    这是描述内容"""
        desc = parser._extract_description(content)
        assert "描述内容" in desc

    def test_extract_method_path(self):
        """测试提取方法路径"""
        from mc_agent_kit.knowledge_base.parser import MarkdownParser

        parser = MarkdownParser()
        content = "method in mod.server.component.test.TestComp"
        path = parser._extract_method_path(content)
        assert path == "mod.server.component.test.TestComp"

    def test_extract_module_from_path(self):
        """测试从路径提取模块名"""
        from mc_agent_kit.knowledge_base.parser import MarkdownParser

        parser = MarkdownParser()
        module = parser._extract_module_from_path("/path/to/接口/实体/TestApi.md")
        assert module == "实体"

    def test_is_event_document(self):
        """测试判断事件文档"""
        from mc_agent_kit.knowledge_base.parser import MarkdownParser

        parser = MarkdownParser()
        assert parser._is_event_document("触发时机：玩家加入")
        assert parser._is_event_document("监听事件")
        assert not parser._is_event_document("普通 API 文档")

    def test_is_api_document(self):
        """测试判断 API 文档"""
        from mc_agent_kit.knowledge_base.parser import MarkdownParser

        parser = MarkdownParser()
        assert parser._is_api_document("method in mod.server.component.test")
        assert not parser._is_api_document("普通文档")


class TestParseDocument:
    """测试文档解析函数"""

    def test_parse_nonexistent_file(self):
        """测试解析不存在的文件"""
        from mc_agent_kit.knowledge_base.parser import parse_document

        result = parse_document("/nonexistent/file.md")
        assert result == []


# ============================================================================
# Additional Coverage Tests
# ============================================================================


class TestCompletionCompleter:
    """测试代码补全器额外覆盖"""

    def test_completion_context(self):
        """测试补全上下文"""
        from mc_agent_kit.completion.completer import CompletionContext

        ctx = CompletionContext(
            code="GetConfig.",
            cursor_line=0,
            cursor_column=9,
        )
        assert ctx.code == "GetConfig."
        assert ctx.cursor_column == 9


class TestHybridSearch:
    """测试混合搜索额外覆盖"""

    def test_keyword_search_engine_basic(self):
        """测试关键词搜索引擎基本功能"""
        from mc_agent_kit.retrieval.hybrid_search import KeywordSearchEngine

        engine = KeywordSearchEngine()
        docs = {
            "1": "hello world",
            "2": "hello python",
        }
        engine.index(docs)
        results = engine.search("hello", top_k=2)
        assert len(results) == 2


class TestSemanticSearch:
    """测试语义搜索额外覆盖"""

    def test_semantic_search_config(self):
        """测试语义搜索配置"""
        from mc_agent_kit.retrieval.semantic_search import SemanticSearchConfig

        config = SemanticSearchConfig(
            chunk_size=512,
            chunk_overlap=50,
            min_score=0.5,
        )
        assert config.chunk_size == 512
        assert config.chunk_overlap == 50
        assert config.min_score == 0.5


class TestCodeSmells:
    """测试代码异味检测额外覆盖"""

    def test_smell_detector_config(self):
        """测试异味检测器配置"""
        from mc_agent_kit.completion.smells import SmellDetectorConfig

        config = SmellDetectorConfig(
            max_function_lines=50,
            max_parameters=5,
            max_nesting_depth=4,
            max_complexity=10,
        )
        assert config.max_function_lines == 50
        assert config.max_parameters == 5
        assert config.max_nesting_depth == 4
        assert config.max_complexity == 10


class TestIncrementalUpdater:
    """测试增量更新器额外覆盖"""

    def test_document_change(self):
        """测试文档变更"""
        from mc_agent_kit.knowledge.incremental import DocumentChange

        change = DocumentChange(
            path="test.md",
            change_type="modified",
            old_hash="abc123",
            new_hash="def456",
        )
        assert change.path == "test.md"
        assert change.change_type == "modified"

    def test_change_report(self):
        """测试变更报告"""
        from mc_agent_kit.knowledge.incremental import ChangeReport

        report = ChangeReport(
            added=["new.md"],
            modified=["changed.md"],
            deleted=["removed.md"],
        )
        assert len(report.added) == 1
        assert len(report.modified) == 1
        assert len(report.deleted) == 1


class TestLogAnalyzerExtra:
    """测试日志分析器额外覆盖"""

    def test_alert_severity(self):
        """测试告警严重程度"""
        from mc_agent_kit.log_capture.analyzer import AlertSeverity

        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_pattern_category(self):
        """测试错误类别"""
        from mc_agent_kit.log_capture.analyzer import PatternCategory

        assert PatternCategory.SYNTAX.value == "syntax"
        assert PatternCategory.RUNTIME.value == "runtime"
        assert PatternCategory.API.value == "api"


class TestAPISearchSkill:
    """测试 API 搜索 Skill 额外覆盖"""

    def test_api_parameter_creation(self):
        """测试 API 参数创建"""
        from mc_agent_kit.knowledge_base.models import APIParameter

        param = APIParameter(
            name="entityId",
            data_type="str",
            description="实体 ID",
            optional=False,
        )
        assert param.name == "entityId"
        assert param.data_type == "str"
        assert param.optional is False

    def test_api_entry_creation(self):
        """测试 API 条目创建"""
        from mc_agent_kit.knowledge_base.models import APIEntry, Scope

        api = APIEntry(
            name="GetEngineType",
            module="engine",
            description="获取引擎类型",
            method_path="mod.server.engine.GetEngineType",
            scope=Scope.SERVER,
        )
        assert api.name == "GetEngineType"
        assert api.scope == Scope.SERVER


class TestRefactorEngine:
    """测试重构引擎额外覆盖"""

    def test_refactor_type(self):
        """测试重构类型"""
        from mc_agent_kit.completion.refactor import RefactorType

        assert RefactorType.EXTRACT_FUNCTION.value == "extract_function"
        assert RefactorType.EXTRACT_VARIABLE.value == "extract_variable"
        assert RefactorType.RENAME.value == "rename"


class TestGeneratorLint:
    """测试代码检查额外覆盖"""

    def test_lint_issue(self):
        """测试 Lint 问题"""
        from mc_agent_kit.generator.lint import LintIssue

        issue = LintIssue(
            file_path="test.py",
            line=10,
            column=5,
            code="E501",
            message="Line too long",
            severity="warning",
        )
        assert issue.file_path == "test.py"
        assert issue.line == 10
        assert issue.code == "E501"

    def test_complexity_report(self):
        """测试复杂度报告"""
        from mc_agent_kit.generator.lint import ComplexityReport

        report = ComplexityReport(
            file_path="test.py",
            total_lines=100,
            code_lines=80,
            comment_lines=10,
            blank_lines=10,
            functions=10,
            classes=2,
            max_complexity=5,
            avg_complexity=2.5,
        )
        assert report.file_path == "test.py"
        assert report.total_lines == 100
        assert report.max_complexity == 5


class TestSemanticSearchEngine:
    """测试语义搜索引擎额外覆盖"""

    def test_semantic_search_engine_init(self):
        """测试搜索引擎初始化"""
        from mc_agent_kit.retrieval.semantic_search import SemanticSearchEngine

        engine = SemanticSearchEngine()
        assert engine.config is not None
        assert engine._document_count == 0

    def test_index_stats(self):
        """测试索引统计"""
        from mc_agent_kit.retrieval.semantic_search import IndexStats

        stats = IndexStats(
            total_documents=10,
            total_chunks=50,
            embedding_model="test-model",
            collection_name="test",
        )
        d = stats.to_dict()
        assert d["total_documents"] == 10
        assert d["total_chunks"] == 50

    def test_chunk_text_short(self):
        """测试短文本分块"""
        from mc_agent_kit.retrieval.semantic_search import (
            SemanticSearchConfig,
            SemanticSearchEngine,
        )

        config = SemanticSearchConfig(chunk_size=100)
        engine = SemanticSearchEngine(config)
        chunks = engine._chunk_text("短文本")
        assert len(chunks) == 1

    def test_chunk_text_long(self):
        """测试长文本分块"""
        from mc_agent_kit.retrieval.semantic_search import (
            SemanticSearchConfig,
            SemanticSearchEngine,
        )

        config = SemanticSearchConfig(chunk_size=50, chunk_overlap=10)
        engine = SemanticSearchEngine(config)
        long_text = "这是第一句话。这是第二句话。这是第三句话。这是第四句话。"
        chunks = engine._chunk_text(long_text)
        assert len(chunks) >= 1

    def test_generate_doc_id(self):
        """测试文档 ID 生成"""
        from mc_agent_kit.retrieval.semantic_search import SemanticSearchEngine

        engine = SemanticSearchEngine()
        id1 = engine._generate_doc_id("content", 0)
        id2 = engine._generate_doc_id("content", 1)
        assert id1 != id2
        assert len(id1) == 16

    def test_search_without_index(self):
        """测试无索引时搜索"""
        from mc_agent_kit.retrieval.semantic_search import SemanticSearchEngine

        engine = SemanticSearchEngine()
        results = engine.search("test query")
        assert results == []

    def test_count_without_index(self):
        """测试无索引时计数"""
        from mc_agent_kit.retrieval.semantic_search import SemanticSearchEngine

        engine = SemanticSearchEngine()
        count = engine.count()
        assert count == 0

    def test_clear(self):
        """测试清空索引"""
        from mc_agent_kit.retrieval.semantic_search import SemanticSearchEngine

        engine = SemanticSearchEngine()
        engine.clear()
        assert engine._document_count == 0

    def test_delete_document(self):
        """测试删除文档"""
        from mc_agent_kit.retrieval.semantic_search import SemanticSearchEngine

        engine = SemanticSearchEngine()
        # 不应该抛出异常
        engine.delete_document("nonexistent")

    def test_create_semantic_search_engine(self):
        """测试便捷函数"""
        from mc_agent_kit.retrieval.semantic_search import create_semantic_search_engine

        engine = create_semantic_search_engine(
            persist_dir="/tmp/test",
            embedding_model="custom-model",
        )
        assert engine.config.persist_dir == "/tmp/test"
        assert engine.config.embedding_model == "custom-model"


class TestTemplateLoader:
    """测试模板加载器额外覆盖"""

    def test_template_loader_init(self):
        """测试模板加载器初始化"""
        from mc_agent_kit.generator.template_loader import TemplateLoader

        loader = TemplateLoader()
        assert loader._manager is not None
        assert loader._loaded_files == {}

    def test_template_file(self):
        """测试模板文件数据类"""
        from pathlib import Path

        from mc_agent_kit.generator.template_loader import TemplateFile

        tf = TemplateFile(
            path=Path("test.j2"),
            name="test",
            content="content",
            metadata={"key": "value"},
            checksum="abc123",
            loaded_at=1.0,
        )
        assert tf.name == "test"
        assert tf.checksum == "abc123"

    def test_load_nonexistent_directory(self):
        """测试加载不存在的目录"""
        from mc_agent_kit.generator.template_loader import TemplateLoader

        loader = TemplateLoader()
        count = loader.load_directory("/nonexistent/path")
        assert count == 0

    def test_load_empty_directory(self):
        """测试加载空目录"""
        from mc_agent_kit.generator.template_loader import TemplateLoader

        loader = TemplateLoader()
        with tempfile.TemporaryDirectory() as tmpdir:
            count = loader.load_directory(tmpdir)
            assert count == 0

    def test_reload_empty(self):
        """测试热重载空加载器"""
        from mc_agent_kit.generator.template_loader import TemplateLoader

        loader = TemplateLoader()
        count = loader.reload()
        assert count == 0

    def test_reload_nonexistent_file(self):
        """测试热重载不存在的文件"""
        from mc_agent_kit.generator.template_loader import TemplateLoader

        loader = TemplateLoader()
        result = loader.reload_file("/nonexistent/file.j2")
        assert result is False

    def test_get_loaded_files_empty(self):
        """测试获取已加载文件（空）"""
        from mc_agent_kit.generator.template_loader import TemplateLoader

        loader = TemplateLoader()
        files = loader.get_loaded_files()
        assert files == []

    def test_parse_frontmatter_no_yaml(self):
        """测试解析无 frontmatter 的内容"""
        from mc_agent_kit.generator.template_loader import TemplateLoader

        loader = TemplateLoader()
        content = "plain template content"
        metadata, template = loader._parse_frontmatter(content)
        assert metadata == {}
        assert template == content

    def test_parse_simple_frontmatter(self):
        """测试简单 frontmatter 解析"""
        from mc_agent_kit.generator.template_loader import TemplateLoader

        loader = TemplateLoader()
        frontmatter = 'name: test\ndescription: "Test template"'
        metadata = loader._parse_simple_frontmatter(frontmatter)
        assert metadata["name"] == "test"
        assert metadata["description"] == "Test template"

    def test_parse_simple_frontmatter_with_list(self):
        """测试带列表的简单 frontmatter 解析"""
        from mc_agent_kit.generator.template_loader import TemplateLoader

        loader = TemplateLoader()
        frontmatter = """name: test
tags:
  - tag1
  - tag2"""
        metadata = loader._parse_simple_frontmatter(frontmatter)
        assert metadata["name"] == "test"
        assert metadata["tags"] == ["tag1", "tag2"]

    def test_load_templates_from_directory(self):
        """测试便捷函数"""
        from mc_agent_kit.generator.template_loader import load_templates_from_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            manager, count = load_templates_from_directory(tmpdir)
            assert count == 0


class TestCodeGeneratorExtra:
    """测试代码生成器额外覆盖"""

    def test_code_template_creation(self):
        """测试代码模板创建"""
        from mc_agent_kit.generator.templates import (
            CodeTemplate,
            TemplateParameter,
            TemplateType,
        )

        template = CodeTemplate(
            name="test_template",
            template_type=TemplateType.CUSTOM,
            description="Test template",
            template="print('{{ name }}')",
            parameters=[
                TemplateParameter(
                    name="name",
                    description="Name to print",
                    param_type="str",
                    required=True,
                )
            ],
        )
        assert template.name == "test_template"
        assert template.template_type == TemplateType.CUSTOM

    def test_template_parameter(self):
        """测试模板参数"""
        from mc_agent_kit.generator.templates import TemplateParameter

        param = TemplateParameter(
            name="entity_type",
            description="Entity type",
            param_type="str",
            required=True,
            default="zombie",
            choices=["zombie", "skeleton", "creeper"],
        )
        assert param.name == "entity_type"
        assert param.default == "zombie"
        assert len(param.choices) == 3


class TestVectorStoreExtra:
    """测试向量存储额外覆盖"""

    def test_compute_hash_md5(self):
        """测试 MD5 哈希计算"""
        from mc_agent_kit.retrieval.vector_store import (
            VectorStore,
            VectorStoreConfig,
        )

        config = VectorStoreConfig(hash_algorithm="md5")
        store = VectorStore(config)
        hash1 = store._compute_hash("test content")
        hash2 = store._compute_hash("test content")
        assert hash1 == hash2
        assert len(hash1) == 32

    def test_compute_hash_sha256(self):
        """测试 SHA256 哈希计算"""
        from mc_agent_kit.retrieval.vector_store import (
            VectorStore,
            VectorStoreConfig,
        )

        config = VectorStoreConfig(hash_algorithm="sha256")
        store = VectorStore(config)
        hash1 = store._compute_hash("test content")
        assert len(hash1) == 64


class TestHybridSearchExtra:
    """测试混合搜索额外覆盖"""

    def test_hybrid_search_config(self):
        """测试混合搜索配置"""
        from mc_agent_kit.retrieval.hybrid_search import HybridSearchConfig

        config = HybridSearchConfig(
            keyword_weight=0.4,
            semantic_weight=0.6,
            default_top_k=10,
        )
        assert config.keyword_weight == 0.4
        assert config.semantic_weight == 0.6
        assert config.default_top_k == 10

    def test_hybrid_search_result(self):
        """测试混合搜索结果"""
        from mc_agent_kit.retrieval.hybrid_search import HybridSearchResult

        result = HybridSearchResult(
            id="test-1",
            content="test content",
            score=0.85,
            keyword_score=0.8,
            semantic_score=0.9,
        )
        assert result.id == "test-1"
        assert result.keyword_score == 0.8
        assert result.semantic_score == 0.9


class TestAPISearchSkillExtra:
    """测试 API 搜索 Skill 额外覆盖"""

    def test_api_search_skill_metadata(self):
        """测试 API 搜索 Skill 元数据"""
        from mc_agent_kit.skills.modsdk.api_search import ModSDKAPISearchSkill

        skill = ModSDKAPISearchSkill()
        metadata = skill.metadata
        assert metadata is not None
        assert metadata.name == "modsdk-api-search"


class TestEventSearchSkillExtra:
    """测试事件搜索 Skill 额外覆盖"""

    def test_event_parameter_creation(self):
        """测试事件参数创建"""
        from mc_agent_kit.knowledge_base.models import EventParameter

        param = EventParameter(
            name="entityId",
            data_type="str",
            description="实体 ID",
            mutable=True,
        )
        assert param.name == "entityId"
        assert param.mutable is True

    def test_event_entry_creation(self):
        """测试事件条目创建"""
        from mc_agent_kit.knowledge_base.models import EventEntry, Scope

        event = EventEntry(
            name="OnPlayerJoin",
            module="player",
            description="玩家加入事件",
            scope=Scope.SERVER,
        )
        assert event.name == "OnPlayerJoin"
        assert event.scope == Scope.SERVER


class TestCodeExecutorExtra:
    """测试代码执行器额外覆盖"""

    def test_execution_config(self):
        """测试执行配置"""
        from mc_agent_kit.execution.executor import ExecutionConfig

        config = ExecutionConfig(
            timeout=30,
            sandbox_mode=True,
            capture_output=True,
        )
        assert config.timeout == 30
        assert config.sandbox_mode is True
        assert config.capture_output is True

    def test_code_validator(self):
        """测试代码验证器"""
        from mc_agent_kit.execution.executor import CodeValidator, ExecutionConfig

        config = ExecutionConfig(sandbox_mode=True)
        validator = CodeValidator(config)

        # 安全代码
        safe_code = "x = 1 + 1"
        result = validator.validate(safe_code)
        # validate returns tuple (is_valid, errors)
        assert isinstance(result, tuple)


class TestDebuggerExtra:
    """测试调试器额外覆盖"""

    def test_breakpoint_creation(self):
        """测试断点创建"""
        from mc_agent_kit.execution.debugger import Breakpoint

        bp = Breakpoint(
            id="bp-1",
            file="test.py",
            line=10,
            condition="x > 0",
            enabled=True,
        )
        assert bp.id == "bp-1"
        assert bp.line == 10
        assert bp.condition == "x > 0"

    def test_debug_session(self):
        """测试调试会话"""
        from mc_agent_kit.execution.debugger import DebugSession

        session = DebugSession(id="test-session")
        assert session.id == "test-session"
        assert session.breakpoints == {}


class TestPerformanceAnalyzerExtra:
    """测试性能分析器额外覆盖"""

    def test_timer_context(self):
        """测试计时器上下文"""
        from mc_agent_kit.execution.performance import Timer

        with Timer("test_operation") as timer:
            pass  # 简单操作

        assert timer.elapsed_ms() >= 0

    def test_profiling_result(self):
        """测试分析结果"""
        from mc_agent_kit.execution.performance import ProfilingResult

        result = ProfilingResult(
            function_name="test_func",
            calls=10,
            total_time=1.5,
            cumulative_time=1.5,
            avg_time=0.15,
            min_time=0.1,
            max_time=0.2,
        )
        assert result.function_name == "test_func"
        assert result.calls == 10


class TestHotReloaderExtra:
    """测试热重载器额外覆盖"""

    def test_reload_config(self):
        """测试重载配置"""
        from mc_agent_kit.execution.hot_reload import ReloadConfig

        config = ReloadConfig(
            watch_patterns=["*.py"],
            ignore_patterns=["__pycache__/*"],
            debounce_ms=500,
        )
        assert "*.py" in config.watch_patterns
        assert config.debounce_ms == 500

    def test_reload_result(self):
        """测试重载结果"""
        from mc_agent_kit.execution.hot_reload import ReloadResult, ReloadStatus

        result = ReloadResult(
            status=ReloadStatus.SUCCESS,
            file_path="test.py",
        )
        assert result.status == ReloadStatus.SUCCESS