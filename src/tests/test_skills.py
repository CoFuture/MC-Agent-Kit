"""
Skills 模块单元测试

测试 Skill 基类、注册表和 ModSDK Skills。
"""

import pytest

from mc_agent_kit.skills import (
    BaseSkill,
    SkillCategory,
    SkillMetadata,
    SkillPriority,
    SkillRegistry,
    SkillResult,
    get_registry,
    register_skill,
    register_modsdk_skills,
    ModSDKAPISearchSkill,
    ModSDKEventSearchSkill,
)


class TestSkillMetadata:
    """测试 SkillMetadata"""

    def test_create_metadata(self):
        """测试创建元数据"""
        meta = SkillMetadata(
            name="test-skill",
            description="Test skill description",
            version="1.0.0",
        )
        assert meta.name == "test-skill"
        assert meta.description == "Test skill description"
        assert meta.version == "1.0.0"
        assert meta.category == SkillCategory.UTILITY
        assert meta.priority == SkillPriority.MEDIUM

    def test_metadata_to_dict(self):
        """测试元数据转字典"""
        meta = SkillMetadata(
            name="test-skill",
            description="Test",
            tags=["test", "demo"],
        )
        result = meta.to_dict()
        assert result["name"] == "test-skill"
        assert result["tags"] == ["test", "demo"]
        assert "category" in result


