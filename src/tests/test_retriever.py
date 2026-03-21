"""
知识库检索器测试

测试 KnowledgeRetriever 类的检索功能。
"""

import tempfile
from pathlib import Path

import pytest

from mc_agent_kit.knowledge_base import (
    APIEntry,
    APIParameter,
    EnumEntry,
    EnumValue,
    EventEntry,
    EventParameter,
    KnowledgeBase,
    KnowledgeRetriever,
    create_retriever,
)
from mc_agent_kit.knowledge_base.models import Scope


class TestKnowledgeRetriever:
    """知识库检索器测试"""

    @pytest.fixture
    def sample_kb(self):
        """创建示例知识库"""
        kb = KnowledgeBase()

        # 添加 API
        api1 = APIEntry(
            name="GetEntityPosition",
            module="实体/属性",
            description="获取实体的位置坐标",
            method_path="mod.server.component.actorCompServer.ActorCompServer",
            scope=Scope.SERVER,
            parameters=[
                APIParameter(name="entityId", data_type="str", description="实体ID"),
            ],
            return_type="tuple",
            return_description="(x, y, z) 坐标",
        )
        kb.add_api(api1)

        api2 = APIEntry(
            name="SetEntityPosition",
            module="实体/属性",
            description="设置实体的位置坐标",
            method_path="mod.server.component.actorCompServer.ActorCompServer",
            scope=Scope.SERVER,
            parameters=[
                APIParameter(name="entityId", data_type="str", description="实体ID"),
                APIParameter(name="pos", data_type="tuple", description="坐标"),
            ],
            return_type="bool",
            return_description="是否成功",
        )
        kb.add_api(api2)

        api3 = APIEntry(
            name="GetPlayerName",
            module="玩家",
            description="获取玩家名称",
            method_path="mod.server.component.playerCompServer.PlayerCompServer",
            scope=Scope.SERVER,
            parameters=[
                APIParameter(name="playerId", data_type="str", description="玩家ID"),
            ],
            return_type="str",
        )
        kb.add_api(api3)

        api4 = APIEntry(
            name="ClientGetEntity",
            module="实体",
            description="客户端获取实体",
            method_path="mod.client.component.actorCompClient.ActorCompClient",
            scope=Scope.CLIENT,
            parameters=[
                APIParameter(name="entityId", data_type="str", description="实体ID"),
            ],
        )
        kb.add_api(api4)

        # 添加事件
        event1 = EventEntry(
            name="ActorHurtServerEvent",
            module="实体",
            description="生物受伤时触发",
            scope=Scope.SERVER,
            parameters=[
                EventParameter(name="entityId", data_type="str", description="生物ID"),
                EventParameter(name="damage", data_type="int", description="伤害值", mutable=True),
            ],
        )
        kb.add_event(event1)

        event2 = EventEntry(
            name="PlayerJoinServerEvent",
            module="玩家",
            description="玩家加入服务器时触发",
            scope=Scope.SERVER,
            parameters=[
                EventParameter(name="playerId", data_type="str", description="玩家ID"),
            ],
        )
        kb.add_event(event2)

        event3 = EventEntry(
            name="ClientEntityTickEvent",
            module="实体",
            description="客户端实体tick事件",
            scope=Scope.CLIENT,
            parameters=[
                EventParameter(name="entityId", data_type="str", description="实体ID"),
            ],
        )
        kb.add_event(event3)

        # 添加枚举
        enum1 = EnumEntry(
            name="Facing",
            description="方向枚举",
            values=[
                EnumValue(name="UP", value=0, description="向上"),
                EnumValue(name="DOWN", value=1, description="向下"),
                EnumValue(name="NORTH", value=2, description="北"),
            ],
        )
        kb.add_enum(enum1)

        return kb

    @pytest.fixture
    def retriever(self, sample_kb):
        """创建检索器"""
        return KnowledgeRetriever(sample_kb)

    def test_search_api_by_name(self, retriever):
        """测试按名称搜索 API"""
        results = retriever.search_api("Entity")
        assert len(results) >= 3  # GetEntityPosition, SetEntityPosition, ClientGetEntity

    def test_search_api_by_description(self, retriever):
        """测试按描述搜索 API"""
        results = retriever.search_api("位置")
        assert len(results) >= 2  # GetEntityPosition, SetEntityPosition

    def test_search_api_with_module_filter(self, retriever):
        """测试按模块过滤 API"""
        results = retriever.search_api("Entity", module="实体/属性")
        assert len(results) == 2  # GetEntityPosition, SetEntityPosition
        for api in results:
            assert api.module == "实体/属性"

    def test_search_api_with_scope_filter(self, retriever):
        """测试按作用域过滤 API"""
        results = retriever.search_api("Entity", scope=Scope.SERVER)
        # 应该包含服务端 API，但不包含纯客户端 API
        for api in results:
            assert api.scope in (Scope.SERVER, Scope.BOTH)

    def test_search_event_by_name(self, retriever):
        """测试按名称搜索事件"""
        results = retriever.search_event("Hurt")
        assert len(results) >= 1
        assert results[0].name == "ActorHurtServerEvent"

    def test_search_event_with_module_filter(self, retriever):
        """测试按模块过滤事件"""
        results = retriever.search_event("Event", module="玩家")
        assert len(results) == 1
        assert results[0].name == "PlayerJoinServerEvent"

    def test_search_event_with_scope_filter(self, retriever):
        """测试按作用域过滤事件"""
        results = retriever.search_event("", scope=Scope.CLIENT)
        assert len(results) == 1
        assert results[0].name == "ClientEntityTickEvent"

    def test_search_enum(self, retriever):
        """测试搜索枚举"""
        results = retriever.search_enum("Facing")
        assert len(results) == 1
        assert results[0].name == "Facing"

    def test_search_all_types(self, retriever):
        """测试搜索所有类型"""
        results = retriever.search("entity", entry_type="all")
        # 应该包含 API 和事件
        assert len(results) > 0

    def test_search_api_only(self, retriever):
        """测试只搜索 API"""
        results = retriever.search("entity", entry_type="api")
        for r in results:
            assert isinstance(r, APIEntry)

    def test_search_event_only(self, retriever):
        """测试只搜索事件"""
        results = retriever.search("entity", entry_type="event")
        for r in results:
            assert isinstance(r, EventEntry)

    def test_get_api_by_name(self, retriever):
        """测试获取指定 API"""
        api = retriever.get_api("GetEntityPosition")
        assert api is not None
        assert api.name == "GetEntityPosition"

    def test_get_nonexistent_api(self, retriever):
        """测试获取不存在的 API"""
        api = retriever.get_api("NonexistentAPI")
        assert api is None

    def test_get_event_by_name(self, retriever):
        """测试获取指定事件"""
        event = retriever.get_event("ActorHurtServerEvent")
        assert event is not None
        assert event.name == "ActorHurtServerEvent"

    def test_get_enum_by_name(self, retriever):
        """测试获取指定枚举"""
        enum = retriever.get_enum("Facing")
        assert enum is not None
        assert enum.name == "Facing"

    def test_list_modules(self, retriever):
        """测试列出所有模块"""
        modules = retriever.list_modules()
        assert "实体/属性" in modules
        assert "玩家" in modules
        assert "实体" in modules

    def test_list_api_modules(self, retriever):
        """测试列出 API 模块"""
        modules = retriever.list_modules(entry_type="api")
        assert "实体/属性" in modules
        assert "玩家" in modules

    def test_list_apis_by_module(self, retriever):
        """测试获取模块的所有 API"""
        apis = retriever.list_apis_by_module("实体/属性")
        assert len(apis) == 2
        names = [api.name for api in apis]
        assert "GetEntityPosition" in names
        assert "SetEntityPosition" in names

    def test_list_events_by_module(self, retriever):
        """测试获取模块的所有事件"""
        events = retriever.list_events_by_module("玩家")
        assert len(events) == 1
        assert events[0].name == "PlayerJoinServerEvent"

    def test_search_by_parameter_name(self, retriever):
        """测试按参数名搜索"""
        results = retriever.search_by_parameter("entityId", entry_type="api")
        assert len(results) >= 3  # 多个 API 使用 entityId 参数

    def test_search_by_return_type(self, retriever):
        """测试按返回类型搜索"""
        results = retriever.search_by_return_type("bool")
        assert len(results) >= 1
        assert results[0].return_type == "bool"

    def test_search_relevance_sorting(self, retriever):
        """测试搜索结果相关度排序"""
        # 精确名称匹配应该排在最前面
        results = retriever.search("GetEntityPosition")
        assert len(results) >= 1
        assert results[0].name == "GetEntityPosition"

    def test_fuzzy_search(self, retriever):
        """测试模糊搜索"""
        # 少量拼写错误也能找到
        results = retriever.fuzzy_search("GetEntityPositin", threshold=2)
        assert len(results) >= 1
        entry, distance = results[0]
        assert entry.name == "GetEntityPosition"
        assert distance <= 2

    def test_suggest(self, retriever):
        """测试搜索建议"""
        suggestions = retriever.suggest("Get")
        assert len(suggestions) >= 2
        # 前缀匹配的建议应该都以 Get 开头
        prefix_matches = [s for s in suggestions if s.startswith("Get")]
        assert len(prefix_matches) >= 2

    def test_get_stats(self, retriever):
        """测试获取统计信息"""
        stats = retriever.get_stats()
        assert stats["total_apis"] == 4
        assert stats["total_events"] == 3
        assert stats["total_enums"] == 1

    def test_save_and_load(self, retriever):
        """测试保存和加载"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            # 保存
            retriever.save(path)

            # 加载
            retriever2 = KnowledgeRetriever()
            retriever2.load(path)

            # 验证
            stats1 = retriever.get_stats()
            stats2 = retriever2.get_stats()
            assert stats1["total_apis"] == stats2["total_apis"]
            assert stats1["total_events"] == stats2["total_events"]

            # 验证搜索功能
            results = retriever2.search_api("Entity")
            assert len(results) >= 3
        finally:
            Path(path).unlink(missing_ok=True)

    def test_limit_parameter(self, retriever):
        """测试结果数量限制"""
        results = retriever.search("entity", limit=2)
        assert len(results) <= 2

    def test_empty_query(self, retriever):
        """测试空查询"""
        results = retriever.search("")
        # 空查询应该返回有限结果或空结果
        assert isinstance(results, list)


class TestCreateRetriever:
    """create_retriever 函数测试"""

    def test_create_empty_retriever(self):
        """测试创建空检索器"""
        retriever = create_retriever()
        assert retriever is not None
        stats = retriever.get_stats()
        assert stats["total_apis"] == 0

    def test_create_with_kb_path(self, sample_kb=None):
        """测试从知识库文件创建检索器"""
        # 先创建一个临时知识库文件
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_path = Path(tmpdir) / "kb.json"

            # 创建知识库
            kb = KnowledgeBase()
            api = APIEntry(
                name="TestAPI",
                module="测试",
                description="测试API",
                method_path="test",
            )
            kb.add_api(api)

            # 保存
            retriever = KnowledgeRetriever(kb)
            retriever.save(str(kb_path))

            # 从文件创建
            retriever2 = create_retriever(str(kb_path))
            assert retriever2.get_stats()["total_apis"] == 1

    def test_create_with_nonexistent_path(self):
        """测试从不存在的路径创建"""
        retriever = create_retriever("/nonexistent/path.json")
        # 应该返回空检索器
        assert retriever.get_stats()["total_apis"] == 0


class TestRetrieverEdgeCases:
    """边界情况测试"""

    @pytest.fixture
    def empty_retriever(self):
        """创建空知识库检索器"""
        return KnowledgeRetriever(KnowledgeBase())

    def test_search_empty_kb(self, empty_retriever):
        """测试搜索空知识库"""
        results = empty_retriever.search("anything")
        assert len(results) == 0

    def test_get_from_empty_kb(self, empty_retriever):
        """测试从空知识库获取"""
        assert empty_retriever.get_api("Nonexistent") is None
        assert empty_retriever.get_event("Nonexistent") is None
        assert empty_retriever.get_enum("Nonexistent") is None

    def test_list_modules_empty_kb(self, empty_retriever):
        """测试空知识库模块列表"""
        modules = empty_retriever.list_modules()
        assert len(modules) == 0

    def test_fuzzy_search_empty_kb(self, empty_retriever):
        """测试空知识库模糊搜索"""
        results = empty_retriever.fuzzy_search("test")
        assert len(results) == 0

    def test_suggest_empty_kb(self, empty_retriever):
        """测试空知识库建议"""
        suggestions = empty_retriever.suggest("test")
        assert len(suggestions) == 0

    def test_case_insensitive_search(self):
        """测试大小写不敏感搜索"""
        kb = KnowledgeBase()
        api = APIEntry(
            name="GetPlayerHealth",
            module="玩家",
            description="获取玩家血量",
            method_path="test",
        )
        kb.add_api(api)
        retriever = KnowledgeRetriever(kb)

        # 各种大小写组合
        results1 = retriever.search_api("player")
        results2 = retriever.search_api("PLAYER")
        results3 = retriever.search_api("PlAyEr")

        assert len(results1) == len(results2) == len(results3) == 1

    def test_chinese_keyword_search(self):
        """测试中文关键词搜索"""
        kb = KnowledgeBase()
        api = APIEntry(
            name="GetPlayerHealth",
            module="玩家/属性",
            description="获取玩家的血量值",
            method_path="test",
        )
        kb.add_api(api)
        retriever = KnowledgeRetriever(kb)

        results = retriever.search_api("血量")
        assert len(results) == 1

        results = retriever.search_api("玩家")
        assert len(results) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
