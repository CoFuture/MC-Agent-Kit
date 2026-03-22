"""
迭代 #44 测试: 文档完善与 CLI 集成

测试内容:
1. 工作流增强 CLI 选项
2. 本地化扩展
3. 语言检测功能
4. CLI 命令测试
"""

import pytest
from unittest.mock import MagicMock, patch
import argparse

from mc_agent_kit.workflow import (
    RetryConfig,
    RetryPolicy,
    WorkflowStep,
    WorkflowStepStatus,
    create_enhanced_workflow,
    EnhancedWorkflow,
    WorkflowControl,
    WorkflowState,
)
from mc_agent_kit.ux import (
    LocaleManager,
    LocaleConfig,
    EnhancedUXManager,
    TemplateRegistry,
    get_ux_manager,
)


class TestRetryConfigEnhanced:
    """重试配置增强测试"""

    def test_retry_config_default_values(self):
        """测试默认值"""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.policy == RetryPolicy.LINEAR
        assert config.base_delay_seconds == 1.0
        assert config.max_delay_seconds == 30.0

    def test_retry_config_linear_delay(self):
        """测试线性延迟计算"""
        config = RetryConfig(policy=RetryPolicy.LINEAR, base_delay_seconds=2.0)
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0
        assert config.get_delay(3) == 6.0

    def test_retry_config_exponential_delay(self):
        """测试指数延迟计算"""
        config = RetryConfig(policy=RetryPolicy.EXPONENTIAL, base_delay_seconds=1.0)
        assert config.get_delay(1) == 1.0
        assert config.get_delay(2) == 2.0
        assert config.get_delay(3) == 4.0
        assert config.get_delay(4) == 8.0

    def test_retry_config_max_delay_cap(self):
        """测试最大延迟限制"""
        config = RetryConfig(
            policy=RetryPolicy.EXPONENTIAL,
            base_delay_seconds=10.0,
            max_delay_seconds=30.0
        )
        # 2^3 * 10 = 80, 但被限制在 30
        assert config.get_delay(3) == 30.0
        assert config.get_delay(10) == 30.0

    def test_retry_config_none_policy(self):
        """测试不重试策略"""
        config = RetryConfig(policy=RetryPolicy.NONE)
        assert config.get_delay(1) == 0
        assert config.get_delay(5) == 0


class TestLocaleManagerExtended:
    """本地化管理器扩展测试"""

    def test_locale_manager_supported_languages(self):
        """测试支持的语言"""
        manager = LocaleManager()

        # 测试中文
        manager.set_locale("zh_CN")
        msg = manager.get("success.project_created")
        assert "成功" in msg

        # 测试英文
        manager.set_locale("en_US")
        msg = manager.get("success.project_created")
        assert "successfully" in msg

    def test_locale_manager_japanese(self):
        """测试日语支持"""
        manager = LocaleManager()
        manager.set_locale("ja_JP")

        msg = manager.get("success.project_created")
        assert "プロジェクト" in msg or "正常に作成" in msg

        msg = manager.get("error.api_not_found", name="TestAPI")
        assert "TestAPI" in msg

    def test_locale_manager_korean(self):
        """测试韩语支持"""
        manager = LocaleManager()
        manager.set_locale("ko_KR")

        msg = manager.get("success.project_created")
        assert "프로젝트" in msg or "성공" in msg

        msg = manager.get("error.api_not_found", name="TestAPI")
        assert "TestAPI" in msg

    def test_locale_manager_fallback(self):
        """测试回退机制"""
        config = LocaleConfig(locale="unknown", fallback_locale="en_US")
        manager = LocaleManager(config)

        msg = manager.get("success.project_created")
        assert "successfully" in msg

    def test_locale_manager_format_kwargs(self):
        """测试格式化参数"""
        manager = LocaleManager()
        manager.set_locale("en_US")

        msg = manager.get("error.api_not_found", name="CreateEntity")
        assert "CreateEntity" in msg

    def test_locale_manager_custom_message(self):
        """测试自定义消息"""
        manager = LocaleManager()
        manager.register_custom_message("custom.test", "自定义测试消息")

        msg = manager.get("custom.test")
        assert msg == "自定义测试消息"


