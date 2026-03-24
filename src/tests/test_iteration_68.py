"""
迭代 #68 测试：CLI 增强与自动化工作流

测试内容：
- 批量工作流功能
- 插件系统增强
- 性能优化功能
"""

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from mc_agent_kit.workflow.batch_workflow import (
    BatchWorkflow,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStep,
)


class TestWorkflowStep:
    """Workflow step tests."""

    def test_step_creation(self) -> None:
        """Test basic step creation."""
        step = WorkflowStep(
            name="test_step",
            action="echo",
            params={"message": "Hello"},
        )

        assert step.name == "test_step"
        assert step.action == "echo"
        assert step.params == {"message": "Hello"}
        assert step.timeout == 300
        assert step.retry_count == 0
        assert step.max_retries == 3

    def test_step_defaults(self) -> None:
        """Test step default values."""
        step = WorkflowStep(
            name="simple_step",
            action="test",
        )

        assert step.params == {}
        assert step.timeout == 300
        assert step.max_retries == 3


class TestWorkflowResult:
    """Workflow result tests."""

    def test_result_creation(self) -> None:
        """Test basic result creation."""
        result = WorkflowResult(
            workflow_name="test_workflow",
            status=WorkflowStatus.PENDING,
        )

        assert result.workflow_name == "test_workflow"
        assert result.status == WorkflowStatus.PENDING
        assert result.results == []
        assert result.errors == []
        assert result.duration == 0.0

    def test_result_with_timing(self) -> None:
        """Test result with timing information."""
        result = WorkflowResult(
            workflow_name="test",
            status=WorkflowStatus.COMPLETED,
            start_time=100.0,
            end_time=105.5,
        )

        assert result.duration == 5.5

    def test_result_to_dict(self) -> None:
        """Test result serialization."""
        result = WorkflowResult(
            workflow_name="test",
            status=WorkflowStatus.COMPLETED,
            start_time=100.0,
            end_time=105.0,
            results=[{"step": "step1", "success": True}],
            errors=[],
        )

        data = result.to_dict()
        assert data["workflow_name"] == "test"
        assert data["status"] == "completed"
        assert data["duration"] == 5.0
        assert len(data["results"]) == 1


