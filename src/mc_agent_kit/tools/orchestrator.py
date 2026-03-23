"""
Tool Orchestrator Module

工具编排引擎，支持多工具协同执行和工作流编排。
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from mc_agent_kit.tools.mcp_client import MCPClient, MCPToolResult
    from mc_agent_kit.tools.registry import ToolRegistry

__all__ = [
    "ToolOrchestrator",
    "ToolWorkflow",
    "WorkflowStep",
    "WorkflowResult",
    "StepResult",
    "ExecutionMode",
    "StepStatus",
    "create_tool_orchestrator",
    "create_workflow",
]


class ExecutionMode(Enum):
    """执行模式"""

    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    CONDITIONAL = "conditional"  # 条件执行


class StepStatus(Enum):
    """步骤状态"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """
    工作流步骤

    Attributes:
        name: 步骤名称
        tool_name: 工具名称
        input_mapping: 输入映射
        output_key: 输出键名
        condition: 执行条件
        retry_count: 重试次数
        timeout: 超时时间
        on_error: 错误处理策略
        status: 步骤状态
    """

    name: str
    tool_name: str
    input_mapping: dict[str, str] = field(default_factory=dict)
    output_key: str = ""
    condition: str | None = None
    retry_count: int = 0
    timeout: float = 30.0
    on_error: str = "fail"  # fail, skip, continue
    status: StepStatus = StepStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "tool_name": self.tool_name,
            "input_mapping": self.input_mapping,
            "output_key": self.output_key,
            "condition": self.condition,
            "retry_count": self.retry_count,
            "timeout": self.timeout,
            "on_error": self.on_error,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowStep:
        """从字典创建"""
        return cls(
            name=data["name"],
            tool_name=data["tool_name"],
            input_mapping=data.get("input_mapping", {}),
            output_key=data.get("output_key", ""),
            condition=data.get("condition"),
            retry_count=data.get("retry_count", 0),
            timeout=data.get("timeout", 30.0),
            on_error=data.get("on_error", "fail"),
            status=StepStatus(data.get("status", "pending")),
        )


@dataclass
class StepResult:
    """
    步骤执行结果

    Attributes:
        step_name: 步骤名称
        success: 是否成功
        result: 执行结果
        error: 错误信息
        execution_time: 执行时间
        status: 步骤状态
    """

    step_name: str
    success: bool
    result: Any = None
    error: str | None = None
    execution_time: float = 0.0
    status: StepStatus = StepStatus.SUCCESS

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "step_name": self.step_name,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "status": self.status.value,
        }


@dataclass
class WorkflowResult:
    """
    工作流执行结果

    Attributes:
        workflow_name: 工作流名称
        success: 是否成功
        results: 各步骤结果
        output: 最终输出
        total_time: 总执行时间
        error: 错误信息
    """

    workflow_name: str
    success: bool
    results: list[StepResult] = field(default_factory=list)
    output: dict[str, Any] = field(default_factory=dict)
    total_time: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "workflow_name": self.workflow_name,
            "success": self.success,
            "results": [r.to_dict() for r in self.results],
            "output": self.output,
            "total_time": self.total_time,
            "error": self.error,
        }

    def get_step_result(self, step_name: str) -> StepResult | None:
        """获取步骤结果"""
        for result in self.results:
            if result.step_name == step_name:
                return result
        return None


@dataclass
class ToolWorkflow:
    """
    工具工作流

    Attributes:
        name: 工作流名称
        description: 描述
        steps: 步骤列表
        execution_mode: 执行模式
        input_schema: 输入 Schema
        output_mapping: 输出映射
        variables: 变量定义
    """

    name: str
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_mapping: dict[str, str] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)

    def add_step(
        self,
        name: str,
        tool_name: str,
        input_mapping: dict[str, str] | None = None,
        output_key: str = "",
        condition: str | None = None,
        retry_count: int = 0,
        timeout: float = 30.0,
        on_error: str = "fail",
    ) -> WorkflowStep:
        """
        添加步骤

        Args:
            name: 步骤名称
            tool_name: 工具名称
            input_mapping: 输入映射
            output_key: 输出键名
            condition: 执行条件
            retry_count: 重试次数
            timeout: 超时时间
            on_error: 错误处理策略

        Returns:
            添加的步骤
        """
        step = WorkflowStep(
            name=name,
            tool_name=tool_name,
            input_mapping=input_mapping or {},
            output_key=output_key,
            condition=condition,
            retry_count=retry_count,
            timeout=timeout,
            on_error=on_error,
        )
        self.steps.append(step)
        return step

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "execution_mode": self.execution_mode.value,
            "input_schema": self.input_schema,
            "output_mapping": self.output_mapping,
            "variables": self.variables,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolWorkflow:
        """从字典创建"""
        workflow = cls(
            name=data["name"],
            description=data.get("description", ""),
            steps=[WorkflowStep.from_dict(s) for s in data.get("steps", [])],
            execution_mode=ExecutionMode(data.get("execution_mode", "sequential")),
            input_schema=data.get("input_schema", {}),
            output_mapping=data.get("output_mapping", {}),
            variables=data.get("variables", {}),
        )
        return workflow


class ToolOrchestrator:
    """
    工具编排器

    支持多工具协同执行和工作流编排。

    Example:
        >>> orchestrator = ToolOrchestrator(client)
        >>> workflow = orchestrator.create_workflow("my_workflow")
        >>> workflow.add_step("read", "read_file", {"path": "$input.file"}, "content")
        >>> workflow.add_step("parse", "parse_json", {"data": "$content"}, "result")
        >>> result = orchestrator.execute_workflow(workflow, {"file": "data.json"})
    """

    def __init__(self, client: MCPClient, registry: ToolRegistry | None = None):
        """
        初始化编排器

        Args:
            client: MCP 客户端
            registry: 工具注册中心（可选）
        """
        self._client = client
        self._registry = registry
        self._workflows: dict[str, ToolWorkflow] = {}
        self._workflow_history: list[WorkflowResult] = []

    @property
    def workflows(self) -> dict[str, ToolWorkflow]:
        """获取已注册的工作流"""
        return self._workflows.copy()

    def create_workflow(
        self,
        name: str,
        description: str = "",
        execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
    ) -> ToolWorkflow:
        """
        创建工作流

        Args:
            name: 工作流名称
            description: 描述
            execution_mode: 执行模式

        Returns:
            创建的工作流
        """
        workflow = ToolWorkflow(
            name=name,
            description=description,
            execution_mode=execution_mode,
        )
        self._workflows[name] = workflow
        return workflow

    def register_workflow(self, workflow: ToolWorkflow) -> bool:
        """
        注册工作流

        Args:
            workflow: 工作流

        Returns:
            是否注册成功
        """
        if workflow.name in self._workflows:
            return False
        self._workflows[workflow.name] = workflow
        return True

    def unregister_workflow(self, name: str) -> bool:
        """
        注销工作流

        Args:
            name: 工作流名称

        Returns:
            是否注销成功
        """
        if name not in self._workflows:
            return False
        del self._workflows[name]
        return True

    def get_workflow(self, name: str) -> ToolWorkflow | None:
        """
        获取工作流

        Args:
            name: 工作流名称

        Returns:
            工作流或 None
        """
        return self._workflows.get(name)

    def execute_workflow(
        self,
        workflow: ToolWorkflow | str,
        input_data: dict[str, Any],
        variables: dict[str, Any] | None = None,
    ) -> WorkflowResult:
        """
        执行工作流（同步）

        Args:
            workflow: 工作流或工作流名称
            input_data: 输入数据
            variables: 变量

        Returns:
            执行结果
        """
        # 获取工作流
        if isinstance(workflow, str):
            wf = self._workflows.get(workflow)
            if not wf:
                return WorkflowResult(
                    workflow_name=workflow,
                    success=False,
                    error=f"Workflow '{workflow}' not found",
                )
        else:
            wf = workflow

        start_time = time.time()
        context: dict[str, Any] = {
            "input": input_data,
            "variables": {**wf.variables, **(variables or {})},
            "steps": {},
        }

        results: list[StepResult] = []

        try:
            if wf.execution_mode == ExecutionMode.SEQUENTIAL:
                result = self._execute_sequential(wf, context)
                results = result.results
            elif wf.execution_mode == ExecutionMode.PARALLEL:
                result = self._execute_parallel(wf, context)
                results = result.results
            else:
                result = self._execute_conditional(wf, context)
                results = result.results

            # 构建最终输出
            output = self._build_output(context, wf.output_mapping)

            total_time = time.time() - start_time

            workflow_result = WorkflowResult(
                workflow_name=wf.name,
                success=all(r.success for r in results),
                results=results,
                output=output,
                total_time=total_time,
            )

        except Exception as e:
            total_time = time.time() - start_time
            workflow_result = WorkflowResult(
                workflow_name=wf.name,
                success=False,
                results=results,
                error=str(e),
                total_time=total_time,
            )

        self._workflow_history.append(workflow_result)
        return workflow_result

    async def execute_workflow_async(
        self,
        workflow: ToolWorkflow | str,
        input_data: dict[str, Any],
        variables: dict[str, Any] | None = None,
    ) -> WorkflowResult:
        """
        执行工作流（异步）

        Args:
            workflow: 工作流或工作流名称
            input_data: 输入数据
            variables: 变量

        Returns:
            执行结果
        """
        # 获取工作流
        if isinstance(workflow, str):
            wf = self._workflows.get(workflow)
            if not wf:
                return WorkflowResult(
                    workflow_name=workflow,
                    success=False,
                    error=f"Workflow '{workflow}' not found",
                )
        else:
            wf = workflow

        start_time = time.time()
        context: dict[str, Any] = {
            "input": input_data,
            "variables": {**wf.variables, **(variables or {})},
            "steps": {},
        }

        results: list[StepResult] = []

        try:
            if wf.execution_mode == ExecutionMode.SEQUENTIAL:
                result = await self._execute_sequential_async(wf, context)
                results = result.results
            elif wf.execution_mode == ExecutionMode.PARALLEL:
                result = await self._execute_parallel_async(wf, context)
                results = result.results
            else:
                result = await self._execute_conditional_async(wf, context)
                results = result.results

            output = self._build_output(context, wf.output_mapping)
            total_time = time.time() - start_time

            workflow_result = WorkflowResult(
                workflow_name=wf.name,
                success=all(r.success for r in results),
                results=results,
                output=output,
                total_time=total_time,
            )

        except Exception as e:
            total_time = time.time() - start_time
            workflow_result = WorkflowResult(
                workflow_name=wf.name,
                success=False,
                results=results,
                error=str(e),
                total_time=total_time,
            )

        self._workflow_history.append(workflow_result)
        return workflow_result

    def _execute_sequential(
        self,
        workflow: ToolWorkflow,
        context: dict[str, Any],
    ) -> WorkflowResult:
        """顺序执行步骤"""
        results = []

        for step in workflow.steps:
            result = self._execute_step(step, context)
            results.append(result)

            if not result.success and step.on_error == "fail":
                break

        return WorkflowResult(
            workflow_name=workflow.name,
            success=all(r.success for r in results),
            results=results,
        )

    async def _execute_sequential_async(
        self,
        workflow: ToolWorkflow,
        context: dict[str, Any],
    ) -> WorkflowResult:
        """顺序执行步骤（异步）"""
        results = []

        for step in workflow.steps:
            result = await self._execute_step_async(step, context)
            results.append(result)

            if not result.success and step.on_error == "fail":
                break

        return WorkflowResult(
            workflow_name=workflow.name,
            success=all(r.success for r in results),
            results=results,
        )

    def _execute_parallel(
        self,
        workflow: ToolWorkflow,
        context: dict[str, Any],
    ) -> WorkflowResult:
        """并行执行步骤"""
        results = []

        for step in workflow.steps:
            result = self._execute_step(step, context)
            results.append(result)

        return WorkflowResult(
            workflow_name=workflow.name,
            success=all(r.success for r in results),
            results=results,
        )

    async def _execute_parallel_async(
        self,
        workflow: ToolWorkflow,
        context: dict[str, Any],
    ) -> WorkflowResult:
        """并行执行步骤（异步）"""
        tasks = [
            self._execute_step_async(step, context)
            for step in workflow.steps
        ]
        results = await asyncio.gather(*tasks)

        return WorkflowResult(
            workflow_name=workflow.name,
            success=all(r.success for r in results),
            results=list(results),
        )

    def _execute_conditional(
        self,
        workflow: ToolWorkflow,
        context: dict[str, Any],
    ) -> WorkflowResult:
        """条件执行步骤"""
        results = []

        for step in workflow.steps:
            # 检查条件
            if step.condition and not self._evaluate_condition(step.condition, context):
                results.append(StepResult(
                    step_name=step.name,
                    success=True,
                    status=StepStatus.SKIPPED,
                ))
                continue

            result = self._execute_step(step, context)
            results.append(result)

            if not result.success and step.on_error == "fail":
                break

        return WorkflowResult(
            workflow_name=workflow.name,
            success=all(r.success for r in results),
            results=results,
        )

    async def _execute_conditional_async(
        self,
        workflow: ToolWorkflow,
        context: dict[str, Any],
    ) -> WorkflowResult:
        """条件执行步骤（异步）"""
        results = []

        for step in workflow.steps:
            if step.condition and not self._evaluate_condition(step.condition, context):
                results.append(StepResult(
                    step_name=step.name,
                    success=True,
                    status=StepStatus.SKIPPED,
                ))
                continue

            result = await self._execute_step_async(step, context)
            results.append(result)

            if not result.success and step.on_error == "fail":
                break

        return WorkflowResult(
            workflow_name=workflow.name,
            success=all(r.success for r in results),
            results=results,
        )

    def _execute_step(
        self,
        step: WorkflowStep,
        context: dict[str, Any],
    ) -> StepResult:
        """执行单个步骤"""
        start_time = time.time()
        step.status = StepStatus.RUNNING

        try:
            # 解析输入
            args = self._resolve_input(step.input_mapping, context)

            # 调用工具
            result = self._client.call_tool(step.tool_name, args)

            execution_time = time.time() - start_time

            if result.success:
                step.status = StepStatus.SUCCESS

                # 保存输出
                if step.output_key:
                    context["steps"][step.name] = result.result

                return StepResult(
                    step_name=step.name,
                    success=True,
                    result=result.result,
                    execution_time=execution_time,
                    status=StepStatus.SUCCESS,
                )
            else:
                step.status = StepStatus.FAILED
                return StepResult(
                    step_name=step.name,
                    success=False,
                    error=result.error,
                    execution_time=execution_time,
                    status=StepStatus.FAILED,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            step.status = StepStatus.FAILED
            return StepResult(
                step_name=step.name,
                success=False,
                error=str(e),
                execution_time=execution_time,
                status=StepStatus.FAILED,
            )

    async def _execute_step_async(
        self,
        step: WorkflowStep,
        context: dict[str, Any],
    ) -> StepResult:
        """执行单个步骤（异步）"""
        start_time = time.time()
        step.status = StepStatus.RUNNING

        try:
            args = self._resolve_input(step.input_mapping, context)
            result = await self._client.call_tool_async(step.tool_name, args)

            execution_time = time.time() - start_time

            if result.success:
                step.status = StepStatus.SUCCESS
                if step.output_key:
                    context["steps"][step.name] = result.result

                return StepResult(
                    step_name=step.name,
                    success=True,
                    result=result.result,
                    execution_time=execution_time,
                    status=StepStatus.SUCCESS,
                )
            else:
                step.status = StepStatus.FAILED
                return StepResult(
                    step_name=step.name,
                    success=False,
                    error=result.error,
                    execution_time=execution_time,
                    status=StepStatus.FAILED,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            step.status = StepStatus.FAILED
            return StepResult(
                step_name=step.name,
                success=False,
                error=str(e),
                execution_time=execution_time,
                status=StepStatus.FAILED,
            )

    def _resolve_input(
        self,
        mapping: dict[str, str],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """解析输入映射"""
        result = {}

        for key, value_expr in mapping.items():
            result[key] = self._resolve_value(value_expr, context)

        return result

    def _resolve_value(self, expr: str, context: dict[str, Any]) -> Any:
        """解析值表达式"""
        if not expr.startswith("$"):
            return expr

        # 解析路径表达式
        path = expr[1:].split(".")
        value = context

        for part in path:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

        return value

    def _evaluate_condition(self, condition: str, context: dict[str, Any]) -> bool:
        """评估条件表达式"""
        # 简单条件评估
        # 支持: $step.success, $input.field == value, etc.
        try:
            # 解析条件中的变量引用
            if "$" in condition:
                for key in ["input", "steps", "variables"]:
                    pattern = f"${key}."
                    if pattern in condition:
                        # 提取变量路径
                        start = condition.find(pattern)
                        end = condition.find(" ", start) if " " in condition[start:] else len(condition)
                        var_expr = condition[start:end]
                        value = self._resolve_value(var_expr, context)

                        # 替换条件中的变量
                        condition = condition.replace(var_expr, repr(value))

            # 评估条件
            return bool(eval(condition))  # noqa: S307
        except Exception:
            return False

    def _build_output(
        self,
        context: dict[str, Any],
        output_mapping: dict[str, str],
    ) -> dict[str, Any]:
        """构建输出"""
        if not output_mapping:
            return context.get("steps", {})

        output = {}
        for key, expr in output_mapping.items():
            output[key] = self._resolve_value(expr, context)

        return output

    def parallel_execute(
        self,
        tool_names: list[str],
        args_list: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        并行执行多个工具

        Args:
            tool_names: 工具名称列表
            args_list: 参数列表

        Returns:
            执行结果字典
        """
        results = {}

        for name, args in zip(tool_names, args_list):
            result = self._client.call_tool(name, args)
            results[name] = result

        return results

    async def parallel_execute_async(
        self,
        tool_names: list[str],
        args_list: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        并行执行多个工具（异步）

        Args:
            tool_names: 工具名称列表
            args_list: 参数列表

        Returns:
            执行结果字典
        """
        tasks = [
            self._client.call_tool_async(name, args)
            for name, args in zip(tool_names, args_list)
        ]
        results_list = await asyncio.gather(*tasks)

        return dict(zip(tool_names, results_list))

    def get_history(self, limit: int = 10) -> list[WorkflowResult]:
        """
        获取执行历史

        Args:
            limit: 最大数量

        Returns:
            执行历史列表
        """
        return self._workflow_history[-limit:]


def create_tool_orchestrator(
    client: MCPClient,
    registry: ToolRegistry | None = None,
) -> ToolOrchestrator:
    """
    创建工具编排器

    Args:
        client: MCP 客户端
        registry: 工具注册中心

    Returns:
        工具编排器实例
    """
    return ToolOrchestrator(client, registry)


def create_workflow(
    name: str,
    description: str = "",
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
) -> ToolWorkflow:
    """
    创建工作流

    Args:
        name: 工作流名称
        description: 描述
        execution_mode: 执行模式

    Returns:
        工作流实例
    """
    return ToolWorkflow(
        name=name,
        description=description,
        execution_mode=execution_mode,
    )