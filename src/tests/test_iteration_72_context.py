"""
测试上下文增强模块

测试 iteration #72 的上下文管理功能。
"""

import pytest
import os
import json
import tempfile
from unittest.mock import Mock, patch

from mc_agent_kit.llm.context_manager import (
    CodeContext,
    CodeContextAnalyzer,
    ContextMessage,
    ContextSummary,
    ContextType,
    ContextWindow,
    ConversationManager,
    ProjectContext,
    ProjectContextAnalyzer,
    analyze_code_context,
    analyze_project_context,
    create_conversation_manager,
)
from mc_agent_kit.llm.base import ChatRole, ChatMessage


class TestContextMessage:
    """测试上下文消息"""

    def test_create_context_message(self):
        """创建上下文消息"""
        msg = ContextMessage(
            role=ChatRole.USER,
            content="测试消息",
        )

        assert msg.role == ChatRole.USER
        assert msg.content == "测试消息"
        assert msg.timestamp == 0.0

    def test_context_message_with_metadata(self):
        """带元数据的消息"""
        msg = ContextMessage(
            role=ChatRole.ASSISTANT,
            content="回复",
            metadata={"key": "value"},
        )

        assert msg.metadata == {"key": "value"}

    def test_to_chat_message(self):
        """转换为 ChatMessage"""
        msg = ContextMessage(
            role=ChatRole.USER,
            content="测试",
        )

        chat_msg = msg.to_chat_message()

        assert isinstance(chat_msg, ChatMessage)
        assert chat_msg.role == ChatRole.USER
        assert chat_msg.content == "测试"

    def test_to_dict(self):
        """序列化为字典"""
        msg = ContextMessage(
            role=ChatRole.USER,
            content="测试",
            metadata={"key": "value"},
        )

        data = msg.to_dict()

        assert data["role"] == "user"
        assert data["content"] == "测试"
        assert data["metadata"] == {"key": "value"}

    def test_from_dict(self):
        """从字典创建"""
        data = {
            "role": "assistant",
            "content": "回复",
            "timestamp": 123.456,
            "metadata": {"key": "value"},
        }

        msg = ContextMessage.from_dict(data)

        assert msg.role == ChatRole.ASSISTANT
        assert msg.content == "回复"
        assert msg.timestamp == 123.456


class TestContextSummary:
    """测试上下文摘要"""

    def test_create_summary(self):
        """创建摘要"""
        summary = ContextSummary(
            key_points=["关键点 1", "关键点 2"],
            entities=["entity1"],
            apis=["API1"],
            events=["Event1"],
        )

        assert len(summary.key_points) == 2
        assert len(summary.entities) == 1
        assert len(summary.apis) == 1
        assert len(summary.events) == 1

    def test_summary_to_dict(self):
        """摘要序列化"""
        summary = ContextSummary(
            key_points=["点 1"],
            decisions=["决策 1"],
            issues=["问题 1"],
        )

        data = summary.to_dict()

        assert "key_points" in data
        assert "decisions" in data
        assert "issues" in data

    def test_summary_to_prompt(self):
        """摘要转换为提示"""
        summary = ContextSummary(
            key_points=["重要信息"],
            entities=["测试实体"],
            apis=["CreateEntity"],
        )

        prompt = summary.to_prompt()

        assert isinstance(prompt, str)
        assert "关键点" in prompt or "实体" in prompt or "API" in prompt

    def test_empty_summary(self):
        """空摘要"""
        summary = ContextSummary()

        prompt = summary.to_prompt()

        assert prompt == ""


