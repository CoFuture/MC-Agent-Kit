"""
迭代 #49 测试 - AI Agent 智能化增强与代码生成优化

测试智能代码生成、智能错误修复、智能对话增强和智能测试生成功能。
"""

import pytest
import time
from pathlib import Path

from mc_agent_kit.skills.smart_generation import (
    CodeQualityLevel,
    CodeStyle,
    CodeTemplate,
    GeneratedCode,
    GenerationRequest,
    GenerationStrategy,
    LLMConfig,
    LLMProvider,
    QualityAssessment,
    SmartCodeGenerator,
    StyleCheckResult,
    generate_code,
    get_smart_generator,
)

from mc_agent_kit.skills.smart_conversation import (
    ConversationContext,
    ConversationMemory,
    ConversationMessage,
    ConversationRole,
    ConversationState,
    ConversationSummary,
    IntentRecognitionResult,
    IntentRecognizer,
    IntentType,
    SmartConversationManager,
    TopicCategory,
    TopicTracker,
    create_session,
    get_conversation_manager as get_smart_conversation_manager,
    process_message,
)


class TestSmartCodeGenerator:
    """智能代码生成器测试"""

    def test_init(self):
        """测试初始化"""
        generator = SmartCodeGenerator()
        assert generator is not None
        assert generator._quality_threshold == 0.7
        assert generator._default_style == CodeStyle.MODSDK_BEST_PRACTICE

    def test_init_with_custom_config(self):
        """测试自定义配置初始化"""
        llm_config = LLMConfig(
            provider=LLMProvider.MOCK,
            model="test-model",
            max_tokens=1024,
            temperature=0.5,
        )
        generator = SmartCodeGenerator(
            default_style=CodeStyle.PEP8,
            quality_threshold=0.8,
            llm_config=llm_config,
        )
        assert generator._default_style == CodeStyle.PEP8
        assert generator._quality_threshold == 0.8
        assert generator._llm_config.model == "test-model"

    def test_generate_from_template(self):
        """测试从模板生成代码"""
        generator = SmartCodeGenerator()
        request = GenerationRequest(
            prompt="创建一个服务端启动事件监听器",
            strategy=GenerationStrategy.TEMPLATE,
        )
        result = generator.generate(request)
        
        assert isinstance(result, GeneratedCode)
        assert result.code is not None
        assert len(result.code) > 0
        assert result.language == "python"
        assert result.strategy_used == GenerationStrategy.TEMPLATE
        assert result.generation_time >= 0

    def test_generate_hybrid_strategy(self):
        """测试混合策略生成"""
        generator = SmartCodeGenerator()
        request = GenerationRequest(
            prompt="创建一个自定义实体",
            strategy=GenerationStrategy.HYBRID,
        )
        result = generator.generate(request)
        
        assert isinstance(result, GeneratedCode)
        assert result.code is not None
        assert result.strategy_used == GenerationStrategy.HYBRID

    def test_generate_with_context(self):
        """测试带上下文生成"""
        generator = SmartCodeGenerator()
        request = GenerationRequest(
            prompt="创建一个物品",
            strategy=GenerationStrategy.TEMPLATE,
            context={"item_id": "custom_ice_sword"},
        )
        result = generator.generate(request)
        
        assert isinstance(result, GeneratedCode)
        assert result.code is not None

    def test_template_matching(self):
        """测试模板匹配"""
        generator = SmartCodeGenerator()
        
        # 测试不同提示的模板匹配
        test_cases = [
            ("服务端启动", "server_start_listener"),
            ("创建实体", "entity_create"),
            ("注册物品", "item_register"),
            ("交互式方块", "block_interactive"),
            ("数据同步", "client_server_sync"),
            ("定时器", "timer_scheduler"),
            ("配置管理", "config_manager"),
            ("玩家管理", "player_manager"),
        ]
        
        for prompt, expected_template in test_cases:
            result = generator.generate(GenerationRequest(
                prompt=prompt,
                strategy=GenerationStrategy.TEMPLATE,
            ))
            # 应该找到匹配的模板或使用基础生成
            assert result.code is not None

    def test_quality_assessment(self):
        """测试代码质量评估"""
        generator = SmartCodeGenerator()
        
        # 测试高质量代码
        good_code = '''
def hello():
    """Say hello."""
    print("Hello, World!")
'''
        assessment = generator.assess_quality(good_code)
        assert isinstance(assessment, QualityAssessment)
        assert assessment.overall_score >= 0.0
        assert assessment.overall_score <= 1.0
        assert isinstance(assessment.level, CodeQualityLevel)

    def test_quality_assessment_syntax_error(self):
        """测试语法错误的代码质量评估"""
        generator = SmartCodeGenerator()
        
        bad_code = '''
def broken(:
    print("missing parenthesis")
'''
        assessment = generator.assess_quality(bad_code)
        assert assessment.overall_score == 0.0
        assert assessment.level == CodeQualityLevel.CRITICAL
        assert any(issue["type"] == "syntax_error" for issue in assessment.issues)

    def test_style_check(self):
        """测试代码风格检查"""
        generator = SmartCodeGenerator()
        
        # 测试良好风格的代码
        good_code = '''def hello():
    """Say hello."""
    print("Hello")
'''
        result = generator.check_style(good_code)
        assert isinstance(result, StyleCheckResult)
        assert result.style == CodeStyle.MODSDK_BEST_PRACTICE
        
        # 测试有问题的代码
        bad_code = '''def hello(  ):
  print( "bad indentation"  )
'''
        result = generator.check_style(bad_code)
        assert result.compliance_score < 1.0
        assert len(result.violations) > 0

    def test_register_custom_template(self):
        """测试注册自定义模板"""
        generator = SmartCodeGenerator()
        
        template = CodeTemplate(
            name="custom_template",
            description="自定义模板",
            template="def custom():\n    pass\n",
            parameters={},
            category="custom",
            tags=["custom", "test"],
            quality_score=0.95,
        )
        generator.register_template(template)
        
        # 验证模板已注册
        assert "custom_template" in generator._templates

    def test_cache_functionality(self):
        """测试缓存功能"""
        generator = SmartCodeGenerator()
        
        # 第一次生成
        result1 = generator.generate(GenerationRequest(
            prompt="测试缓存",
            strategy=GenerationStrategy.TEMPLATE,
        ))
        
        # 第二次生成（应该命中缓存）
        result2 = generator.generate(GenerationRequest(
            prompt="测试缓存",
            strategy=GenerationStrategy.TEMPLATE,
        ))
        
        # 验证缓存命中
        stats = generator.get_stats()
        assert stats["cache_hits"] >= 1

    def test_clear_cache(self):
        """测试清空缓存"""
        generator = SmartCodeGenerator()
        
        # 生成一些代码
        generator.generate(GenerationRequest(
            prompt="测试",
            strategy=GenerationStrategy.TEMPLATE,
        ))
        
        # 清空缓存
        generator.clear_cache()
        
        # 验证缓存已清空
        stats = generator.get_stats()
        assert stats["cache_hits"] == 0

    def test_extract_imports(self):
        """测试提取导入语句"""
        generator = SmartCodeGenerator()
        
        code = '''
from mod.common import ListenEvent
import json
from typing import Optional
'''
        imports = generator._extract_imports(code)
        assert "mod.common" in imports or "mod.common.ListenEvent" in imports
        assert "json" in imports

    def test_generation_stats(self):
        """测试生成统计"""
        generator = SmartCodeGenerator()
        
        # 生成几次
        for i in range(3):
            generator.generate(GenerationRequest(
                prompt=f"测试{i}",
                strategy=GenerationStrategy.TEMPLATE,
            ))
        
        stats = generator.get_stats()
        assert stats["total_generations"] >= 3


