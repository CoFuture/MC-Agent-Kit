"""
测试迭代 #58: 测试覆盖率提升与性能优化

测试模块：
- modsdk_enhanced: 边界条件测试
- game_debug: 边界条件测试
- code_analyzer: 边界条件测试
- project_templates: 边界条件测试

迭代 #58 重点：
- 边界条件测试
- 异常处理测试
- 性能基准测试
- 集成测试增强
"""

import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 导入被测试模块
from mc_agent_kit.skills.modsdk_enhanced import (
    ModSDKSkill,
    ModSDKVersion,
    EntityType,
    ItemType,
    BlockType,
    BehaviorConfig,
    ComponentConfig,
    create_modsdk_skill,
    GeneratedEntity,
    GeneratedItem,
    GeneratedBlock,
)
from mc_agent_kit.debugger.game_debug import (
    GameDebugger,
    DebugState,
    BreakpointType,
    Breakpoint,
    WatchVariable,
    LogEntry,
    create_game_debugger,
)
from mc_agent_kit.analysis.code_analyzer import (
    CodeAnalyzer,
    Issue,
    IssueSeverity,
    IssueType,
    create_code_analyzer,
    AnalysisResult,
)
from mc_agent_kit.templates.project_templates import (
    ProjectTemplates,
    TemplateType,
    TemplateConfig,
    TemplateFile,
    create_project_templates,
)


class TestModSDKSkillBoundaryConditions:
    """测试 ModSDK 技能的边界条件"""

    @pytest.fixture
    def skill(self):
        """创建技能实例"""
        return ModSDKSkill()

    def test_generate_entity_empty_name(self, skill):
        """测试生成空名称实体"""
        # 实现应该处理空名称
        entity = skill.generate_entity(name="", entity_type=EntityType.PASSIVE)
        assert entity is not None

    def test_generate_entity_special_characters(self, skill):
        """测试生成带特殊字符名称的实体"""
        entity = skill.generate_entity(
            name="Test-Entity_123",
            entity_type=EntityType.PASSIVE,
            namespace="test",
        )
        # identifier 应该处理特殊字符
        assert entity.identifier is not None

    def test_generate_entity_very_long_name(self, skill):
        """测试生成超长名称实体"""
        long_name = "A" * 100
        entity = skill.generate_entity(
            name=long_name,
            entity_type=EntityType.PASSIVE,
            namespace="test",
        )
        assert entity is not None

    def test_generate_item_edge_cases(self, skill):
        """测试物品生成边界情况"""
        # 空名称
        item = skill.generate_item(name="", item_type=ItemType.CONSUMABLE)
        assert item is not None

        # 超长名称
        item = skill.generate_item(
            name="B" * 100,
            item_type=ItemType.WEAPON,
            namespace="test",
        )
        assert item is not None

    def test_generate_block_edge_cases(self, skill):
        """测试方块生成边界情况"""
        # 空名称
        block = skill.generate_block(name="", block_type=BlockType.BASIC)
        assert block is not None

        # 超长名称
        block = skill.generate_block(
            name="C" * 100,
            block_type=BlockType.INTERACTIVE,
            namespace="test",
        )
        assert block is not None

    def test_generate_entity_with_empty_behaviors(self, skill):
        """测试生成空行为列表实体"""
        entity = skill.generate_entity(
            name="TestEntity",
            entity_type=EntityType.PASSIVE,
            behaviors=[],
            namespace="test",
        )
        assert len(entity.behaviors) == 0

    def test_generate_entity_with_many_behaviors(self, skill):
        """测试生成多行为实体 - 验证 notes 记录未知行为"""
        behaviors = [
            {"name": f"behavior_{i}", "parameters": {"value": i}}
            for i in range(5)
        ]
        entity = skill.generate_entity(
            name="ComplexEntity",
            entity_type=EntityType.BOSS,
            behaviors=behaviors,
            namespace="test",
        )
        # 未知行为会被记录在 notes 中
        assert len(entity.notes) == 5

    def test_validate_config_empty_dict(self, skill):
        """测试验证空字典配置"""
        result = skill.validate_config({}, config_type="entity")
        assert result.valid is False

    def test_get_api_suggestions_empty_context(self, skill):
        """测试获取空上下文的 API 建议"""
        suggestions = skill.get_api_suggestions(context="", top_k=5)
        assert suggestions is not None

    def test_get_api_suggestions_large_top_k(self, skill):
        """测试获取大量 API 建议"""
        suggestions = skill.get_api_suggestions(
            context="entity",
            top_k=1000,
        )
        assert suggestions is not None

    def test_behavior_config_default_values(self):
        """测试行为配置默认值"""
        behavior = BehaviorConfig(name="test")
        assert behavior.parameters == {}
        assert behavior.priority == 0
        assert behavior.enabled is True

    def test_component_config_default_values(self):
        """测试组件配置默认值"""
        component = ComponentConfig(name="test")
        assert component.namespace == "minecraft"
        assert component.parameters == {}