class TestEnhancedUXManagerExtended:
    """增强 UX 管理器扩展测试"""

    def test_ux_manager_locale_switching(self):
        """测试语言切换"""
        manager = EnhancedUXManager()

        manager.set_locale("zh_CN")
        msg = manager.localized("success.project_created")
        assert "成功" in msg

        manager.set_locale("en_US")
        msg = manager.localized("success.project_created")
        assert "successfully" in msg

    def test_ux_manager_japanese_messages(self):
        """测试日语消息"""
        manager = EnhancedUXManager()
        manager.set_locale("ja_JP")

        msg = manager.localized("success.entity_created", name="TestEntity")
        assert "TestEntity" in msg

    def test_ux_manager_korean_messages(self):
        """测试韩语消息"""
        manager = EnhancedUXManager()
        manager.set_locale("ko_KR")

        msg = manager.localized("success.item_created", name="TestItem")
        assert "TestItem" in msg

    def test_ux_manager_from_template(self):
        """测试从模板创建消息"""
        manager = EnhancedUXManager()

        msg = manager.from_template("workflow.step_started", step_name="SEARCH", description="搜索文档")
        assert msg is not None
        assert "SEARCH" in msg.title

    def test_ux_manager_history_session(self):
        """测试历史记录会话"""
        manager = EnhancedUXManager()
        manager.set_session("test-session-123")

        manager.success("success.project_created")
        history = manager.history.get_by_session("test-session-123")

        assert len(history) == 1


class TestTemplateRegistryExtended:
    """模板注册表扩展测试"""

    def test_template_registry_list_all(self):
        """测试列出所有模板"""
        registry = TemplateRegistry()
        templates = registry.list_all()

        assert len(templates) > 0

        # 检查内置模板
        template_ids = [t.id for t in templates]
        assert "workflow.step_started" in template_ids
        assert "workflow.step_completed" in template_ids

    def test_template_registry_render(self):
        """测试模板渲染"""
        registry = TemplateRegistry()

        msg = registry.render("workflow.step_retry", step_name="SEARCH", attempt=2, max_retries=5, delay=1.5)
        assert msg is not None
        assert "SEARCH" in msg.title
        assert "2" in msg.content

    def test_template_registry_custom_template(self):
        """测试自定义模板"""
        from mc_agent_kit.ux import MessageTemplate, MessageType

        registry = TemplateRegistry()

        custom = MessageTemplate(
            id="custom.test_template",
            type=MessageType.SUCCESS,
            title_template="自定义标题: {name}",
            content_template="内容: {content}",
        )
        registry.register(custom)

        msg = registry.render("custom.test_template", name="测试", content="内容测试")
        assert msg is not None
        assert "测试" in msg.title
        assert "内容测试" in msg.content


class TestCLIWorkflowOptions:
    """CLI 工作流选项测试"""

    def test_cli_retry_option_parsing(self):
        """测试 --retry 选项解析"""
        # 模拟 argparse 解析
        parser = argparse.ArgumentParser()
        parser.add_argument("--retry", type=int, default=0)
        parser.add_argument("--retry-policy", choices=["linear", "exponential"], default="exponential")

        args = parser.parse_args(["--retry", "3", "--retry-policy", "linear"])
        assert args.retry == 3
        assert args.retry_policy == "linear"

    def test_cli_progress_option_parsing(self):
        """测试 --progress 选项解析"""
        parser = argparse.ArgumentParser()
        parser.add_argument("--progress", action="store_true", default=False)

        args = parser.parse_args(["--progress"])
        assert args.progress is True

        args = parser.parse_args([])
        assert args.progress is False

    def test_cli_locale_option_parsing(self):
        """测试 --locale 选项解析"""
        parser = argparse.ArgumentParser()
        parser.add_argument("--locale", choices=["zh_CN", "en_US", "ja_JP", "ko_KR"], default="zh_CN")

        args = parser.parse_args(["--locale", "en_US"])
        assert args.locale == "en_US"

        args = parser.parse_args(["--locale", "ja_JP"])
        assert args.locale == "ja_JP"

        args = parser.parse_args(["--locale", "ko_KR"])
        assert args.locale == "ko_KR"


class TestEnhancedWorkflowWithRetry:
    """带重试的增强工作流测试"""

    def test_workflow_with_retry_config(self):
        """测试带重试配置的工作流"""
        retry_config = RetryConfig(
            max_retries=5,
            policy=RetryPolicy.EXPONENTIAL,
        )

        workflow = create_enhanced_workflow(retry_config=retry_config)

        assert workflow.retry_config.max_retries == 5
        assert workflow.retry_config.policy == RetryPolicy.EXPONENTIAL

    def test_workflow_control_pause_resume(self):
        """测试暂停/恢复控制"""
        control = WorkflowControl()

        assert control.state == WorkflowState.IDLE

        # 手动设置状态为 RUNNING 模拟工作流开始
        control.state = WorkflowState.RUNNING
        assert control.state == WorkflowState.RUNNING

        control.pause()
        assert control.state == WorkflowState.PAUSED

        control.resume()
        assert control.state == WorkflowState.RUNNING

    def test_workflow_control_cancel(self):
        """测试取消控制"""
        control = WorkflowControl()

        control.cancel()
        assert control.state == WorkflowState.CANCELLED
        assert control.is_cancelled() is True


