"""
工作流编排引擎模块

提供工作流编排、条件分支、并行执行、模板和可视化功能。
"""

from __future__ import annotations

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class StepType(Enum):
    """步骤类型"""
    TASK = "task"           # 普通任务
    PARALLEL = "parallel"   # 并行任务组
    CONDITION = "condition" # 条件分支
    LOOP = "loop"           # 循环任务


class BranchCondition(Enum):
    """分支条件"""
    SUCCESS = "success"     # 上一步成功时执行
    FAILURE = "failure"     # 上一步失败时执行
    ALWAYS = "always"       # 总是执行
    CUSTOM = "custom"       # 自定义条件


@dataclass
class WorkflowTemplate:
    """工作流模板"""
    id: str
    name: str
    description: str
    steps: list[dict[str, Any]]
    variables: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "variables": self.variables,
            "tags": self.tags,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowTemplate":
        """从字典创建"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            steps=data.get("steps", []),
            variables=data.get("variables", {}),
            tags=data.get("tags", []),
            version=data.get("version", "1.0.0"),
        )


@dataclass
class WorkflowStepConfig:
    """工作流步骤配置"""
    id: str
    name: str
    step_type: StepType = StepType.TASK
    action: Callable[[dict[str, Any]], Any] | None = None
    condition: BranchCondition = BranchCondition.SUCCESS
    custom_condition: Callable[[dict[str, Any]], bool] | None = None
    parallel_steps: list["WorkflowStepConfig"] = field(default_factory=list)
    loop_items: list[Any] = field(default_factory=list)
    loop_variable: str = "item"
    max_retries: int = 0
    timeout_seconds: float = 300.0
    on_failure: str = "stop"  # stop, continue, skip
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StepResult:
    """步骤执行结果"""
    step_id: str
    step_name: str
    success: bool
    output: Any = None
    error: str | None = None
    duration_seconds: float = 0.0
    retry_count: int = 0
    skipped: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "success": self.success,
            "output": str(self.output) if self.output else None,
            "error": self.error,
            "duration_seconds": round(self.duration_seconds, 3),
            "retry_count": self.retry_count,
            "skipped": self.skipped,
            "metadata": self.metadata,
        }


@dataclass
class WorkflowExecutionResult:
    """工作流执行结果"""
    workflow_id: str
    workflow_name: str
    success: bool
    step_results: list[StepResult]
    total_duration_seconds: float
    variables: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "success": self.success,
            "step_results": [r.to_dict() for r in self.step_results],
            "total_duration_seconds": round(self.total_duration_seconds, 3),
            "variables": self.variables,
            "error": self.error,
        }


@dataclass
class WorkflowVisualization:
    """工作流可视化"""
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    layout: str = "dagre"  # dagre, hierarchical, force

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "layout": self.layout,
        }

    def to_mermaid(self) -> str:
        """生成 Mermaid 图表代码"""
        lines = ["graph TD"]
        for node in self.nodes:
            node_id = node.get("id", "")
            node_label = node.get("label", node_id)
            node_type = node.get("type", "task")
            shape = {"task": "[]", "parallel": "[[]]", "condition": "{}", "loop": "(())"}.get(node_type, "[]")
            lines.append(f"    {node_id}{shape[0]}{node_label}{shape[1]}")
        for edge in self.edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            label = edge.get("label", "")
            if label:
                lines.append(f"    {source} -->|{label}| {target}")
            else:
                lines.append(f"    {source} --> {target}")
        return "\n".join(lines)


class WorkflowOrchestrator:
    """
    工作流编排引擎

    支持:
    - 串行/并行/条件分支/循环任务
    - 重试和超时
    - 工作流模板
    - 可视化生成

    使用示例:
        orchestrator = WorkflowOrchestrator()
        
        # 定义步骤
        steps = [
            WorkflowStepConfig(id="step1", name="搜索文档", action=lambda ctx: {"result": "found"}),
            WorkflowStepConfig(id="step2", name="创建项目", action=lambda ctx: {"created": True}),
        ]
        
        # 执行工作流
        result = orchestrator.execute("my_workflow", steps)
        print(result.success)
    """

    def __init__(
        self,
        max_workers: int = 4,
        default_timeout: float = 300.0,
        on_step_complete: Callable[[StepResult], None] | None = None,
    ):
        self.max_workers = max_workers
        self.default_timeout = default_timeout
        self.on_step_complete = on_step_complete
        self._templates: dict[str, WorkflowTemplate] = {}
        self._results: dict[str, WorkflowExecutionResult] = {}
        self._lock = threading.Lock()

        # 注册内置模板
        self._register_builtin_templates()

    def _register_builtin_templates(self) -> None:
        """注册内置工作流模板"""
        # 开发闭环模板
        self.register_template(WorkflowTemplate(
            id="dev_cycle",
            name="开发闭环",
            description="查文档 → 创建项目 → 启动测试 → 诊断错误 → 修复",
            steps=[
                {"id": "search", "name": "搜索文档", "type": "task"},
                {"id": "create", "name": "创建项目", "type": "task", "depends_on": ["search"]},
                {"id": "launch", "name": "启动测试", "type": "task", "depends_on": ["create"]},
                {"id": "diagnose", "name": "诊断错误", "type": "condition", "condition": "has_errors"},
                {"id": "fix", "name": "修复问题", "type": "task", "depends_on": ["diagnose"]},
            ],
            tags=["development", "mvp"],
        ))

        # 项目创建模板
        self.register_template(WorkflowTemplate(
            id="project_create",
            name="项目创建",
            description="创建新的 ModSDK 项目",
            steps=[
                {"id": "init", "name": "初始化项目", "type": "task"},
                {"id": "bp", "name": "创建行为包", "type": "task", "depends_on": ["init"]},
                {"id": "rp", "name": "创建资源包", "type": "task", "depends_on": ["init"]},
                {"id": "config", "name": "生成配置", "type": "task", "depends_on": ["bp", "rp"]},
            ],
            tags=["project", "scaffold"],
        ))

        # 实体开发模板
        self.register_template(WorkflowTemplate(
            id="entity_dev",
            name="实体开发",
            description="创建自定义实体",
            steps=[
                {"id": "search_api", "name": "搜索 API", "type": "task"},
                {"id": "create_entity", "name": "创建实体文件", "type": "task", "depends_on": ["search_api"]},
                {"id": "create_behavior", "name": "创建行为文件", "type": "task", "depends_on": ["search_api"]},
                {"id": "create_texture", "name": "创建纹理", "type": "task", "depends_on": ["create_entity"]},
                {"id": "register", "name": "注册实体", "type": "task", "depends_on": ["create_behavior", "create_texture"]},
            ],
            tags=["entity", "development"],
        ))

        # 批量测试模板
        self.register_template(WorkflowTemplate(
            id="batch_test",
            name="批量测试",
            description="并行执行多个测试",
            steps=[
                {"id": "tests", "name": "测试组", "type": "parallel", "steps": [
                    {"id": "test1", "name": "测试1", "type": "task"},
                    {"id": "test2", "name": "测试2", "type": "task"},
                    {"id": "test3", "name": "测试3", "type": "task"},
                ]},
                {"id": "report", "name": "生成报告", "type": "task", "depends_on": ["tests"]},
            ],
            tags=["test", "batch"],
        ))

    def register_template(self, template: WorkflowTemplate) -> None:
        """注册工作流模板"""
        with self._lock:
            self._templates[template.id] = template

    def get_template(self, template_id: str) -> WorkflowTemplate | None:
        """获取工作流模板"""
        return self._templates.get(template_id)

    def list_templates(self, tag: str | None = None) -> list[WorkflowTemplate]:
        """列出所有模板"""
        templates = list(self._templates.values())
        if tag:
            templates = [t for t in templates if tag in t.tags]
        return templates

    def execute(
        self,
        workflow_name: str,
        steps: list[WorkflowStepConfig],
        variables: dict[str, Any] | None = None,
        max_workers: int | None = None,
    ) -> WorkflowExecutionResult:
        """
        执行工作流

        Args:
            workflow_name: 工作流名称
            steps: 步骤配置列表
            variables: 初始变量
            max_workers: 并行执行的最大工作线程数

        Returns:
            WorkflowExecutionResult: 执行结果
        """
        workflow_id = str(uuid.uuid4())
        start_time = time.time()
        context = {"variables": variables or {}, "results": {}}
        step_results: list[StepResult] = []
        success = True
        error = None

        try:
            # 构建执行顺序
            execution_order = self._build_execution_order(steps)
            
            # 执行步骤
            for step_config in execution_order:
                # 检查是否应该执行
                if not self._should_execute(step_config, context):
                    result = StepResult(
                        step_id=step_config.id,
                        step_name=step_config.name,
                        success=True,
                        skipped=True,
                        metadata={"reason": "condition_not_met"},
                    )
                    step_results.append(result)
                    continue

                # 执行步骤
                result = self._execute_step(step_config, context, max_workers)
                step_results.append(result)

                # 回调
                if self.on_step_complete:
                    self.on_step_complete(result)

                # 更新上下文
                context["results"][step_config.id] = result

                # 处理失败
                if not result.success and not result.skipped:
                    if step_config.on_failure == "stop":
                        success = False
                        error = result.error
                        break
                    elif step_config.on_failure == "skip":
                        continue

        except Exception as e:
            success = False
            error = str(e)

        total_duration = time.time() - start_time
        result = WorkflowExecutionResult(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            success=success,
            step_results=step_results,
            total_duration_seconds=total_duration,
            variables=context.get("variables", {}),
            error=error,
        )

        with self._lock:
            self._results[workflow_id] = result

        return result

    def execute_template(
        self,
        template_id: str,
        variables: dict[str, Any] | None = None,
        action_map: dict[str, Callable[[dict[str, Any]], Any]] | None = None,
    ) -> WorkflowExecutionResult:
        """
        从模板执行工作流

        Args:
            template_id: 模板 ID
            variables: 变量
            action_map: 步骤 ID 到动作的映射

        Returns:
            WorkflowExecutionResult: 执行结果
        """
        template = self.get_template(template_id)
        if not template:
            return WorkflowExecutionResult(
                workflow_id=str(uuid.uuid4()),
                workflow_name="",
                success=False,
                step_results=[],
                total_duration_seconds=0,
                error=f"Template not found: {template_id}",
            )

        # 将模板步骤转换为配置
        steps = self._convert_template_steps(template.steps, action_map or {})
        return self.execute(template.name, steps, variables)

    def _convert_template_steps(
        self,
        template_steps: list[dict[str, Any]],
        action_map: dict[str, Callable[[dict[str, Any]], Any]],
    ) -> list[WorkflowStepConfig]:
        """将模板步骤转换为配置"""
        steps = []
        for ts in template_steps:
            step_type = StepType(ts.get("type", "task"))
            step = WorkflowStepConfig(
                id=ts.get("id", ""),
                name=ts.get("name", ""),
                step_type=step_type,
                action=action_map.get(ts.get("id", "")),
                metadata={"depends_on": ts.get("depends_on", [])},
            )
            
            # 处理并行步骤
            if step_type == StepType.PARALLEL and "steps" in ts:
                step.parallel_steps = self._convert_template_steps(ts["steps"], action_map)
            
            # 处理循环
            if step_type == StepType.LOOP:
                step.loop_items = ts.get("items", [])
                step.loop_variable = ts.get("variable", "item")
            
            steps.append(step)
        return steps

    def _build_execution_order(self, steps: list[WorkflowStepConfig]) -> list[WorkflowStepConfig]:
        """构建执行顺序（拓扑排序）"""
        # 简单实现：按顺序执行，考虑依赖关系
        # 更复杂的实现需要拓扑排序
        return steps

    def _should_execute(self, step: WorkflowStepConfig, context: dict[str, Any]) -> bool:
        """判断步骤是否应该执行"""
        if step.condition == BranchCondition.ALWAYS:
            return True
        if step.condition == BranchCondition.CUSTOM and step.custom_condition:
            return step.custom_condition(context)
        
        # 检查依赖
        depends_on = step.metadata.get("depends_on", [])
        for dep_id in depends_on:
            dep_result = context.get("results", {}).get(dep_id)
            if dep_result and not dep_result.success:
                if step.condition == BranchCondition.SUCCESS:
                    return False
                elif step.condition == BranchCondition.FAILURE:
                    return True
        
        return True

    def _execute_step(
        self,
        step: WorkflowStepConfig,
        context: dict[str, Any],
        max_workers: int | None = None,
    ) -> StepResult:
        """执行单个步骤"""
        start_time = time.time()
        
        if step.step_type == StepType.PARALLEL:
            return self._execute_parallel(step, context, max_workers)
        elif step.step_type == StepType.LOOP:
            return self._execute_loop(step, context)
        else:
            return self._execute_task(step, context)

    def _execute_task(self, step: WorkflowStepConfig, context: dict[str, Any]) -> StepResult:
        """执行普通任务"""
        start_time = time.time()
        retry_count = 0
        last_error = None

        for attempt in range(step.max_retries + 1):
            try:
                if step.action:
                    output = step.action(context)
                else:
                    output = None
                
                return StepResult(
                    step_id=step.id,
                    step_name=step.name,
                    success=True,
                    output=output,
                    duration_seconds=time.time() - start_time,
                    retry_count=retry_count,
                )
            except Exception as e:
                last_error = str(e)
                retry_count = attempt + 1
                if attempt < step.max_retries:
                    time.sleep(1)  # 简单重试延迟

        return StepResult(
            step_id=step.id,
            step_name=step.name,
            success=False,
            error=last_error,
            duration_seconds=time.time() - start_time,
            retry_count=retry_count,
        )

    def _execute_parallel(
        self,
        step: WorkflowStepConfig,
        context: dict[str, Any],
        max_workers: int | None = None,
    ) -> StepResult:
        """执行并行任务"""
        start_time = time.time()
        workers = max_workers or self.max_workers
        results: list[StepResult] = []
        success = True

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._execute_task, ps, context): ps
                for ps in step.parallel_steps
            }
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                if not result.success:
                    success = False

        return StepResult(
            step_id=step.id,
            step_name=step.name,
            success=success,
            output={"parallel_results": [r.to_dict() for r in results]},
            duration_seconds=time.time() - start_time,
            metadata={"parallel_count": len(step.parallel_steps)},
        )

    def _execute_loop(self, step: WorkflowStepConfig, context: dict[str, Any]) -> StepResult:
        """执行循环任务"""
        start_time = time.time()
        results: list[StepResult] = []
        success = True

        for item in step.loop_items:
            loop_context = {**context, step.loop_variable: item}
            result = self._execute_task(step, loop_context)
            results.append(result)
            if not result.success:
                success = False
                break

        return StepResult(
            step_id=step.id,
            step_name=step.name,
            success=success,
            output={"loop_results": [r.to_dict() for r in results]},
            duration_seconds=time.time() - start_time,
            metadata={"loop_count": len(step.loop_items)},
        )

    def visualize(self, steps: list[WorkflowStepConfig]) -> WorkflowVisualization:
        """生成工作流可视化"""
        nodes = []
        edges = []

        def process_step(step: WorkflowStepConfig, parent_id: str | None = None) -> None:
            node = {
                "id": step.id,
                "label": step.name,
                "type": step.step_type.value,
                "metadata": step.metadata,
            }
            nodes.append(node)

            if parent_id:
                edges.append({
                    "source": parent_id,
                    "target": step.id,
                    "label": "",
                })

            # 处理并行步骤
            for ps in step.parallel_steps:
                process_step(ps, step.id)

        for step in steps:
            process_step(step)

            # 处理依赖关系
            depends_on = step.metadata.get("depends_on", [])
            for dep_id in depends_on:
                edges.append({
                    "source": dep_id,
                    "target": step.id,
                    "label": "depends_on",
                })

        return WorkflowVisualization(nodes=nodes, edges=edges)

    def visualize_template(self, template_id: str) -> WorkflowVisualization | None:
        """可视化模板"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        steps = self._convert_template_steps(template.steps, {})
        return self.visualize(steps)

    def get_result(self, workflow_id: str) -> WorkflowExecutionResult | None:
        """获取执行结果"""
        return self._results.get(workflow_id)

    def save_workflow(self, steps: list[WorkflowStepConfig], name: str, description: str = "") -> WorkflowTemplate:
        """保存工作流为模板"""
        template = WorkflowTemplate(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            steps=[self._step_to_dict(s) for s in steps],
        )
        self.register_template(template)
        return template

    def _step_to_dict(self, step: WorkflowStepConfig) -> dict[str, Any]:
        """将步骤转换为字典"""
        return {
            "id": step.id,
            "name": step.name,
            "type": step.step_type.value,
            "max_retries": step.max_retries,
            "timeout_seconds": step.timeout_seconds,
            "on_failure": step.on_failure,
            "depends_on": step.metadata.get("depends_on", []),
            "steps": [self._step_to_dict(s) for s in step.parallel_steps],
            "loop_items": step.loop_items,
            "loop_variable": step.loop_variable,
        }


# 便捷函数
def create_orchestrator(
    max_workers: int = 4,
    on_step_complete: Callable[[StepResult], None] | None = None,
) -> WorkflowOrchestrator:
    """创建工作流编排器"""
    return WorkflowOrchestrator(max_workers=max_workers, on_step_complete=on_step_complete)


def execute_workflow(
    name: str,
    steps: list[WorkflowStepConfig],
    variables: dict[str, Any] | None = None,
) -> WorkflowExecutionResult:
    """便捷执行工作流"""
    orchestrator = WorkflowOrchestrator()
    return orchestrator.execute(name, steps, variables)