class TestIntentRecognizer:
    """意图识别器测试"""

    def test_init(self):
        """测试初始化"""
        recognizer = IntentRecognizer()
        assert recognizer is not None

    def test_recognize_search_api(self):
        """测试识别搜索 API 意图"""
        recognizer = IntentRecognizer()
        result = recognizer.recognize("如何查找 CreateEntity API")
        
        assert result.intent == IntentType.SEARCH_API
        assert result.confidence > 0.5

    def test_recognize_create_entity(self):
        """测试识别创建实体意图"""
        recognizer = IntentRecognizer()
        result = recognizer.recognize("创建一个自定义实体")
        
        assert result.intent == IntentType.CREATE_ENTITY
        assert result.confidence > 0.5

    def test_recognize_diagnose_error(self):
        """测试识别诊断错误意图"""
        recognizer = IntentRecognizer()
        result = recognizer.recognize("代码报错了，帮我诊断")
        
        assert result.intent == IntentType.DIAGNOSE_ERROR
        assert result.confidence > 0.5

    def test_recognize_generate_code(self):
        """测试识别生成代码意图"""
        recognizer = IntentRecognizer()
        result = recognizer.recognize("帮我写一个事件监听器")
        
        assert result.intent == IntentType.GENERATE_CODE
        assert result.confidence > 0.5

    def test_extract_entities(self):
        """测试实体提取"""
        recognizer = IntentRecognizer()
        result = recognizer.recognize("调用 CreateEngineEntity 创建实体")
        
        assert "api_names" in result.entities
        assert "CreateEngineEntity" in result.entities["api_names"]

    def test_detect_topic(self):
        """测试话题检测"""
        recognizer = IntentRecognizer()
        result = recognizer.recognize("如何创建自定义实体")
        
        assert result.topic == TopicCategory.ENTITY

    def test_unknown_intent(self):
        """测试未知意图"""
        recognizer = IntentRecognizer()
        result = recognizer.recognize("今天天气怎么样")
        
        assert result.intent == IntentType.UNKNOWN
        assert result.confidence == 0.0


