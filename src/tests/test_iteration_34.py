"""
迭代 #34 测试

测试知识库索引缓存、搜索结果缓存和 CLI 性能优化。
"""

import json
import os
import tempfile
import time
from pathlib import Path

import pytest


# ============================================================
# KnowledgeIndexCache Tests
# ============================================================

class TestCacheMetadata:
    """缓存元数据测试"""

    def test_create_metadata(self):
        """测试创建元数据"""
        from mc_agent_kit.knowledge.index_cache import CacheMetadata

        metadata = CacheMetadata(
            source_hash="abc123",
            file_count=10,
            total_size=1000,
            build_time_ms=500.0,
        )

        assert metadata.source_hash == "abc123"
        assert metadata.file_count == 10
        assert metadata.total_size == 1000
        assert metadata.build_time_ms == 500.0
        assert metadata.cache_version == "1.0.0"

    def test_metadata_timestamps(self):
        """测试元数据时间戳"""
        from mc_agent_kit.knowledge.index_cache import CacheMetadata

        before = time.time()
        metadata = CacheMetadata()
        after = time.time()

        assert before <= metadata.created_at <= after
        assert before <= metadata.updated_at <= after


class TestFileState:
    """文件状态测试"""

    def test_create_file_state(self):
        """测试创建文件状态"""
        from mc_agent_kit.knowledge.index_cache import FileState

        state = FileState(
            path="docs/api.md",
            hash="md5hash123",
            size=500,
            modified_time=12345.0,
        )

        assert state.path == "docs/api.md"
        assert state.hash == "md5hash123"
        assert state.size == 500
        assert state.modified_time == 12345.0


class TestIndexCacheStats:
    """索引缓存统计测试"""

    def test_default_stats(self):
        """测试默认统计"""
        from mc_agent_kit.knowledge.index_cache import IndexCacheStats

        stats = IndexCacheStats()

        assert stats.total_entries == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0
        assert stats.hit_rate == 0.0


