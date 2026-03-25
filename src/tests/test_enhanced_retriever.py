"""
增强知识检索模块测试

迭代 #71: 知识库增强与检索优化
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from mc_agent_kit.knowledge.enhanced_retriever import (
    DifficultyLevel,
    EntryScope,
    EntryType,
    ExampleCategory,
    EnhancedKnowledgeRetriever,
    SearchFilter,
    SearchReport,
    SearchResult,
    UnifiedEntry,
    get_retriever,
    search_knowledge,
    get_api_info,
    get_event_info,
)
from mc_agent_kit.knowledge.example_library import (
    ExampleCode,
    ExampleMetadata,
    CodeBlock,
)


class TestSearchFilter:
    """SearchFilter 测试"""

    def test_create_filter(self) -> None:
        """测试创建过滤器"""
        f = SearchFilter(
            entry_type=EntryType.API,
            scope=EntryScope.SERVER,
            module="entity",
        )
        assert f.entry_type == EntryType.API
        assert f.scope == EntryScope.SERVER
        assert f.module == "entity"

    def test_filter_matches(self) -> None:
        """测试过滤器匹配"""
        f = SearchFilter(
            entry_type=EntryType.API,
            scope=EntryScope.SERVER,
        )
        
        entry = UnifiedEntry.create_api(
            name="TestAPI",
            description="Test",
            scope=EntryScope.SERVER,
        )
        
        assert f.matches(entry) is True

    def test_filter_no_match_type(self) -> None:
        """测试类型不匹配"""
        f = SearchFilter(entry_type=EntryType.API)
        
        entry = UnifiedEntry.create_event(
            name="TestEvent",
            description="Test",
        )
        
        assert f.matches(entry) is False

    def test_filter_no_match_scope(self) -> None:
        """测试作用域不匹配"""
        f = SearchFilter(scope=EntryScope.SERVER)
        
        entry = UnifiedEntry.create_api(
            name="TestAPI",
            description="Test",
            scope=EntryScope.CLIENT,
        )
        
        assert f.matches(entry) is False

    def test_filter_with_tags(self) -> None:
        """测试标签过滤"""
        f = SearchFilter(tags=["important"])
        
        entry = UnifiedEntry.create_api(
            name="TestAPI",
            description="Test",
        )
        entry.add_tag("important")
        
        assert f.matches(entry) is True


class TestSearchResult:
    """SearchResult 测试"""

    def test_create_search_result(self) -> None:
        """测试创建搜索结果"""
        entry = UnifiedEntry.create_api(
            name="TestAPI",
            description="Test",
        )
        result = SearchResult(
            entry=entry,
            score=0.95,
            matched_keywords=["test"],
            highlights=["名称匹配"],
        )
        assert result.score == 0.95
        assert "test" in result.matched_keywords

    def test_search_result_to_dict(self) -> None:
        """测试搜索结果转字典"""
        entry = UnifiedEntry.create_api(
            name="TestAPI",
            description="Test",
        )
        result = SearchResult(
            entry=entry,
            score=0.9,
        )
        data = result.to_dict()
        assert "entry" in data
        assert data["score"] == 0.9


class TestSearchReport:
    """SearchReport 测试"""

    def test_create_search_report(self) -> None:
        """测试创建搜索报告"""
        report = SearchReport(
            query="test query",
            total_results=5,
            results=[],
            duration_ms=10.5,
        )
        assert report.query == "test query"
        assert report.total_results == 5
        assert report.duration_ms == 10.5

    def test_search_report_to_dict(self) -> None:
        """测试搜索报告转字典"""
        report = SearchReport(
            query="test",
            total_results=0,
            results=[],
            suggestions=["建议 1"],
        )
        data = report.to_dict()
        assert data["query"] == "test"
        assert data["total_results"] == 0
        assert "建议 1" in data["suggestions"]


class TestEnhancedKnowledgeRetriever:
    """EnhancedKnowledgeRetriever 测试"""

    def test_create_retriever(self) -> None:
        """测试创建检索器"""
        retriever = EnhancedKnowledgeRetriever()
        assert retriever._entries == {}
        assert retriever._loaded is False

    def test_add_entry(self) -> None:
        """测试添加条目"""
        retriever = EnhancedKnowledgeRetriever()
        
        entry = UnifiedEntry.create_api(
            name="TestAPI",
            description="Test API",
            module="test",
        )
        retriever.add_entry(entry)
        
        # 名称索引使用小写
        assert "testapi" in retriever._by_name
        assert entry.id in retriever._entries

    def test_get_api(self) -> None:
        """测试获取 API"""
        retriever = EnhancedKnowledgeRetriever()
        
        entry = UnifiedEntry.create_api(
            name="CreateEntity",
            description="创建实体",
            module="entity",
        )
        retriever.add_entry(entry)
        
        result = retriever.get_api("CreateEntity")
        assert result is not None
        assert result.name == "CreateEntity"

    def test_get_api_not_found(self) -> None:
        """测试获取不存在的 API"""
        retriever = EnhancedKnowledgeRetriever()
        result = retriever.get_api("NonExistentAPI")
        assert result is None

    def test_get_event(self) -> None:
        """测试获取事件"""
        retriever = EnhancedKnowledgeRetriever()
        
        entry = UnifiedEntry.create_event(
            name="OnPlayerJoin",
            description="玩家加入",
            module="player",
        )
        retriever.add_entry(entry)
        
        result = retriever.get_event("OnPlayerJoin")
        assert result is not None
        assert result.name == "OnPlayerJoin"

    def test_list_apis(self) -> None:
        """测试列出 API"""
        retriever = EnhancedKnowledgeRetriever()
        
        for i in range(5):
            entry = UnifiedEntry.create_api(
                name=f"API_{i}",
                description=f"API {i}",
                module="test",
            )
            retriever.add_entry(entry)
        
        apis = retriever.list_apis(limit=10)
        assert len(apis) == 5

    def test_list_apis_with_module_filter(self) -> None:
        """测试按模块过滤列出 API"""
        retriever = EnhancedKnowledgeRetriever()
        
        entry1 = UnifiedEntry.create_api(
            name="API1",
            description="Test",
            module="entity",
        )
        entry2 = UnifiedEntry.create_api(
            name="API2",
            description="Test",
            module="player",
        )
        retriever.add_entry(entry1)
        retriever.add_entry(entry2)
        
        apis = retriever.list_apis(module="entity")
        assert len(apis) == 1
        assert apis[0].name == "API1"

    def test_list_events(self) -> None:
        """测试列出事件"""
        retriever = EnhancedKnowledgeRetriever()
        
        for i in range(3):
            entry = UnifiedEntry.create_event(
                name=f"Event_{i}",
                description=f"Event {i}",
            )
            retriever.add_entry(entry)
        
        events = retriever.list_events(limit=10)
        assert len(events) == 3

    def test_search_basic(self) -> None:
        """测试基本搜索"""
        retriever = EnhancedKnowledgeRetriever()
        
        entry = UnifiedEntry.create_api(
            name="CreateEntity",
            description="创建实体 API",
            module="entity",
        )
        retriever.add_entry(entry)
        
        report = retriever.search("CreateEntity", limit=10)
        assert report.total_results >= 1
        assert report.query == "CreateEntity"

    def test_search_with_filter(self) -> None:
        """测试带过滤器的搜索"""
        retriever = EnhancedKnowledgeRetriever()
        
        api_entry = UnifiedEntry.create_api(
            name="TestAPI",
            description="Test",
            scope=EntryScope.SERVER,
        )
        event_entry = UnifiedEntry.create_event(
            name="TestEvent",
            description="Test",
        )
        retriever.add_entry(api_entry)
        retriever.add_entry(event_entry)
        
        # 只搜索 API
        filters = SearchFilter(entry_type=EntryType.API)
        report = retriever.search("Test", filters=filters)
        
        # 应该只返回 API
        for result in report.results:
            assert result.entry.type == EntryType.API

    def test_search_score_exact_match(self) -> None:
        """测试精确匹配分数"""
        retriever = EnhancedKnowledgeRetriever()
        
        entry = UnifiedEntry.create_api(
            name="ExactMatch",
            description="Test",
        )
        retriever.add_entry(entry)
        
        report = retriever.search("ExactMatch", limit=10)
        assert report.total_results >= 1
        # 精确匹配应该有高分
        assert report.results[0].score >= 100.0

    def test_search_score_partial_match(self) -> None:
        """测试部分匹配分数"""
        retriever = EnhancedKnowledgeRetriever()
        
        entry = UnifiedEntry.create_api(
            name="CreateEntity",
            description="创建实体",
        )
        retriever.add_entry(entry)
        
        report = retriever.search("Create", limit=10)
        assert report.total_results >= 1
        # 部分匹配分数应该低于精确匹配但大于 0
        assert 0 < report.results[0].score < 100.0

    def test_get_related(self) -> None:
        """测试获取相关条目"""
        retriever = EnhancedKnowledgeRetriever()
        
        api_entry = UnifiedEntry.create_api(
            name="MainAPI",
            description="Main API",
        )
        api_entry.related_apis.append(
            type('obj', (object,), {"name": "RelatedAPI", "relationship": "related"})()
        )
        
        related_entry = UnifiedEntry.create_api(
            name="RelatedAPI",
            description="Related API",
        )
        
        retriever.add_entry(api_entry)
        retriever.add_entry(related_entry)
        
        related = retriever.get_related("MainAPI")
        assert len(related) >= 1

    def test_get_stats(self) -> None:
        """测试获取统计信息"""
        retriever = EnhancedKnowledgeRetriever()
        
        # 添加不同类型的条目
        api_entry = UnifiedEntry.create_api(
            name="TestAPI",
            description="Test",
            module="test",
        )
        event_entry = UnifiedEntry.create_event(
            name="TestEvent",
            description="Test",
            module="test",
        )
        retriever.add_entry(api_entry)
        retriever.add_entry(event_entry)
        
        stats = retriever.get_stats()
        assert stats["total_entries"] == 2
        assert "api" in stats["by_type"]
        assert "event" in stats["by_type"]
        assert "test" in stats["by_module"]

    def test_save_and_load(self, tmp_path: Path) -> None:
        """测试保存和加载"""
        index_path = tmp_path / "index.json"
        retriever = EnhancedKnowledgeRetriever(index_path=str(index_path))
        
        # 添加条目
        entry = UnifiedEntry.create_api(
            name="TestAPI",
            description="Test",
        )
        retriever.add_entry(entry)
        
        # 保存
        retriever.save_to_file()
        assert index_path.exists()
        
        # 加载到新检索器
        retriever2 = EnhancedKnowledgeRetriever(index_path=str(index_path))
        retriever2.load()
        
        # 验证加载
        loaded_entry = retriever2.get_api("TestAPI")
        assert loaded_entry is not None
        assert loaded_entry.name == "TestAPI"

    def test_get_examples_by_api(self, tmp_path: Path) -> None:
        """测试按 API 获取示例"""
        example_path = tmp_path / "examples"
        example_path.mkdir()
        
        retriever = EnhancedKnowledgeRetriever(
            example_library_path=str(example_path)
        )
        
        # 添加示例到库
        from mc_agent_kit.knowledge.example_library import ExampleLibrary
        library = ExampleLibrary(str(example_path))
        
        meta = ExampleMetadata(
            name="test_example",
            title="Test",
            description="Test",
            category=ExampleCategory.BASIC,
            difficulty=DifficultyLevel.BEGINNER,
            apis_used=["TestAPI"],
        )
        example = ExampleCode(
            metadata=meta,
            code_blocks=[
                CodeBlock(language="python", code="print('test')")
            ],
        )
        library.add_example(example)
        library.save_example(example)
        
        # 加载检索器
        retriever.load()
        
        examples = retriever.get_examples_by_api("TestAPI")
        assert len(examples) == 1

    def test_get_examples_by_event(self, tmp_path: Path) -> None:
        """测试按事件获取示例"""
        example_path = tmp_path / "examples"
        example_path.mkdir()
        
        retriever = EnhancedKnowledgeRetriever(
            example_library_path=str(example_path)
        )
        
        from mc_agent_kit.knowledge.example_library import ExampleLibrary
        library = ExampleLibrary(str(example_path))
        
        meta = ExampleMetadata(
            name="test_example",
            title="Test",
            description="Test",
            category=ExampleCategory.BASIC,
            difficulty=DifficultyLevel.BEGINNER,
            events_used=["TestEvent"],
        )
        example = ExampleCode(
            metadata=meta,
            code_blocks=[
                CodeBlock(language="python", code="print('test')")
            ],
        )
        library.add_example(example)
        library.save_example(example)
        
        retriever.load()
        
        examples = retriever.get_examples_by_event("TestEvent")
        assert len(examples) == 1


class TestGlobalFunctions:
    """全局函数测试"""

    def test_get_retriever(self) -> None:
        """测试获取全局检索器"""
        retriever = get_retriever()
        assert retriever is not None

    def test_search_knowledge(self) -> None:
        """测试全局搜索函数"""
        # 获取检索器并添加测试数据
        retriever = get_retriever()
        
        entry = UnifiedEntry.create_api(
            name="GlobalSearchTest",
            description="Test for global search",
        )
        retriever.add_entry(entry)
        
        report = search_knowledge("GlobalSearchTest", limit=5)
        assert isinstance(report, SearchReport)

    def test_get_api_info(self) -> None:
        """测试获取 API 信息"""
        retriever = get_retriever()
        
        entry = UnifiedEntry.create_api(
            name="GlobalAPITest",
            description="Test",
        )
        retriever.add_entry(entry)
        
        result = get_api_info("GlobalAPITest")
        assert result is not None
        assert result.name == "GlobalAPITest"

    def test_get_event_info(self) -> None:
        """测试获取事件信息"""
        retriever = get_retriever()
        
        entry = UnifiedEntry.create_event(
            name="GlobalEventTest",
            description="Test",
        )
        retriever.add_entry(entry)
        
        result = get_event_info("GlobalEventTest")
        assert result is not None
        assert result.name == "GlobalEventTest"