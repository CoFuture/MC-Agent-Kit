"""
代码生成和调试 Skills 测试
"""

import pytest

from mc_agent_kit.skills import (
    ModSDKCodeGenSkill,
    ModSDKDebugSkill,
    SkillRegistry,
)


class TestModSDKCodeGenSkill:
    """代码生成 Skill 测试"""

    @pytest.fixture
    def skill(self):
        """创建代码生成 Skill"""
        skill = ModSDKCodeGenSkill()
        skill.initialize()
        return skill

    def test_skill_metadata(self, skill):
        """测试 Skill 元数据"""
        assert skill.name == "modsdk-code-gen"
        assert skill.metadata.category.value == "code_gen"
        assert skill.metadata.priority.value == 1  # HIGH

    def test_list_templates(self, skill):
        """测试列出模板"""
        result = skill.execute(action="list")

        assert result.success
        assert len(result.data) > 0

        template_names = [t["name"] for t in result.data]
        assert "event_listener" in template_names

    def test_get_template_info(self, skill):
        """测试获取模板信息"""
        result = skill.execute(action="info", template="event_listener")

        assert result.success
        assert result.data["name"] == "event_listener"
        assert "parameters" in result.data

    def test_generate_event_listener(self, skill):
        """测试生成事件监听器"""
        result = skill.execute(
            template="event_listener",
            params={"event_name": "OnServerChat", "scope": "服务端"},
        )

        assert result.success
        assert "code" in result.data
        assert "OnServerChat" in result.data["code"]
        assert "服务端" in result.data["code"]

    def test_generate_api_call(self, skill):
        """测试生成 API 调用"""
        result = skill.execute(
            template="api_call",
            params={"api_name": "GetEngineType"},
        )

        assert result.success
        assert "code" in result.data
        assert "GetEngineType" in result.data["code"]

    def test_generate_with_missing_required_param(self, skill):
        """测试缺少必需参数"""
        result = skill.execute(template="event_listener", params={})

        assert not result.success
        assert "缺少必需参数" in result.error

    def test_generate_with_invalid_template(self, skill):
        """测试无效模板"""
        result = skill.execute(template="invalid_template", params={})

        assert not result.success
        assert "模板不存在" in result.error

    def test_search_templates(self, skill):
        """测试搜索模板"""
        result = skill.execute(action="search", keyword="event")

        assert result.success
        assert len(result.data) > 0

    def test_custom_template(self, skill):
        """测试自定义模板"""
        result = skill.execute(
            custom_template="Hello, {{ name }}!",
            params={"name": "ModSDK"},
        )

        assert result.success
        assert result.data["code"] == "Hello, ModSDK!"

    def test_convenience_methods(self, skill):
        """测试便捷方法"""
        # generate_event_listener
        result = skill.generate_event_listener("OnPlayerDeath")
        assert result.success
        assert "OnPlayerDeath" in result.data["code"]

        # generate_api_call
        result = skill.generate_api_call("GetPlayerName")
        assert result.success
        assert "GetPlayerName" in result.data["code"]


