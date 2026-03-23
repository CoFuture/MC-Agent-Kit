"""
智能推理引擎模块

提供基于知识图谱的推理、规则推理、因果推理和推理路径可视化。
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Callable

from .knowledge_graph import (
    GraphNode,
    GraphEdge,
    GraphPath,
    KnowledgeGraph,
    NodeType,
    RelationType,
    get_knowledge_graph,
)


class InferenceType(Enum):
    """推理类型"""
    DEDUCTIVE = "deductive"       # 演绎推理
    INDUCTIVE = "inductive"       # 归纳推理
    ABDUCTIVE = "abductive"       # 溯因推理
    ANALOGICAL = "analogical"     # 类比推理
    CAUSAL = "causal"             # 因果推理


class InferenceStatus(Enum):
    """推理状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class RuleType(Enum):
    """规则类型"""
    IF_THEN = "if_then"           # 如果...那么
    IMPLIES = "implies"           # 蕴含
    EQUIVALENT = "equivalent"     # 等价
    EXCLUDES = "excludes"         # 排斥
    REQUIRES = "requires"         # 要求


@dataclass
class InferenceRule:
    """推理规则"""
    id: str
    name: str
    rule_type: RuleType
    conditions: list[dict[str, Any]]  # 条件列表
    conclusions: list[dict[str, Any]]  # 结论列表
    confidence: float = 1.0
    priority: int = 0
    description: str = ""
    source: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "rule_type": self.rule_type.value,
            "conditions": self.conditions,
            "conclusions": self.conclusions,
            "confidence": self.confidence,
            "priority": self.priority,
            "description": self.description,
            "source": self.source,
            "created_at": self.created_at,
        }


@dataclass
class InferenceResult:
    """推理结果"""
    inference_type: InferenceType
    conclusions: list[dict[str, Any]]
    confidence: float
    reasoning_chain: list[dict[str, Any]]
    evidence: list[str]
    execution_time: float
    status: InferenceStatus

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "inference_type": self.inference_type.value,
            "conclusions": self.conclusions,
            "confidence": self.confidence,
            "reasoning_chain": self.reasoning_chain,
            "evidence": self.evidence,
            "execution_time": self.execution_time,
            "status": self.status.value,
        }


@dataclass
class CausalChain:
    """因果链"""
    cause: str
    effect: str
    intermediate_steps: list[str]
    strength: float
    evidence: list[str]

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "cause": self.cause,
            "effect": self.effect,
            "intermediate_steps": self.intermediate_steps,
            "strength": self.strength,
            "evidence": self.evidence,
        }


@dataclass
class InferenceContext:
    """推理上下文"""
    query: str
    facts: dict[str, Any] = field(default_factory=dict)
    goals: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    timeout: float = 5.0
    max_depth: int = 5

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "facts": self.facts,
            "goals": self.goals,
            "constraints": self.constraints,
            "timeout": self.timeout,
            "max_depth": self.max_depth,
        }


