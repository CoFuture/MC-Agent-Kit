"""
LLM 集成模块

提供统一的 LLM 接口，支持多种提供商。
"""

from .base import (
    ChatMessage,
    ChatRole,
    CompletionResult,
    LLMConfig,
    LLMProvider,
    StreamChunk,
)
from .code_generation import (
    CodeGenerationType,
    GenerationContext,
    GeneratedCode,
    IntelligentCodeGenerator,
    generate_code,
)
from .code_review import (
    IntelligentCodeReviewer,
    ReviewCategory,
    ReviewIssue,
    ReviewResult,
    ReviewSeverity,
    review_code,
)
from .context_manager import (
    CodeContext,
    CodeContextAnalyzer,
    ContextMessage,
    ContextSummary,
    ContextType,
    ContextWindow,
    ConversationManager,
    ProjectContext,
    ProjectContextAnalyzer,
    analyze_code_context,
    analyze_project_context,
    create_conversation_manager,
)
from .intelligent_fix import (
    DiagnosisResult,
    ErrorContext,
    FixConfidence,
    FixResult,
    FixSuggestion,
    IntelligentFixer,
    diagnose_error,
    fix_error,
)
from .manager import LLMManager, get_llm_manager
from .providers import (
    AnthropicProvider,
    GeminiProvider,
    MockProvider,
    OllamaProvider,
    OpenAIProvider,
)
from .workflow import (
    IntelligentWorkflow,
    RequirementAnalyzer,
    SolutionDesigner,
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStep,
    WorkflowStepType,
    run_workflow,
)

__all__ = [
    # Base
    "LLMConfig",
    "LLMProvider",
    "ChatMessage",
    "ChatRole",
    "CompletionResult",
    "StreamChunk",
    # Manager
    "LLMManager",
    "get_llm_manager",
    # Providers
    "OpenAIProvider",
    "AnthropicProvider",
    "GeminiProvider",
    "OllamaProvider",
    "MockProvider",
    # Code Generation
    "CodeGenerationType",
    "GenerationContext",
    "GeneratedCode",
    "IntelligentCodeGenerator",
    "generate_code",
    # Code Review
    "IntelligentCodeReviewer",
    "ReviewCategory",
    "ReviewIssue",
    "ReviewResult",
    "ReviewSeverity",
    "review_code",
    # Intelligent Fix
    "DiagnosisResult",
    "ErrorContext",
    "FixConfidence",
    "FixResult",
    "FixSuggestion",
    "IntelligentFixer",
    "diagnose_error",
    "fix_error",
    # Workflow
    "IntelligentWorkflow",
    "RequirementAnalyzer",
    "SolutionDesigner",
    "WorkflowContext",
    "WorkflowResult",
    "WorkflowStatus",
    "WorkflowStep",
    "WorkflowStepType",
    "run_workflow",
    # Context Management
    "CodeContext",
    "CodeContextAnalyzer",
    "ContextMessage",
    "ContextSummary",
    "ContextType",
    "ContextWindow",
    "ConversationManager",
    "ProjectContext",
    "ProjectContextAnalyzer",
    "analyze_code_context",
    "analyze_project_context",
    "create_conversation_manager",
]