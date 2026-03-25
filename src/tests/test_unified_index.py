"""
统一索引模块测试

迭代 #71: 知识库增强与检索优化
"""

import pytest
from datetime import datetime

from mc_agent_kit.knowledge.unified_index import (
    CodeBlock,
    DifficultyLevel,
    EntryScope,
    EntryType,
    ExampleCategory,
    IndexStats,
    Parameter,
    RelatedAPI,
    UnifiedEntry,
)


class TestCodeBlock:
    """CodeBlock 测试"""

    def test_create_code_block(self) -> None:
        """测试创建代码块"""
        block = CodeBlock(
            language="python",
            code="print('hello')",
            description="简单示例",
        )
        assert block.language == "python"
        assert block.code == "print('hello')"
        assert block.description == "简单示例"

    def test_code_block_to_dict(self) -> None:
        """测试代码块转字典"""
        block = CodeBlock(
            language="python",
            code="print('hello')",
            line_start=1,
            line_end=5,
        )
        data = block.to_dict()
        assert data["language"] == "python"
        assert data["code"] == "print('hello')"
        assert data["line_start"] == 1
        assert data["line_end"] == 5

    def test_code_block_from_dict(self) -> None:
        """测试从字典创建代码块"""
        data = {
            "language": "python",
            "code": "print('hello')",
            "description": "示例",
        }
        block = CodeBlock.from_dict(data)
        assert block.language == "python"
        assert block.code == "print('hello')"
        assert block.description == "示例"


class TestParameter:
    """Parameter 测试"""

    def test_create_parameter(self) -> None:
        """测试创建参数"""
        param = Parameter(
            name="playerId",
            type="str",
            description="玩家ID",
            required=True,
        )
        assert param.name == "playerId"
        assert param.type == "str"
        assert param.required is True

    def test_parameter_with_default(self) -> None:
        """测试带默认值的参数"""
        param = Parameter(
            name="count",
            type="int",
            description="数量",
            required=False,
            default="10",
        )
        assert param.default == "10"
        assert param.required is False

    def test_parameter_roundtrip(self) -> None:
        """测试参数序列化往返"""
        param = Parameter(
            name="pos",
            type="tuple",
            description="位置坐标",
            required=True,
            example="(0, 64, 0)",
        )
        data = param.to_dict()
        restored = Parameter.from_dict(data)
        assert restored.name == param.name
        assert restored.type == param.type
        assert restored.example == param.example


class TestRelatedAPI:
    """RelatedAPI 测试"""

    def test_create_related_api(self) -> None:
        """测试创建相关 API"""
        related = RelatedAPI(
            name="DestroyEntity",
            relationship="related",
            description="销毁实体",
        )
        assert related.name == "DestroyEntity"
        assert related.relationship == "related"

    def test_related_api_roundtrip(self) -> None:
        """测试相关 API 序列化往返"""
        related = RelatedAPI(
            name="GetPlayerPos",
            relationship="requires",
        )
        data = related.to_dict()
        restored = RelatedAPI.from_dict(data)
        assert restored.name == "GetPlayerPos"
        assert restored.relationship == "requires"