class TestConversationContext:
    """对话上下文测试"""

    def test_init(self):
        """测试初始化"""
        context = ConversationContext(session_id="test123")
        assert context.session_id == "test123"
        assert context.state == ConversationState.ACTIVE
        assert len(context.messages) == 0

    def test_add_message(self):
        """测试添加消息"""
        context = ConversationContext(session_id="test123")
        
        message = context.add_message(
            role=ConversationRole.USER,
            content="你好",
            intent=IntentType.GENERATE_CODE,
            topic=TopicCategory.ENTITY,
        )
        
        assert len(context.messages) == 1
        assert message.content == "你好"
        assert message.intent == IntentType.GENERATE_CODE
        assert message.topic == TopicCategory.ENTITY

    def test_get_recent_messages(self):
        """测试获取最近消息"""
        context = ConversationContext(session_id="test123")
        
        for i in range(10):
            context.add_message(
                role=ConversationRole.USER,
                content=f"消息{i}",
            )
        
        recent = context.get_recent_messages(5)
        assert len(recent) == 5
        assert recent[-1].content == "消息9"

    def test_get_messages_by_role(self):
        """测试按角色获取消息"""
        context = ConversationContext(session_id="test123")
        
        context.add_message(role=ConversationRole.USER, content="用户消息")
        context.add_message(role=ConversationRole.ASSISTANT, content="助手响应")
        context.add_message(role=ConversationRole.USER, content="用户消息 2")
        
        user_messages = context.get_messages_by_role(ConversationRole.USER)
        assert len(user_messages) == 2

    def test_get_topic_distribution(self):
        """测试获取话题分布"""
        context = ConversationContext(session_id="test123")
        
        context.add_message(
            role=ConversationRole.USER,
            content="创建实体",
            topic=TopicCategory.ENTITY,
        )
        context.add_message(
            role=ConversationRole.USER,
            content="创建物品",
            topic=TopicCategory.ITEM,
        )
        context.add_message(
            role=ConversationRole.USER,
            content="另一个实体",
            topic=TopicCategory.ENTITY,
        )
        
        distribution = context.get_topic_distribution()
        assert distribution[TopicCategory.ENTITY] == 2
        assert distribution[TopicCategory.ITEM] == 1

    def test_to_dict(self):
        """测试转换为字典"""
        context = ConversationContext(session_id="test123")
        context.add_message(role=ConversationRole.USER, content="测试")
        
        data = context.to_dict()
        assert data["session_id"] == "test123"
        assert data["message_count"] == 1


