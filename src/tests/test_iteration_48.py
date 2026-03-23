"""
迭代 #48 测试

测试 AI Agent 能力增强、用户体验优化和性能优化功能。
"""

import pytest
import time


class TestIntentRecognizer:
    """意图识别器测试"""

    def test_intent_search_api(self):
        """测试 API 搜索意图识别"""
        from mc_agent_kit.skills import IntentRecognizer, IntentType

        recognizer = IntentRecognizer()
        result = recognizer.recognize("查找 CreateEntity API")

        assert result.intent == IntentType.SEARCH_API
        assert result.confidence > 0.5
        assert "api_names" in result.entities

    def test_intent_search_event(self):
        """测试事件搜索意图识别"""
        from mc_agent_kit.skills import IntentRecognizer, IntentType

        recognizer = IntentRecognizer()
        result = recognizer.recognize("监听 OnServerStart 事件")

        assert result.intent == IntentType.SEARCH_EVENT
        assert result.confidence > 0.5

    def test_intent_create_entity(self):
        """测试创建实体意图识别"""
        from mc_agent_kit.skills import IntentRecognizer, IntentType

        recognizer = IntentRecognizer()
        result = recognizer.recognize("我想创建一个自定义实体")

        assert result.intent == IntentType.CREATE_ENTITY
        assert result.confidence > 0.5

    def test_intent_diagnose_error(self):
        """测试诊断错误意图识别"""
        from mc_agent_kit.skills import IntentRecognizer, IntentType

        recognizer = IntentRecognizer()
        result = recognizer.recognize("帮我看看这个报错")

        assert result.intent == IntentType.DIAGNOSE_ERROR
        assert result.confidence > 0.5

    def test_intent_unknown(self):
        """测试未知意图"""
        from mc_agent_kit.skills import IntentRecognizer, IntentType

        recognizer = IntentRecognizer()
        result = recognizer.recognize("今天天气怎么样")

        assert result.intent == IntentType.UNKNOWN

    def test_entity_extraction(self):
        """测试实体提取"""
        from mc_agent_kit.skills import IntentRecognizer

        recognizer = IntentRecognizer()
        result = recognizer.recognize("服务端的 GetConfig API 怎么用")

        assert result.entities.get("scope") == "server"
        assert "GetConfig" in result.entities.get("api_names", [])


class TestConversationManager:
    """对话管理器测试"""

    def test_create_session(self):
        """测试创建会话"""
        from mc_agent_kit.skills import ConversationManager

        manager = ConversationManager()
        session = manager.create_session()

        assert session.session_id is not None
        assert len(session.messages) == 0

    def test_add_message(self):
        """测试添加消息"""
        from mc_agent_kit.skills import ConversationManager, ConversationRole

        manager = ConversationManager()
        session = manager.create_session()

        session.add_message(ConversationRole.USER, "你好")

        assert len(session.messages) == 1
        assert session.messages[0].content == "你好"
        assert session.messages[0].role == ConversationRole.USER

    def test_process_message(self):
        """测试处理消息"""
        from mc_agent_kit.skills import ConversationManager, IntentType

        manager = ConversationManager()
        session = manager.create_session()

        result = manager.process_message(session, "查找 CreateEntity API")

        assert result.intent == IntentType.SEARCH_API
        assert len(session.messages) == 1
        assert len(session.intent_history) == 1

    def test_get_recent_messages(self):
        """测试获取最近消息"""
        from mc_agent_kit.skills import ConversationManager, ConversationRole

        manager = ConversationManager()
        session = manager.create_session()

        for i in range(10):
            session.add_message(ConversationRole.USER, f"消息 {i}")

        recent = session.get_recent_messages(3)

        assert len(recent) == 3
        assert "7" in recent[0].content

    def test_session_count(self):
        """测试会话计数"""
        from mc_agent_kit.skills import ConversationManager

        manager = ConversationManager(max_sessions=10)

        for _ in range(5):
            manager.create_session()

        assert manager.get_session_count() == 5


