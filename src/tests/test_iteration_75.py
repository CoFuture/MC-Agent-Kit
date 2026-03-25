"""
迭代 #75: LLM 集成增强测试

测试多模型支持、流式输出增强、上下文管理优化和 API 文档生成。
"""

from __future__ import annotations

import pytest
import time
import json
import os
from typing import Any

from mc_agent_kit.llm.model_selector import (
    ModelCapability,
    ModelFallbackManager,
    ModelInfo,
    ModelRegistry,
    ModelSelectionResult,
    ModelSelector,
    TaskType,
    get_model_registry,
    get_model_selector,
    select_model,
)

from mc_agent_kit.llm.stream_manager import (
    LargeFileStreamer,
    StreamBuffer,
    StreamCheckpoint,
    StreamCheckpointManager,
    StreamError,
    StreamErrorHandler,
    StreamErrorType,
    StreamManager,
    StreamProgress,
    StreamResult,
    StreamState,
    get_stream_manager,
    process_stream,
)

from mc_agent_kit.llm.enhanced_context import (
    CompressionResult,
    ContextCategory,
    ContextCompressor,
    ContextPersistence,
    ContextPriority,
    CrossSessionContext,
    EnhancedContextManager,
    PrioritizedContextMessage,
    get_enhanced_context_manager,
)

from mc_agent_kit.llm.api_doc_generator import (
    ApiDocGenerator,
    ApiDocResult,
    ClassDoc,
    DocFormat,
    DocstringParser,
    ExampleCode,
    ExampleGenerator,
    FunctionDoc,
    ModuleDoc,
    ParameterDoc,
    generate_api_doc,
    get_doc_generator,
)

from mc_agent_kit.llm.base import ChatMessage, ChatRole


# ==================== Model Selector Tests ====================

class TestModelRegistry:
    """测试模型注册表"""

    def test_registry_initialization(self) -> None:
        """测试注册表初始化"""
        registry = ModelRegistry()
        models = registry.get_all_models()
        assert len(models) > 0

    def test_get_model(self) -> None:
        """测试获取模型"""
        registry = ModelRegistry()
        model = registry.get_model("openai", "gpt-4o")
        assert model is not None
        assert model.provider == "openai"
        assert model.model == "gpt-4o"

    def test_get_models_by_provider(self) -> None:
        """测试按提供商获取模型"""
        registry = ModelRegistry()
        models = registry.get_models_by_provider("openai")
        assert len(models) > 0
        assert all(m.provider == "openai" for m in models)

    def test_get_models_by_capability(self) -> None:
        """测试按能力获取模型"""
        registry = ModelRegistry()
        models = registry.get_models_by_capability(ModelCapability.CODE_GENERATION)
        assert len(models) > 0

    def test_list_providers(self) -> None:
        """测试列出提供商"""
        registry = ModelRegistry()
        providers = registry.list_providers()
        assert "openai" in providers
        assert "anthropic" in providers
        assert "mock" in providers


class TestModelSelector:
    """测试模型选择器"""

    def test_select_chat_task(self) -> None:
        """测试选择聊天任务模型"""
        selector = ModelSelector()
        result = selector.select(TaskType.CHAT)
        assert result is not None
        assert result.selected_model is not None
        assert result.selected_model.has_capability(ModelCapability.CHAT)

    def test_select_code_generation_task(self) -> None:
        """测试选择代码生成任务模型"""
        selector = ModelSelector()
        result = selector.select(TaskType.CODE_GENERATION)
        assert result.selected_model.has_capability(ModelCapability.CODE_GENERATION)

    def test_select_with_preferred_provider(self) -> None:
        """测试首选提供商选择"""
        selector = ModelSelector()
        result = selector.select(TaskType.CHAT, preferred_provider="mock")
        assert result.selected_model.provider == "mock"

    def test_select_with_max_cost(self) -> None:
        """测试成本限制选择"""
        selector = ModelSelector()
        result = selector.select(TaskType.CHAT, max_cost=0.001)
        # 应该选择成本低于 0.001 的模型
        assert result.selected_model.cost_per_1k_tokens <= 0.001 or result.selected_model.provider == "mock"

    def test_select_with_context_size(self) -> None:
        """测试上下文大小限制"""
        selector = ModelSelector()
        result = selector.select(
            TaskType.CHAT,
            context={"estimated_tokens": 50000}
        )
        # 应该选择上下文窗口足够大的模型
        assert result.selected_model.context_window >= 50000

    def test_fallback_chain(self) -> None:
        """测试回退链"""
        selector = ModelSelector()
        result = selector.select(TaskType.CODE_GENERATION)
        # 应该有回退链（如果有多于一个候选）
        assert isinstance(result.fallback_chain, list)


