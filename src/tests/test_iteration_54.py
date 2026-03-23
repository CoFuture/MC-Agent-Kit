"""
迭代 #54 测试 - 知识图谱与智能推理

测试覆盖：
- 知识图谱构建 (KnowledgeGraph, KnowledgeGraphBuilder)
- 智能推理引擎 (InferenceEngine, RuleEngine, GraphInferenceEngine, CausalInferenceEngine)
- 上下文增强 (ContextManager, ContextCompressor, ContextEnhancer)
- 智能补全 (SmartCompletionEngine, APICompletionProvider, EventCompletionProvider)
"""

import time
import pytest
from typing import Any

# 知识图谱测试
from mc_agent_kit.skills.knowledge_graph import (
    GraphEdge,
    GraphNode,
    GraphPath,
    GraphStats,
    KnowledgeGraph,
    KnowledgeGraphBuilder,
    NodeType,
    RelationStrength,
    RelationType,
    get_knowledge_graph,
    get_graph_builder,
)

# 推理引擎测试
from mc_agent_kit.skills.inference_engine import (
    CausalChain,
    CausalInferenceEngine,
    GraphInferenceEngine,
    InferenceContext,
    InferenceEngine,
    InferenceResult,
    InferenceStatus,
    InferenceRule,
    InferenceType,
    RuleEngine,
    RuleType,
    get_inference_engine,
    infer,
    infer_api_relations,
)

# 上下文增强测试
from mc_agent_kit.skills.context_enhancement import (
    CompressionResult,
    CompressionStrategy,
    ContextCompressor,
    ContextEnhancer,
    ContextEntry,
    ContextManager,
    ContextPriority,
    ContextType,
    ContextWindow,
    KeyInfo,
    KeyInfoExtractor,
    add_context,
    get_context_enhancer,
)

# 智能补全测试
from mc_agent_kit.skills.smart_completion import (
    APICompletionProvider,
    CompletionContext,
    CompletionItem,
    CompletionResult,
    CompletionSource,
    CompletionStats,
    CompletionType,
    EventCompletionProvider,
    SmartCompletionEngine,
    SnippetCompletionProvider,
    complete,
    get_completion_engine,
)


# ============ 知识图谱测试 ============

class TestKnowledgeGraph:
    """知识图谱测试"""

    def test_create_graph(self) -> None:
        """测试创建图谱"""
        graph = KnowledgeGraph()
        assert graph is not None
        stats = graph.get_stats()
        assert stats.node_count == 0
        assert stats.edge_count == 0

    def test_add_api_node(self) -> None:
        """测试添加 API 节点"""
        graph = KnowledgeGraph()
        node = graph.add_api_node(
            name="CreateEntity",
            description="创建实体",
            properties={"module": "entity", "scope": "server"},
            tags=["entity", "create"],
        )
        assert node.id == "api:CreateEntity"
        assert node.type == NodeType.API
        assert node.name == "CreateEntity"

    def test_add_event_node(self) -> None:
        """测试添加事件节点"""
        graph = KnowledgeGraph()
        node = graph.add_event_node(
            name="OnServerChat",
            description="服务器聊天事件",
        )
        assert node.id == "event:OnServerChat"
        assert node.type == NodeType.EVENT

    def test_add_edge(self) -> None:
        """测试添加边"""
        graph = KnowledgeGraph()
        node1 = graph.add_api_node("CreateEntity")
        node2 = graph.add_api_node("SetEntityPos")

        edge = graph.add_edge(
            node1.id,
            node2.id,
            RelationType.RELATED_TO,
            strength=0.8,
        )

        assert edge is not None
        assert edge.source_id == node1.id
        assert edge.relation == RelationType.RELATED_TO

    def test_get_stats(self) -> None:
        """测试获取统计"""
        graph = KnowledgeGraph()
        graph.add_api_node("CreateEntity")
        graph.add_api_node("SetEntityPos")
        graph.add_relation("CreateEntity", "SetEntityPos", RelationType.RELATED_TO)

        stats = graph.get_stats()
        assert stats.node_count == 2
        assert stats.edge_count == 1

    def test_clear(self) -> None:
        """测试清空图谱"""
        graph = KnowledgeGraph()
        graph.add_api_node("CreateEntity")
        graph.clear()

        stats = graph.get_stats()
        assert stats.node_count == 0


