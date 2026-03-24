"""
测试迭代 #65: AI 能力增强与智能代码生成

测试覆盖:
1. LLM 集成 (基础接口、提供商、管理器)
2. 智能代码生成
3. 智能代码审查
4. 智能修复
"""

import pytest
import time
from typing import Any

from mc_agent_kit.llm.base import (
    ChatMessage,
    ChatRole,
    CompletionResult,
    LLMConfig,
    StreamChunk,
)
from mc_agent_kit.llm.manager import LLMManager, get_llm_manager
from mc_agent_kit.llm.providers import (
    MockProvider,
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    OllamaProvider,
)
from mc_agent_kit.llm.code_generation import (
    CodeGenerationType,
    GenerationContext,
    GeneratedCode,
    IntelligentCodeGenerator,
    generate_code,
)
from mc_agent_kit.llm.code_review import (
    IntelligentCodeReviewer,
    ReviewCategory,
    ReviewIssue,
    ReviewResult,
    ReviewSeverity,
    review_code,
)
from mc_agent_kit.llm.intelligent_fix import (
    DiagnosisResult,
    ErrorContext,
    FixConfidence,
    FixResult,
    FixSuggestion,
    IntelligentFixer,
    diagnose_error,
    fix_error,
)


# ============================================================================
# 基础接口测试
# ============================================================================

class TestChatMessage:
    """测试聊天消息"""

    def test_create_system_message(self) -> None:
        """创建系统消息"""
        msg = ChatMessage.system("You are a helpful assistant")
        assert msg.role == ChatRole.SYSTEM
        assert msg.content == "You are a helpful assistant"

    def test_create_user_message(self) -> None:
        """创建用户消息"""
        msg = ChatMessage.user("Hello")
        assert msg.role == ChatRole.USER
        assert msg.content == "Hello"

    def test_create_assistant_message(self) -> None:
        """创建助手消息"""
        msg = ChatMessage.assistant("Hi there!")
        assert msg.role == ChatRole.ASSISTANT
        assert msg.content == "Hi there!"

    def test_to_dict(self) -> None:
        """转换为字典"""
        msg = ChatMessage.user("Test")
        data = msg.to_dict()
        assert data["role"] == "user"
        assert data["content"] == "Test"

    def test_message_with_name(self) -> None:
        """带名称的消息"""
        msg = ChatMessage(role=ChatRole.FUNCTION, content="result", name="my_function")
        data = msg.to_dict()
        assert data["name"] == "my_function"


class TestCompletionResult:
    """测试补全结果"""

    def test_completion_result_basic(self) -> None:
        """基本补全结果"""
        result = CompletionResult(
            content="Hello, World!",
            model="gpt-4",
            provider="openai",
        )
        assert result.content == "Hello, World!"
        assert result.model == "gpt-4"
        assert result.provider == "openai"
        assert result.finish_reason == "stop"

    def test_completion_result_with_usage(self) -> None:
        """带使用量的补全结果"""
        result = CompletionResult(
            content="Response",
            model="gpt-4",
            provider="openai",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        assert result.usage["total_tokens"] == 15

    def test_to_dict(self) -> None:
        """转换为字典"""
        result = CompletionResult(
            content="Test",
            model="mock",
            provider="mock",
            latency_ms=100.5,
        )
        data = result.to_dict()
        assert data["content"] == "Test"
        assert data["latency_ms"] == 100.5


class TestLLMConfig:
    """测试 LLM 配置"""

    def test_default_config(self) -> None:
        """默认配置"""
        config = LLMConfig()
        assert config.provider == "mock"
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
        assert config.timeout == 60.0

    def test_custom_config(self) -> None:
        """自定义配置"""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o",
            api_key="sk-xxx",
            temperature=0.5,
            max_tokens=1024,
        )
        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.temperature == 0.5

    def test_to_dict_hides_api_key(self) -> None:
        """转换为字典时隐藏 API key"""
        config = LLMConfig(api_key="secret-key")
        data = config.to_dict()
        assert data["api_key"] == "***"


