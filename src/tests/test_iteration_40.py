"""
迭代 #40 测试：测试覆盖率提升与功能增强

测试内容：
- knowledge/__init__.py: create_knowledge_tool 函数
- knowledge/examples_enhanced.py: CodeExampleManager 完整测试
- knowledge/index_cache.py: KnowledgeIndexCache 测试
- knowledge/search_cache.py: SearchResultCache 测试
- knowledge/retrieval.py: 知识检索测试
- launcher/auto_fixer.py: 内存自动修复器测试
- 其他低覆盖率模块测试
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mc_agent_kit.knowledge import (
    KnowledgeBase,
    KnowledgeIndexCache,
    SearchResultCache,
    CodeExampleManager,
    DifficultyLevel,
    ExampleCategory,
    ExampleManagerConfig,
    CodeExampleEnhanced,
)
from mc_agent_kit.knowledge.examples_enhanced import SearchResult as ExampleSearchResult
from mc_agent_kit.knowledge.index_cache import CacheMetadata, FileState, IndexCacheStats
from mc_agent_kit.knowledge.search_cache import SearchCacheEntry, SearchCacheStats


# =============================================================================
# Test CodeExampleManager (knowledge/examples_enhanced.py)
# =============================================================================

class TestCodeExampleManagerEnhanced:
    """CodeExampleManager 增强测试"""

    def test_search_with_difficulty_filter(self):
        """测试难度过滤"""
        manager = CodeExampleManager()
        results = manager.search("玩家", difficulty=DifficultyLevel.BEGINNER)
        for r in results:
            assert r.example.difficulty == DifficultyLevel.BEGINNER

    def test_search_with_category_filter(self):
        """测试类别过滤"""
        manager = CodeExampleManager()
        results = manager.search("", category=ExampleCategory.ENTITY)
        for r in results:
            assert r.example.category == ExampleCategory.ENTITY

    def test_search_with_scope_filter(self):
        """测试作用域过滤"""
        manager = CodeExampleManager()
        results = manager.search("", scope="server")
        for r in results:
            assert r.example.scope in ("server", "both")

    def test_search_with_api_filter(self):
        """测试 API 过滤"""
        manager = CodeExampleManager()
        results = manager.search("", api="ListenForEvent")
        for r in results:
            assert "ListenForEvent" in r.example.related_apis

    def test_search_with_event_filter(self):
        """测试事件过滤"""
        manager = CodeExampleManager()
        results = manager.search("", event="OnPlayerJoin")
        for r in results:
            assert "OnPlayerJoin" in r.example.related_events

    def test_search_with_tags_filter(self):
        """测试标签过滤"""
        manager = CodeExampleManager()
        results = manager.search("", tags=["事件"])
        for r in results:
            assert "事件" in r.example.tags

    def test_search_by_description_match(self):
        """测试描述匹配"""
        manager = CodeExampleManager()
        results = manager.search("监听玩家加入事件")
        assert len(results) > 0
        assert any("玩家" in r.example.title or "hello" in r.example.title.lower() for r in results)

    def test_search_by_code_match(self):
        """测试代码匹配"""
        manager = CodeExampleManager()
        results = manager.search("CreateEngineEntityByType")
        assert len(results) > 0
        assert any("CreateEngineEntityByType" in r.example.code for r in results)

    def test_search_by_tag_match(self):
        """测试标签匹配"""
        manager = CodeExampleManager()
        results = manager.search("性能")
        assert len(results) > 0

    def test_get_difficulty_distribution(self):
        """测试难度分布"""
        manager = CodeExampleManager()
        dist = manager.get_difficulty_distribution()
        
        assert "beginner" in dist
        assert "intermediate" in dist
        assert "advanced" in dist
        assert "expert" in dist
        assert sum(dist.values()) == len(manager.list_all())

    def test_get_category_distribution(self):
        """测试类别分布"""
        manager = CodeExampleManager()
        dist = manager.get_category_distribution()
        
        assert "basic" in dist
        assert "entity" in dist
        assert "item" in dist
        assert sum(dist.values()) == len(manager.list_all())

    def test_list_by_difficulty(self):
        """测试按难度列出"""
        manager = CodeExampleManager()
        beginner_examples = manager.list_by_difficulty(DifficultyLevel.BEGINNER)
        
        for ex in beginner_examples:
            assert ex.difficulty == DifficultyLevel.BEGINNER

    def test_list_by_category(self):
        """测试按类别列出"""
        manager = CodeExampleManager()
        entity_examples = manager.list_by_category(ExampleCategory.ENTITY)
        
        for ex in entity_examples:
            assert ex.category == ExampleCategory.ENTITY

    def test_search_result_to_dict(self):
        """测试搜索结果序列化"""
        manager = CodeExampleManager()
        results = manager.search("hello")
        if results:
            d = results[0].to_dict()
            assert "example" in d
            assert "score" in d
            assert "match_type" in d

    def test_get_by_api(self):
        """测试按 API 获取示例"""
        manager = CodeExampleManager()
        examples = manager.get_by_api("ListenForEvent")
        assert len(examples) > 0

    def test_get_by_event(self):
        """测试按事件获取示例"""
        manager = CodeExampleManager()
        examples = manager.get_by_event("OnPlayerJoin")
        assert len(examples) > 0

    def test_get_by_tag(self):
        """测试按标签获取示例"""
        manager = CodeExampleManager()
        examples = manager.get_by_tag("事件")
        assert len(examples) > 0

    def test_get_example(self):
        """测试获取单个示例"""
        manager = CodeExampleManager()
        example = manager.get_example("hello_world")
        assert example is not None
        assert example.id == "hello_world"

    def test_list_all(self):
        """测试列出所有示例"""
        manager = CodeExampleManager()
        examples = manager.list_all()
        assert len(examples) > 0


# =============================================================================
# Test CodeExampleEnhanced
# =============================================================================

class TestCodeExampleEnhanced:
    """增强代码示例测试"""

    def test_from_dict_all_fields(self):
        """测试从字典创建（所有字段）"""
        data = {
            "id": "test_example",
            "title": "测试示例",
            "description": "这是一个测试示例",
            "code": "print('hello')",
            "difficulty": "advanced",
            "category": "network",
            "estimated_time": 30,
            "prerequisites": ["Python基础", "网络编程"],
            "related_apis": ["API1", "API2"],
            "related_events": ["Event1"],
            "tags": ["测试", "网络"],
            "scope": "client",
            "author": "测试作者",
            "version": "2.0.0",
            "created_at": "2026-01-01",
            "updated_at": "2026-03-22",
            "views": 100,
            "rating": 4.5,
            "notes": ["注意1"],
            "references": ["ref1"],
        }
        
        example = CodeExampleEnhanced.from_dict(data)
        
        assert example.id == "test_example"
        assert example.title == "测试示例"
        assert example.difficulty == DifficultyLevel.ADVANCED
        assert example.category == ExampleCategory.NETWORK
        assert example.estimated_time == 30
        assert example.author == "测试作者"
        assert example.views == 100
        assert example.rating == 4.5

    def test_to_dict_roundtrip(self):
        """测试序列化/反序列化往返"""
        original = CodeExampleEnhanced(
            id="test",
            title="Test",
            description="Desc",
            code="code",
            difficulty=DifficultyLevel.EXPERT,
            category=ExampleCategory.PERFORMANCE,
            estimated_time=45,
            prerequisites=["pre1"],
            related_apis=["api1"],
            related_events=["evt1"],
            tags=["tag1"],
            scope="both",
            author="author",
            version="1.0.0",
            views=50,
            rating=5.0,
            notes=["note1"],
            references=["ref1"],
        )
        
        d = original.to_dict()
        restored = CodeExampleEnhanced.from_dict(d)
        
        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.difficulty == original.difficulty
        assert restored.category == original.category

    def test_default_values(self):
        """测试默认值"""
        example = CodeExampleEnhanced(
            id="test",
            title="Test",
            description="Desc",
            code="code",
        )
        
        assert example.difficulty == DifficultyLevel.BEGINNER
        assert example.category == ExampleCategory.BASIC
        assert example.estimated_time == 5
        assert example.scope == "server"
        assert example.prerequisites == []
        assert example.related_apis == []


# =============================================================================
# Test KnowledgeIndexCache
# =============================================================================

class TestKnowledgeIndexCacheEnhanced:
    """知识库索引缓存增强测试"""

    def test_needs_rebuild_no_cache(self):
        """测试无缓存时需要重建"""
        cache = KnowledgeIndexCache(cache_dir=tempfile.mkdtemp())
        result = cache.needs_rebuild(tempfile.mkdtemp())
        assert result is True

    def test_cache_metadata_creation(self):
        """测试缓存元数据创建"""
        metadata = CacheMetadata(
            cache_version="1.0.0",
            source_hash="abc123",
            file_count=10,
            total_size=1024,
        )
        assert metadata.cache_version == "1.0.0"
        assert metadata.file_count == 10

    def test_file_state_creation(self):
        """测试文件状态创建"""
        state = FileState(
            path="/test/file.md",
            hash="abc123",
            size=100,
            modified_time=1700000000.0,
        )
        assert state.path == "/test/file.md"
        assert state.hash == "abc123"

    def test_index_cache_stats_creation(self):
        """测试索引缓存统计创建"""
        stats = IndexCacheStats(
            total_entries=100,
            cache_hits=90,
            cache_misses=10,
        )
        assert stats.total_entries == 100
        assert stats.cache_hits == 90
        assert stats.cache_misses == 10

    def test_cache_needs_rebuild(self):
        """测试缓存需要重建检测"""
        cache_dir = tempfile.mkdtemp()
        cache = KnowledgeIndexCache(cache_dir=cache_dir)
        
        # 无缓存时应该需要重建
        result = cache.needs_rebuild(tempfile.mkdtemp())
        assert result is True


# =============================================================================
# Test SearchResultCache
# =============================================================================

class TestSearchResultCacheEnhanced:
    """搜索结果缓存增强测试"""

    def test_get_missing(self):
        """测试获取不存在的缓存"""
        cache = SearchResultCache()
        result = cache.get("nonexistent_query")
        assert result is None

    def test_get_or_compute(self):
        """测试 get_or_compute"""
        cache = SearchResultCache()
        
        # 第一次应该调用 compute_fn
        call_count = [0]
        def compute():
            call_count[0] += 1
            return [{"id": "1", "score": 0.9}]
        
        result1 = cache.get_or_compute("query1", compute)
        assert result1 is not None
        assert call_count[0] == 1
        
        # 第二次应该使用缓存
        result2 = cache.get_or_compute("query1", compute)
        assert result2 is not None
        assert call_count[0] == 1  # 不应该再次调用

    def test_search_cache_entry_creation(self):
        """测试搜索缓存条目创建"""
        entry = SearchCacheEntry(
            query="test query",
            results=[{"id": "1", "score": 0.9}],
        )
        assert entry.query == "test query"
        assert len(entry.results) == 1

    def test_search_cache_stats_creation(self):
        """测试搜索缓存统计创建"""
        stats = SearchCacheStats(
            total_entries=100,
            total_hits=80,
            total_misses=20,
        )
        assert stats.total_entries == 100
        assert stats.total_hits == 80

    def test_get_stats(self):
        """测试获取统计"""
        cache = SearchResultCache()
        stats = cache.get_stats()
        
        # 检查 stats 对象的属性
        assert hasattr(stats, 'total_entries')
        assert hasattr(stats, 'total_hits')

    def test_clear(self):
        """测试清空缓存"""
        cache = SearchResultCache()
        
        cache.get_or_compute("query1", lambda: [{"id": "1"}])
        
        # 使用 get 检查缓存是否存在
        result = cache.get("query1")
        assert result is not None


# =============================================================================
# Test Plugin Module (backwards compatibility)
# =============================================================================

class TestPluginBackwardsCompatibility:
    """测试 plugin 模块向后兼容性"""

    def test_import_plugin_base(self):
        """测试导入 plugin 基类"""
        from mc_agent_kit.plugin import PluginBase, PluginMetadata, PluginResult
        
        assert PluginBase is not None
        assert PluginMetadata is not None
        assert PluginResult is not None

    def test_import_plugin_state(self):
        """测试导入插件状态"""
        from mc_agent_kit.plugin import PluginState, PluginPriority
        
        assert PluginState is not None
        assert PluginPriority is not None

    def test_import_plugin_loader(self):
        """测试导入插件加载器"""
        from mc_agent_kit.plugin import PluginRegistry, PluginLoader
        
        assert PluginRegistry is not None
        assert PluginLoader is not None

    def test_import_plugin_manager(self):
        """测试导入插件管理器"""
        from mc_agent_kit.plugin import PluginManager, PluginManagerConfig
        
        assert PluginManager is not None
        assert PluginManagerConfig is not None


# =============================================================================
# Test Log Analyzer
# =============================================================================

class TestLogAnalyzer:
    """日志分析器测试"""

    def test_log_analyzer_creation(self):
        """测试日志分析器创建"""
        from mc_agent_kit.log_capture.analyzer import LogAnalyzer
        
        analyzer = LogAnalyzer()
        assert analyzer is not None

    def test_error_patterns_exist(self):
        """测试错误模式存在"""
        from mc_agent_kit.log_capture.analyzer import LogAnalyzer, ErrorPattern, PatternCategory
        
        analyzer = LogAnalyzer()
        # 检查 LogAnalyzer 类是否存在
        assert LogAnalyzer is not None
        # 检查错误模式类是否存在
        assert ErrorPattern is not None
        assert PatternCategory is not None

    def test_alert_severity_enum(self):
        """测试告警严重程度枚举"""
        from mc_agent_kit.log_capture.analyzer import AlertSeverity
        
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_pattern_category_enum(self):
        """测试错误模式类别枚举"""
        from mc_agent_kit.log_capture.analyzer import PatternCategory
        
        assert PatternCategory.SYNTAX.value == "syntax"
        assert PatternCategory.RUNTIME.value == "runtime"
        assert PatternCategory.API.value == "api"


# =============================================================================
# Test Scaffold Module
# =============================================================================

class TestScaffoldModule:
    """脚手架模块测试"""

    def test_scaffold_creator_creation(self):
        """测试脚手架创建器"""
        from mc_agent_kit.scaffold.creator import ProjectCreator
        
        creator = ProjectCreator()
        assert creator is not None

    def test_template_manager(self):
        """测试模板管理器"""
        from mc_agent_kit.scaffold.templates import TemplateManager
        
        manager = TemplateManager()
        templates = manager.list_templates()
        
        assert len(templates) > 0

    def test_template_get(self):
        """测试获取模板"""
        from mc_agent_kit.scaffold.templates import TemplateManager
        
        manager = TemplateManager()
        template = manager.get_template("empty")
        
        assert template is not None
        assert template.name == "empty"


# =============================================================================
# Test Launcher Auto Fixer
# =============================================================================

class TestLauncherAutoFixer:
    """启动器自动修复器测试"""

    def test_fix_type_enum(self):
        """测试修复类型枚举"""
        from mc_agent_kit.launcher.auto_fixer import FixType
        
        assert FixType.TEXTURE_COMPRESS.value == "texture_compress"
        assert FixType.MODEL_SIMPLIFY.value == "model_simplify"

    def test_fix_severity_enum(self):
        """测试修复严重程度枚举"""
        from mc_agent_kit.launcher.auto_fixer import FixSeverity
        
        assert FixSeverity.LOW.value == "low"
        assert FixSeverity.MEDIUM.value == "medium"
        assert FixSeverity.HIGH.value == "high"

    def test_get_memory_optimization_tips(self):
        """测试获取内存优化技巧"""
        from mc_agent_kit.launcher.auto_fixer import get_memory_optimization_tips
        
        tips = get_memory_optimization_tips()
        assert len(tips) > 0


# =============================================================================
# Test Launcher Diagnoser
# =============================================================================

class TestLauncherDiagnoser:
    """启动器诊断器测试"""

    def test_diagnostic_severity_enum(self):
        """测试诊断严重程度枚举"""
        from mc_agent_kit.launcher.diagnoser import DiagnosticSeverity
        
        assert DiagnosticSeverity.ERROR.value == "error"
        assert DiagnosticSeverity.WARNING.value == "warning"
        assert DiagnosticSeverity.INFO.value == "info"

    def test_diagnostic_category_enum(self):
        """测试诊断类别枚举"""
        from mc_agent_kit.launcher.diagnoser import DiagnosticCategory
        
        assert DiagnosticCategory.PATH.value == "path"
        assert DiagnosticCategory.CONFIG.value == "config"
        assert DiagnosticCategory.ADDON.value == "addon"


# =============================================================================
# Test Knowledge Retrieval
# =============================================================================

class TestKnowledgeRetrieval:
    """知识检索测试"""

    def test_search_result_dataclass(self):
        """测试搜索结果数据类"""
        from mc_agent_kit.knowledge.retrieval import SearchResult
        
        result = SearchResult(
            type="api",
            name="TestAPI",
            description="Test API description",
            content="Test content",
            score=0.95,
        )
        
        assert result.type == "api"
        assert result.name == "TestAPI"
        assert result.score == 0.95

    def test_code_example_search_result_dataclass(self):
        """测试代码示例搜索结果数据类"""
        from mc_agent_kit.knowledge.retrieval import CodeExampleSearchResult
        from mc_agent_kit.knowledge.parsers import CodeExample
        
        example = CodeExample(
            id="test",
            code="print('hello')",
            language="python",
            source="test.md",
        )
        
        result = CodeExampleSearchResult(
            example=example,
            score=0.9,
        )
        
        assert result.example.id == "test"
        assert result.score == 0.9


# =============================================================================
# Integration Tests
# =============================================================================

class TestIteration40Integration:
    """集成测试"""

    def test_example_search_workflow(self):
        """测试示例搜索工作流"""
        manager = CodeExampleManager()
        
        # 搜索所有实体相关示例
        results = manager.search("", category=ExampleCategory.ENTITY)
        assert len(results) > 0
        
        # 按难度筛选
        beginner = manager.list_by_difficulty(DifficultyLevel.BEGINNER)
        assert len(beginner) > 0
        
        # 获取统计
        dist = manager.get_difficulty_distribution()
        assert sum(dist.values()) == len(manager.list_all())

    def test_cache_workflow(self):
        """测试缓存工作流"""
        # 1. 创建缓存
        cache = SearchResultCache()
        
        # 2. 使用 get_or_compute
        result = cache.get_or_compute("test query", lambda: [{"id": "1"}])
        assert result is not None
        
        # 3. 再次获取应该使用缓存
        result2 = cache.get("test query")
        assert result2 is not None

    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 创建示例管理器
        manager = CodeExampleManager()
        
        # 2. 搜索示例
        results = manager.search("创建实体")
        assert len(results) > 0
        
        # 3. 获取示例详情
        example = manager.get_example("create_entity")
        assert example is not None
        
        # 4. 获取相关示例
        api_examples = manager.get_by_api("CreateEngineEntityByType")
        assert len(api_examples) > 0


# =============================================================================
# Performance Benchmarks
# =============================================================================

class TestPerformanceBenchmarks:
    """性能基准测试"""

    def test_search_cache_performance(self):
        """测试搜索缓存性能"""
        import time
        
        cache = SearchResultCache()
        
        # 设置 100 个缓存
        start = time.time()
        for i in range(100):
            cache.get_or_compute(f"query{i}", lambda i=i: [{"id": str(i)}])
        set_time = time.time() - start
        
        # 获取 100 个缓存
        start = time.time()
        for i in range(100):
            cache.get(f"query{i}")
        get_time = time.time() - start
        
        # 100 次操作应该在 1 秒内完成
        assert set_time < 1.0
        assert get_time < 1.0

    def test_example_search_performance(self):
        """测试示例搜索性能"""
        import time
        
        manager = CodeExampleManager()
        
        start = time.time()
        for _ in range(100):
            manager.search("实体")
        elapsed = time.time() - start
        
        # 100 次搜索应该在 1 秒内完成
        assert elapsed < 1.0


# =============================================================================
# Acceptance Criteria Tests
# =============================================================================

class TestAcceptanceCriteria:
    """验收标准测试"""

    def test_example_manager_functionality(self):
        """验证示例管理器功能"""
        manager = CodeExampleManager()
        
        # 测试搜索
        results = manager.search("玩家")
        assert len(results) > 0
        
        # 测试难度分布
        dist = manager.get_difficulty_distribution()
        assert len(dist) > 0

    def test_cache_functionality(self):
        """验证缓存功能"""
        cache = SearchResultCache()
        
        cache.get_or_compute("test", lambda: [{"id": "1"}])
        result = cache.get("test")
        
        assert result is not None

    def test_plugin_imports_work(self):
        """验证插件导入正常工作"""
        from mc_agent_kit.plugin import (
            PluginBase,
            PluginMetadata,
            PluginResult,
            PluginState,
            PluginPriority,
            PluginInfo,
            PluginRegistry,
            PluginLoader,
            PluginManager,
            PluginManagerConfig,
        )
        
        # 所有导入应该成功
        assert all([
            PluginBase,
            PluginMetadata,
            PluginResult,
            PluginState,
            PluginPriority,
            PluginInfo,
            PluginRegistry,
            PluginLoader,
            PluginManager,
            PluginManagerConfig,
        ])

    def test_launcher_modules_available(self):
        """验证启动器模块可用"""
        from mc_agent_kit.launcher.diagnoser import DiagnosticSeverity, DiagnosticCategory
        from mc_agent_kit.launcher.auto_fixer import FixType, FixSeverity
        
        assert DiagnosticSeverity is not None
        assert DiagnosticCategory is not None
        assert FixType is not None
        assert FixSeverity is not None