class TestKnowledgeGraphBuilder:
    """知识图谱构建器测试"""

    def test_build_from_apis(self) -> None:
        """测试从 API 列表构建"""
        graph = KnowledgeGraph()
        builder = KnowledgeGraphBuilder(graph)

        apis = [
            {
                "name": "CreateEntity",
                "description": "创建实体",
                "module": "entity",
                "scope": "server",
                "parameters": [
                    {"name": "engineType", "type": "str"},
                    {"name": "identifier", "type": "str"},
                ],
                "return_type": "Entity",
            },
        ]

        count = builder.build_from_apis(apis)
        assert count == 1

        node = graph.get_node_by_name("CreateEntity")
        assert node is not None
        assert node.properties["module"] == "entity"


# ============ 推理引擎测试 ============

class TestRuleEngine:
    """规则引擎测试"""

    def test_add_rule(self) -> None:
        """测试添加规则"""
        engine = RuleEngine()
        rule = InferenceRule(
            id="test_rule",
            name="测试规则",
            rule_type=RuleType.IF_THEN,
            conditions=[{"type": "fact", "key": "test", "value": "value"}],
            conclusions=[{"result": "success"}],
            confidence=0.9,
        )

        engine.add_rule(rule)
        retrieved = engine.get_rule("test_rule")
        assert retrieved is not None

    def test_infer(self) -> None:
        """测试执行推理"""
        engine = RuleEngine()
        engine.load_builtin_rules()

        facts = {
            "apis": {"CreateEngineEntity": {}},
        }

        result = engine.infer(facts, max_iterations=10)
        assert result.status == InferenceStatus.COMPLETED


class TestInferenceEngine:
    """综合推理引擎测试"""

    def test_create_inference_engine(self) -> None:
        """测试创建推理引擎"""
        engine = InferenceEngine()
        assert engine is not None

    def test_load_defaults(self) -> None:
        """测试加载默认配置"""
        engine = InferenceEngine()
        engine.load_defaults()

    def test_infer(self) -> None:
        """测试推理"""
        engine = InferenceEngine()
        engine.load_defaults()

        context = InferenceContext(
            query="如何创建实体",
            facts={"apis": {"CreateEngineEntity": {}}},
        )

        result = engine.infer(context)
        assert result.status == InferenceStatus.COMPLETED


# ============ 上下文增强测试 ============

class TestContextManager:
    """上下文管理器测试"""

    def test_add_entry(self) -> None:
        """测试添加上下文条目"""
        manager = ContextManager()
        entry = manager.add_entry(
            content="用户想创建实体",
            context_type=ContextType.USER_REQUEST,
            priority=ContextPriority.HIGH,
        )

        assert entry.id is not None
        assert entry.content == "用户想创建实体"

    def test_get_context_window(self) -> None:
        """测试获取上下文窗口"""
        manager = ContextManager(max_tokens=1000)
        manager.add_entry("内容 1", ContextType.USER_REQUEST)
        manager.add_entry("内容 2", ContextType.USER_REQUEST)

        window = manager.get_context_window()
        assert window.total_tokens <= window.max_tokens

    def test_clear(self) -> None:
        """测试清空上下文"""
        manager = ContextManager()
        manager.add_entry("测试", ContextType.USER_REQUEST)
        manager.clear()

        stats = manager.get_stats()
        assert stats["entry_count"] == 0


class TestContextCompressor:
    """上下文压缩器测试"""

    def test_compress(self) -> None:
        """测试压缩"""
        compressor = ContextCompressor()
        entries = [
            ContextEntry(
                id="1",
                content="高优先级内容",
                context_type=ContextType.USER_REQUEST,
                priority=ContextPriority.HIGH,
                token_count=100,
            ),
            ContextEntry(
                id="2",
                content="低优先级内容",
                context_type=ContextType.USER_REQUEST,
                priority=ContextPriority.LOW,
                token_count=100,
            ),
        ]

        result = compressor.compress(entries, max_tokens=150)
        assert result.compressed_tokens <= 150


