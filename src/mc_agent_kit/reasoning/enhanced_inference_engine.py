"""
增强推理引擎模块

提供多跳推理、上下文推理、规则冲突检测和推理可视化。
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .enhanced_knowledge_graph import (
    EnhancedKnowledgeGraph,
    EnhancedGraphNode,
    EnhancedGraphEdge,
    EnhancedNodeType,
    EnhancedRelationType,
    get_enhanced_knowledge_graph,
)


class ReasoningType(Enum):
    """推理类型"""
    DEDUCTIVE = "deductive"       # 演绎推理
    INDUCTIVE = "inductive"       # 归纳推理
    ABDUCTIVE = "abductive"       # 溯因推理
    ANALOGICAL = "analogical"     # 类比推理
    CAUSAL = "causal"             # 因果推理
    MULTI_HOP = "multi_hop"       # 多跳推理
    CONTEXTUAL = "contextual"     # 上下文推理


class ReasoningStatus(Enum):
    """推理状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class RulePriority(Enum):
    """规则优先级"""
    CRITICAL = 100
    HIGH = 80
    NORMAL = 50
    LOW = 20
    BACKGROUND = 10


@dataclass
class EnhancedRule:
    """增强推理规则"""
    id: str
    name: str
    conditions: list[dict[str, Any]]
    conclusions: list[dict[str, Any]]
    priority: RulePriority = RulePriority.NORMAL
    confidence: float = 1.0
    description: str = ""
    tags: list[str] = field(default_factory=list)
    enabled: bool = True
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "conditions": self.conditions,
            "conclusions": self.conclusions,
            "priority": self.priority.value,
            "confidence": self.confidence,
            "description": self.description,
            "tags": self.tags,
            "enabled": self.enabled,
            "created_at": self.created_at,
        }


@dataclass
class RuleConflict:
    """规则冲突"""
    rule1_id: str
    rule2_id: str
    conflict_type: str  # "conclusion" | "condition" | "priority"
    description: str
    resolution: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule1_id": self.rule1_id,
            "rule2_id": self.rule2_id,
            "conflict_type": self.conflict_type,
            "description": self.description,
            "resolution": self.resolution,
        }


@dataclass
class ReasoningContext:
    """推理上下文"""
    query: str
    facts: dict[str, Any] = field(default_factory=dict)
    goals: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    timeout: float = 10.0
    max_depth: int = 5
    session_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "facts": self.facts,
            "goals": self.goals,
            "constraints": self.constraints,
            "history": self.history,
            "timeout": self.timeout,
            "max_depth": self.max_depth,
            "session_id": self.session_id,
        }

    def add_to_history(self, step: dict[str, Any]) -> None:
        """添加历史记录"""
        self.history.append(step)

    def compress_history(self, max_items: int = 10) -> None:
        """压缩历史记录"""
        if len(self.history) > max_items:
            # 保留关键信息
            compressed = []
            for step in self.history[-max_items:]:
                compressed.append({
                    "type": step.get("type"),
                    "summary": step.get("summary", ""),
                })
            self.history = compressed


@dataclass
class EnhancedInferenceResult:
    """增强推理结果"""
    reasoning_type: ReasoningType
    conclusions: list[dict[str, Any]]
    confidence: float
    reasoning_chain: list[dict[str, Any]]
    evidence: list[str]
    execution_time: float
    status: ReasoningStatus
    context_summary: Optional[str] = None
    alternative_paths: list[list[dict[str, Any]]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reasoning_type": self.reasoning_type.value,
            "conclusions": self.conclusions,
            "confidence": self.confidence,
            "reasoning_chain": self.reasoning_chain,
            "evidence": self.evidence,
            "execution_time": self.execution_time,
            "status": self.status.value,
            "context_summary": self.context_summary,
            "alternative_paths": self.alternative_paths,
        }