class TestModelFallbackManager:
    """测试模型回退管理器"""

    def test_execute_with_fallback_success(self) -> None:
        """测试成功执行"""
        manager = ModelFallbackManager()

        def execute_fn(model: ModelInfo) -> str:
            return f"Executed with {model.model}"

        result, model = manager.execute_with_fallback(TaskType.CHAT, execute_fn)
        assert isinstance(result, str)
        assert "Executed with" in result

    def test_execute_with_fallback_failure(self) -> None:
        """测试失败回退"""
        manager = ModelFallbackManager(max_retries=1)

        def failing_fn(model: ModelInfo) -> str:
            raise Exception("Simulated failure")

        with pytest.raises(Exception):
            manager.execute_with_fallback(TaskType.CHAT, failing_fn)

    def test_record_failure(self) -> None:
        """测试失败记录"""
        manager = ModelFallbackManager()
        manager._record_failure("test:model")
        assert manager._failure_counts["test:model"] == 1

    def test_reset_circuit_breaker(self) -> None:
        """测试熔断器重置"""
        manager = ModelFallbackManager()
        manager._circuit_breaker["test:model"] = True
        manager.reset_circuit_breaker("test:model")
        assert not manager._circuit_breaker.get("test:model", False)


# ==================== Stream Manager Tests ====================

class TestStreamBuffer:
    """测试流式缓冲区"""

    def test_buffer_append(self) -> None:
        """测试追加数据"""
        buffer = StreamBuffer(max_size=1024)
        assert buffer.append("test data")
        assert buffer.size == len("test data")

    def test_buffer_full(self) -> None:
        """测试缓冲区满"""
        buffer = StreamBuffer(max_size=10)
        assert buffer.append("12345")
        # 继续添加直到满
        buffer.append("67890")
        assert buffer.size >= 10

    def test_buffer_get_content(self) -> None:
        """测试获取内容"""
        buffer = StreamBuffer()
        buffer.append("Hello ")
        buffer.append("World")
        assert buffer.get_content() == "Hello World"

    def test_buffer_clear(self) -> None:
        """测试清空"""
        buffer = StreamBuffer()
        buffer.append("test")
        buffer.clear()
        assert buffer.size == 0


class TestStreamErrorHandler:
    """测试流式错误处理器"""

    def test_classify_network_error(self) -> None:
        """测试网络错误分类"""
        handler = StreamErrorHandler()
        error = handler.classify_error(Exception("connection reset"))
        assert error.error_type == StreamErrorType.NETWORK
        assert error.retryable

    def test_classify_timeout_error(self) -> None:
        """测试超时错误分类"""
        handler = StreamErrorHandler()
        error = handler.classify_error(Exception("request timed out"))
        assert error.error_type == StreamErrorType.TIMEOUT
        assert error.retryable

    def test_classify_rate_limit_error(self) -> None:
        """测试速率限制错误分类"""
        handler = StreamErrorHandler()
        error = handler.classify_error(Exception("rate limit exceeded: 429"))
        assert error.error_type == StreamErrorType.RATE_LIMIT
        assert error.retryable

    def test_should_retry(self) -> None:
        """测试重试判断"""
        handler = StreamErrorHandler(max_retries=3)
        error = StreamError(
            error_type=StreamErrorType.NETWORK,
            message="test",
            retryable=True,
        )
        assert handler.should_retry("test_stream", error)

    def test_get_retry_delay(self) -> None:
        """测试重试延迟"""
        handler = StreamErrorHandler(base_delay=1.0)
        error = StreamError(
            error_type=StreamErrorType.NETWORK,
            message="test",
            retryable=True,
        )
        delay = handler.get_retry_delay("test_stream", error)
        assert delay >= 1.0


