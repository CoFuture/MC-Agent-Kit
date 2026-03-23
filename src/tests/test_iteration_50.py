"""
迭代 #50 测试

测试内容：
1. LLM 集成模块测试（OpenAI、Azure、Ollama、LM Studio、Mock）
2. 提示工程模块测试（模板、Few-shot、CoT）
3. 异步代码生成测试（异步生成、批量生成、缓存）
4. 集成测试
5. 性能测试
6. 验收标准测试
"""

import asyncio
import time
import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from mc_agent_kit.skills.llm_integration import (
    AzureOpenAIClient,
    ChatMessage,
    CostTracker,
    LLMClientFactory,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    LLMService,
    LMStudioClient,
    MessageRole,
    MockLLMClient,
    OllamaClient,
    OpenAIClient,
    StreamChunk,
    TokenUsage,
    chat,
    get_llm_service,
)
from mc_agent_kit.skills.prompt_engineering import (
    ChainOfThoughtConfig,
    ChainOfThoughtPrompter,
    FewShotConfig,
    FewShotExample,
    FewShotLearner,
    PromptEngineeringService,
    PromptOptimizer,
    PromptOptimizationResult,
    PromptTemplate,
    PromptTemplateRegistry,
    PromptTemplateType,
    ReasoningType,
    build_cot_prompt,
    get_prompt_service,
    render_prompt,
)
from mc_agent_kit.skills.async_generation import (
    AsyncCodeGenerator,
    AsyncGenerationResult,
    BatchGenerationConfig,
    BatchGenerationResult,
    IncrementalCache,
    LazyLoader,
    MemoryOptimizedGenerator,
    generate_code_async,
    generate_codes_batch_async,
    get_async_generator,
    get_memory_optimized_generator,
)
from mc_agent_kit.skills.smart_generation import (
    CodeStyle,
    GeneratedCode,
    GenerationRequest,
    GenerationStrategy,
)


# =============================================================================
# LLM Integration Tests
# =============================================================================