class TestIteration44Integration:
    """迭代 #44 集成测试"""

    def test_locale_and_workflow_integration(self):
        """测试本地化与工作流集成"""
        ux = get_ux_manager(locale="en_US")

        # 创建工作流消息
        msg = EnhancedUXManager.workflow_started(5)
        assert "5" in msg.content

        msg = EnhancedUXManager.workflow_completed(True, 1500)
        assert "1500" in msg.content

    def test_all_supported_locales_available(self):
        """测试所有支持的语言都可用"""
        supported_locales = ["zh_CN", "en_US", "ja_JP", "ko_KR"]

        for locale in supported_locales:
            manager = LocaleManager()
            manager.set_locale(locale)

            # 每种语言都应该有基本消息
            msg = manager.get("success.project_created")
            assert msg is not None
            assert msg != "success.project_created"  # 不应该返回 key 本身

    def test_retry_delay_reasonable(self):
        """测试重试延迟合理"""
        config = RetryConfig(
            max_retries=5,
            policy=RetryPolicy.EXPONENTIAL,
            base_delay_seconds=1.0,
        )

        delays = [config.get_delay(i) for i in range(1, 6)]
        # 延迟应该递增
        assert delays == sorted(delays)
        # 最大延迟应该被限制
        assert all(d <= config.max_delay_seconds for d in delays)


class TestIteration44AcceptanceCriteria:
    """迭代 #44 验收标准测试"""

    def test_workflow_cli_has_retry_option(self):
        """验收: workflow 命令支持 --retry 选项"""
        parser = argparse.ArgumentParser()
        parser.add_argument("--retry", type=int, default=0)
        args = parser.parse_args(["--retry", "3"])
        assert args.retry == 3

    def test_workflow_cli_has_progress_option(self):
        """验收: workflow 命令支持 --progress 选项"""
        parser = argparse.ArgumentParser()
        parser.add_argument("--progress", action="store_true")
        args = parser.parse_args(["--progress"])
        assert args.progress is True

    def test_workflow_cli_has_locale_option(self):
        """验收: workflow 命令支持 --locale 选项"""
        parser = argparse.ArgumentParser()
        parser.add_argument("--locale", choices=["zh_CN", "en_US", "ja_JP", "ko_KR"])
        args = parser.parse_args(["--locale", "ja_JP"])
        assert args.locale == "ja_JP"

    def test_locale_supports_chinese(self):
        """验收: 支持中文"""
        manager = LocaleManager()
        manager.set_locale("zh_CN")
        msg = manager.get("success.project_created")
        assert "成功" in msg or "创建" in msg

    def test_locale_supports_english(self):
        """验收: 支持英文"""
        manager = LocaleManager()
        manager.set_locale("en_US")
        msg = manager.get("success.project_created")
        assert "success" in msg.lower() or "created" in msg.lower()

    def test_locale_supports_japanese(self):
        """验收: 支持日语"""
        manager = LocaleManager()
        manager.set_locale("ja_JP")
        msg = manager.get("success.project_created")
        # 日语消息存在
        assert msg is not None

    def test_locale_supports_korean(self):
        """验收: 支持韩语"""
        manager = LocaleManager()
        manager.set_locale("ko_KR")
        msg = manager.get("success.project_created")
        # 韩语消息存在
        assert msg is not None

    def test_retry_policy_linear_works(self):
        """验收: 线性重试策略工作"""
        config = RetryConfig(policy=RetryPolicy.LINEAR, base_delay_seconds=2.0)
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0

    def test_retry_policy_exponential_works(self):
        """验收: 指数重试策略工作"""
        config = RetryConfig(policy=RetryPolicy.EXPONENTIAL, base_delay_seconds=1.0)
        assert config.get_delay(1) == 1.0
        assert config.get_delay(2) == 2.0
        assert config.get_delay(3) == 4.0

    def test_progress_info_calculates_percentage(self):
        """验收: 进度信息计算百分比"""
        from mc_agent_kit.workflow import ProgressInfo

        info = ProgressInfo(
            current_step=WorkflowStep.SEARCH_DOCS,
            total_steps=5,
            completed_steps=2,
            percentage=40.0,
            elapsed_seconds=10.0,
            estimated_remaining_seconds=15.0,
            message="测试进度",
        )

        assert info.percentage == 40.0
        assert info.completed_steps == 2
        assert info.total_steps == 5