class RuleEngine:
    """规则推理引擎

    基于规则的推理系统。

    使用示例:
        engine = RuleEngine()
        engine.add_rule(InferenceRule(
            id="r1",
            name="实体创建规则",
            rule_type=RuleType.IF_THEN,
            conditions=[{"type": "api", "name": "CreateEntity"}],
            conclusions=[{"suggestion": "需要调用 SetEntityPos 设置位置"}],
        ))
        results = engine.infer(facts)
    """

    def __init__(self) -> None:
        """初始化规则引擎"""
        self._rules: dict[str, InferenceRule] = {}
        self._rule_index: dict[RuleType, list[str]] = defaultdict(list)
        self._lock = threading.RLock()

    def add_rule(self, rule: InferenceRule) -> None:
        """添加规则"""
        with self._lock:
            self._rules[rule.id] = rule
            self._rule_index[rule.rule_type].append(rule.id)

    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        with self._lock:
            if rule_id in self._rules:
                rule = self._rules[rule_id]
                self._rule_index[rule.rule_type].remove(rule_id)
                del self._rules[rule_id]
                return True
            return False

    def get_rule(self, rule_id: str) -> Optional[InferenceRule]:
        """获取规则"""
        return self._rules.get(rule_id)

    def get_rules_by_type(self, rule_type: RuleType) -> list[InferenceRule]:
        """按类型获取规则"""
        rule_ids = self._rule_index.get(rule_type, [])
        return [self._rules[rid] for rid in rule_ids if rid in self._rules]

    def infer(
        self,
        facts: dict[str, Any],
        max_iterations: int = 100,
    ) -> InferenceResult:
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
                self._rules.values(),
                key=lambda r: r.priority,
                reverse=True,
            )

            for rule in sorted_rules:
                # 检查条件是否满足
                conditions_met = self._check_conditions(
                    rule.conditions,
                    derived_facts,
                )

                if conditions_met:
                    # 应用结论
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

                            # 更新派生事实
                            if "fact" in conclusion:
                                derived_facts.update(conclusion["fact"])
                                new_facts_derived = True

        execution_time = time.time() - start_time
        confidence = self._calculate_confidence(reasoning_chain)

        return InferenceResult(
            inference_type=InferenceType.DEDUCTIVE,
            conclusions=conclusions,
            confidence=confidence,
            reasoning_chain=reasoning_chain,
            evidence=evidence,
            execution_time=execution_time,
            status=InferenceStatus.COMPLETED,
        )

    def _check_conditions(
        self,
        conditions: list[dict[str, Any]],
        facts: dict[str, Any],
    ) -> bool:
        """检查条件是否满足"""
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

    def _calculate_confidence(
        self,
        reasoning_chain: list[dict[str, Any]],
    ) -> float:
        """计算置信度"""
        if not reasoning_chain:
            return 0.0

        total = sum(step.get("confidence", 1.0) for step in reasoning_chain)
        return total / len(reasoning_chain)

    def load_builtin_rules(self) -> None:
        """加载内置规则"""
        # 实体创建规则
        self.add_rule(InferenceRule(
            id="entity_create_pos",
            name="实体创建需要设置位置",
            rule_type=RuleType.IF_THEN,
            conditions=[{"type": "api", "name": "CreateEngineEntity"}],
            conclusions=[
                {"suggestion": "创建实体后需要调用 SetEngineEntityPos 设置位置"},
                {"related_api": "SetEngineEntityPos"},
            ],
            confidence=0.95,
            priority=10,
        ))

        # 事件监听规则
        self.add_rule(InferenceRule(
            id="event_listener",
            name="事件监听需要注册",
            rule_type=RuleType.IF_THEN,
            conditions=[{"type": "event", "name": "OnServerChat"}],
            conclusions=[
                {"suggestion": "需要使用 ListenEvent 注册事件监听"},
                {"related_api": "ListenEvent"},
            ],
            confidence=0.95,
            priority=10,
        ))

        # 物品创建规则
        self.add_rule(InferenceRule(
            id="item_register",
            name="物品需要注册",
            rule_type=RuleType.REQUIRES,
            conditions=[{"type": "api", "name": "CreateEngineItem"}],
            conclusions=[
                {"suggestion": "自定义物品需要在 mod.json 中注册"},
                {"required": "mod.json 配置"},
            ],
            confidence=0.9,
            priority=9,
        ))


