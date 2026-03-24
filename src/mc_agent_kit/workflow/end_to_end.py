"""
端到端工作流模块

实现 MVP 闭环：查文档 → 创建项目 → 启动测试 → 诊断错误
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from mc_agent_kit.knowledge.retrieval import KnowledgeRetrieval
from mc_agent_kit.launcher.auto_fixer import MemoryAutoFixer, MemoryFixReport
from mc_agent_kit.launcher.diagnoser import DiagnosticReport, LauncherDiagnoser
from mc_agent_kit.log_capture.analyzer import LogAnalyzer
from mc_agent_kit.scaffold.creator import ProjectCreator


class WorkflowStep(Enum):
    """工作流步骤"""
    SEARCH_DOCS = "search_docs"        # 查文档
    CREATE_PROJECT = "create_project"  # 创建项目
    LAUNCH_TEST = "launch_test"        # 启动测试
    DIAGNOSE_ERROR = "diagnose_error"  # 诊断错误
    FIX_ERROR = "fix_error"            # 修复错误


class WorkflowStepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStepResult:
    """工作流步骤结果"""
    step: WorkflowStep
    status: WorkflowStepStatus
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    duration_ms: int = 0
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step.value,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "output": self.output,
            "error": self.error,
            "suggestions": self.suggestions,
        }


@dataclass
class WorkflowResult:
    """工作流结果"""
    success: bool
    steps: list[WorkflowStepResult] = field(default_factory=list)
    total_duration_ms: int = 0
    final_message: str = ""
    project_path: str | None = None
    diagnostic_report: DiagnosticReport | None = None
    memory_fix_report: MemoryFixReport | None = None

    @property
    def failed_steps(self) -> list[WorkflowStepResult]:
        return [s for s in self.steps if s.status == WorkflowStepStatus.FAILED]

    @property
    def success_steps(self) -> list[WorkflowStepResult]:
        return [s for s in self.steps if s.status == WorkflowStepStatus.SUCCESS]

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "steps": [s.to_dict() for s in self.steps],
            "total_duration_ms": self.total_duration_ms,
            "final_message": self.final_message,
            "project_path": self.project_path,
            "failed_steps_count": len(self.failed_steps),
            "success_steps_count": len(self.success_steps),
        }


@dataclass
class WorkflowConfig:
    """工作流配置"""
    project_name: str = "my_addon"
    output_dir: str = "."
    game_path: str | None = None
    knowledge_base_path: str | None = None
    search_query: str = ""
    entity_name: str | None = None
    item_name: str | None = None
    auto_fix: bool = True
    verbose: bool = False
    timeout_seconds: int = 300  # 5 minutes total timeout
    step_timeout_seconds: int = 60  # 1 minute per step


class EndToEndWorkflow:
    """
    端到端工作流管理器

    整合完整的 MCP 开发闭环：
    1. 搜索文档：查询相关 API 和事件
    2. 创建项目：生成 Addon 项目结构
    3. 启动测试：运行游戏验证
    4. 诊断错误：分析日志定位问题
    5. 修复错误：提供或应用修复建议
    """

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self._retrieval: KnowledgeRetrieval | None = None
        self._creator: ProjectCreator | None = None
        self._diagnoser: LauncherDiagnoser | None = None
        self._memory_fixer: MemoryAutoFixer | None = None
        self._log_analyzer: LogAnalyzer | None = None
        self._step_results: list[WorkflowStepResult] = []

    def _init_retrieval(self) -> None:
        """初始化知识检索器"""
        if self._retrieval is None:
            self._retrieval = KnowledgeRetrieval(
                knowledge_base_path=self.config.knowledge_base_path
            )

    def _init_creator(self) -> None:
        """初始化项目创建器"""
        if self._creator is None:
            self._creator = ProjectCreator()

    def _init_diagnoser(self) -> None:
        """初始化诊断器"""
        if self._diagnoser is None:
            self._diagnoser = LauncherDiagnoser(game_path=self.config.game_path)

    def _init_memory_fixer(self) -> None:
        """初始化内存修复器"""
        if self._memory_fixer is None:
            self._memory_fixer = MemoryAutoFixer()

    def _init_log_analyzer(self) -> None:
        """初始化日志分析器"""
        if self._log_analyzer is None:
            self._log_analyzer = LogAnalyzer()

    def _record_step(
        self,
        step: WorkflowStep,
        status: WorkflowStepStatus,
        output: dict[str, Any] | None = None,
        error: str | None = None,
        suggestions: list[str] | None = None,
    ) -> WorkflowStepResult:
        """记录步骤结果"""
        result = WorkflowStepResult(
            step=step,
            status=status,
            output=output or {},
            error=error,
            suggestions=suggestions or [],
        )
        result.end_time = datetime.now()
        result.duration_ms = int(
            (result.end_time - result.start_time).total_seconds() * 1000
        )
        self._step_results.append(result)
        return result

    def step_search_docs(self, query: str) -> WorkflowStepResult:
        """
        步骤 1: 搜索文档

        Args:
            query: 搜索查询

        Returns:
            步骤结果
        """
        step = WorkflowStep.SEARCH_DOCS
        time.time()

        try:
            self._init_retrieval()

            # 执行搜索 - 使用正确的 API
            results = self._retrieval.search(query, limit=5)

            # 统计结果
            api_count = sum(1 for r in results if r.type == "api")
            event_count = sum(1 for r in results if r.type == "event")
            example_count = sum(1 for r in results if r.type == "example")

            output = {
                "query": query,
                "api_count": api_count,
                "event_count": event_count,
                "example_count": example_count,
                "total_count": len(results),
                "results": [
                    {
                        "type": r.type,
                        "name": r.name,
                        "description": r.description,
                        "score": r.score,
                    }
                    for r in results[:5]
                ],
            }

            suggestions = []
            if len(results) == 0:
                suggestions.append("未找到相关文档，请尝试使用不同的关键词")

            return self._record_step(
                step,
                WorkflowStepStatus.SUCCESS,
                output=output,
                suggestions=suggestions,
            )
        except Exception as e:
            return self._record_step(
                step,
                WorkflowStepStatus.FAILED,
                error=str(e),
                suggestions=["检查知识库路径是否正确"],
            )

    def step_create_project(self) -> WorkflowStepResult:
        """
        步骤 2: 创建项目

        Returns:
            步骤结果
        """
        step = WorkflowStep.CREATE_PROJECT

        try:
            self._init_creator()

            # 创建项目 - 使用正确的 API
            project = self._creator.create_project(
                name=self.config.project_name,
                path=self.config.output_dir,
            )
            project_path = str(project.path)

            # 添加实体（如果配置了）
            entity_path = None
            if self.config.entity_name:
                try:
                    entity_result = self._creator.add_entity(self.config.entity_name, project)
                    entity_path = str(entity_result) if entity_result else None
                except Exception:
                    pass  # 实体添加失败不影响项目创建

            # 添加物品（如果配置了）
            item_path = None
            if self.config.item_name:
                try:
                    item_result = self._creator.add_item(self.config.item_name, project)
                    item_path = str(item_result) if item_result else None
                except Exception:
                    pass  # 物品添加失败不影响项目创建

            output = {
                "project_path": project_path,
                "entity_path": entity_path,
                "item_path": item_path,
            }

            return self._record_step(
                step,
                WorkflowStepStatus.SUCCESS,
                output=output,
            )
        except Exception as e:
            return self._record_step(
                step,
                WorkflowStepStatus.FAILED,
                error=str(e),
                suggestions=["检查输出目录权限", "确保项目名称有效"],
            )

    def step_launch_test(self, addon_path: str) -> WorkflowStepResult:
        """
        步骤 3: 启动测试

        Args:
            addon_path: Addon 路径

        Returns:
            步骤结果
        """
        step = WorkflowStep.LAUNCH_TEST

        try:
            self._init_diagnoser()

            # 运行诊断检查
            report = self._diagnoser.diagnose(addon_path=addon_path)

            output = {
                "addon_path": addon_path,
                "diagnostic_success": report.success,
                "errors_count": report.checks_failed,
                "warnings_count": report.checks_warning,
            }

            suggestions = []
            if report.has_errors:
                suggestions.extend([
                    issue.suggestion for issue in report.issues
                    if issue.severity.value == "error" and issue.suggestion
                ])

            # 如果有错误，标记为失败
            if report.has_errors:
                return self._record_step(
                    step,
                    WorkflowStepStatus.FAILED,
                    output=output,
                    error="启动诊断发现问题",
                    suggestions=suggestions,
                )

            return self._record_step(
                step,
                WorkflowStepStatus.SUCCESS,
                output=output,
                suggestions=suggestions if suggestions else None,
            )
        except Exception as e:
            return self._record_step(
                step,
                WorkflowStepStatus.FAILED,
                error=str(e),
                suggestions=["检查游戏路径是否正确", "确保 Addon 结构完整"],
            )

    def step_diagnose_error(
        self,
        addon_path: str | None = None,
        log_content: str | None = None,
    ) -> WorkflowStepResult:
        """
        步骤 4: 诊断错误

        Args:
            addon_path: Addon 路径
            log_content: 日志内容（可选）

        Returns:
            步骤结果
        """
        step = WorkflowStep.DIAGNOSE_ERROR

        try:
            self._init_diagnoser()
            self._init_log_analyzer()

            output = {}
            suggestions = []

            # 诊断 Addon
            if addon_path:
                report = self._diagnoser.diagnose(addon_path=addon_path)
                output["diagnostic_report"] = report.to_dict()

                if report.has_errors:
                    for issue in report.issues:
                        if issue.severity.value == "error":
                            suggestions.append(f"{issue.code}: {issue.suggestion}")

            # 分析日志
            if log_content:
                self._log_analyzer.process_batch(log_content.split("\n"))
                alerts = self._log_analyzer.get_alerts()
                stats = self._log_analyzer.get_statistics()

                output["log_analysis"] = {
                    "error_count": stats.error_count,
                    "warning_count": stats.warning_count,
                    "alert_count": len(alerts),
                    "alerts": [
                        {
                            "severity": a.severity.value,
                            "title": a.title,
                            "message": a.message,
                        }
                        for a in alerts[:5]  # 只返回前 5 个
                    ],
                }

                for alert in alerts:
                    if alert.pattern and alert.pattern.suggestions:
                        suggestions.extend(alert.pattern.suggestions[:2])

            # 判断是否成功
            has_issues = (
                output.get("diagnostic_report", {}).get("has_errors", False) or
                output.get("log_analysis", {}).get("error_count", 0) > 0
            )

            if has_issues:
                return self._record_step(
                    step,
                    WorkflowStepStatus.SUCCESS,  # 诊断成功，但发现了问题
                    output=output,
                    suggestions=suggestions,
                )

            return self._record_step(
                step,
                WorkflowStepStatus.SUCCESS,
                output=output,
            )
        except Exception as e:
            return self._record_step(
                step,
                WorkflowStepStatus.FAILED,
                error=str(e),
                suggestions=["检查日志格式是否正确"],
            )

    def step_fix_error(self, addon_path: str) -> WorkflowStepResult:
        """
        步骤 5: 修复错误

        Args:
            addon_path: Addon 路径

        Returns:
            步骤结果
        """
        step = WorkflowStep.FIX_ERROR

        try:
            self._init_memory_fixer()

            # 分析并生成修复建议
            report = self._memory_fixer.analyze(addon_path)

            output = {
                "addon_path": addon_path,
                "total_issues": report.total_issues,
                "fixable_count": report.fixable_count,
                "fixes": [
                    {
                        "type": fix.fix_type.value,
                        "severity": fix.severity.value,
                        "description": fix.description,
                        "auto_fixable": fix.auto_fixable,
                    }
                    for fix in report.fixes[:10]  # 只返回前 10 个
                ],
            }

            suggestions = report.optimization_tips[:5] if report.optimization_tips else []

            if report.total_issues > 0:
                return self._record_step(
                    step,
                    WorkflowStepStatus.SUCCESS,  # 分析成功
                    output=output,
                    suggestions=suggestions,
                )

            return self._record_step(
                step,
                WorkflowStepStatus.SUCCESS,
                output=output,
                suggestions=["未发现需要修复的问题"],
            )
        except Exception as e:
            return self._record_step(
                step,
                WorkflowStepStatus.FAILED,
                error=str(e),
                suggestions=["检查 Addon 路径是否正确"],
            )

    def run_full_cycle(
        self,
        search_query: str | None = None,
        addon_path: str | None = None,
        log_content: str | None = None,
    ) -> WorkflowResult:
        """
        运行完整开发闭环

        Args:
            search_query: 搜索查询（可选）
            addon_path: Addon 路径（可选）
            log_content: 日志内容（可选）

        Returns:
            工作流结果
        """
        start_time = time.time()
        self._step_results = []

        # 步骤 1: 搜索文档
        if search_query or self.config.search_query:
            query = search_query or self.config.search_query
            self.step_search_docs(query)

        # 步骤 2: 创建项目
        if not addon_path:
            result = self.step_create_project()
            if result.status == WorkflowStepStatus.SUCCESS:
                addon_path = result.output.get("project_path")

        # 步骤 3: 启动测试
        if addon_path:
            self.step_launch_test(addon_path)

        # 步骤 4: 诊断错误
        if addon_path or log_content:
            diag_result = self.step_diagnose_error(addon_path, log_content)

            # 步骤 5: 修复错误（如果需要且启用了自动修复）
            if self.config.auto_fix and addon_path and diag_result.suggestions:
                self.step_fix_error(addon_path)

        # 计算总时间
        total_duration_ms = int((time.time() - start_time) * 1000)

        # 判断整体成功
        success = all(
            s.status in (WorkflowStepStatus.SUCCESS, WorkflowStepStatus.SKIPPED)
            for s in self._step_results
        )

        return WorkflowResult(
            success=success,
            steps=self._step_results,
            total_duration_ms=total_duration_ms,
            final_message="工作流完成" if success else "工作流遇到问题",
            project_path=addon_path,
        )


def create_workflow(config: WorkflowConfig | None = None) -> EndToEndWorkflow:
    """
    创建工作流实例

    Args:
        config: 工作流配置

    Returns:
        工作流实例
    """
    if config is None:
        config = WorkflowConfig()
    return EndToEndWorkflow(config)


def run_development_cycle(
    project_name: str,
    output_dir: str,
    search_query: str | None = None,
    entity_name: str | None = None,
    game_path: str | None = None,
    auto_fix: bool = True,
) -> WorkflowResult:
    """
    运行开发周期的便捷函数

    Args:
        project_name: 项目名称
        output_dir: 输出目录
        search_query: 搜索查询
        entity_name: 实体名称
        game_path: 游戏路径
        auto_fix: 是否自动修复

    Returns:
        工作流结果
    """
    config = WorkflowConfig(
        project_name=project_name,
        output_dir=output_dir,
        search_query=search_query or "",
        entity_name=entity_name,
        game_path=game_path,
        auto_fix=auto_fix,
    )
    workflow = create_workflow(config)
    return workflow.run_full_cycle()
