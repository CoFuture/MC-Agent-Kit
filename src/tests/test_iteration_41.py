"""
迭代 #41 测试

测试 MVP 闭环完善与用户体验提升的新增功能
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import os

# Workflow 模块测试
from mc_agent_kit.workflow import (
    EndToEndWorkflow,
    WorkflowConfig,
    WorkflowResult,
    WorkflowStep,
    WorkflowStepResult,
    create_workflow,
    run_development_cycle,
)

# UX 模块测试
from mc_agent_kit.ux import (
    CLIOutputFormatter,
    MessageType,
    OutputFormat,
    UserExperienceEnhancer,
    UserMessage,
    UserMessageBuilder,
    error,
    hint,
    info,
    success,
    warning,
)


class TestWorkflowStep:
    """工作流步骤测试"""

    def test_workflow_step_values(self):
        """测试步骤枚举值"""
        assert WorkflowStep.SEARCH_DOCS.value == "search_docs"
        assert WorkflowStep.CREATE_PROJECT.value == "create_project"
        assert WorkflowStep.LAUNCH_TEST.value == "launch_test"
        assert WorkflowStep.DIAGNOSE_ERROR.value == "diagnose_error"
        assert WorkflowStep.FIX_ERROR.value == "fix_error"

    def test_workflow_step_count(self):
        """测试步骤数量"""
        assert len(WorkflowStep) == 5


class TestWorkflowStepStatus:
    """工作流步骤状态测试"""

    def test_status_values(self):
        """测试状态枚举值"""
        from mc_agent_kit.workflow.end_to_end import WorkflowStepStatus
        assert WorkflowStepStatus.SUCCESS.value == "success"
        assert WorkflowStepStatus.FAILED.value == "failed"
        assert WorkflowStepStatus.PENDING.value == "pending"
        assert WorkflowStepStatus.RUNNING.value == "running"
        assert WorkflowStepStatus.SKIPPED.value == "skipped"


class TestWorkflowStepResult:
    """工作流步骤结果测试"""

    def test_step_result_creation(self):
        """测试创建步骤结果"""
        from mc_agent_kit.workflow.end_to_end import WorkflowStepStatus
        result = WorkflowStepResult(
            step=WorkflowStep.SEARCH_DOCS,
            status=WorkflowStepStatus.SUCCESS,
        )
        assert result.step == WorkflowStep.SEARCH_DOCS
        assert result.status == WorkflowStepStatus.SUCCESS

    def test_step_result_to_dict(self):
        """测试步骤结果转字典"""
        from mc_agent_kit.workflow.end_to_end import WorkflowStepStatus
        result = WorkflowStepResult(
            step=WorkflowStep.CREATE_PROJECT,
            status=WorkflowStepStatus.SUCCESS,
            output={"project_path": "/tmp/test"},
        )
        data = result.to_dict()
        assert data["step"] == "create_project"
        assert data["status"] == "success"
        assert data["output"]["project_path"] == "/tmp/test"

    def test_step_result_with_error(self):
        """测试带错误的步骤结果"""
        from mc_agent_kit.workflow.end_to_end import WorkflowStepStatus
        result = WorkflowStepResult(
            step=WorkflowStep.LAUNCH_TEST,
            status=WorkflowStepStatus.FAILED,
            error="游戏路径不存在",
            suggestions=["检查游戏安装"],
        )
        assert result.error == "游戏路径不存在"
        assert "检查游戏安装" in result.suggestions


class TestWorkflowConfig:
    """工作流配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = WorkflowConfig()
        assert config.project_name == "my_addon"
        assert config.auto_fix is True
        assert config.verbose is False
        assert config.timeout_seconds == 300

    def test_custom_config(self):
        """测试自定义配置"""
        config = WorkflowConfig(
            project_name="test_project",
            output_dir="/tmp",
            game_path="/path/to/game",
            auto_fix=False,
        )
        assert config.project_name == "test_project"
        assert config.output_dir == "/tmp"
        assert config.game_path == "/path/to/game"
        assert config.auto_fix is False