class TestKnowledgeIndexCache:
    """知识库索引缓存测试"""

    def test_create_cache(self):
        """测试创建缓存"""
        from mc_agent_kit.knowledge.index_cache import KnowledgeIndexCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = KnowledgeIndexCache(cache_dir=tmpdir)
            assert cache.cache_dir == Path(tmpdir)

    def test_needs_rebuild_no_cache(self):
        """测试无缓存时需要重建"""
        from mc_agent_kit.knowledge.index_cache import KnowledgeIndexCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = KnowledgeIndexCache(cache_dir=os.path.join(tmpdir, "cache"))
            
            with tempfile.TemporaryDirectory() as source_dir:
                # 创建源文件
                (Path(source_dir) / "test.md").write_text("# Test")
                
                assert cache.needs_rebuild(source_dir) is True

    def test_save_and_load(self):
        """测试保存和加载"""
        from mc_agent_kit.knowledge.index_cache import KnowledgeIndexCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "cache")
            source_dir = os.path.join(tmpdir, "source")
            
            # 创建源文件
            os.makedirs(source_dir)
            (Path(source_dir) / "test.md").write_text("# Test")
            
            # 创建缓存
            cache = KnowledgeIndexCache(cache_dir=cache_dir)
            
            # 保存索引
            index_data = {
                "apis": {"CreateEntity": {"name": "CreateEntity"}},
                "events": {},
            }
            cache.save(index_data, source_dir, build_time_ms=100.0)
            
            # 检查文件存在
            assert (Path(cache_dir) / "index.json").exists()
            assert (Path(cache_dir) / "metadata.json").exists()
            
            # 加载索引
            loaded = cache.load()
            assert loaded is not None
            assert "CreateEntity" in loaded["apis"]

    def test_needs_rebuild_after_save(self):
        """测试保存后不需要重建"""
        from mc_agent_kit.knowledge.index_cache import KnowledgeIndexCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "cache")
            source_dir = os.path.join(tmpdir, "source")
            
            # 创建源文件
            os.makedirs(source_dir)
            (Path(source_dir) / "test.md").write_text("# Test")
            
            # 创建缓存并保存
            cache = KnowledgeIndexCache(cache_dir=cache_dir)
            cache.save({"apis": {}, "events": {}}, source_dir)
            
            # 不需要重建
            assert cache.needs_rebuild(source_dir) is False

    def test_needs_rebuild_after_file_change(self):
        """测试文件变化后需要重建"""
        from mc_agent_kit.knowledge.index_cache import KnowledgeIndexCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "cache")
            source_dir = os.path.join(tmpdir, "source")
            
            # 创建源文件
            os.makedirs(source_dir)
            test_file = Path(source_dir) / "test.md"
            test_file.write_text("# Test")
            
            # 创建缓存并保存
            cache = KnowledgeIndexCache(cache_dir=cache_dir)
            cache.save({"apis": {}, "events": {}}, source_dir)
            
            # 修改文件
            time.sleep(0.1)  # 确保时间戳变化
            test_file.write_text("# Modified Test")
            
            # 需要重建
            assert cache.needs_rebuild(source_dir) is True

    def test_get_incremental_changes(self):
        """测试获取增量变化"""
        from mc_agent_kit.knowledge.index_cache import KnowledgeIndexCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "cache")
            source_dir = os.path.join(tmpdir, "source")
            
            # 创建源文件
            os.makedirs(source_dir)
            (Path(source_dir) / "test1.md").write_text("# Test 1")
            
            # 创建缓存并保存
            cache = KnowledgeIndexCache(cache_dir=cache_dir)
            cache.save({"apis": {}, "events": {}}, source_dir)
            
            # 添加新文件
            (Path(source_dir) / "test2.md").write_text("# Test 2")
            
            # 获取增量变化
            changes = cache.get_incremental_changes(source_dir)
            
            assert len(changes["added"]) == 1
            assert "test2.md" in changes["added"][0]

    def test_invalidate(self):
        """测试使缓存失效"""
        from mc_agent_kit.knowledge.index_cache import KnowledgeIndexCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "cache")
            source_dir = os.path.join(tmpdir, "source")
            
            # 创建源文件和缓存
            os.makedirs(source_dir)
            (Path(source_dir) / "test.md").write_text("# Test")
            
            cache = KnowledgeIndexCache(cache_dir=cache_dir)
            cache.save({"apis": {}, "events": {}}, source_dir)
            
            # 使缓存失效
            result = cache.invalidate()
            assert result is True
            
            # 需要重建
            assert cache.needs_rebuild(source_dir) is True

    def test_get_stats(self):
        """测试获取统计"""
        from mc_agent_kit.knowledge.index_cache import KnowledgeIndexCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = KnowledgeIndexCache(cache_dir=os.path.join(tmpdir, "cache"))
            stats = cache.get_stats()
            
            assert isinstance(stats.total_entries, int)
            assert isinstance(stats.cache_hits, int)
            assert isinstance(stats.cache_misses, int)

    def test_cleanup(self):
        """测试清理过期缓存"""
        from mc_agent_kit.knowledge.index_cache import KnowledgeIndexCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = os.path.join(tmpdir, "cache")
            os.makedirs(cache_dir)
            
            # 创建一个旧文件
            old_file = Path(cache_dir) / "old.json"
            old_file.write_text("{}")
            
            # 设置修改时间为 31 天前
            import time
            old_time = time.time() - (31 * 24 * 3600)
            os.utime(old_file, (old_time, old_time))
            
            cache = KnowledgeIndexCache(cache_dir=cache_dir)
            cleaned = cache.cleanup(max_age_days=30)
            
            assert cleaned >= 1


# ============================================================
# SearchResultCache Tests
# ============================================================