class TestLLMConfig(unittest.TestCase):
    """LLM 配置测试"""

    def test_openai_config(self) -> None:
        """测试 OpenAI 配置"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo",
            api_key="test-key",
        )
        self.assertEqual(config.provider, LLMProvider.OPENAI)
        self.assertEqual(config.model, "gpt-3.5-turbo")
        self.assertEqual(config.api_key, "test-key")

    def test_azure_config(self) -> None:
        """测试 Azure 配置"""
        config = LLMConfig(
            provider=LLMProvider.AZURE,
            model="gpt-4",
            api_key="test-key",
            base_url="https://test.openai.azure.com",
            api_version="2024-02-15-preview",
        )
        self.assertEqual(config.provider, LLMProvider.AZURE)
        self.assertEqual(config.api_version, "2024-02-15-preview")

    def test_ollama_config(self) -> None:
        """测试 Ollama 配置"""
        config = LLMConfig(
            provider=LLMProvider.OLLAMA,
            model="llama2",
            local_host="localhost",
            local_port=11434,
        )
        self.assertEqual(
            config.base_url,
            "http://localhost:11434",
        )

    def test_lm_studio_config(self) -> None:
        """测试 LM Studio 配置"""
        config = LLMConfig(
            provider=LLMProvider.LM_STUDIO,
            model="local-model",
            local_host="localhost",
        )
        self.assertEqual(
            config.base_url,
            "http://localhost:1234/v1",
        )


class TestChatMessage(unittest.TestCase):
    """聊天消息测试"""

    def test_user_message(self) -> None:
        """测试用户消息"""
        msg = ChatMessage(
            role=MessageRole.USER,
            content="Hello",
        )
        self.assertEqual(msg.role, MessageRole.USER)
        self.assertEqual(msg.content, "Hello")

    def test_system_message(self) -> None:
        """测试系统消息"""
        msg = ChatMessage(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant",
        )
        self.assertEqual(msg.role, MessageRole.SYSTEM)

    def test_message_to_dict(self) -> None:
        """测试消息转字典"""
        msg = ChatMessage(
            role=MessageRole.USER,
            content="Test",
            name="test_user",
        )
        d = msg.to_dict()
        self.assertEqual(d["role"], "user")
        self.assertEqual(d["content"], "Test")
        self.assertEqual(d["name"], "test_user")


class TestTokenUsage(unittest.TestCase):
    """Token 使用统计测试"""

    def test_token_usage_creation(self) -> None:
        """测试 Token 使用创建"""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )
        self.assertEqual(usage.prompt_tokens, 100)
        self.assertEqual(usage.completion_tokens, 50)
        self.assertEqual(usage.total_tokens, 150)

    def test_token_usage_add(self) -> None:
        """测试 Token 使用相加"""
        usage1 = TokenUsage(100, 50, 150)
        usage2 = TokenUsage(200, 100, 300)
        total = usage1 + usage2
        self.assertEqual(total.prompt_tokens, 300)
        self.assertEqual(total.completion_tokens, 150)
        self.assertEqual(total.total_tokens, 450)


class TestCostTracker(unittest.TestCase):
    """成本追踪器测试"""

    def test_cost_calculation(self) -> None:
        """测试成本计算"""
        tracker = CostTracker()
        usage = TokenUsage(1000, 500, 1500)
        cost = tracker.calculate_cost("gpt-3.5-turbo", usage)
        # gpt-3.5-turbo: prompt=$0.0005/1K, completion=$0.0015/1K
        expected = (1000 / 1000) * 0.0005 + (500 / 1000) * 0.0015
        self.assertAlmostEqual(cost, expected, places=4)

    def test_cost_recording(self) -> None:
        """测试成本记录"""
        tracker = CostTracker()
        usage = TokenUsage(1000, 500, 1500)
        cost = tracker.record_usage("gpt-3.5-turbo", usage)
        self.assertGreater(cost, 0)
        self.assertEqual(tracker.request_count, 1)

    def test_cost_stats(self) -> None:
        """测试成本统计"""
        tracker = CostTracker()
        usage = TokenUsage(1000, 500, 1500)
        tracker.record_usage("gpt-3.5-turbo", usage)
        stats = tracker.get_stats()
        self.assertEqual(stats["request_count"], 1)
        self.assertEqual(stats["total_tokens"], 1500)


class TestMockLLMClient(unittest.TestCase):
    """Mock LLM 客户端测试"""

    def test_mock_complete(self) -> None:
        """测试 Mock 完成对话"""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            model="mock-model",
        )
        client = MockLLMClient(config)
        messages = [
            ChatMessage(role=MessageRole.USER, content="create_entity")
        ]
        response = client.complete(messages)
        self.assertIsInstance(response, LLMResponse)
        self.assertTrue(len(response.content) > 0)
        self.assertEqual(response.cost, 0.0)

    def test_mock_stream(self) -> None:
        """测试 Mock 流式响应"""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            model="mock-model",
        )
        client = MockLLMClient(config)
        messages = [
            ChatMessage(role=MessageRole.USER, content="test")
        ]
        chunks: list[StreamChunk] = []

        def callback(chunk: StreamChunk) -> None:
            chunks.append(chunk)

        response = client.stream(messages, callback)
        self.assertGreater(len(chunks), 0)
        self.assertEqual(chunks[-1].content, response.content)


class TestLLMClientFactory(unittest.TestCase):
    """LLM 客户端工厂测试"""

    def test_create_openai_client(self) -> None:
        """测试创建 OpenAI 客户端"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo",
            api_key="test",
        )
        client = LLMClientFactory.create(config)
        self.assertIsInstance(client, OpenAIClient)

    def test_create_mock_client(self) -> None:
        """测试创建 Mock 客户端"""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            model="mock",
        )
        client = LLMClientFactory.create(config)
        self.assertIsInstance(client, MockLLMClient)

    def test_client_caching(self) -> None:
        """测试客户端缓存"""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            model="mock",
        )
        client1 = LLMClientFactory.create(config)
        client2 = LLMClientFactory.create(config)
        self.assertIs(client1, client2)


class TestLLMService(unittest.TestCase):
    """LLM 服务测试"""

    def test_llm_service_chat(self) -> None:
        """测试 LLM 服务聊天"""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            model="mock",
        )
        service = LLMService(config)
        messages = [
            ChatMessage(role=MessageRole.USER, content="Hello")
        ]
        response = service.chat(messages)
        self.assertIsInstance(response, LLMResponse)
        self.assertTrue(len(response.content) > 0)

    def test_llm_service_with_system_prompt(self) -> None:
        """测试带系统提示的聊天"""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            model="mock",
        )
        service = LLMService(config)
        messages = [
            ChatMessage(role=MessageRole.USER, content="Hello")
        ]
        response = service.chat(
            messages,
            system_prompt="You are helpful",
        )
        self.assertIsInstance(response, LLMResponse)

    def test_llm_service_template(self) -> None:
        """测试 LLM 服务模板"""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            model="mock",
        )
        service = LLMService(config)
        service.register_prompt_template(
            "test",
            "Hello {{name}}",
        )
        rendered = service.apply_prompt_template("test", {"name": "World"})
        self.assertEqual(rendered, "Hello World")