class TestBatchWorkflow:
    """Batch workflow tests."""

    def test_workflow_creation(self) -> None:
        """Test basic workflow creation."""
        workflow = BatchWorkflow(name="test_workflow")

        assert workflow.name == "test_workflow"
        assert workflow.steps == []
        assert workflow.result.status == WorkflowStatus.PENDING

    def test_workflow_with_steps(self) -> None:
        """Test workflow with initial steps."""
        steps = [
            WorkflowStep(name="step1", action="echo"),
            WorkflowStep(name="step2", action="print"),
        ]
        workflow = BatchWorkflow(name="test", steps=steps)

        assert len(workflow.steps) == 2
        assert workflow.steps[0].name == "step1"

    def test_add_step(self) -> None:
        """Test adding steps to workflow."""
        workflow = BatchWorkflow(name="test")
        workflow.add_step(WorkflowStep(name="new_step", action="test"))

        assert len(workflow.steps) == 1
        assert workflow.steps[0].name == "new_step"

    def test_context_management(self) -> None:
        """Test context variable management."""
        workflow = BatchWorkflow(name="test")

        workflow.set_context("key1", "value1")
        workflow.set_context("key2", 42)

        assert workflow.get_context("key1") == "value1"
        assert workflow.get_context("key2") == 42
        assert workflow.get_context("nonexistent", "default") == "default"

    def test_register_action(self) -> None:
        """Test action registration."""
        workflow = BatchWorkflow(name="test")

        def echo_action(message: str) -> str:
            return f"Echo: {message}"

        workflow.register_action("echo", echo_action)

        assert "echo" in workflow._action_registry
        assert workflow._action_registry["echo"] == echo_action

    def test_execute_step_success(self) -> None:
        """Test successful step execution."""
        workflow = BatchWorkflow(name="test")

        def echo_action(message: str) -> str:
            return message

        workflow.register_action("echo", echo_action)
        workflow.set_context("message", "Hello")

        step = WorkflowStep(
            name="test_step",
            action="echo",
            params={"message": "World"},
        )

        result = workflow._execute_step(step)

        assert result["success"] is True
        assert result["result"] == "World"

    def test_execute_step_unknown_action(self) -> None:
        """Test step with unknown action."""
        workflow = BatchWorkflow(name="test")

        step = WorkflowStep(
            name="test_step",
            action="unknown_action",
        )

        result = workflow._execute_step(step)

        assert result["success"] is False
        assert "Unknown action" in result["error"]

    def test_execute_step_with_exception(self) -> None:
        """Test step that raises an exception."""
        workflow = BatchWorkflow(name="test")

        def failing_action(**kwargs: Any) -> None:
            raise ValueError("Test error")

        workflow.register_action("fail", failing_action)

        step = WorkflowStep(
            name="failing_step",
            action="fail",
        )

        result = workflow._execute_step(step)

        assert result["success"] is False
        assert "Test error" in result["error"]

    def test_execute_workflow_success(self) -> None:
        """Test successful workflow execution."""
        workflow = BatchWorkflow(name="test")

        def echo_action(message: str) -> str:
            return message

        workflow.register_action("echo", echo_action)
        workflow.add_step(WorkflowStep(name="step1", action="echo", params={"message": "Hello"}))
        workflow.add_step(WorkflowStep(name="step2", action="echo", params={"message": "World"}))

        result = workflow.execute()

        assert result.status == WorkflowStatus.COMPLETED
        assert len(result.results) == 2
        assert result.results[0]["success"] is True
        assert result.results[1]["success"] is True

    def test_execute_workflow_failure(self) -> None:
        """Test workflow execution with failure."""
        workflow = BatchWorkflow(name="test")

        def failing_action(**kwargs: Any) -> None:
            raise ValueError("Error")

        workflow.register_action("fail", failing_action)
        workflow.add_step(WorkflowStep(name="failing_step", action="fail"))

        result = workflow.execute()

        assert result.status == WorkflowStatus.FAILED
        assert len(result.errors) > 0

    def test_execute_with_retry(self) -> None:
        """Test workflow retry logic."""
        workflow = BatchWorkflow(name="test")

        call_count = [0]

        def flaky_action(**kwargs: Any) -> str:
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Temporary error")
            return "Success"

        workflow.register_action("flaky", flaky_action)
        workflow.add_step(WorkflowStep(
            name="flaky_step",
            action="flaky",
            max_retries=2,
        ))

        result = workflow.execute()

        assert result.status == WorkflowStatus.COMPLETED
        assert call_count[0] == 2

    def test_workflow_serialization(self) -> None:
        """Test workflow to_dict method."""
        workflow = BatchWorkflow(name="test")
        workflow.add_step(WorkflowStep(
            name="step1",
            action="echo",
            params={"message": "Hello"},
            timeout=60,
            max_retries=5,
        ))

        data = workflow.to_dict()

        assert data["name"] == "test"
        assert len(data["steps"]) == 1
        assert data["steps"][0]["name"] == "step1"
        assert data["steps"][0]["timeout"] == 60
        assert data["steps"][0]["max_retries"] == 5

    def test_workflow_from_dict(self) -> None:
        """Test workflow from_dict method."""
        data = {
            "name": "loaded_workflow",
            "steps": [
                {
                    "name": "step1",
                    "action": "echo",
                    "params": {"message": "Hello"},
                    "timeout": 120,
                    "max_retries": 2,
                },
            ],
        }

        workflow = BatchWorkflow.from_dict(data)

        assert workflow.name == "loaded_workflow"
        assert len(workflow.steps) == 1
        assert workflow.steps[0].name == "step1"
        assert workflow.steps[0].timeout == 120

    def test_workflow_save_and_load(self) -> None:
        """Test workflow file persistence."""
        workflow = BatchWorkflow(name="persistent_workflow")
        workflow.add_step(WorkflowStep(name="step1", action="test"))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            workflow.save(temp_path)

            loaded = BatchWorkflow.load(temp_path)

            assert loaded.name == "persistent_workflow"
            assert len(loaded.steps) == 1
            assert loaded.steps[0].name == "step1"
        finally:
            Path(temp_path).unlink()

    def test_workflow_context_merge(self) -> None:
        """Test context merging with step params."""
        workflow = BatchWorkflow(name="test")

        received_params: dict[str, Any] = {}

        def capture_action(**kwargs: Any) -> dict[str, Any]:
            received_params.update(kwargs)
            return kwargs

        workflow.register_action("capture", capture_action)
        workflow.set_context("global_key", "global_value")
        workflow.set_context("override_key", "original")

        workflow.add_step(WorkflowStep(
            name="test_step",
            action="capture",
            params={"override_key": "overridden", "local_key": "local_value"},
        ))

        workflow.execute()

        assert received_params["global_key"] == "global_value"
        assert received_params["override_key"] == "overridden"
        assert received_params["local_key"] == "local_value"