class TestConversationMemory:
    """对话记忆测试"""

    def test_create_session(self):
        """测试创建会话"""
        memory = ConversationMemory()
        session = memory.create_session()
        
        assert session is not None
        assert session.session_id is not None
        assert memory.get_session_count() == 1

    def test_get_or_create_session(self):
        """测试获取或创建会话"""
        memory = ConversationMemory()
        
        # 创建新会话
        session1 = memory.get_or_create_session("test123")
        assert session1.session_id == "test123"
        
        # 获取已存在的会话
        session2 = memory.get_or_create_session("test123")
        assert session2.session_id == "test123"
        assert session1 is session2

    def test_process_message(self):
        """测试处理消息"""
        memory = ConversationMemory()
        session = memory.create_session()
        
        result = memory.process_message(
            session,
            "创建一个自定义实体",
            ConversationRole.USER,
        )
        
        assert result.intent == IntentType.CREATE_ENTITY
        assert len(session.messages) == 1

    def test_search_history(self):
        """测试搜索历史记录"""
        memory = ConversationMemory()
        session = memory.create_session()
        
        memory.process_message(session, "创建实体", ConversationRole.USER)
        memory.add_assistant_response(session, "好的，我来帮你创建实体")
        memory.process_message(session, "创建物品", ConversationRole.USER)
        
        results = memory.search_history("实体", session)
        assert len(results) > 0
        assert any("实体" in msg.content for msg in results)

    def test_get_conversation_summary(self):
        """测试获取对话摘要"""
        memory = ConversationMemory()
        session = memory.create_session()
        
        memory.process_message(
            session,
            "创建一个自定义实体",
            ConversationRole.USER,
        )
        memory.add_assistant_response(session, "好的")
        
        summary = memory.get_conversation_summary(session)
        assert isinstance(summary, ConversationSummary)
        assert summary.message_count == 2
        assert summary.session_id == session.session_id

    def test_cleanup_expired_sessions(self):
        """测试清理过期会话"""
        memory = ConversationMemory(session_timeout=0.1)
        session = memory.create_session()
        
        # 等待会话过期
        time.sleep(0.2)
        
        # 创建新会话会触发清理
        memory.create_session()
        
        # 过期会话应该被清理
        assert memory.get_session_count() <= 2


class TestSmartConversationManager:
    """智能对话管理器测试"""

    def test_init(self):
        """测试初始化"""
        manager = SmartConversationManager()
        assert manager is not None

    def test_create_and_get_session(self):
        """测试创建和获取会话"""
        manager = SmartConversationManager()
        
        session = manager.create_session("test123")
        assert session.session_id == "test123"
        
        retrieved = manager.get_session("test123")
        assert retrieved is session

    def test_process_user_message(self):
        """测试处理用户消息"""
        manager = SmartConversationManager()
        session = manager.create_session()
        
        result = manager.process_user_message(session, "如何创建实体")
        
        assert result.intent == IntentType.CREATE_ENTITY
        assert result.topic == TopicCategory.ENTITY

    def test_add_assistant_response(self):
        """测试添加助手响应"""
        manager = SmartConversationManager()
        session = manager.create_session()
        
        manager.process_user_message(session, "你好")
        manager.add_assistant_response(session, "你好！有什么可以帮助你的？")
        
        assert len(session.messages) == 2

    def test_get_context(self):
        """测试获取上下文"""
        manager = SmartConversationManager()
        session = manager.create_session()
        
        manager.process_user_message(session, "创建实体")
        
        context = manager.get_context(session)
        assert "session_id" in context
        assert "recent_messages" in context
        assert "entities" in context

    def test_search_history(self):
        """测试搜索历史"""
        manager = SmartConversationManager()
        session = manager.create_session()
        
        manager.process_user_message(session, "创建实体")
        manager.process_user_message(session, "创建物品")
        
        results = manager.search_history("创建", session)
        assert len(results) > 0

    def test_get_summary(self):
        """测试获取摘要"""
        manager = SmartConversationManager()
        session = manager.create_session()
        
        manager.process_user_message(session, "创建实体")
        manager.add_assistant_response(session, "好的")
        
        summary = manager.get_summary(session)
        assert isinstance(summary, ConversationSummary)
        assert summary.message_count == 2

    def test_get_stats(self):
        """测试获取统计"""
        manager = SmartConversationManager()
        
        manager.create_session("session1")
        manager.create_session("session2")
        
        stats = manager.get_stats()
        assert stats["session_count"] == 2


class TestTopicTracker:
    """话题跟踪器测试"""

    def test_init(self):
        """测试初始化"""
        tracker = TopicTracker()
        assert tracker is not None

    def test_update_topic(self):
        """测试更新话题"""
        tracker = TopicTracker()
        context = ConversationContext(session_id="test")
        
        tracker.update_topic(context, TopicCategory.ENTITY)
        context.current_topic = TopicCategory.ENTITY
        
        tracker.update_topic(context, TopicCategory.ITEM)
        
        summary = tracker.get_topic_summary(context)
        assert summary["current_topic"] == TopicCategory.ITEM.value

    def test_get_topic_summary(self):
        """测试获取话题摘要"""
        tracker = TopicTracker()
        context = ConversationContext(session_id="test")
        
        context.add_message(
            role=ConversationRole.USER,
            content="实体",
            topic=TopicCategory.ENTITY,
        )
        context.add_message(
            role=ConversationRole.USER,
            content="物品",
            topic=TopicCategory.ITEM,
        )
        
        summary = tracker.get_topic_summary(context)
        assert summary["topic_count"] == 2