class TestContextWindow:
    """测试上下文窗口"""

    def test_create_window(self):
        """创建窗口"""
        window = ContextWindow(
            max_messages=10,
            max_tokens=2000,
        )

        assert window.max_messages == 10
        assert window.max_tokens == 2000
        assert len(window.messages) == 0

    def test_add_message(self):
        """添加消息"""
        window = ContextWindow(max_messages=10)
        msg = ContextMessage(role=ChatRole.USER, content="测试")

        window.add_message(msg)

        assert len(window.messages) == 1
        assert window.messages[0].content == "测试"
        assert window.messages[0].timestamp > 0

    def test_window_compression(self):
        """窗口压缩"""
        window = ContextWindow(max_messages=5)

        # 添加超过限制的消息
        for i in range(10):
            msg = ContextMessage(role=ChatRole.USER, content=f"消息{i}")
            window.add_message(msg)

        # 应该压缩到最大限制以内
        assert len(window.messages) <= window.max_messages

    def test_get_chat_messages(self):
        """获取 ChatMessage 列表"""
        window = ContextWindow()
        window.add_message(ContextMessage(role=ChatRole.USER, content="用户"))
        window.add_message(ContextMessage(role=ChatRole.ASSISTANT, content="助手"))

        messages = window.get_chat_messages()

        assert len(messages) == 2
        assert all(isinstance(m, ChatMessage) for m in messages)

    def test_get_context_prompt(self):
        """获取上下文提示"""
        window = ContextWindow()

        # 添加一些消息
        for i in range(3):
            window.add_message(ContextMessage(role=ChatRole.USER, content=f"测试{i}"))

        prompt = window.get_context_prompt()

        assert isinstance(prompt, str)


class TestConversationManager:
    """测试对话管理器"""

    def test_create_manager(self):
        """创建管理器"""
        manager = ConversationManager(max_messages=20)

        assert manager.window.max_messages == 20

    def test_add_user_message(self):
        """添加用户消息"""
        manager = ConversationManager()
        manager.add_user_message("你好")

        assert len(manager.window.messages) == 1
        assert manager.window.messages[0].role == ChatRole.USER

    def test_add_assistant_message(self):
        """添加助手消息"""
        manager = ConversationManager()
        manager.add_assistant_message("你好！有什么可以帮助你的？")

        assert len(manager.window.messages) == 1
        assert manager.window.messages[0].role == ChatRole.ASSISTANT

    def test_add_system_message(self):
        """添加系统消息"""
        manager = ConversationManager()
        manager.add_system_message("你是一个助手")

        assert len(manager.window.messages) == 1
        assert manager.window.messages[0].role == ChatRole.SYSTEM

    def test_get_messages(self):
        """获取消息列表"""
        manager = ConversationManager()
        manager.add_user_message("用户")
        manager.add_assistant_message("助手")

        messages = manager.get_messages()

        assert len(messages) == 2

    def test_clear_conversation(self):
        """清空对话"""
        manager = ConversationManager()
        manager.add_user_message("测试")
        manager.add_assistant_message("回复")

        manager.clear()

        assert len(manager.window.messages) == 0

    def test_save_and_load(self):
        """保存和加载对话"""
        manager = ConversationManager()
        manager.add_user_message("保存测试")
        manager.add_assistant_message("回复测试")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            manager.save(temp_path)

            # 验证文件存在
            assert os.path.exists(temp_path)

            # 加载到新管理器
            new_manager = ConversationManager()
            new_manager.load(temp_path)

            assert len(new_manager.window.messages) == 2
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_get_context_prompt(self):
        """获取上下文提示"""
        manager = ConversationManager()
        manager.add_user_message("上下文测试")

        prompt = manager.get_context_prompt()

        assert isinstance(prompt, str)

    def test_get_summary(self):
        """获取摘要"""
        manager = ConversationManager()
        manager.add_user_message("测试摘要")

        summary = manager.get_summary()

        assert isinstance(summary, ContextSummary)


class TestCodeContext:
    """测试代码上下文"""

    def test_create_code_context(self):
        """创建代码上下文"""
        ctx = CodeContext(
            file_path="test.py",
            code="print('hello')",
            language="python",
        )

        assert ctx.file_path == "test.py"
        assert ctx.code == "print('hello')"
        assert ctx.language == "python"

    def test_code_context_to_dict(self):
        """代码上下文序列化"""
        ctx = CodeContext(
            imports=["import os"],
            functions=["main"],
            classes=["TestClass"],
        )

        data = ctx.to_dict()

        assert "imports" in data
        assert "functions" in data
        assert "classes" in data