class TestCodeContextAnalyzer:
    """代码上下文分析器测试"""

    def test_analyze_simple_code(self):
        """测试分析简单代码"""
        from mc_agent_kit.skills import CodeContextAnalyzer

        analyzer = CodeContextAnalyzer()
        code = '''
import mod.server as server

def hello():
    print("Hello")
'''
        info = analyzer.analyze(code)

        assert info.language == "python"
        assert len(info.imports) > 0
        assert len(info.functions) == 1

    def test_analyze_class(self):
        """测试分析类"""
        from mc_agent_kit.skills import CodeContextAnalyzer

        analyzer = CodeContextAnalyzer()
        code = '''
class MyEntity:
    def __init__(self):
        pass

    def spawn(self):
        pass
'''
        info = analyzer.analyze(code)

        assert len(info.classes) == 1
        assert info.classes[0]["name"] == "MyEntity"
        assert "spawn" in info.classes[0]["methods"]

    def test_extract_modsdk_apis(self):
        """测试提取 ModSDK API"""
        from mc_agent_kit.skills import CodeContextAnalyzer

        analyzer = CodeContextAnalyzer()
        code = '''
def create():
    entity = CreateEngineEntity()
    config = GetConfig()
    ListenEvent("OnServerStart", callback)
'''
        info = analyzer.analyze(code)

        assert "CreateEngineEntity" in info.apis_used
        assert "GetConfig" in info.apis_used
        assert "ListenEvent" in info.apis_used

    def test_detect_issues(self):
        """测试检测问题"""
        from mc_agent_kit.skills import CodeContextAnalyzer

        analyzer = CodeContextAnalyzer()
        code = '''
try:
    do_something()
except:
    pass
'''
        info = analyzer.analyze(code)

        # 检测到裸 except
        assert len(info.issues) > 0
        assert any(issue["type"] == "bare_except" for issue in info.issues)

    def test_syntax_error(self):
        """测试语法错误处理"""
        from mc_agent_kit.skills import CodeContextAnalyzer

        analyzer = CodeContextAnalyzer()
        code = "def broken("

        info = analyzer.analyze(code)

        assert len(info.issues) > 0
        assert info.issues[0]["type"] == "syntax_error"


class TestSmartRecommender:
    """智能推荐器测试"""

    def test_recommend_apis(self):
        """测试推荐 API"""
        from mc_agent_kit.skills import SmartRecommender

        recommender = SmartRecommender()
        results = recommender.recommend_apis(None, "创建一个实体")

        assert len(results) > 0
        assert any("Create" in r["api"] for r in results)

    def test_recommend_events(self):
        """测试推荐事件"""
        from mc_agent_kit.skills import SmartRecommender

        recommender = SmartRecommender()
        results = recommender.recommend_events(None, "服务端启动时")

        assert len(results) > 0
        assert any("OnServer" in r["event"] for r in results)

    def test_recommend_with_context(self):
        """测试带上下文推荐"""
        from mc_agent_kit.skills import (
            SmartRecommender,
            ConversationContext,
        )

        recommender = SmartRecommender()
        context = ConversationContext(
            session_id="test",
            entities={"scope": "server"},
        )

        results = recommender.recommend_apis(context, "同步数据")

        assert len(results) > 0


class TestRichOutputManager:
    """Rich 输出管理器测试"""

    def test_create_manager(self):
        """测试创建管理器"""
        from mc_agent_kit.ux import RichOutputManager, RichOutputConfig, OutputTheme

        config = RichOutputConfig(theme=OutputTheme.DARK)
        manager = RichOutputManager(config)

        assert manager.config.theme == OutputTheme.DARK

    def test_print_success(self):
        """测试打印成功消息"""
        from mc_agent_kit.ux import RichOutputManager

        manager = RichOutputManager()
        # 不应该抛出异常
        manager.print_success("测试成功", "详细信息")

    def test_print_error(self):
        """测试打印错误消息"""
        from mc_agent_kit.ux import RichOutputManager

        manager = RichOutputManager()
        manager.print_error("测试错误", "错误详情", ["建议1", "建议2"])

    def test_print_table(self):
        """测试打印表格"""
        from mc_agent_kit.ux import RichOutputManager

        manager = RichOutputManager()
        data = [
            {"name": "API1", "count": 10},
            {"name": "API2", "count": 20},
        ]
        manager.print_table(data, title="测试表格")

    def test_progress_info(self):
        """测试进度信息"""
        from mc_agent_kit.ux import ProgressInfo

        info = ProgressInfo(
            description="测试任务",
            total=100,
            completed=50,
        )

        assert info.percentage == 50.0
        assert info.elapsed > 0