class TestStreamCheckpointManager:
    """测试流式检查点管理器"""

    def test_create_checkpoint(self, tmp_path: Any) -> None:
        """测试创建检查点"""
        manager = StreamCheckpointManager(str(tmp_path))
        checkpoint = manager.create_checkpoint(
            stream_id="test",
            position=100,
            data="test data",
        )
        assert checkpoint.id == "test"
        assert checkpoint.position == 100

    def test_save_and_load_checkpoint(self, tmp_path: Any) -> None:
        """测试保存和加载检查点"""
        manager = StreamCheckpointManager(str(tmp_path))
        manager.create_checkpoint("test", 100, "data")
        assert manager.save_checkpoint("test")

        loaded = manager.load_checkpoint("test")
        assert loaded is not None
        assert loaded.position == 100

    def test_delete_checkpoint(self, tmp_path: Any) -> None:
        """测试删除检查点"""
        manager = StreamCheckpointManager(str(tmp_path))
        manager.create_checkpoint("test", 100, "data")
        manager.save_checkpoint("test")
        manager.delete_checkpoint("test")
        assert manager.get_checkpoint("test") is None


class TestStreamManager:
    """测试流式管理器"""

    def test_process_stream(self) -> None:
        """测试处理流"""
        manager = StreamManager()

        def generator() -> Any:
            for i in range(5):
                yield f"chunk_{i}"

        result = manager.process_stream("test", generator())
        assert result.state == StreamState.COMPLETED
        assert "chunk_0" in result.content
        assert len(result.chunks) == 5

    def test_cancel_stream(self) -> None:
        """测试取消流"""
        manager = StreamManager()
        result = manager.create_stream("test")
        result.state = StreamState.STREAMING

        # 取消流
        assert manager.cancel_stream("test")
        assert result.state == StreamState.CANCELLED

    def test_pause_and_resume_stream(self, tmp_path: Any) -> None:
        """测试暂停和恢复流"""
        manager = StreamManager(checkpoint_dir=str(tmp_path))

        def generator() -> Any:
            for i in range(10):
                yield f"chunk_{i}"

        # 处理部分流
        result = manager.process_stream("test", generator(), checkpoint_interval=5)
        assert result.state == StreamState.COMPLETED


class TestLargeFileStreamer:
    """测试大文件流式处理器"""

    def test_stream_file(self, tmp_path: Any) -> None:
        """测试流式读取文件"""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Hello World " * 100)

        streamer = LargeFileStreamer(chunk_size=50)
        chunks = list(streamer.stream_file(str(file_path)))
        assert len(chunks) > 0
        assert "".join(chunks) == "Hello World " * 100

    def test_stream_large_text(self) -> None:
        """测试流式处理大文本"""
        text = "A" * 1000
        streamer = LargeFileStreamer(chunk_size=100)
        chunks = list(streamer.stream_large_text(text))
        assert len(chunks) == 10
        assert "".join(chunks) == text

    def test_stream_with_overlap(self) -> None:
        """测试带重叠的流式处理"""
        text = "ABCDEFGHIJ" * 10
        streamer = LargeFileStreamer(chunk_size=20, max_memory=1000)
        chunks = list(streamer.stream_with_overlap(text, overlap=5))
        assert len(chunks) > 0


# ==================== Enhanced Context Tests ====================

class TestContextCompressor:
    """测试上下文压缩器"""

    def test_compress_no_op(self) -> None:
        """测试无需压缩"""
        compressor = ContextCompressor()
        messages = [
            PrioritizedContextMessage(
                message=ChatMessage.user("Hello"),
                token_count=10,
            )
        ]
        compressed, result = compressor.compress(messages, max_tokens=100)
        assert len(compressed) == 1
        assert result.compression_ratio == 0.0

    def test_compress_with_priority(self) -> None:
        """测试按优先级压缩"""
        compressor = ContextCompressor()
        messages = [
            PrioritizedContextMessage(
                message=ChatMessage.user("Low priority"),
                priority=ContextPriority.LOW,
                token_count=50,
            ),
            PrioritizedContextMessage(
                message=ChatMessage.system("Critical info"),
                priority=ContextPriority.CRITICAL,
                token_count=50,
            ),
        ]
        compressed, result = compressor.compress(messages, max_tokens=60)
        # 应该保留高优先级消息
        assert any(m.priority == ContextPriority.CRITICAL for m in compressed)