class TestModSDKDebugSkill:
    """调试辅助 Skill 测试"""

    @pytest.fixture
    def skill(self):
        """创建调试辅助 Skill"""
        skill = ModSDKDebugSkill()
        skill.initialize()
        return skill

    def test_skill_metadata(self, skill):
        """测试 Skill 元数据"""
        assert skill.name == "modsdk-debug"
        assert skill.metadata.category.value == "debug"
        assert skill.metadata.priority.value == 1  # HIGH

    def test_list_error_patterns(self, skill):
        """测试列出错误模式"""
        result = skill.execute(action="list_errors")

        assert result.success
        assert len(result.data) > 0

        error_types = [e["error_type"] for e in result.data]
        assert "SyntaxError" in error_types
        assert "NameError" in error_types

    def test_diagnose_syntax_error(self, skill):
        """测试诊断语法错误"""
        result = skill.execute(
            action="diagnose",
            log_content="SyntaxError: invalid syntax on line 10",
        )

        assert result.success
        assert len(result.data) > 0

        error = result.data[0]
        assert error["error_type"] == "SyntaxError"
        assert error["category"] == "syntax"
        assert len(error["suggestions"]) > 0

    def test_diagnose_name_error(self, skill):
        """测试诊断 NameError"""
        result = skill.execute(
            action="diagnose",
            log_content="NameError: name 'player_id' is not defined",
        )

        assert result.success
        assert len(result.data) > 0

        error = result.data[0]
        assert error["error_type"] == "NameError"
        assert error["category"] == "runtime"

    def test_diagnose_type_error(self, skill):
        """测试诊断 TypeError"""
        result = skill.execute(
            action="diagnose",
            log_content="TypeError: 'NoneType' object is not callable",
        )

        assert result.success
        assert len(result.data) > 0

        error = result.data[0]
        assert error["error_type"] == "TypeError"

    def test_diagnose_attribute_error(self, skill):
        """测试诊断 AttributeError"""
        result = skill.execute(
            action="diagnose",
            log_content="AttributeError: 'dict' object has no attribute 'name'",
        )

        assert result.success
        assert len(result.data) > 0

        error = result.data[0]
        assert error["error_type"] == "AttributeError"

    def test_analyze_log(self, skill):
        """测试分析日志"""
        log_content = """
SyntaxError: invalid syntax
NameError: name 'x' is not defined
NameError: name 'y' is not defined
"""
        result = skill.execute(action="analyze", log_content=log_content)

        assert result.success
        assert "statistics" in result.data
        assert result.data["statistics"]["total_errors"] == 3
        assert result.data["statistics"]["by_type"]["NameError"] == 2

    def test_diagnose_no_errors(self, skill):
        """测试无错误的日志"""
        result = skill.execute(
            action="diagnose",
            log_content="Everything is fine, no errors here.",
        )

        assert result.success
        assert len(result.data) == 0

    def test_diagnose_with_file_info(self, skill):
        """测试包含文件信息的日志"""
        result = skill.execute(
            action="diagnose",
            log_content='File "main.py", line 42\nSyntaxError: invalid syntax',
        )

        assert result.success
        assert len(result.data) > 0
        assert result.data[0]["file_name"] == "main.py"
        assert result.data[0]["line_number"] == 42

    def test_diagnose_warning(self, skill):
        """测试诊断警告"""
        result = skill.execute(
            action="diagnose",
            log_content="WARNING: This is a warning message",
        )

        assert result.success
        assert len(result.data) > 0

        error = result.data[0]
        assert error["severity"] == "warning"

    def test_diagnose_api_error(self, skill):
        """测试诊断 API 错误"""
        result = skill.execute(
            action="diagnose",
            log_content="component CreateGame not found",
        )

        assert result.success
        assert len(result.data) > 0

        error = result.data[0]
        assert error["category"] == "api"

    def test_missing_log_content(self, skill):
        """测试缺少日志内容"""
        result = skill.execute(action="diagnose")

        assert not result.success
        assert "请提供 log_content" in result.error


class TestSkillIntegration:
    """Skills 集成测试"""

    def test_register_all_skills(self):
        """测试注册所有 Skills"""
        registry = SkillRegistry()

        # 注册代码生成 Skill
        code_gen = ModSDKCodeGenSkill()
        registry.register(code_gen)

        # 注册调试 Skill
        debug = ModSDKDebugSkill()
        registry.register(debug)

        assert registry.has("modsdk-code-gen")
        assert registry.has("modsdk-debug")

    def test_skill_registry_operations(self):
        """测试 Skill 注册表操作"""
        registry = SkillRegistry()

        skill = ModSDKCodeGenSkill()
        registry.register(skill)

        # 获取 Skill
        retrieved = registry.get("modsdk-code-gen")
        assert retrieved is not None
        assert retrieved.name == "modsdk-code-gen"

        # 搜索 Skill
        results = registry.search("代码")
        assert len(results) > 0

        # 列出所有 Skills
        all_skills = registry.list_all()
        assert len(all_skills) > 0

        # 注销 Skill
        assert registry.unregister("modsdk-code-gen")
        assert not registry.has("modsdk-code-gen")