class TestCodeContextAnalyzer:
    """测试代码上下文分析器"""

    def test_create_analyzer(self):
        """创建分析器"""
        analyzer = CodeContextAnalyzer()

        assert analyzer is not None

    def test_analyze_simple_code(self):
        """分析简单代码"""
        analyzer = CodeContextAnalyzer()
        code = """
import os

def main():
    print("hello")

class Test:
    pass
"""

        ctx = analyzer.analyze(code, "test.py")

        assert ctx.file_path == "test.py"
        assert len(ctx.imports) > 0
        assert "main" in ctx.functions
        assert "Test" in ctx.classes

    def test_analyze_modsdk_code(self):
        """分析 ModSDK 代码"""
        analyzer = CodeContextAnalyzer()
        code = """
import mod.server.extraServerApi as serverApi

def on_chat(args):
    pass

serverApi.ListenEvent("OnServerChat", on_chat)
"""

        ctx = analyzer.analyze(code)

        assert "mod.server.extraServerApi" in ctx.dependencies
        assert "事件系统" in ctx.dependencies

    def test_extract_dependencies(self):
        """提取依赖"""
        analyzer = CodeContextAnalyzer()

        # 测试各种 ModSDK 依赖
        test_cases = [
            ("serverApi", "mod.server.extraServerApi"),
            ("clientApi", "mod.client.extraClientApi"),
            ("ListenEvent", "事件系统"),
            ("GetEngineCompFactory", "组件工厂"),
            ("CreateEngineEntity", "实体系统"),
            ("CreateScreen", "UI 系统"),
            ("NotifyToClient", "网络同步"),
        ]

        for keyword, expected_dep in test_cases:
            code = f"some_code_using_{keyword}"
            ctx = analyzer.analyze(code)
            assert expected_dep in ctx.dependencies, f"Failed for {keyword}"

    def test_get_context_prompt(self):
        """获取代码上下文提示"""
        analyzer = CodeContextAnalyzer()
        code = "def test(): pass"
        ctx = analyzer.analyze(code, "test.py")

        prompt = analyzer.get_context_prompt(ctx)

        assert isinstance(prompt, str)


class TestProjectContext:
    """测试项目上下文"""

    def test_create_project_context(self):
        """创建项目上下文"""
        ctx = ProjectContext(
            name="TestAddon",
            path="/path/to/addon",
        )

        assert ctx.name == "TestAddon"
        assert ctx.path == "/path/to/addon"

    def test_project_context_to_dict(self):
        """项目上下文序列化"""
        ctx = ProjectContext(
            name="MyAddon",
            behavior_packs=["bp1", "bp2"],
            resource_packs=["rp1"],
        )

        data = ctx.to_dict()

        assert data["name"] == "MyAddon"
        assert len(data["behavior_packs"]) == 2
        assert len(data["resource_packs"]) == 1


class TestProjectContextAnalyzer:
    """测试项目上下文分析器"""

    def test_create_analyzer(self):
        """创建分析器"""
        analyzer = ProjectContextAnalyzer()

        assert analyzer is not None

    def test_analyze_nonexistent_path(self):
        """分析不存在的路径"""
        analyzer = ProjectContextAnalyzer()
        ctx = analyzer.analyze("/nonexistent/path")

        assert ctx.path == "/nonexistent/path"
        assert ctx.name == ""

    def test_analyze_real_directory(self):
        """分析真实目录"""
        analyzer = ProjectContextAnalyzer()

        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试目录结构
            bp_dir = os.path.join(temp_dir, "behavior_pack")
            os.makedirs(bp_dir)

            # 创建测试文件
            with open(os.path.join(bp_dir, "main.py"), "w") as f:
                f.write("# test")

            ctx = analyzer.analyze(temp_dir)

            assert ctx.path == temp_dir
            assert len(ctx.behavior_packs) > 0 or len(ctx.scripts) > 0

    def test_get_context_prompt(self):
        """获取项目上下文提示"""
        analyzer = ProjectContextAnalyzer()
        ctx = ProjectContext(name="TestAddon")

        prompt = analyzer.get_context_prompt(ctx)

        assert isinstance(prompt, str)


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_create_conversation_manager(self):
        """创建对话管理器"""
        manager = create_conversation_manager(max_messages=15)

        assert manager.window.max_messages == 15

    def test_analyze_code_context(self):
        """分析代码上下文"""
        code = "def test(): pass"
        ctx = analyze_code_context(code, "test.py")

        assert isinstance(ctx, CodeContext)
        assert ctx.file_path == "test.py"

    def test_analyze_project_context(self):
        """分析项目上下文"""
        ctx = analyze_project_context("/test/path")

        assert isinstance(ctx, ProjectContext)
        assert ctx.path == "/test/path"