class TestWorkflowResult:
    """工作流结果测试"""

    def test_empty_result(self):
        """测试空结果"""
        result = WorkflowResult(success=True)
        assert result.success is True
        assert len(result.steps) == 0

    def test_result_with_steps(self):
        """测试带步骤的结果"""
        from mc_agent_kit.workflow.end_to_end import WorkflowStepStatus
        step1 = WorkflowStepResult(step=WorkflowStep.SEARCH_DOCS, status=WorkflowStepStatus.SUCCESS)
        step2 = WorkflowStepResult(step=WorkflowStep.CREATE_PROJECT, status=WorkflowStepStatus.SUCCESS)
        result = WorkflowResult(success=True, steps=[step1, step2])
        assert len(result.steps) == 2
        assert len(result.success_steps) == 2
        assert len(result.failed_steps) == 0

    def test_result_with_failed_steps(self):
        """测试有失败步骤的结果"""
        from mc_agent_kit.workflow.end_to_end import WorkflowStepStatus
        step1 = WorkflowStepResult(step=WorkflowStep.SEARCH_DOCS, status=WorkflowStepStatus.SUCCESS)
        step2 = WorkflowStepResult(step=WorkflowStep.LAUNCH_TEST, status=WorkflowStepStatus.FAILED)
        result = WorkflowResult(success=False, steps=[step1, step2])
        assert len(result.success_steps) == 1
        assert len(result.failed_steps) == 1

    def test_result_to_dict(self):
        """测试结果转字典"""
        from mc_agent_kit.workflow.end_to_end import WorkflowStepStatus
        step = WorkflowStepResult(step=WorkflowStep.SEARCH_DOCS, status=WorkflowStepStatus.SUCCESS)
        result = WorkflowResult(success=True, steps=[step], total_duration_ms=100)
        data = result.to_dict()
        assert data["success"] is True
        assert data["total_duration_ms"] == 100
        assert len(data["steps"]) == 1


class TestEndToEndWorkflow:
    """端到端工作流测试"""

    def test_workflow_creation(self):
        """测试工作流创建"""
        config = WorkflowConfig(project_name="test")
        workflow = EndToEndWorkflow(config)
        assert workflow.config.project_name == "test"

    def test_create_workflow_function(self):
        """测试便捷创建函数"""
        workflow = create_workflow()
        assert workflow is not None
        assert workflow.config.project_name == "my_addon"

    def test_step_search_docs(self):
        """测试搜索文档步骤"""
        from mc_agent_kit.workflow.end_to_end import WorkflowStepStatus
        config = WorkflowConfig()
        workflow = EndToEndWorkflow(config)
        result = workflow.step_search_docs("创建实体")
        assert result.step == WorkflowStep.SEARCH_DOCS
        # 知识库可能未加载，但步骤应该完成（成功或失败）
        assert result.status in (WorkflowStepStatus.SUCCESS, WorkflowStepStatus.FAILED)

    def test_step_create_project(self):
        """测试创建项目步骤"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = WorkflowConfig(
                project_name="test_project",
                output_dir=tmpdir,
            )
            workflow = EndToEndWorkflow(config)
            result = workflow.step_create_project()
            assert result.step == WorkflowStep.CREATE_PROJECT
            assert "project_path" in result.output

    def test_step_diagnose_error_no_path(self):
        """测试诊断错误步骤（无路径）"""
        config = WorkflowConfig()
        workflow = EndToEndWorkflow(config)
        result = workflow.step_diagnose_error()
        assert result.step == WorkflowStep.DIAGNOSE_ERROR


class TestRunDevelopmentCycle:
    """运行开发周期测试"""

    def test_run_development_cycle(self):
        """测试运行开发周期"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_development_cycle(
                project_name="test_addon",
                output_dir=tmpdir,
                search_query="创建实体",
            )
            assert result is not None
            assert isinstance(result, WorkflowResult)


