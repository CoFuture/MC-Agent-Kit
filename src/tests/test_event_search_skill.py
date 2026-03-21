"""
事件检索 Skill 测试

测试 ModSDKEventSearchSkill 的各项功能。
"""

from unittest import mock

import pytest

from mc_agent_kit.skills.base import SkillCategory, SkillPriority, SkillResult
from mc_agent_kit.skills.modsdk.event_search import ModSDKEventSearchSkill


class TestModSDKEventSearchSkillMetadata:
    """测试 Skill 元数据"""

    def test_skill_metadata(self):
        """测试元数据属性"""
        skill = ModSDKEventSearchSkill()

        assert skill.metadata.name == "modsdk-event-search"
        assert "事件" in skill.metadata.description
        assert skill.metadata.version == "1.0.0"
        assert skill.metadata.category == SkillCategory.SEARCH
        assert skill.metadata.priority == SkillPriority.HIGH
        assert "modsdk" in skill.metadata.tags
        assert "event" in skill.metadata.tags

    def test_skill_not_initialized(self):
        """测试未初始化状态"""
        skill = ModSDKEventSearchSkill()
        assert not skill._initialized


class TestModSDKEventSearchSkillExecute:
    """测试 Skill 执行"""

    def test_execute_without_initialize(self):
        """测试未初始化时执行"""
        skill = ModSDKEventSearchSkill()
        # 即使未初始化，execute 也会尝试初始化
        result = skill.execute(query="test")
        # 可能成功或失败，取决于知识库是否存在
        assert isinstance(result, SkillResult)

    def test_execute_no_params(self):
        """测试无参数执行"""
        skill = ModSDKEventSearchSkill()
        skill._initialized = True
        skill._retriever = mock.MagicMock()

        result = skill.execute()

        assert result.success is False
        assert "请提供" in result.message or "query" in result.message

    def test_execute_with_name(self):
        """测试按名称搜索"""
        skill = ModSDKEventSearchSkill()
        skill._initialized = True

        # Mock retriever
        mock_event = mock.MagicMock()
        mock_event.name = "AddEntityClientEvent"
        mock_event.module = "实体"
        mock_event.description = "实体添加事件"
        mock_event.scope.value = "client"
        mock_event.parameters = []
        mock_event.return_value = None
        mock_event.examples = []
        mock_event.remarks = ""

        mock_retriever = mock.MagicMock()
        mock_retriever.get_event.return_value = mock_event
        skill._retriever = mock_retriever

        result = skill.execute(name="AddEntityClientEvent")

        assert result.success is True
        assert result.data[0]["name"] == "AddEntityClientEvent"
        mock_retriever.get_event.assert_called_once_with("AddEntityClientEvent")

    def test_execute_with_name_not_found(self):
        """测试按名称搜索未找到"""
        skill = ModSDKEventSearchSkill()
        skill._initialized = True

        mock_retriever = mock.MagicMock()
        mock_retriever.get_event.return_value = None
        mock_retriever.suggest.return_value = ["Suggestion1", "Suggestion2"]
        skill._retriever = mock_retriever

        result = skill.execute(name="NonExistentEvent")

        assert result.success is False
        assert "未找到事件" in result.error
        assert result.suggestions == ["Suggestion1", "Suggestion2"]

    def test_execute_with_query(self):
        """测试关键词搜索"""
        skill = ModSDKEventSearchSkill()
        skill._initialized = True

        # Mock events
        mock_event1 = mock.MagicMock()
        mock_event1.name = "OnPlayerJoin"
        mock_event1.module = "玩家"
        mock_event1.description = "玩家加入事件"
        mock_event1.scope.value = "server"
        mock_event1.parameters = []
        mock_event1.return_value = None
        mock_event1.examples = []
        mock_event1.remarks = ""

        mock_retriever = mock.MagicMock()
        mock_retriever.search_event.return_value = [mock_event1]
        skill._retriever = mock_retriever

        result = skill.execute(query="player", limit=10)

        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0]["name"] == "OnPlayerJoin"

    def test_execute_with_module_filter(self):
        """测试模块过滤"""
        skill = ModSDKEventSearchSkill()
        skill._initialized = True

        mock_event = mock.MagicMock()
        mock_event.name = "TestEvent"
        mock_event.module = "实体"
        mock_event.description = "测试事件"
        mock_event.scope.value = "both"
        mock_event.parameters = []
        mock_event.return_value = None
        mock_event.examples = []
        mock_event.remarks = ""

        mock_retriever = mock.MagicMock()
        mock_retriever.list_events_by_module.return_value = [mock_event]
        skill._retriever = mock_retriever

        result = skill.execute(module="实体")

        assert result.success is True
        mock_retriever.list_events_by_module.assert_called_once_with("实体")

    def test_execute_with_param_name(self):
        """测试按参数名搜索"""
        skill = ModSDKEventSearchSkill()
        skill._initialized = True

        mock_event = mock.MagicMock()
        mock_event.name = "HurtEvent"
        mock_event.module = "实体"
        mock_event.description = "伤害事件"
        mock_event.scope.value = "server"
        mock_event.parameters = []
        mock_event.return_value = None
        mock_event.examples = []
        mock_event.remarks = ""

        mock_retriever = mock.MagicMock()
        mock_retriever.search_by_parameter.return_value = [mock_event]
        skill._retriever = mock_retriever

        result = skill.execute(param_name="damage")

        assert result.success is True
        mock_retriever.search_by_parameter.assert_called_once_with(
            "damage", entry_type="event"
        )

    def test_execute_fuzzy_search(self):
        """测试模糊搜索"""
        skill = ModSDKEventSearchSkill()
        skill._initialized = True

        mock_event = mock.MagicMock()
        mock_event.name = "OnPlayerJoin"
        mock_event.module = "玩家"
        mock_event.description = "玩家加入"
        mock_event.scope.value = "server"
        mock_event.parameters = []
        mock_event.return_value = None
        mock_event.examples = []
        mock_event.remarks = ""

        mock_retriever = mock.MagicMock()
        mock_retriever.fuzzy_search.return_value = [(mock_event, 1)]
        skill._retriever = mock_retriever

        result = skill.execute(query="playr", fuzzy=True)

        assert result.success is True
        mock_retriever.fuzzy_search.assert_called_once()


