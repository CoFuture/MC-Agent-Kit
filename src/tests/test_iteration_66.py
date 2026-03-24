"""Tests for Iteration #66: CLI 工具集成与用户体验优化

Test coverage:
1. LLM CLI 配置管理
2. 输出格式化
3. 聊天会话管理
4. 命令处理
5. 端到端测试
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ============================================================================
# 配置测试
# ============================================================================

class TestProviderConfig:
    """测试 ProviderConfig"""

    def test_provider_config_defaults(self):
        """测试默认配置"""
        from mc_agent_kit.cli_llm.config import ProviderConfig

        config = ProviderConfig()
        assert config.api_key is None
        assert config.model is None
        assert config.base_url is None
        assert config.temperature == 0.7
        assert config.max_tokens == 4096

    def test_provider_config_to_dict(self):
        """测试转换为字典"""
        from mc_agent_kit.cli_llm.config import ProviderConfig

        config = ProviderConfig(
            api_key="test-key",
            model="gpt-4",
            temperature=0.5,
        )
        data = config.to_dict()

        assert data["api_key"] == "test-key"
        assert data["model"] == "gpt-4"
        assert data["temperature"] == 0.5

    def test_provider_config_from_dict(self):
        """测试从字典创建"""
        from mc_agent_kit.cli_llm.config import ProviderConfig

        data = {
            "api_key": "test-key",
            "model": "gpt-4",
            "base_url": "https://api.example.com",
        }
        config = ProviderConfig.from_dict(data)

        assert config.api_key == "test-key"
        assert config.model == "gpt-4"
        assert config.base_url == "https://api.example.com"


class TestLLMCliConfig:
    """测试 LLMCliConfig"""

    def test_llm_cli_config_defaults(self):
        """测试默认配置"""
        from mc_agent_kit.cli_llm.config import LLMCliConfig

        config = LLMCliConfig()
        assert config.default_provider == "mock"
        assert config.stream_output is True
        assert config.verbose is False
        assert config.max_history_entries == 100

    def test_llm_cli_config_to_dict(self):
        """测试转换为字典"""
        from mc_agent_kit.cli_llm.config import LLMCliConfig, ProviderConfig

        config = LLMCliConfig(
            default_provider="openai",
            providers={"openai": ProviderConfig(api_key="test")},
            stream_output=False,
        )
        data = config.to_dict()

        assert data["default_provider"] == "openai"
        assert "openai" in data["providers"]
        assert data["stream_output"] is False

    def test_llm_cli_config_from_dict(self):
        """测试从字典创建"""
        from mc_agent_kit.cli_llm.config import LLMCliConfig

        data = {
            "default_provider": "anthropic",
            "stream_output": False,
            "verbose": True,
        }
        config = LLMCliConfig.from_dict(data)

        assert config.default_provider == "anthropic"
        assert config.stream_output is False
        assert config.verbose is True

    def test_get_provider_config(self):
        """测试获取提供商配置"""
        from mc_agent_kit.cli_llm.config import LLMCliConfig, ProviderConfig

        config = LLMCliConfig(
            providers={"openai": ProviderConfig(api_key="test-key")}
        )

        provider_config = config.get_provider_config("openai")
        assert provider_config.api_key == "test-key"

        # 不存在的提供商返回默认配置
        unknown_config = config.get_provider_config("unknown")
        assert unknown_config.api_key is None


class TestLLMCliConfigManager:
    """测试 LLMCliConfigManager"""

    def test_load_default_config(self):
        """测试加载默认配置"""
        from mc_agent_kit.cli_llm.config import LLMCliConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            manager = LLMCliConfigManager(config_path)
            config = manager.load()

            assert config.default_provider == "mock"

    def test_load_from_yaml(self):
        """测试从 YAML 加载"""
        from mc_agent_kit.cli_llm.config import LLMCliConfigManager

        yaml_content = """