class GraphInferenceEngine:
    """图谱推理引擎

    基于知识图谱进行推理。
    """

    def __init__(
        self,
        graph: Optional[KnowledgeGraph] = None,
    ) -> None:
        """初始化图谱推理引擎"""
        self._graph = graph or get_knowledge_graph()
        self._lock = threading.RLock()

    def infer_related_apis(
        self,
        api_name: str,
        max_depth: int = 3,
        min_strength: float = 0.3,
    ) -> InferenceResult:
        """推断相关 API"""
        start_time = time.time()

        node = self._graph.get_node_by_name(api_name)
        if not node:
            return InferenceResult(
                inference_type=InferenceType.ANALOGICAL,
                conclusions=[],
                confidence=0.0,
                reasoning_chain=[],
                evidence=[],
                execution_time=time.time() - start_time,
                status=InferenceStatus.FAILED,
            )

        conclusions: list[dict[str, Any]] = []
        reasoning_chain: list[dict[str, Any]] = []
        evidence: list[str] = []

        # 获取邻居节点
        visited: set[str] = {node.id}
        frontier: list[tuple[str, int, float]] = [(node.id, 0, 1.0)]

        while frontier:
            current_id, depth, cumulative_strength = frontier.pop(0)

            if depth >= max_depth:
                continue

            neighbors = self._graph.get_neighbors(current_id, min_strength=min_strength)

            for neighbor, edge in neighbors:
                if neighbor.id in visited:
                    continue

                visited.add(neighbor.id)
                new_strength = cumulative_strength * edge.strength

                if neighbor.type == NodeType.API:
                    conclusions.append({
                        "api_name": neighbor.name,
                        "relation": edge.relation.value,
                        "strength": new_strength,
                        "path_length": depth + 1,
                    })
                    evidence.append(f"通过 {edge.relation.value} 关系关联")

                reasoning_chain.append({
                    "step": depth + 1,
                    "from": current_id,
                    "to": neighbor.id,
                    "relation": edge.relation.value,
                    "strength": edge.strength,
                })

                frontier.append((neighbor.id, depth + 1, new_strength))

        # 按强度排序
        conclusions.sort(key=lambda x: x.get("strength", 0), reverse=True)

        execution_time = time.time() - start_time
        confidence = min(1.0, len(conclusions) * 0.1 + 0.5)

        return InferenceResult(
            inference_type=InferenceType.ANALOGICAL,
            conclusions=conclusions,
            confidence=confidence,
            reasoning_chain=reasoning_chain,
            evidence=evidence,
            execution_time=execution_time,
            status=InferenceStatus.COMPLETED,
        )

    def infer_api_usage(
        self,
        api_name: str,
    ) -> InferenceResult:
        """推断 API 使用方式"""
        start_time = time.time()

        node = self._graph.get_node_by_name(api_name)
        if not node:
            return InferenceResult(
                inference_type=InferenceType.DEDUCTIVE,
                conclusions=[],
                confidence=0.0,
                reasoning_chain=[],
                evidence=[],
                execution_time=time.time() - start_time,
                status=InferenceStatus.FAILED,
            )

        conclusions: list[dict[str, Any]] = []
        reasoning_chain: list[dict[str, Any]] = []
        evidence: list[str] = []

        # 从节点属性推断
        if node.properties:
            # 参数推断
            params = node.properties.get("parameters", [])
            if params:
                conclusions.append({
                    "type": "parameters",
                    "values": params,
                    "description": "API 参数",
                })
                evidence.append("从 API 定义获取参数")

            # 返回值推断
            return_type = node.properties.get("return_type")
            if return_type:
                conclusions.append({
                    "type": "return_type",
                    "value": return_type,
                    "description": "返回值类型",
                })
                evidence.append("从 API 定义获取返回值")

            # 作用域推断
            scope = node.properties.get("scope")
            if scope:
                conclusions.append({
                    "type": "scope",
                    "value": scope,
                    "description": "运行作用域",
                })
                evidence.append("从 API 定义获取作用域")

        # 从关系推断
        edges = self._graph.get_outgoing_edges(node.id)
        for edge in edges:
            target = self._graph.get_node(edge.target_id)
            if target:
                if edge.relation == RelationType.RETURNS:
                    conclusions.append({
                        "type": "returns",
                        "value": target.name,
                        "description": "返回值",
                    })
                    evidence.append(f"返回 {target.name}")

                elif edge.relation == RelationType.TAKES:
                    conclusions.append({
                        "type": "parameter",
                        "value": target.name,
                        "description": "参数",
                    })
                    evidence.append(f"接受参数 {target.name}")

        reasoning_chain.append({
            "step": 1,
            "node": api_name,
            "conclusions_count": len(conclusions),
        })

        execution_time = time.time() - start_time
        confidence = 0.9 if conclusions else 0.0

        return InferenceResult(
            inference_type=InferenceType.DEDUCTIVE,
            conclusions=conclusions,
            confidence=confidence,
            reasoning_chain=reasoning_chain,
            evidence=evidence,
            execution_time=execution_time,
            status=InferenceStatus.COMPLETED,
        )

    def infer_dependencies(
        self,
        api_name: str,
    ) -> InferenceResult:
        """推断 API 依赖"""
        start_time = time.time()

        node = self._graph.get_node_by_name(api_name)
        if not node:
            return InferenceResult(
                inference_type=InferenceType.CAUSAL,
                conclusions=[],
                confidence=0.0,
                reasoning_chain=[],
                evidence=[],
                execution_time=time.time() - start_time,
                status=InferenceStatus.FAILED,
            )

        conclusions: list[dict[str, Any]] = []
        reasoning_chain: list[dict[str, Any]] = []
        evidence: list[str] = []

        # 查找依赖路径
        paths = self._graph.find_paths(
            node.id,
            "",  # 空目标表示查找所有路径
            max_depth=3,
        )

        dependencies: set[str] = set()
        for path in paths[:10]:  # 限制路径数量
            for edge in path.edges:
                if edge.relation in (
                    RelationType.DEPENDS_ON,
                    RelationType.CALLS,
                    RelationType.REQUIRES,
                ):
                    target = self._graph.get_node(edge.target_id)
                    if target and target.id != node.id:
                        dependencies.add(target.name)
                        evidence.append(f"依赖 {target.name} ({edge.relation.value})")

        for dep in sorted(dependencies):
            conclusions.append({
                "type": "dependency",
                "name": dep,
            })

        reasoning_chain.append({
            "step": 1,
            "api": api_name,
            "dependencies_found": len(dependencies),
        })

        execution_time = time.time() - start_time
        confidence = 0.8 if dependencies else 0.0

        return InferenceResult(
            inference_type=InferenceType.CAUSAL,
            conclusions=conclusions,
            confidence=confidence,
            reasoning_chain=reasoning_chain,
            evidence=evidence,
            execution_time=execution_time,
            status=InferenceStatus.COMPLETED,
        )