class TestWorkflowStatus:
    """Workflow status enum tests."""

    def test_status_values(self) -> None:
        """Test status enum values."""
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"
        assert WorkflowStatus.CANCELLED.value == "cancelled"


class TestIteration68AcceptanceCriteria:
    """Iteration #68 acceptance criteria tests."""

    def test_batch_workflow_module_exists(self) -> None:
        """Test batch workflow module exists."""
        from mc_agent_kit.workflow import batch_workflow
        assert hasattr(batch_workflow, "BatchWorkflow")
        assert hasattr(batch_workflow, "WorkflowStep")
        assert hasattr(batch_workflow, "WorkflowStatus")

    def test_workflow_creation(self) -> None:
        """Test workflow can be created and executed."""
        workflow = BatchWorkflow(name="acceptance_test")
        workflow.add_step(WorkflowStep(name="test", action="echo"))

        assert workflow.name == "acceptance_test"
        assert len(workflow.steps) == 1

    def test_workflow_serialization_roundtrip(self) -> None:
        """Test workflow serialization and deserialization."""
        original = BatchWorkflow(name="roundtrip")
        original.add_step(WorkflowStep(name="step1", action="test", params={"key": "value"}))

        data = original.to_dict()
        restored = BatchWorkflow.from_dict(data)

        assert restored.name == original.name
        assert len(restored.steps) == len(original.steps)
        assert restored.steps[0].name == original.steps[0].name

    def test_workflow_file_persistence(self) -> None:
        """Test workflow can be saved and loaded from file."""
        workflow = BatchWorkflow(name="file_test")
        workflow.add_step(WorkflowStep(name="step1", action="test"))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            workflow.save(temp_path)
            assert Path(temp_path).exists()

            with open(temp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert data["name"] == "file_test"
        finally:
            Path(temp_path).unlink()

    def test_action_registration_and_execution(self) -> None:
        """Test actions can be registered and executed."""
        workflow = BatchWorkflow(name="action_test")

        def test_action(value: int) -> int:
            return value * 2

        workflow.register_action("double", test_action)
        workflow.add_step(WorkflowStep(
            name="double_step",
            action="double",
            params={"value": 21},
        ))

        result = workflow.execute()

        assert result.status == WorkflowStatus.COMPLETED
        assert result.results[0]["result"] == 42

    def test_error_handling(self) -> None:
        """Test workflow handles errors gracefully."""
        workflow = BatchWorkflow(name="error_test")

        def failing_action(**kwargs: Any) -> None:
            raise RuntimeError("Expected error")

        workflow.register_action("fail", failing_action)
        workflow.add_step(WorkflowStep(name="failing", action="fail"))

        result = workflow.execute()

        assert result.status == WorkflowStatus.FAILED
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