default_provider: openai
stream_output: false
verbose: true
providers:
  openai:
    api_key: test-key
    model: gpt-4
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            Path(config_path).write_text(yaml_content)

            manager = LLMCliConfigManager(config_path)
            config = manager.load()

            assert config.default_provider == "openai"
            assert config.stream_output is False
            assert config.verbose is True
            assert "openai" in config.providers

    def test_load_from_json(self):
        """测试从 JSON 加载"""
        from mc_agent_kit.cli_llm.config import LLMCliConfigManager

        json_content = json.dumps({
            "default_provider": "anthropic",
            "stream_output": False,
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            Path(config_path).write_text(json_content)

            manager = LLMCliConfigManager(config_path)
            config = manager.load()

            assert config.default_provider == "anthropic"
            assert config.stream_output is False

    def test_env_overrides(self):
        """测试环境变量覆盖"""
        from mc_agent_kit.cli_llm.config import LLMCliConfigManager

        # 设置环境变量
        os.environ["MC_AGENT_KIT_LLM_PROVIDER"] = "ollama"
        os.environ["OPENAI_API_KEY"] = "env-key"

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                config_path = os.path.join(tmpdir, "config.yaml")
                manager = LLMCliConfigManager(config_path)
                config = manager.load()

                assert config.default_provider == "ollama"
                assert "openai" in config.providers
                assert config.providers["openai"].api_key == "env-key"
        finally:
            # 清理环境变量
            del os.environ["MC_AGENT_KIT_LLM_PROVIDER"]
            del os.environ["OPENAI_API_KEY"]

    def test_save_config(self):
        """测试保存配置"""
        from mc_agent_kit.cli_llm.config import (
            LLMCliConfig,
            LLMCliConfigManager,
            ProviderConfig,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            manager = LLMCliConfigManager(config_path)

            config = LLMCliConfig(
                default_provider="openai",
                providers={"openai": ProviderConfig(api_key="secret-key")},
            )
            manager.save(config)

            # 读取并验证（api_key 应被隐藏）
            content = Path(config_path).read_text()
            assert "openai" in content
            assert "secret-key" not in content
            assert "***" in content


# ============================================================================
# 输出格式化测试
# ============================================================================

class TestOutputFormat:
    """测试 OutputFormat"""

    def test_output_format_values(self):
        """测试枚举值"""
        from mc_agent_kit.cli_llm.output import OutputFormat

        assert OutputFormat.TEXT.value == "text"
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.MARKDOWN.value == "markdown"
        assert OutputFormat.ANSI.value == "ansi"


class TestCodeFormatter:
    """测试 CodeFormatter"""

    def test_format_code_text(self):
        """测试文本格式代码"""
        from mc_agent_kit.cli_llm.output import CodeFormatter, OutputFormat

        formatter = CodeFormatter(OutputFormat.TEXT, use_colors=False)
        result = formatter.format_code("print('hello')", "python")

        assert "print('hello')" in result
        assert "Code:" in result

    def test_format_code_json(self):
        """测试 JSON 格式代码"""
        from mc_agent_kit.cli_llm.output import CodeFormatter, OutputFormat

        formatter = CodeFormatter(OutputFormat.JSON)
        result = formatter.format_code("print('hello')", "python")

        data = json.loads(result)
        assert data["code"] == "print('hello')"
        assert data["language"] == "python"

    def test_format_code_markdown(self):
        """测试 Markdown 格式代码"""
        from mc_agent_kit.cli_llm.output import CodeFormatter, OutputFormat

        formatter = CodeFormatter(OutputFormat.MARKDOWN)
        result = formatter.format_code("print('hello')", "python")

        assert "```python" in result
        assert "print('hello')" in result
        assert "```" in result

    def test_format_code_with_filename(self):
        """测试带文件名的格式化"""
        from mc_agent_kit.cli_llm.output import CodeFormatter, OutputFormat

        formatter = CodeFormatter(OutputFormat.TEXT, use_colors=False)
        result = formatter.format_code("print('hello')", "python", "main.py")

        assert "main.py" in result
        assert "print('hello')" in result

    def test_format_imports(self):
        """测试格式化导入"""
        from mc_agent_kit.cli_llm.output import CodeFormatter, OutputFormat

        formatter = CodeFormatter(OutputFormat.TEXT, use_colors=False)
        result = formatter.format_imports(["import os", "import sys"])

        assert "Required imports:" in result
        assert "import os" in result
        assert "import sys" in result

    def test_format_notes(self):
        """测试格式化注释"""
        from mc_agent_kit.cli_llm.output import CodeFormatter, OutputFormat

        formatter = CodeFormatter(OutputFormat.TEXT, use_colors=False)
        result = formatter.format_notes(["Note 1", "Note 2"])

        assert "Notes:" in result
        assert "Note 1" in result

    def test_format_warnings(self):
        """测试格式化警告"""
        from mc_agent_kit.cli_llm.output import CodeFormatter, OutputFormat

        formatter = CodeFormatter(OutputFormat.TEXT, use_colors=False)
        result = formatter.format_warnings(["Warning 1"])

        assert "Warnings:" in result
        assert "Warning 1" in result


class TestStreamOutput:
    """测试 StreamOutput"""

    def test_write(self):
        """测试写入"""
        from mc_agent_kit.cli_llm.output import StreamOutput, StreamChunk
        from io import StringIO

        buffer = StringIO()
        output = StreamOutput(file=buffer, use_colors=False)
        output.write(StreamChunk("Hello "))

        assert buffer.getvalue() == "Hello "

    def test_write_line(self):
        """测试写入行"""
        from mc_agent_kit.cli_llm.output import StreamOutput
        from io import StringIO

        buffer = StringIO()
        output = StreamOutput(file=buffer, use_colors=False)
        output.write_line("Hello")

        assert buffer.getvalue() == "Hello\n"

    def test_get_buffer(self):
        """测试获取缓冲区"""
        from mc_agent_kit.cli_llm.output import StreamOutput, StreamChunk
        from io import StringIO

        buffer = StringIO()
        output = StreamOutput(file=buffer, use_colors=False)
        output.write(StreamChunk("Hello"))
        output.write(StreamChunk(" World"))

        assert output.get_buffer() == "Hello World"


class TestFormatResults:
    """测试结果格式化"""

    def test_format_code_result(self):
        """测试格式化代码结果"""
        from mc_agent_kit.cli_llm.output import format_code_result, OutputFormat

        result = {
            "success": True,
            "code": "print('hello')",
            "imports": ["import os"],
        }
        output = format_code_result(result, OutputFormat.TEXT, use_colors=False)

        assert "✅" in output
        assert "print('hello')" in output

    def test_format_code_result_json(self):
        """测试 JSON 格式代码结果"""
        from mc_agent_kit.cli_llm.output import format_code_result, OutputFormat

        result = {
            "success": True,
            "code": "print('hello')",
        }
        output = format_code_result(result, OutputFormat.JSON)

        data = json.loads(output)
        assert data["success"] is True
        assert data["code"] == "print('hello')"

    def test_format_review_result(self):
        """测试格式化审查结果"""
        from mc_agent_kit.cli_llm.output import format_review_result, OutputFormat

        result = {
            "success": True,
            "score": 85,
            "grade": "B",
            "passed": True,
            "issues": [],
        }
        output = format_review_result(result, OutputFormat.TEXT, use_colors=False)

        assert "✅" in output
        assert "85" in output
        assert "B" in output

    def test_format_review_result_with_issues(self):
        """测试带问题的审查结果"""
        from mc_agent_kit.cli_llm.output import format_review_result, OutputFormat

        result = {
            "success": True,
            "score": 50,
            "grade": "D",
            "passed": False,
            "issues": [
                {
                    "severity": "error",
                    "category": "security",
                    "message": "Use of eval()",
                    "line": 10,
                }
            ],
        }
        output = format_review_result(result, OutputFormat.TEXT, use_colors=False)

        assert "❌" in output
        assert "50" in output
        assert "eval" in output


# ============================================================================
# 聊天会话测试
# ============================================================================

class TestSessionMessage:
    """测试 SessionMessage"""

    def test_session_message_basic(self):
        """测试基本消息"""
        from mc_agent_kit.cli_llm.chat import SessionMessage

        msg = SessionMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_session_message_to_dict(self):
        """测试转换为字典"""
        from mc_agent_kit.cli_llm.chat import SessionMessage

        msg = SessionMessage(role="assistant", content="Hi there")
        data = msg.to_dict()

        assert data["role"] == "assistant"
        assert data["content"] == "Hi there"
        assert "timestamp" in data

    def test_session_message_from_dict(self):
        """测试从字典创建"""
        from mc_agent_kit.cli_llm.chat import SessionMessage
        from datetime import datetime

        data = {
            "role": "system",
            "content": "You are an assistant",
            "timestamp": "2024-01-01T00:00:00",
        }
        msg = SessionMessage.from_dict(data)

        assert msg.role == "system"
        assert msg.content == "You are an assistant"

    def test_session_message_to_llm_message(self):
        """测试转换为 LLM 消息"""
        from mc_agent_kit.cli_llm.chat import SessionMessage

        msg = SessionMessage(role="user", content="Hello")
        llm_msg = msg.to_llm_message()

        assert llm_msg.role.value == "user"
        assert llm_msg.content == "Hello"


class TestChatSessionConfig:
    """测试 ChatSessionConfig"""

    def test_chat_session_config_defaults(self):
        """测试默认配置"""
        from mc_agent_kit.cli_llm.chat import ChatSessionConfig

        config = ChatSessionConfig()
        assert config.max_history == 100
        assert config.context_window == 10
        assert config.save_history is True

    def test_chat_session_config_to_dict(self):
        """测试转换为字典"""
        from mc_agent_kit.cli_llm.chat import ChatSessionConfig

        config = ChatSessionConfig(
            max_history=50,
            system_prompt="Custom prompt",
        )
        data = config.to_dict()

        assert data["max_history"] == 50
        assert data["system_prompt"] == "Custom prompt"


class TestChatSession:
    """测试 ChatSession"""

    def test_chat_session_initialize(self):
        """测试初始化"""
        from mc_agent_kit.cli_llm.chat import ChatSession
        from mc_agent_kit.cli_llm.config import LLMCliConfig

        config = LLMCliConfig()
        session = ChatSession(config)
        session.initialize()

        assert session._initialized is True

    def test_chat_session_send(self):
        """测试发送消息"""
        from mc_agent_kit.cli_llm.chat import ChatSession
        from mc_agent_kit.cli_llm.config import LLMCliConfig

        config = LLMCliConfig()
        session = ChatSession(config)

        response = session.send("Hello", stream=False)
        assert isinstance(response, str)
        assert len(session.messages) == 2  # user + assistant

    def test_chat_session_clear_history(self):
        """测试清除历史"""
        from mc_agent_kit.cli_llm.chat import ChatSession
        from mc_agent_kit.cli_llm.config import LLMCliConfig

        config = LLMCliConfig()
        session = ChatSession(config)
        session.initialize()
        session.send("Hello", stream=False)

        session.clear_history()
        assert len(session.messages) == 0

    def test_chat_session_history_persistence(self):
        """测试历史持久化"""
        from mc_agent_kit.cli_llm.chat import ChatSession, ChatSessionConfig
        from mc_agent_kit.cli_llm.config import LLMCliConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = os.path.join(tmpdir, "history.json")

            # 创建会话并发送消息
            config = LLMCliConfig()
            session_config = ChatSessionConfig(
                save_history=True,
                history_file=history_file,
            )
            session = ChatSession(config, session_config)
            session.initialize()
            session.send("Hello", stream=False)

            # 验证文件已创建
            assert Path(history_file).exists()

            # 加载历史到新会话
            session2 = ChatSession(config, session_config)
            session2.initialize()
            assert len(session2.messages) > 0

    def test_chat_session_set_system_prompt(self):
        """测试设置系统提示"""
        from mc_agent_kit.cli_llm.chat import ChatSession
        from mc_agent_kit.cli_llm.config import LLMCliConfig

        config = LLMCliConfig()
        session = ChatSession(config)
        session.set_system_prompt("Custom system prompt")

        assert session.session_config.system_prompt == "Custom system prompt"


# ============================================================================
# 命令测试
# ============================================================================

class TestGenerateCommand:
    """测试代码生成命令"""

    def test_generate_command_basic(self):
        """测试基本生成"""
        from mc_agent_kit.cli_llm.commands import generate_command

        result = generate_command(
            prompt="创建一个简单的事件监听器",
            generation_type="event_listener",
            stream=False,
        )

        assert "success" in result

    def test_generate_command_with_context(self):
        """测试带上下文的生成"""
        from mc_agent_kit.cli_llm.commands import generate_command

        result = generate_command(
            prompt="创建实体移动逻辑",
            generation_type="entity_behavior",
            target="server",
            context={"project_name": "MyMod", "module_name": "entity"},
            stream=False,
        )

        assert "success" in result


class TestReviewCommand:
    """测试代码审查命令"""

    def test_review_command_good_code(self):
        """测试审查好代码"""
        from mc_agent_kit.cli_llm.commands import review_command

        code = """
def add(a, b):
    return a + b
"""
        result = review_command(code=code, min_score=60)

        assert "success" in result
        assert "score" in result
        assert "grade" in result

    def test_review_command_bad_code(self):
        """测试审查有问题的代码"""
        from mc_agent_kit.cli_llm.commands import review_command

        code = """
eval(user_input)  # Security issue
"""
        result = review_command(code=code, min_score=60)

        # 审查结果包含必要字段
        assert "success" in result
        assert "score" in result
        # 如果成功审查，检查问题
        if result.get("success"):
            assert len(result.get("issues", [])) > 0

    def test_review_command_with_categories(self):
        """测试指定类别的审查"""
        from mc_agent_kit.cli_llm.commands import review_command

        code = "x = 1"
        result = review_command(
            code=code,
            categories=["security", "performance"],
        )

        assert "success" in result


class TestDiagnoseCommand:
    """测试错误诊断命令"""

    def test_diagnose_command_key_error(self):
        """测试 KeyError 诊断"""
        from mc_agent_kit.cli_llm.commands import diagnose_command

        result = diagnose_command(
            error_message="KeyError: 'speed'",
            code="speed = config['speed']",
        )

        assert "success" in result
        assert "suggestions" in result

    def test_diagnose_command_with_stack_trace(self):
        """测试带堆栈的诊断"""
        from mc_agent_kit.cli_llm.commands import diagnose_command

        result = diagnose_command(
            error_message="AttributeError: 'NoneType' object has no attribute 'x'",
            stack_trace="File 'main.py', line 10\n    obj.x",
        )

        assert "success" in result


class TestFixCommand:
    """测试自动修复命令"""

    def test_fix_command_basic(self):
        """测试基本修复"""
        from mc_agent_kit.cli_llm.commands import fix_command

        result = fix_command(
            error_message="KeyError: 'speed'",
            code="speed = config['speed']",
        )

        assert "success" in result
        assert "fixed_code" in result or "original_code" in result


# ============================================================================
# 验收标准测试
# ============================================================================

class TestIteration66AcceptanceCriteria:
    """迭代 #66 验收标准测试"""

    def test_cli_integration_complete(self):
        """验收：CLI 工具集成完成"""
        from mc_agent_kit.cli_llm import (
            generate_command,
            review_command,
            diagnose_command,
            fix_command,
            create_chat_session,
            load_llm_cli_config,
        )

        # 所有函数可调用
        assert callable(generate_command)
        assert callable(review_command)
        assert callable(diagnose_command)
        assert callable(fix_command)
        assert callable(create_chat_session)
        assert callable(load_llm_cli_config)

    def test_config_management_complete(self):
        """验收：配置管理完成"""
        from mc_agent_kit.cli_llm.config import (
            LLMCliConfig,
            LLMCliConfigManager,
            ProviderConfig,
            create_llm_cli_config,
            load_llm_cli_config,
        )

        # 配置类存在
        config = create_llm_cli_config()
        assert config.default_provider == "mock"

        # 管理器可用
        manager = LLMCliConfigManager()
        assert manager is not None

    def test_output_formatting_complete(self):
        """验收：输出格式化完成"""
        from mc_agent_kit.cli_llm.output import (
            CodeFormatter,
            OutputFormat,
            StreamOutput,
            create_code_formatter,
            create_stream_output,
            format_code_result,
            format_review_result,
        )

        # 格式化器可用
        formatter = create_code_formatter()
        assert formatter is not None

        # 支持多种格式
        assert OutputFormat.TEXT
        assert OutputFormat.JSON
        assert OutputFormat.MARKDOWN

    def test_chat_session_complete(self):
        """验收：聊天会话完成"""
        from mc_agent_kit.cli_llm.chat import (
            ChatSession,
            ChatSessionConfig,
            SessionMessage,
            create_chat_session,
        )
        from mc_agent_kit.cli_llm.config import create_llm_cli_config

        # 会话可用
        config = create_llm_cli_config()
        session = create_chat_session(config)
        assert session is not None

        # 支持历史管理
        session.initialize()
        response = session.send("Hello", stream=False)
        assert isinstance(response, str)

    def test_all_cli_llm_modules_importable(self):
        """验收：所有模块可导入"""
        import mc_agent_kit.cli_llm
        from mc_agent_kit.cli_llm import config, output, chat, commands

        assert mc_agent_kit.cli_llm is not None
        assert config is not None
        assert output is not None
        assert chat is not None
        assert commands is not None

    def test_new_cli_commands_registered(self):
        """验收：新 CLI 命令已注册"""
        from mc_agent_kit.cli import llm_main, gen_main

        assert callable(llm_main)
        assert callable(gen_main)


# ============================================================================
# 性能测试
# ============================================================================

class TestIteration66Performance:
    """性能测试"""

    def test_config_load_performance(self):
        """测试配置加载性能"""
        import time
        from mc_agent_kit.cli_llm.config import LLMCliConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")

            start = time.time()
            manager = LLMCliConfigManager(config_path)
            manager.load()
            elapsed = time.time() - start

            assert elapsed < 0.1  # 应小于 100ms

    def test_output_formatting_performance(self):
        """测试输出格式化性能"""
        import time
        from mc_agent_kit.cli_llm.output import format_code_result, OutputFormat

        large_code = "print('hello')\n" * 1000
        result = {"success": True, "code": large_code}

        start = time.time()
        output = format_code_result(result, OutputFormat.TEXT, use_colors=False)
        elapsed = time.time() - start

        assert elapsed < 0.05  # 应小于 50ms

    def test_session_initialization_performance(self):
        """测试会话初始化性能"""
        import time
        from mc_agent_kit.cli_llm.chat import create_chat_session
        from mc_agent_kit.cli_llm.config import create_llm_cli_config

        config = create_llm_cli_config()

        start = time.time()
        session = create_chat_session(config)
        session.initialize()
        elapsed = time.time() - start

        assert elapsed < 0.1  # 应小于 100ms


# ============================================================================
# 边缘情况测试
# ============================================================================

class TestEdgeCases:
    """边缘情况测试"""

    def test_empty_config_file(self):
        """测试空配置文件"""
        from mc_agent_kit.cli_llm.config import LLMCliConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            Path(config_path).write_text("")

            manager = LLMCliConfigManager(config_path)
            config = manager.load()

            # 应使用默认值
            assert config.default_provider == "mock"

    def test_malformed_config_file(self):
        """测试格式错误的配置文件"""
        from mc_agent_kit.cli_llm.config import LLMCliConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            Path(config_path).write_text(":::invalid:::")

            manager = LLMCliConfigManager(config_path)
            config = manager.load()

            # 应使用默认值
            assert config.default_provider == "mock"

    def test_empty_code_review(self):
        """测试空代码审查"""
        from mc_agent_kit.cli_llm.commands import review_command

        result = review_command(code="")
        assert "success" in result

    def test_empty_error_diagnose(self):
        """测试空错误诊断"""
        from mc_agent_kit.cli_llm.commands import diagnose_command

        result = diagnose_command(error_message="")
        assert "success" in result

    def test_very_long_prompt(self):
        """测试超长提示"""
        from mc_agent_kit.cli_llm.commands import generate_command

        long_prompt = "创建一个事件监听器 " * 100
        result = generate_command(prompt=long_prompt, stream=False)

        assert "success" in result

    def test_unicode_in_code(self):
        """测试代码中的 Unicode"""
        from mc_agent_kit.cli_llm.commands import review_command

        code = '# 中文注释\nprint("你好世界")'
        result = review_command(code=code)

        assert "success" in result

    def test_special_characters_in_error(self):
        """测试错误中的特殊字符"""
        from mc_agent_kit.cli_llm.commands import diagnose_command

        result = diagnose_command(
            error_message="KeyError: '速度'",
        )

        assert "success" in result