# ==================== UX 模块测试 ====================

class TestMessageType:
    """消息类型测试"""

    def test_message_type_values(self):
        """测试消息类型值"""
        assert MessageType.SUCCESS.value == "success"
        assert MessageType.ERROR.value == "error"
        assert MessageType.WARNING.value == "warning"
        assert MessageType.INFO.value == "info"
        assert MessageType.HINT.value == "hint"


class TestOutputFormat:
    """输出格式测试"""

    def test_output_format_values(self):
        """测试输出格式值"""
        assert OutputFormat.TEXT.value == "text"
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.MARKDOWN.value == "markdown"


class TestUserMessage:
    """用户消息测试"""

    def test_message_creation(self):
        """测试创建消息"""
        msg = UserMessage(
            type=MessageType.SUCCESS,
            title="操作成功",
        )
        assert msg.type == MessageType.SUCCESS
        assert msg.title == "操作成功"

    def test_message_to_text(self):
        """测试消息转文本"""
        msg = UserMessage(
            type=MessageType.SUCCESS,
            title="操作成功",
            content="项目已创建",
        )
        text = msg.to_text()
        assert "✅" in text
        assert "操作成功" in text
        assert "项目已创建" in text

    def test_message_to_json(self):
        """测试消息转 JSON"""
        msg = UserMessage(
            type=MessageType.ERROR,
            title="发生错误",
            content="文件不存在",
        )
        data = msg.to_json()
        assert data["type"] == "error"
        assert data["title"] == "发生错误"
        assert data["content"] == "文件不存在"

    def test_message_to_markdown(self):
        """测试消息转 Markdown"""
        msg = UserMessage(
            type=MessageType.INFO,
            title="提示信息",
            content="这是一条提示",
        )
        md = msg.to_markdown()
        assert "##" in md
        assert "提示信息" in md

    def test_message_with_suggestions(self):
        """测试带建议的消息"""
        msg = UserMessage(
            type=MessageType.ERROR,
            title="API 未找到",
            suggestions=["检查拼写", "搜索相关 API"],
        )
        text = msg.to_text()
        assert "建议:" in text
        assert "检查拼写" in text

    def test_message_with_code_example(self):
        """测试带代码示例的消息"""
        msg = UserMessage(
            type=MessageType.HINT,
            title="使用示例",
            code_example="CreateEngineEntity('my_entity', (0, 64, 0))",
        )
        text = msg.to_text()
        assert "示例:" in text
        assert "CreateEngineEntity" in text


class TestUserMessageBuilder:
    """用户消息构建器测试"""

    def test_builder_success(self):
        """测试成功消息构建"""
        msg = (
            UserMessageBuilder(MessageType.SUCCESS, "成功")
            .content("操作完成")
            .build()
        )
        assert msg.type == MessageType.SUCCESS
        assert msg.title == "成功"
        assert msg.content == "操作完成"

    def test_builder_with_details(self):
        """测试带详情的消息构建"""
        msg = (
            UserMessageBuilder(MessageType.INFO, "信息")
            .detail("详情1")
            .detail("详情2")
            .build()
        )
        assert len(msg.details) == 2
        assert "详情1" in msg.details

    def test_builder_with_suggestions(self):
        """测试带建议的消息构建"""
        msg = (
            UserMessageBuilder(MessageType.WARNING, "警告")
            .suggestion("建议1")
            .suggestion("建议2")
            .build()
        )
        assert len(msg.suggestions) == 2

    def test_builder_with_code(self):
        """测试带代码的消息构建"""
        msg = (
            UserMessageBuilder(MessageType.HINT, "提示")
            .code("print('Hello')")
            .build()
        )
        assert msg.code_example == "print('Hello')"

    def test_builder_with_learn_more(self):
        """测试带了解更多链接的消息构建"""
        msg = (
            UserMessageBuilder(MessageType.INFO, "信息")
            .learn_more("https://docs.example.com")
            .build()
        )
        assert msg.learn_more == "https://docs.example.com"


