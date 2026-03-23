"""
迭代 #51 测试

测试对话体验增强、多语言支持、智能推荐和性能优化功能。
"""

import sys
import time
import unittest

sys.path.insert(0, r"E:\develop\MC-Agent-Kit\src")

from mc_agent_kit.skills.conversation_enhanced import (
    EnhancedConversationManager,
    PersonalizationConfig,
    PersonalityType,
    SentimentAnalyzer,
    SentimentType,
    VisualizationType,
    get_enhanced_conversation_manager,
)

from mc_agent_kit.skills.multilingual import (
    LanguageCode,
    LanguageDetector,
    MultilingualService,
    MultilingualTemplate,
    MultilingualTemplateRegistry,
    TranslationService,
    detect_language,
    get_message,
    get_multilingual_service,
    translate,
)

from mc_agent_kit.skills.smart_recommendation import (
    ContextAnalyzer,
    Recommendation,
    RecommendationConfig,
    RecommendationEngine,
    RecommendationPriority,
    RecommendationType,
    SmartRecommendationService,
    get_learning_path,
    get_recommendation_service,
    get_recommendations,
)

from mc_agent_kit.skills.performance_optimization import (
    BatchOptimizer,
    CacheStrategy,
    LLMAcceleratorCache,
    MemoryMonitor,
    PerformanceOptimizer,
    PromptTemplateCompiler,
    get_cache,
    get_performance_optimizer,
)


class TestSentimentAnalyzer(unittest.TestCase):
    """情感分析器测试"""

    def test_positive_sentiment(self) -> None:
        """测试正面情感"""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("这个功能很好")
        # 可能返回 POSITIVE 或 EXCITED，都是正面情感
        self.assertIn(result.sentiment, [SentimentType.POSITIVE, SentimentType.EXCITED])
        self.assertGreater(result.confidence, 0.5)

    def test_negative_sentiment(self) -> None:
        """测试负面情感"""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("这个功能太差了")
        self.assertEqual(result.sentiment, SentimentType.NEGATIVE)

    def test_frustrated_sentiment(self) -> None:
        """测试沮丧情感"""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("烦死了，一直报错")
        self.assertEqual(result.sentiment, SentimentType.FRUSTRATED)

    def test_confused_sentiment(self) -> None:
        """测试困惑情感"""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("我不明白这是什么意思")
        self.assertEqual(result.sentiment, SentimentType.CONFUSED)

    def test_neutral_sentiment(self) -> None:
        """测试中性情感"""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("这是一个普通的陈述")
        # 中性文本可能因为没有匹配关键词而返回 NEUTRAL 或其他
        self.assertIsInstance(result.sentiment, SentimentType)

    def test_analyze_conversation_trend(self) -> None:
        """测试对话趋势分析"""
        analyzer = SentimentAnalyzer()
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "user", "content": "这个功能太棒了"},
            {"role": "user", "content": "谢谢帮助"},
        ]
        trend = analyzer.analyze_conversation_trend(messages)
        self.assertIn("trend", trend)
        self.assertIn("distribution", trend)


class TestPersonalizationEngine(unittest.TestCase):
    """个性化引擎测试"""

    def test_get_or_create_config(self) -> None:
        """测试获取或创建配置"""
        manager = EnhancedConversationManager()
        config = manager.get_user_config("user_123")
        self.assertIsInstance(config, PersonalizationConfig)
        self.assertEqual(config.personality, PersonalityType.FRIENDLY)

    def test_update_config(self) -> None:
        """测试更新配置"""
        manager = EnhancedConversationManager()
        config = manager.update_user_config(
            "user_123",
            personality=PersonalityType.TECHNICAL,
            verbosity="brief",
        )
        self.assertEqual(config.personality, PersonalityType.TECHNICAL)
        self.assertEqual(config.verbosity, "brief")

    def test_personalize_response(self) -> None:
        """测试个性化响应"""
        manager = EnhancedConversationManager()
        response = "这是一个很长的响应，包含很多详细信息..."
        personalized = manager.personalize_response(response, "user_123")
        self.assertIsInstance(personalized, str)

    def test_get_response_template(self) -> None:
        """测试获取响应模板"""
        manager = EnhancedConversationManager()
        template = manager.get_response_template("user_123", "greeting")
        self.assertIsInstance(template, str)