class TestConvenienceFunctions(unittest.TestCase):
    """便捷函数测试"""

    def test_chat_function(self) -> None:
        """测试 chat 便捷函数"""
        result = chat(
            "create_entity",
            config=LLMConfig(
                provider=LLMProvider.MOCK,
                model="mock",
            ),
        )
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


# =============================================================================
# Prompt Engineering Tests
# =============================================================================


class TestPromptTemplate(unittest.TestCase):
    """提示模板测试"""

    def test_template_creation(self) -> None:
        """测试模板创建"""
        template = PromptTemplate(
            name="test",
            template="Hello {{name}}",
            description="Test template",
            template_type=PromptTemplateType.USER,
            variables=["name"],
        )
        self.assertEqual(template.name, "test")
        self.assertEqual(template.variables, ["name"])

    def test_template_render(self) -> None:
        """测试模板渲染"""
        template = PromptTemplate(
            name="test",
            template="Hello {{name}}",
            description="Test",
            template_type=PromptTemplateType.USER,
        )
        result = template.render(name="World")
        self.assertEqual(result, "Hello World")


class TestPromptTemplateRegistry(unittest.TestCase):
    """提示模板注册表测试"""

    def test_registry_init(self) -> None:
        """测试注册表初始化"""
        registry = PromptTemplateRegistry()
        templates = registry.list_templates()
        self.assertGreater(len(templates), 0)

    def test_registry_get(self) -> None:
        """测试获取模板"""
        registry = PromptTemplateRegistry()
        template = registry.get("modsdk_entity_create")
        self.assertIsNotNone(template)
        self.assertEqual(template.name, "modsdk_entity_create")

    def test_registry_render(self) -> None:
        """测试渲染模板"""
        registry = PromptTemplateRegistry()
        result = registry.render(
            "modsdk_entity_create",
            entity_name="TestEntity",
            entity_type="monster",
            behavior="hostile",
        )
        self.assertIn("TestEntity", result)

    def test_registry_register(self) -> None:
        """测试注册模板"""
        registry = PromptTemplateRegistry()
        template = PromptTemplate(
            name="custom",
            template="Custom {{value}}",
            description="Custom template",
            template_type=PromptTemplateType.USER,
        )
        registry.register(template)
        result = registry.render("custom", value="test")
        self.assertEqual(result, "Custom test")


class TestFewShotExample(unittest.TestCase):
    """Few-shot 示例测试"""

    def test_example_format(self) -> None:
        """测试示例格式化"""
        example = FewShotExample(
            input="Create entity",
            output="code here",
            explanation="This creates an entity",
        )
        result = example.format(include_explanation=True)
        self.assertIn("输入:", result)
        self.assertIn("输出:", result)
        self.assertIn("解释:", result)

    def test_example_format_no_explanation(self) -> None:
        """测试示例格式化（无解释）"""
        example = FewShotExample(
            input="Create entity",
            output="code here",
        )
        result = example.format(include_explanation=False)
        self.assertNotIn("解释:", result)


class TestFewShotLearner(unittest.TestCase):
    """Few-shot 学习器测试"""

    def test_add_example(self) -> None:
        """测试添加示例"""
        learner = FewShotLearner()
        example = FewShotExample(
            input="test input",
            output="test output",
        )
        learner.add_example("test_category", example)
        examples = learner.get_examples("test_category")
        self.assertEqual(len(examples), 1)

    def test_add_examples(self) -> None:
        """测试批量添加示例"""
        learner = FewShotLearner()
        examples = [
            FewShotExample(input=f"input{i}", output=f"output{i}")
            for i in range(5)
        ]
        learner.add_examples("test", examples)
        retrieved = learner.get_examples("test")
        self.assertEqual(len(retrieved), 5)

    def test_max_examples_limit(self) -> None:
        """测试最大示例数限制"""
        config = FewShotConfig(max_examples=3)
        learner = FewShotLearner(config)
        examples = [
            FewShotExample(input=f"input{i}", output=f"output{i}")
            for i in range(10)
        ]
        learner.add_examples("test", examples)
        retrieved = learner.get_examples("test")
        self.assertEqual(len(retrieved), 3)

    def test_build_few_shot_prompt(self) -> None:
        """测试构建 Few-shot 提示"""
        learner = FewShotLearner()
        learner.add_example(
            "entity",
            FewShotExample(
                input="Create zombie",
                output="zombie code",
            ),
        )
        prompt = learner.build_few_shot_prompt(
            "entity",
            "Create an entity",
            "Create skeleton",
        )
        self.assertIn("Create zombie", prompt)
        self.assertIn("zombie code", prompt)


