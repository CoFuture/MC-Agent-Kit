"""
MC-Agent-Kit Skills 模块

提供 AI Agent 的技能扩展接口。
"""

from .base import (
    BaseSkill,
    SkillCategory,
    SkillMetadata,
    SkillPriority,
    SkillRegistry,
    SkillResult,
    get_registry,
    get_skill,
    register_skill,
)
from .modsdk import (
    ModSDKAPISearchSkill,
    ModSDKCodeGenSkill,
    ModSDKDebugSkill,
    ModSDKEventSearchSkill,
)
from .ai_enhanced import (
    CodeContextAnalyzer,
    CodeContextInfo,
    ConversationContext,
    ConversationManager,
    ConversationMessage,
    ConversationRole,
    IntentRecognitionResult,
    IntentRecognizer,
    IntentType,
    SmartRecommender,
    create_code_analyzer,
    create_conversation_manager,
    create_smart_recommender,
    get_code_analyzer,
    get_conversation_manager,
    get_smart_recommender,
)
from .intelligent_codegen import (
    CodeQualityLevel,
    CodeStyle,
    CodeTemplate,
    GeneratedCode,
    GenerationStrategy,
    IntelligentCodeGenerator,
    QualityAssessment,
    StyleCheckResult,
    generate_code,
    get_code_generator,
)
from .intelligent_fix import (
    ErrorAnalysis,
    ErrorCategory,
    ErrorPattern,
    ErrorPatternLearner,
    FixConfidence,
    FixResult,
    FixStatus,
    FixSuggestion,
    IntelligentFixer,
    analyze_and_fix,
    get_intelligent_fixer,
)
from .test_generator import (
    CoverageLevel,
    IntelligentTestGenerator,
    TestCase,
    TestReport,
    TestResult,
    TestStatus,
    TestSuite,
    TestType,
    generate_tests,
    get_test_analyzer,
    get_test_generator,
)
from .smart_generation import (
    CodeQualityLevel as SmartCodeQualityLevel,
    CodeStyle as SmartCodeStyle,
    CodeTemplate as SmartCodeTemplate,
    GeneratedCode as SmartGeneratedCode,
    GenerationStrategy as SmartGenerationStrategy,
    LLMConfig,
    LLMProvider,
    QualityAssessment as SmartQualityAssessment,
    SmartCodeGenerator,
    StyleCheckResult as SmartStyleCheckResult,
    generate_code as smart_generate_code,
    get_smart_generator,
)
from .smart_conversation import (
    ConversationContext as SmartConversationContext,
    ConversationMemory,
    ConversationMessage as SmartConversationMessage,
    ConversationRole as SmartConversationRole,
    ConversationState,
    ConversationSummary,
    IntentRecognitionResult as SmartIntentRecognitionResult,
    IntentRecognizer as SmartIntentRecognizer,
    IntentType as SmartIntentType,
    SmartConversationManager,
    TopicCategory,
    TopicTracker,
    create_session,
    get_conversation_manager as get_smart_conversation_manager,
    process_message,
)

# Iteration #50: LLM Integration
from .llm_integration import (
    AzureOpenAIClient,
    BaseLLMClient,
    ChatMessage,
    CostTracker,
    LLMClientFactory,
    LLMConfig as IntegrationLLMConfig,
    LLMProvider as IntegrationLLMProvider,
    LLMResponse,
    LLMService,
    LMStudioClient,
    MessageRole,
    MockLLMClient,
    OllamaClient,
    OpenAIClient,
    StreamChunk,
    TokenUsage,
    chat,
    get_llm_service,
)

# Iteration #50: Prompt Engineering
from .prompt_engineering import (
    ChainOfThoughtConfig,
    ChainOfThoughtPrompter,
    FewShotConfig,
    FewShotExample,
    FewShotLearner,
    PromptEngineeringService,
    PromptOptimizer,
    PromptOptimizationResult,
    PromptTemplate,
    PromptTemplateRegistry,
    PromptTemplateType,
    ReasoningType,
    build_cot_prompt,
    get_prompt_service,
    render_prompt,
)

# Iteration #50: Async Generation
from .async_generation import (
    AsyncCodeGenerator,
    AsyncGenerationResult,
    BatchGenerationConfig,
    BatchGenerationResult,
    IncrementalCache,
    LazyLoader,
    MemoryOptimizedGenerator,
    generate_code_async,
    generate_codes_batch_async,
    get_async_generator,
    get_memory_optimized_generator,
)

