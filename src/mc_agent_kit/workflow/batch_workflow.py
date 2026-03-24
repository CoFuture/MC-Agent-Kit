"""Batch workflow automation for MC-Agent-Kit."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    name: str
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    timeout: int = 300
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_name: str
    status: WorkflowStatus
    start_time: float | None = None
    end_time: float | None = None
    results: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def duration(self) -> float:
        """Get workflow duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "results": self.results,
            "errors": self.errors,
        }


class BatchWorkflow:
    """Batch workflow executor for automation."""

    def __init__(self, name: str, steps: list[WorkflowStep] | None = None):
        """Initialize the workflow.

        Args:
            name: Workflow name.
            steps: Optional list of workflow steps.
        """
        self.name = name
        self.steps = steps or []
        self.result = WorkflowResult(workflow_name=name, status=WorkflowStatus.PENDING)
        self._context: dict[str, Any] = {}
        self._action_registry: dict[str, Callable] = {}

    def register_action(self, name: str, action: Callable) -> None:
        """Register an action handler.

        Args:
            name: Action name.
            action: Action handler function.
        """
        self._action_registry[name] = action

    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow.

        Args:
            step: Workflow step to add.
        """
        self.steps.append(step)

    def set_context(self, key: str, value: Any) -> None:
        """Set a context variable.

        Args:
            key: Variable name.
            value: Variable value.
        """
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context variable.

        Args:
            key: Variable name.
            default: Default value if not found.

        Returns:
            Context variable value.
        """
        return self._context.get(key, default)

    def _execute_step(self, step: WorkflowStep) -> dict[str, Any]:
        """Execute a single workflow step.

        Args:
            step: Step to execute.

        Returns:
            Step result.
        """
        action_name = step.action
        handler = self._action_registry.get(action_name)

        if not handler:
            return {
                "step": step.name,
                "success": False,
                "error": f"Unknown action: {action_name}",
            }

        try:
            # Merge context with step params
            params = {**self._context, **step.params}
            result = handler(**params)
            return {
                "step": step.name,
                "success": True,
                "result": result,
            }
        except Exception as e:
            return {
                "step": step.name,
                "success": False,
                "error": str(e),
            }

    def execute(self) -> WorkflowResult:
        """Execute the workflow.

        Returns:
            Workflow result.
        """
        self.result = WorkflowResult(
            workflow_name=self.name,
            status=WorkflowStatus.RUNNING,
            start_time=time.time(),
        )

        for i, step in enumerate(self.steps):
            step_result = self._execute_step(step)
            self.result.results.append(step_result)

            if not step_result["success"]:
                # Retry logic
                if step.retry_count < step.max_retries:
                    step.retry_count += 1
                    self.result.results.append({
                        "step": f"{step.name} (retry {step.retry_count})",
                        "message": "Retrying...",
                    })
                    step_result = self._execute_step(step)
                    self.result.results[-1] = step_result

                if not step_result["success"]:
                    error_msg = step_result.get("error", "Unknown error")
                    self.result.errors.append(f"Step {step.name} failed: {error_msg}")
                    self.result.status = WorkflowStatus.FAILED
                    break

        if self.result.status != WorkflowStatus.FAILED:
            self.result.status = WorkflowStatus.COMPLETED

        self.result.end_time = time.time()
        return self.result

    def to_dict(self) -> dict[str, Any]:
        """Convert workflow to dictionary.

        Returns:
            Workflow configuration as dict.
        """
        return {
            "name": self.name,
            "steps": [
                {
                    "name": step.name,
                    "action": step.action,
                    "params": step.params,
                    "timeout": step.timeout,
                    "max_retries": step.max_retries,
                }
                for step in self.steps
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BatchWorkflow:
        """Create workflow from dictionary.

        Args:
            data: Workflow configuration.

        Returns:
            BatchWorkflow instance.
        """
        workflow = cls(name=data["name"])
        for step_data in data.get("steps", []):
            step = WorkflowStep(
                name=step_data["name"],
                action=step_data["action"],
                params=step_data.get("params", {}),
                timeout=step_data.get("timeout", 300),
                max_retries=step_data.get("max_retries", 3),
            )
            workflow.add_step(step)
        return workflow

    def save(self, path: str | Path) -> None:
        """Save workflow to file.

        Args:
            path: File path.
        """
        path = Path(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> BatchWorkflow:
        """Load workflow from file.

        Args:
            path: File path.

        Returns:
            BatchWorkflow instance.
        """
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