class TestChainOfThoughtPrompter(unittest.TestCase):
    """Chain-of-Thought 提示器测试"""

    def test_cot_prompt_basic(self) -> None:
        """测试基本 CoT 提示"""
        prompter = ChainOfThoughtPrompter()
        prompt = prompter.build_cot_prompt("What is 2+2?")
        self.assertIn("让我们一步步思考", prompt)

    def test_cot_prompt_with_context(self) -> None:
        """测试带上下文的 CoT 提示"""
        prompter = ChainOfThoughtPrompter()
        prompt = prompter.build_cot_prompt(
            "What is the answer?",
            context="Background info",
        )
        self.assertIn("背景信息:", prompt)
        self.assertIn("Background info", prompt)

    def test_extract_reasoning(self) -> None:
        """测试提取推理过程"""
        prompter = ChainOfThoughtPrompter(
            ChainOfThoughtConfig(
                final_answer_prompt="因此，最终答案是："
            )
        )
        response = """
        首先分析问题...
        然后考虑解决方案...
        因此，最终答案是：42
        """
        result = prompter.extract_reasoning(response)
        self.assertIn("首先分析", result["reasoning"])
        self.assertEqual(result["final_answer"], "42")


class TestPromptOptimizer(unittest.TestCase):
    """提示优化器测试"""

    def test_optimize_whitespace(self) -> None:
        """测试空白优化"""
        optimizer = PromptOptimizer()
        prompt = "Hello    World\n\n\nTest"
        result = optimizer.optimize(prompt, preserve_structure=False)
        self.assertEqual(result.optimized_prompt, "Hello World Test")
        self.assertIn("whitespace_compression", result.techniques_applied)

    def test_optimize_preserve_structure(self) -> None:
        """测试保留结构优化"""
        optimizer = PromptOptimizer()
        prompt = "Hello    World\n\n\nTest"
        result = optimizer.optimize(prompt, preserve_structure=True)
        # 保留结构时不应压缩空白
        self.assertNotEqual(result.optimized_prompt, "Hello World Test")

    def test_optimize_truncation(self) -> None:
        """测试截断优化"""
        optimizer = PromptOptimizer()
        prompt = "A" * 100
        result = optimizer.optimize(prompt, max_length=50)
        self.assertEqual(len(result.optimized_prompt), 50)
        self.assertIn("truncation", result.techniques_applied)

    def test_optimize_duplicate_removal(self) -> None:
        """测试重复内容移除"""
        optimizer = PromptOptimizer()
        prompt = "line1\nline2\nline1\nline3"
        result = optimizer.optimize(prompt)
        self.assertIn("duplicate_removal", result.techniques_applied)


class TestPromptEngineeringService(unittest.TestCase):
    """提示工程服务测试"""

    def test_service_render_template(self) -> None:
        """测试服务渲染模板"""
        service = PromptEngineeringService()
        result = service.render_template(
            "modsdk_entity_create",
            entity_name="Test",
            entity_type="monster",
            behavior="hostile",
        )
        self.assertIn("Test", result)

    def test_service_build_cot_prompt(self) -> None:
        """测试服务构建 CoT 提示"""
        service = PromptEngineeringService()
        result = service.build_cot_prompt("How to optimize code?")
        self.assertIn("让我们一步步思考", result)

    def test_service_add_few_shot_example(self) -> None:
        """测试服务添加 Few-shot 示例"""
        service = PromptEngineeringService()
        service.add_few_shot_example(
            "test",
            "input",
            "output",
            "explanation",
        )
        examples = service.few_shot_learner.get_examples("test")
        self.assertEqual(len(examples), 1)

    def test_service_optimize_prompt(self) -> None:
        """测试服务优化提示"""
        service = PromptEngineeringService()
        result = service.optimize_prompt("Hello    World")
        self.assertIsInstance(result, PromptOptimizationResult)