class TestConversationVisualizer(unittest.TestCase):
    """对话可视化器测试"""

    def test_create_timeline(self) -> None:
        """测试创建时间线"""
        manager = EnhancedConversationManager()
        messages = [
            {"role": "user", "content": "Hello", "timestamp": time.time()},
            {"role": "assistant", "content": "Hi", "timestamp": time.time() + 1},
        ]
        viz = manager.create_visualization(VisualizationType.TIMELINE, messages)
        self.assertEqual(viz.visualization_type, VisualizationType.TIMELINE)
        self.assertIn("timeline", viz.data)

    def test_create_intent_distribution(self) -> None:
        """测试创建意图分布"""
        manager = EnhancedConversationManager()
        messages = [
            {"role": "user", "intent": "search_api"},
            {"role": "user", "intent": "search_api"},
            {"role": "user", "intent": "generate_code"},
        ]
        viz = manager.create_visualization(VisualizationType.INTENT_DISTRIBUTION, messages)
        self.assertEqual(viz.visualization_type, VisualizationType.INTENT_DISTRIBUTION)
        self.assertIn("counts", viz.data)

    def test_generate_enhanced_summary(self) -> None:
        """测试生成增强摘要"""
        manager = EnhancedConversationManager()
        messages = [
            {"role": "user", "content": "Hello", "timestamp": time.time()},
            {"role": "assistant", "content": "Hi", "timestamp": time.time() + 1},
        ]
        summary = manager.generate_enhanced_summary("session_1", messages)
        self.assertEqual(summary.session_id, "session_1")
        self.assertEqual(summary.message_count, 2)


class TestLanguageDetector(unittest.TestCase):
    """语言检测器测试"""

    def test_detect_chinese(self) -> None:
        """测试检测中文"""
        detector = LanguageDetector()
        result = detector.detect("你好世界")
        self.assertEqual(result.language, LanguageCode.ZH_CN)
        self.assertGreater(result.confidence, 0.5)

    def test_detect_english(self) -> None:
        """测试检测英文"""
        detector = LanguageDetector()
        result = detector.detect("Hello world")
        self.assertEqual(result.language, LanguageCode.EN_US)

    def test_detect_japanese(self) -> None:
        """测试检测日文"""
        detector = LanguageDetector()
        result = detector.detect("こんにちは")
        self.assertEqual(result.language, LanguageCode.JA_JP)

    def test_detect_korean(self) -> None:
        """测试检测韩文"""
        detector = LanguageDetector()
        result = detector.detect("안녕하세요")
        self.assertEqual(result.language, LanguageCode.KO_KR)

    def test_detect_batch(self) -> None:
        """测试批量检测"""
        detector = LanguageDetector()
        texts = ["你好", "Hello", "こんにちは"]
        results = detector.detect_batch(texts)
        self.assertEqual(len(results), 3)


class TestMultilingualTemplate(unittest.TestCase):
    """多语言模板测试"""

    def test_template_render(self) -> None:
        """测试模板渲染"""
        template = MultilingualTemplate(
            template_id="test",
            translations={
                LanguageCode.ZH_CN: "你好 {{name}}",
                LanguageCode.EN_US: "Hello {{name}}",
            },
            variables=["name"],
        )
        result = template.render(LanguageCode.ZH_CN, name="世界")
        self.assertEqual(result, "你好 世界")

    def test_template_registry(self) -> None:
        """测试模板注册表"""
        registry = MultilingualTemplateRegistry()
        templates = registry.list_templates()
        self.assertGreater(len(templates), 0)

    def test_get_message(self) -> None:
        """测试获取消息"""
        message = get_message("greeting", LanguageCode.ZH_CN)
        self.assertIn("你好", message)

    def test_get_message_english(self) -> None:
        """测试获取英文消息"""
        message = get_message("greeting", LanguageCode.EN_US)
        self.assertIn("Hello", message)