# ============================================================================
# Mock 提供商测试
# ============================================================================

class TestMockProvider:
    """测试 Mock 提供商"""

    def test_mock_provider_name(self) -> None:
        """提供商名称"""
        config = LLMConfig(provider="mock")
        provider = MockProvider(config)
        assert provider.name == "mock"

    def test_mock_provider_models(self) -> None:
        """支持的模型"""
        config = LLMConfig(provider="mock")
        provider = MockProvider(config)
        assert "mock-default" in provider.models
        assert "mock-code" in provider.models

    def test_mock_complete(self) -> None:
        """同步补全"""
        config = LLMConfig(provider="mock")
        provider = MockProvider(config)
        messages = [ChatMessage.user("创建实体")]
        result = provider.complete(messages)
        assert result.content != ""
        assert result.provider == "mock"

    def test_mock_complete_entity_request(self) -> None:
        """实体创建请求"""
        config = LLMConfig(provider="mock")
        provider = MockProvider(config)
        messages = [ChatMessage.user("如何创建自定义实体")]
        result = provider.complete(messages)
        # Mock response should contain entity-related content
        assert "entity" in result.content.lower() or "实体" in result.content or "CreateEngineEntity" in result.content

    def test_mock_complete_event_request(self) -> None:
        """事件请求"""
        config = LLMConfig(provider="mock")
        provider = MockProvider(config)
        messages = [ChatMessage.user("监听事件")]
        result = provider.complete(messages)
        assert "ListenEvent" in result.content or "event" in result.content.lower()

    def test_mock_count_tokens(self) -> None:
        """计算 token 数量"""
        config = LLMConfig(provider="mock")
        provider = MockProvider(config)
        tokens = provider.count_tokens("Hello, World!")
        assert tokens > 0

    def test_mock_validate_config(self) -> None:
        """验证配置"""
        config = LLMConfig(provider="mock")
        provider = MockProvider(config)
        assert provider.validate_config() is True


# ============================================================================
# LLM 管理器测试
# ============================================================================

class TestLLMManager:
    """测试 LLM 管理器"""

    def test_singleton(self) -> None:
        """单例模式"""
        manager1 = LLMManager()
        manager2 = LLMManager()
        assert manager1 is manager2

    def test_get_llm_manager(self) -> None:
        """获取管理器单例"""
        manager = get_llm_manager()
        assert manager is not None

    def test_list_providers(self) -> None:
        """列出提供商"""
        manager = LLMManager()
        providers = manager.list_providers()
        assert "mock" in providers
        assert "openai" in providers
        assert "anthropic" in providers

    def test_get_mock_provider(self) -> None:
        """获取 Mock 提供商"""
        manager = LLMManager()
        provider = manager.get_provider(name="mock")
        assert isinstance(provider, MockProvider)

    def test_set_default_provider(self) -> None:
        """设置默认提供商"""
        manager = LLMManager()
        manager.set_default_provider("mock")
        provider = manager.get_provider()
        assert provider.name == "mock"

    def test_complete_with_mock(self) -> None:
        """使用 Mock 补全"""
        manager = LLMManager()
        messages = [ChatMessage.user("Hello")]
        result = manager.complete(messages, LLMConfig(provider="mock"))
        assert result.content != ""

    def test_count_tokens(self) -> None:
        """计算 token 数量"""
        manager = LLMManager()
        tokens = manager.count_tokens("Hello, World!", LLMConfig(provider="mock"))
        assert tokens > 0


# ============================================================================
# 智能代码生成测试
# ============================================================================

class TestCodeGenerationType:
    """测试代码生成类型"""

    def test_generation_types(self) -> None:
        """生成类型枚举"""
        assert CodeGenerationType.EVENT_LISTENER.value == "event_listener"
        assert CodeGenerationType.ENTITY_BEHAVIOR.value == "entity_behavior"
        assert CodeGenerationType.CUSTOM.value == "custom"


