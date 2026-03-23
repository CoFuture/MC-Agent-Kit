"""
知识图谱构建模块

为 ModSDK API 构建知识图谱，支持实体关系抽取、图谱查询和可视化。
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class NodeType(Enum):
    """节点类型"""
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


class RelationType(Enum):
    """关系类型"""
    CALLS = "calls"                    # API 调用 API
    TRIGGERS = "triggers"              # 事件触发
    LISTENS = "listens"                # 监听事件
    RETURNS = "returns"                # 返回值
    TAKES = "takes"                    # 接受参数
    BELONGS_TO = "belongs_to"          # 属于模块
    DEPENDS_ON = "depends_on"          # 依赖
    RELATED_TO = "related_to"          # 相关
    EXTENDS = "extends"                # 继承
    IMPLEMENTS = "implements"          # 实现
    CONTAINS = "contains"              # 包含
    USES = "uses"                      # 使用
    CREATES = "creates"                # 创建
    MODIFIES = "modifies"              # 修改
    EXAMPLE_OF = "example_of"          # 示例
    SIMILAR_TO = "similar_to"          # 相似


class RelationStrength(Enum):
    """关系强度"""
    STRONG = 1.0      # 直接依赖
    MEDIUM = 0.7      # 间接关联
    WEAK = 0.4        # 弱关联
    INFERRED = 0.2    # 推断关系


@dataclass
class GraphNode:
    """图谱节点"""
    id: str
    type: NodeType
    name: str
    description: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    source: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "properties": self.properties,
            "tags": self.tags,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class GraphEdge:
    """图谱边"""
    source_id: str
    target_id: str
    relation: RelationType
    strength: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)
    evidence: str = ""  # 关系证据/来源
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation.value,
            "strength": self.strength,
            "properties": self.properties,
            "evidence": self.evidence,
            "created_at": self.created_at,
        }


@dataclass
class GraphPath:
    """图谱路径"""
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    total_weight: float
    length: int

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "total_weight": self.total_weight,
            "length": self.length,
        }


@dataclass
class GraphStats:
    """图谱统计"""
    node_count: int
    edge_count: int
    node_types: dict[str, int]
    relation_types: dict[str, int]
    avg_connections: float
    max_depth: int
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "node_types": self.node_types,
            "relation_types": self.relation_types,
            "avg_connections": self.avg_connections,
            "max_depth": self.max_depth,
            "created_at": self.created_at,
        }


class KnowledgeGraph:
    """知识图谱

    管理 ModSDK API 知识图谱的构建、查询和可视化。

    使用示例:
        graph = KnowledgeGraph()
        graph.add_api_node("CreateEntity", "创建实体", {"module": "entity"})
        graph.add_relation("CreateEntity", "SetEntityPos", RelationType.RELATED_TO)
        paths = graph.find_paths("CreateEntity", "GetEntityPos")
    """

    def __init__(self) -> None:
        """初始化知识图谱"""
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, list[GraphEdge]] = defaultdict(list)  # source_id -> edges
        self._reverse_edges: dict[str, list[GraphEdge]] = defaultdict(list)  # target_id -> edges
        self._name_index: dict[str, str] = {}  # name -> node_id
        self._type_index: dict[NodeType, list[str]] = defaultdict(list)  # type -> node_ids
        self._tag_index: dict[str, list[str]] = defaultdict(list)  # tag -> node_ids
        self._lock = threading.RLock()
        self._stats_cache: Optional[GraphStats] = None

    # ============ 节点操作 ============

    def add_node(
        self,
        node: GraphNode,
    ) -> None:
        """添加节点"""
        with self._lock:
            self._nodes[node.id] = node
            self._name_index[node.name.lower()] = node.id
            self._type_index[node.type].append(node.id)
            for tag in node.tags:
                self._tag_index[tag.lower()].append(node.id)
            self._invalidate_stats_cache()

    def add_api_node(
        self,
        name: str,
        description: str = "",
        properties: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
        source: str = "",
    ) -> GraphNode:
        """添加 API 节点"""
        node = GraphNode(
            id=f"api:{name}",
            type=NodeType.API,
            name=name,
            description=description,
            properties=properties or {},
            tags=tags or [],
            source=source,
        )
        self.add_node(node)
        return node

    def add_event_node(
        self,
        name: str,
        description: str = "",
        properties: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
        source: str = "",
    ) -> GraphNode:
        """添加事件节点"""
        node = GraphNode(
            id=f"event:{name}",
            type=NodeType.EVENT,
            name=name,
            description=description,
            properties=properties or {},
            tags=tags or [],
            source=source,
        )
        self.add_node(node)
        return node

    def add_module_node(
        self,
        name: str,
        description: str = "",
        properties: Optional[dict[str, Any]] = None,
    ) -> GraphNode:
        """添加模块节点"""
        node = GraphNode(
            id=f"module:{name}",
            type=NodeType.MODULE,
            name=name,
            description=description,
            properties=properties or {},
        )
        self.add_node(node)
        return node

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """获取节点"""
        return self._nodes.get(node_id)

    def get_node_by_name(self, name: str) -> Optional[GraphNode]:
        """通过名称获取节点"""
        node_id = self._name_index.get(name.lower())
        return self._nodes.get(node_id) if node_id else None

    def get_nodes_by_type(self, node_type: NodeType) -> list[GraphNode]:
        """按类型获取节点"""
        node_ids = self._type_index.get(node_type, [])
        return [self._nodes[nid] for nid in node_ids if nid in self._nodes]

    def get_nodes_by_tag(self, tag: str) -> list[GraphNode]:
        """按标签获取节点"""
        node_ids = self._tag_index.get(tag.lower(), [])
        return [self._nodes[nid] for nid in node_ids if nid in self._nodes]

    def search_nodes(
        self,
        query: str,
        node_types: Optional[list[NodeType]] = None,
        limit: int = 10,
    ) -> list[tuple[GraphNode, float]]:
        """搜索节点"""
        query_lower = query.lower()
        results: list[tuple[GraphNode, float]] = []

        for node in self._nodes.values():
            # 类型过滤
            if node_types and node.type not in node_types:
                continue

            # 计算匹配分数
            score = 0.0
            if query_lower in node.name.lower():
                score = 1.0
            elif query_lower in node.description.lower():
                score = 0.7
            elif any(query_lower in tag.lower() for tag in node.tags):
                score = 0.5

            if score > 0:
                results.append((node, score))

        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def update_node(
        self,
        node_id: str,
        properties: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
        description: Optional[str] = None,
    ) -> Optional[GraphNode]:
        """更新节点"""
        with self._lock:
            node = self._nodes.get(node_id)
            if not node:
                return None

            if properties:
                node.properties.update(properties)
            if tags is not None:
                # 更新标签索引
                for old_tag in node.tags:
                    self._tag_index[old_tag.lower()].remove(node_id)
                node.tags = tags
                for new_tag in tags:
                    self._tag_index[new_tag.lower()].append(node_id)
            if description is not None:
                node.description = description

            node.updated_at = time.time()
            self._invalidate_stats_cache()
            return node

    def delete_node(self, node_id: str) -> bool:
        """删除节点"""
        with self._lock:
            if node_id not in self._nodes:
                return False

            node = self._nodes[node_id]

            # 删除相关边
            edges_to_remove = self._edges.get(node_id, []) + self._reverse_edges.get(node_id, [])
            for edge in edges_to_remove:
                self._remove_edge_internal(edge)

            # 删除索引
            del self._name_index[node.name.lower()]
            self._type_index[node.type].remove(node_id)
            for tag in node.tags:
                self._tag_index[tag.lower()].remove(node_id)

            # 删除节点
            del self._nodes[node_id]
            self._invalidate_stats_cache()
            return True

    # ============ 边操作 ============

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: RelationType,
        strength: float = 1.0,
        properties: Optional[dict[str, Any]] = None,
        evidence: str = "",
    ) -> Optional[GraphEdge]:
        """添加边"""
        with self._lock:
            # 检查节点存在
            if source_id not in self._nodes or target_id not in self._nodes:
                return None

            edge = GraphEdge(
                source_id=source_id,
                target_id=target_id,
                relation=relation,
                strength=strength,
                properties=properties or {},
                evidence=evidence,
            )

            self._edges[source_id].append(edge)
            self._reverse_edges[target_id].append(edge)
            self._invalidate_stats_cache()
            return edge

    def add_relation(
        self,
        source_name: str,
        target_name: str,
        relation: RelationType,
        strength: float = 1.0,
    ) -> Optional[GraphEdge]:
        """通过节点名称添加关系"""
        source_node = self.get_node_by_name(source_name)
        target_node = self.get_node_by_name(target_name)

        if not source_node or not target_node:
            return None

        return self.add_edge(
            source_node.id,
            target_node.id,
            relation,
            strength,
        )

    def get_outgoing_edges(self, node_id: str) -> list[GraphEdge]:
        """获取出边"""
        return self._edges.get(node_id, [])

    def get_incoming_edges(self, node_id: str) -> list[GraphEdge]:
        """获取入边"""
        return self._reverse_edges.get(node_id, [])

    def get_edges_by_relation(
        self,
        relation: RelationType,
        limit: int = 100,
    ) -> list[GraphEdge]:
        """按关系类型获取边"""
        results = []
        for edges in self._edges.values():
            for edge in edges:
                if edge.relation == relation:
                    results.append(edge)
                    if len(results) >= limit:
                        return results
        return results

    def _remove_edge_internal(self, edge: GraphEdge) -> None:
        """内部方法：删除边"""
        if edge in self._edges.get(edge.source_id, []):
            self._edges[edge.source_id].remove(edge)
        if edge in self._reverse_edges.get(edge.target_id, []):
            self._reverse_edges[edge.target_id].remove(edge)

    def delete_edge(
        self,
        source_id: str,
        target_id: str,
        relation: RelationType,
    ) -> bool:
        """删除边"""
        with self._lock:
            for edge in self._edges.get(source_id, []):
                if edge.target_id == target_id and edge.relation == relation:
                    self._remove_edge_internal(edge)
                    self._invalidate_stats_cache()
                    return True
            return False

    # ============ 查询操作 ============

    def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
        min_strength: float = 0.0,
    ) -> list[GraphPath]:
        """查找两个节点之间的路径

        使用 BFS 算法查找所有路径。
        """
        if source_id not in self._nodes or target_id not in self._nodes:
            return []

        paths: list[GraphPath] = []
        queue: list[tuple[str, list[GraphNode], list[GraphEdge], float]]

        with self._lock:
            queue = [(source_id, [self._nodes[source_id]], [], 0.0)]

            while queue:
                current_id, nodes, edges, weight = queue.pop(0)

                # 到达目标
                if current_id == target_id and edges:
                    paths.append(GraphPath(
                        nodes=nodes,
                        edges=edges,
                        total_weight=weight,
                        length=len(edges),
                    ))
                    continue

                # 深度限制
                if len(edges) >= max_depth:
                    continue

                # 扩展邻居
                for edge in self._edges.get(current_id, []):
                    if edge.strength < min_strength:
                        continue
                    if edge.target_id in [n.id for n in nodes]:  # 避免循环
                        continue

                    new_nodes = nodes + [self._nodes[edge.target_id]]
                    new_edges = edges + [edge]
                    new_weight = weight + (1.0 - edge.strength)

                    queue.append((edge.target_id, new_nodes, new_edges, new_weight))

        # 按权重排序
        paths.sort(key=lambda p: p.total_weight)
        return paths

    def get_neighbors(
        self,
        node_id: str,
        relation_types: Optional[list[RelationType]] = None,
        min_strength: float = 0.0,
        limit: int = 20,
    ) -> list[tuple[GraphNode, GraphEdge]]:
        """获取邻居节点"""
        if node_id not in self._nodes:
            return []

        results: list[tuple[GraphNode, GraphEdge]] = []

        with self._lock:
            for edge in self._edges.get(node_id, []):
                if edge.strength < min_strength:
                    continue
                if relation_types and edge.relation not in relation_types:
                    continue
                if edge.target_id in self._nodes:
                    results.append((self._nodes[edge.target_id], edge))

        # 按强度排序
        results.sort(key=lambda x: x[1].strength, reverse=True)
        return results[:limit]

    def get_subgraph(
        self,
        center_id: str,
        depth: int = 2,
        max_nodes: int = 50,
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        """获取子图"""
        if center_id not in self._nodes:
            return [], []

        nodes: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []

        with self._lock:
            # BFS 扩展
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

                        # 添加边
                        for edge in self._edges.get(node_id, []):
                            if edge.target_id in self._nodes:
                                edges.append(edge)
                                if edge.target_id not in visited:
                                    new_frontier.add(edge.target_id)

                frontier = new_frontier

        return list(nodes.values()), edges

    def get_important_nodes(
        self,
        top_k: int = 10,
    ) -> list[tuple[GraphNode, float]]:
        """获取重要节点（基于 PageRank 简化版）"""
        # 简化版：基于入边数量和强度
        scores: dict[str, float] = defaultdict(float)

        with self._lock:
            for node_id, node in self._nodes.items():
                # 入边贡献
                for edge in self._reverse_edges.get(node_id, []):
                    scores[node_id] += edge.strength

                # 出边贡献
                for edge in self._edges.get(node_id, []):
                    scores[node_id] += edge.strength * 0.5

        # 排序
        sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(self._nodes[nid], score) for nid, score in sorted_nodes[:top_k] if nid in self._nodes]

    # ============ 统计与可视化 ============

    def get_stats(self) -> GraphStats:
        """获取图谱统计"""
        if self._stats_cache:
            return self._stats_cache

        with self._lock:
            node_types: dict[str, int] = defaultdict(int)
            relation_types: dict[str, int] = defaultdict(int)
            total_connections = 0

            for node in self._nodes.values():
                node_types[node.type.value] += 1
                total_connections += len(self._edges.get(node.id, []))

            for edges in self._edges.values():
                for edge in edges:
                    relation_types[edge.relation.value] += 1

            avg_connections = total_connections / len(self._nodes) if self._nodes else 0.0

            self._stats_cache = GraphStats(
                node_count=len(self._nodes),
                edge_count=sum(len(e) for e in self._edges.values()),
                node_types=dict(node_types),
                relation_types=dict(relation_types),
                avg_connections=avg_connections,
                max_depth=self._calculate_max_depth(),
            )

            return self._stats_cache

    def _calculate_max_depth(self) -> int:
        """计算最大深度"""
        if not self._nodes:
            return 0

        visited: set[str] = set()
        max_depth = 0

        for start_id in self._nodes:
            if start_id in visited:
                continue

            queue: list[tuple[str, int]] = [(start_id, 0)]
            while queue:
                node_id, depth = queue.pop(0)
                if node_id in visited:
                    continue
                visited.add(node_id)
                max_depth = max(max_depth, depth)

                for edge in self._edges.get(node_id, []):
                    if edge.target_id not in visited:
                        queue.append((edge.target_id, depth + 1))

        return max_depth

    def _invalidate_stats_cache(self) -> None:
        """失效统计缓存"""
        self._stats_cache = None

    def to_mermaid(self) -> str:
        """生成 Mermaid 图表代码"""
        lines = ["graph TD"]

        # 添加节点
        for node in self._nodes.values():
            label = node.name.replace('"', "'")
            lines.append(f'    {node.id}["{label}<br/>{node.type.value}"]')

        # 添加边
        for edges in self._edges.values():
            for edge in edges:
                # 根据关系类型选择箭头样式
                arrow = "-->"
                if edge.relation == RelationType.DEPENDS_ON:
                    arrow = "-.->"
                elif edge.relation == RelationType.TRIGGERS:
                    arrow = "==>"
                lines.append(f"    {edge.source_id} {arrow}|{edge.relation.value}| {edge.target_id}")

        return "\n".join(lines)

    def to_json(self) -> dict[str, Any]:
        """导出为 JSON"""
        return {
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "edges": [edge.to_dict() for edges in self._edges.values() for edge in edges],
            "stats": self.get_stats().to_dict(),
        }

    def from_json(self, data: dict[str, Any]) -> None:
        """从 JSON 导入"""
        with self._lock:
            # 清空现有数据
            self._nodes.clear()
            self._edges.clear()
            self._reverse_edges.clear()
            self._name_index.clear()
            self._type_index.clear()
            self._tag_index.clear()

            # 导入节点
            for node_data in data.get("nodes", []):
                node = GraphNode(
                    id=node_data["id"],
                    type=NodeType(node_data["type"]),
                    name=node_data["name"],
                    description=node_data.get("description", ""),
                    properties=node_data.get("properties", {}),
                    tags=node_data.get("tags", []),
                    source=node_data.get("source", ""),
                    created_at=node_data.get("created_at", time.time()),
                    updated_at=node_data.get("updated_at", time.time()),
                )
                self._nodes[node.id] = node
                self._name_index[node.name.lower()] = node.id
                self._type_index[node.type].append(node.id)
                for tag in node.tags:
                    self._tag_index[tag.lower()].append(node.id)

            # 导入边
            for edge_data in data.get("edges", []):
                edge = GraphEdge(
                    source_id=edge_data["source_id"],
                    target_id=edge_data["target_id"],
                    relation=RelationType(edge_data["relation"]),
                    strength=edge_data.get("strength", 1.0),
                    properties=edge_data.get("properties", {}),
                    evidence=edge_data.get("evidence", ""),
                    created_at=edge_data.get("created_at", time.time()),
                )
                self._edges[edge.source_id].append(edge)
                self._reverse_edges[edge.target_id].append(edge)

            self._invalidate_stats_cache()

    def clear(self) -> None:
        """清空图谱"""
        with self._lock:
            self._nodes.clear()
            self._edges.clear()
            self._reverse_edges.clear()
            self._name_index.clear()
            self._type_index.clear()
            self._tag_index.clear()
            self._invalidate_stats_cache()


class KnowledgeGraphBuilder:
    """知识图谱构建器

    从 ModSDK 文档构建知识图谱。

    使用示例:
        builder = KnowledgeGraphBuilder(graph)
        builder.build_from_apis(api_list)
        builder.build_from_events(event_list)
        builder.infer_relations()
    """

    def __init__(self, graph: KnowledgeGraph) -> None:
        """初始化构建器"""
        self._graph = graph
        self._lock = threading.Lock()

    def build_from_apis(
        self,
        apis: list[dict[str, Any]],
    ) -> int:
        """从 API 列表构建图谱"""
        count = 0

        with self._lock:
            for api in apis:
                # 创建 API 节点
                name = api.get("name", "")
                if not name:
                    continue

                node = self._graph.add_api_node(
                    name=name,
                    description=api.get("description", ""),
                    properties={
                        "module": api.get("module", ""),
                        "scope": api.get("scope", ""),
                        "parameters": api.get("parameters", []),
                        "return_type": api.get("return_type", ""),
                    },
                    tags=api.get("tags", []),
                    source=api.get("source", ""),
                )

                # 创建参数节点
                for param in api.get("parameters", []):
                    param_name = param.get("name", "")
                    if param_name:
                        param_node = GraphNode(
                            id=f"param:{name}:{param_name}",
                            type=NodeType.PARAMETER,
                            name=param_name,
                            description=param.get("description", ""),
                            properties={"type": param.get("type", "")},
                        )
                        self._graph.add_node(param_node)
                        self._graph.add_edge(
                            node.id,
                            param_node.id,
                            RelationType.TAKES,
                        )

                # 创建返回值节点
                return_type = api.get("return_type", "")
                if return_type:
                    return_node = GraphNode(
                        id=f"return:{name}",
                        type=NodeType.RETURN_VALUE,
                        name=return_type,
                        properties={"type": return_type},
                    )
                    self._graph.add_node(return_node)
                    self._graph.add_edge(
                        node.id,
                        return_node.id,
                        RelationType.RETURNS,
                    )

                # 添加模块关系
                module = api.get("module", "")
                if module:
                    module_node = self._graph.get_node_by_name(module)
                    if not module_node:
                        module_node = self._graph.add_module_node(
                            name=module,
                            description=f"{module} 模块",
                        )
                    self._graph.add_edge(
                        node.id,
                        module_node.id,
                        RelationType.BELONGS_TO,
                    )

                count += 1

        return count

    def build_from_events(
        self,
        events: list[dict[str, Any]],
    ) -> int:
        """从事件列表构建图谱"""
        count = 0

        with self._lock:
            for event in events:
                name = event.get("name", "")
                if not name:
                    continue

                node = self._graph.add_event_node(
                    name=name,
                    description=event.get("description", ""),
                    properties={
                        "scope": event.get("scope", ""),
                        "parameters": event.get("parameters", []),
                    },
                    tags=event.get("tags", []),
                    source=event.get("source", ""),
                )

                # 添加模块关系
                module = event.get("module", "")
                if module:
                    module_node = self._graph.get_node_by_name(module)
                    if not module_node:
                        module_node = self._graph.add_module_node(
                            name=module,
                            description=f"{module} 模块",
                        )
                    self._graph.add_edge(
                        node.id,
                        module_node.id,
                        RelationType.BELONGS_TO,
                    )

                count += 1

        return count

    def infer_relations(self) -> int:
        """推断关系"""
        count = 0

        with self._lock:
            # 基于名称相似性推断关系
            api_nodes = self._graph.get_nodes_by_type(NodeType.API)
            for i, node1 in enumerate(api_nodes):
                for node2 in api_nodes[i + 1:]:
                    # 检查名称相似性
                    similarity = self._calculate_similarity(node1.name, node2.name)
                    if similarity > 0.6:
                        self._graph.add_edge(
                            node1.id,
                            node2.id,
                            RelationType.SIMILAR_TO,
                            strength=similarity * RelationStrength.WEAK.value,
                            evidence="名称相似性推断",
                        )
                        count += 1

            # 基于模块关系推断
            module_nodes = self._graph.get_nodes_by_type(NodeType.MODULE)
            for module in module_nodes:
                neighbors = self._graph.get_neighbors(module.id)
                for i, (node1, _) in enumerate(neighbors):
                    for node2, _ in neighbors[i + 1:]:
                        # 同模块的 API 可能相关
                        if node1.type == NodeType.API and node2.type == NodeType.API:
                            exists = any(
                                e.target_id == node2.id
                                for e in self._graph.get_outgoing_edges(node1.id)
                            )
                            if not exists:
                                self._graph.add_edge(
                                    node1.id,
                                    node2.id,
                                    RelationType.RELATED_TO,
                                    strength=RelationStrength.WEAK.value,
                                    evidence="同模块推断",
                                )
                                count += 1

        return count

    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """计算名称相似性"""
        # 简单的 Levenshtein 距离
        m, n = len(name1), len(name2)
        if m == 0 or n == 0:
            return 0.0

        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if name1[i - 1].lower() == name2[j - 1].lower():
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = min(
                        dp[i - 1][j] + 1,
                        dp[i][j - 1] + 1,
                        dp[i - 1][j - 1] + 1,
                    )

        distance = dp[m][n]
        max_len = max(m, n)
        return 1.0 - distance / max_len

    def add_example_relation(
        self,
        example_id: str,
        api_names: list[str],
    ) -> None:
        """添加示例关系"""
        example_node = GraphNode(
            id=f"example:{example_id}",
            type=NodeType.EXAMPLE,
            name=example_id,
        )
        self._graph.add_node(example_node)

        for api_name in api_names:
            api_node = self._graph.get_node_by_name(api_name)
            if api_node:
                self._graph.add_edge(
                    example_node.id,
                    api_node.id,
                    RelationType.EXAMPLE_OF,
                    strength=RelationStrength.STRONG.value,
                )


# 全局实例
_graph: Optional[KnowledgeGraph] = None
_builder: Optional[KnowledgeGraphBuilder] = None


def get_knowledge_graph() -> KnowledgeGraph:
    """获取全局知识图谱"""
    global _graph
    if _graph is None:
        _graph = KnowledgeGraph()
    return _graph


def get_graph_builder() -> KnowledgeGraphBuilder:
    """获取全局图谱构建器"""
    global _builder
    if _builder is None:
        _builder = KnowledgeGraphBuilder(get_knowledge_graph())
    return _builder