class TestModSDKEventSearchSkillHelperMethods:
    """测试辅助方法"""

    def test_format_event(self):
        """测试格式化事件"""
        skill = ModSDKEventSearchSkill()

        # 创建 mock event
        mock_param = mock.MagicMock()
        mock_param.name = "entityId"
        mock_param.data_type = "int"
        mock_param.description = "实体ID"
        mock_param.mutable = False

        mock_example = mock.MagicMock()
        mock_example.code = "print('test')"

        mock_event = mock.MagicMock()
        mock_event.name = "TestEvent"
        mock_event.module = "测试模块"
        mock_event.description = "测试事件描述"
        mock_event.scope.value = "server"
        mock_event.parameters = [mock_param]
        mock_event.return_value = "None"
        mock_event.examples = [mock_example]
        mock_event.remarks = "备注"

        result = skill._format_event(mock_event, relevance_score=0.9)

        assert result["name"] == "TestEvent"
        assert result["module"] == "测试模块"
        assert result["description"] == "测试事件描述"
        assert result["scope"] == "server"
        assert len(result["parameters"]) == 1
        assert result["parameters"][0]["name"] == "entityId"
        assert result["return_value"] == "None"
        assert len(result["examples"]) == 1
        assert result["remarks"] == "备注"
        assert result["relevance_score"] == 0.9

    def test_parse_scope(self):
        """测试解析作用域"""
        skill = ModSDKEventSearchSkill()

        # 测试各种作用域字符串
        from mc_agent_kit.knowledge_base import Scope

        assert skill._parse_scope("client") == Scope.CLIENT
        assert skill._parse_scope("server") == Scope.SERVER
        assert skill._parse_scope("both") == Scope.BOTH
        assert skill._parse_scope("客户端") == Scope.CLIENT
        assert skill._parse_scope("服务端") == Scope.SERVER
        assert skill._parse_scope("双端") == Scope.BOTH
        assert skill._parse_scope("unknown") == Scope.UNKNOWN