class TestUnifiedEntry:
    """UnifiedEntry 测试"""

    def test_create_api_entry(self) -> None:
        """测试创建 API 条目"""
        entry = UnifiedEntry.create_api(
            name="CreateEntity",
            description="创建实体",
            module="entity",
            scope=EntryScope.SERVER,
        )
        assert entry.name == "CreateEntity"
        assert entry.type == EntryType.API
        assert entry.scope == EntryScope.SERVER
        assert entry.is_api is True
        assert entry.is_event is False

    def test_create_event_entry(self) -> None:
        """测试创建事件条目"""
        entry = UnifiedEntry.create_event(
            name="OnPlayerJoin",
            description="玩家加入事件",
            module="player",
            scope=EntryScope.SERVER,
        )
        assert entry.name == "OnPlayerJoin"
        assert entry.type == EntryType.EVENT
        assert entry.is_event is True

    def test_create_example_entry(self) -> None:
        """测试创建示例条目"""
        entry = UnifiedEntry.create_example(
            name="entity_example",
            description="实体创建示例",
            category=ExampleCategory.ENTITY,
            difficulty=DifficultyLevel.INTERMEDIATE,
        )
        assert entry.name == "entity_example"
        assert entry.type == EntryType.EXAMPLE
        assert entry.example_category == ExampleCategory.ENTITY
        assert entry.difficulty == DifficultyLevel.INTERMEDIATE
        assert entry.is_example is True

    def test_add_keyword(self) -> None:
        """测试添加关键词"""
        entry = UnifiedEntry.create_api(
            name="TestAPI",
            description="测试API",
        )
        entry.add_keyword("entity")
        entry.add_keyword("create")
        assert "entity" in entry.keywords
        assert "create" in entry.keywords
        # 重复添加不会重复
        entry.add_keyword("entity")
        assert entry.keywords.count("entity") == 1

    def test_add_tag(self) -> None:
        """测试添加标签"""
        entry = UnifiedEntry.create_api(
            name="TestAPI",
            description="测试API",
        )
        entry.add_tag("important")
        assert "important" in entry.tags

    def test_add_alias(self) -> None:
        """测试添加别名"""
        entry = UnifiedEntry.create_api(
            name="CreateEngineEntity",
            description="创建实体",
        )
        entry.add_alias("createEntity")
        assert "createEntity" in entry.aliases

    def test_add_code_block(self) -> None:
        """测试添加代码块"""
        entry = UnifiedEntry.create_api(
            name="TestAPI",
            description="测试API",
        )
        entry.add_code_block(
            code="print('hello')",
            language="python",
            description="示例代码",
        )
        assert len(entry.code_blocks) == 1
        assert entry.code_blocks[0].code == "print('hello')"

    def test_add_parameter(self) -> None:
        """测试添加参数"""
        entry = UnifiedEntry.create_api(
            name="TestAPI",
            description="测试API",
        )
        entry.add_parameter(
            name="playerId",
            type="str",
            description="玩家ID",
        )
        assert len(entry.parameters) == 1
        assert entry.parameters[0].name == "playerId"

    def test_entry_to_dict(self) -> None:
        """测试条目转字典"""
        entry = UnifiedEntry.create_api(
            name="TestAPI",
            description="测试API",
            module="test",
            scope=EntryScope.BOTH,
        )
        entry.add_keyword("test")
        entry.add_tag("demo")

        data = entry.to_dict()
        assert data["name"] == "TestAPI"
        assert data["type"] == "api"
        assert data["module"] == "test"
        assert data["scope"] == "both"
        assert "test" in data["keywords"]
        assert "demo" in data["tags"]

    def test_entry_from_dict(self) -> None:
        """测试从字典创建条目"""
        data = {
            "id": "test123",
            "name": "TestAPI",
            "type": "api",
            "description": "测试API",
            "module": "test",
            "scope": "server",
            "keywords": ["entity", "create"],
            "tags": ["important"],
            "code_blocks": [
                {"language": "python", "code": "print('test')"}
            ],
            "parameters": [
                {"name": "id", "type": "str", "description": "ID"}
            ],
            "example_category": "entity",
            "difficulty": "intermediate",
        }
        entry = UnifiedEntry.from_dict(data)
        assert entry.name == "TestAPI"
        assert entry.type == EntryType.API
        assert entry.scope == EntryScope.SERVER
        assert "entity" in entry.keywords
        assert len(entry.code_blocks) == 1
        assert len(entry.parameters) == 1

    def test_compute_id(self) -> None:
        """测试 ID 计算"""
        entry1 = UnifiedEntry.create_api(
            name="TestAPI",
            description="测试",
            module="test",
        )
        entry2 = UnifiedEntry.create_api(
            name="TestAPI",
            description="测试",
            module="test",
        )
        # 相同名称和模块应该生成相同 ID
        assert entry1.id == entry2.id

        entry3 = UnifiedEntry.create_api(
            name="OtherAPI",
            description="测试",
            module="test",
        )
        # 不同名称应该生成不同 ID
        assert entry1.id != entry3.id


class TestIndexStats:
    """IndexStats 测试"""

    def test_create_stats(self) -> None:
        """测试创建统计"""
        stats = IndexStats(
            total_entries=100,
            by_type={"api": 50, "event": 30, "example": 20},
            by_module={"entity": 40, "player": 30},
        )
        assert stats.total_entries == 100
        assert stats.by_type["api"] == 50

    def test_stats_roundtrip(self) -> None:
        """测试统计序列化往返"""
        stats = IndexStats(
            total_entries=100,
            by_type={"api": 50},
            by_scope={"server": 60, "client": 40},
        )
        data = stats.to_dict()
        restored = IndexStats.from_dict(data)
        assert restored.total_entries == 100
        assert restored.by_type["api"] == 50


class TestEnums:
    """枚举测试"""

    def test_entry_type_enum(self) -> None:
        """测试条目类型枚举"""
        assert EntryType.API.value == "api"
        assert EntryType.EVENT.value == "event"
        assert EntryType.EXAMPLE.value == "example"

    def test_entry_scope_enum(self) -> None:
        """测试作用域枚举"""
        assert EntryScope.CLIENT.value == "client"
        assert EntryScope.SERVER.value == "server"
        assert EntryScope.BOTH.value == "both"

    def test_example_category_enum(self) -> None:
        """测试示例分类枚举"""
        assert ExampleCategory.BASIC.value == "basic"
        assert ExampleCategory.ENTITY.value == "entity"
        assert ExampleCategory.NETWORK.value == "network"

    def test_difficulty_level_enum(self) -> None:
        """测试难度等级枚举"""
        assert DifficultyLevel.BEGINNER.value == "beginner"
        assert DifficultyLevel.INTERMEDIATE.value == "intermediate"
        assert DifficultyLevel.ADVANCED.value == "advanced"
        assert DifficultyLevel.EXPERT.value == "expert"