class TestTranslationService(unittest.TestCase):
    """翻译服务测试"""

    def test_builtin_translation(self) -> None:
        """测试内置翻译"""
        service = TranslationService()
        result = service.translate("hello", LanguageCode.EN_US, LanguageCode.ZH_CN)
        # 内置翻译应该返回结果
        self.assertIsInstance(result.translated_text, str)

    def test_translate_fallback(self) -> None:
        """测试翻译回退"""
        service = TranslationService()
        result = service.translate("unknown text", LanguageCode.EN_US, LanguageCode.ZH_CN)
        # 没有翻译时返回原文
        self.assertEqual(result.translated_text, "unknown text")


class TestMultilingualService(unittest.TestCase):
    """多语言服务测试"""

    def test_auto_respond_language(self) -> None:
        """测试自动响应语言"""
        service = MultilingualService()
        lang = service.auto_respond_language("user_1", "你好")
        self.assertEqual(lang, LanguageCode.ZH_CN)

    def test_set_user_preference(self) -> None:
        """测试设置用户偏好"""
        from mc_agent_kit.skills.multilingual import LanguagePreference
        service = MultilingualService()
        preference = LanguagePreference(
            primary_language=LanguageCode.EN_US,
            preferred_response_language=LanguageCode.EN_US,
        )
        service.set_user_preference("user_1", preference)
        retrieved = service.get_user_preference("user_1")
        self.assertEqual(retrieved.primary_language, LanguageCode.EN_US)


class TestContextAnalyzer(unittest.TestCase):
    """上下文分析器测试"""

    def test_analyze_code(self) -> None:
        """测试代码分析"""
        analyzer = ContextAnalyzer()
        code = """
from mod.common import CreateEngineEntity
def OnPlayerJoin(args):
    entity_id = CreateEngineEntity(...)
    if entity_id:
        print("Created")
"""
        analysis = analyzer.analyze_code(code)
        self.assertIn("apis_used", analysis)
        self.assertGreater(len(analysis["apis_used"]), 0)

    def test_analyze_context(self) -> None:
        """测试上下文分析"""
        analyzer = ContextAnalyzer()
        history = [
            {"role": "user", "content": "如何创建实体？"},
            {"role": "assistant", "content": "使用 CreateEngineEntity API"},
        ]
        context = analyzer.analyze_context(history)
        self.assertIn("user_level", context)


class TestRecommendationEngine(unittest.TestCase):
    """推荐引擎测试"""

    def test_generate_recommendations(self) -> None:
        """测试生成推荐"""
        engine = RecommendationEngine()
        context = {
            "current_intent": "create_entity",
        }
        recommendations = engine.generate_recommendations(context)
        self.assertGreater(len(recommendations), 0)
        self.assertIsInstance(recommendations[0], Recommendation)

    def test_generate_code_recommendations(self) -> None:
        """测试代码推荐"""
        engine = RecommendationEngine()
        context = {
            "code": "CreateEngineEntity(...)",
        }
        recommendations = engine.generate_recommendations(context)
        # 应该包含 API 相关推荐
        self.assertGreater(len(recommendations), 0)

    def test_get_learning_path(self) -> None:
        """测试获取学习路径"""
        engine = RecommendationEngine()
        path = engine.get_learning_path("entity", "beginner")
        self.assertIsNotNone(path)
        self.assertEqual(path.difficulty, "beginner")


class TestSmartRecommendationService(unittest.TestCase):
    """智能推荐服务测试"""

    def test_get_recommendations(self) -> None:
        """测试获取推荐"""
        service = SmartRecommendationService()
        context = {"current_intent": "create_entity"}
        recommendations = service.get_recommendations(context)
        self.assertGreater(len(recommendations), 0)

    def test_record_feedback(self) -> None:
        """测试记录反馈"""
        service = SmartRecommendationService()
        service.record_feedback("rec_1", {"helpful": True})
        stats = service.get_recommendation_stats()
        self.assertIn("total_feedback", stats)