class TestEnhancedLRUCache:
    """增强 LRU 缓存测试"""

    def test_basic_operations(self):
        """测试基本操作"""
        from mc_agent_kit.performance import EnhancedLRUCache

        cache = EnhancedLRUCache(max_size=3)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        assert cache.get("a") == 1
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_lru_eviction(self):
        """测试 LRU 淘汰"""
        from mc_agent_kit.performance import EnhancedLRUCache

        cache = EnhancedLRUCache(max_size=2)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # 应该淘汰 "a"

        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_ttl_expiration(self):
        """测试 TTL 过期"""
        from mc_agent_kit.performance import EnhancedLRUCache

        cache = EnhancedLRUCache(max_size=10, ttl_seconds=0.1)

        cache.set("key", "value")
        assert cache.get("key") == "value"

        time.sleep(0.15)
        assert cache.get("key") is None

    def test_cache_metrics(self):
        """测试缓存指标"""
        from mc_agent_kit.performance import EnhancedLRUCache

        cache = EnhancedLRUCache(max_size=10)

        cache.set("a", 1)
        cache.get("a")  # hit
        cache.get("b")  # miss

        metrics = cache.get_metrics()

        assert metrics.hits == 1
        assert metrics.misses == 1
        assert metrics.hit_rate == 0.5

    def test_get_or_set(self):
        """测试 get_or_set"""
        from mc_agent_kit.performance import EnhancedLRUCache

        cache = EnhancedLRUCache(max_size=10)

        # 不存在，调用 factory
        value = cache.get_or_set("key", lambda: "computed")
        assert value == "computed"

        # 已存在，不调用 factory
        value = cache.get_or_set("key", lambda: "new_value")
        assert value == "computed"


class TestSmartCache:
    """智能缓存测试"""

    def test_set_and_get(self):
        """测试设置和获取"""
        from mc_agent_kit.performance import SmartCache

        cache = SmartCache()
        cache.set("key1", {"data": "value1"})

        result = cache.get("key1")
        assert result == {"data": "value1"}

    def test_tags(self):
        """测试标签功能"""
        from mc_agent_kit.performance import SmartCache

        cache = SmartCache()

        cache.set("api1", {"name": "API1"}, tags={"api", "entity"})
        cache.set("api2", {"name": "API2"}, tags={"api", "item"})
        cache.set("event1", {"name": "Event1"}, tags={"event"})

        # 按标签获取
        apis = cache.get_by_tag("api")
        assert len(apis) == 2

        # 按标签失效
        count = cache.invalidate_by_tag("entity")
        assert count == 1
        assert cache.get("api1") is None

    def test_size_tracking(self):
        """测试大小追踪"""
        from mc_agent_kit.performance import SmartCache

        cache = SmartCache(max_size_mb=0.001)  # 1KB

        cache.set("key1", "x" * 100)

        metrics = cache.get_metrics()
        assert metrics["total_size_bytes"] > 0

    def test_cache_metrics(self):
        """测试缓存指标"""
        from mc_agent_kit.performance import SmartCache

        cache = SmartCache()

        cache.set("a", 1)
        cache.get("a")  # hit
        cache.get("b")  # miss

        metrics = cache.get_metrics()

        assert metrics["hits"] == 1
        assert metrics["misses"] == 1


