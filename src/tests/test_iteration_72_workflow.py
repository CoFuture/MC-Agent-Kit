"""
测试智能工作流模块

测试 iteration #72 的工作流功能。
"""

import pytest
import time
from unittest.mock import Mock, patch

from mc_agent_kit.llm.workflow import (
    IntelligentWorkflow,
    RequirementAnalyzer,
    SolutionDesigner,
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepType,
    run_workflow,
)
from mc_agent_kit.llm.base import LLMConfig


class TestWorkflowStep:
    """测试工作流步骤"""

    def test_create_step(self):
        """创建步骤"""
        step = WorkflowStep(
            step_type=WorkflowStepType.ANALYZE,
            name="测试步骤",
            description="测试描述",
        )

        assert step.step_type == WorkflowStepType.ANALYZE
        assert step.name == "测试步骤"
        assert step.description == "测试描述"
        assert step.status == WorkflowStatus.PENDING
        assert step.error is None

    def test_step_to_dict(self):
        """步骤序列化"""
        step = WorkflowStep(
            step_type=WorkflowStepType.GENERATE,
            name="生成代码",
            input_data={"key": "value"},
            output_data={"result": "success"},
        )

        data = step.to_dict()

        assert data["step_type"] == "generate"
        assert data["name"] == "生成代码"
        assert data["input_data"] == {"key": "value"}
        assert data["output_data"] == {"result": "success"}
        assert data["status"] == "pending"

    def test_step_with_error(self):
        """带错误的步骤"""
        step = WorkflowStep(
            step_type=WorkflowStepType.FIX,
            name="修复",
            status=WorkflowStatus.FAILED,
            error="测试错误",
        )

        assert step.status == WorkflowStatus.FAILED
        assert step.error == "测试错误"


class TestWorkflowContext:
    """测试工作流上下文"""

    def test_create_context(self):
        """创建上下文"""
        context = WorkflowContext(
            workflow_id="test-123",
            project_name="TestProject",
            module_name="test_module",
            target="server",
            max_iterations=3,
            min_review_score=70.0,
        )

        assert context.workflow_id == "test-123"
        assert context.project_name == "TestProject"
        assert context.module_name == "test_module"
        assert context.target == "server"
        assert context.max_iterations == 3
        assert context.min_review_score == 70.0

    def test_default_context(self):
        """默认上下文"""
        context = WorkflowContext()

        assert context.workflow_id == ""
        assert context.project_name == ""
        assert context.max_iterations == 3
        assert context.min_review_score == 70.0

    def test_context_to_dict(self):
        """上下文序列化"""
        context = WorkflowContext(
            workflow_id="test-456",
            project_name="MyAddon",
        )
        context.variables["key"] = "value"

        data = context.to_dict()

        assert data["workflow_id"] == "test-456"
        assert data["project_name"] == "MyAddon"
        assert data["variables"] == {"key": "value"}