class CausalInferenceEngine:
    """因果推理引擎

    推断因果关系。
    """

    def __init__(self) -> None:
        """初始化因果推理引擎"""
        self._causal_rules: dict[str, CausalChain] = {}
        self._lock = threading.RLock()

    def add_causal_chain(self, chain: CausalChain) -> None:
        """添加因果链"""
        with self._lock:
            key = f"{chain.cause}->{chain.effect}"
            self._causal_rules[key] = chain

    def infer_cause(
        self,
        effect: str,
        context: Optional[dict[str, Any]] = None,
    ) -> InferenceResult:
        """推断原因"""
        start_time = time.time()

        conclusions: list[dict[str, Any]] = []
        reasoning_chain: list[dict[str, Any]] = []
        evidence: list[str] = []

        # 查找匹配的因果链
        for key, chain in self._causal_rules.items():
            if chain.effect == effect or effect in chain.effect:
                conclusions.append({
                    "type": "cause",
                    "cause": chain.cause,
                    "strength": chain.strength,
                    "intermediate_steps": chain.intermediate_steps,
                })
                evidence.extend(chain.evidence)

        reasoning_chain.append({
            "step": 1,
            "effect": effect,
            "causes_found": len(conclusions),
        })

        execution_time = time.time() - start_time
        confidence = max((c.get("strength", 0) for c in conclusions), default=0.0)

        return InferenceResult(
            inference_type=InferenceType.ABDUCTIVE,
            conclusions=conclusions,
            confidence=confidence,
            reasoning_chain=reasoning_chain,
            evidence=evidence,
            execution_time=execution_time,
            status=InferenceStatus.COMPLETED,
        )

    def infer_effect(
        self,
        cause: str,
        context: Optional[dict[str, Any]] = None,
    ) -> InferenceResult:
        """推断结果"""
        start_time = time.time()

        conclusions: list[dict[str, Any]] = []
        reasoning_chain: list[dict[str, Any]] = []
        evidence: list[str] = []

        # 查找匹配的因果链
        for key, chain in self._causal_rules.items():
            if chain.cause == cause or cause in chain.cause:
                conclusions.append({
                    "type": "effect",
                    "effect": chain.effect,
                    "strength": chain.strength,
                    "intermediate_steps": chain.intermediate_steps,
                })
                evidence.extend(chain.evidence)

        reasoning_chain.append({
            "step": 1,
            "cause": cause,
            "effects_found": len(conclusions),
        })

        execution_time = time.time() - start_time
        confidence = max((c.get("strength", 0) for c in conclusions), default=0.0)

        return InferenceResult(
            inference_type=InferenceType.DEDUCTIVE,
            conclusions=conclusions,
            confidence=confidence,
            reasoning_chain=reasoning_chain,
            evidence=evidence,
            execution_time=execution_time,
            status=InferenceStatus.COMPLETED,
        )

    def load_builtin_causal_rules(self) -> None:
        """加载内置因果规则"""
        # API 调用错误
        self.add_causal_chain(CausalChain(
            cause="未注册事件监听",
            effect="事件回调不执行",
            intermediate_steps=["事件触发", "无监听器", "回调未调用"],
            strength=0.95,
            evidence=["常见错误模式"],
        ))

        # 配置错误
        self.add_causal_chain(CausalChain(
            cause="mod.json 配置错误",
            effect="Addon 加载失败",
            intermediate_steps=["解析配置", "验证失败", "加载中止"],
            strength=0.9,
            evidence=["配置验证"],
        ))

        # 权限错误
        self.add_causal_chain(CausalChain(
            cause="客户端调用服务端 API",
            effect="API 调用失败",
            intermediate_steps=["作用域检查", "权限验证失败"],
            strength=0.85,
            evidence=["作用域限制"],
        ))


