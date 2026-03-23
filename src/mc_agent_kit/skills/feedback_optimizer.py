"""
反馈优化模块

提供用户反馈收集、推理规则权重调整、补全排序优化和常见错误模式识别。
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class FeedbackType(Enum):
    """反馈类型"""
    ACCEPT = "accept"           # 接受
    REJECT = "reject"           # 拒绝
    MODIFY = "modify"           # 修改
    RATE = "rate"               # 评分
    CORRECT = "correct"         # 纠正
    SKIP = "skip"               # 跳过


class FeedbackTarget(Enum):
    """反馈目标类型"""
    COMPLETION = "completion"       # 补全建议
    INFERENCE = "inference"         # 推理结果
    SUGGESTION = "suggestion"       # 建议
    FIX = "fix"                     # 修复建议
    CODE_GEN = "code_gen"           # 代码生成
    API_CALL = "api_call"           # API 调用


@dataclass
class Feedback:
    """用户反馈"""
    id: str
    feedback_type: FeedbackType
    target_type: FeedbackTarget
    target_id: str
    original_content: str
    modified_content: str = ""
    rating: int = 0  # 1-5 分
    comment: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    session_id: str = ""
    user_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "feedback_type": self.feedback_type.value,
            "target_type": self.target_type.value,
            "target_id": self.target_id,
            "original_content": self.original_content,
            "modified_content": self.modified_content,
            "rating": self.rating,
            "comment": self.comment,
            "context": self.context,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "user_id": self.user_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Feedback":
        """从字典创建"""
        return cls(
            id=data["id"],
            feedback_type=FeedbackType(data["feedback_type"]),
            target_type=FeedbackTarget(data["target_type"]),
            target_id=data["target_id"],
            original_content=data.get("original_content", ""),
            modified_content=data.get("modified_content", ""),
            rating=data.get("rating", 0),
            comment=data.get("comment", ""),
            context=data.get("context", {}),
            timestamp=data.get("timestamp", time.time()),
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
        )


@dataclass
class ErrorPattern:
    """错误模式"""
    id: str
    pattern: str                   # 错误模式描述
    frequency: int                 # 出现频率
    last_seen: float              # 最后出现时间
    affected_targets: list[str]   # 受影响的目标类型
    common_fixes: list[str]       # 常见修复方法
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "pattern": self.pattern,
            "frequency": self.frequency,
            "last_seen": self.last_seen,
            "affected_targets": self.affected_targets,
            "common_fixes": self.common_fixes,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class AdjustmentScore:
    """调整分数"""
    target_id: str
    base_score: float
    adjustment: float
    final_score: float
    factors: dict[str, float]
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "target_id": self.target_id,
            "base_score": self.base_score,
            "adjustment": self.adjustment,
            "final_score": self.final_score,
            "factors": self.factors,
            "reason": self.reason,
        }


@dataclass
class OptimizationStats:
    """优化统计"""
    total_feedback: int = 0
    accept_rate: float = 0.0
    average_rating: float = 0.0
    patterns_identified: int = 0
    improvements: int = 0
    regressions: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_feedback": self.total_feedback,
            "accept_rate": self.accept_rate,
            "average_rating": self.average_rating,
            "patterns_identified": self.patterns_identified,
            "improvements": self.improvements,
            "regressions": self.regressions,
        }


class FeedbackCollector:
    """反馈收集器

    收集和管理用户反馈。
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
    ) -> None:
        """初始化反馈收集器"""
        self._storage_path = storage_path or Path.home() / ".mc_agent_kit" / "feedback"
        self._feedback_store: dict[str, Feedback] = {}
        self._feedback_by_target: dict[str, list[str]] = defaultdict(list)
        self._feedback_by_type: dict[FeedbackType, list[str]] = defaultdict(list)
        self._lock = threading.RLock()

        # 加载已有反馈
        self._load_feedback()

    def record_feedback(
        self,
        feedback_type: FeedbackType,
        target_type: FeedbackTarget,
        target_id: str,
        original_content: str,
        modified_content: str = "",
        rating: int = 0,
        comment: str = "",
        context: Optional[dict[str, Any]] = None,
        session_id: str = "",
        user_id: str = "",
    ) -> Feedback:
        """记录反馈"""
        feedback_id = self._generate_id()

        feedback = Feedback(
            id=feedback_id,
            feedback_type=feedback_type,
            target_type=target_type,
            target_id=target_id,
            original_content=original_content,
            modified_content=modified_content,
            rating=rating,
            comment=comment,
            context=context or {},
            session_id=session_id,
            user_id=user_id,
        )

        with self._lock:
            self._feedback_store[feedback_id] = feedback
            self._feedback_by_target[target_id].append(feedback_id)
            self._feedback_by_type[feedback_type].append(feedback_id)

        # 保存反馈
        self._save_feedback()

        return feedback

    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """获取反馈"""
        return self._feedback_store.get(feedback_id)

    def get_feedback_by_target(
        self,
        target_id: str,
        limit: int = 100,
    ) -> list[Feedback]:
        """获取目标的反馈"""
        with self._lock:
            feedback_ids = self._feedback_by_target.get(target_id, [])[:limit]
            return [self._feedback_store[fid] for fid in feedback_ids if fid in self._feedback_store]

    def get_feedback_by_type(
        self,
        feedback_type: FeedbackType,
        limit: int = 100,
    ) -> list[Feedback]:
        """获取类型的反馈"""
        with self._lock:
            feedback_ids = self._feedback_by_type.get(feedback_type, [])[:limit]
            return [self._feedback_store[fid] for fid in feedback_ids if fid in self._feedback_store]

    def get_recent_feedback(
        self,
        limit: int = 50,
    ) -> list[Feedback]:
        """获取最近的反馈"""
        with self._lock:
            feedback_list = list(self._feedback_store.values())
            feedback_list.sort(key=lambda x: x.timestamp, reverse=True)
            return feedback_list[:limit]

    def get_feedback_stats(
        self,
        target_type: Optional[FeedbackTarget] = None,
    ) -> dict[str, Any]:
        """获取反馈统计"""
        with self._lock:
            feedback_list = list(self._feedback_store.values())

            if target_type:
                feedback_list = [f for f in feedback_list if f.target_type == target_type]

            if not feedback_list:
                return {
                    "total": 0,
                    "accept_rate": 0.0,
                    "average_rating": 0.0,
                }

            accept_count = sum(1 for f in feedback_list if f.feedback_type == FeedbackType.ACCEPT)
            ratings = [f.rating for f in feedback_list if f.rating > 0]

            return {
                "total": len(feedback_list),
                "accept_rate": accept_count / len(feedback_list),
                "average_rating": sum(ratings) / len(ratings) if ratings else 0.0,
                "type_distribution": self._get_type_distribution(feedback_list),
            }

    def _get_type_distribution(
        self,
        feedback_list: list[Feedback],
    ) -> dict[str, int]:
        """获取类型分布"""
        distribution: dict[str, int] = {}
        for feedback in feedback_list:
            type_name = feedback.feedback_type.value
            distribution[type_name] = distribution.get(type_name, 0) + 1
        return distribution

    def _generate_id(self) -> str:
        """生成反馈 ID"""
        hash_input = f"{time.time()}{threading.get_ident()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

    def _load_feedback(self) -> None:
        """加载已存储的反馈"""
        if not self._storage_path.exists():
            return

        feedback_file = self._storage_path / "feedback.json"
        if not feedback_file.exists():
            return

        try:
            with open(feedback_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for feedback_data in data.get("feedback", []):
                feedback = Feedback.from_dict(feedback_data)
                self._feedback_store[feedback.id] = feedback
                self._feedback_by_target[feedback.target_id].append(feedback.id)
                self._feedback_by_type[feedback.feedback_type].append(feedback.id)

        except (json.JSONDecodeError, KeyError):
            pass

    def _save_feedback(self) -> None:
        """保存反馈到存储"""
        self._storage_path.mkdir(parents=True, exist_ok=True)
        feedback_file = self._storage_path / "feedback.json"

        with self._lock:
            data = {
                "feedback": [f.to_dict() for f in self._feedback_store.values()],
                "saved_at": time.time(),
            }

        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def clear(self) -> None:
        """清空反馈"""
        with self._lock:
            self._feedback_store.clear()
            self._feedback_by_target.clear()
            self._feedback_by_type.clear()
        self._save_feedback()


class FeedbackOptimizer:
    """反馈优化器

    根据反馈调整系统行为。
    """

    def __init__(
        self,
        collector: Optional[FeedbackCollector] = None,
    ) -> None:
        """初始化反馈优化器"""
        self._collector = collector or FeedbackCollector()
        self._weight_adjustments: dict[str, float] = defaultdict(float)
        self._target_scores: dict[str, float] = defaultdict(lambda: 1.0)
        self._error_patterns: dict[str, ErrorPattern] = {}
        self._lock = threading.RLock()

    def record_feedback(
        self,
        feedback_type: FeedbackType,
        target_type: FeedbackTarget,
        target_id: str,
        original_content: str,
        modified_content: str = "",
        rating: int = 0,
        comment: str = "",
        context: Optional[dict[str, Any]] = None,
    ) -> Feedback:
        """记录反馈并更新优化"""
        feedback = self._collector.record_feedback(
            feedback_type=feedback_type,
            target_type=target_type,
            target_id=target_id,
            original_content=original_content,
            modified_content=modified_content,
            rating=rating,
            comment=comment,
            context=context,
        )

        # 更新权重
        self._update_weights(feedback)

        # 识别错误模式
        if feedback_type in (FeedbackType.REJECT, FeedbackType.MODIFY):
            self._identify_error_pattern(feedback)

        return feedback

    def get_adjustment_score(
        self,
        target_id: str,
        target_type: FeedbackTarget,
        base_score: float = 1.0,
    ) -> AdjustmentScore:
        """获取调整后的分数"""
        with self._lock:
            # 获取历史反馈
            feedbacks = self._collector.get_feedback_by_target(target_id)

            # 计算调整因子
            factors: dict[str, float] = {}

            # 接受率因子
            accept_count = sum(1 for f in feedbacks if f.feedback_type == FeedbackType.ACCEPT)
            reject_count = sum(1 for f in feedbacks if f.feedback_type == FeedbackType.REJECT)
            total = len(feedbacks)

            if total > 0:
                factors["accept_rate"] = accept_count / total
            else:
                factors["accept_rate"] = 1.0

            # 评分因子
            ratings = [f.rating for f in feedbacks if f.rating > 0]
            if ratings:
                factors["rating"] = sum(ratings) / (len(ratings) * 5)  # 归一化到 0-1
            else:
                factors["rating"] = 1.0

            # 修改因子
            modify_count = sum(1 for f in feedbacks if f.feedback_type == FeedbackType.MODIFY)
            if total > 0:
                factors["modify_rate"] = 1.0 - (modify_count / total) * 0.3
            else:
                factors["modify_rate"] = 1.0

            # 错误模式因子
            if target_type.value in self._get_affected_error_patterns(target_id):
                factors["error_pattern"] = 0.7
            else:
                factors["error_pattern"] = 1.0

            # 计算总调整
            adjustment = 1.0
            for factor_name, factor_value in factors.items():
                weight = self._get_factor_weight(factor_name)
                adjustment *= factor_value * weight + (1 - weight)

            final_score = base_score * adjustment

            return AdjustmentScore(
                target_id=target_id,
                base_score=base_score,
                adjustment=adjustment,
                final_score=final_score,
                factors=factors,
                reason=self._explain_adjustment(factors),
            )

    def optimize_completions(
        self,
        items: list[dict[str, Any]],
        context: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """优化补全排序"""
        if not items:
            return items

        optimized: list[tuple[dict[str, Any], float]] = []

        for item in items:
            target_id = item.get("id", item.get("text", ""))
            base_score = item.get("confidence", 1.0)

            adjustment = self.get_adjustment_score(
                target_id=target_id,
                target_type=FeedbackTarget.COMPLETION,
                base_score=base_score,
            )

            optimized.append((item, adjustment.final_score))

        # 按调整后分数排序
        optimized.sort(key=lambda x: x[1], reverse=True)

        return [item for item, _ in optimized]

    def identify_error_patterns(
        self,
        min_frequency: int = 3,
    ) -> list[ErrorPattern]:
        """识别错误模式"""
        with self._lock:
            patterns: list[ErrorPattern] = []

            for pattern_id, pattern in self._error_patterns.items():
                if pattern.frequency >= min_frequency:
                    patterns.append(pattern)

            patterns.sort(key=lambda p: p.frequency, reverse=True)
            return patterns

    def get_optimization_stats(self) -> OptimizationStats:
        """获取优化统计"""
        stats = self._collector.get_feedback_stats()

        with self._lock:
            return OptimizationStats(
                total_feedback=stats.get("total", 0),
                accept_rate=stats.get("accept_rate", 0.0),
                average_rating=stats.get("average_rating", 0.0),
                patterns_identified=len(self._error_patterns),
                improvements=sum(1 for v in self._weight_adjustments.values() if v > 0),
                regressions=sum(1 for v in self._weight_adjustments.values() if v < 0),
            )

    def _update_weights(self, feedback: Feedback) -> None:
        """更新权重"""
        with self._lock:
            target_key = f"{feedback.target_type.value}:{feedback.target_id}"

            if feedback.feedback_type == FeedbackType.ACCEPT:
                self._weight_adjustments[target_key] += 0.1
                self._target_scores[feedback.target_id] *= 1.1

            elif feedback.feedback_type == FeedbackType.REJECT:
                self._weight_adjustments[target_key] -= 0.2
                self._target_scores[feedback.target_id] *= 0.8

            elif feedback.feedback_type == FeedbackType.MODIFY:
                self._weight_adjustments[target_key] -= 0.1
                self._target_scores[feedback.target_id] *= 0.9

            elif feedback.feedback_type == FeedbackType.RATE:
                # 根据评分调整
                adjustment = (feedback.rating - 3) * 0.1  # 3 是中性评分
                self._weight_adjustments[target_key] += adjustment
                self._target_scores[feedback.target_id] *= (1.0 + adjustment)

    def _identify_error_pattern(self, feedback: Feedback) -> None:
        """识别错误模式"""
        # 提取错误模式
        if feedback.feedback_type == FeedbackType.REJECT:
            pattern_key = f"reject:{feedback.target_type.value}"
        else:
            pattern_key = f"modify:{feedback.target_type.value}"

        with self._lock:
            if pattern_key not in self._error_patterns:
                self._error_patterns[pattern_key] = ErrorPattern(
                    id=pattern_key,
                    pattern=f"{feedback.target_type.value} 被 {feedback.feedback_type.value}",
                    frequency=1,
                    last_seen=time.time(),
                    affected_targets=[feedback.target_type.value],
                    common_fixes=[],
                    confidence=0.5,
                )
            else:
                pattern = self._error_patterns[pattern_key]
                pattern.frequency += 1
                pattern.last_seen = time.time()
                pattern.confidence = min(1.0, pattern.confidence + 0.1)

            # 如果有修改内容，记录修复方法
            if feedback.modified_content:
                pattern = self._error_patterns[pattern_key]
                if feedback.modified_content not in pattern.common_fixes:
                    pattern.common_fixes.append(feedback.modified_content)

    def _get_affected_error_patterns(self, target_id: str) -> list[str]:
        """获取影响目标的错误模式"""
        affected: list[str] = []
        for pattern_id, pattern in self._error_patterns.items():
            if target_id in pattern.common_fixes or pattern.frequency > 5:
                affected.append(pattern_id)
        return affected

    def _get_factor_weight(self, factor_name: str) -> float:
        """获取因子权重"""
        weights = {
            "accept_rate": 0.4,
            "rating": 0.3,
            "modify_rate": 0.2,
            "error_pattern": 0.1,
        }
        return weights.get(factor_name, 0.25)

    def _explain_adjustment(self, factors: dict[str, float]) -> str:
        """解释调整原因"""
        reasons: list[str] = []

        if factors.get("accept_rate", 1.0) < 0.7:
            reasons.append("历史接受率较低")

        if factors.get("rating", 1.0) < 0.6:
            reasons.append("用户评分较低")

        if factors.get("modify_rate", 1.0) < 0.8:
            reasons.append("经常被修改")

        if factors.get("error_pattern", 1.0) < 0.8:
            reasons.append("存在相关错误模式")

        if not reasons:
            return "无明显调整"

        return "; ".join(reasons)

    def reset(self) -> None:
        """重置优化器"""
        with self._lock:
            self._weight_adjustments.clear()
            self._target_scores.clear()
            self._error_patterns.clear()


# 全局实例
_collector: Optional[FeedbackCollector] = None
_optimizer: Optional[FeedbackOptimizer] = None


def get_feedback_collector() -> FeedbackCollector:
    """获取全局反馈收集器"""
    global _collector
    if _collector is None:
        _collector = FeedbackCollector()
    return _collector


def get_feedback_optimizer() -> FeedbackOptimizer:
    """获取全局反馈优化器"""
    global _optimizer
    if _optimizer is None:
        _optimizer = FeedbackOptimizer(get_feedback_collector())
    return _optimizer


def record_feedback(
    feedback_type: FeedbackType,
    target_type: FeedbackTarget,
    target_id: str,
    original_content: str,
    modified_content: str = "",
    rating: int = 0,
    comment: str = "",
) -> Feedback:
    """便捷函数：记录反馈"""
    return get_feedback_optimizer().record_feedback(
        feedback_type=feedback_type,
        target_type=target_type,
        target_id=target_id,
        original_content=original_content,
        modified_content=modified_content,
        rating=rating,
        comment=comment,
    )


def optimize_items(
    items: list[dict[str, Any]],
    context: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """便捷函数：优化补全排序"""
    return get_feedback_optimizer().optimize_completions(items, context)