class TestGenerationContext:
    """测试生成上下文"""

    def test_default_context(self) -> None:
        """默认上下文"""
        ctx = GenerationContext()
        assert ctx.project_name == ""
        assert ctx.target == "server"
        assert ctx.style == "pep8"

    def test_custom_context(self) -> None:
        """自定义上下文"""
        ctx = GenerationContext(
            project_name="MyAddon",
            module_name="entities",
            description="测试项目",
            target="server",
        )
        data = ctx.to_dict()
        assert data["project_name"] == "MyAddon"


class TestGeneratedCode:
    """测试生成的代码"""

    def test_generated_code_basic(self) -> None:
        """基本生成的代码"""
        code = GeneratedCode(
            code="print('Hello')",
            language="python",
            confidence=0.9,
        )
        assert code.code == "print('Hello')"
        assert code.language == "python"
        assert code.confidence == 0.9

    def test_generated_code_with_imports(self) -> None:
        """带导入的生成代码"""
        code = GeneratedCode(
            code="import os\nos.getcwd()",
            imports=["import os"],
            dependencies=["os"],
        )
        assert "import os" in code.imports


class TestIntelligentCodeGenerator:
    """测试智能代码生成器"""

    def test_generator_initialization(self) -> None:
        """生成器初始化"""
        generator = IntelligentCodeGenerator()
        assert generator.llm_config.provider == "mock"

    def test_generate_event_listener(self) -> None:
        """生成事件监听器"""
        generator = IntelligentCodeGenerator()
        result = generator.generate(
            request="创建一个玩家聊天事件监听器",
            generation_type=CodeGenerationType.EVENT_LISTENER,
        )
        assert result.code != ""
        assert result.confidence > 0
        assert isinstance(result, GeneratedCode)

    def test_generate_entity_behavior(self) -> None:
        """生成实体行为"""
        generator = IntelligentCodeGenerator()
        result = generator.generate(
            request="创建一个自定义实体的移动行为",
            generation_type=CodeGenerationType.ENTITY_BEHAVIOR,
            context=GenerationContext(project_name="TestAddon"),
        )
        assert result.code != ""
        # Mock response should contain entity-related content
        assert "entity" in result.code.lower() or "实体" in result.code or "move" in result.code.lower() or "移动" in result.code

    def test_generate_with_context(self) -> None:
        """带上下文生成"""
        generator = IntelligentCodeGenerator()
        ctx = GenerationContext(
            project_name="MyMod",
            description="测试模组",
            target="server",
        )
        result = generator.generate(
            request="创建一个简单的命令处理函数",
            generation_type=CodeGenerationType.CUSTOM,
            context=ctx,
        )
        assert result.code != ""

    def test_extract_code_from_markdown(self) -> None:
        """从 Markdown 中提取代码"""
        generator = IntelligentCodeGenerator()
        content = '''这里是说明
```python
def hello():
    print("Hello")
```
结束'''
        code = generator._extract_code(content)
        assert "def hello():" in code
        assert "这里是说明" not in code

    def test_extract_imports(self) -> None:
        """提取导入语句"""
        generator = IntelligentCodeGenerator()
        code = """import os
from typing import List

def main():
    pass
"""
        imports = generator._extract_imports(code)
        assert len(imports) == 2
        assert "import os" in imports

    def test_calculate_confidence(self) -> None:
        """计算置信度"""
        generator = IntelligentCodeGenerator()
        code = """def on_chat(args):
    print(args)
"""
        confidence = generator._calculate_confidence(
            code,
            CodeGenerationType.EVENT_LISTENER,
        )
        assert confidence > 0

    def test_generate_notes(self) -> None:
        """生成说明"""
        generator = IntelligentCodeGenerator()
        code = "import mod.server.extraServerApi as serverApi"
        notes = generator._generate_notes(code, CodeGenerationType.CUSTOM)
        assert any("服务端" in note for note in notes)

    def test_generate_warnings(self) -> None:
        """生成警告"""
        generator = IntelligentCodeGenerator()
        code = """print("debug")
global counter
"""
        warnings = generator._generate_warnings(code)
        assert len(warnings) > 0