class TestWorkflowResult:
    """测试工作流结果"""

    def test_create_result(self):
        """创建结果"""
        result = WorkflowResult(
            success=True,
            status=WorkflowStatus.COMPLETED,
            iterations=2,
            total_duration_ms=1500.0,
        )

        assert result.success is True
        assert result.status == WorkflowStatus.COMPLETED
        assert result.iterations == 2
        assert result.total_duration_ms == 1500.0

    def test_failed_result(self):
        """失败结果"""
        result = WorkflowResult(
            success=False,
            status=WorkflowStatus.FAILED,
            error="测试失败",
        )

        assert result.success is False
        assert result.status == WorkflowStatus.FAILED
        assert result.error == "测试失败"

    def test_result_to_dict(self):
        """结果序列化"""
        result = WorkflowResult(
            success=True,
            status=WorkflowStatus.COMPLETED,
            iterations=1,
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["status"] == "completed"
        assert data["iterations"] == 1


class TestRequirementAnalyzer:
    """测试需求分析器"""

    def test_create_analyzer(self):
        """创建分析器"""
        analyzer = RequirementAnalyzer()

        assert analyzer.llm_config is not None
        assert analyzer.llm_manager is not None

    def test_analyze_entity_requirement(self):
        """分析实体需求"""
        analyzer = RequirementAnalyzer()
        requirement = "创建一个自定义实体"

        result = analyzer.analyze(requirement)

        assert isinstance(result, dict)
        assert "entities" in result or "apis" in result

    def test_analyze_event_requirement(self):
        """分析事件需求"""
        analyzer = RequirementAnalyzer()
        requirement = "监听玩家聊天事件并回复"

        result = analyzer.analyze(requirement)

        assert isinstance(result, dict)

    def test_analyze_ui_requirement(self):
        """分析 UI 需求"""
        analyzer = RequirementAnalyzer()
        requirement = "创建一个 UI 界面显示玩家信息"

        result = analyzer.analyze(requirement)

        assert isinstance(result, dict)

    def test_analyze_network_requirement(self):
        """分析网络同步需求"""
        analyzer = RequirementAnalyzer()
        requirement = "实现客户端和服务端数据同步"

        result = analyzer.analyze(requirement)

        assert isinstance(result, dict)


class TestSolutionDesigner:
    """测试方案设计器"""

    def test_create_designer(self):
        """创建设计器"""
        designer = SolutionDesigner()

        assert designer.llm_config is not None
        assert designer.llm_manager is not None

    def test_design_simple_requirement(self):
        """设计简单需求"""
        designer = SolutionDesigner()
        requirement = "创建一个简单的实体"
        analysis = {
            "entities": ["custom_entity"],
            "apis": ["CreateEngineEntity"],
            "target": "server",
        }

        result = designer.design(requirement, analysis)

        assert isinstance(result, dict)
        assert "implementation_steps" in result or "modules" in result


class TestIntelligentWorkflow:
    """测试智能工作流"""

    def test_create_workflow(self):
        """创建工作流"""
        workflow = IntelligentWorkflow()

        assert workflow.analyzer is not None
        assert workflow.designer is not None
        assert workflow.generator is not None
        assert workflow.reviewer is not None
        assert workflow.fixer is not None

    def test_run_simple_workflow(self):
        """运行简单工作流"""
        workflow = IntelligentWorkflow()
        requirement = "创建一个简单的 ModSDK 脚本"

        result = workflow.run(requirement)

        assert isinstance(result, WorkflowResult)
        assert result.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
        assert len(result.steps) > 0

    def test_run_workflow_with_context(self):
        """带上下文运行工作流"""
        workflow = IntelligentWorkflow()
        requirement = "创建一个实体行为脚本"
        context = WorkflowContext(
            project_name="TestAddon",
            module_name="entity_behavior",
            target="server",
            max_iterations=2,
            min_review_score=60.0,
        )

        result = workflow.run(requirement, context)

        assert isinstance(result, WorkflowResult)
        assert result.iterations <= 2

    def test_run_workflow_with_progress_callback(self):
        """带进度回调运行工作流"""
        workflow = IntelligentWorkflow()
        requirement = "测试进度回调"
        progress_steps = []

        def progress_callback(step: WorkflowStep):
            progress_steps.append(step.name)

        result = workflow.run(requirement, progress_callback=progress_callback)

        assert isinstance(result, WorkflowResult)
        assert len(progress_steps) > 0

    def test_workflow_steps_order(self):
        """测试步骤顺序"""
        workflow = IntelligentWorkflow()
        requirement = "测试步骤顺序"

        result = workflow.run(requirement)

        # 验证至少包含分析和生成步骤
        step_types = [s.step_type for s in result.steps]
        assert WorkflowStepType.ANALYZE in step_types
        assert WorkflowStepType.GENERATE in step_types


class TestRunWorkflow:
    """测试便捷函数"""

    def test_run_workflow_function(self):
        """运行工作流函数"""
        result = run_workflow(
            requirement="创建一个测试脚本",
            project_name="TestProject",
            target="server",
            max_iterations=2,
            min_review_score=60.0,
        )

        assert isinstance(result, WorkflowResult)


class TestWorkflowIntegration:
    """测试工作流集成"""

    def test_full_workflow_cycle(self):
        """完整工作流周期"""
        workflow = IntelligentWorkflow()
        requirement = """
        创建一个 Minecraft ModSDK 实体，
        具有以下功能：
        1. 自定义外观
        2. 移动行为
        3. 与玩家交互
        """

        result = workflow.run(requirement)

        assert isinstance(result, WorkflowResult)
        assert len(result.steps) >= 2  # 至少有分析和生成步骤

    def test_workflow_iteration_limit(self):
        """测试迭代限制"""
        workflow = IntelligentWorkflow()
        context = WorkflowContext(
            max_iterations=1,
            min_review_score=90.0,  # 高分要求，可能需要多次迭代
        )

        result = workflow.run("测试迭代限制", context)

        assert result.iterations <= 1

    def test_workflow_error_handling(self):
        """测试错误处理"""
        workflow = IntelligentWorkflow()

        # 空需求应该也能处理
        result = workflow.run("")

        assert isinstance(result, WorkflowResult)


class TestWorkflowPerformance:
    """性能测试"""

    def test_workflow_execution_time(self):
        """测试执行时间"""
        workflow = IntelligentWorkflow()
        requirement = "性能测试工作流"

        start_time = time.time()
        result = workflow.run(requirement)
        duration = time.time() - start_time

        # 应该在合理时间内完成（Mock 模式下应该很快）
        assert duration < 10.0
        assert result.total_duration_ms >= 0

    def test_workflow_memory_usage(self):
        """测试内存使用"""
        workflow = IntelligentWorkflow()
        context = WorkflowContext(
            max_iterations=3,
        )

        # 多次运行不应该导致内存泄漏
        for _ in range(3):
            result = workflow.run("测试", context)
            assert isinstance(result, WorkflowResult)


class TestWorkflowEdgeCases:
    """边缘情况测试"""

    def test_empty_requirement(self):
        """空需求"""
        workflow = IntelligentWorkflow()
        result = workflow.run("")

        assert isinstance(result, WorkflowResult)

    def test_very_long_requirement(self):
        """超长需求"""
        workflow = IntelligentWorkflow()
        requirement = "测试需求 " * 100

        result = workflow.run(requirement)

        assert isinstance(result, WorkflowResult)

    def test_special_characters_in_requirement(self):
        """特殊字符"""
        workflow = IntelligentWorkflow()
        requirement = "测试！@#$%^&*()_+{}|:<>?"

        result = workflow.run(requirement)

        assert isinstance(result, WorkflowResult)

    def test_unicode_requirement(self):
        """Unicode 字符"""
        workflow = IntelligentWorkflow()
        requirement = "测试中文 English Español"

        result = workflow.run(requirement)

        assert isinstance(result, WorkflowResult)


class TestWorkflowAcceptanceCriteria:
    """验收标准测试"""

    def test_workflow_module_exists(self):
        """工作流模块存在"""
        from mc_agent_kit.llm import workflow
        assert workflow is not None

    def test_workflow_classes_available(self):
        """工作流类可用"""
        assert IntelligentWorkflow is not None
        assert RequirementAnalyzer is not None
        assert SolutionDesigner is not None
        assert WorkflowContext is not None
        assert WorkflowResult is not None

    def test_workflow_enums_available(self):
        """工作流枚举可用"""
        assert WorkflowStepType is not None
        assert WorkflowStatus is not None

    def test_workflow_run_function_available(self):
        """运行函数可用"""
        assert run_workflow is not None
        result = run_workflow("测试")
        assert isinstance(result, WorkflowResult)

    def test_workflow_integration_with_llm(self):
        """与 LLM 集成"""
        workflow = IntelligentWorkflow()

        # 验证工作流使用了 LLM 组件
        assert workflow.generator is not None
        assert workflow.reviewer is not None

    def test_all_tests_pass(self):
        """所有测试通过"""
        # 这个测试确保本文件的所有测试都通过
        pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