class TestConvenienceFunctionsPrompt(unittest.TestCase):
    """提示便捷函数测试"""

    def test_render_prompt_function(self) -> None:
        """测试 render_prompt 便捷函数"""
        result = render_prompt(
            "modsdk_entity_create",
            entity_name="Test",
            entity_type="monster",
            behavior="hostile",
        )
        self.assertIn("Test", result)

    def test_build_cot_prompt_function(self) -> None:
        """测试 build_cot_prompt 便捷函数"""
        result = build_cot_prompt("Test question")
        self.assertIsInstance(result, str)


# =============================================================================
# Async Generation Tests
# =============================================================================


class TestIncrementalCache(unittest.TestCase):
    """增量缓存测试"""

    def test_cache_set_get(self) -> None:
        """测试缓存设置和获取"""
        cache = IncrementalCache()
        code = GeneratedCode(
            code="test code",
            language="python",
            template_used=None,
            quality_score=0.9,
            style_compliance=0.95,
            modsdk_compatible=True,
            imports_needed=[],
            dependencies=[],
            warnings=[],
            suggestions=[],
        )
        cache.set(
            "test prompt",
            GenerationStrategy.TEMPLATE,
            CodeStyle.MODSDK_BEST_PRACTICE,
            code,
        )
        retrieved = cache.get(
            "test prompt",
            GenerationStrategy.TEMPLATE,
            CodeStyle.MODSDK_BEST_PRACTICE,
        )
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.code, "test code")

    def test_cache_miss(self) -> None:
        """测试缓存未命中"""
        cache = IncrementalCache()
        result = cache.get(
            "nonexistent",
            GenerationStrategy.TEMPLATE,
            CodeStyle.MODSDK_BEST_PRACTICE,
        )
        self.assertIsNone(result)

    def test_cache_expiration(self) -> None:
        """测试缓存过期"""
        cache = IncrementalCache(ttl=0.1)
        code = GeneratedCode(
            code="test",
            language="python",
            template_used=None,
            quality_score=0.9,
            style_compliance=0.9,
            modsdk_compatible=True,
            imports_needed=[],
            dependencies=[],
            warnings=[],
            suggestions=[],
        )
        cache.set(
            "test",
            GenerationStrategy.TEMPLATE,
            CodeStyle.MODSDK_BEST_PRACTICE,
            code,
        )
        time.sleep(0.15)
        result = cache.get(
            "test",
            GenerationStrategy.TEMPLATE,
            CodeStyle.MODSDK_BEST_PRACTICE,
        )
        self.assertIsNone(result)

    def test_cache_invalidate(self) -> None:
        """测试缓存失效"""
        cache = IncrementalCache()
        code = GeneratedCode(
            code="test",
            language="python",
            template_used=None,
            quality_score=0.9,
            style_compliance=0.9,
            modsdk_compatible=True,
            imports_needed=[],
            dependencies=[],
            warnings=[],
            suggestions=[],
        )
        cache.set(
            "test1",
            GenerationStrategy.TEMPLATE,
            CodeStyle.MODSDK_BEST_PRACTICE,
            code,
        )
        cache.set(
            "test2",
            GenerationStrategy.LLM,
            CodeStyle.MODSDK_BEST_PRACTICE,
            code,
        )
        count = cache.invalidate(strategy=GenerationStrategy.TEMPLATE)
        self.assertEqual(count, 1)

    def test_cache_stats(self) -> None:
        """测试缓存统计"""
        cache = IncrementalCache()
        code = GeneratedCode(
            code="test",
            language="python",
            template_used=None,
            quality_score=0.9,
            style_compliance=0.9,
            modsdk_compatible=True,
            imports_needed=[],
            dependencies=[],
            warnings=[],
            suggestions=[],
        )
        cache.set(
            "test",
            GenerationStrategy.TEMPLATE,
            CodeStyle.MODSDK_BEST_PRACTICE,
            code,
        )
        cache.get(
            "test",
            GenerationStrategy.TEMPLATE,
            CodeStyle.MODSDK_BEST_PRACTICE,
        )
        stats = cache.get_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["size"], 1)