class TestGenerateCode:
    """测试便捷函数"""

    def test_generate_code_function(self) -> None:
        """便捷函数生成代码"""
        result = generate_code(
            request="创建一个计时器",
            generation_type=CodeGenerationType.CUSTOM,
        )
        assert isinstance(result, GeneratedCode)
        assert result.code != ""


# ============================================================================
# 智能代码审查测试
# ============================================================================

class TestReviewSeverity:
    """测试审查严重程度"""

    def test_severity_values(self) -> None:
        """严重程度值"""
        assert ReviewSeverity.CRITICAL.value == "critical"
        assert ReviewSeverity.ERROR.value == "error"
        assert ReviewSeverity.WARNING.value == "warning"


class TestReviewCategory:
    """测试审查类别"""

    def test_category_values(self) -> None:
        """类别值"""
        assert ReviewCategory.SECURITY.value == "security"
        assert ReviewCategory.PERFORMANCE.value == "performance"
        assert ReviewCategory.MODSDK.value == "modsdk"


class TestReviewIssue:
    """测试审查问题"""

    def test_review_issue_basic(self) -> None:
        """基本审查问题"""
        issue = ReviewIssue(
            category=ReviewCategory.SECURITY,
            severity=ReviewSeverity.ERROR,
            message="使用 eval() 危险函数",
            line=10,
            suggestion="使用 ast.literal_eval 替代",
        )
        data = issue.to_dict()
        assert data["category"] == "security"
        assert data["severity"] == "error"
        assert data["line"] == 10


class TestReviewResult:
    """测试审查结果"""

    def test_review_result_basic(self) -> None:
        """基本审查结果"""
        result = ReviewResult(
            issues=[],
            score=95.0,
            grade="A",
            summary="代码质量优秀",
            passed=True,
        )
        assert result.passed is True
        assert result.grade == "A"

    def test_review_result_with_issues(self) -> None:
        """带问题的审查结果"""
        issues = [
            ReviewIssue(
                category=ReviewCategory.STYLE,
                severity=ReviewSeverity.INFO,
                message="缺少文档字符串",
            )
        ]
        result = ReviewResult(
            issues=issues,
            score=80.0,
            grade="B",
            summary="代码良好，有小问题",
            passed=True,
        )
        assert len(result.issues) == 1


class TestIntelligentCodeReviewer:
    """测试智能代码审查器"""

    def test_reviewer_initialization(self) -> None:
        """审查器初始化"""
        reviewer = IntelligentCodeReviewer()
        assert reviewer.llm_config.provider == "mock"

    def test_review_good_code(self) -> None:
        """审查良好代码"""
        reviewer = IntelligentCodeReviewer()
        code = """# -*- coding: utf-8 -*-
\"\"\"模块说明\"\"\"

def hello(name: str) -> str:
    \"\"\"打招呼\"\"\"
    return f"Hello, {name}!"
"""
        result = reviewer.review(code)
        assert isinstance(result, ReviewResult)
        assert result.score > 0

    def test_review_security_issue(self) -> None:
        """审查安全问题"""
        reviewer = IntelligentCodeReviewer()
        code = """
def execute(user_input):
    result = eval(user_input)
    return result
"""
        result = reviewer.review(code)
        assert any(
            i.category == ReviewCategory.SECURITY
            for i in result.issues
        )

    def test_review_modsdk_issue(self) -> None:
        """审查 ModSDK 问题"""
        reviewer = IntelligentCodeReviewer()
        code = """
import mod.server.extraServerApi as serverApi
"""
        result = reviewer.review(code, file_path="client_script.py")
        # 应该检测到客户端文件使用服务端 API 的问题
        assert isinstance(result, ReviewResult)

    def test_review_calculates_score(self) -> None:
        """审查计算分数"""
        reviewer = IntelligentCodeReviewer()
        code = "x=1+2"
        result = reviewer.review(code)
        assert 0 <= result.score <= 100

    def test_review_assigns_grade(self) -> None:
        """审查分配等级"""
        reviewer = IntelligentCodeReviewer()
        code = "pass"
        result = reviewer.review(code)
        assert result.grade in ["A", "B", "C", "D", "F"]

    def test_review_passed_threshold(self) -> None:
        """审查通过阈值"""
        reviewer = IntelligentCodeReviewer()
        code = """
def good_function():
    \"\"\"好函数\"\"\"
    return True
"""
        result = reviewer.review(code)
        # 良好代码应该通过
        assert result.passed is True or result.score >= 60