class InferenceEngine:
    """综合推理引擎

    整合规则推理、图谱推理和因果推理。

    使用示例:
        engine = InferenceEngine()
        engine.load_defaults()
        result = engine.infer(context)
    """

    def __init__(
        self,
        graph: Optional[KnowledgeGraph] = None,
    ) -> None:
        """初始化推理引擎"""
        self._rule_engine = RuleEngine()
        self._graph_engine = GraphInferenceEngine(graph)
        self._causal_engine = CausalInferenceEngine()
        self._lock = threading.RLock()

    def load_defaults(self) -> None:
        """加载默认配置"""
        self._rule_engine.load_builtin_rules()
        self._causal_engine.load_builtin_causal_rules()

    def infer(
        self,
        context: InferenceContext,
    ) -> InferenceResult:
        """执行推理"""
        start_time = time.time()

        # 确定推理类型
        inference_type = self._determine_inference_type(context)

        # 根据推理类型选择引擎
        if inference_type == InferenceType.DEDUCTIVE:
            result = self._rule_engine.infer(context.facts)
        elif inference_type == InferenceType.ANALOGICAL:
            api_name = context.facts.get("api_name", "")
            result = self._graph_engine.infer_related_apis(api_name)
        elif inference_type == InferenceType.ABDUCTIVE:
            effect = context.facts.get("effect", "")
            result = self._causal_engine.infer_cause(effect)
        elif inference_type == InferenceType.CAUSAL:
            cause = context.facts.get("cause", "")
            result = self._causal_engine.infer_effect(cause)
        else:
            # 默认使用规则推理
            result = self._rule_engine.infer(context.facts)

        # 检查超时
        execution_time = time.time() - start_time
        if execution_time > context.timeout:
            result.status = InferenceStatus.TIMEOUT

        return result

    def _determine_inference_type(
        self,
        context: InferenceContext,
    ) -> InferenceType:
        """确定推理类型"""
        query_lower = context.query.lower()

        # 检查因果关键词
        causal_keywords = ["为什么", "原因", "导致", "why", "cause", "because"]
        if any(kw in query_lower for kw in causal_keywords):
            return InferenceType.ABDUCTIVE

        # 检查相关关键词
        related_keywords = ["相关", "类似", "similar", "related", "关联"]
        if any(kw in query_lower for kw in related_keywords):
            return InferenceType.ANALOGICAL

        # 检查因果推断关键词
        effect_keywords = ["会怎样", "结果", "效果", "effect", "result"]
        if any(kw in query_lower for kw in effect_keywords):
            return InferenceType.CAUSAL

        # 默认演绎推理
        return InferenceType.DEDUCTIVE

    def infer_api_relations(
        self,
        api_name: str,
        max_depth: int = 3,
    ) -> InferenceResult:
        """推断 API 关系"""
        return self._graph_engine.infer_related_apis(api_name, max_depth)

    def infer_api_usage(self, api_name: str) -> InferenceResult:
        """推断 API 使用方式"""
        return self._graph_engine.infer_api_usage(api_name)

    def infer_api_dependencies(self, api_name: str) -> InferenceResult:
        """推断 API 依赖"""
        return self._graph_engine.infer_dependencies(api_name)

    def infer_error_cause(self, error: str) -> InferenceResult:
        """推断错误原因"""
        return self._causal_engine.infer_cause(error)

    def add_rule(self, rule: InferenceRule) -> None:
        """添加规则"""
        self._rule_engine.add_rule(rule)

    def add_causal_chain(self, chain: CausalChain) -> None:
        """添加因果链"""
        self._causal_engine.add_causal_chain(chain)

    def visualize_reasoning(
        self,
        result: InferenceResult,
    ) -> str:
        """可视化推理过程"""
        lines = ["# 推理过程"]
        lines.append(f"**推理类型**: {result.inference_type.value}")
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
_engine: Optional[InferenceEngine] = None


def get_inference_engine() -> InferenceEngine:
    """获取全局推理引擎"""
    global _engine
    if _engine is None:
        _engine = InferenceEngine()
        _engine.load_defaults()
    return _engine


def infer(context: InferenceContext) -> InferenceResult:
    """便捷函数：执行推理"""
    return get_inference_engine().infer(context)


def infer_api_relations(api_name: str, max_depth: int = 3) -> InferenceResult:
    """便捷函数：推断 API 关系"""
    return get_inference_engine().infer_api_relations(api_name, max_depth)