class TestAsyncCodeGenerator(unittest.TestCase):
    """异步代码生成器测试"""

    def test_async_generate(self) -> None:
        """测试异步生成"""
        generator = AsyncCodeGenerator()
        request = GenerationRequest(
            prompt="create_entity",
            strategy=GenerationStrategy.TEMPLATE,
        )
        result = asyncio.run(generator.generate_async(request))
        self.assertIsInstance(result, AsyncGenerationResult)
        self.assertIsNotNone(result.code)
        self.assertFalse(result.cached)

    def test_async_generate_cached(self) -> None:
        """测试异步生成（缓存命中）"""
        generator = AsyncCodeGenerator()
        request = GenerationRequest(
            prompt="test_cached",
            strategy=GenerationStrategy.TEMPLATE,
        )
        # 第一次生成
        result1 = asyncio.run(generator.generate_async(request))
        # 第二次生成（应该命中缓存）
        result2 = asyncio.run(generator.generate_async(request))
        self.assertTrue(result2.cached)

    def test_async_batch_generate(self) -> None:
        """测试异步批量生成"""
        generator = AsyncCodeGenerator()
        requests = [
            GenerationRequest(
                prompt=f"prompt{i}",
                strategy=GenerationStrategy.TEMPLATE,
            )
            for i in range(3)
        ]
        result = asyncio.run(
            generator.generate_batch_async(requests)
        )
        self.assertIsInstance(result, BatchGenerationResult)
        self.assertEqual(result.total_requests, 3)
        self.assertGreaterEqual(result.successful, 0)

    def test_sync_batch_generate(self) -> None:
        """测试同步批量生成"""
        generator = AsyncCodeGenerator()
        requests = [
            GenerationRequest(
                prompt=f"prompt{i}",
                strategy=GenerationStrategy.TEMPLATE,
            )
            for i in range(3)
        ]
        result = generator.generate_batch_sync(requests)
        self.assertIsInstance(result, BatchGenerationResult)
        self.assertEqual(result.total_requests, 3)

    def test_cache_stats(self) -> None:
        """测试缓存统计"""
        generator = AsyncCodeGenerator()
        request = GenerationRequest(
            prompt="stats_test",
            strategy=GenerationStrategy.TEMPLATE,
        )
        asyncio.run(generator.generate_async(request))
        asyncio.run(generator.generate_async(request))
        stats = generator.get_cache_stats()
        self.assertIn("hits", stats)
        self.assertIn("misses", stats)


class TestMemoryOptimizedGenerator(unittest.TestCase):
    """内存优化生成器测试"""

    def test_memory_generate(self) -> None:
        """测试内存优化生成"""
        generator = MemoryOptimizedGenerator()
        request = GenerationRequest(
            prompt="test",
            strategy=GenerationStrategy.TEMPLATE,
        )
        code = generator.generate(request)
        self.assertIsInstance(code, GeneratedCode)

    def test_memory_pool(self) -> None:
        """测试内存池"""
        generator = MemoryOptimizedGenerator()
        request = GenerationRequest(
            prompt="test",
            strategy=GenerationStrategy.TEMPLATE,
        )
        generator.generate(request)
        stats = generator.get_memory_stats()
        self.assertIn("cached_count", stats)
        self.assertGreaterEqual(stats["cached_count"], 0)

    def test_clear_pool(self) -> None:
        """测试清空内存池"""
        generator = MemoryOptimizedGenerator()
        request = GenerationRequest(
            prompt="test",
            strategy=GenerationStrategy.TEMPLATE,
        )
        generator.generate(request)
        generator.clear_pool()
        stats = generator.get_memory_stats()
        self.assertEqual(stats["cached_count"], 0)


class TestLazyLoader(unittest.TestCase):
    """懒加载器测试"""

    def test_lazy_loading(self) -> None:
        """测试懒加载"""
        created = [False]

        def factory() -> AsyncCodeGenerator:
            created[0] = True
            return AsyncCodeGenerator()

        loader = LazyLoader(factory)
        self.assertFalse(created[0])
        loader.get()
        self.assertTrue(created[0])

    def test_lazy_singleton(self) -> None:
        """测试懒加载单例"""
        loader = LazyLoader(AsyncCodeGenerator)
        instance1 = loader.get()
        instance2 = loader.get()
        self.assertIs(instance1, instance2)

    def test_lazy_reset(self) -> None:
        """测试懒加载重置"""
        loader = LazyLoader(AsyncCodeGenerator)
        loader.get()
        loader.reset()
        instance = loader.get()
        self.assertIsNotNone(instance)