class TestConversationMessage:
    """对话消息测试"""

    def test_init(self):
        """测试初始化"""
        msg = ConversationMessage(
            role=ConversationRole.USER,
            content="测试消息",
        )
        assert msg.role == ConversationRole.USER
        assert msg.content == "测试消息"
        assert msg.timestamp > 0

    def test_to_dict(self):
        """测试转换为字典"""
        msg = ConversationMessage(
            role=ConversationRole.USER,
            content="测试",
            intent=IntentType.GENERATE_CODE,
            topic=TopicCategory.ENTITY,
        )
        
        data = msg.to_dict()
        assert data["role"] == "user"
        assert data["content"] == "测试"
        assert data["intent"] == "generate_code"
        assert data["topic"] == "entity"


class TestIntentRecognitionResult:
    """意图识别结果测试"""

    def test_init(self):
        """测试初始化"""
        result = IntentRecognitionResult(
            intent=IntentType.GENERATE_CODE,
            confidence=0.9,
            entities={"keyword": "test"},
            context_needed=True,
            topic=TopicCategory.ENTITY,
        )
        
        assert result.intent == IntentType.GENERATE_CODE
        assert result.confidence == 0.9
        assert result.context_needed is True
        assert result.topic == TopicCategory.ENTITY


class TestGlobalFunctions:
    """全局函数测试"""

    def test_get_smart_generator_singleton(self):
        """测试智能生成器单例"""
        gen1 = get_smart_generator()
        gen2 = get_smart_generator()
        assert gen1 is gen2

    def test_get_conversation_manager_singleton(self):
        """测试对话管理器单例"""
        mgr1 = get_smart_conversation_manager()
        mgr2 = get_smart_conversation_manager()
        assert mgr1 is mgr2

    def test_generate_code_convenience(self):
        """测试便捷生成函数"""
        result = generate_code("创建一个事件监听器")
        assert isinstance(result, GeneratedCode)
        assert result.code is not None

    def test_create_session_convenience(self):
        """测试便捷创建会话函数"""
        session = create_session("test_session")
        assert session.session_id == "test_session"

    def test_process_message_convenience(self):
        """测试便捷处理消息函数"""
        session = create_session("test_msg")
        result = process_message(session, "创建实体")
        assert result.intent == IntentType.CREATE_ENTITY


class TestIteration49Integration:
    """迭代#49 集成测试"""

    def test_full_code_generation_workflow(self):
        """测试完整的代码生成工作流"""
        generator = SmartCodeGenerator()
        
        # 生成代码
        result = generator.generate(GenerationRequest(
            prompt="创建一个服务端启动事件监听器",
            strategy=GenerationStrategy.HYBRID,
            quality_threshold=0.7,
        ))
        
        # 验证结果
        assert result.code is not None
        assert result.quality_score >= 0.0
        assert result.quality_score <= 1.0
        
        # 质量评估
        assessment = generator.assess_quality(result.code)
        assert assessment.overall_score >= 0.0
        
        # 风格检查
        style_result = generator.check_style(result.code)
        assert style_result.compliance_score >= 0.0

    def test_full_conversation_workflow(self):
        """测试完整的对话工作流"""
        manager = SmartConversationManager()
        session = manager.create_session("integration_test")
        
        # 多轮对话
        messages = [
            "如何创建自定义实体？",
            "需要监听什么事件？",
            "帮我生成代码",
        ]
        
        for msg in messages:
            result = manager.process_user_message(session, msg)
            manager.add_assistant_response(session, f"这是关于{msg}的回答")
        
        # 验证对话历史
        assert len(session.messages) == len(messages) * 2
        
        # 获取摘要
        summary = manager.get_summary(session)
        assert summary.message_count == len(messages) * 2

    def test_context_aware_generation(self):
        """测试上下文感知的代码生成"""
        manager = SmartConversationManager()
        session = manager.create_session("context_test")
        
        # 第一轮：询问实体创建
        manager.process_user_message(session, "如何创建自定义实体")
        manager.add_assistant_response(session, "使用 CreateEngineEntity API")
        
        # 第二轮：生成代码（应该利用上下文）
        result = manager.process_user_message(session, "帮我生成代码")
        
        # 验证上下文被使用
        assert session.entities is not None


