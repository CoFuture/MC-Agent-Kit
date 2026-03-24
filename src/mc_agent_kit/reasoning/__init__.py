"""
推理能力增强模块

提供知识图谱扩展、推理规则增强、因果推理增强和上下文推理。
"""

from .enhanced_knowledge_graph import (
    EnhancedKnowledgeGraph,
    EnhancedNodeType,
    EnhancedRelationType,
    GraphVersion,
    GraphVersionManager,
    get_enhanced_knowledge_graph,
)

from .enhanced_inference_engine import (
    EnhancedInferenceEngine,
    EnhancedInferenceResult,
    ReasoningContext,
    MultiHopReasoning,
    ContextualReasoner,
    get_enhanced_inference_engine,
)

from .enhanced_causal_engine import (
    EnhancedCausalEngine,
    CausalRule,
    CausalChainResult,
    DiagnosticResult,
    get_enhanced_causal_engine,
)

from .async_inference import (
    AsyncInferenceEngine,
    InferenceTask,
    InferenceQueue,
    InferenceCallback,
    get_async_inference_engine,
)

__all__ = [
    # Enhanced Knowledge Graph
    "EnhancedKnowledgeGraph",
    "EnhancedNodeType",
    "EnhancedRelationType",
    "GraphVersion",
    "GraphVersionManager",
    "get_enhanced_knowledge_graph",
    # Enhanced Inference Engine
    "EnhancedInferenceEngine",
    "EnhancedInferenceResult",
    "ReasoningContext",
    "MultiHopReasoning",
    "ContextualReasoner",
    "get_enhanced_inference_engine",
    # Enhanced Causal Engine
    "EnhancedCausalEngine",
    "CausalRule",
    "CausalChainResult",
    "DiagnosticResult",
    "get_enhanced_causal_engine",
    # Async Inference
    "AsyncInferenceEngine",
    "InferenceTask",
    "InferenceQueue",
    "InferenceCallback",
    "get_async_inference_engine",
]