class TestConvenienceFunctionsAsync(unittest.TestCase):
    """异步便捷函数测试"""

    def test_generate_code_async(self) -> None:
        """测试 generate_code_async 便捷函数"""
        result = asyncio.run(
            generate_code_async(
                "create_entity",
                strategy=GenerationStrategy.TEMPLATE,
            )
        )
        self.assertIsInstance(result, GeneratedCode)

    def test_generate_codes_batch_async(self) -> None:
        """测试 generate_codes_batch_async 便捷函数"""
        result = asyncio.run(
            generate_codes_batch_async(
                ["prompt1", "prompt2"],
                strategy=GenerationStrategy.TEMPLATE,
            )
        )
        self.assertIsInstance(result, BatchGenerationResult)


# =============================================================================
# Integration Tests
# =============================================================================


class TestIteration50Integration(unittest.TestCase):
    """迭代 #50 集成测试"""

    def test_llm_with_prompt_engineering(self) -> None:
        """测试 LLM 与提示工程集成"""
        from mc_agent_kit.skills import (
            IntegrationLLMConfig,
            LLMProvider,
            PromptEngineeringService,
            LLMService,
        )

        llm_config = IntegrationLLMConfig(
            provider=LLMProvider.MOCK,
            model="mock",
        )
        llm_service = LLMService(llm_config)
        prompt_service = PromptEngineeringService(llm_config)
        prompt_service.set_llm_service(llm_service)

        result = prompt_service.execute_with_template(
            "modsdk_entity_create",
            {
                "entity_name": "TestEntity",
                "entity_type": "monster",
                "behavior": "hostile",
            },
        )
        self.assertIsInstance(result, LLMResponse)

    def test_async_with_cache(self) -> None:
        """测试异步生成与缓存集成"""
        from mc_agent_kit.skills import (
            AsyncCodeGenerator,
            IncrementalCache,
            GenerationStrategy,
            GenerationRequest,
        )

        cache = IncrementalCache()
        generator = AsyncCodeGenerator(cache=cache)
        request = GenerationRequest(
            prompt="integration_test",
            strategy=GenerationStrategy.TEMPLATE,
        )

        result1 = asyncio.run(generator.generate_async(request))
        result2 = asyncio.run(generator.generate_async(request))

        self.assertFalse(result1.cached)
        self.assertTrue(result2.cached)