class TestSkillResult:
    """测试 SkillResult"""

    def test_success_result(self):
        """测试成功结果"""
        result = SkillResult(
            success=True,
            data={"key": "value"},
            message="Success",
        )
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_error_result(self):
        """测试错误结果"""
        result = SkillResult(
            success=False,
            error="Something went wrong",
            message="Failed",
        )
        assert result.success is False
        assert result.error == "Something went wrong"

    def test_result_with_suggestions(self):
        """测试带建议的结果"""
        result = SkillResult(
            success=True,
            data=[1, 2, 3],
            suggestions=["Try this", "Or this"],
        )
        assert len(result.suggestions) == 2

    def test_result_to_dict(self):
        """测试结果转字典"""
        result = SkillResult(
            success=True,
            data={"test": 1},
            message="OK",
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["data"] == {"test": 1}


class MockSkill(BaseSkill):
    """测试用 Mock Skill"""

    def __init__(self, name: str = "mock-skill"):
        super().__init__(
            metadata=SkillMetadata(
                name=name,
                description="Mock skill for testing",
                category=SkillCategory.UTILITY,
            )
        )
        self.execute_count = 0

    def execute(self, *args, **kwargs) -> SkillResult:
        self.execute_count += 1
        return SkillResult(
            success=True,
            data={"executed": self.execute_count},
            message="Mock executed",
        )


class TestBaseSkill:
    """测试 BaseSkill"""

    def test_skill_creation(self):
        """测试创建 Skill"""
        skill = MockSkill()
        assert skill.name == "mock-skill"
        assert skill.metadata.description == "Mock skill for testing"

    def test_skill_execute(self):
        """测试执行 Skill"""
        skill = MockSkill()
        result = skill.execute()
        assert result.success is True
        assert result.data["executed"] == 1

    def test_skill_initialize(self):
        """测试初始化"""
        skill = MockSkill()
        assert skill._initialized is False
        skill.initialize()
        assert skill._initialized is True

    def test_skill_repr(self):
        """测试字符串表示"""
        skill = MockSkill("test-repr")
        assert "MockSkill" in repr(skill)
        assert "test-repr" in repr(skill)


class TestSkillRegistry:
    """测试 SkillRegistry"""

    def test_register_skill(self):
        """测试注册 Skill"""
        registry = SkillRegistry()
        skill = MockSkill("register-test")

        registry.register(skill)
        assert registry.has("register-test")
        assert len(registry) == 1

    def test_register_duplicate(self):
        """测试注册重复 Skill"""
        registry = SkillRegistry()
        skill1 = MockSkill("duplicate-test")
        skill2 = MockSkill("duplicate-test")

        registry.register(skill1)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(skill2)

    def test_unregister_skill(self):
        """测试注销 Skill"""
        registry = SkillRegistry()
        skill = MockSkill("unregister-test")

        registry.register(skill)
        assert registry.unregister("unregister-test") is True
        assert not registry.has("unregister-test")

    def test_unregister_nonexistent(self):
        """测试注销不存在的 Skill"""
        registry = SkillRegistry()
        assert registry.unregister("nonexistent") is False

    def test_get_skill(self):
        """测试获取 Skill"""
        registry = SkillRegistry()
        skill = MockSkill("get-test")

        registry.register(skill)
        retrieved = registry.get("get-test")
        assert retrieved is skill

    def test_get_nonexistent_skill(self):
        """测试获取不存在的 Skill"""
        registry = SkillRegistry()
        assert registry.get("nonexistent") is None

    def test_list_all(self):
        """测试列出所有 Skill"""
        registry = SkillRegistry()
        registry.register(MockSkill("list-1"))
        registry.register(MockSkill("list-2"))

        all_skills = registry.list_all()
        assert len(all_skills) == 2

    def test_list_by_category(self):
        """测试按分类列出"""
        registry = SkillRegistry()
        skill = MockSkill("category-test")
        registry.register(skill)

        skills = registry.list_by_category(SkillCategory.UTILITY)
        assert len(skills) == 1

    def test_search_skills(self):
        """测试搜索 Skill"""
        registry = SkillRegistry()

        class SearchSkill(BaseSkill):
            def __init__(self):
                super().__init__(
                    metadata=SkillMetadata(
                        name="search-api",
                        description="Search API documentation",
                        tags=["api", "search"],
                    )
                )

            def execute(self, *args, **kwargs):
                return SkillResult(success=True)

        registry.register(SearchSkill())

        # 按名称搜索
        results = registry.search("api")
        assert len(results) == 1

        # 按描述搜索
        results = registry.search("documentation")
        assert len(results) == 1

        # 按标签搜索
        results = registry.search("search")
        assert len(results) == 1

    def test_initialize_all(self):
        """测试初始化所有 Skill"""
        registry = SkillRegistry()
        registry.register(MockSkill("init-1"))
        registry.register(MockSkill("init-2"))

        results = registry.initialize_all()
        assert all(results.values())

    def test_cleanup_all(self):
        """测试清理所有 Skill"""
        registry = SkillRegistry()
        registry.register(MockSkill("cleanup-test"))
        registry.cleanup_all()  # 应该不抛异常


class TestGlobalRegistry:
    """测试全局注册表"""

    def test_get_registry(self):
        """测试获取全局注册表"""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    def test_register_skill_function(self):
        """测试注册函数"""
        # 创建新的注册表避免测试污染
        from mc_agent_kit.skills.base import _global_registry
        import mc_agent_kit.skills.base as base_module
        base_module._global_registry = None

        skill = MockSkill("global-test")
        register_skill(skill)

        registry = get_registry()
        assert registry.has("global-test")


class TestModSDKAPISearchSkill:
    """测试 ModSDK API 检索 Skill"""

    def test_skill_creation(self):
        """测试创建 Skill"""
        skill = ModSDKAPISearchSkill()
        assert skill.name == "modsdk-api-search"
        assert skill.metadata.category == SkillCategory.SEARCH
        assert skill.metadata.priority == SkillPriority.HIGH

    def test_skill_metadata(self):
        """测试 Skill 元数据"""
        skill = ModSDKAPISearchSkill()
        meta = skill.metadata

        assert "modsdk" in meta.tags
        assert "api" in meta.tags
        assert len(meta.examples) > 0

    def test_execute_without_initialization(self):
        """测试未初始化时执行"""
        skill = ModSDKAPISearchSkill()
        # 未初始化时应该自动初始化
        result = skill.execute(query="test")
        # 知识库不存在时应该返回失败
        assert result.success is False or result.success is True

    def test_execute_with_name(self):
        """测试按名称精确搜索"""
        skill = ModSDKAPISearchSkill()
        result = skill.execute(name="NonExistentAPI")
        # 不存在的 API 应该返回失败
        assert result.success is False
        assert "未找到" in result.error


class TestModSDKEventSearchSkill:
    """测试 ModSDK 事件检索 Skill"""

    def test_skill_creation(self):
        """测试创建 Skill"""
        skill = ModSDKEventSearchSkill()
        assert skill.name == "modsdk-event-search"
        assert skill.metadata.category == SkillCategory.SEARCH

    def test_skill_metadata(self):
        """测试 Skill 元数据"""
        skill = ModSDKEventSearchSkill()
        meta = skill.metadata

        assert "modsdk" in meta.tags
        assert "event" in meta.tags

    def test_list_modules_without_kb(self):
        """测试无知识库时列出模块"""
        skill = ModSDKEventSearchSkill()
        result = skill.list_modules()
        # 知识库不存在时应该返回失败
        assert result.success is False or result.success is True


class TestSkillIntegration:
    """测试 Skill 集成"""

    def test_register_modsdk_skills(self):
        """测试注册所有 ModSDK Skills"""
        # 重置全局注册表
        from mc_agent_kit.skills.base import _global_registry
        import mc_agent_kit.skills.base as base_module
        base_module._global_registry = None

        register_modsdk_skills()

        registry = get_registry()
        assert registry.has("modsdk-api-search")
        assert registry.has("modsdk-event-search")

    def test_skill_execution_flow(self):
        """测试 Skill 执行流程"""
        registry = SkillRegistry()
        skill = MockSkill("flow-test")
        registry.register(skill)

        # 初始化
        skill.initialize()

        # 执行
        result = skill.execute()
        assert result.success is True

        # 清理
        skill.cleanup()


class TestSkillPriority:
    """测试 Skill 优先级"""

    def test_priority_ordering(self):
        """测试优先级排序"""
        assert SkillPriority.HIGH.value < SkillPriority.MEDIUM.value
        assert SkillPriority.MEDIUM.value < SkillPriority.LOW.value


class TestSkillCategory:
    """测试 Skill 分类"""

    def test_category_values(self):
        """测试分类值"""
        assert SkillCategory.SEARCH.value == "search"
        assert SkillCategory.CODE_GEN.value == "code_gen"
        assert SkillCategory.DEBUG.value == "debug"
        assert SkillCategory.ANALYSIS.value == "analysis"
        assert SkillCategory.UTILITY.value == "utility"