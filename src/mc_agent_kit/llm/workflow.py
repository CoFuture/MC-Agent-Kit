"""
智能工作流模块

提供端到端的开发工作流自动化能力。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from .base import ChatMessage, CompletionResult, LLMConfig
from .code_generation import CodeGenerationType, GeneratedCode, GenerationContext, IntelligentCodeGenerator
from .code_review import IntelligentCodeReviewer, ReviewResult
from .intelligent_fix import DiagnosisResult, ErrorContext, IntelligentFixer
from .manager import LLMManager


class WorkflowStepType(Enum):
    """工作流步骤类型"""
    ANALYZE = "analyze"           # 需求分析
    DESIGN = "design"             # 方案设计
    GENERATE = "generate"         # 代码生成
    REVIEW = "review"             # 代码审查
    FIX = "fix"                   # 修复错误
    TEST = "test"                 # 测试验证
    ITERATE = "iterate"           # 迭代优化


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """工作流步骤"""
    step_type: WorkflowStepType
    name: str = ""
    description: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    error: str | None = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_type": self.step_type.value,
            "name": self.name,
            "description": self.description,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "status": self.status.value,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


@dataclass
class WorkflowContext:
    """工作流上下文"""
    workflow_id: str = ""
    project_name: str = ""
    module_name: str = ""
    target: str = "server"
    max_iterations: int = 3
    min_review_score: float = 70.0
    variables: dict[str, Any] = field(default_factory=dict)
    history: list[WorkflowStep] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "project_name": self.project_name,
            "module_name": self.module_name,
            "target": self.target,
            "max_iterations": self.max_iterations,
            "min_review_score": self.min_review_score,
            "variables": self.variables,
            "history": [s.to_dict() for s in self.history],
        }


@dataclass
class WorkflowResult:
    """工作流结果"""
    success: bool
    status: WorkflowStatus
    steps: list[WorkflowStep] = field(default_factory=list)
    generated_code: GeneratedCode | None = None
    review_result: ReviewResult | None = None
    diagnosis_result: DiagnosisResult | None = None
    iterations: int = 0
    total_duration_ms: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "generated_code": self.generated_code.to_dict() if self.generated_code else None,
            "review_result": self.review_result.to_dict() if self.review_result else None,
            "diagnosis_result": self.diagnosis_result.to_dict() if self.diagnosis_result else None,
            "iterations": self.iterations,
            "total_duration_ms": self.total_duration_ms,
            "error": self.error,
        }


class RequirementAnalyzer:
    """
    需求分析器

    分析用户需求，提取关键信息。
    """

    def __init__(self, llm_config: LLMConfig | None = None) -> None:
        self.llm_config = llm_config or LLMConfig(provider="mock")
        self.llm_manager = LLMManager()

    def analyze(self, requirement: str) -> dict[str, Any]:
        """
        分析需求

        Args:
            requirement: 用户需求描述

        Returns:
            dict: 分析结果，包含：
                - entities: 涉及的实体
                - events: 涉及的事件
                - apis: 涉及的 API
                - target: 运行环境
                - complexity: 复杂度评估
                - suggestions: 实现建议
        """
        system_prompt = '''你是一个 Minecraft ModSDK 需求分析专家。
分析用户需求，提取以下信息：
1. 涉及的实体类型
2. 需要监听的事件
3. 需要使用的 API
4. 运行环境（服务端/客户端）
5. 复杂度评估（简单/中等/复杂）

输出 JSON 格式。'''

        user_prompt = f"请分析以下需求：\n\n{requirement}"

        messages = [
            ChatMessage.system(system_prompt),
            ChatMessage.user(user_prompt),
        ]

        result = self.llm_manager.complete(messages, self.llm_config)

        # 解析结果
        import json
        try:
            # 尝试提取 JSON
            content = result.content
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()

            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            # 返回默认分析结果
            return self._default_analysis(requirement)

    def _default_analysis(self, requirement: str) -> dict[str, Any]:
        """默认分析结果（基于关键词匹配）"""
        result: dict[str, Any] = {
            "entities": [],
            "events": [],
            "apis": [],
            "target": "server",
            "complexity": "中等",
            "suggestions": [],
        }

        # 关键词匹配
        entity_keywords = ["实体", "entity", "怪物", "生物", "npc"]
        event_keywords = ["事件", "event", "监听", "触发", "回调"]
        ui_keywords = ["ui", "界面", "UI", "屏幕", "screen"]
        network_keywords = ["同步", "网络", "数据", "通知"]

        req_lower = requirement.lower()

        if any(kw in req_lower for kw in entity_keywords):
            result["entities"].append("custom_entity")
            result["apis"].append("CreateEngineEntity")

        if any(kw in req_lower for kw in event_keywords):
            result["events"].append("OnServerChat")
            result["apis"].append("ListenEvent")

        if any(kw in req_lower for kw in ui_keywords):
            result["target"] = "client"
            result["apis"].append("CreateScreen")

        if any(kw in req_lower for kw in network_keywords):
            result["apis"].extend(["NotifyToClient", "NotifyToServer"])

        return result


class SolutionDesigner:
    """
    方案设计器

    根据需求分析结果设计实现方案。
    """

    def __init__(self, llm_config: LLMConfig | None = None) -> None:
        self.llm_config = llm_config or LLMConfig(provider="mock")
        self.llm_manager = LLMManager()

    def design(
        self,
        requirement: str,
        analysis: dict[str, Any],
        context: GenerationContext | None = None,
    ) -> dict[str, Any]:
        """
        设计实现方案

        Args:
            requirement: 用户需求
            analysis: 需求分析结果
            context: 生成上下文

        Returns:
            dict: 方案设计结果，包含：
                - architecture: 架构设计
                - modules: 模块划分
                - code_generation_type: 代码生成类型
                - dependencies: 依赖项
                - implementation_steps: 实现步骤
        """
        system_prompt = '''你是一个 Minecraft ModSDK 架构设计专家。
根据需求分析设计实现方案，包括：
1. 模块划分
2. 代码结构
3. 实现步骤
4. 依赖关系

输出 JSON 格式。'''

        analysis_str = str(analysis)
        user_prompt = f"""需求：{requirement}