class TestModSDKEventSearchSkillListMethods:
    """测试列表方法"""

    def test_list_modules(self):
        """测试列出模块"""
        skill = ModSDKEventSearchSkill()
        skill._initialized = True

        mock_retriever = mock.MagicMock()
        mock_retriever.list_modules.return_value = ["实体", "玩家", "物品"]
        skill._retriever = mock_retriever

        result = skill.list_modules()

        assert result.success is True
        assert result.data == ["实体", "玩家", "物品"]

    def test_list_modules_without_retriever(self):
        """测试无检索器时列出模块"""
        skill = ModSDKEventSearchSkill()
        skill._initialized = True
        skill._retriever = None

        result = skill.list_modules()

        assert result.success is False
        assert "知识库未初始化" in result.error

    def test_get_stats(self):
        """测试获取统计信息"""
        skill = ModSDKEventSearchSkill()
        skill._initialized = True

        mock_retriever = mock.MagicMock()
        mock_retriever.get_stats.return_value = {
            "api_count": 100,
            "event_count": 50,
        }
        skill._retriever = mock_retriever

        result = skill.get_stats()

        assert result.success is True
        assert result.data["api_count"] == 100
        assert result.data["event_count"] == 50

    def test_get_stats_without_retriever(self):
        """测试无检索器时获取统计"""
        skill = ModSDKEventSearchSkill()
        skill._initialized = True
        skill._retriever = None

        result = skill.get_stats()

        assert result.success is False
        assert "知识库未初始化" in result.error


class TestModSDKEventSearchSkillInitialize:
    """测试初始化"""

    def test_initialize_success(self):
        """测试初始化成功"""
        skill = ModSDKEventSearchSkill()

        with mock.patch.object(skill, "_retriever", None):
            with mock.patch(
                "mc_agent_kit.skills.modsdk.event_search.KnowledgeRetriever"
            ) as MockRetriever:
                mock_instance = mock.MagicMock()
                MockRetriever.return_value = mock_instance

                result = skill.initialize()

                assert result is True
                assert skill._initialized is True

    def test_initialize_already_initialized(self):
        """测试已初始化"""
        skill = ModSDKEventSearchSkill()
        skill._initialized = True

        result = skill.initialize()

        assert result is True

    def test_initialize_with_kb_path(self):
        """测试带知识库路径初始化"""
        skill = ModSDKEventSearchSkill(kb_path="/path/to/kb.json")

        with mock.patch(
            "mc_agent_kit.skills.modsdk.event_search.KnowledgeRetriever"
        ) as MockRetriever:
            mock_instance = mock.MagicMock()
            MockRetriever.return_value = mock_instance

            result = skill.initialize()

            assert result is True
            mock_instance.load.assert_called_once_with("/path/to/kb.json")


class TestModSDKEventSearchSkillExceptionHandling:
    """测试异常处理"""

    def test_execute_exception(self):
        """测试执行异常"""
        skill = ModSDKEventSearchSkill()
        skill._initialized = True

        mock_retriever = mock.MagicMock()
        mock_retriever.search_event.side_effect = Exception("Database error")
        skill._retriever = mock_retriever

        result = skill.execute(query="test")

        assert result.success is False
        assert "Database error" in result.error

    def test_initialize_exception(self):
        """测试初始化异常"""
        skill = ModSDKEventSearchSkill()

        with mock.patch(
            "mc_agent_kit.skills.modsdk.event_search.KnowledgeRetriever",
            side_effect=Exception("Init error"),
        ):
            result = skill.initialize()

            assert result is False
            assert skill._initialized is False