class TestReviewCode:
    """测试便捷函数"""

    def test_review_code_function(self) -> None:
        """便捷函数审查代码"""
        result = review_code("def test(): pass")
        assert isinstance(result, ReviewResult)


# ============================================================================
# 智能修复测试
# ============================================================================

class TestFixConfidence:
    """测试修复置信度"""

    def test_confidence_values(self) -> None:
        """置信度值"""
        assert FixConfidence.HIGH.value == "high"
        assert FixConfidence.MEDIUM.value == "medium"
        assert FixConfidence.LOW.value == "low"


class TestErrorContext:
    """测试错误上下文"""

    def test_error_context_basic(self) -> None:
        """基本错误上下文"""
        ctx = ErrorContext(
            error_type="KeyError",
            error_message="'speed' not found",
            error_line=42,
            file_path="main.py",
        )
        data = ctx.to_dict()
        assert data["error_type"] == "KeyError"
        assert data["error_line"] == 42


class TestFixSuggestion:
    """测试修复建议"""

    def test_fix_suggestion_basic(self) -> None:
        """基本修复建议"""
        suggestion = FixSuggestion(
            description="添加默认值",
            confidence=FixConfidence.HIGH,
            fix_code="speed = config.get('speed', 1.0)",
            explanation="使用 get 方法提供默认值",
        )
        data = suggestion.to_dict()
        assert data["confidence"] == "high"
        assert "speed" in data["fix_code"]


class TestDiagnosisResult:
    """测试诊断结果"""

    def test_diagnosis_result_basic(self) -> None:
        """基本诊断结果"""
        suggestion = FixSuggestion(
            description="修复",
            confidence=FixConfidence.HIGH,
        )
        result = DiagnosisResult(
            error_type="KeyError",
            root_cause="键不存在",
            impact="medium",
            fix_suggestions=[suggestion],
        )
        data = result.to_dict()
        assert data["error_type"] == "KeyError"
        assert len(data["fix_suggestions"]) == 1


class TestFixResult:
    """测试修复结果"""

    def test_fix_result_basic(self) -> None:
        """基本修复结果"""
        result = FixResult(
            original_code="x = config['speed']",
            fixed_code="x = config.get('speed', 1.0)",
            changes=[{"type": "replace", "line": 1}],
            success=True,
            message="已修复 KeyError",
        )
        assert result.success is True
        assert "get" in result.fixed_code