__all__ = [
    # 基类和工具
    "BaseSkill",
    "SkillCategory",
    "SkillMetadata",
    "SkillPriority",
    "SkillRegistry",
    "SkillResult",
    "get_registry",
    "get_skill",
    "register_skill",
    # ModSDK Skills
    "ModSDKAPISearchSkill",
    "ModSDKCodeGenSkill",
    "ModSDKDebugSkill",
    "ModSDKEventSearchSkill",
    # AI Enhanced
    "CodeContextAnalyzer",
    "CodeContextInfo",
    "ConversationContext",
    "ConversationManager",
    "ConversationMessage",
    "ConversationRole",
    "IntentRecognitionResult",
    "IntentRecognizer",
    "IntentType",
    "SmartRecommender",
    "create_code_analyzer",
    "create_conversation_manager",
    "create_smart_recommender",
    "get_code_analyzer",
    "get_conversation_manager",
    "get_smart_recommender",
    # Intelligent Code Generation
    "CodeQualityLevel",
    "CodeStyle",
    "CodeTemplate",
    "GeneratedCode",
    "GenerationStrategy",
    "IntelligentCodeGenerator",
    "QualityAssessment",
    "StyleCheckResult",
    "generate_code",
    "get_code_generator",
    # Intelligent Fix
    "ErrorAnalysis",
    "ErrorCategory",
    "ErrorPattern",
    "ErrorPatternLearner",
    "FixConfidence",
    "FixResult",
    "FixStatus",
    "FixSuggestion",
    "IntelligentFixer",
    "analyze_and_fix",
    "get_intelligent_fixer",
    # Test Generator
    "CoverageLevel",
    "IntelligentTestGenerator",
    "TestCase",
    "TestReport",
    "TestResult",
    "TestStatus",
    "TestSuite",
    "TestType",
    "generate_tests",
    "get_test_analyzer",
    "get_test_generator",
    # Smart Generation (Iteration #49)
    "SmartCodeGenerator",
    "SmartCodeQualityLevel",
    "SmartCodeStyle",
    "SmartCodeTemplate",
    "SmartGeneratedCode",
    "SmartGenerationStrategy",
    "LLMConfig",
    "LLMProvider",
    "SmartQualityAssessment",
    "SmartStyleCheckResult",
    "smart_generate_code",
    "get_smart_generator",
    # Smart Conversation (Iteration #49)
    "SmartConversationManager",
    "SmartConversationContext",
    "SmartConversationMessage",
    "SmartConversationRole",
    "ConversationMemory",
    "ConversationState",
    "ConversationSummary",
    "SmartIntentRecognitionResult",
    "SmartIntentRecognizer",
    "SmartIntentType",
    "TopicCategory",
    "TopicTracker",
    "create_session",
    "get_smart_conversation_manager",
    "process_message",
    # LLM Integration (Iteration #50)
    "BaseLLMClient",
    "OpenAIClient",
    "AzureOpenAIClient",
    "OllamaClient",
    "LMStudioClient",
    "MockLLMClient",
    "LLMClientFactory",
    "LLMService",
    "ChatMessage",
    "MessageRole",
    "TokenUsage",
    "CostTracker",
    "LLMResponse",
    "StreamChunk",
    "IntegrationLLMConfig",
    "IntegrationLLMProvider",
    "get_llm_service",
    "chat",
    # Prompt Engineering (Iteration #50)
    "PromptTemplateRegistry",
    "PromptTemplate",
    "PromptTemplateType",
    "FewShotExample",
    "FewShotConfig",
    "FewShotLearner",
    "ChainOfThoughtPrompter",
    "ChainOfThoughtConfig",
    "ReasoningType",
    "PromptOptimizer",
    "PromptOptimizationResult",
    "PromptEngineeringService",
    "get_prompt_service",
    "render_prompt",
    "build_cot_prompt",
    # Async Generation (Iteration #50)
    "AsyncCodeGenerator",
    "AsyncGenerationResult",
    "BatchGenerationConfig",
    "BatchGenerationResult",
    "IncrementalCache",
    "LazyLoader",
    "MemoryOptimizedGenerator",
    "get_async_generator",
    "get_memory_optimized_generator",
    "generate_code_async",
    "generate_codes_batch_async",
]


def register_modsdk_skills(kb_path: str | None = None) -> None:
    """注册所有 ModSDK Skills

    Args:
        kb_path: 可选的知识库文件路径
    """
    registry = get_registry()

    # 注册 API 搜索 Skill
    api_skill = ModSDKAPISearchSkill(kb_path=kb_path)
    registry.register(api_skill)

    # 注册事件搜索 Skill
    event_skill = ModSDKEventSearchSkill(kb_path=kb_path)
    registry.register(event_skill)

    # 注册代码生成 Skill
    code_gen_skill = ModSDKCodeGenSkill()
    registry.register(code_gen_skill)

    # 注册调试辅助 Skill
    debug_skill = ModSDKDebugSkill()
    registry.register(debug_skill)
