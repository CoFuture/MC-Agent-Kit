"""
知识库模块测试

测试数据模型、文档解析器和索引构建器。
"""

import pytest
from pathlib import Path
import tempfile
import json

from mc_agent_kit.knowledge_base import (
    APIEntry,
    APIParameter,
    EventEntry,
    EventParameter,
    EnumEntry,
    EnumValue,
    CodeExample,
    KnowledgeBase,
    MarkdownParser,
    KnowledgeIndexer,
)
from mc_agent_kit.knowledge_base.models import Scope


class TestModels:
    """数据模型测试"""

    def test_api_parameter_creation(self):
        """测试 API 参数创建"""
        param = APIParameter(
            name="entityId",
            data_type="str",
            description="实体ID",
            optional=False,
        )
        assert param.name == "entityId"
        assert param.data_type == "str"
        assert param.description == "实体ID"
        assert not param.optional

    def test_event_parameter_creation(self):
        """测试事件参数创建"""
        param = EventParameter(
            name="cancel",
            data_type="bool",
            description="是否取消",
            mutable=True,
        )
        assert param.name == "cancel"
        assert param.mutable is True

    def test_api_entry_creation(self):
        """测试 API 条目创建"""
        api = APIEntry(
            name="GetItemDurability",
            module="物品",
            description="获取物品耐久",
            method_path="mod.server.component.itemCompServer.ItemCompServer",
            scope=Scope.SERVER,
            parameters=[
                APIParameter(name="slot", data_type="int", description="槽位"),
            ],
            return_type="int",
        )
        assert api.name == "GetItemDurability"
        assert api.scope == Scope.SERVER
        assert len(api.parameters) == 1

    def test_event_entry_creation(self):
        """测试事件条目创建"""
        event = EventEntry(
            name="ActorHurtServerEvent",
            module="实体",
            description="生物受伤时触发",
            scope=Scope.SERVER,
            parameters=[
                EventParameter(name="entityId", data_type="str", description="生物ID"),
                EventParameter(name="damage", data_type="int", description="伤害值", mutable=True),
            ],
        )
        assert event.name == "ActorHurtServerEvent"
        assert event.scope == Scope.SERVER
        assert len(event.parameters) == 2

    def test_enum_entry_creation(self):
        """测试枚举条目创建"""
        enum = EnumEntry(
            name="Facing",
            values=[
                EnumValue(name="UP", value=0, description="向上"),
                EnumValue(name="DOWN", value=1, description="向下"),
            ],
            description="方向枚举",
        )
        assert enum.name == "Facing"
        assert len(enum.values) == 2
        assert enum.values[0].name == "UP"

    def test_knowledge_base_operations(self):
        """测试知识库操作"""
        kb = KnowledgeBase()

        # 添加 API
        api = APIEntry(
            name="TestAPI",
            module="测试模块",
            description="测试API",
            method_path="test.module",
        )
        kb.add_api(api)
        assert len(kb.apis) == 1
        assert kb.get_api("TestAPI") == api

        # 添加事件
        event = EventEntry(
            name="TestEvent",
            module="测试模块",
            description="测试事件",
        )
        kb.add_event(event)
        assert len(kb.events) == 1
        assert kb.get_event("TestEvent") == event

        # 测试模块索引
        assert "测试模块" in kb.api_by_module
        assert "TestAPI" in kb.api_by_module["测试模块"]

    def test_knowledge_base_search(self):
        """测试知识库搜索"""
        kb = KnowledgeBase()

        api1 = APIEntry(
            name="GetPlayerName",
            module="玩家",
            description="获取玩家名称",
            method_path="test",
        )
        api2 = APIEntry(
            name="SetPlayerHealth",
            module="玩家",
            description="设置玩家生命值",
            method_path="test",
        )
        kb.add_api(api1)
        kb.add_api(api2)

        results = kb.search_apis("player")
        assert len(results) == 2

        results = kb.search_apis("health")
        assert len(results) == 1
        assert results[0].name == "SetPlayerHealth"

    def test_knowledge_base_to_dict(self):
        """测试知识库序列化"""
        kb = KnowledgeBase()
        api = APIEntry(
            name="TestAPI",
            module="测试",
            description="测试",
            method_path="test",
        )
        kb.add_api(api)

        data = kb.to_dict()
        assert "apis" in data
        assert "TestAPI" in data["apis"]
        assert data["apis"]["TestAPI"]["name"] == "TestAPI"