class MultiHopReasoning:
    """多跳推理引擎"""

    def __init__(
        self,
        graph: Optional[EnhancedKnowledgeGraph] = None,
        max_hops: int = 3,
    ) -> None:
        self._graph = graph or get_enhanced_knowledge_graph()
        self._max_hops = max_hops
        self._lock = threading.RLock()

    def reason(
        self,
        start_node_id: str,
        target_type: Optional[EnhancedNodeType] = None,
        relation_filter: Optional[list[EnhancedRelationType]] = None,
        min_confidence: float = 0.5,
    ) -> EnhancedInferenceResult:
        """执行多跳推理"""
        start_time = time.time()

        if start_node_id not in self._graph._nodes:
            return EnhancedInferenceResult(
                reasoning_type=ReasoningType.MULTI_HOP,
                conclusions=[],
                confidence=0.0,
                reasoning_chain=[],
                evidence=[],
                execution_time=time.time() - start_time,
                status=ReasoningStatus.FAILED,
            )

        conclusions: list[dict[str, Any]] = []
        reasoning_chain: list[dict[str, Any]] = []
        evidence: list[str] = []
        alternative_paths: list[list[dict[str, Any]]] = []

        # BFS 多跳推理
        visited: set[str] = {start_node_id}
        frontier: list[tuple[str, int, float, list[dict[str, Any]]]] = [
            (start_node_id, 0, 1.0, [])
        ]

        while frontier:
            current_id, hops, cumulative_conf, path = frontier.pop(0)

            if hops >= self._max_hops:
                continue

            neighbors = self._graph.get_neighbors(current_id, relation_filter)

            for neighbor, edge in neighbors:
                if neighbor.id in visited:
                    continue

                visited.add(neighbor.id)
                new_conf = cumulative_conf * edge.confidence

                if new_conf < min_confidence:
                    continue

                step_info = {
                    "hop": hops + 1,
                    "from": current_id,
                    "to": neighbor.id,
                    "relation": edge.relation.value,
                    "confidence": new_conf,
                }
                new_path = path + [step_info]

                # 检查是否匹配目标类型
                if target_type is None or neighbor.type == target_type:
                    conclusions.append({
                        "node_id": neighbor.id,
                        "node_name": neighbor.name,
                        "node_type": neighbor.type.value,
                        "confidence": new_conf,
                        "path_length": hops + 1,
                    })
                    evidence.append(f"通过 {hops + 1} 跳 {edge.relation.value} 关系到达")
                    alternative_paths.append(new_path)

                reasoning_chain.append(step_info)
                frontier.append((neighbor.id, hops + 1, new_conf, new_path))

        # 按置信度排序
        conclusions.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        execution_time = time.time() - start_time
        final_confidence = max((c.get("confidence", 0) for c in conclusions), default=0.0)

        return EnhancedInferenceResult(
            reasoning_type=ReasoningType.MULTI_HOP,
            conclusions=conclusions,
            confidence=final_confidence,
            reasoning_chain=reasoning_chain,
            evidence=evidence,
            execution_time=execution_time,
            status=ReasoningStatus.COMPLETED,
            alternative_paths=alternative_paths[:5],  # 限制返回路径数
        )