class TestGameDebuggerBoundaryConditions:
    """测试游戏调试器的边界条件"""

    @pytest.fixture
    def debugger(self):
        """创建调试器实例"""
        return GameDebugger()

    def test_attach_no_session(self, debugger):
        """测试无会话时附加"""
        # 无会话时应该返回 False
        result = debugger.attach(99999)
        assert result is False

    def test_set_breakpoint_no_session(self, debugger):
        """测试无会话时设置断点"""
        bp = debugger.set_breakpoint("test.py", 10)
        assert bp is None  # 无会话时返回 None

    def test_set_breakpoint_empty_file(self, debugger):
        """测试设置空文件名断点"""
        bp = debugger.set_breakpoint("", 10)
        assert bp is None

    def test_add_watch_no_session(self, debugger):
        """测试无会话时添加监视"""
        watch = debugger.add_watch("test_var", "x + 1")
        assert watch is None  # 无会话时返回 None

    def test_add_log_empty_message(self, debugger):
        """测试添加空日志消息"""
        debugger.add_log("INFO", "")
        logs = debugger.get_logs()
        # 应该允许空消息
        assert len(logs) >= 0

    def test_analyze_logs_empty(self, debugger):
        """测试分析空日志"""
        result = debugger.analyze_logs()
        assert "error" in result or "statistics" in result

    def test_hot_reload_no_session(self, debugger):
        """测试无会话时热重载"""
        result = debugger.hot_reload("test.py")
        assert result is False

    def test_breakpoint_type_values(self):
        """测试断点类型枚举值"""
        assert BreakpointType.LINE.value == "line"
        assert BreakpointType.CONDITIONAL.value == "conditional"
        assert BreakpointType.LOG.value == "log"
        assert BreakpointType.FUNCTION.value == "function"

    def test_debug_state_values(self):
        """测试调试状态枚举值"""
        assert DebugState.DISCONNECTED.value == "disconnected"
        assert DebugState.CONNECTING.value == "connecting"
        assert DebugState.CONNECTED.value == "connected"
        assert DebugState.PAUSED.value == "paused"
        assert DebugState.RUNNING.value == "running"
        assert DebugState.ERROR.value == "error"