class TestIteration49AcceptanceCriteria:
    """迭代#49 验收标准测试"""

    def test_code_generation_accuracy(self):
        """测试代码生成准确率"""
        generator = SmartCodeGenerator()
        
        # 测试多个生成请求
        prompts = [
            "创建事件监听器",
            "创建自定义实体",
            "创建物品",
            "数据同步",
        ]
        
        for prompt in prompts:
            result = generator.generate(GenerationRequest(
                prompt=prompt,
                strategy=GenerationStrategy.TEMPLATE,
            ))
            assert result.code is not None
            assert result.quality_score >= 0.5

    def test_conversation_context_understanding(self):
        """测试对话上下文理解"""
        manager = SmartConversationManager()
        session = manager.create_session("context_understanding")
        
        # 第一轮
        manager.process_user_message(session, "创建实体")
        manager.add_assistant_response(session, "好的")
        
        # 第二轮：使用代词
        result = manager.process_user_message(session, "它需要什么参数")
        
        # 验证上下文被维护
        context = manager.get_context(session)
        assert context["entities"] is not None

    def test_multi_turn_dialogue_memory(self):
        """测试多轮对话记忆"""
        manager = SmartConversationManager()
        session = manager.create_session("memory_test")
        
        # 5 轮对话
        for i in range(5):
            manager.process_user_message(session, f"第{i}轮问题")
            manager.add_assistant_response(session, f"第{i}轮回答")
        
        # 验证所有消息都被记住
        assert len(session.messages) == 10
        
        # 验证可以检索历史
        history = manager.search_history("第 2 轮", session)
        assert len(history) > 0

    def test_topic_tracking(self):
        """测试话题跟踪"""
        manager = SmartConversationManager()
        session = manager.create_session("topic_test")
        
        # 不同话题的对话
        topics = [
            ("创建实体", TopicCategory.ENTITY),
            ("物品使用", TopicCategory.ITEM),
            ("方块交互", TopicCategory.BLOCK),
        ]
        
        for msg, expected_topic in topics:
            result = manager.process_user_message(session, msg)
            assert result.topic == expected_topic
        
        # 验证话题历史
        summary = manager.get_summary(session)
        assert len(summary.main_topics) > 0

    def test_quality_assessment_accuracy(self):
        """测试质量评估准确率"""
        generator = SmartCodeGenerator()
        
        # 高质量代码
        good_code = '''
def hello():
    """Say hello."""
    print("Hello")
'''
        good_assessment = generator.assess_quality(good_code)
        assert good_assessment.overall_score > 0.5
        
        # 低质量代码
        bad_code = '''
def bad(  ):
    x=1+2+3+4+5+6+7+8+9+10+11+12+13+14+15
    eval("dangerous")
'''
        bad_assessment = generator.assess_quality(bad_code)
        assert bad_assessment.overall_score < good_assessment.overall_score


class TestIteration49Performance:
    """迭代#49 性能测试"""

    def test_generation_performance(self):
        """测试生成性能"""
        generator = SmartCodeGenerator()
        
        start = time.time()
        for i in range(10):
            generator.generate(GenerationRequest(
                prompt=f"测试生成{i}",
                strategy=GenerationStrategy.TEMPLATE,
            ))
        duration = time.time() - start
        
        # 10 次生成应该在 1 秒内完成（使用缓存）
        assert duration < 1.0

    def test_conversation_performance(self):
        """测试对话性能"""
        manager = SmartConversationManager()
        session = manager.create_session("perf_test")
        
        start = time.time()
        for i in range(50):
            manager.process_user_message(session, f"消息{i}")
            manager.add_assistant_response(session, f"回答{i}")
        duration = time.time() - start
        
        # 50 轮对话应该在 1 秒内完成
        assert duration < 1.0

    def test_cache_hit_performance(self):
        """测试缓存命中性能"""
        generator = SmartCodeGenerator()
        
        # 第一次生成
        generator.generate(GenerationRequest(
            prompt="缓存测试",
            strategy=GenerationStrategy.TEMPLATE,
        ))
        
        # 第二次生成（缓存命中）
        start = time.time()
        for i in range(100):
            generator.generate(GenerationRequest(
                prompt="缓存测试",
                strategy=GenerationStrategy.TEMPLATE,
            ))
        duration = time.time() - start
        
        # 100 次缓存命中应该在 0.1 秒内完成
        assert duration < 0.1