class ContextualReasoner:
    """上下文推理器"""

    def __init__(
        self,
        graph: Optional[EnhancedKnowledgeGraph] = None,
        context_window_size: int = 5,
    ) -> None:
        self._graph = graph or get_enhanced_knowledge_graph()
        self._context_window_size = context_window_size
        self._context_cache: dict[str, list[dict[str, Any]]] = {}
        self._lock = threading.RLock()

    def reason(
        self,
        context: ReasoningContext,
    ) -> EnhancedInferenceResult:
        """执行上下文推理"""
        start_time = time.time()

        conclusions: list[dict[str, Any]] = []
        reasoning_chain: list[dict[str, Any]] = []
        evidence: list[str] = []

        # 1. 提取关键信息
        key_entities = self._extract_key_entities(context)
        reasoning_chain.append({
            "step": 1,
            "type": "entity_extraction",
            "entities": key_entities,
        })

        # 2. 构建上下文窗口
        context_window = self._build_context_window(context, key_entities)
        reasoning_chain.append({
            "step": 2,
            "type": "context_window",
            "window_size": len(context_window),
        })

        # 3. 压缩上下文
        compressed = self._compress_context(context_window)
        reasoning_chain.append({
            "step": 3,
            "type": "context_compression",
            "compressed_size": len(compressed),
        })

        # 4. 基于上下文推理
        for entity_id, entity_context in compressed.items():
            node = self._graph.get_node(entity_id)
            if node:
                # 推断相关 API
                related = self._graph.get_neighbors(entity_id)
                for neighbor, edge in related[:5]:
                    conclusions.append({
                        "entity": entity_id,
                        "related": neighbor.name,
                        "relation": edge.relation.value,
                        "context_relevance": edge.confidence,
                    })
                    evidence.append(f"上下文中 {node.name} 与 {neighbor.name} 相关")

        # 5. 多轮对话推理
        if len(context.history) > 1:
            multi_turn_result = self._multi_turn_inference(context)
            conclusions.extend(multi_turn_result)
            evidence.append("多轮对话推断")

        execution_time = time.time() - start_time
        confidence = self._calculate_confidence(conclusions)

        # 生成上下文摘要
        context_summary = self._generate_context_summary(context, conclusions)

        return EnhancedInferenceResult(
            reasoning_type=ReasoningType.CONTEXTUAL,
            conclusions=conclusions,
            confidence=confidence,
            reasoning_chain=reasoning_chain,
            evidence=evidence,
            execution_time=execution_time,
            status=ReasoningStatus.COMPLETED,
            context_summary=context_summary,
        )

    def _extract_key_entities(self, context: ReasoningContext) -> list[str]:
        """提取关键实体"""
        entities: list[str] = []

        # 从查询中提取
        query_lower = context.query.lower()
        for node_id, node in self._graph._nodes.items():
            if node.name.lower() in query_lower:
                entities.append(node_id)

        # 从事实中提取
        for key, value in context.facts.items():
            if isinstance(value, str):
                for node_id, node in self._graph._nodes.items():
                    if node.name.lower() == value.lower():
                        entities.append(node_id)

        return list(set(entities))[:10]

    def _build_context_window(
        self,
        context: ReasoningContext,
        key_entities: list[str],
    ) -> list[dict[str, Any]]:
        """构建上下文窗口"""
        window: list[dict[str, Any]] = []

        # 添加历史记录
        for hist in context.history[-self._context_window_size:]:
            window.append({
                "type": "history",
                "content": hist,
            })

        # 添加关键实体信息
        for entity_id in key_entities:
            node = self._graph.get_node(entity_id)
            if node:
                window.append({
                    "type": "entity",
                    "id": entity_id,
                    "name": node.name,
                    "properties": node.properties,
                })

        return window

    def _compress_context(
        self,
        context_window: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """压缩上下文"""
        compressed: dict[str, dict[str, Any]] = {}

        for item in context_window:
            if item.get("type") == "entity":
                entity_id = item.get("id")
                if entity_id:
                    compressed[entity_id] = item

        return compressed

    def _multi_turn_inference(self, context: ReasoningContext) -> list[dict[str, Any]]:
        """多轮对话推理"""
        results: list[dict[str, Any]] = []

        # 分析历史趋势
        if len(context.history) >= 2:
            # 检测重复查询
            queries = [h.get("query", "") for h in context.history if isinstance(h, dict)]
            if len(queries) != len(set(queries)):
                results.append({
                    "type": "clarification_needed",
                    "reason": "重复查询检测",
                })

        return results

    def _calculate_confidence(self, conclusions: list[dict[str, Any]]) -> float:
        """计算置信度"""
        if not conclusions:
            return 0.0

        confidences = [
            c.get("context_relevance", c.get("confidence", 0.5))
            for c in conclusions
        ]
        return sum(confidences) / len(confidences)

    def _generate_context_summary(
        self,
        context: ReasoningContext,
        conclusions: list[dict[str, Any]],
    ) -> str:
        """生成上下文摘要"""
        parts: list[str] = []

        if context.query:
            parts.append(f"查询: {context.query[:50]}")

        if context.facts:
            parts.append(f"事实数: {len(context.facts)}")

        if context.history:
            parts.append(f"历史轮数: {len(context.history)}")

        if conclusions:
            parts.append(f"结论数: {len(conclusions)}")

        return " | ".join(parts)


class RuleEngineEnhanced:
    """增强规则引擎"""

    def __init__(self) -> None:
        self._rules: dict[str, EnhancedRule] = {}
        self._rule_index: dict[str, list[str]] = defaultdict(list)  # tag -> rule_ids
        self._conflicts: list[RuleConflict] = []
        self._lock = threading.RLock()

    def add_rule(self, rule: EnhancedRule) -> None:
        """添加规则"""
        with self._lock:
            self._rules[rule.id] = rule
            for tag in rule.tags:
                self._rule_index[tag].append(rule.id)

    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        with self._lock:
            if rule_id in self._rules:
                rule = self._rules[rule_id]
                for tag in rule.tags:
                    if rule_id in self._rule_index[tag]:
                        self._rule_index[tag].remove(rule_id)
                del self._rules[rule_id]
                return True
            return False

    def get_rules_by_tag(self, tag: str) -> list[EnhancedRule]:
        """按标签获取规则"""
        rule_ids = self._rule_index.get(tag, [])
        return [self._rules[rid] for rid in rule_ids if rid in self._rules]

    def detect_conflicts(self) -> list[RuleConflict]:
        """检测规则冲突"""
        self._conflicts.clear()

        rules = list(self._rules.values())
        for i, rule1 in enumerate(rules):
            for rule2 in rules[i + 1:]:
                conflict = self._check_conflict(rule1, rule2)
                if conflict:
                    self._conflicts.append(conflict)

        return self._conflicts

    def _check_conflict(
        self,
        rule1: EnhancedRule,
        rule2: EnhancedRule,
    ) -> Optional[RuleConflict]:
        """检查两个规则是否冲突"""
        # 检查结论冲突
        for c1 in rule1.conclusions:
            for c2 in rule2.conclusions:
                if self._conclusions_conflict(c1, c2):
                    return RuleConflict(
                        rule1_id=rule1.id,
                        rule2_id=rule2.id,
                        conflict_type="conclusion",
                        description=f"结论冲突: {c1} vs {c2}",
                        resolution=f"使用优先级更高的规则",
                    )

        return None

    def _conclusions_conflict(
        self,
        c1: dict[str, Any],
        c2: dict[str, Any],
    ) -> bool:
        """检查结论是否冲突"""
        # 简单检查：相同键但不同值
        for key in c1:
            if key in c2 and c1[key] != c2[key]:
                return True
        return False

    def infer(
        self,
        facts: dict[str, Any],
        max_iterations: int = 100,
    ) -> EnhancedInferenceResult:
        """执行推理"""
        start_time = time.time()

        reasoning_chain: list[dict[str, Any]] = []
        conclusions: list[dict[str, Any]] = []
        evidence: list[str] = []
        derived_facts = dict(facts)

        iteration = 0
        new_facts_derived = True

        while new_facts_derived and iteration < max_iterations:
            new_facts_derived = False
            iteration += 1

            # 按优先级排序规则
            sorted_rules = sorted(
                [r for r in self._rules.values() if r.enabled],
                key=lambda r: r.priority.value,
                reverse=True,
            )

            for rule in sorted_rules:
                if self._check_conditions(rule.conditions, derived_facts):
                    for conclusion in rule.conclusions:
                        if conclusion not in conclusions:
                            conclusions.append(conclusion)
                            reasoning_chain.append({
                                "step": iteration,
                                "rule": rule.name,
                                "conclusion": conclusion,
                                "confidence": rule.confidence,
                            })
                            evidence.append(f"规则: {rule.name}")

                            if "fact" in conclusion:
                                derived_facts.update(conclusion["fact"])
                                new_facts_derived = True

        execution_time = time.time() - start_time
        confidence = self._calculate_confidence(reasoning_chain)

        return EnhancedInferenceResult(
            reasoning_type=ReasoningType.DEDUCTIVE,
            conclusions=conclusions,
            confidence=confidence,
            reasoning_chain=reasoning_chain,
            evidence=evidence,
            execution_time=execution_time,
            status=ReasoningStatus.COMPLETED,
        )

    def _check_conditions(
        self,
        conditions: list[dict[str, Any]],
        facts: dict[str, Any],
    ) -> bool:
        """检查条件"""
        for condition in conditions:
            if not self._check_single_condition(condition, facts):
                return False
        return True

    def _check_single_condition(
        self,
        condition: dict[str, Any],
        facts: dict[str, Any],
    ) -> bool:
        """检查单个条件"""
        cond_type = condition.get("type")

        if cond_type == "api":
            api_name = condition.get("name")
            return facts.get("apis", {}).get(api_name) is not None
        elif cond_type == "event":
            event_name = condition.get("name")
            return facts.get("events", {}).get(event_name) is not None
        elif cond_type == "fact":
            key = condition.get("key")
            value = condition.get("value")
            return facts.get(key) == value
        elif cond_type == "contains":
            key = condition.get("key")
            value = condition.get("value")
            return value in facts.get(key, [])

        return False

    def _calculate_confidence(self, reasoning_chain: list[dict[str, Any]]) -> float:
        """计算置信度"""
        if not reasoning_chain:
            return 0.0

        total = sum(step.get("confidence", 1.0) for step in reasoning_chain)
        return total / len(reasoning_chain)

    def load_builtin_rules(self) -> None:
        """加载内置规则"""
        # 实体创建规则
        self.add_rule(EnhancedRule(
            id="entity_create_pos",
            name="实体创建需要设置位置",
            conditions=[{"type": "api", "name": "CreateEngineEntity"}],
            conclusions=[
                {"suggestion": "创建实体后需要调用 SetEngineEntityPos 设置位置"},
                {"related_api": "SetEngineEntityPos"},
            ],
            priority=RulePriority.HIGH,
            confidence=0.95,
            tags=["entity", "creation"],
        ))

        # 事件监听规则
        self.add_rule(EnhancedRule(
            id="event_listener",
            name="事件监听需要注册",
            conditions=[{"type": "event", "name": "OnServerChat"}],
            conclusions=[
                {"suggestion": "需要使用 ListenEvent 注册事件监听"},
                {"related_api": "ListenEvent"},
            ],
            priority=RulePriority.HIGH,
            confidence=0.95,
            tags=["event", "listener"],
        ))

        # UI 规则
        self.add_rule(EnhancedRule(
            id="ui_screen_create",
            name="UI 屏幕创建规则",
            conditions=[{"type": "api", "name": "CreateUI"}],
            conclusions=[
                {"suggestion": "创建 UI 后需要注册事件处理"},
                {"related_api": "RegisterUIEventHandler"},
            ],
            priority=RulePriority.NORMAL,
            confidence=0.9,
            tags=["ui", "creation"],
        ))

        # 网络同步规则
        self.add_rule(EnhancedRule(
            id="network_sync",
            name="网络同步规则",
            conditions=[{"type": "api", "name": "SyncData"}],
            conclusions=[
                {"suggestion": "同步数据需要检查客户端/服务端一致性"},
                {"related_api": "CheckDataConsistency"},
            ],
            priority=RulePriority.NORMAL,
            confidence=0.85,
            tags=["network", "sync"],
        ))


class EnhancedInferenceEngine:
    """
    增强推理引擎

    整合多跳推理、上下文推理和规则推理。

    使用示例:
        engine = EnhancedInferenceEngine()
        engine.load_defaults()
        result = engine.infer(context)
    """

    def __init__(
        self,
        graph: Optional[EnhancedKnowledgeGraph] = None,
    ) -> None:
        self._graph = graph or get_enhanced_knowledge_graph()
        self._multi_hop = MultiHopReasoning(self._graph)
        self._contextual = ContextualReasoner(self._graph)
        self._rule_engine = RuleEngineEnhanced()
        self._lock = threading.RLock()

    def load_defaults(self) -> None:
        """加载默认配置"""
        self._rule_engine.load_builtin_rules()

    def infer(
        self,
        context: ReasoningContext,
    ) -> EnhancedInferenceResult:
        """执行推理"""
        start_time = time.time()

        # 确定推理类型
        reasoning_type = self._determine_reasoning_type(context)

        # 根据推理类型选择引擎
        if reasoning_type == ReasoningType.MULTI_HOP:
            start_node = context.facts.get("start_node", "")
            if start_node:
                return self._multi_hop.reason(start_node)
            # 回退到规则推理
            reasoning_type = ReasoningType.DEDUCTIVE

        if reasoning_type == ReasoningType.CONTEXTUAL:
            return self._contextual.reason(context)

        # 默认使用规则推理
        result = self._rule_engine.infer(context.facts)

        # 检查超时
        execution_time = time.time() - start_time
        if execution_time > context.timeout:
            result.status = ReasoningStatus.TIMEOUT

        return result

    def _determine_reasoning_type(self, context: ReasoningContext) -> ReasoningType:
        """确定推理类型"""
        query_lower = context.query.lower()

        # 多跳推理关键词
        multi_hop_keywords = ["关联", "路径", "相关", "linked", "path", "related"]
        if any(kw in query_lower for kw in multi_hop_keywords):
            return ReasoningType.MULTI_HOP

        # 上下文推理关键词
        contextual_keywords = ["上下文", "历史", "之前", "context", "history", "previous"]
        if any(kw in query_lower for kw in contextual_keywords) or len(context.history) > 0:
            return ReasoningType.CONTEXTUAL

        return ReasoningType.DEDUCTIVE

    def multi_hop_reasoning(
        self,
        start_node_id: str,
        target_type: Optional[EnhancedNodeType] = None,
        max_hops: int = 3,
    ) -> EnhancedInferenceResult:
        """多跳推理"""
        self._multi_hop._max_hops = max_hops
        return self._multi_hop.reason(start_node_id, target_type)

    def contextual_reasoning(
        self,
        context: ReasoningContext,
    ) -> EnhancedInferenceResult:
        """上下文推理"""
        return self._contextual.reason(context)

    def add_rule(self, rule: EnhancedRule) -> None:
        """添加规则"""
        self._rule_engine.add_rule(rule)

    def detect_rule_conflicts(self) -> list[RuleConflict]:
        """检测规则冲突"""
        return self._rule_engine.detect_conflicts()

    def visualize_reasoning(
        self,
        result: EnhancedInferenceResult,
    ) -> str:
        """可视化推理过程"""
        lines = ["# 推理过程"]
        lines.append(f"**推理类型**: {result.reasoning_type.value}")
        lines.append(f"**置信度**: {result.confidence:.2f}")
        lines.append(f"**状态**: {result.status.value}")
        lines.append("")

        # 推理链
        if result.reasoning_chain:
            lines.append("## 推理链")
            for step in result.reasoning_chain:
                lines.append(f"- 步骤 {step.get('step', '?')}: {step}")
            lines.append("")

        # 结论
        if result.conclusions:
            lines.append("## 结论")
            for conclusion in result.conclusions:
                lines.append(f"- {conclusion}")
            lines.append("")

        # 证据
        if result.evidence:
            lines.append("## 证据")
            for evidence in result.evidence:
                lines.append(f"- {evidence}")

        return "\n".join(lines)


# 全局实例
_enhanced_engine: Optional[EnhancedInferenceEngine] = None


def get_enhanced_inference_engine() -> EnhancedInferenceEngine:
    """获取全局增强推理引擎"""
    global _enhanced_engine
    if _enhanced_engine is None:
        _enhanced_engine = EnhancedInferenceEngine()
        _enhanced_engine.load_defaults()
    return _enhanced_engine