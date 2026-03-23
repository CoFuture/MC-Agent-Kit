"""
迭代 #50 简化测试

直接测试新模块，避免导入链问题。
"""

import asyncio
import sys
import time
import unittest

sys.path.insert(0, r"E:\develop\MC-Agent-Kit\src")

# 直接导入新模块，避免通过 __init__.py
import importlib.util

# 加载 llm_integration
spec = importlib.util.spec_from_file_location(
    "llm_integration",
    r"E:\develop\MC-Agent-Kit\src\mc_agent_kit\skills\llm_integration.py"
)
llm_integration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llm_integration)

# 加载 smart_generation (需要先加载)
spec = importlib.util.spec_from_file_location(
    "smart_generation",
    r"E:\develop\MC-Agent-Kit\src\mc_agent_kit\skills\smart_generation.py"
)
smart_generation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smart_generation)

# 加载 prompt_engineering
spec = importlib.util.spec_from_file_location(
    "prompt_engineering",
    r"E:\develop\MC-Agent-Kit\src\mc_agent_kit\skills\prompt_engineering.py"
)
prompt_engineering = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prompt_engineering)

# 加载 async_generation
spec = importlib.util.spec_from_file_location(
    "async_generation",
    r"E:\develop\MC-Agent-Kit\src\mc_agent_kit\skills\async_generation.py"
)
async_generation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(async_generation)

# 从加载的模块导入
ChatMessage = llm_integration.ChatMessage
CostTracker = llm_integration.CostTracker
LLMConfig = llm_integration.LLMConfig
LLMProvider = llm_integration.LLMProvider
LLMResponse = llm_integration.LLMResponse
MessageRole = llm_integration.MessageRole
MockLLMClient = llm_integration.MockLLMClient
StreamChunk = llm_integration.StreamChunk
TokenUsage = llm_integration.TokenUsage

ChainOfThoughtConfig = prompt_engineering.ChainOfThoughtConfig
ChainOfThoughtPrompter = prompt_engineering.ChainOfThoughtPrompter
FewShotConfig = prompt_engineering.FewShotConfig
FewShotExample = prompt_engineering.FewShotExample
FewShotLearner = prompt_engineering.FewShotLearner
PromptOptimizer = prompt_engineering.PromptOptimizer
PromptTemplate = prompt_engineering.PromptTemplate
PromptTemplateRegistry = prompt_engineering.PromptTemplateRegistry
PromptTemplateType = prompt_engineering.PromptTemplateType

IncrementalCache = async_generation.IncrementalCache

CodeStyle = smart_generation.CodeStyle
GeneratedCode = smart_generation.GeneratedCode
GenerationRequest = smart_generation.GenerationRequest
GenerationStrategy = smart_generation.GenerationStrategy