class TestSearchCacheEntry:
    """搜索缓存条目测试"""

    def test_create_entry(self):
        """测试创建条目"""
        from mc_agent_kit.knowledge.search_cache import SearchCacheEntry

        entry = SearchCacheEntry(
            query="创建实体",
            results=[{"name": "CreateEntity"}],
            search_type="api",
            limit=10,
        )

        assert entry.query == "创建实体"
        assert len(entry.results) == 1
        assert entry.search_type == "api"
        assert entry.limit == 10
        assert entry.hit_count == 0

    def test_entry_timestamps(self):
        """测试条目时间戳"""
        from mc_agent_kit.knowledge.search_cache import SearchCacheEntry

        before = time.time()
        entry = SearchCacheEntry(query="test", results=[])
        after = time.time()

        assert before <= entry.created_at <= after
        assert before <= entry.accessed_at <= after


class TestSearchCacheStats:
    """搜索缓存统计测试"""

    def test_default_stats(self):
        """测试默认统计"""
        from mc_agent_kit.knowledge.search_cache import SearchCacheStats

        stats = SearchCacheStats()

        assert stats.total_entries == 0
        assert stats.total_hits == 0
        assert stats.total_misses == 0
        assert stats.hit_rate == 0.0


class TestSearchResultCache:
    """搜索结果缓存测试"""

    def test_create_cache(self):
        """测试创建缓存"""
        from mc_agent_kit.knowledge.search_cache import SearchResultCache

        cache = SearchResultCache(max_size=100, ttl_seconds=3600)

        assert cache.max_size == 100
        assert cache.ttl_seconds == 3600

    def test_set_and_get(self):
        """测试设置和获取"""
        from mc_agent_kit.knowledge.search_cache import SearchResultCache

        cache = SearchResultCache()
        
        # 设置缓存
        cache.set("创建实体", [{"name": "CreateEntity"}])
        
        # 获取缓存
        results = cache.get("创建实体")
        
        assert results is not None
        assert len(results) == 1
        assert results[0]["name"] == "CreateEntity"

    def test_cache_miss(self):
        """测试缓存未命中"""
        from mc_agent_kit.knowledge.search_cache import SearchResultCache

        cache = SearchResultCache()
        
        results = cache.get("不存在的查询")
        
        assert results is None

    def test_get_or_compute(self):
        """测试获取或计算"""
        from mc_agent_kit.knowledge.search_cache import SearchResultCache

        cache = SearchResultCache()
        
        compute_count = 0
        
        def compute_fn():
            nonlocal compute_count
            compute_count += 1
            return [{"name": "computed"}]
        
        # 首次调用，应该计算
        results1 = cache.get_or_compute("query1", compute_fn)
        assert compute_count == 1
        assert results1[0]["name"] == "computed"
        
        # 再次调用，应该从缓存获取
        results2 = cache.get_or_compute("query1", compute_fn)
        assert compute_count == 1  # 未增加
        assert results2[0]["name"] == "computed"

    def test_warmup(self):
        """测试缓存预热"""
        from mc_agent_kit.knowledge.search_cache import SearchResultCache

        cache = SearchResultCache()
        
        def search_fn(query, search_type, limit):
            return [{"query": query}]
        
        results = cache.warmup(
            queries=["query1", "query2"],
            search_fn=search_fn,
        )
        
        assert results["query1"] is True
        assert results["query2"] is True
        
        # 验证缓存已存在
        assert cache.get("query1") is not None
        assert cache.get("query2") is not None

    def test_invalidate(self):
        """测试使缓存失效"""
        from mc_agent_kit.knowledge.search_cache import SearchResultCache

        cache = SearchResultCache()
        cache.set("query1", [{"name": "result"}])
        
        # 使缓存失效
        result = cache.invalidate("query1")
        
        assert result is True
        assert cache.get("query1") is None

    def test_invalidate_all(self):
        """测试使所有缓存失效"""
        from mc_agent_kit.knowledge.search_cache import SearchResultCache

        cache = SearchResultCache()
        cache.set("query1", [{}])
        cache.set("query2", [{}])
        
        count = cache.invalidate_all()
        
        assert count == 2
        assert cache.get("query1") is None
        assert cache.get("query2") is None

    def test_lru_eviction(self):
        """测试 LRU 淘汰"""
        from mc_agent_kit.knowledge.search_cache import SearchResultCache

        cache = SearchResultCache(max_size=3)
        
        cache.set("query1", [{}])
        cache.set("query2", [{}])
        cache.set("query3", [{}])
        cache.set("query4", [{}])  # 应该淘汰 query1
        
        assert cache.get("query1") is None
        assert cache.get("query2") is not None
        assert cache.get("query3") is not None
        assert cache.get("query4") is not None

    def test_ttl_expiration(self):
        """测试 TTL 过期"""
        from mc_agent_kit.knowledge.search_cache import SearchResultCache

        cache = SearchResultCache(ttl_seconds=0)  # 立即过期
        
        cache.set("query1", [{}])
        
        # 等待一小段时间
        time.sleep(0.1)
        
        # 应该过期
        results = cache.get("query1")
        assert results is None

    def test_get_stats(self):
        """测试获取统计"""
        from mc_agent_kit.knowledge.search_cache import SearchResultCache

        cache = SearchResultCache()
        cache.set("query1", [{}])
        cache.get("query1")  # 命中
        cache.get("query2")  # 未命中
        
        stats = cache.get_stats()
        
        assert stats.total_hits == 1
        assert stats.total_misses == 1

    def test_get_hot_queries(self):
        """测试获取热门查询"""
        from mc_agent_kit.knowledge.search_cache import SearchResultCache

        cache = SearchResultCache()
        cache.set("query1", [{}])
        cache.set("query2", [{}])
        
        # 多次访问 query1
        for _ in range(5):
            cache.get("query1")
        
        cache.get("query2")
        
        hot = cache.get_hot_queries(limit=10)
        
        assert len(hot) == 2
        assert hot[0]["query"] == "query1"
        assert hot[0]["hit_count"] == 5

    def test_persist_and_load(self):
        """测试持久化和加载"""
        from mc_agent_kit.knowledge.search_cache import SearchResultCache

        with tempfile.TemporaryDirectory() as tmpdir:
            persist_path = os.path.join(tmpdir, "cache.json")
            
            # 创建并保存
            cache1 = SearchResultCache(persist_path=persist_path)
            cache1.set("query1", [{"name": "result1"}])
            cache1.set("query2", [{"name": "result2"}])
            cache1.persist()
            
            # 加载到新实例
            cache2 = SearchResultCache(persist_path=persist_path)
            loaded = cache2.load()
            
            assert loaded == 2
            assert cache2.get("query1") is not None
            assert cache2.get("query2") is not None

    def test_prune_expired(self):
        """测试清理过期条目"""
        from mc_agent_kit.knowledge.search_cache import SearchResultCache

        cache = SearchResultCache(ttl_seconds=0)
        cache.set("query1", [{}])
        
        time.sleep(0.1)
        
        cleaned = cache.prune_expired()
        
        assert cleaned == 1