class TestUserExperienceEnhancer:
    """用户体验增强器测试"""

    def test_success_builder(self):
        """测试成功消息构建器"""
        builder = UserExperienceEnhancer.success("操作成功")
        assert builder._message.type == MessageType.SUCCESS
        assert builder._message.title == "操作成功"

    def test_error_builder(self):
        """测试错误消息构建器"""
        builder = UserExperienceEnhancer.error("发生错误")
        assert builder._message.type == MessageType.ERROR

    def test_warning_builder(self):
        """测试警告消息构建器"""
        builder = UserExperienceEnhancer.warning("警告信息")
        assert builder._message.type == MessageType.WARNING

    def test_info_builder(self):
        """测试信息消息构建器"""
        builder = UserExperienceEnhancer.info("提示信息")
        assert builder._message.type == MessageType.INFO

    def test_hint_builder(self):
        """测试提示消息构建器"""
        builder = UserExperienceEnhancer.hint("小提示")
        assert builder._message.type == MessageType.HINT

    def test_project_created_message(self):
        """测试项目创建消息"""
        msg = UserExperienceEnhancer.project_created("/tmp/my_project")
        assert msg.type == MessageType.SUCCESS
        assert "/tmp/my_project" in msg.content

    def test_entity_created_message(self):
        """测试实体创建消息"""
        msg = UserExperienceEnhancer.entity_created("zombie", "/tmp/entities/zombie.json")
        assert msg.type == MessageType.SUCCESS
        assert "zombie" in msg.title
        assert msg.code_example is not None

    def test_search_result_message(self):
        """测试搜索结果消息"""
        msg = UserExperienceEnhancer.search_result("创建实体", 5, 3)
        assert msg.type == MessageType.INFO
        assert "5 个 API" in msg.content
        assert "3 个事件" in msg.content

    def test_diagnostic_issue_message(self):
        """测试诊断问题消息"""
        msg = UserExperienceEnhancer.diagnostic_issue(
            "配置错误",
            "manifest.json 缺少 name 字段",
            "添加 name 字段",
        )
        assert msg.type == MessageType.ERROR
        assert "配置错误" in msg.title

    def test_memory_issue_message(self):
        """测试内存问题消息"""
        msg = UserExperienceEnhancer.memory_issue("texture", "纹理过大")
        assert msg.type == MessageType.WARNING
        assert "纹理" in msg.suggestions[0]

    def test_api_not_found_message(self):
        """测试 API 未找到消息"""
        msg = UserExperienceEnhancer.api_not_found("CreateEntiti")  # 拼写错误
        assert msg.type == MessageType.WARNING
        assert "CreateEntiti" in msg.title
        assert len(msg.suggestions) >= 2

    def test_config_invalid_message(self):
        """测试配置无效消息"""
        msg = UserExperienceEnhancer.config_invalid(
            "manifest.json",
            ["缺少 name 字段", "版本号格式错误"],
        )
        assert msg.type == MessageType.ERROR
        assert "manifest.json" in msg.content

    def test_game_launch_failed_message(self):
        """测试游戏启动失败消息"""
        msg = UserExperienceEnhancer.game_launch_failed("游戏路径不存在")
        assert msg.type == MessageType.ERROR
        assert "游戏路径不存在" in msg.content