class TestMarkdownParser:
    """Markdown 解析器测试"""

    @pytest.fixture
    def parser(self):
        return MarkdownParser()

    def test_parse_scope(self, parser):
        """测试作用域解析"""
        assert parser._parse_scope("服务端") == Scope.SERVER
        assert parser._parse_scope("客户端") == Scope.CLIENT
        assert parser._parse_scope("服务端客户端") == Scope.BOTH
        assert parser._parse_scope("无标记") == Scope.UNKNOWN

    def test_remove_frontmatter(self, parser):
        """测试移除 YAML frontmatter"""
        content = "---\nsidebarDepth: 1\n---\n# 实体"
        result = parser._remove_frontmatter(content)
        assert result == "# 实体"

    def test_parse_table(self, parser):
        """测试表格解析"""
        table = "| 参数名 | 数据类型 | 说明 |\n| --- | --- | --- |\n| id | str | 实体ID |"
        rows = parser._parse_table(table)
        assert len(rows) == 1
        assert rows[0]["参数名"] == "id"
        assert rows[0]["数据类型"] == "str"

    def test_extract_code_blocks(self, parser):
        """测试代码块提取"""
        text = "```python\nprint('hello')\n```"
        examples = parser._extract_code_blocks(text)
        assert len(examples) == 1
        assert examples[0].language == "python"
        assert "print" in examples[0].code

    def test_parse_event_document(self, parser):
        """测试解析事件文档"""
        content = """---
sidebarDepth: 1
---
# 实体事件

## ActorHurtServerEvent

<span style="display:inline;color:#ff5555">服务端</span>

- 描述

    触发时机：生物（包括玩家）受伤时触发

- 参数

    | 参数名 | 数据类型 | 说明 |
    | :--- | :--- | :--- |
    | entityId | str | 生物Id |
    | damage | int | 伤害值 |

- 返回值

    无

- 示例

```python
def OnActorHurt(self, args):
    print(args['entityId'])
```
"""
        events = parser.parse(content, "mcdocs/1-ModAPI/事件/实体.md")
        assert len(events) >= 1

        event = events[0]
        assert event.name == "ActorHurtServerEvent"
        assert event.scope == Scope.SERVER
        assert "受伤" in event.description
        assert len(event.parameters) == 2
        assert event.parameters[0].name == "entityId"

    def test_parse_api_document(self, parser):
        """测试解析 API 文档"""
        content = """---
sidebarDepth: 1
---
# 物品接口

## GetItemDurability

<span style="display:inline;color:#ff5555">服务端</span>

method in mod.server.component.itemCompServer.ItemCompServer

- 描述

    获取物品耐久值

- 参数

    | 参数名 | 数据类型 | 说明 |
    | :--- | :--- | :--- |
    | slot | int | 槽位索引 |

- 返回值

    | 数据类型 | 说明 |
    | :--- | :--- |
    | int | 耐久值 |

- 示例

```python
import mod.server.extraServerApi as serverApi
comp = serverApi.GetEngineCompFactory().CreateItem(entityId)
durability = comp.GetItemDurability(0)
```
"""
        apis = parser.parse(content, "mcdocs/1-ModAPI/接口/物品.md")
        assert len(apis) >= 1

        api = apis[0]
        assert api.name == "GetItemDurability"
        assert api.scope == Scope.SERVER
        assert "耐久" in api.description
        assert len(api.parameters) == 1
        assert api.return_type == "int"


class TestKnowledgeIndexer:
    """索引构建器测试"""

    @pytest.fixture
    def temp_docs_dir(self):
        """创建临时文档目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_path = Path(tmpdir)

            # 创建目录结构
            events_dir = docs_path / "1-ModAPI" / "事件"
            events_dir.mkdir(parents=True)

            apis_dir = docs_path / "1-ModAPI" / "接口"
            apis_dir.mkdir(parents=True)

            # 创建测试文档
            event_doc = events_dir / "实体.md"
            event_doc.write_text(
                """---
sidebarDepth: 1
---
# 实体

## TestEvent

<span style="display:inline;color:#ff5555">服务端</span>

- 描述

    测试事件

- 参数

    | 参数名 | 数据类型 | 说明 |
    | :--- | :--- | :--- |
    | id | str | ID |

- 返回值

    无
""",
                encoding="utf-8",
            )

            api_doc = apis_dir / "物品.md"
            api_doc.write_text(
                """---
sidebarDepth: 1
---
# 物品

## TestAPI

<span style="display:inline;color:#ff5555">服务端</span>

method in mod.server.component.test.TestComp

- 描述

    测试API

- 参数

    无

- 返回值

    | 数据类型 | 说明 |
    | :--- | :--- |
    | bool | 是否成功 |
""",
                encoding="utf-8",
            )

            yield str(docs_path)

    def test_build_index(self, temp_docs_dir):
        """测试构建索引"""
        indexer = KnowledgeIndexer()
        kb = indexer.build(temp_docs_dir)

        # 验证统计信息
        stats = kb.stats()
        assert stats["total_events"] >= 1
        assert stats["total_apis"] >= 1

    def test_save_and_load(self, temp_docs_dir):
        """测试保存和加载"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            # 构建
            indexer = KnowledgeIndexer()
            kb1 = indexer.build(temp_docs_dir, output_path)

            # 验证文件存在
            assert Path(output_path).exists()

            # 加载
            indexer2 = KnowledgeIndexer()
            kb2 = indexer2.load(output_path)

            # 验证内容一致
            assert kb2.stats()["total_events"] == kb1.stats()["total_events"]
            assert kb2.stats()["total_apis"] == kb1.stats()["total_apis"]
        finally:
            Path(output_path).unlink(missing_ok=True)


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        # 创建知识库
        kb = KnowledgeBase()

        # 添加一些条目
        api = APIEntry(
            name="GetEntityPos",
            module="实体/属性",
            description="获取实体位置",
            method_path="mod.server.component.actorCompServer.ActorCompServer",
            scope=Scope.SERVER,
            parameters=[
                APIParameter(name="entityId", data_type="str", description="实体ID"),
            ],
            return_type="tuple",
            return_description="(x, y, z) 坐标",
        )
        kb.add_api(api)

        event = EventEntry(
            name="EntityTickServerEvent",
            module="实体",
            description="实体tick时触发",
            scope=Scope.SERVER,
            parameters=[
                EventParameter(name="entityId", data_type="str", description="实体ID"),
                EventParameter(name="identifier", data_type="str", description="实体类型"),
            ],
        )
        kb.add_event(event)

        # 测试搜索
        results = kb.search_apis("entity")
        assert len(results) == 1

        # 测试统计
        stats = kb.stats()
        assert stats["total_apis"] == 1
        assert stats["total_events"] == 1
        assert "实体/属性" in stats["api_modules"]
        assert "实体" in stats["event_modules"]

        # 测试模块查询
        entity_apis = kb.get_apis_by_module("实体/属性")
        assert len(entity_apis) == 1

        entity_events = kb.get_events_by_module("实体")
        assert len(entity_events) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])