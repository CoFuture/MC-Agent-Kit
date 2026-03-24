"""
增强因果推理引擎模块

提供增强的因果推理、错误诊断和解决方案推荐。
"""

from __future__ import annotations

import re
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class CausalType(Enum):
    """因果类型"""
    DIRECT = "direct"           # 直接因果
    INDIRECT = "indirect"       # 间接因果
    CONTRIBUTORY = "contributory"  # 贡献性因果
    CONDITIONAL = "conditional"  # 条件性因果


class DiagnosticSeverity(Enum):
    """诊断严重程度"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class CausalRule:
    """因果规则"""
    id: str
    cause: str
    effect: str
    causal_type: CausalType
    strength: float = 0.8
    conditions: list[str] = field(default_factory=list)
    intermediate_steps: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    solutions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "cause": self.cause,
            "effect": self.effect,
            "causal_type": self.causal_type.value,
            "strength": self.strength,
            "conditions": self.conditions,
            "intermediate_steps": self.intermediate_steps,
            "evidence": self.evidence,
            "solutions": self.solutions,
            "tags": self.tags,
        }

    def matches_effect(self, effect: str) -> bool:
        """检查是否匹配效果"""
        # 精确匹配
        if effect == self.effect:
            return True
        # 包含匹配
        if effect in self.effect or self.effect in effect:
            return True
        # 正则匹配
        try:
            if re.search(self.effect, effect, re.IGNORECASE):
                return True
        except re.error:
            pass
        return False

    def matches_cause(self, cause: str) -> bool:
        """检查是否匹配原因"""
        if cause == self.cause:
            return True
        if cause in self.cause or self.cause in cause:
            return True
        try:
            if re.search(self.cause, cause, re.IGNORECASE):
                return True
        except re.error:
            pass
        return False


@dataclass
class CausalChainResult:
    """因果链结果"""
    root_cause: str
    effect: str
    chain: list[dict[str, Any]]
    total_strength: float
    depth: int
    evidence: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_cause": self.root_cause,
            "effect": self.effect,
            "chain": self.chain,
            "total_strength": self.total_strength,
            "depth": self.depth,
            "evidence": self.evidence,
        }


@dataclass
class DiagnosticResult:
    """诊断结果"""
    error_type: str
    error_message: str
    severity: DiagnosticSeverity
    root_causes: list[dict[str, Any]]
    solutions: list[dict[str, Any]]
    confidence: float
    related_docs: list[str]
    execution_time: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "severity": self.severity.value,
            "root_causes": self.root_causes,
            "solutions": self.solutions,
            "confidence": self.confidence,
            "related_docs": self.related_docs,
            "execution_time": self.execution_time,
        }


class EnhancedCausalEngine:
    """
    增强因果推理引擎

    支持多跳因果推理、错误诊断和解决方案推荐。

    使用示例:
        engine = EnhancedCausalEngine()
        engine.load_builtin_rules()
        result = engine.diagnose_error("KeyError: 'speed'")
    """

    def __init__(self) -> None:
        self._rules: dict[str, CausalRule] = {}
        self._effect_index: dict[str, list[str]] = defaultdict(list)
        self._cause_index: dict[str, list[str]] = defaultdict(list)
        self._solution_cache: dict[str, list[str]] = {}
        self._lock = threading.RLock()

    def add_rule(self, rule: CausalRule) -> None:
        """添加因果规则"""
        with self._lock:
            self._rules[rule.id] = rule
            self._effect_index[rule.effect.lower()].append(rule.id)
            self._cause_index[rule.cause.lower()].append(rule.id)

    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        with self._lock:
            if rule_id not in self._rules:
                return False

            rule = self._rules[rule_id]

            # 从索引中移除
            effect_key = rule.effect.lower()
            cause_key = rule.cause.lower()

            if rule_id in self._effect_index[effect_key]:
                self._effect_index[effect_key].remove(rule_id)
            if rule_id in self._cause_index[cause_key]:
                self._cause_index[cause_key].remove(rule_id)

            del self._rules[rule_id]
            return True

    def get_rule(self, rule_id: str) -> Optional[CausalRule]:
        """获取规则"""
        return self._rules.get(rule_id)

    def find_causes(
        self,
        effect: str,
        max_depth: int = 3,
        min_strength: float = 0.3,
    ) -> list[CausalChainResult]:
        """查找原因（支持多跳）"""
        results: list[CausalChainResult] = []

        # 直接原因
        direct_causes = self._find_direct_causes(effect)

        for rule_id in direct_causes:
            rule = self._rules.get(rule_id)
            if not rule or rule.strength < min_strength:
                continue

            results.append(CausalChainResult(
                root_cause=rule.cause,
                effect=effect,
                chain=[{
                    "cause": rule.cause,
                    "effect": rule.effect,
                    "strength": rule.strength,
                }],
                total_strength=rule.strength,
                depth=1,
                evidence=rule.evidence,
            ))

        # 多跳推理
        if max_depth > 1:
            multi_hop_results = self._multi_hop_cause_search(
                effect, max_depth, min_strength
            )
            results.extend(multi_hop_results)

        # 按强度排序
        results.sort(key=lambda x: x.total_strength, reverse=True)
        return results[:10]

    def _find_direct_causes(self, effect: str) -> list[str]:
        """查找直接原因"""
        effect_lower = effect.lower()
        rule_ids = set()

        # 精确匹配
        rule_ids.update(self._effect_index.get(effect_lower, []))

        # 模糊匹配
        for effect_key, ids in self._effect_index.items():
            if effect_lower in effect_key or effect_key in effect_lower:
                rule_ids.update(ids)

        return list(rule_ids)

    def _multi_hop_cause_search(
        self,
        effect: str,
        max_depth: int,
        min_strength: float,
    ) -> list[CausalChainResult]:
        """多跳因果搜索"""
        results: list[CausalChainResult] = []

        # BFS 搜索
        queue: list[tuple[str, float, list[dict[str, Any]], list[str], int]] = [
            (effect, 1.0, [], [], 0)
        ]
        visited: set[str] = {effect}

        while queue:
            current_effect, cum_strength, chain, evidence, depth = queue.pop(0)

            if depth >= max_depth:
                continue

            causes = self._find_direct_causes(current_effect)

            for rule_id in causes:
                rule = self._rules.get(rule_id)
                if not rule:
                    continue

                new_strength = cum_strength * rule.strength
                if new_strength < min_strength:
                    continue

                new_chain = chain + [{
                    "cause": rule.cause,
                    "effect": rule.effect,
                    "strength": rule.strength,
                }]
                new_evidence = evidence + rule.evidence

                if rule.cause not in visited:
                    visited.add(rule.cause)
                    results.append(CausalChainResult(
                        root_cause=rule.cause,
                        effect=effect,
                        chain=new_chain,
                        total_strength=new_strength,
                        depth=depth + 1,
                        evidence=new_evidence,
                    ))
                    queue.append((rule.cause, new_strength, new_chain, new_evidence, depth + 1))

        return results

    def find_effects(
        self,
        cause: str,
        max_depth: int = 3,
        min_strength: float = 0.3,
    ) -> list[CausalChainResult]:
        """查找结果（支持多跳）"""
        results: list[CausalChainResult] = []

        # 直接结果
        direct_effects = self._find_direct_effects(cause)

        for rule_id in direct_effects:
            rule = self._rules.get(rule_id)
            if not rule or rule.strength < min_strength:
                continue

            results.append(CausalChainResult(
                root_cause=cause,
                effect=rule.effect,
                chain=[{
                    "cause": rule.cause,
                    "effect": rule.effect,
                    "strength": rule.strength,
                }],
                total_strength=rule.strength,
                depth=1,
                evidence=rule.evidence,
            ))

        # 多跳推理
        if max_depth > 1:
            queue: list[tuple[str, float, list[dict[str, Any]], list[str], int]] = [
                (cause, 1.0, [], [], 0)
            ]
            visited: set[str] = {cause}

            while queue:
                current_cause, cum_strength, chain, evidence, depth = queue.pop(0)

                if depth >= max_depth:
                    continue

                effects = self._find_direct_effects(current_cause)

                for rule_id in effects:
                    rule = self._rules.get(rule_id)
                    if not rule:
                        continue

                    new_strength = cum_strength * rule.strength
                    if new_strength < min_strength:
                        continue

                    new_chain = chain + [{
                        "cause": rule.cause,
                        "effect": rule.effect,
                        "strength": rule.strength,
                    }]
                    new_evidence = evidence + rule.evidence

                    if rule.effect not in visited:
                        visited.add(rule.effect)
                        results.append(CausalChainResult(
                            root_cause=cause,
                            effect=rule.effect,
                            chain=new_chain,
                            total_strength=new_strength,
                            depth=depth + 1,
                            evidence=new_evidence,
                        ))
                        queue.append((rule.effect, new_strength, new_chain, new_evidence, depth + 1))

        results.sort(key=lambda x: x.total_strength, reverse=True)
        return results[:10]

    def _find_direct_effects(self, cause: str) -> list[str]:
        """查找直接结果"""
        cause_lower = cause.lower()
        rule_ids = set()

        rule_ids.update(self._cause_index.get(cause_lower, []))

        for cause_key, ids in self._cause_index.items():
            if cause_lower in cause_key or cause_key in cause_lower:
                rule_ids.update(ids)

        return list(rule_ids)

    def diagnose_error(
        self,
        error_message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> DiagnosticResult:
        """诊断错误"""
        start_time = time.time()

        # 提取错误类型
        error_type = self._extract_error_type(error_message)

        # 查找原因
        causal_results = self.find_causes(error_message, max_depth=3)

        # 构建根本原因列表
        root_causes: list[dict[str, Any]] = []
        solutions: list[dict[str, Any]] = []
        related_docs: list[str] = []

        for result in causal_results[:5]:
            root_causes.append({
                "cause": result.root_cause,
                "strength": result.total_strength,
                "depth": result.depth,
                "evidence": result.evidence[:3],
            })

            # 获取解决方案
            rule = self._find_rule_by_cause(result.root_cause)
            if rule:
                for sol in rule.solutions:
                    if sol not in [s.get("description") for s in solutions]:
                        solutions.append({
                            "description": sol,
                            "confidence": result.total_strength,
                        })

        # 确定严重程度
        severity = self._determine_severity(error_type, error_message)

        # 计算置信度
        confidence = max((r.get("strength", 0) for r in root_causes), default=0.0)

        execution_time = time.time() - start_time

        return DiagnosticResult(
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            root_causes=root_causes,
            solutions=solutions,
            confidence=confidence,
            related_docs=related_docs,
            execution_time=execution_time,
        )

    def _extract_error_type(self, error_message: str) -> str:
        """提取错误类型"""
        # Python 错误类型
        patterns = [
            r"(\w+Error):",
            r"(\w+Exception):",
            r"(\w+Warning):",
            r"error[:\s]+(\w+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                return match.group(1)

        return "Unknown"

    def _find_rule_by_cause(self, cause: str) -> Optional[CausalRule]:
        """根据原因查找规则"""
        for rule in self._rules.values():
            if rule.cause == cause:
                return rule
        return None

    def _determine_severity(
        self,
        error_type: str,
        error_message: str,
    ) -> DiagnosticSeverity:
        """确定严重程度"""
        critical_keywords = ["memory", "segfault", "crash", "fatal"]
        error_keywords = ["error", "failed", "invalid", "not found"]

        message_lower = error_message.lower()

        if any(kw in message_lower for kw in critical_keywords):
            return DiagnosticSeverity.CRITICAL

        if error_type.endswith("Error"):
            return DiagnosticSeverity.ERROR

        if error_type.endswith("Warning"):
            return DiagnosticSeverity.WARNING

        if any(kw in message_lower for kw in error_keywords):
            return DiagnosticSeverity.ERROR

        return DiagnosticSeverity.INFO

    def load_builtin_rules(self) -> None:
        """加载内置因果规则"""
        # Python 错误规则
        self.add_rule(CausalRule(
            id="key_error",
            cause="变量/字典键不存在",
            effect="KeyError",
            causal_type=CausalType.DIRECT,
            strength=0.95,
            intermediate_steps=["访问字典", "键不存在", "抛出异常"],
            evidence=["常见错误模式"],
            solutions=[
                "使用 dict.get(key, default) 方法",
                "检查键是否存在: if key in dict",
                "使用 try-except 捕获异常",
            ],
            tags=["python", "error"],
        ))

        self.add_rule(CausalRule(
            id="attribute_error",
            cause="对象没有该属性",
            effect="AttributeError",
            causal_type=CausalType.DIRECT,
            strength=0.95,
            intermediate_steps=["访问属性", "属性不存在", "抛出异常"],
            evidence=["常见错误模式"],
            solutions=[
                "检查对象类型: type(obj)",
                "使用 hasattr(obj, attr) 检查",
                "检查是否为 None",
            ],
            tags=["python", "error"],
        ))

        self.add_rule(CausalRule(
            id="import_error",
            cause="模块不存在或路径错误",
            effect="ImportError",
            causal_type=CausalType.DIRECT,
            strength=0.9,
            intermediate_steps=["导入模块", "模块未找到", "抛出异常"],
            evidence=["常见错误模式"],
            solutions=[
                "检查模块名称拼写",
                "确认模块已安装: pip install module",
                "检查 Python 路径",
            ],
            tags=["python", "error"],
        ))

        # ModSDK 特定规则
        self.add_rule(CausalRule(
            id="event_not_triggered",
            cause="未注册事件监听",
            effect="事件回调不执行",
            causal_type=CausalType.DIRECT,
            strength=0.95,
            intermediate_steps=["事件触发", "无监听器", "回调未调用"],
            evidence=["ModSDK 常见问题"],
            solutions=[
                "使用 ListenEvent 注册事件监听",
                "检查事件名称是否正确",
                "确认回调函数签名正确",
            ],
            tags=["modsdk", "event"],
        ))

        self.add_rule(CausalRule(
            id="addon_load_failed",
            cause="mod.json 配置错误",
            effect="Addon 加载失败",
            causal_type=CausalType.DIRECT,
            strength=0.9,
            intermediate_steps=["解析配置", "验证失败", "加载中止"],
            evidence=["配置验证"],
            solutions=[
                "检查 mod.json 格式是否正确",
                "确认 UUID 和版本号有效",
                "验证脚本路径正确",
            ],
            tags=["modsdk", "config"],
        ))

        self.add_rule(CausalRule(
            id="api_call_failed",
            cause="客户端调用服务端 API",
            effect="API 调用失败",
            causal_type=CausalType.DIRECT,
            strength=0.85,
            intermediate_steps=["作用域检查", "权限验证失败"],
            evidence=["作用域限制"],
            solutions=[
                "检查 API 作用域要求",
                "在正确的端调用 API",
                "使用 GetMinecraftEnum().GetServerOrClient() 判断",
            ],
            tags=["modsdk", "scope"],
        ))

        self.add_rule(CausalRule(
            id="entity_not_found",
            cause="实体 ID 无效或实体已销毁",
            effect="GetEngineEntity 返回 None",
            causal_type=CausalType.DIRECT,
            strength=0.85,
            intermediate_steps=["查询实体", "实体不存在", "返回空"],
            evidence=["实体生命周期"],
            solutions=[
                "检查实体 ID 是否有效",
                "确认实体未被销毁",
                "使用 try-except 处理空值",
            ],
            tags=["modsdk", "entity"],
        ))

        self.add_rule(CausalRule(
            id="ui_create_failed",
            cause="UI 资源未加载",
            effect="CreateUI 失败",
            causal_type=CausalType.CONDITIONAL,
            strength=0.8,
            conditions=["资源包已加载"],
            intermediate_steps=["创建 UI", "资源检查", "创建失败"],
            evidence=["UI 资源加载"],
            solutions=[
                "确认 UI 资源在资源包中",
                "检查 UI 文件路径",
                "确保资源包正确加载",
            ],
            tags=["modsdk", "ui"],
        ))

        # 多跳因果规则
        self.add_rule(CausalRule(
            id="sync_data_failed_chain",
            cause="网络连接断开",
            effect="SyncData 调用失败",
            causal_type=CausalType.INDIRECT,
            strength=0.7,
            intermediate_steps=["网络断开", "数据同步请求", "同步失败"],
            evidence=["网络状态"],
            solutions=[
                "检查网络连接",
                "添加重连逻辑",
                "使用心跳检测",
            ],
            tags=["modsdk", "network"],
        ))

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            causal_types: dict[str, int] = defaultdict(int)
            tags: dict[str, int] = defaultdict(int)

            for rule in self._rules.values():
                causal_types[rule.causal_type.value] += 1
                for tag in rule.tags:
                    tags[tag] += 1

            return {
                "total_rules": len(self._rules),
                "causal_types": dict(causal_types),
                "tags": dict(tags),
                "effect_index_size": len(self._effect_index),
                "cause_index_size": len(self._cause_index),
            }


# 全局实例
_causal_engine: Optional[EnhancedCausalEngine] = None


def get_enhanced_causal_engine() -> EnhancedCausalEngine:
    """获取全局因果推理引擎"""
    global _causal_engine
    if _causal_engine is None:
        _causal_engine = EnhancedCausalEngine()
        _causal_engine.load_builtin_rules()
    return _causal_engine