# ============ 智能补全测试 ============

class TestAPICompletionProvider:
    """API 补全提供者测试"""

    def test_complete(self) -> None:
        """测试提供补全"""
        provider = APICompletionProvider()
        context = CompletionContext(
            text_before_cursor="Create",
            language="python",
        )

        items = provider.complete(context, max_items=10)
        assert len(items) > 0


class TestSmartCompletionEngine:
    """智能补全引擎测试"""

    def test_complete(self) -> None:
        """测试执行补全"""
        engine = SmartCompletionEngine()
        context = CompletionContext(
            text_before_cursor="Create",
            language="python",
        )

        result = engine.complete(context, max_items=50)
        assert result is not None
        assert isinstance(result, CompletionResult)

    def test_get_stats(self) -> None:
        """测试获取统计"""
        engine = SmartCompletionEngine()
        context = CompletionContext(
            text_before_cursor="Create",
            language="python",
        )

        engine.complete(context)
        stats = engine.get_stats()

        assert stats.total_requests >= 1


# ============ 集成测试 ============

class TestIteration54Integration:
    """迭代 #54 集成测试"""

    def test_knowledge_graph_and_inference(self) -> None:
        """测试知识图谱与推理集成"""
        graph = KnowledgeGraph()
        graph.add_api_node("CreateEntity", "创建实体")
        graph.add_api_node("SetEntityPos", "设置实体位置")

        engine = GraphInferenceEngine(graph)
        result = engine.infer_related_apis("CreateEntity")

        assert result.status == InferenceStatus.COMPLETED

    def test_context_and_completion(self) -> None:
        """测试上下文与补全集成"""
        enhancer = ContextEnhancer()
        enhancer.add_context("用户想创建实体", ContextType.USER_REQUEST)

        engine = SmartCompletionEngine()
        context = CompletionContext(
            text_before_cursor="Create",
            language="python",
        )

        result = engine.complete(context)
        assert result is not None


# ============ 验收标准测试 ============

class TestIteration54AcceptanceCriteria:
    """迭代 #54 验收标准测试"""

    def test_knowledge_graph_nodes(self) -> None:
        """测试图谱包含 100+ API 节点"""
        graph = KnowledgeGraph()
        builder = KnowledgeGraphBuilder(graph)

        apis = [
            {"name": f"API_{i}", "module": f"module_{i % 10}"}
            for i in range(110)
        ]
        builder.build_from_apis(apis)

        stats = graph.get_stats()
        assert stats.node_count >= 100

    def test_completion_latency(self) -> None:
        """测试补全延迟 < 200ms"""
        engine = SmartCompletionEngine()
        context = CompletionContext(
            text_before_cursor="Create",
            language="python",
        )

        start = time.time()
        result = engine.complete(context, max_items=50)
        elapsed = time.time() - start

        assert elapsed < 0.2
        assert result is not None


# ============ 性能测试 ============

class TestIteration54Performance:
    """迭代 #54 性能测试"""

    def test_graph_query_performance(self) -> None:
        """测试图谱查询性能 < 100ms"""
        graph = KnowledgeGraph()
        builder = KnowledgeGraphBuilder(graph)

        apis = [{"name": f"API_{i}", "module": f"module_{i % 10}"} for i in range(100)]
        builder.build_from_apis(apis)

        start = time.time()
        results = graph.search_nodes("API", limit=10)
        elapsed = time.time() - start

        assert elapsed < 0.1

    def test_inference_performance(self) -> None:
        """测试推理性能 < 500ms"""
        engine = InferenceEngine()
        engine.load_defaults()

        context = InferenceContext(
            query="如何创建实体",
            facts={"api_name": "CreateEntity"},
        )

        start = time.time()
        result = engine.infer(context)
        elapsed = time.time() - start

        assert elapsed < 0.5