class TestParallelProcessor:
    """并行处理器测试"""

    def test_map_threaded(self):
        """测试线程并行映射"""
        from mc_agent_kit.performance import ParallelProcessor

        processor = ParallelProcessor(max_workers=4)

        def square(x):
            return x * x

        results = processor.map_threaded(square, [1, 2, 3, 4, 5])

        assert len(results) == 5
        assert all(r in [1, 4, 9, 16, 25] for r in results)

    def test_map_empty(self):
        """测试空输入"""
        from mc_agent_kit.performance import ParallelProcessor

        processor = ParallelProcessor()
        results = processor.map_threaded(lambda x: x, [])

        assert results == []


class TestPerformanceMonitor:
    """性能监控器测试"""

    def test_track_decorator(self):
        """测试追踪装饰器"""
        from mc_agent_kit.performance import PerformanceMonitor

        monitor = PerformanceMonitor()

        @monitor.track("test_func")
        def slow_func():
            time.sleep(0.01)
            return "done"

        result = slow_func()

        assert result == "done"

        stats = monitor.get_stats("test_func")
        assert stats["count"] == 1
        assert stats["min"] > 0

    def test_multiple_calls(self):
        """测试多次调用"""
        from mc_agent_kit.performance import PerformanceMonitor

        monitor = PerformanceMonitor()

        @monitor.track("multi")
        def func():
            return 1

        for _ in range(5):
            func()

        stats = monitor.get_stats("multi")
        assert stats["count"] == 5

    def test_get_all_stats(self):
        """测试获取所有统计"""
        from mc_agent_kit.performance import PerformanceMonitor

        monitor = PerformanceMonitor()

        @monitor.track("func1")
        def func1():
            pass

        @monitor.track("func2")
        def func2():
            pass

        func1()
        func2()

        all_stats = monitor.get_all_stats()

        assert "func1" in all_stats
        assert "func2" in all_stats


class TestLazyLoader:
    """懒加载器测试"""

    def test_lazy_value(self):
        """测试延迟加载值"""
        from mc_agent_kit.performance import LazyLoader

        call_count = [0]

        def compute():
            call_count[0] += 1
            return "computed"

        lazy_value = LazyLoader.load(compute)

        # 未调用
        assert call_count[0] == 0

        # 调用后计算
        result = lazy_value()
        assert result == "computed"
        assert call_count[0] == 1

        # 再次调用不重新计算
        result = lazy_value()
        assert call_count[0] == 1


class TestIteration48Integration:
    """迭代 #48 集成测试"""

    def test_full_conversation_flow(self):
        """测试完整对话流程"""
        from mc_agent_kit.skills import (
            ConversationManager,
            SmartRecommender,
            IntentType,
        )

        manager = ConversationManager()
        recommender = SmartRecommender()
        session = manager.create_session()

        # 用户询问创建实体
        result = manager.process_message(session, "如何创建自定义实体")
        assert result.intent == IntentType.CREATE_ENTITY

        # 获取推荐
        recommendations = recommender.recommend_apis(session, "创建实体")
        assert len(recommendations) > 0

        # 添加助手响应
        manager.add_assistant_response(
            session,
            f"您可以使用 {recommendations[0]['api']} API",
        )

        # 检查历史
        assert len(session.messages) == 2

    def test_code_analysis_flow(self):
        """测试代码分析流程"""
        from mc_agent_kit.skills import CodeContextAnalyzer

        analyzer = CodeContextAnalyzer()
        code = '''
from mod.common import *

def on_player_join(args):
    player_name = GetPlayerName(args['id'])
    BroadcastToAllClient(f"{player_name} 加入了游戏")

ListenEvent("OnAddServerPlayer", on_player_join)
'''
        info = analyzer.analyze(code)

        # 验证分析结果
        assert "GetPlayerName" in info.apis_used
        assert "BroadcastToAllClient" in info.apis_used
        assert "ListenEvent" in info.apis_used
        assert "OnAddServerPlayer" in info.events_used