# ============================================================
# CLI Optimize Tests
# ============================================================

class TestLazyModule:
    """懒加载模块测试"""

    def test_create_lazy_module(self):
        """测试创建懒加载模块"""
        from mc_agent_kit.cli_optimize import LazyModule

        mod = LazyModule(name="json", import_path="json")

        assert mod.name == "json"
        assert mod.import_path == "json"
        assert mod.loaded is False

    def test_lazy_load(self):
        """测试延迟加载"""
        from mc_agent_kit.cli_optimize import LazyModule

        mod = LazyModule(name="json", import_path="json")

        # 加载前
        assert mod.loaded is False

        # 首次获取时加载
        json_mod = mod.get()
        import json as expected_mod
        assert json_mod is expected_mod
        assert mod.loaded is True


class TestLazyLoader:
    """懒加载器测试"""

    def test_register_module(self):
        """测试注册模块"""
        from mc_agent_kit.cli_optimize import LazyLoader

        loader = LazyLoader()
        loader.register("json", "json")

        assert loader.is_loaded("json") is False

    def test_get_module(self):
        """测试获取模块"""
        from mc_agent_kit.cli_optimize import LazyLoader

        loader = LazyLoader()
        loader.register("json", "json")

        json_mod = loader.get("json")

        import json as expected_mod
        assert json_mod is expected_mod
        assert loader.is_loaded("json") is True

    def test_get_unregistered_module(self):
        """测试获取未注册模块"""
        from mc_agent_kit.cli_optimize import LazyLoader

        loader = LazyLoader()

        with pytest.raises(KeyError):
            loader.get("not_registered")

    def test_preload(self):
        """测试预加载"""
        from mc_agent_kit.cli_optimize import LazyLoader

        loader = LazyLoader()
        loader.register("json", "json")
        loader.register("os", "os")

        times = loader.preload(["json", "os"])

        assert "json" in times
        assert "os" in times
        assert loader.is_loaded("json")
        assert loader.is_loaded("os")

    def test_get_loaded_modules(self):
        """测试获取已加载模块"""
        from mc_agent_kit.cli_optimize import LazyLoader

        loader = LazyLoader()
        loader.register("json", "json")
        loader.register("os", "os")

        loader.get("json")

        loaded = loader.get_loaded_modules()

        assert "json" in loaded
        assert "os" not in loaded

    def test_clear(self):
        """测试清除"""
        from mc_agent_kit.cli_optimize import LazyLoader

        loader = LazyLoader()
        loader.register("json", "json")
        loader.get("json")

        loader.clear()

        assert len(loader.get_loaded_modules()) == 0