分析结果：{analysis_str}

请设计实现方案。"""

        messages = [
            ChatMessage.system(system_prompt),
            ChatMessage.user(user_prompt),
        ]

        result = self.llm_manager.complete(messages, self.llm_config)

        # 解析结果
        import json
        try:
            content = result.content
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()

            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return self._default_design(analysis)

    def _default_design(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """默认设计方案"""
        return {
            "architecture": "单模块架构",
            "modules": ["main"],
            "code_generation_type": CodeGenerationType.CUSTOM.value,
            "dependencies": analysis.get("apis", []),
            "implementation_steps": [
                "1. 初始化模块",
                "2. 注册事件监听",
                "3. 实现业务逻辑",
                "4. 测试验证",
            ],
        }


class IntelligentWorkflow:
    """
    智能工作流

    端到端的开发工作流自动化。
    """

    def __init__(self, llm_config: LLMConfig | None = None) -> None:
        self.llm_config = llm_config or LLMConfig(provider="mock")

        # 初始化各组件
        self.analyzer = RequirementAnalyzer(llm_config)
        self.designer = SolutionDesigner(llm_config)
        self.generator = IntelligentCodeGenerator(llm_config)
        self.reviewer = IntelligentCodeReviewer(llm_config)
        self.fixer = IntelligentFixer(llm_config)

    def run(
        self,
        requirement: str,
        context: WorkflowContext | None = None,
        progress_callback: Callable[[WorkflowStep], None] | None = None,
    ) -> WorkflowResult:
        """
        运行工作流

        Args:
            requirement: 用户需求
            context: 工作流上下文
            progress_callback: 进度回调函数

        Returns:
            WorkflowResult: 工作流结果
        """
        import time
        import uuid

        context = context or WorkflowContext(workflow_id=str(uuid.uuid4()))
        steps: list[WorkflowStep] = []
        generated_code: GeneratedCode | None = None
        review_result: ReviewResult | None = None
        diagnosis_result: DiagnosisResult | None = None
        iterations = 0

        try:
            # 1. 需求分析
            step = WorkflowStep(
                step_type=WorkflowStepType.ANALYZE,
                name="需求分析",
                description=f"分析需求：{requirement[:50]}...",
            )
            step.status = WorkflowStatus.RUNNING
            if progress_callback:
                progress_callback(step)

            start_time = time.time()
            analysis = self.analyzer.analyze(requirement)
            step.duration_ms = (time.time() - start_time) * 1000
            step.output_data = analysis
            step.status = WorkflowStatus.COMPLETED
            steps.append(step)

            # 2. 方案设计
            step = WorkflowStep(
                step_type=WorkflowStepType.DESIGN,
                name="方案设计",
                description="设计实现方案",
            )
            step.status = WorkflowStatus.RUNNING
            if progress_callback:
                progress_callback(step)

            start_time = time.time()
            design = self.designer.design(requirement, analysis)
            step.duration_ms = (time.time() - start_time) * 1000
            step.output_data = design
            step.status = WorkflowStatus.COMPLETED
            steps.append(step)

            # 确定生成类型
            gen_type_str = design.get("code_generation_type", "custom")
            try:
                gen_type = CodeGenerationType(gen_type_str)
            except ValueError:
                gen_type = CodeGenerationType.CUSTOM

            # 生成上下文
            gen_context = GenerationContext(
                project_name=context.project_name,
                module_name=context.module_name,
                target=context.target,
            )

            # 迭代生成-审查-修复循环
            while iterations < context.max_iterations:
                iterations += 1

                # 3. 代码生成
                step = WorkflowStep(
                    step_type=WorkflowStepType.GENERATE,
                    name=f"代码生成 (迭代 {iterations})",
                    description="生成代码",
                    input_data={"iteration": iterations},
                )
                step.status = WorkflowStatus.RUNNING
                if progress_callback:
                    progress_callback(step)

                start_time = time.time()
                generated_code = self.generator.generate(
                    requirement, gen_type, gen_context
                )
                step.duration_ms = (time.time() - start_time) * 1000
                step.output_data = {"code_length": len(generated_code.code)}
                step.status = WorkflowStatus.COMPLETED
                steps.append(step)

                if not generated_code.code:
                    continue

                # 4. 代码审查
                step = WorkflowStep(
                    step_type=WorkflowStepType.REVIEW,
                    name=f"代码审查 (迭代 {iterations})",
                    description="审查代码质量",
                    input_data={"iteration": iterations},
                )
                step.status = WorkflowStatus.RUNNING
                if progress_callback:
                    progress_callback(step)

                start_time = time.time()
                review_result = self.reviewer.review(generated_code.code)
                step.duration_ms = (time.time() - start_time) * 1000
                step.output_data = {"score": review_result.score}
                step.status = WorkflowStatus.COMPLETED
                steps.append(step)

                # 检查是否满足最低分数要求
                if review_result.score >= context.min_review_score:
                    break

                # 5. 修复问题
                if review_result.issues:
                    step = WorkflowStep(
                        step_type=WorkflowStepType.FIX,
                        name=f"修复问题 (迭代 {iterations})",
                        description="修复审查发现的问题",
                        input_data={"issue_count": len(review_result.issues)},
                    )
                    step.status = WorkflowStatus.RUNNING
                    if progress_callback:
                        progress_callback(step)

                    start_time = time.time()

                    # 创建错误上下文
                    error_ctx = ErrorContext(
                        error_type="CodeReviewIssue",
                        error_message=review_result.issues[0].message if review_result.issues else "",
                        code=generated_code.code,
                    )

                    diagnosis_result = self.fixer.diagnose(error_ctx)
                    step.duration_ms = (time.time() - start_time) * 1000
                    step.output_data = {
                        "diagnosis_success": diagnosis_result.success,
                        "suggestion_count": len(diagnosis_result.suggestions),
                    }
                    step.status = WorkflowStatus.COMPLETED
                    steps.append(step)

                    # 更新生成上下文，用于下一轮迭代
                    if diagnosis_result.suggestions:
                        gen_context.existing_code = generated_code.code

            # 计算总耗时
            total_duration = sum(s.duration_ms for s in steps)

            return WorkflowResult(
                success=generated_code is not None and generated_code.code != "",
                status=WorkflowStatus.COMPLETED,
                steps=steps,
                generated_code=generated_code,
                review_result=review_result,
                diagnosis_result=diagnosis_result,
                iterations=iterations,
                total_duration_ms=total_duration,
            )

        except Exception as e:
            return WorkflowResult(
                success=False,
                status=WorkflowStatus.FAILED,
                steps=steps,
                error=str(e),
            )

    async def run_async(
        self,
        requirement: str,
        context: WorkflowContext | None = None,
        progress_callback: Callable[[WorkflowStep], None] | None = None,
    ) -> WorkflowResult:
        """
        异步运行工作流

        Args:
            requirement: 用户需求
            context: 工作流上下文
            progress_callback: 进度回调函数

        Returns:
            WorkflowResult: 工作流结果
        """
        # 简化实现：调用同步方法
        return self.run(requirement, context, progress_callback)


def run_workflow(
    requirement: str,
    project_name: str = "",
    target: str = "server",
    max_iterations: int = 3,
    min_review_score: float = 70.0,
    llm_config: LLMConfig | None = None,
) -> WorkflowResult:
    """
    便捷函数：运行智能工作流

    Args:
        requirement: 用户需求
        project_name: 项目名称
        target: 运行环境
        max_iterations: 最大迭代次数
        min_review_score: 最低审查分数
        llm_config: LLM 配置

    Returns:
        WorkflowResult: 工作流结果
    """
    context = WorkflowContext(
        project_name=project_name,
        target=target,
        max_iterations=max_iterations,
        min_review_score=min_review_score,
    )

    workflow = IntelligentWorkflow(llm_config)
    return workflow.run(requirement, context)