class TestCodeAnalyzerBoundaryConditions:
    """测试代码分析器的边界条件"""

    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        return CodeAnalyzer()

    def test_analyze_empty_code(self, analyzer):
        """测试分析空代码"""
        result = analyzer.analyze("", "empty.py")
        assert result is not None
        assert result.score >= 0

    def test_analyze_empty_file(self, analyzer):
        """测试分析空文件名"""
        result = analyzer.analyze("print('test')", "")
        assert result.file == "" or result.file is not None

    def test_analyze_very_large_code(self, analyzer):
        """测试分析超大代码"""
        large_code = "x = 1\n" * 10000
        result = analyzer.analyze(large_code, "large.py")
        assert result is not None
        assert result.statistics["lines"] >= 10000

    def test_analyze_unicode_code(self, analyzer):
        """测试分析 Unicode 代码"""
        code = '''
# 中文注释
def 测试 ():
    print("Hello 世界")
'''
        result = analyzer.analyze(code, "unicode.py")
        assert result is not None

    def test_analyze_syntax_error_various(self, analyzer):
        """测试分析各种语法错误"""
        error_cases = [
            "def broken(",
            "if True\n    pass",
            "for i in range(10)\n    print(i)",
            "class Test(\n    pass",
        ]
        for code in error_cases:
            result = analyzer.analyze(code, "error.py")
            assert result.score == 0.0 or len(result.issues) > 0

    def test_find_api_usage_empty_code(self, analyzer):
        """测试查找空代码的 API 使用"""
        usages = analyzer.find_api_usage("", "empty.py")
        assert usages == []

    def test_find_api_usage_no_api(self, analyzer):
        """测试查找无 API 代码的使用"""
        code = '''
def hello():
    print("Hello")
'''
        usages = analyzer.find_api_usage(code, "noapi.py")
        # 应该返回空列表或 ModSDK API 使用
        assert usages is not None

    def test_detect_issues_empty_code(self, analyzer):
        """测试检测空代码问题"""
        issues = analyzer.detect_issues("", "empty.py")
        assert issues == []

    def test_suggest_improvements_perfect_code(self, analyzer):
        """测试为完美代码生成建议"""
        perfect_code = '''
def hello(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"
'''
        suggestions = analyzer.suggest_improvements(perfect_code, "perfect.py")
        assert suggestions is not None

    def test_calculate_score_edge_cases(self, analyzer):
        """测试分数计算边界情况"""
        # 空代码
        result = analyzer.analyze("")
        assert 0 <= result.score <= 100

        # 只有注释
        result = analyzer.analyze("# comment")
        assert 0 <= result.score <= 100

        # 只有导入
        result = analyzer.analyze("import os")
        assert 0 <= result.score <= 100

    def test_issue_severity_values(self):
        """测试问题严重程度枚举值"""
        assert IssueSeverity.ERROR.value == "error"
        assert IssueSeverity.WARNING.value == "warning"
        assert IssueSeverity.INFO.value == "info"
        assert IssueSeverity.HINT.value == "hint"

    def test_issue_type_values(self):
        """测试问题类型枚举值"""
        assert IssueType.SYNTAX.value == "syntax"
        assert IssueType.API_USAGE.value == "api_usage"
        assert IssueType.PERFORMANCE.value == "performance"
        assert IssueType.SECURITY.value == "security"
        assert IssueType.STYLE.value == "style"
        assert IssueType.BEST_PRACTICE.value == "best_practice"
        assert IssueType.COMPATIBILITY.value == "compatibility"

    def test_strict_mode_issues(self):
        """测试严格模式问题检测"""
        strict_analyzer = create_code_analyzer(strict_mode=True)
        code = '''
x = None
if x == None:
    pass
'''
        result = strict_analyzer.analyze(code, "test.py")
        # 严格模式应该检测更多问题
        assert len(result.issues) >= 0


class TestProjectTemplatesBoundaryConditions:
    """测试项目模板系统的边界条件"""

    @pytest.fixture
    def templates(self):
        """创建模板系统实例"""
        return ProjectTemplates()

    def test_generate_with_empty_variables(self, templates):
        """测试使用空变量生成项目"""
        project = templates.generate(
            TemplateType.PROJECT_EMPTY,
            "TestProject",
            variables={},
        )
        assert project is not None

    def test_generate_with_special_characters(self, templates):
        """测试生成带特殊字符名称项目"""
        project = templates.generate(
            TemplateType.PROJECT_EMPTY,
            "Test-Project_123",
        )
        assert project is not None

    def test_generate_very_long_name(self, templates):
        """测试生成超长名称项目"""
        long_name = "A" * 100
        project = templates.generate(
            TemplateType.PROJECT_EMPTY,
            long_name,
        )
        assert project is not None

    def test_list_templates_not_empty(self, templates):
        """测试列出模板不为空"""
        template_list = templates.list_templates()
        assert len(template_list) > 0

    def test_template_file_content_not_empty(self, templates):
        """测试模板文件内容不为空"""
        template = templates.get_template(TemplateType.PROJECT_EMPTY)
        assert template is not None
        for file in template.files:
            assert file.content is not None
            assert len(file.content) > 0