class TestIteration50AcceptanceCriteria(unittest.TestCase):
    """迭代 #50 验收标准测试"""

    def test_llm_providers_supported(self) -> None:
        """测试支持多种 LLM 提供者"""
        from mc_agent_kit.skills import (
            LLMProvider,
            OpenAIClient,
            AzureOpenAIClient,
            OllamaClient,
            LMStudioClient,
            MockLLMClient,
            LLMConfig,
            LLMClientFactory,
        )

        providers = [
            (LLMProvider.OPENAI, OpenAIClient),
            (LLMProvider.AZURE, AzureOpenAIClient),
            (LLMProvider.OLLAMA, OllamaClient),
            (LLMProvider.LM_STUDIO, LMStudioClient),
            (LLMProvider.MOCK, MockLLMClient),
        ]

        for provider, expected_class in providers:
            config = LLMConfig(
                provider=provider,
                model="test",
                api_key="test" if provider != LLMProvider.MOCK else None,
            )
            client = LLMClientFactory.create(config)
            self.assertIsInstance(client, expected_class)

    def test_prompt_templates_available(self) -> None:
        """测试提示模板可用"""
        from mc_agent_kit.skills import PromptTemplateRegistry

        registry = PromptTemplateRegistry()
        templates = registry.list_templates()
        self.assertGreater(len(templates), 5)

    def test_few_shot_learning(self) -> None:
        """测试 Few-shot Learning"""
        from mc_agent_kit.skills import FewShotLearner, FewShotExample

        learner = FewShotLearner()
        learner.add_example(
            "test",
            FewShotExample(
                input="test input",
                output="test output",
            ),
        )
        examples = learner.get_examples("test")
        self.assertEqual(len(examples), 1)

    def test_chain_of_thought(self) -> None:
        """测试 Chain-of-Thought"""
        from mc_agent_kit.skills import ChainOfThoughtPrompter

        prompter = ChainOfThoughtPrompter()
        prompt = prompter.build_cot_prompt("Test question")
        self.assertIn("让我们一步步思考", prompt)

    def test_async_generation(self) -> None:
        """测试异步代码生成"""
        from mc_agent_kit.skills import (
            AsyncCodeGenerator,
            GenerationRequest,
            GenerationStrategy,
        )

        generator = AsyncCodeGenerator()
        request = GenerationRequest(
            prompt="test",
            strategy=GenerationStrategy.TEMPLATE,
        )
        result = asyncio.run(generator.generate_async(request))
        self.assertIsNotNone(result.code)

    def test_batch_generation(self) -> None:
        """测试批量生成"""
        from mc_agent_kit.skills import (
            AsyncCodeGenerator,
            GenerationRequest,
            GenerationStrategy,
        )

        generator = AsyncCodeGenerator()
        requests = [
            GenerationRequest(
                prompt=f"prompt{i}",
                strategy=GenerationStrategy.TEMPLATE,
            )
            for i in range(5)
        ]
        result = asyncio.run(
            generator.generate_batch_async(requests)
        )
        self.assertEqual(result.total_requests, 5)

    def test_incremental_cache(self) -> None:
        """测试增量缓存"""
        from mc_agent_kit.skills import (
            IncrementalCache,
            GeneratedCode,
            GenerationStrategy,
            CodeStyle,
        )

        cache = IncrementalCache()
        code = GeneratedCode(
            code="test",
            language="python",
            template_used=None,
            quality_score=0.9,
            style_compliance=0.9,
            modsdk_compatible=True,
            imports_needed=[],
            dependencies=[],
            warnings=[],
            suggestions=[],
        )
        cache.set(
            "test",
            GenerationStrategy.TEMPLATE,
            CodeStyle.MODSDK_BEST_PRACTICE,
            code,
        )
        retrieved = cache.get(
            "test",
            GenerationStrategy.TEMPLATE,
            CodeStyle.MODSDK_BEST_PRACTICE,
        )
        self.assertIsNotNone(retrieved)


class TestIteration50Performance(unittest.TestCase):
    """迭代 #50 性能测试"""

    def test_cache_performance(self) -> None:
        """测试缓存性能"""
        from mc_agent_kit.skills import (
            IncrementalCache,
            GeneratedCode,
            GenerationStrategy,
            CodeStyle,
        )

        cache = IncrementalCache()
        code = GeneratedCode(
            code="test",
            language="python",
            template_used=None,
            quality_score=0.9,
            style_compliance=0.9,
            modsdk_compatible=True,
            imports_needed=[],
            dependencies=[],
            warnings=[],
            suggestions=[],
        )

        # 写入 100 次
        start = time.time()
        for i in range(100):
            cache.set(
                f"test{i}",
                GenerationStrategy.TEMPLATE,
                CodeStyle.MODSDK_BEST_PRACTICE,
                code,
            )
        write_time = time.time() - start

        # 读取 100 次
        start = time.time()
        for i in range(100):
            cache.get(
                f"test{i}",
                GenerationStrategy.TEMPLATE,
                CodeStyle.MODSDK_BEST_PRACTICE,
            )
        read_time = time.time() - start

        self.assertLess(write_time, 1.0)
        self.assertLess(read_time, 1.0)

    def test_batch_generation_performance(self) -> None:
        """测试批量生成性能"""
        from mc_agent_kit.skills import (
            AsyncCodeGenerator,
            GenerationRequest,
            GenerationStrategy,
        )

        generator = AsyncCodeGenerator()
        requests = [
            GenerationRequest(
                prompt=f"prompt{i}",
                strategy=GenerationStrategy.TEMPLATE,
            )
            for i in range(10)
        ]

        start = time.time()
        result = asyncio.run(
            generator.generate_batch_async(
                requests,
                BatchGenerationConfig(max_concurrent=5),
            )
        )
        elapsed = time.time() - start

        self.assertEqual(result.total_requests, 10)
        self.assertLess(elapsed, 5.0)

    def test_prompt_optimization_performance(self) -> None:
        """测试提示优化性能"""
        from mc_agent_kit.skills import PromptOptimizer

        optimizer = PromptOptimizer()
        prompt = "A" * 10000

        start = time.time()
        for _ in range(100):
            optimizer.optimize(prompt)
        elapsed = time.time() - start

        self.assertLess(elapsed, 1.0)


if __name__ == "__main__":
    unittest.main()