class TestCLIOutputFormatter:
    """CLI 输出格式化器测试"""

    def test_format_table(self):
        """测试表格格式化"""
        output = CLIOutputFormatter.format_table(
            headers=["名称", "类型", "状态"],
            rows=[
                ["CreateEntity", "API", "可用"],
                ["OnServerChat", "事件", "可用"],
            ],
            title="API 列表",
        )
        assert "API 列表" in output
        assert "名称" in output
        assert "CreateEntity" in output

    def test_format_table_no_title(self):
        """测试无标题表格格式化"""
        output = CLIOutputFormatter.format_table(
            headers=["A", "B"],
            rows=[["1", "2"]],
        )
        assert "A" in output
        assert "1" in output

    def test_format_list_numbered(self):
        """测试编号列表格式化"""
        output = CLIOutputFormatter.format_list(
            items=["项目1", "项目2", "项目3"],
            title="列表",
            numbered=True,
        )
        assert "1." in output
        assert "2." in output
        assert "项目1" in output

    def test_format_list_bullet(self):
        """测试项目符号列表格式化"""
        output = CLIOutputFormatter.format_list(
            items=["项目A", "项目B"],
            numbered=False,
        )
        assert "•" in output

    def test_format_key_value(self):
        """测试键值对格式化"""
        output = CLIOutputFormatter.format_key_value(
            data={"名称": "测试", "版本": "1.0.0"},
            title="信息",
        )
        assert "名称" in output
        assert "测试" in output
        assert "版本" in output


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_success_function(self):
        """测试 success 函数"""
        builder = success("成功")
        assert builder._message.type == MessageType.SUCCESS

    def test_error_function(self):
        """测试 error 函数"""
        builder = error("错误")
        assert builder._message.type == MessageType.ERROR

    def test_warning_function(self):
        """测试 warning 函数"""
        builder = warning("警告")
        assert builder._message.type == MessageType.WARNING

    def test_info_function(self):
        """测试 info 函数"""
        builder = info("信息")
        assert builder._message.type == MessageType.INFO

    def test_hint_function(self):
        """测试 hint 函数"""
        builder = hint("提示")
        assert builder._message.type == MessageType.HINT


class TestIteration41Integration:
    """迭代 #41 集成测试"""

    def test_workflow_with_ux_messages(self):
        """测试工作流与 UX 消息集成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = WorkflowConfig(
                project_name="integration_test",
                output_dir=tmpdir,
            )
            workflow = EndToEndWorkflow(config)
            
            # 执行创建项目步骤
            result = workflow.step_create_project()
            
            # 生成用户友好的消息
            if result.output.get("project_path"):
                msg = UserExperienceEnhancer.project_created(
                    result.output["project_path"]
                )
                assert msg.type == MessageType.SUCCESS

    def test_end_to_end_workflow_timing(self):
        """测试端到端工作流计时"""
        import time
        start = time.time()
        
        config = WorkflowConfig()
        workflow = EndToEndWorkflow(config)
        result = workflow.step_search_docs("测试")
        
        elapsed = time.time() - start
        assert elapsed < 5.0  # 应该在 5 秒内完成
        assert result.duration_ms >= 0


class TestIteration41AcceptanceCriteria:
    """迭代 #41 验收标准测试"""

    def test_workflow_module_available(self):
        """验证工作流模块可用"""
        from mc_agent_kit import workflow
        assert hasattr(workflow, "EndToEndWorkflow")
        assert hasattr(workflow, "WorkflowConfig")

    def test_ux_module_available(self):
        """验证 UX 模块可用"""
        from mc_agent_kit import ux
        assert hasattr(ux, "UserExperienceEnhancer")
        assert hasattr(ux, "CLIOutputFormatter")

    def test_workflow_steps_complete(self):
        """验证工作流步骤完整"""
        steps = list(WorkflowStep)
        assert len(steps) == 5
        assert WorkflowStep.SEARCH_DOCS in steps
        assert WorkflowStep.CREATE_PROJECT in steps
        assert WorkflowStep.LAUNCH_TEST in steps
        assert WorkflowStep.DIAGNOSE_ERROR in steps
        assert WorkflowStep.FIX_ERROR in steps

    def test_message_types_complete(self):
        """验证消息类型完整"""
        types = list(MessageType)
        assert len(types) == 5
        assert MessageType.SUCCESS in types
        assert MessageType.ERROR in types
        assert MessageType.WARNING in types
        assert MessageType.INFO in types
        assert MessageType.HINT in types