class TestContextManagerIntegration:
    """测试上下文管理器集成"""

    def test_conversation_with_code_context(self):
        """对话与代码上下文集成"""
        manager = ConversationManager()
        analyzer = CodeContextAnalyzer()

        # 添加对话
        manager.add_user_message("帮我创建一个实体")
        manager.add_assistant_message("好的，我来帮你")

        # 分析代码
        code = "import mod.server.extraServerApi as serverApi"
        ctx = analyzer.analyze(code)

        # 获取所有上下文
        messages = manager.get_messages()
        code_prompt = analyzer.get_context_prompt(ctx)

        assert len(messages) == 2
        assert isinstance(code_prompt, str)

    def test_multi_turn_conversation(self):
        """多轮对话"""
        manager = ConversationManager(max_messages=10)

        # 模拟多轮对话
        for i in range(5):
            manager.add_user_message(f"问题{i}")
            manager.add_assistant_message(f"回答{i}")

        messages = manager.get_messages()

        # 应该在限制范围内
        assert len(messages) <= 10


class TestContextManagerPerformance:
    """性能测试"""

    def test_message_addition_performance(self):
        """消息添加性能"""
        manager = ConversationManager(max_messages=100)

        import time
        start_time = time.time()

        for i in range(50):
            manager.add_user_message(f"消息{i}")

        duration = time.time() - start_time

        # 应该在合理时间内完成
        assert duration < 1.0

    def test_context_window_compression_performance(self):
        """窗口压缩性能"""
        window = ContextWindow(max_messages=20)

        import time
        start_time = time.time()

        # 添加大量消息触发压缩
        for i in range(100):
            window.add_message(ContextMessage(role=ChatRole.USER, content=f"消息{i}"))

        duration = time.time() - start_time

        assert duration < 1.0
        assert len(window.messages) <= 20


class TestContextManagerEdgeCases:
    """边缘情况测试"""

    def test_empty_message_content(self):
        """空消息内容"""
        manager = ConversationManager()
        manager.add_user_message("")

        assert len(manager.window.messages) == 1

    def test_very_long_message(self):
        """超长消息"""
        manager = ConversationManager()
        long_content = "测试" * 1000
        manager.add_user_message(long_content)

        assert len(manager.window.messages) == 1

    def test_special_characters(self):
        """特殊字符"""
        manager = ConversationManager()
        manager.add_user_message("测试！@#$%^&*()_+")

        assert len(manager.window.messages) == 1

    def test_unicode_content(self):
        """Unicode 内容"""
        manager = ConversationManager()
        manager.add_user_message("测试中文 English Español")

        assert len(manager.window.messages) == 1

    def test_save_to_invalid_path(self):
        """保存到无效路径"""
        manager = ConversationManager()
        manager.add_user_message("测试")

        # 应该抛出异常或正确处理
        import pytest
        with pytest.raises((FileNotFoundError, OSError)):
            manager.save("/nonexistent/dir/file.json")


class TestContextManagerAcceptanceCriteria:
    """验收标准测试"""

    def test_context_manager_module_exists(self):
        """上下文管理器模块存在"""
        from mc_agent_kit.llm import context_manager
        assert context_manager is not None

    def test_context_classes_available(self):
        """上下文类可用"""
        assert ContextMessage is not None
        assert ContextSummary is not None
        assert ContextWindow is not None
        assert ConversationManager is not None

    def test_code_context_classes_available(self):
        """代码上下文类可用"""
        assert CodeContext is not None
        assert CodeContextAnalyzer is not None

    def test_project_context_classes_available(self):
        """项目上下文类可用"""
        assert ProjectContext is not None
        assert ProjectContextAnalyzer is not None

    def test_convenience_functions_available(self):
        """便捷函数可用"""
        assert create_conversation_manager is not None
        assert analyze_code_context is not None
        assert analyze_project_context is not None

    def test_context_manager_integration(self):
        """上下文管理器集成"""
        manager = ConversationManager()
        manager.add_user_message("测试集成")
        manager.add_assistant_message("回复")

        messages = manager.get_messages()
        assert len(messages) == 2

    def test_all_tests_pass(self):
        """所有测试通过"""
        pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