class TestCompletionSuggestion:
    """补全建议测试"""

    def test_create_suggestion(self):
        """测试创建补全建议"""
        from mc_agent_kit.cli_optimize import CompletionSuggestion

        suggestion = CompletionSuggestion(
            name="api",
            description="搜索 ModSDK API",
            type="command",
            aliases=["a"],
        )

        assert suggestion.name == "api"
        assert suggestion.description == "搜索 ModSDK API"
        assert suggestion.type == "command"
        assert suggestion.aliases == ["a"]


class TestShellCompletion:
    """Shell 补全测试"""

    def test_register_command(self):
        """测试注册命令"""
        from mc_agent_kit.cli_optimize import ShellCompletion

        completion = ShellCompletion()
        completion.register_command(
            name="test",
            description="Test command",
            subcommands=["sub1", "sub2"],
        )

        # 获取命令建议
        suggestions = completion.get_suggestions("mc-agent", "te")

        assert len(suggestions) == 1
        assert suggestions[0].name == "test"

    def test_register_global_option(self):
        """测试注册全局选项"""
        from mc_agent_kit.cli_optimize import ShellCompletion

        completion = ShellCompletion()
        completion.register_global_option(
            name="format",
            description="输出格式",
        )

        suggestions = completion.get_suggestions("mc-agent", "--for")

        assert len(suggestions) >= 1

    def test_generate_bash_script(self):
        """测试生成 bash 补全脚本"""
        from mc_agent_kit.cli_optimize import ShellCompletion

        completion = ShellCompletion()
        completion.register_command(name="api", description="API 命令")
        completion.register_command(name="event", description="事件命令")

        script = completion.generate_bash_script("mc-agent")

        assert "_mc-agent_completion" in script
        assert "api" in script
        assert "event" in script

    def test_generate_zsh_script(self):
        """测试生成 zsh 补全脚本"""
        from mc_agent_kit.cli_optimize import ShellCompletion

        completion = ShellCompletion()
        completion.register_command(name="api", description="API 命令")

        script = completion.generate_zsh_script("mc-agent")

        assert "#compdef mc-agent" in script
        assert "api" in script

    def test_generate_fish_script(self):
        """测试生成 fish 补全脚本"""
        from mc_agent_kit.cli_optimize import ShellCompletion

        completion = ShellCompletion()
        completion.register_command(name="api", description="API 命令")

        script = completion.generate_fish_script("mc-agent")

        assert "complete -c mc-agent" in script
        assert "api" in script