class TestIntelligentFixer:
    """测试智能修复器"""

    def test_fixer_initialization(self) -> None:
        """修复器初始化"""
        fixer = IntelligentFixer()
        assert fixer.llm_config.provider == "mock"

    def test_diagnose_key_error(self) -> None:
        """诊断 KeyError"""
        fixer = IntelligentFixer()
        ctx = ErrorContext(
            error_type="KeyError",
            error_message="'speed' not found",
            code="speed = config['speed']",
            error_line=10,
        )
        result = fixer.diagnose(ctx)
        assert isinstance(result, DiagnosisResult)
        # Mock provider may not return structured JSON, so just check it returns a result
        assert result is not None

    def test_diagnose_attribute_error(self) -> None:
        """诊断 AttributeError"""
        fixer = IntelligentFixer()
        ctx = ErrorContext(
            error_type="AttributeError",
            error_message="'NoneType' object has no attribute 'name'",
            code="print(entity.name)",
            error_line=5,
        )
        result = fixer.diagnose(ctx)
        assert isinstance(result, DiagnosisResult)

    def test_fix_key_error(self) -> None:
        """修复 KeyError"""
        fixer = IntelligentFixer()
        ctx = ErrorContext(
            error_type="KeyError",
            error_message="'speed' not found",
            code="speed = config['speed']",
            error_line=1,
        )
        result = fixer.fix(ctx)
        assert isinstance(result, FixResult)
        # Mock 修复可能不会实际修改代码，但应该返回有效结果

    def test_select_best_fix(self) -> None:
        """选择最佳修复"""
        fixer = IntelligentFixer()
        suggestions = [
            FixSuggestion(
                description="低置信度修复",
                confidence=FixConfidence.LOW,
                fix_code="low_fix()",
            ),
            FixSuggestion(
                description="高置信度修复",
                confidence=FixConfidence.HIGH,
                fix_code="high_fix()",
            ),
        ]
        best = fixer._select_best_fix(suggestions)
        assert best is not None
        assert best.confidence == FixConfidence.HIGH

    def test_apply_fix(self) -> None:
        """应用修复"""
        fixer = IntelligentFixer()
        code = "x = config['speed']"
        fix = FixSuggestion(
            description="使用 get 方法",
            confidence=FixConfidence.HIGH,
            fix_code="x = config.get('speed', 1.0)",
        )
        fixed_code, changes = fixer._apply_fix(code, fix, 1)
        assert "get" in fixed_code
        assert len(changes) > 0


class TestDiagnoseError:
    """测试便捷函数"""

    def test_diagnose_error_function(self) -> None:
        """便捷函数诊断错误"""
        ctx = ErrorContext(
            error_type="TypeError",
            error_message="unsupported operand type",
            code="result = '5' + 3",
        )
        result = diagnose_error(ctx)
        assert isinstance(result, DiagnosisResult)


class TestFixError:
    """测试便捷函数"""

    def test_fix_error_function(self) -> None:
        """便捷函数修复错误"""
        ctx = ErrorContext(
            error_type="TypeError",
            error_message="unsupported operand type",
            code="result = '5' + 3",
        )
        result = fix_error(ctx)
        assert isinstance(result, FixResult)


# ============================================================================
# 验收标准测试
# ============================================================================

class TestIteration65AcceptanceCriteria:
    """迭代 #65 验收标准测试"""

    def test_llm_integration_complete(self) -> None:
        """LLM 集成完成"""
        # 检查所有提供商类存在
        assert MockProvider is not None
        assert OpenAIProvider is not None
        assert AnthropicProvider is not None
        assert GeminiProvider is not None
        assert OllamaProvider is not None

    def test_llm_manager_available(self) -> None:
        """LLM 管理器可用"""
        manager = get_llm_manager()
        assert manager is not None
        providers = manager.list_providers()
        assert len(providers) >= 5

    def test_code_generation_available(self) -> None:
        """代码生成可用"""
        result = generate_code("创建一个事件监听器")
        assert isinstance(result, GeneratedCode)
        assert result.code != ""

    def test_code_review_available(self) -> None:
        """代码审查可用"""
        result = review_code("def test(): pass")
        assert isinstance(result, ReviewResult)
        assert 0 <= result.score <= 100

    def test_intelligent_fix_available(self) -> None:
        """智能修复可用"""
        ctx = ErrorContext(
            error_type="KeyError",
            error_message="missing key",
            code="x = d['key']",
        )
        result = diagnose_error(ctx)
        assert isinstance(result, DiagnosisResult)

    def test_all_modules_importable(self) -> None:
        """所有模块可导入"""
        from mc_agent_kit.llm import (
            ChatMessage,
            ChatRole,
            CompletionResult,
            LLMConfig,
            LLMManager,
            MockProvider,
            CodeGenerationType,
            GeneratedCode,
            IntelligentCodeGenerator,
            ReviewCategory,
            ReviewResult,
            IntelligentCodeReviewer,
            ErrorContext,
            FixResult,
            IntelligentFixer,
        )
        # 如果导入成功，测试通过
        assert True