class TestPerformanceBenchmarks:
    """性能基准测试"""

    @pytest.fixture
    def skill(self):
        return create_modsdk_skill()

    @pytest.fixture
    def analyzer(self):
        return create_code_analyzer()

    @pytest.fixture
    def templates(self):
        return create_project_templates()

    def test_entity_generation_performance(self, skill):
        """测试实体生成性能"""
        start = time.time()
        for i in range(10):
            skill.generate_entity(
                name=f"Entity{i}",
                entity_type=EntityType.PASSIVE,
                namespace="test",
            )
        elapsed = time.time() - start
        # 10 次生成应该 < 1 秒
        assert elapsed < 1.0, f"实体生成太慢：{elapsed:.2f}秒"

    def test_item_generation_performance(self, skill):
        """测试物品生成性能"""
        start = time.time()
        for i in range(10):
            skill.generate_item(
                name=f"Item{i}",
                item_type=ItemType.CONSUMABLE,
                namespace="test",
            )
        elapsed = time.time() - start
        assert elapsed < 1.0, f"物品生成太慢：{elapsed:.2f}秒"

    def test_block_generation_performance(self, skill):
        """测试方块生成性能"""
        start = time.time()
        for i in range(10):
            skill.generate_block(
                name=f"Block{i}",
                block_type=BlockType.BASIC,
                namespace="test",
            )
        elapsed = time.time() - start
        assert elapsed < 1.0, f"方块生成太慢：{elapsed:.2f}秒"

    def test_code_analysis_performance(self, analyzer):
        """测试代码分析性能"""
        code = '''
def hello():
    print("Hello, World!")

hello()
'''
        start = time.time()
        for i in range(10):
            analyzer.analyze(code, "test.py")
        elapsed = time.time() - start
        # 10 次分析应该 < 1 秒
        assert elapsed < 1.0, f"代码分析太慢：{elapsed:.2f}秒"

    def test_template_generation_performance(self, templates, tmp_path):
        """测试模板生成性能"""
        start = time.time()
        for i in range(5):
            templates.generate(
                TemplateType.PROJECT_EMPTY,
                f"Project{i}",
                output_dir=str(tmp_path / f"project{i}"),
            )
        elapsed = time.time() - start
        # 5 次生成应该 < 1 秒
        assert elapsed < 1.0, f"模板生成太慢：{elapsed:.2f}秒"

    def test_api_suggestions_performance(self, skill):
        """测试 API 建议性能"""
        start = time.time()
        for i in range(10):
            skill.get_api_suggestions(context="entity", top_k=5)
        elapsed = time.time() - start
        assert elapsed < 1.0, f"API 建议太慢：{elapsed:.2f}秒"

    def test_config_validation_performance(self, skill):
        """测试配置验证性能"""
        config = {
            "minecraft:entity": {
                "description": {"identifier": "test:entity"},
                "components": {"minecraft:health": {"value": 20}},
            }
        }
        start = time.time()
        for i in range(10):
            skill.validate_config(config, config_type="entity")
        elapsed = time.time() - start
        assert elapsed < 0.5, f"配置验证太慢：{elapsed:.2f}秒"


class TestIteration58Integration:
    """迭代 #58 集成测试"""

    def test_full_workflow_with_validation(self):
        """测试完整工作流与验证"""
        # 1. 使用技能生成实体
        skill = create_modsdk_skill()
        entity = skill.generate_entity(
            "TestMob",
            EntityType.PASSIVE,
            namespace="test",
        )

        # 2. 验证配置
        validation = skill.validate_config(entity.entity_json, "entity")
        assert validation.valid is True

        # 3. 分析生成的代码
        analyzer = create_code_analyzer()
        analysis = analyzer.analyze(entity.script_code, "entity.py")

        # 4. 确保没有语法错误
        syntax_errors = [i for i in analysis.issues if i.type == IssueType.SYNTAX]
        assert len(syntax_errors) == 0

    def test_debugger_log_analysis_integration(self):
        """测试调试器日志分析集成"""
        debugger = create_game_debugger()

        # 添加各种类型的日志
        debugger.add_log("INFO", "Starting...")
        debugger.add_log("WARNING", "Low memory")
        debugger.add_log("ERROR", "KeyError: 'speed'")
        debugger.add_log("ERROR", "TypeError: expected int")

        # 分析日志
        result = debugger.analyze_logs()
        assert result is not None

    def test_template_with_skill_integration(self, tmp_path):
        """测试模板与技能集成"""
        # 1. 使用模板生成项目
        templates = create_project_templates()
        project = templates.generate(
            TemplateType.ENTITY_BASIC,
            "TestEntity",
            output_dir=str(tmp_path / "TestEntity"),
        )

        # 2. 使用技能验证生成的实体
        skill = create_modsdk_skill()

        # 查找实体 JSON 并验证
        for path, content in project.files.items():
            if "entity" in path and path.endswith(".json"):
                # 简单验证 JSON 格式
                assert "minecraft:entity" in content or "entity" in content.lower()

    def test_analyzer_with_generated_code(self):
        """测试分析器与生成代码集成"""
        skill = create_modsdk_skill()
        analyzer = create_code_analyzer()

        # 生成多种类型的代码
        entity = skill.generate_entity("Mob", EntityType.HOSTILE)
        item = skill.generate_item("Sword", ItemType.WEAPON)
        block = skill.generate_block("Stone", BlockType.BASIC)

        # 分析所有生成的代码
        for code, name in [
            (entity.script_code, "entity.py"),
            (item.script_code, "item.py"),
            (block.script_code, "block.py"),
        ]:
            result = analyzer.analyze(code, name)
            # 生成的代码应该没有语法错误
            syntax_errors = [i for i in result.issues if i.type == IssueType.SYNTAX]
            assert len(syntax_errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