class TestCreateShellCompletion:
    """创建 Shell 补全测试"""

    def test_create_and_get_suggestions(self):
        """测试创建并获取建议"""
        from mc_agent_kit.cli_optimize import create_shell_completion

        completion = create_shell_completion()

        # 测试命令补全
        suggestions = completion.get_suggestions("mc-agent", "ap")
        names = [s.name for s in suggestions]
        assert "api" in names


class TestCLIStartupMetrics:
    """CLI 启动性能指标测试"""

    def test_default_metrics(self):
        """测试默认指标"""
        from mc_agent_kit.cli_optimize import CLIStartupMetrics

        metrics = CLIStartupMetrics()

        assert metrics.total_time_ms == 0.0
        assert metrics.import_time_ms == 0.0
        assert metrics.parser_time_ms == 0.0
        assert metrics.lazy_modules == {}


class TestMeasureStartup:
    """启动性能测量测试"""

    def test_measure_startup(self):
        """测试测量启动性能"""
        from mc_agent_kit.cli_optimize import measure_startup

        metrics = measure_startup()

        assert metrics.total_time_ms >= 0
        assert metrics.import_time_ms >= 0
        assert metrics.parser_time_ms >= 0


class TestOptimizeCLIStartup:
    """CLI 启动优化测试"""

    def test_optimize_cli_startup(self):
        """测试优化 CLI 启动"""
        from mc_agent_kit.cli_optimize import optimize_cli_startup

        result = optimize_cli_startup()

        assert "metrics" in result
        assert "suggestions" in result
        assert len(result["suggestions"]) >= 1


# ============================================================
# Integration Tests
# ============================================================

class TestIteration34Integration:
    """迭代 #34 集成测试"""

    def test_index_cache_with_search_cache(self):
        """测试索引缓存与搜索缓存集成"""
        from mc_agent_kit.knowledge.index_cache import KnowledgeIndexCache
        from mc_agent_kit.knowledge.search_cache import SearchResultCache

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建索引缓存
            index_cache = KnowledgeIndexCache(
                cache_dir=os.path.join(tmpdir, "index_cache")
            )
            
            # 创建搜索缓存
            search_cache = SearchResultCache(
                persist_path=os.path.join(tmpdir, "search_cache.json")
            )
            
            # 创建源文件
            source_dir = os.path.join(tmpdir, "source")
            os.makedirs(source_dir)
            (Path(source_dir) / "test.md").write_text("# Test API")
            
            # 保存索引
            index_data = {
                "apis": {"CreateEntity": {"name": "CreateEntity", "description": "创建实体"}},
            }
            index_cache.save(index_data, source_dir)
            
            # 模拟搜索
            def search_fn(query, search_type, limit):
                return [{"name": "CreateEntity", "score": 0.9}]
            
            # 使用搜索缓存
            results = search_cache.get_or_compute(
                "创建实体",
                lambda: search_fn("创建实体", "api", 10),
            )
            
            assert len(results) == 1
            assert results[0]["name"] == "CreateEntity"
            
            # 验证缓存命中
            stats = search_cache.get_stats()
            assert stats.total_hits == 0  # 首次是 miss
            
            # 再次查询
            search_cache.get("创建实体")
            stats = search_cache.get_stats()
            assert stats.total_hits == 1

    def test_cli_optimize_with_caches(self):
        """测试 CLI 优化与缓存集成"""
        from mc_agent_kit.cli_optimize import get_lazy_loader, measure_startup
        from mc_agent_kit.knowledge.search_cache import create_search_cache

        # 获取懒加载器
        loader = get_lazy_loader()
        
        # 注册缓存模块
        loader.register("search_cache", "mc_agent_kit.knowledge.search_cache")
        
        # 测量启动
        metrics = measure_startup()
        
        assert metrics.total_time_ms >= 0
        
        # 懒加载搜索缓存模块
        search_cache_mod = loader.get("search_cache")
        assert search_cache_mod is not None
        
        # 创建搜索缓存
        cache = create_search_cache()
        cache.set("test", [{"result": "data"}])
        
        assert cache.get("test") is not None


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])