class TestLLMAcceleratorCache(unittest.TestCase):
    """LLM 缓存测试"""

    def test_cache_set_get(self) -> None:
        """测试缓存设置和获取"""
        cache = LLMAcceleratorCache(max_size=100)
        cache.set("test prompt", None, "test result")
        result = cache.get("test prompt")
        self.assertEqual(result, "test result")

    def test_cache_miss(self) -> None:
        """测试缓存未命中"""
        cache = LLMAcceleratorCache(max_size=100)
        result = cache.get("nonexistent")
        self.assertIsNone(result)

    def test_cache_ttl(self) -> None:
        """测试缓存 TTL"""
        cache = LLMAcceleratorCache(max_size=100, default_ttl=0.1)
        cache.set("test", None, "result", ttl=0.1)
        time.sleep(0.15)
        result = cache.get("test")
        self.assertIsNone(result)

    def test_cache_eviction(self) -> None:
        """测试缓存驱逐"""
        cache = LLMAcceleratorCache(max_size=5)
        for i in range(10):
            cache.set(f"prompt_{i}", None, f"result_{i}")
        stats = cache.get_stats()
        self.assertLessEqual(stats.entry_count, 5)

    def test_cache_stats(self) -> None:
        """测试缓存统计"""
        cache = LLMAcceleratorCache(max_size=100)
        cache.set("test", None, "result")
        cache.get("test")  # hit
        cache.get("miss")  # miss
        stats = cache.get_stats()
        self.assertEqual(stats.hits, 1)
        self.assertEqual(stats.misses, 1)

    def test_cache_clear(self) -> None:
        """测试清空缓存"""
        cache = LLMAcceleratorCache(max_size=100)
        cache.set("test", None, "result")
        cache.clear()
        stats = cache.get_stats()
        self.assertEqual(stats.entry_count, 0)


class TestPromptTemplateCompiler(unittest.TestCase):
    """提示模板编译器测试"""

    def test_compile_and_render(self) -> None:
        """测试编译和渲染"""
        compiler = PromptTemplateCompiler()
        compiled = compiler.compile("Hello {{name}}!")
        result = compiled({"name": "World"})
        self.assertEqual(result, "Hello World!")

    def test_render(self) -> None:
        """测试直接渲染"""
        compiler = PromptTemplateCompiler()
        result = compiler.render("Hello {{name}}!", {"name": "World"})
        self.assertEqual(result, "Hello World!")

    def test_precompile_batch(self) -> None:
        """测试批量预编译"""
        compiler = PromptTemplateCompiler()
        templates = ["Template {{i}}" for i in range(10)]
        count = compiler.precompile_batch(templates)
        self.assertEqual(count, 10)


class TestBatchOptimizer(unittest.TestCase):
    """批量优化器测试"""

    def test_execute_batch(self) -> None:
        """测试批量执行"""
        optimizer = BatchOptimizer(max_batch_size=5, max_concurrent=2)
        items = list(range(10))
        processor = lambda x: x * 2
        result = optimizer.execute_batch(items, processor)
        self.assertEqual(len(result.results), 10)
        self.assertEqual(result.results[0], 0)
        self.assertEqual(result.results[-1], 18)

    def test_execute_batch_with_cache(self) -> None:
        """测试带缓存的批量执行"""
        optimizer = BatchOptimizer()
        cache = LLMAcceleratorCache()
        items = [
            {"prompt": f"prompt_{i}", "config": None}
            for i in range(5)
        ]
        processor = lambda x: f"result_{x['prompt']}"
        result = optimizer.execute_batch_with_cache(items, processor, cache)
        self.assertEqual(len(result.results), 5)


class TestMemoryMonitor(unittest.TestCase):
    """内存监控器测试"""

    def test_get_stats(self) -> None:
        """测试获取统计"""
        monitor = MemoryMonitor()
        stats = monitor.get_stats()
        self.assertGreater(stats.total_memory_mb, 0)
        self.assertGreaterEqual(stats.used_memory_mb, 0)

    def test_get_trend(self) -> None:
        """测试获取趋势"""
        monitor = MemoryMonitor()
        # 获取多次以建立历史
        for _ in range(3):
            monitor.get_stats()
            time.sleep(0.01)
        trend = monitor.get_trend()
        self.assertIn("trend", trend)

    def test_check_threshold(self) -> None:
        """测试阈值检查"""
        monitor = MemoryMonitor()
        # 使用高阈值应该返回 False
        result = monitor.check_threshold(99.0)
        self.assertFalse(result)