class TestLLMIntegration(unittest.TestCase):
    """LLM 集成测试"""

    def test_llm_config(self) -> None:
        """测试 LLM 配置"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo",
            api_key="test-key",
        )
        self.assertEqual(config.provider, LLMProvider.OPENAI)
        self.assertEqual(config.model, "gpt-3.5-turbo")

    def test_chat_message(self) -> None:
        """测试聊天消息"""
        msg = ChatMessage(
            role=MessageRole.USER,
            content="Hello",
        )
        self.assertEqual(msg.role, MessageRole.USER)
        self.assertEqual(msg.content, "Hello")

    def test_token_usage(self) -> None:
        """测试 Token 使用"""
        usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )
        self.assertEqual(usage.prompt_tokens, 100)
        self.assertEqual(usage.total_tokens, 150)

    def test_cost_tracker(self) -> None:
        """测试成本追踪"""
        tracker = CostTracker()
        usage = TokenUsage(1000, 500, 1500)
        cost = tracker.calculate_cost("gpt-3.5-turbo", usage)
        self.assertGreater(cost, 0)

    def test_mock_llm_client(self) -> None:
        """测试 Mock LLM 客户端"""
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
        messages = [ChatMessage(role=MessageRole.USER, content="test")]
        chunks: list[StreamChunk] = []

        def callback(chunk: StreamChunk) -> None:
            chunks.append(chunk)

        response = client.stream(messages, callback)
        self.assertGreater(len(chunks), 0)
        self.assertEqual(chunks[-1].content, response.content)


class TestPromptEngineering(unittest.TestCase):
    """提示工程测试"""

    def test_prompt_template(self) -> None:
        """测试提示模板"""
        template = PromptTemplate(
            name="test",
            template="Hello {{name}}",
            description="Test",
            template_type=PromptTemplateType.USER,
        )
        result = template.render(name="World")
        self.assertEqual(result, "Hello World")

    def test_template_registry(self) -> None:
        """测试模板注册表"""
        registry = PromptTemplateRegistry()
        templates = registry.list_templates()
        self.assertGreater(len(templates), 0)

        result = registry.render(
            "modsdk_entity_create",
            entity_name="TestEntity",
            entity_type="monster",
            behavior="hostile",
        )
        self.assertIn("TestEntity", result)

    def test_few_shot_example(self) -> None:
        """测试 Few-shot 示例"""
        example = FewShotExample(
            input="Create entity",
            output="code here",
            explanation="This creates an entity",
        )
        result = example.format(include_explanation=True)
        self.assertIn("输入:", result)
        self.assertIn("解释:", result)

    def test_few_shot_learner(self) -> None:
        """测试 Few-shot 学习器"""
        learner = FewShotLearner()
        example = FewShotExample(
            input="test input",
            output="test output",
        )
        learner.add_example("test_category", example)
        examples = learner.get_examples("test_category")
        self.assertEqual(len(examples), 1)

    def test_chain_of_thought(self) -> None:
        """测试 Chain-of-Thought"""
        prompter = ChainOfThoughtPrompter()
        prompt = prompter.build_cot_prompt("What is 2+2?")
        self.assertIn("让我们一步步思考", prompt)

    def test_prompt_optimizer(self) -> None:
        """测试提示优化器"""
        optimizer = PromptOptimizer()
        prompt = "Hello    World\n\n\nTest"
        result = optimizer.optimize(prompt, preserve_structure=False)
        self.assertEqual(result.optimized_prompt, "Hello World Test")
        self.assertIn("whitespace_compression", result.techniques_applied)


class TestAsyncGeneration(unittest.TestCase):
    """异步生成测试"""

    def test_incremental_cache(self) -> None:
        """测试增量缓存"""
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


class TestIteration50Acceptance(unittest.TestCase):
    """迭代 #50 验收标准测试"""

    def test_llm_providers(self) -> None:
        """测试 LLM 提供者枚举"""
        providers = [
            LLMProvider.OPENAI,
            LLMProvider.AZURE,
            LLMProvider.OLLAMA,
            LLMProvider.LM_STUDIO,
            LLMProvider.MOCK,
        ]
        self.assertEqual(len(providers), 5)

    def test_prompt_templates_available(self) -> None:
        """测试提示模板可用"""
        registry = PromptTemplateRegistry()
        templates = registry.list_templates()
        self.assertGreater(len(templates), 5)

    def test_few_shot_learning(self) -> None:
        """测试 Few-shot Learning"""
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

    def test_chain_of_thought_available(self) -> None:
        """测试 CoT 可用"""
        prompter = ChainOfThoughtPrompter()
        prompt = prompter.build_cot_prompt("Test question")
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 0)

    def test_cache_functional(self) -> None:
        """测试缓存功能"""
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

    def test_prompt_optimization_performance(self) -> None:
        """测试提示优化性能"""
        optimizer = PromptOptimizer()
        prompt = "A" * 10000

        start = time.time()
        for _ in range(100):
            optimizer.optimize(prompt)
        elapsed = time.time() - start

        self.assertLess(elapsed, 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
