"""
代码生成模块测试
"""

import pytest

from mc_agent_kit.generator import CodeGenerator, TemplateManager
from mc_agent_kit.generator.templates import (
    CodeTemplate,
    TemplateParameter,
    TemplateType,
)


class TestTemplateManager:
    """模板管理器测试"""

    def test_template_manager_init(self):
        """测试模板管理器初始化"""
        manager = TemplateManager()
        assert len(manager.list_all()) > 0

    def test_get_builtin_template(self):
        """测试获取内置模板"""
        manager = TemplateManager()

        template = manager.get("event_listener")
        assert template is not None
        assert template.name == "event_listener"
        assert template.template_type == TemplateType.EVENT_LISTENER

    def test_list_templates_by_type(self):
        """测试按类型列出模板"""
        manager = TemplateManager()

        event_templates = manager.list_by_type(TemplateType.EVENT_LISTENER)
        assert len(event_templates) > 0
        for t in event_templates:
            assert t.template_type == TemplateType.EVENT_LISTENER

    def test_search_templates(self):
        """测试搜索模板"""
        manager = TemplateManager()

        results = manager.search("event")
        assert len(results) > 0
        for t in results:
            assert "event" in t.name.lower() or any(
                "event" in tag.lower() for tag in t.tags
            )

    def test_register_custom_template(self):
        """测试注册自定义模板"""
        manager = TemplateManager()

        custom = CodeTemplate(
            name="my_custom_template",
            template_type=TemplateType.CUSTOM,
            description="自定义模板",
            template="Hello, {{ name }}!",
            parameters=[
                TemplateParameter(name="name", description="名称", required=True)
            ],
        )

        manager.register(custom)

        assert manager.get("my_custom_template") is not None
        assert manager.unregister("my_custom_template")
        assert manager.get("my_custom_template") is None


class TestCodeGenerator:
    """代码生成器测试"""

    @pytest.fixture
    def generator(self):
        """创建代码生成器"""
        return CodeGenerator()

    def test_generator_init(self, generator):
        """测试生成器初始化"""
        assert generator is not None
        templates = generator.list_templates()
        assert len(templates) > 0

    def test_generate_event_listener(self, generator):
        """测试生成事件监听器"""
        code = generator.generate(
            "event_listener",
            {"event_name": "OnServerChat", "scope": "服务端"},
        )

        assert "OnServerChat" in code
        assert "服务端" in code
        assert "ListenForEvent" in code

    def test_generate_api_call(self, generator):
        """测试生成 API 调用代码"""
        code = generator.generate(
            "api_call",
            {"api_name": "GetEngineType", "scope": "服务端"},
        )

        assert "GetEngineType" in code
        assert "服务端" in code

    def test_generate_with_custom_template(self, generator):
        """测试使用自定义模板生成"""
        code = generator.generate_with_template(
            "Hello, {{ name }}! Count: {{ count }}",
            {"name": "World", "count": 42},
        )

        assert "Hello, World!" in code
        assert "Count: 42" in code

    def test_generate_missing_required_param(self, generator):
        """测试缺少必需参数"""
        with pytest.raises(ValueError, match="缺少必需参数"):
            generator.generate("event_listener", {})

    def test_generate_invalid_template(self, generator):
        """测试无效模板"""
        with pytest.raises(ValueError, match="模板不存在"):
            generator.generate("invalid_template", {})

    def test_list_templates(self, generator):
        """测试列出模板"""
        templates = generator.list_templates()
        assert len(templates) > 0

        template_names = [t.name for t in templates]
        assert "event_listener" in template_names
        assert "api_call" in template_names

    def test_search_templates(self, generator):
        """测试搜索模板"""
        templates = generator.search_templates("api")
        assert len(templates) > 0

    def test_get_template_info(self, generator):
        """测试获取模板信息"""
        info = generator.get_template_info("event_listener")
        assert info is not None
        assert info["name"] == "event_listener"
        assert "parameters" in info

    def test_snake_case_filter(self, generator):
        """测试 snake_case 过滤器"""
        code = generator.generate_with_template(
            "{{ name | snake_case }}",
            {"name": "OnServerChat"},
        )
        assert code.strip() == "on_server_chat"

    def test_camel_case_filter(self, generator):
        """测试 camelCase 过滤器"""
        code = generator.generate_with_template(
            "{{ name | camel_case }}",
            {"name": "on-server-chat"},
        )
        assert code.strip() == "onServerChat"

    def test_pascal_case_filter(self, generator):
        """测试 PascalCase 过滤器"""
        code = generator.generate_with_template(
            "{{ name | pascal_case }}",
            {"name": "on_server_chat"},
        )
        assert code.strip() == "OnServerChat"


class TestCodeTemplate:
    """代码模板测试"""

    def test_template_validation(self):
        """测试模板参数验证"""
        template = CodeTemplate(
            name="test",
            template_type=TemplateType.CUSTOM,
            description="测试模板",
            template="{{ name }}",
            parameters=[
                TemplateParameter(name="name", description="名称", required=True),
                TemplateParameter(
                    name="count",
                    description="计数",
                    required=False,
                    default=0,
                ),
            ],
        )

        # 缺少必需参数
        valid, errors = template.validate_params({})
        assert not valid
        assert any("缺少必需参数" in e for e in errors)

        # 参数有效
        valid, errors = template.validate_params({"name": "test"})
        assert valid
        assert len(errors) == 0

    def test_template_choices_validation(self):
        """测试参数可选值验证"""
        template = CodeTemplate(
            name="test",
            template_type=TemplateType.CUSTOM,
            description="测试模板",
            template="{{ scope }}",
            parameters=[
                TemplateParameter(
                    name="scope",
                    description="作用域",
                    required=True,
                    choices=["client", "server"],
                )
            ],
        )

        # 无效的参数值
        valid, errors = template.validate_params({"scope": "invalid"})
        assert not valid
        assert any("必须是" in e for e in errors)

        # 有效的参数值
        valid, errors = template.validate_params({"scope": "client"})
        assert valid

    def test_template_get_parameter(self):
        """测试获取参数"""
        template = CodeTemplate(
            name="test",
            template_type=TemplateType.CUSTOM,
            description="测试模板",
            template="",
            parameters=[
                TemplateParameter(name="name", description="名称"),
                TemplateParameter(name="count", description="计数"),
            ],
        )

        param = template.get_parameter("name")
        assert param is not None
        assert param.name == "name"

        param = template.get_parameter("not_exist")
        assert param is None


class TestTemplateParameter:
    """模板参数测试"""

    def test_parameter_creation(self):
        """测试参数创建"""
        param = TemplateParameter(
            name="test_param",
            description="测试参数",
            param_type="str",
            required=True,
            default=None,
            choices=["a", "b", "c"],
        )

        assert param.name == "test_param"
        assert param.description == "测试参数"
        assert param.param_type == "str"
        assert param.required is True
        assert param.choices == ["a", "b", "c"]


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_generate_event_listener(self):
        """测试便捷函数生成事件监听器"""
        from mc_agent_kit.generator.code_gen import generate_event_listener

        code = generate_event_listener(
            event_name="OnPlayerDeath",
            scope="服务端",
            event_params=[{"name": "playerId", "type": "str", "desc": "玩家 ID"}],
        )

        assert "OnPlayerDeath" in code
        assert "服务端" in code

    def test_generate_api_call(self):
        """测试便捷函数生成 API 调用"""
        from mc_agent_kit.generator.code_gen import generate_api_call

        code = generate_api_call(
            api_name="GetPlayerName",
            scope="服务端",
        )

        assert "GetPlayerName" in code
        assert "服务端" in code