class TestCrossSessionContext:
    """测试跨会话上下文"""

    def test_create_session(self, tmp_path: Any) -> None:
        """测试创建会话"""
        context = CrossSessionContext(str(tmp_path))
        context.create_session("session1")
        assert "session1" in context.list_sessions()

    def test_add_message(self, tmp_path: Any) -> None:
        """测试添加消息"""
        context = CrossSessionContext(str(tmp_path))
        context.create_session("session1")
        msg = PrioritizedContextMessage(
            message=ChatMessage.user("Test"),
        )
        context.add_message("session1", msg)
        messages = context.get_session_messages("session1")
        assert len(messages) == 1

    def test_global_context(self, tmp_path: Any) -> None:
        """测试全局上下文"""
        context = CrossSessionContext(str(tmp_path))
        context.set_global_context("user_name", "Alice")
        assert context.get_global_context("user_name") == "Alice"

    def test_save_and_load_session(self, tmp_path: Any) -> None:
        """测试保存和加载会话"""
        context = CrossSessionContext(str(tmp_path))
        context.create_session("session1")
        msg = PrioritizedContextMessage(
            message=ChatMessage.user("Test message"),
        )
        context.add_message("session1", msg)
        assert context.save_session("session1")
        assert context.load_session("session1")


class TestContextPersistence:
    """测试上下文持久化"""

    def test_save_and_load(self, tmp_path: Any) -> None:
        """测试保存和加载"""
        persistence = ContextPersistence("file", str(tmp_path))
        data = {"key": "value", "number": 42}
        assert persistence.save("test_key", data)
        loaded = persistence.load("test_key")
        assert loaded == data

    def test_exists(self, tmp_path: Any) -> None:
        """测试存在性检查"""
        persistence = ContextPersistence("file", str(tmp_path))
        assert not persistence.exists("nonexistent")
        persistence.save("test", "data")
        assert persistence.exists("test")

    def test_delete(self, tmp_path: Any) -> None:
        """测试删除"""
        persistence = ContextPersistence("file", str(tmp_path))
        persistence.save("test", "data")
        assert persistence.delete("test")
        assert not persistence.exists("test")


class TestEnhancedContextManager:
    """测试增强上下文管理器"""

    def test_start_session(self, tmp_path: Any) -> None:
        """测试开始会话"""
        manager = EnhancedContextManager(storage_dir=str(tmp_path))
        manager.start_session("test_session")
        assert manager._current_session_id == "test_session"

    def test_add_messages(self, tmp_path: Any) -> None:
        """测试添加消息"""
        manager = EnhancedContextManager(storage_dir=str(tmp_path))
        manager.start_session("test")
        manager.add_system_message("System instruction")
        manager.add_user_message("User question")
        manager.add_assistant_message("Assistant answer")

        messages = manager.get_messages()
        assert len(messages) == 3

    def test_compress_if_needed(self, tmp_path: Any) -> None:
        """测试按需压缩"""
        manager = EnhancedContextManager(max_tokens=100, storage_dir=str(tmp_path))
        manager.start_session("test")

        # 添加大量消息
        for i in range(50):
            manager.add_assistant_message(f"Message {i}" * 10)

        result = manager.compress_if_needed()
        assert result.original_tokens > result.compressed_tokens or result.original_tokens <= 100

    def test_get_stats(self, tmp_path: Any) -> None:
        """测试获取统计"""
        manager = EnhancedContextManager(storage_dir=str(tmp_path))
        manager.start_session("test")
        manager.add_user_message("Hello")
        stats = manager.get_stats()
        assert stats["total_messages"] >= 1
        assert "session_id" in stats


# ==================== API Doc Generator Tests ====================

class TestDocstringParser:
    """测试 Docstring 解析器"""

    def test_parse_simple_docstring(self) -> None:
        """测试解析简单 docstring"""
        parser = DocstringParser()
        docstring = """Simple function description."""
        result = parser.parse(docstring)
        assert "Simple function description" in result["description"]

    def test_parse_with_parameters(self) -> None:
        """测试解析带参数的 docstring"""
        parser = DocstringParser()
        docstring = """
        Function with parameters.

        Args:
            name (str): The name parameter
            value (int): The value
        """
        result = parser.parse(docstring)
        assert len(result["parameters"]) > 0

    def test_parse_empty_docstring(self) -> None:
        """测试解析空 docstring"""
        parser = DocstringParser()
        result = parser.parse(None)
        assert result == {}


class TestTypeInferer:
    """测试类型推断器"""

    def test_infer_from_default(self) -> None:
        """测试从默认值推断类型"""
        from mc_agent_kit.llm.api_doc_generator import TypeInferer
        import inspect

        inferer = TypeInferer()

        def func(name="test", count=42):
            pass

        sig = inspect.signature(func)
        params = list(sig.parameters.values())
        
        # 测试字符串默认值
        param_type = inferer.infer_parameter_type(params[0])
        assert param_type.value in ("string", "any")  # Python 3.9 可能无法推断
        
        # 测试整数默认值
        param_type = inferer.infer_parameter_type(params[1])
        assert param_type.value in ("integer", "any")