class TestIteration48AcceptanceCriteria:
    """迭代 #48 验收标准测试"""

    def test_intent_recognition_accuracy(self):
        """测试意图识别准确率"""
        from mc_agent_kit.skills import IntentRecognizer, IntentType

        recognizer = IntentRecognizer()

        # 测试用例
        test_cases = [
            ("查找 CreateEntity API", IntentType.SEARCH_API),
            ("监听 OnServerStart 事件", IntentType.SEARCH_EVENT),
            ("创建一个自定义实体", IntentType.CREATE_ENTITY),
            ("帮我看看这个报错", IntentType.DIAGNOSE_ERROR),
            ("如何创建项目", IntentType.CREATE_PROJECT),
        ]

        correct = 0
        for text, expected in test_cases:
            result = recognizer.recognize(text)
            if result.intent == expected:
                correct += 1

        accuracy = correct / len(test_cases)
        assert accuracy >= 0.8  # 80% 准确率

    def test_cache_performance(self):
        """测试缓存性能"""
        from mc_agent_kit.performance import EnhancedLRUCache
        import time

        cache = EnhancedLRUCache(max_size=1000)

        # 预填充
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}")

        # 测试读取性能
        start = time.perf_counter()
        for i in range(100):
            cache.get(f"key_{i}")
        elapsed = time.perf_counter() - start

        # 100 次读取应该在 1ms 内完成
        assert elapsed < 0.001

    def test_conversation_memory(self):
        """测试对话记忆"""
        from mc_agent_kit.skills import ConversationManager, ConversationRole

        manager = ConversationManager()
        session = manager.create_session()

        # 添加多轮对话
        messages = [
            (ConversationRole.USER, "如何创建实体?"),
            (ConversationRole.ASSISTANT, "您可以使用 CreateEngineEntity API"),
            (ConversationRole.USER, "如何设置位置?"),
        ]

        for role, content in messages:
            session.add_message(role, content)

        # 验证历史记录
        recent = session.get_recent_messages(3)
        assert len(recent) == 3

    def test_code_analysis_accuracy(self):
        """测试代码分析准确率"""
        from mc_agent_kit.skills import CodeContextAnalyzer

        analyzer = CodeContextAnalyzer()

        code = '''
def spawn_entity():
    entity = CreateEngineEntity()
    SetEntityPos(entity, 0, 64, 0)
    return entity
'''
        info = analyzer.analyze(code)

        # 验证 API 提取
        assert "CreateEngineEntity" in info.apis_used
        assert "SetEntityPos" in info.apis_used

    def test_recommendation_relevance(self):
        """测试推荐相关性"""
        from mc_agent_kit.skills import SmartRecommender

        recommender = SmartRecommender()

        results = recommender.recommend_apis(None, "创建一个怪物实体", limit=5)

        # 应该有推荐结果
        assert len(results) > 0

        # 第一个推荐应该相关
        first = results[0]
        assert "Create" in first["api"] or "Entity" in first["api"]


class TestIteration48Performance:
    """迭代 #48 性能测试"""

    def test_intent_recognition_speed(self):
        """测试意图识别速度"""
        from mc_agent_kit.skills import IntentRecognizer

        recognizer = IntentRecognizer()

        start = time.perf_counter()
        for _ in range(100):
            recognizer.recognize("查找 CreateEntity API")
        elapsed = time.perf_counter() - start

        # 100 次识别应该在 100ms 内完成
        assert elapsed < 0.1

    def test_code_analysis_speed(self):
        """测试代码分析速度"""
        from mc_agent_kit.skills import CodeContextAnalyzer

        analyzer = CodeContextAnalyzer()
        code = '''
def func1(): pass
def func2(): pass
def func3(): pass
class MyClass:
    def method1(self): pass
    def method2(self): pass
'''

        start = time.perf_counter()
        for _ in range(100):
            analyzer.analyze(code)
        elapsed = time.perf_counter() - start

        # 100 次分析应该在 500ms 内完成
        assert elapsed < 0.5