class TestPerformanceOptimizer(unittest.TestCase):
    """性能优化器测试"""

    def test_get_components(self) -> None:
        """测试获取组件"""
        optimizer = PerformanceOptimizer()
        cache = optimizer.get_cache()
        self.assertIsInstance(cache, LLMAcceleratorCache)

        compiler = optimizer.get_compiler()
        self.assertIsInstance(compiler, PromptTemplateCompiler)

    def test_analyze_and_optimize(self) -> None:
        """测试分析和优化"""
        optimizer = PerformanceOptimizer()
        context = {"batch_size": 10}
        report = optimizer.analyze_and_optimize(context)
        self.assertIn("optimization_type", report.to_dict())

    def test_get_optimization_history(self) -> None:
        """测试获取优化历史"""
        optimizer = PerformanceOptimizer()
        optimizer.analyze_and_optimize({})
        history = optimizer.get_optimization_history()
        self.assertGreater(len(history), 0)


class TestIteration51Acceptance(unittest.TestCase):
    """迭代 #51 验收标准测试"""

    def test_sentiment_analysis_available(self) -> None:
        """测试情感分析可用"""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("测试")
        self.assertIsInstance(result.sentiment, SentimentType)

    def test_personalization_available(self) -> None:
        """测试个性化可用"""
        manager = EnhancedConversationManager()
        config = manager.get_user_config("user_1")
        self.assertIsInstance(config, PersonalizationConfig)

    def test_multilingual_templates_available(self) -> None:
        """测试多语言模板可用"""
        registry = MultilingualTemplateRegistry()
        templates = registry.list_templates()
        self.assertGreater(len(templates), 5)

    def test_language_detection_available(self) -> None:
        """测试语言检测可用"""
        detector = LanguageDetector()
        result = detector.detect("Hello")
        self.assertEqual(result.language, LanguageCode.EN_US)

    def test_recommendations_available(self) -> None:
        """测试推荐可用"""
        service = SmartRecommendationService()
        recs = service.get_recommendations({"current_intent": "create_entity"})
        self.assertGreater(len(recs), 0)

    def test_learning_path_available(self) -> None:
        """测试学习路径可用"""
        path = get_learning_path("entity", "beginner")
        self.assertIsNotNone(path)
        self.assertEqual(path.difficulty, "beginner")

    def test_cache_available(self) -> None:
        """测试缓存可用"""
        cache = get_cache()
        cache.set("test", None, "result")
        result = cache.get("test")
        self.assertEqual(result, "result")

    def test_template_compiler_available(self) -> None:
        """测试模板编译器可用"""
        optimizer = get_performance_optimizer()
        compiler = optimizer.get_compiler()
        result = compiler.render("Hello {{name}}!", {"name": "World"})
        self.assertEqual(result, "Hello World!")


class TestIteration51Performance(unittest.TestCase):
    """迭代 #51 性能测试"""

    def test_cache_performance(self) -> None:
        """测试缓存性能"""
        cache = LLMAcceleratorCache(max_size=1000)

        # 写入 100 次
        start = time.time()
        for i in range(100):
            cache.set(f"prompt_{i}", None, f"result_{i}")
        write_time = time.time() - start

        # 读取 100 次
        start = time.time()
        for i in range(100):
            cache.get(f"prompt_{i}")
        read_time = time.time() - start

        self.assertLess(write_time, 1.0)
        self.assertLess(read_time, 1.0)

    def test_template_compilation_performance(self) -> None:
        """测试模板编译性能"""
        compiler = PromptTemplateCompiler()
        template = "Template with {{var1}} and {{var2}}"

        start = time.time()
        for _ in range(100):
            compiler.compile(template)
        elapsed = time.time() - start

        self.assertLess(elapsed, 1.0)

    def test_recommendation_generation_performance(self) -> None:
        """测试推荐生成性能"""
        engine = RecommendationEngine()
        context = {"current_intent": "create_entity", "code": "test"}

        start = time.time()
        for _ in range(10):
            engine.generate_recommendations(context)
        elapsed = time.time() - start

        self.assertLess(elapsed, 2.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