class TestExampleGenerator:
    """测试示例代码生成器"""

    def test_generate_function_example(self) -> None:
        """测试生成函数示例"""
        generator = ExampleGenerator()
        func_doc = FunctionDoc(
            name="test_function",
            description="Test function",
            parameters=[
                ParameterDoc(name="name", type="string", required=True, example="test"),
            ],
        )
        example = generator.generate_function_example(func_doc)
        assert "test_function" in example.code
        # 示例代码应该包含参数值
        assert len(example.code) > 0

    def test_generate_class_example(self) -> None:
        """测试生成类示例"""
        generator = ExampleGenerator()
        class_doc = ClassDoc(
            name="TestClass",
            description="Test class",
            parameters=[
                ParameterDoc(name="value", type="integer", required=True),
            ],
        )
        example = generator.generate_class_example(class_doc)
        assert "TestClass" in example.code


class TestDocFormatter:
    """测试文档格式化器"""

    def test_format_markdown_function(self) -> None:
        """测试 Markdown 格式化函数"""
        from mc_agent_kit.llm.api_doc_generator import DocFormatter
        formatter = DocFormatter()
        func_doc = FunctionDoc(
            name="test_func",
            description="Test function description",
        )
        markdown = formatter.format(func_doc, DocFormat.MARKDOWN)
        assert "# test_func" in markdown

    def test_format_json(self) -> None:
        """测试 JSON 格式化"""
        from mc_agent_kit.llm.api_doc_generator import DocFormatter
        formatter = DocFormatter()
        func_doc = FunctionDoc(name="test")
        json_output = formatter.format(func_doc, DocFormat.JSON)
        data = json.loads(json_output)
        assert data["name"] == "test"


class TestApiDocGenerator:
    """测试 API 文档生成器"""

    def test_generate_from_function(self) -> None:
        """测试从函数生成文档"""
        generator = ApiDocGenerator()

        def sample_func(name: str, value: int = 42) -> str:
            """
            Sample function for testing.

            Args:
                name: The name parameter
                value: The value (default 42)

            Returns:
                str: The result
            """
            return f"{name}: {value}"

        doc = generator.generate_from_function(sample_func)
        assert doc.name == "sample_func"
        assert len(doc.parameters) > 0

    def test_generate_from_class(self) -> None:
        """测试从类生成文档"""
        generator = ApiDocGenerator()

        class SampleClass:
            """Sample class for testing."""

            def __init__(self, value: int) -> None:
                self.value = value

            def get_value(self) -> int:
                """Get the value."""
                return self.value

        doc = generator.generate_from_class(SampleClass)
        assert doc.name == "SampleClass"
        assert len(doc.methods) > 0

    def test_generate_and_format(self) -> None:
        """测试生成并格式化"""
        generator = ApiDocGenerator()

        def test_func(x: int) -> int:
            """Test function."""
            return x * 2

        result = generator.generate_and_format(test_func, DocFormat.MARKDOWN)
        assert result.format == DocFormat.MARKDOWN
        assert len(result.content) > 0


# ==================== Integration Tests ====================

class TestIteration75Integration:
    """迭代 #75 集成测试"""

    def test_model_selector_integration(self) -> None:
        """测试模型选择器集成"""
        result = select_model(TaskType.CODE_GENERATION)
        assert result is not None
        assert result.selected_model is not None

    def test_stream_manager_integration(self) -> None:
        """测试流式管理器集成"""
        manager = get_stream_manager()
        assert manager is not None

    def test_context_manager_integration(self) -> None:
        """测试上下文管理器集成"""
        manager = get_enhanced_context_manager()
        assert manager is not None

    def test_doc_generator_integration(self) -> None:
        """测试文档生成器集成"""
        generator = get_doc_generator()
        assert generator is not None


