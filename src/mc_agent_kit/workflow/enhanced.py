"""
工作流增强模块

提供工作流步骤重试机制、跳过条件、进度回调和暂停/恢复功能
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from mc_agent_kit.workflow.end_to_end import (
    EndToEndWorkflow,
    WorkflowConfig,
    WorkflowResult,
    WorkflowStep,
    WorkflowStepResult,
    WorkflowStepStatus,
)


class RetryPolicy(Enum):
    """重试策略"""
    NONE = "none"           # 不重试
    LINEAR = "linear"       # 线性重试
    EXPONENTIAL = "exponential"  # 指数退避


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    policy: RetryPolicy = RetryPolicy.LINEAR
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    retryable_errors: list[str] = field(default_factory=list)  # 可重试的错误类型

    def get_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        if self.policy == RetryPolicy.NONE:
            return 0
        elif self.policy == RetryPolicy.LINEAR:
            delay = self.base_delay_seconds * attempt
        else:  # EXPONENTIAL
            delay = self.base_delay_seconds * (2 ** (attempt - 1))

        return min(delay, self.max_delay_seconds)


@dataclass
class SkipCondition:
    """跳过条件"""
    step: WorkflowStep
    condition: Callable[[dict[str, Any]], bool]
    reason: str

    def should_skip(self, context: dict[str, Any]) -> bool:
        """检查是否应该跳过"""
        try:
            return self.condition(context)
        except Exception:
            return False


@dataclass
class ProgressInfo:
    """进度信息"""
    current_step: WorkflowStep
    total_steps: int
    completed_steps: int
    percentage: float
    elapsed_seconds: float
    estimated_remaining_seconds: float | None
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_step": self.current_step.value,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "percentage": round(self.percentage, 1),
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "estimated_remaining_seconds": round(self.estimated_remaining_seconds, 1) if self.estimated_remaining_seconds else None,
            "message": self.message,
        }


# 进度回调类型
ProgressCallback = Callable[[ProgressInfo], None]


class WorkflowState(Enum):
    """工作流状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowControl:
    """工作流控制"""
    state: WorkflowState = WorkflowState.IDLE
    _pause_event: threading.Event = field(default_factory=threading.Event)
    _cancel_flag: bool = False

    def __post_init__(self):
        self._pause_event.set()  # 默认不暂停

    def pause(self) -> None:
        """暂停工作流"""
        self.state = WorkflowState.PAUSED
        self._pause_event.clear()

    def resume(self) -> None:
        """恢复工作流"""
        if self.state == WorkflowState.PAUSED:
            self.state = WorkflowState.RUNNING
            self._pause_event.set()

    def cancel(self) -> None:
        """取消工作流"""
        self._cancel_flag = True
        self.state = WorkflowState.CANCELLED
        self._pause_event.set()  # 确保取消时不会卡在暂停状态

    def check_paused(self) -> None:
        """检查是否暂停，如果暂停则阻塞"""
        self._pause_event.wait()

    def is_cancelled(self) -> bool:
        """检查是否取消"""
        return self._cancel_flag


