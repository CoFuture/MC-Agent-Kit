"""
增强知识图谱模块

扩展节点类型（UI、网络、配置）、支持自定义关系和图谱版本管理。
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EnhancedNodeType(Enum):
    """增强节点类型"""
    # 原有类型
    API = "api"
    EVENT = "event"
    ENTITY = "entity"
    ITEM = "item"
    BLOCK = "block"
    COMPONENT = "component"
    MODULE = "module"
    PARAMETER = "parameter"
    RETURN_VALUE = "return_value"
    EXAMPLE = "example"
    CONCEPT = "concept"
    
    # 新增类型
    UI = "ui"                       # UI 组件
    UI_SCREEN = "ui_screen"         # UI 屏幕
    UI_CONTROL = "ui_control"       # UI 控件
    NETWORK = "network"             # 网络相关
    NETWORK_EVENT = "network_event" # 网络事件
    CONFIG = "config"               # 配置项
    CONFIG_FILE = "config_file"     # 配置文件
    ERROR = "error"                 # 错误类型
    ERROR_PATTERN = "error_pattern" # 错误模式
    SOLUTION = "solution"           # 解决方案
    BEST_PRACTICE = "best_practice" # 最佳实践
    WORKFLOW = "workflow"           # 工作流
    DATA_TYPE = "data_type"         # 数据类型


class EnhancedRelationType(Enum):
    """增强关系类型"""
    # 原有关系
    CALLS = "calls"
    TRIGGERS = "triggers"
    LISTENS = "listens"
    RETURNS = "returns"
    TAKES = "takes"
    BELONGS_TO = "belongs_to"
    DEPENDS_ON = "depends_on"
    RELATED_TO = "related_to"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    CONTAINS = "contains"
    USES = "uses"
    CREATES = "creates"
    MODIFIES = "modifies"
    EXAMPLE_OF = "example_of"
    SIMILAR_TO = "similar_to"
    
    # 新增关系
    # UI 相关
    RENDERS = "renders"             # 渲染 UI
    HANDLES_INPUT = "handles_input" # 处理输入
    UPDATES_UI = "updates_ui"       # 更新 UI
    
    # 网络相关
    SENDS = "sends"                 # 发送数据
    RECEIVES = "receives"           # 接收数据
    SYNCHRONIZES = "synchronizes"   # 同步数据
    
    # 配置相关
    CONFIGURES = "configures"       # 配置
    DEFINES = "defines"             # 定义
    VALIDATES = "validates"         # 验证
    
    # 错误诊断相关
    CAUSES = "causes"               # 导致错误
    FIXES = "fixes"                 # 修复
    PREVENTS = "prevents"           # 预防
    DIAGNOSES = "diagnoses"         # 诊断
    
    # 推理相关
    IMPLIES = "implies"             # 蕴含
    REQUIRES = "requires"           # 需要
    CONFLICTS_WITH = "conflicts_with"  # 冲突
    ALTERNATIVE_TO = "alternative_to"  # 替代方案


@dataclass
class GraphVersion:
    """图谱版本"""
    version: str
    created_at: float
    description: str = ""
    changes: list[str] = field(default_factory=list)
    checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "created_at": self.created_at,
            "description": self.description,
            "changes": self.changes,
            "checksum": self.checksum,
        }


@dataclass
class EnhancedGraphNode:
    """增强图谱节点"""
    id: str
    type: EnhancedNodeType
    name: str
    description: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    source: str = ""
    version: str = "1.0.0"
    confidence: float = 1.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "properties": self.properties,
            "tags": self.tags,
            "source": self.source,
            "version": self.version,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class EnhancedGraphEdge:
    """增强图谱边"""
    source_id: str
    target_id: str
    relation: EnhancedRelationType
    strength: float = 1.0
    confidence: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)
    evidence: str = ""
    custom_attributes: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation.value,
            "strength": self.strength,
            "confidence": self.confidence,
            "properties": self.properties,
            "evidence": self.evidence,
            "custom_attributes": self.custom_attributes,
            "created_at": self.created_at,
        }


@dataclass
class CustomRelation:
    """自定义关系"""
    name: str
    description: str
    source_types: list[EnhancedNodeType]
    target_types: list[EnhancedNodeType]
    properties_schema: dict[str, Any] = field(default_factory=dict)
    is_bidirectional: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "source_types": [t.value for t in self.source_types],
            "target_types": [t.value for t in self.target_types],
            "properties_schema": self.properties_schema,
            "is_bidirectional": self.is_bidirectional,
        }


class GraphVersionManager:
    """图谱版本管理器"""

    def __init__(self) -> None:
        self._versions: dict[str, GraphVersion] = {}
        self._current_version: str = "1.0.0"
        self._lock = threading.RLock()

    def create_version(
        self,
        version: str,
        description: str = "",
        changes: Optional[list[str]] = None,
    ) -> GraphVersion:
        """创建新版本"""
        with self._lock:
            gv = GraphVersion(
                version=version,
                created_at=time.time(),
                description=description,
                changes=changes or [],
            )
            self._versions[version] = gv
            self._current_version = version
            return gv

    def get_version(self, version: str) -> Optional[GraphVersion]:
        """获取版本"""
        return self._versions.get(version)

    def get_current_version(self) -> str:
        """获取当前版本"""
        return self._current_version

    def list_versions(self) -> list[GraphVersion]:
        """列出所有版本"""
        return sorted(
            self._versions.values(),
            key=lambda v: v.created_at,
            reverse=True,
        )

    def rollback(self, version: str) -> bool:
        """回滚到指定版本"""
        with self._lock:
            if version in self._versions:
                self._current_version = version
                return True
            return False


class EnhancedKnowledgeGraph:
    """
    增强知识图谱

    支持扩展节点类型、自定义关系和版本管理。

    使用示例:
        graph = EnhancedKnowledgeGraph()
        graph.add_ui_node("MainScreen", "主界面")
        graph.add_network_node("SyncEvent", "同步事件")
        graph.add_custom_relation(CustomRelation(...))
    """

    def __init__(self) -> None:
        """初始化增强知识图谱"""
        self._nodes: dict[str, EnhancedGraphNode] = {}
        self._edges: dict[str, list[EnhancedGraphEdge]] = defaultdict(list)
        self._reverse_edges: dict[str, list[EnhancedGraphEdge]] = defaultdict(list)
        self._name_index: dict[str, str] = {}
        self._type_index: dict[EnhancedNodeType, list[str]] = defaultdict(list)
        self._tag_index: dict[str, list[str]] = defaultdict(list)
        self._custom_relations: dict[str, CustomRelation] = {}
        self._version_manager = GraphVersionManager()
        self._lock = threading.RLock()
        self._stats_cache: Optional[dict[str, Any]] = None

    # ============ 自定义关系 ============

    def register_custom_relation(self, relation: CustomRelation) -> None:
        """注册自定义关系"""
        with self._lock:
            self._custom_relations[relation.name] = relation

    def get_custom_relation(self, name: str) -> Optional[CustomRelation]:
        """获取自定义关系"""
        return self._custom_relations.get(name)

    def list_custom_relations(self) -> list[CustomRelation]:
        """列出所有自定义关系"""
        return list(self._custom_relations.values())

    # ============ 节点操作 ============

    def add_node(self, node: EnhancedGraphNode) -> None:
        """添加节点"""
        with self._lock:
            self._nodes[node.id] = node
            self._name_index[node.name.lower()] = node.id
            self._type_index[node.type].append(node.id)
            for tag in node.tags:
                self._tag_index[tag.lower()].append(node.id)
            self._invalidate_cache()

    def add_api_node(
        self,
        name: str,
        description: str = "",
        properties: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
    ) -> EnhancedGraphNode:
        """添加 API 节点"""
        node = EnhancedGraphNode(
            id=f"api:{name}",
            type=EnhancedNodeType.API,
            name=name,
            description=description,
            properties=properties or {},
            tags=tags or [],
        )
        self.add_node(node)
        return node

    def add_ui_node(
        self,
        name: str,
        description: str = "",
        ui_type: str = "screen",
        properties: Optional[dict[str, Any]] = None,
    ) -> EnhancedGraphNode:
        """添加 UI 节点"""
        ui_node_type = EnhancedNodeType.UI_SCREEN if ui_type == "screen" else EnhancedNodeType.UI_CONTROL
        node = EnhancedGraphNode(
            id=f"ui:{name}",
            type=ui_node_type,
            name=name,
            description=description,
            properties=properties or {},
            tags=["ui", ui_type],
        )
        self.add_node(node)
        return node

    def add_network_node(
        self,
        name: str,
        description: str = "",
        event_type: str = "event",
        properties: Optional[dict[str, Any]] = None,
    ) -> EnhancedGraphNode:
        """添加网络节点"""
        net_type = EnhancedNodeType.NETWORK_EVENT if event_type == "event" else EnhancedNodeType.NETWORK
        node = EnhancedGraphNode(
            id=f"network:{name}",
            type=net_type,
            name=name,
            description=description,
            properties=properties or {},
            tags=["network", event_type],
        )
        self.add_node(node)
        return node

    def add_config_node(
        self,
        name: str,
        description: str = "",
        config_type: str = "item",
        properties: Optional[dict[str, Any]] = None,
    ) -> EnhancedGraphNode:
        """添加配置节点"""
        cfg_type = EnhancedNodeType.CONFIG_FILE if config_type == "file" else EnhancedNodeType.CONFIG
        node = EnhancedGraphNode(
            id=f"config:{name}",
            type=cfg_type,
            name=name,
            description=description,
            properties=properties or {},
            tags=["config", config_type],
        )
        self.add_node(node)
        return node

    def add_error_node(
        self,
        name: str,
        description: str = "",
        error_pattern: str = "",
        solutions: Optional[list[str]] = None,
    ) -> EnhancedGraphNode:
        """添加错误节点"""
        node = EnhancedGraphNode(
            id=f"error:{name}",
            type=EnhancedNodeType.ERROR,
            name=name,
            description=description,
            properties={
                "pattern": error_pattern,
                "solutions": solutions or [],
            },
            tags=["error"],
        )
        self.add_node(node)
        return node

    def add_solution_node(
        self,
        name: str,
        description: str = "",
        steps: Optional[list[str]] = None,
        related_errors: Optional[list[str]] = None,
    ) -> EnhancedGraphNode:
        """添加解决方案节点"""
        node = EnhancedGraphNode(
            id=f"solution:{name}",
            type=EnhancedNodeType.SOLUTION,
            name=name,
            description=description,
            properties={
                "steps": steps or [],
                "related_errors": related_errors or [],
            },
            tags=["solution"],
        )
        self.add_node(node)
        return node

    def get_node(self, node_id: str) -> Optional[EnhancedGraphNode]:
        """获取节点"""
        return self._nodes.get(node_id)

    def get_node_by_name(self, name: str) -> Optional[EnhancedGraphNode]:
        """通过名称获取节点"""
        node_id = self._name_index.get(name.lower())
        return self._nodes.get(node_id) if node_id else None

    def get_nodes_by_type(self, node_type: EnhancedNodeType) -> list[EnhancedGraphNode]:
        """按类型获取节点"""
        node_ids = self._type_index.get(node_type, [])
        return [self._nodes[nid] for nid in node_ids if nid in self._nodes]

    def search_nodes(
        self,
        query: str,
        node_types: Optional[list[EnhancedNodeType]] = None,
        tags: Optional[list[str]] = None,
        limit: int = 10,
    ) -> list[tuple[EnhancedGraphNode, float]]:
        """搜索节点"""
        query_lower = query.lower()
        results: list[tuple[EnhancedGraphNode, float]] = []

        for node in self._nodes.values():
            # 类型过滤
            if node_types and node.type not in node_types:
                continue

            # 标签过滤
            if tags and not any(t in node.tags for t in tags):
                continue

            # 计算匹配分数
            score = 0.0
            if query_lower == node.name.lower():
                score = 1.0
            elif query_lower in node.name.lower():
                score = 0.9
            elif query_lower in node.description.lower():
                score = 0.7
            elif any(query_lower in tag.lower() for tag in node.tags):
                score = 0.5

            if score > 0:
                results.append((node, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    # ============ 边操作 ============

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: EnhancedRelationType,
        strength: float = 1.0,
        confidence: float = 1.0,
        properties: Optional[dict[str, Any]] = None,
        evidence: str = "",
    ) -> Optional[EnhancedGraphEdge]:
        """添加边"""
        with self._lock:
            if source_id not in self._nodes or target_id not in self._nodes:
                return None

            edge = EnhancedGraphEdge(
                source_id=source_id,
                target_id=target_id,
                relation=relation,
                strength=strength,
                confidence=confidence,
                properties=properties or {},
                evidence=evidence,
            )

            self._edges[source_id].append(edge)
            self._reverse_edges[target_id].append(edge)
            self._invalidate_cache()
            return edge

    def get_outgoing_edges(self, node_id: str) -> list[EnhancedGraphEdge]:
        """获取出边"""
        return self._edges.get(node_id, [])

    def get_incoming_edges(self, node_id: str) -> list[EnhancedGraphEdge]:
        """获取入边"""
        return self._reverse_edges.get(node_id, [])

    def get_neighbors(
        self,
        node_id: str,
        relation_types: Optional[list[EnhancedRelationType]] = None,
        min_strength: float = 0.0,
        limit: int = 20,
    ) -> list[tuple[EnhancedGraphNode, EnhancedGraphEdge]]:
        """获取邻居节点"""
        if node_id not in self._nodes:
            return []

        results: list[tuple[EnhancedGraphNode, EnhancedGraphEdge]] = []

        with self._lock:
            for edge in self._edges.get(node_id, []):
                if edge.strength < min_strength:
                    continue
                if relation_types and edge.relation not in relation_types:
                    continue
                if edge.target_id in self._nodes:
                    results.append((self._nodes[edge.target_id], edge))

        results.sort(key=lambda x: x[1].strength, reverse=True)
        return results[:limit]

    # ============ 查询操作 ============

    def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
        min_strength: float = 0.0,
    ) -> list[tuple[list[EnhancedGraphNode], list[EnhancedGraphEdge]]]:
        """查找路径"""
        if source_id not in self._nodes or target_id not in self._nodes:
            return []

        paths: list[tuple[list[EnhancedGraphNode], list[EnhancedGraphEdge]]] = []

        with self._lock:
            queue: list[tuple[str, list[EnhancedGraphNode], list[EnhancedGraphEdge]]] = [
                (source_id, [self._nodes[source_id]], [])
            ]
            visited_sets: list[set[str]] = [{source_id}]

            while queue:
                current_id, nodes, edges = queue.pop(0)
                current_visited = visited_sets.pop(0)

                if current_id == target_id and edges:
                    paths.append((nodes, edges))
                    continue

                if len(edges) >= max_depth:
                    continue

                for edge in self._edges.get(current_id, []):
                    if edge.strength < min_strength:
                        continue
                    if edge.target_id in current_visited:
                        continue

                    new_nodes = nodes + [self._nodes[edge.target_id]]
                    new_edges = edges + [edge]
                    new_visited = current_visited | {edge.target_id}

                    queue.append((edge.target_id, new_nodes, new_edges))
                    visited_sets.append(new_visited)

        return paths

    def get_subgraph(
        self,
        center_id: str,
        depth: int = 2,
        max_nodes: int = 50,
    ) -> tuple[list[EnhancedGraphNode], list[EnhancedGraphEdge]]:
        """获取子图"""
        if center_id not in self._nodes:
            return [], []

        nodes: dict[str, EnhancedGraphNode] = {}
        edges: list[EnhancedGraphEdge] = []

        with self._lock:
            frontier: set[str] = {center_id}
            visited: set[str] = set()

            for _ in range(depth):
                if len(nodes) >= max_nodes:
                    break

                new_frontier: set[str] = set()
                for node_id in frontier:
                    if node_id in visited:
                        continue
                    visited.add(node_id)

                    if node_id in self._nodes:
                        nodes[node_id] = self._nodes[node_id]

                        for edge in self._edges.get(node_id, []):
                            if edge.target_id in self._nodes:
                                edges.append(edge)
                                if edge.target_id not in visited:
                                    new_frontier.add(edge.target_id)

                frontier = new_frontier

        return list(nodes.values()), edges

    # ============ 版本管理 ============

    def create_version(
        self,
        version: str,
        description: str = "",
        changes: Optional[list[str]] = None,
    ) -> GraphVersion:
        """创建新版本"""
        return self._version_manager.create_version(version, description, changes)

    def get_current_version(self) -> str:
        """获取当前版本"""
        return self._version_manager.get_current_version()

    # ============ 统计 ============

    def _invalidate_cache(self) -> None:
        """失效缓存"""
        self._stats_cache = None

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        if self._stats_cache:
            return self._stats_cache

        with self._lock:
            node_types: dict[str, int] = defaultdict(int)
            relation_types: dict[str, int] = defaultdict(int)

            for node in self._nodes.values():
                node_types[node.type.value] += 1

            for edges in self._edges.values():
                for edge in edges:
                    relation_types[edge.relation.value] += 1

            self._stats_cache = {
                "node_count": len(self._nodes),
                "edge_count": sum(len(e) for e in self._edges.values()),
                "node_types": dict(node_types),
                "relation_types": dict(relation_types),
                "custom_relations": len(self._custom_relations),
                "version": self._version_manager.get_current_version(),
            }

            return self._stats_cache

    def to_json(self) -> dict[str, Any]:
        """导出为 JSON"""
        with self._lock:
            return {
                "nodes": [node.to_dict() for node in self._nodes.values()],
                "edges": [edge.to_dict() for edges in self._edges.values() for edge in edges],
                "custom_relations": [r.to_dict() for r in self._custom_relations.values()],
                "version": self._version_manager.get_current_version(),
                "stats": self.get_stats(),
            }

    def from_json(self, data: dict[str, Any]) -> None:
        """从 JSON 导入"""
        with self._lock:
            self._nodes.clear()
            self._edges.clear()
            self._reverse_edges.clear()
            self._name_index.clear()
            self._type_index.clear()
            self._tag_index.clear()

            # 导入节点
            for node_data in data.get("nodes", []):
                node = EnhancedGraphNode(
                    id=node_data["id"],
                    type=EnhancedNodeType(node_data["type"]),
                    name=node_data["name"],
                    description=node_data.get("description", ""),
                    properties=node_data.get("properties", {}),
                    tags=node_data.get("tags", []),
                    source=node_data.get("source", ""),
                    version=node_data.get("version", "1.0.0"),
                    confidence=node_data.get("confidence", 1.0),
                )
                self._nodes[node.id] = node
                self._name_index[node.name.lower()] = node.id
                self._type_index[node.type].append(node.id)
                for tag in node.tags:
                    self._tag_index[tag.lower()].append(node.id)

            # 导入边
            for edge_data in data.get("edges", []):
                edge = EnhancedGraphEdge(
                    source_id=edge_data["source_id"],
                    target_id=edge_data["target_id"],
                    relation=EnhancedRelationType(edge_data["relation"]),
                    strength=edge_data.get("strength", 1.0),
                    confidence=edge_data.get("confidence", 1.0),
                    properties=edge_data.get("properties", {}),
                    evidence=edge_data.get("evidence", ""),
                )
                self._edges[edge.source_id].append(edge)
                self._reverse_edges[edge.target_id].append(edge)

            # 导入自定义关系
            for rel_data in data.get("custom_relations", []):
                rel = CustomRelation(
                    name=rel_data["name"],
                    description=rel_data.get("description", ""),
                    source_types=[EnhancedNodeType(t) for t in rel_data.get("source_types", [])],
                    target_types=[EnhancedNodeType(t) for t in rel_data.get("target_types", [])],
                )
                self._custom_relations[rel.name] = rel

            self._invalidate_cache()

    def clear(self) -> None:
        """清空图谱"""
        with self._lock:
            self._nodes.clear()
            self._edges.clear()
            self._reverse_edges.clear()
            self._name_index.clear()
            self._type_index.clear()
            self._tag_index.clear()
            self._invalidate_cache()


# 全局实例
_enhanced_graph: Optional[EnhancedKnowledgeGraph] = None


def get_enhanced_knowledge_graph() -> EnhancedKnowledgeGraph:
    """获取全局增强知识图谱"""
    global _enhanced_graph
    if _enhanced_graph is None:
        _enhanced_graph = EnhancedKnowledgeGraph()
    return _enhanced_graph