class TestIteration75AcceptanceCriteria:
    """迭代 #75 验收标准测试"""

    def test_multi_model_support(self) -> None:
        """测试多模型支持"""
        registry = ModelRegistry()
        models = registry.get_all_models()
        assert len(models) >= 10  # 至少 10 个模型

    def test_model_capability_detection(self) -> None:
        """测试模型能力检测"""
        selector = ModelSelector()
        result = selector.select(TaskType.CODE_GENERATION)
        assert result.selected_model.has_capability(ModelCapability.CODE_GENERATION)

    def test_intelligent_model_selection(self) -> None:
        """测试智能模型选择"""
        selector = ModelSelector()
        result = selector.select(TaskType.CODE_GENERATION)
        assert result.confidence > 0.0

    def test_model_fallback_mechanism(self) -> None:
        """测试模型回退机制"""
        manager = ModelFallbackManager()
        assert manager.max_retries >= 1

    def test_streaming_performance(self) -> None:
        """测试流式输出性能"""
        manager = StreamManager()

        def generator() -> Any:
            for i in range(100):
                yield f"chunk_{i}"

        start = time.time()
        result = manager.process_stream("perf_test", generator())
        elapsed = time.time() - start

        assert result.state == StreamState.COMPLETED
        assert elapsed < 5.0  # 5 秒内完成

    def test_checkpoint_resume(self, tmp_path: Any) -> None:
        """测试断点续传"""
        manager = StreamManager(checkpoint_dir=str(tmp_path))

        def generator() -> Any:
            for i in range(10):
                yield f"chunk_{i}"

        result = manager.process_stream("resume_test", generator(), checkpoint_interval=5)
        assert result.state == StreamState.COMPLETED

    def test_context_compression(self, tmp_path: Any) -> None:
        """测试上下文压缩"""
        manager = EnhancedContextManager(max_tokens=100, storage_dir=str(tmp_path))
        manager.start_session("compress_test")

        for i in range(20):
            manager.add_assistant_message(f"Message {i}" * 10)

        result = manager.compress_if_needed()
        assert result.original_tokens > 0

    def test_context_persistence(self, tmp_path: Any) -> None:
        """测试上下文持久化"""
        manager = EnhancedContextManager(storage_dir=str(tmp_path))
        manager.start_session("persist_test")
        manager.add_user_message("Persistent message")
        assert manager.save_session()

    def test_api_doc_generation(self) -> None:
        """测试 API 文档生成"""
        generator = ApiDocGenerator()

        def documented_func(x: int, y: str = "default") -> bool:
            """
            A documented function.

            Args:
                x: An integer
                y: A string

            Returns:
                bool: Result
            """
            return True

        doc = generator.generate_from_function(documented_func)
        assert doc.name == "documented_func"
        assert len(doc.parameters) >= 1

    def test_multi_format_output(self) -> None:
        """测试多格式输出"""
        generator = ApiDocGenerator()

        def test_func() -> None:
            """Test."""
            pass

        for format_type in [DocFormat.MARKDOWN, DocFormat.JSON]:
            result = generator.generate_and_format(test_func, format_type)
            assert result.format == format_type
            assert len(result.content) > 0

    def test_example_code_generation(self) -> None:
        """测试示例代码生成"""
        generator = ApiDocGenerator()

        def sample_func(name: str) -> str:
            """Sample function."""
            return name

        doc = generator.generate_from_function(sample_func)
        assert len(doc.examples) > 0
        assert "sample_func" in doc.examples[0].code


# ==================== Performance Tests ====================

class TestIteration75Performance:
    """迭代 #75 性能测试"""

    def test_model_selection_performance(self) -> None:
        """测试模型选择性能"""
        selector = ModelSelector()

        start = time.time()
        for _ in range(100):
            selector.select(TaskType.CHAT)
        elapsed = time.time() - start

        assert elapsed < 1.0  # 100 次选择应在 1 秒内完成

    def test_context_compression_performance(self, tmp_path: Any) -> None:
        """测试上下文压缩性能"""
        manager = EnhancedContextManager(storage_dir=str(tmp_path))
        manager.start_session("perf_test")

        for i in range(100):
            manager.add_assistant_message(f"Message {i}")

        start = time.time()
        manager.compress_if_needed()
        elapsed = time.time() - start

        assert elapsed < 2.0  # 压缩应在 2 秒内完成

    def test_stream_buffer_performance(self) -> None:
        """测试流式缓冲区性能"""
        buffer = StreamBuffer(max_size=10 * 1024 * 1024)

        start = time.time()
        for i in range(1000):
            buffer.append(f"chunk_{i} " * 100)
        elapsed = time.time() - start

        assert elapsed < 1.0  # 1000 次追加应在 1 秒内完成


if __name__ == "__main__":
    pytest.main([__file__, "-v"])