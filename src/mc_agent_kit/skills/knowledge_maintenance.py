"""
知识库维护模块

提供知识过期检测、重复知识合并、关联关系更新和知识库健康度报告。
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


class MaintenanceAction(Enum):
    """维护动作"""
    MARK_OUTDATED = "mark_outdated"     # 标记过期
    MERGE = "merge"                     # 合并
    DELETE = "delete"                   # 删除
    UPDATE = "update"                   # 更新
    ARCHIVE = "archive"                 # 归档
    KEEP = "keep"                       # 保留


class HealthLevel(Enum):
    """健康度级别"""
    EXCELLENT = "excellent"     # 优秀
    GOOD = "good"               # 良好
    FAIR = "fair"               # 一般
    POOR = "poor"               # 较差
    CRITICAL = "critical"       # 严重


@dataclass
class KnowledgeItem:
    """知识条目（用于维护）"""
    id: str
    content: str
    knowledge_type: str
    created_at: float
    updated_at: float
    usage_count: int = 0
    confidence: float = 1.0
    status: str = "active"
    tags: list[str] = field(default_factory=list)
    source: str = ""
    related_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "knowledge_type": self.knowledge_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "usage_count": self.usage_count,
            "confidence": self.confidence,
            "status": self.status,
            "tags": self.tags,
            "source": self.source,
            "related_ids": self.related_ids,
            "metadata": self.metadata,
        }


@dataclass
class DuplicateGroup:
    """重复知识组"""
    group_id: str
    items: list[KnowledgeItem]
    similarity_score: float
    recommended_action: MaintenanceAction
    recommended_primary: str  # 推荐保留的主条目 ID

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "group_id": self.group_id,
            "items": [i.to_dict() for i in self.items],
            "similarity_score": self.similarity_score,
            "recommended_action": self.recommended_action.value,
            "recommended_primary": self.recommended_primary,
        }


@dataclass
class OutdatedResult:
    """过期检测结果"""
    item: KnowledgeItem
    reason: str
    severity: str
    suggested_action: MaintenanceAction

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "item": self.item.to_dict(),
            "reason": self.reason,
            "severity": self.severity,
            "suggested_action": self.suggested_action.value,
        }


@dataclass
class RelationUpdate:
    """关系更新"""
    source_id: str
    target_id: str
    relation_type: str
    old_strength: float
    new_strength: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "old_strength": self.old_strength,
            "new_strength": self.new_strength,
            "reason": self.reason,
        }


@dataclass
class MaintenanceReport:
    """维护报告"""
    total_knowledge: int
    outdated_count: int
    duplicate_count: int
    merged_count: int
    deleted_count: int
    updated_relations: int
    health_score: float
    health_level: HealthLevel
    issues: list[str]
    recommendations: list[str]
    execution_time: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_knowledge": self.total_knowledge,
            "outdated_count": self.outdated_count,
            "duplicate_count": self.duplicate_count,
            "merged_count": self.merged_count,
            "deleted_count": self.deleted_count,
            "updated_relations": self.updated_relations,
            "health_score": self.health_score,
            "health_level": self.health_level.value,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
        }


@dataclass
class HealthMetrics:
    """健康度指标"""
    coverage_score: float       # 覆盖度
    freshness_score: float      # 新鲜度
    consistency_score: float    # 一致性
    quality_score: float        # 质量
    utilization_score: float    # 利用率

    @property
    def overall_score(self) -> float:
        """计算总体得分"""
        return (
            self.coverage_score * 0.2 +
            self.freshness_score * 0.2 +
            self.consistency_score * 0.2 +
            self.quality_score * 0.2 +
            self.utilization_score * 0.2
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "coverage_score": self.coverage_score,
            "freshness_score": self.freshness_score,
            "consistency_score": self.consistency_score,
            "quality_score": self.quality_score,
            "utilization_score": self.utilization_score,
            "overall_score": self.overall_score,
        }


class KnowledgeMaintenance:
    """知识库维护

    执行知识库的维护任务。

    使用示例:
        maintenance = KnowledgeMaintenance()
        report = maintenance.run_maintenance()
        print(f"健康度: {report.health_level.value}")
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        auto_cleanup: bool = True,
    ) -> None:
        """初始化知识库维护"""
        self._storage_path = storage_path or Path.home() / ".mc_agent_kit" / "knowledge_maintenance"
        self._auto_cleanup = auto_cleanup
        self._knowledge_store: dict[str, KnowledgeItem] = {}
        self._relations: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._lock = threading.RLock()

        # 加载已有知识
        self._load_knowledge()

    def detect_outdated(
        self,
        max_age_days: int = 90,
        min_usage: int = 0,
    ) -> list[OutdatedResult]:
        """检测过期知识"""
        results: list[OutdatedResult] = []
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60

        with self._lock:
            for item in self._knowledge_store.values():
                # 检查年龄
                age = current_time - item.updated_at
                if age > max_age_seconds:
                    severity = "high" if age > max_age_seconds * 2 else "medium"
                    results.append(OutdatedResult(
                        item=item,
                        reason=f"知识已超过 {max_age_days} 天未更新",
                        severity=severity,
                        suggested_action=MaintenanceAction.MARK_OUTDATED,
                    ))

                # 检查使用频率
                if min_usage > 0 and item.usage_count < min_usage:
                    age = current_time - item.created_at
                    if age > 30 * 24 * 60 * 60:  # 超过 30 天
                        results.append(OutdatedResult(
                            item=item,
                            reason=f"知识使用次数低于 {min_usage}",
                            severity="low",
                            suggested_action=MaintenanceAction.ARCHIVE,
                        ))

                # 检查置信度
                if item.confidence < 0.3:
                    results.append(OutdatedResult(
                        item=item,
                        reason="知识置信度过低",
                        severity="medium",
                        suggested_action=MaintenanceAction.DELETE,
                    ))

        return results

    def find_duplicates(
        self,
        similarity_threshold: float = 0.85,
    ) -> list[DuplicateGroup]:
        """查找重复知识"""
        groups: list[DuplicateGroup] = []
        processed_ids: set[str] = set()

        with self._lock:
            items = list(self._knowledge_store.values())

            for i, item1 in enumerate(items):
                if item1.id in processed_ids:
                    continue

                duplicates: list[KnowledgeItem] = [item1]

                for item2 in items[i + 1:]:
                    if item2.id in processed_ids:
                        continue

                    # 检查类型是否相同
                    if item1.knowledge_type != item2.knowledge_type:
                        continue

                    # 计算相似度
                    similarity = self._calculate_similarity(item1.content, item2.content)

                    if similarity >= similarity_threshold:
                        duplicates.append(item2)
                        processed_ids.add(item2.id)

                if len(duplicates) > 1:
                    processed_ids.add(item1.id)

                    # 选择推荐保留的主条目
                    primary = self._select_primary_item(duplicates)

                    groups.append(DuplicateGroup(
                        group_id=self._generate_group_id(duplicates),
                        items=duplicates,
                        similarity_score=similarity_threshold,
                        recommended_action=MaintenanceAction.MERGE,
                        recommended_primary=primary.id,
                    ))

        return groups

    def merge_knowledge(
        self,
        items: list[KnowledgeItem],
        primary_id: Optional[str] = None,
    ) -> KnowledgeItem:
        """合并知识条目"""
        if not items:
            raise ValueError("没有要合并的知识条目")

        if primary_id:
            primary = next((i for i in items if i.id == primary_id), None)
            if not primary:
                primary = items[0]
        else:
            primary = self._select_primary_item(items)

        # 合并标签
        all_tags: set[str] = set()
        for item in items:
            all_tags.update(item.tags)
        primary.tags = list(all_tags)

        # 合并相关 ID
        all_related: set[str] = set()
        for item in items:
            all_related.update(item.related_ids)
        primary.related_ids = list(all_related - {primary.id})

        # 更新使用计数
        primary.usage_count = sum(i.usage_count for i in items)

        # 更新时间
        primary.updated_at = time.time()

        # 合并元数据
        for item in items:
            if item.id != primary.id:
                for key, value in item.metadata.items():
                    if key not in primary.metadata:
                        primary.metadata[key] = value
                primary.metadata[f"merged_from_{item.id}"] = item.content[:100]

        return primary

    def update_relations(
        self,
        min_usage_for_boost: int = 5,
        max_age_for_decay_days: int = 60,
    ) -> list[RelationUpdate]:
        """更新关联关系"""
        updates: list[RelationUpdate] = []
        current_time = time.time()
        max_age_seconds = max_age_for_decay_days * 24 * 60 * 60

        with self._lock:
            for source_id, relations in self._relations.items():
                source_item = self._knowledge_store.get(source_id)
                if not source_item:
                    continue

                for relation in relations:
                    target_id = relation.get("target_id", "")
                    target_item = self._knowledge_store.get(target_id)
                    if not target_item:
                        continue

                    old_strength = relation.get("strength", 1.0)
                    new_strength = old_strength

                    # 根据使用频率增强
                    if source_item.usage_count >= min_usage_for_boost:
                        new_strength = min(1.0, new_strength + 0.1)

                    # 根据年龄衰减
                    age = current_time - max(source_item.updated_at, target_item.updated_at)
                    if age > max_age_seconds:
                        decay = 0.9 ** (age / max_age_seconds)
                        new_strength *= decay

                    # 更新关系
                    if new_strength != old_strength:
                        relation["strength"] = new_strength
                        updates.append(RelationUpdate(
                            source_id=source_id,
                            target_id=target_id,
                            relation_type=relation.get("type", "related"),
                            old_strength=old_strength,
                            new_strength=new_strength,
                            reason="使用频率增强" if new_strength > old_strength else "年龄衰减",
                        ))

        return updates

    def generate_report(
        self,
        run_all_checks: bool = True,
    ) -> MaintenanceReport:
        """生成维护报告"""
        start_time = time.time()

        with self._lock:
            total_knowledge = len(self._knowledge_store)

            # 检测过期知识
            outdated = self.detect_outdated() if run_all_checks else []
            outdated_count = len(outdated)

            # 查找重复
            duplicates = self.find_duplicates() if run_all_checks else []
            duplicate_count = sum(len(g.items) - 1 for g in duplicates)

            # 计算健康度
            metrics = self._calculate_health_metrics(outdated, duplicates)

            # 生成问题和建议
            issues: list[str] = []
            recommendations: list[str] = []

            if outdated_count > total_knowledge * 0.1:
                issues.append(f"过期知识比例过高 ({outdated_count}/{total_knowledge})")
                recommendations.append("执行知识清理以移除过期内容")

            if duplicate_count > total_knowledge * 0.05:
                issues.append(f"重复知识过多 ({duplicate_count} 个重复)")
                recommendations.append("执行知识合并以减少冗余")

            if metrics.utilization_score < 0.5:
                issues.append("知识利用率较低")
                recommendations.append("检查未使用的知识并考虑归档")

            if metrics.quality_score < 0.7:
                issues.append("知识质量有待提高")
                recommendations.append("执行知识验证和修正")

            # 确定健康级别
            health_level = self._determine_health_level(metrics.overall_score)

        execution_time = time.time() - start_time

        return MaintenanceReport(
            total_knowledge=total_knowledge,
            outdated_count=outdated_count,
            duplicate_count=duplicate_count,
            merged_count=0,
            deleted_count=0,
            updated_relations=len(self._relations),
            health_score=metrics.overall_score,
            health_level=health_level,
            issues=issues,
            recommendations=recommendations,
            execution_time=execution_time,
        )

    def run_maintenance(
        self,
        cleanup_outdated: bool = True,
        merge_duplicates: bool = True,
        update_relation_weights: bool = True,
    ) -> MaintenanceReport:
        """执行完整维护"""
        start_time = time.time()

        merged_count = 0
        deleted_count = 0
        updated_relations = 0

        with self._lock:
            # 清理过期知识
            if cleanup_outdated:
                outdated = self.detect_outdated()
                for result in outdated:
                    if result.suggested_action == MaintenanceAction.DELETE:
                        if result.item.id in self._knowledge_store:
                            del self._knowledge_store[result.item.id]
                            deleted_count += 1
                    elif result.suggested_action == MaintenanceAction.MARK_OUTDATED:
                        result.item.status = "outdated"

            # 合并重复知识
            if merge_duplicates:
                duplicates = self.find_duplicates()
                for group in duplicates:
                    merged = self.merge_knowledge(group.items, group.recommended_primary)
                    # 删除非主条目
                    for item in group.items:
                        if item.id != merged.id:
                            if item.id in self._knowledge_store:
                                del self._knowledge_store[item.id]
                                merged_count += 1

            # 更新关系权重
            if update_relation_weights:
                updates = self.update_relations()
                updated_relations = len(updates)

        # 保存更改
        self._save_knowledge()

        # 生成报告
        report = self.generate_report(run_all_checks=False)
        report.merged_count = merged_count
        report.deleted_count = deleted_count
        report.updated_relations = updated_relations
        report.execution_time = time.time() - start_time

        return report

    def add_knowledge(
        self,
        item: KnowledgeItem,
    ) -> None:
        """添加知识条目"""
        with self._lock:
            self._knowledge_store[item.id] = item
        self._save_knowledge()

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str = "related",
        strength: float = 1.0,
    ) -> None:
        """添加关系"""
        with self._lock:
            self._relations[source_id].append({
                "target_id": target_id,
                "type": relation_type,
                "strength": strength,
                "created_at": time.time(),
            })

    def get_health_metrics(self) -> HealthMetrics:
        """获取健康度指标"""
        return self._calculate_health_metrics([], [])

    def get_knowledge(self, knowledge_id: str) -> Optional[KnowledgeItem]:
        """获取知识条目"""
        return self._knowledge_store.get(knowledge_id)

    def get_all_knowledge(self) -> list[KnowledgeItem]:
        """获取所有知识条目"""
        return list(self._knowledge_store.values())

    def clear(self) -> None:
        """清空知识库"""
        with self._lock:
            self._knowledge_store.clear()
            self._relations.clear()
        self._save_knowledge()

    def _calculate_similarity(
        self,
        text1: str,
        text2: str,
    ) -> float:
        """计算文本相似度"""
        # Jaccard 相似度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _select_primary_item(
        self,
        items: list[KnowledgeItem],
    ) -> KnowledgeItem:
        """选择主要条目"""
        # 按使用频率、置信度和更新时间排序
        sorted_items = sorted(
            items,
            key=lambda x: (
                x.usage_count,
                x.confidence,
                x.updated_at,
            ),
            reverse=True,
        )
        return sorted_items[0]

    def _generate_group_id(
        self,
        items: list[KnowledgeItem],
    ) -> str:
        """生成组 ID"""
        ids = sorted(i.id for i in items)
        hash_input = "|".join(ids)
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]

    def _calculate_health_metrics(
        self,
        outdated: list[OutdatedResult],
        duplicates: list[DuplicateGroup],
    ) -> HealthMetrics:
        """计算健康度指标"""
        total = len(self._knowledge_store)

        if total == 0:
            return HealthMetrics(
                coverage_score=0.0,
                freshness_score=0.0,
                consistency_score=0.0,
                quality_score=0.0,
                utilization_score=0.0,
            )

        # 覆盖度：基于类型分布
        type_counts: dict[str, int] = defaultdict(int)
        for item in self._knowledge_store.values():
            type_counts[item.knowledge_type] += 1

        coverage_score = min(1.0, len(type_counts) / 10)  # 假设 10 种类型为满分

        # 新鲜度：基于更新时间
        current_time = time.time()
        fresh_count = sum(
            1 for item in self._knowledge_store.values()
            if current_time - item.updated_at < 30 * 24 * 60 * 60
        )
        freshness_score = fresh_count / total

        # 一致性：基于重复和过期
        outdated_count = len(outdated)
        duplicate_count = sum(len(g.items) - 1 for g in duplicates)
        consistency_score = max(0, 1.0 - (outdated_count + duplicate_count) / total)

        # 质量：基于置信度
        avg_confidence = sum(
            item.confidence for item in self._knowledge_store.values()
        ) / total
        quality_score = avg_confidence

        # 利用率：基于使用频率
        used_count = sum(
            1 for item in self._knowledge_store.values()
            if item.usage_count > 0
        )
        utilization_score = used_count / total

        return HealthMetrics(
            coverage_score=coverage_score,
            freshness_score=freshness_score,
            consistency_score=consistency_score,
            quality_score=quality_score,
            utilization_score=utilization_score,
        )

    def _determine_health_level(
        self,
        score: float,
    ) -> HealthLevel:
        """确定健康级别"""
        if score >= 0.9:
            return HealthLevel.EXCELLENT
        elif score >= 0.75:
            return HealthLevel.GOOD
        elif score >= 0.6:
            return HealthLevel.FAIR
        elif score >= 0.4:
            return HealthLevel.POOR
        else:
            return HealthLevel.CRITICAL

    def _load_knowledge(self) -> None:
        """加载已存储的知识"""
        if not self._storage_path.exists():
            return

        knowledge_file = self._storage_path / "knowledge.json"
        if not knowledge_file.exists():
            return

        try:
            with open(knowledge_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item_data in data.get("knowledge", []):
                item = KnowledgeItem(
                    id=item_data["id"],
                    content=item_data["content"],
                    knowledge_type=item_data["knowledge_type"],
                    created_at=item_data.get("created_at", time.time()),
                    updated_at=item_data.get("updated_at", time.time()),
                    usage_count=item_data.get("usage_count", 0),
                    confidence=item_data.get("confidence", 1.0),
                    status=item_data.get("status", "active"),
                    tags=item_data.get("tags", []),
                    source=item_data.get("source", ""),
                    related_ids=item_data.get("related_ids", []),
                    metadata=item_data.get("metadata", {}),
                )
                self._knowledge_store[item.id] = item

            for relation_data in data.get("relations", []):
                source_id = relation_data.get("source_id")
                if source_id:
                    self._relations[source_id].append(relation_data)

        except (json.JSONDecodeError, KeyError):
            pass

    def _save_knowledge(self) -> None:
        """保存知识到存储"""
        self._storage_path.mkdir(parents=True, exist_ok=True)
        knowledge_file = self._storage_path / "knowledge.json"

        with self._lock:
            data = {
                "knowledge": [item.to_dict() for item in self._knowledge_store.values()],
                "relations": [
                    {"source_id": sid, **rel}
                    for sid, rels in self._relations.items()
                    for rel in rels
                ],
                "saved_at": time.time(),
            }

        with open(knowledge_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# 全局实例
_maintenance: Optional[KnowledgeMaintenance] = None


def get_knowledge_maintenance() -> KnowledgeMaintenance:
    """获取全局知识库维护"""
    global _maintenance
    if _maintenance is None:
        _maintenance = KnowledgeMaintenance()
    return _maintenance


def run_maintenance(
    cleanup_outdated: bool = True,
    merge_duplicates: bool = True,
    update_relation_weights: bool = True,
) -> MaintenanceReport:
    """便捷函数：执行维护"""
    return get_knowledge_maintenance().run_maintenance(
        cleanup_outdated=cleanup_outdated,
        merge_duplicates=merge_duplicates,
        update_relation_weights=update_relation_weights,
    )


def get_health_report() -> MaintenanceReport:
    """便捷函数：获取健康报告"""
    return get_knowledge_maintenance().generate_report()