class EnhancedWorkflow(EndToEndWorkflow):
    """
    增强的工作流管理器
    
    在基础工作流上添加：
    - 重试机制
    - 跳过条件
    - 进度回调
    - 暂停/恢复
    """

    def __init__(
        self,
        config: WorkflowConfig,
        retry_config: RetryConfig | None = None,
        progress_callback: ProgressCallback | None = None,
    ):
        super().__init__(config)
        self.retry_config = retry_config or RetryConfig()
        self.progress_callback = progress_callback
        self.control = WorkflowControl()
        self._skip_conditions: dict[WorkflowStep, SkipCondition] = {}
        self._start_time: float | None = None
        self._completed_steps: int = 0

    def add_skip_condition(
        self,
        step: WorkflowStep,
        condition: Callable[[dict[str, Any]], bool],
        reason: str,
    ) -> None:
        """
        添加跳过条件
        
        Args:
            step: 要跳过的步骤
            condition: 判断条件函数，返回 True 表示跳过
            reason: 跳过原因
        """
        self._skip_conditions[step] = SkipCondition(step, condition, reason)

    def remove_skip_condition(self, step: WorkflowStep) -> None:
        """移除跳过条件"""
        if step in self._skip_conditions:
            del self._skip_conditions[step]

    def _report_progress(
        self,
        step: WorkflowStep,
        message: str,
        total_steps: int,
    ) -> None:
        """报告进度"""
        if not self.progress_callback:
            return

        elapsed = time.time() - (self._start_time or time.time())
        percentage = (self._completed_steps / total_steps) * 100 if total_steps > 0 else 0

        # 估算剩余时间
        if self._completed_steps > 0 and elapsed > 0:
            avg_time_per_step = elapsed / self._completed_steps
            remaining_steps = total_steps - self._completed_steps
            estimated_remaining = avg_time_per_step * remaining_steps
        else:
            estimated_remaining = None

        info = ProgressInfo(
            current_step=step,
            total_steps=total_steps,
            completed_steps=self._completed_steps,
            percentage=percentage,
            elapsed_seconds=elapsed,
            estimated_remaining_seconds=estimated_remaining,
            message=message,
        )
        self.progress_callback(info)

    def _execute_with_retry(
        self,
        step_func: Callable[[], WorkflowStepResult],
        step: WorkflowStep,
    ) -> WorkflowStepResult:
        """
        带重试的执行步骤
        
        Args:
            step_func: 步骤执行函数
            step: 步骤类型
            
        Returns:
            步骤结果
        """
        last_result = None
        attempts = 0
        max_attempts = self.retry_config.max_retries + 1

        while attempts < max_attempts:
            # 检查取消
            if self.control.is_cancelled():
                return WorkflowStepResult(
                    step=step,
                    status=WorkflowStepStatus.FAILED,
                    error="工作流已取消",
                )

            # 检查暂停
            self.control.check_paused()

            # 执行步骤
            result = step_func()
            attempts += 1

            # 成功则返回
            if result.status == WorkflowStepStatus.SUCCESS:
                return result

            # 检查是否可重试
            if result.error and self.retry_config.retryable_errors:
                is_retryable = any(
                    err in result.error for err in self.retry_config.retryable_errors
                )
                if not is_retryable:
                    return result

            # 最后一次尝试不等待
            if attempts < max_attempts:
                delay = self.retry_config.get_delay(attempts)
                if delay > 0:
                    time.sleep(delay)

            last_result = result

        return last_result or WorkflowStepResult(
            step=step,
            status=WorkflowStepStatus.FAILED,
            error="重试次数已用尽",
        )

    def _check_skip(self, step: WorkflowStep, context: dict[str, Any]) -> WorkflowStepResult | None:
        """
        检查是否应该跳过步骤
        
        Args:
            step: 步骤类型
            context: 执行上下文
            
        Returns:
            如果跳过，返回跳过结果；否则返回 None
        """
        if step not in self._skip_conditions:
            return None

        condition = self._skip_conditions[step]
        if condition.should_skip(context):
            return WorkflowStepResult(
                step=step,
                status=WorkflowStepStatus.SKIPPED,
                output={"skip_reason": condition.reason},
            )

        return None

    def run_full_cycle(
        self,
        search_query: str | None = None,
        addon_path: str | None = None,
        log_content: str | None = None,
    ) -> WorkflowResult:
        """
        运行完整开发闭环（增强版）
        
        支持重试、跳过、进度回调和暂停/恢复
        
        Args:
            search_query: 搜索查询（可选）
            addon_path: Addon 路径（可选）
            log_content: 日志内容（可选）
            
        Returns:
            工作流结果
        """
        self._start_time = time.time()
        self._completed_steps = 0
        self.control.state = WorkflowState.RUNNING
        self._step_results = []

        # 定义步骤
        steps = [
            WorkflowStep.SEARCH_DOCS,
            WorkflowStep.CREATE_PROJECT,
            WorkflowStep.LAUNCH_TEST,
            WorkflowStep.DIAGNOSE_ERROR,
            WorkflowStep.FIX_ERROR,
        ]
        total_steps = len(steps)

        # 构建上下文
        context: dict[str, Any] = {
            "search_query": search_query or self.config.search_query,
            "addon_path": addon_path,
            "log_content": log_content,
        }

        try:
            # 步骤 1: 搜索文档
            self._report_progress(WorkflowStep.SEARCH_DOCS, "正在搜索文档...", total_steps)

            skip_result = self._check_skip(WorkflowStep.SEARCH_DOCS, context)
            if skip_result:
                self._step_results.append(skip_result)
            elif search_query or self.config.search_query:
                query = search_query or self.config.search_query
                result = self._execute_with_retry(
                    lambda: self.step_search_docs(query),
                    WorkflowStep.SEARCH_DOCS,
                )
                self._step_results.append(result)
                context["search_result"] = result.output
            else:
                # 没有查询则跳过
                self._step_results.append(WorkflowStepResult(
                    step=WorkflowStep.SEARCH_DOCS,
                    status=WorkflowStepStatus.SKIPPED,
                    output={"skip_reason": "未提供搜索查询"},
                ))

            self._completed_steps += 1

            # 检查取消
            if self.control.is_cancelled():
                self.control.state = WorkflowState.CANCELLED
                return self._build_result(False, "工作流已取消")

            # 步骤 2: 创建项目
            self._report_progress(WorkflowStep.CREATE_PROJECT, "正在创建项目...", total_steps)

            skip_result = self._check_skip(WorkflowStep.CREATE_PROJECT, context)
            if skip_result:
                self._step_results.append(skip_result)
            elif not addon_path:
                result = self._execute_with_retry(
                    lambda: self.step_create_project(),
                    WorkflowStep.CREATE_PROJECT,
                )
                self._step_results.append(result)
                if result.status == WorkflowStepStatus.SUCCESS:
                    addon_path = result.output.get("project_path")
                    context["addon_path"] = addon_path
                context["create_result"] = result.output
            else:
                self._step_results.append(WorkflowStepResult(
                    step=WorkflowStep.CREATE_PROJECT,
                    status=WorkflowStepStatus.SKIPPED,
                    output={"skip_reason": "已提供 Addon 路径"},
                ))

            self._completed_steps += 1

            # 检查取消
            if self.control.is_cancelled():
                self.control.state = WorkflowState.CANCELLED
                return self._build_result(False, "工作流已取消")

            # 步骤 3: 启动测试
            self._report_progress(WorkflowStep.LAUNCH_TEST, "正在启动测试...", total_steps)

            skip_result = self._check_skip(WorkflowStep.LAUNCH_TEST, context)
            if skip_result:
                self._step_results.append(skip_result)
            elif addon_path:
                result = self._execute_with_retry(
                    lambda: self.step_launch_test(addon_path),
                    WorkflowStep.LAUNCH_TEST,
                )
                self._step_results.append(result)
                context["launch_result"] = result.output
            else:
                self._step_results.append(WorkflowStepResult(
                    step=WorkflowStep.LAUNCH_TEST,
                    status=WorkflowStepStatus.SKIPPED,
                    output={"skip_reason": "无 Addon 路径"},
                ))

            self._completed_steps += 1

            # 检查取消
            if self.control.is_cancelled():
                self.control.state = WorkflowState.CANCELLED
                return self._build_result(False, "工作流已取消")

            # 步骤 4: 诊断错误
            self._report_progress(WorkflowStep.DIAGNOSE_ERROR, "正在诊断错误...", total_steps)

            skip_result = self._check_skip(WorkflowStep.DIAGNOSE_ERROR, context)
            if skip_result:
                self._step_results.append(skip_result)
            elif addon_path or log_content:
                diag_result = self._execute_with_retry(
                    lambda: self.step_diagnose_error(addon_path, log_content),
                    WorkflowStep.DIAGNOSE_ERROR,
                )
                self._step_results.append(diag_result)
                context["diagnose_result"] = diag_result.output

                # 步骤 5: 修复错误（如果需要且启用了自动修复）
                self._completed_steps += 1
                self._report_progress(WorkflowStep.FIX_ERROR, "正在修复错误...", total_steps)

                skip_result = self._check_skip(WorkflowStep.FIX_ERROR, context)
                if skip_result:
                    self._step_results.append(skip_result)
                elif self.config.auto_fix and addon_path and diag_result.suggestions:
                    fix_result = self._execute_with_retry(
                        lambda: self.step_fix_error(addon_path),
                        WorkflowStep.FIX_ERROR,
                    )
                    self._step_results.append(fix_result)
                    context["fix_result"] = fix_result.output
                else:
                    self._step_results.append(WorkflowStepResult(
                        step=WorkflowStep.FIX_ERROR,
                        status=WorkflowStepStatus.SKIPPED,
                        output={"skip_reason": "无需修复或未启用自动修复"},
                    ))
            else:
                self._step_results.append(WorkflowStepResult(
                    step=WorkflowStep.DIAGNOSE_ERROR,
                    status=WorkflowStepStatus.SKIPPED,
                    output={"skip_reason": "无 Addon 路径或日志"},
                ))
                self._step_results.append(WorkflowStepResult(
                    step=WorkflowStep.FIX_ERROR,
                    status=WorkflowStepStatus.SKIPPED,
                    output={"skip_reason": "未执行诊断"},
                ))

            self._completed_steps += 1

            # 构建结果
            success = all(
                s.status in (WorkflowStepStatus.SUCCESS, WorkflowStepStatus.SKIPPED)
                for s in self._step_results
            )

            self.control.state = WorkflowState.COMPLETED if success else WorkflowState.FAILED
            return self._build_result(success, "工作流完成" if success else "工作流遇到问题")

        except Exception as e:
            self.control.state = WorkflowState.FAILED
            return self._build_result(False, f"工作流异常: {e}")

    def _build_result(self, success: bool, message: str) -> WorkflowResult:
        """构建工作流结果"""
        total_duration_ms = int((time.time() - (self._start_time or time.time())) * 1000)

        # 获取 project_path
        project_path = None
        for result in self._step_results:
            if result.step == WorkflowStep.CREATE_PROJECT and result.status == WorkflowStepStatus.SUCCESS:
                project_path = result.output.get("project_path")
                break

        return WorkflowResult(
            success=success,
            steps=self._step_results,
            total_duration_ms=total_duration_ms,
            final_message=message,
            project_path=project_path,
        )

    def pause(self) -> None:
        """暂停工作流"""
        self.control.pause()

    def resume(self) -> None:
        """恢复工作流"""
        self.control.resume()

    def cancel(self) -> None:
        """取消工作流"""
        self.control.cancel()

    @property
    def state(self) -> WorkflowState:
        """获取工作流状态"""
        return self.control.state


def create_enhanced_workflow(
    config: WorkflowConfig | None = None,
    retry_config: RetryConfig | None = None,
    progress_callback: ProgressCallback | None = None,
) -> EnhancedWorkflow:
    """
    创建增强工作流实例

    Args:
        config: 工作流配置
        retry_config: 重试配置
        progress_callback: 进度回调函数

    Returns:
        增强工作流实例
    """
    if config is None:
        config = WorkflowConfig()
    return EnhancedWorkflow(
        config=config,
        retry_config=retry_config,
        progress_callback=progress_callback,
    )