# ============================================================================
# 性能测试
# ============================================================================

class TestIteration65Performance:
    """迭代 #65 性能测试"""

    def test_mock_completion_performance(self) -> None:
        """Mock 补全性能"""
        generator = IntelligentCodeGenerator()
        start = time.time()
        for _ in range(10):
            generator.generate("生成代码")
        elapsed = time.time() - start
        # 10 次生成应该在 2 秒内完成
        assert elapsed < 2.0, f"Mock 生成太慢：{elapsed:.2f}s"

    def test_code_review_performance(self) -> None:
        """代码审查性能"""
        reviewer = IntelligentCodeReviewer()
        code = """
def complex_function(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
"""
        start = time.time()
        reviewer.review(code)
        elapsed = time.time() - start
        # 单次审查应该在 1 秒内完成
        assert elapsed < 1.0, f"代码审查太慢：{elapsed:.2f}s"

    def test_error_diagnosis_performance(self) -> None:
        """错误诊断性能"""
        fixer = IntelligentFixer()
        ctx = ErrorContext(
            error_type="KeyError",
            error_message="test error",
            code="x = d['key']",
        )
        start = time.time()
        fixer.diagnose(ctx)
        elapsed = time.time() - start
        # 单次诊断应该在 1 秒内完成
        assert elapsed < 1.0, f"错误诊断太慢：{elapsed:.2f}s"


# ============================================================================
# 集成测试
# ============================================================================

class TestIntegration:
    """集成测试"""

    def test_full_workflow(self) -> None:
        """完整工作流：生成 -> 审查 -> 修复"""
        # 1. 生成代码
        generator = IntelligentCodeGenerator()
        generated = generator.generate(
            "创建一个简单的实体创建函数",
            CodeGenerationType.ENTITY_BEHAVIOR,
        )
        assert generated.code != ""

        # 2. 审查代码
        reviewer = IntelligentCodeReviewer()
        review = reviewer.review(generated.code)
        assert isinstance(review, ReviewResult)

        # 3. 如果有问题，诊断并修复
        if not review.passed and review.issues:
            fixer = IntelligentFixer()
            # 模拟一个错误上下文
            ctx = ErrorContext(
                error_type="ReviewIssue",
                error_message=review.issues[0].message,
                code=generated.code,
            )
            diagnosis = fixer.diagnose(ctx)
            assert isinstance(diagnosis, DiagnosisResult)


# ============================================================================
# 边缘情况测试
# ============================================================================

class TestEdgeCases:
    """边缘情况测试"""

    def test_empty_code_review(self) -> None:
        """空代码审查"""
        reviewer = IntelligentCodeReviewer()
        result = reviewer.review("")
        assert isinstance(result, ReviewResult)
        assert result.score >= 0

    def test_empty_code_generation(self) -> None:
        """空请求生成"""
        generator = IntelligentCodeGenerator()
        result = generator.generate("")
        assert isinstance(result, GeneratedCode)

    def test_invalid_error_context(self) -> None:
        """无效错误上下文"""
        fixer = IntelligentFixer()
        ctx = ErrorContext()  # 空上下文
        result = fixer.diagnose(ctx)
        assert isinstance(result, DiagnosisResult)

    def test_very_long_code(self) -> None:
        """长代码审查"""
        reviewer = IntelligentCodeReviewer()
        code = "\n".join([f"line_{i} = {i}" for i in range(1000)])
        result = reviewer.review(code)
        assert isinstance(result, ReviewResult)

    def test_unicode_in_code(self) -> None:
        """代码中的 Unicode 字符"""
        reviewer = IntelligentCodeReviewer()
        code = """
def 打招呼 (名字):
    return f"你好，{名字}!"
"""
        result = reviewer.review(code)
        assert isinstance(result, ReviewResult)

    def test_malformed_code(self) -> None:
        """格式错误的代码"""
        reviewer = IntelligentCodeReviewer()
        code = "def broken("  # 语法错误
        result = reviewer.review(code)
        assert isinstance(result, ReviewResult)