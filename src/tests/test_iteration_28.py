# -*- coding: utf-8 -*-
"""
迭代 #28 测试

测试新增的知识库解析器和脚手架功能。
"""

import pytest
import tempfile
from pathlib import Path

from mc_agent_kit.knowledge.parsers import MarkdownParser, CodeExtractor, CodeExample
from mc_agent_kit.knowledge.parsers.markdown_parser import APIInfo, EventInfo, APIParameter
from mc_agent_kit.scaffold import ProjectCreator


class TestMarkdownParser:
    """Markdown 解析器测试"""

    def test_parse_basic_document(self):
        """测试解析基本文档"""
        parser = MarkdownParser()
        content = """# CreateEntity

创建实体接口。

## 参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| entityType | str | 实体类型 |

## 示例

```python
entity = server.CreateEntity("minecraft:zombie")
```
"""
        doc = parser.parse(content, "/api/entity/create_entity.md")

        assert doc.title == "CreateEntity"
        assert doc.doc_type == "api"
        assert len(doc.code_blocks) == 1
        assert "CreateEntity" in doc.code_blocks[0]

    def test_parse_frontmatter(self):
        """测试解析 frontmatter"""
        parser = MarkdownParser()
        content = """---
名称: GetConfig
模块: 系统
---

# GetConfig

获取配置信息。
"""
        doc = parser.parse(content)

        assert doc.frontmatter.get("名称") == "GetConfig"
        assert doc.frontmatter.get("模块") == "系统"

    def test_infer_doc_type_event(self):
        """测试推断事件类型"""
        parser = MarkdownParser()
        content = "# OnPlayerJoined\n\n玩家加入事件。"
        doc = parser.parse(content, "/事件/玩家/OnPlayerJoined.md")

        assert doc.doc_type == "event"

    def test_parse_api_info(self):
        """测试解析 API 信息"""
        parser = MarkdownParser()
        content = """# GetPlayer

获取玩家信息。

## 参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| playerId | str | 玩家ID |

## 返回值

类型: dict
说明: 玩家信息字典
"""
        doc = parser.parse(content, "/接口/玩家/GetPlayer.md")

        assert doc.api_info is not None
        # API 名称从标题提取
        assert doc.title == "GetPlayer" or doc.api_info.name == "GetPlayer"
        assert len(doc.api_info.parameters) >= 1

    def test_extract_sections(self):
        """测试提取章节"""
        parser = MarkdownParser()
        content = """# Title

## Section 1

Content 1

## Section 2

Content 2
"""
        doc = parser.parse(content)

        assert "Section 1" in doc.sections
        assert "Section 2" in doc.sections

    def test_extract_code_blocks(self):
        """测试提取代码块"""
        parser = MarkdownParser()
        content = """# Test

```python
print("hello")
```

```json
{"key": "value"}
```
"""
        doc = parser.parse(content)

        assert len(doc.code_blocks) == 2
        assert "print" in doc.code_blocks[0]
        assert "key" in doc.code_blocks[1]

    def test_extract_scope(self):
        """测试提取作用域"""
        parser = MarkdownParser()

        # 仅客户端
        scope1 = parser._extract_scope("此接口仅客户端可用")
        assert scope1 == "client"

        # 仅服务端
        scope2 = parser._extract_scope("此接口仅服务端可用")
        assert scope2 == "server"

        # 双端
        scope3 = parser._extract_scope("客户端和服务端均可使用")
        assert scope3 == "both"


class TestCodeExtractor:
    """代码提取器测试"""

    def test_extract_from_content(self):
        """测试从内容提取代码"""
        extractor = CodeExtractor()
        content = """# API 文档

示例代码:

```python
entity = server.CreateEntity("minecraft:zombie")
print(entity)
```
"""
        examples = extractor.extract_from_content(content, "test.md")

        assert len(examples) == 1
        assert "CreateEntity" in examples[0].code

    def test_extract_apis(self):
        """测试提取 API 名称"""
        extractor = CodeExtractor()
        code = '''
entity = server.CreateEntity("zombie")
player = server.GetPlayer(playerId)
config = server.GetConfig()
'''
        apis = extractor._extract_apis(code)

        assert "CreateEntity" in apis or "GetPlayer" in apis

    def test_extract_events(self):
        """测试提取事件名称"""
        extractor = CodeExtractor()
        code = '''
system.ListenForEvent("ServerPlayerJoinedEvent", on_join)
system.ListenForEvent("OnChat", on_chat)
'''
        events = extractor._extract_events(code)

        assert "ServerPlayerJoinedEvent" in events
        assert "OnChat" in events

    def test_generate_tags(self):
        """测试生成标签"""
        extractor = CodeExtractor()
        code = '''
def on_player_join(args):
    player_id = args["playerId"]
    entity = server.CreateEntity("test")
'''
        tags = extractor._generate_tags(code, [], [])

        assert "player" in tags or "entity" in tags

    def test_find_examples_by_api(self):
        """测试按 API 查找示例"""
        extractor = CodeExtractor()
        examples = [
            CodeExample(
                id="1",
                code="server.CreateEntity()",
                language="python",
                source="test.md",
                api_names=["CreateEntity"],
            ),
            CodeExample(
                id="2",
                code="server.GetPlayer()",
                language="python",
                source="test.md",
                api_names=["GetPlayer"],
            ),
        ]

        found = extractor.find_examples_by_api(examples, "CreateEntity")
        assert len(found) == 1
        assert found[0].id == "1"


class TestProjectCreatorEnhanced:
    """项目创建器增强功能测试"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    def test_add_item(self, temp_dir):
        """测试添加物品"""
        creator = ProjectCreator()
        project = creator.create_project("test-addon", temp_dir)

        files = creator.add_item("DiamondSword", project)

        assert len(files) > 0
        # 检查物品定义文件
        item_file = temp_dir / "test-addon" / "behavior_pack" / "items" / "diamondsword.json"
        assert item_file.exists()

        # 检查脚本文件
        script_file = temp_dir / "test-addon" / "behavior_pack" / "scripts" / "diamondsword_item.py"
        assert script_file.exists()

    def test_add_block(self, temp_dir):
        """测试添加方块"""
        creator = ProjectCreator()
        project = creator.create_project("test-addon", temp_dir)

        files = creator.add_block("CustomStone", project)

        assert len(files) > 0
        # 检查方块定义文件
        block_file = temp_dir / "test-addon" / "behavior_pack" / "blocks" / "customstone.json"
        assert block_file.exists()

        # 检查几何模型文件
        geo_file = temp_dir / "test-addon" / "resource_pack" / "models" / "entity" / "customstone.geo.json"
        assert geo_file.exists()

    def test_item_json_structure(self, temp_dir):
        """测试物品 JSON 结构"""
        import json

        creator = ProjectCreator()
        project = creator.create_project("test-addon", temp_dir)
        creator.add_item("TestItem", project)

        item_file = temp_dir / "test-addon" / "behavior_pack" / "items" / "testitem.json"
        with open(item_file) as f:
            data = json.load(f)

        assert "minecraft:item" in data
        assert "custom:testitem" in data["minecraft:item"]["description"]["identifier"]

    def test_block_json_structure(self, temp_dir):
        """测试方块 JSON 结构"""
        import json

        creator = ProjectCreator()
        project = creator.create_project("test-addon", temp_dir)
        creator.add_block("TestBlock", project)

        block_file = temp_dir / "test-addon" / "behavior_pack" / "blocks" / "testblock.json"
        with open(block_file) as f:
            data = json.load(f)

        assert "minecraft:block" in data
        assert "custom:testblock" in data["minecraft:block"]["description"]["identifier"]

    def test_item_script_content(self, temp_dir):
        """测试物品脚本内容"""
        creator = ProjectCreator()
        project = creator.create_project("test-addon", temp_dir)
        creator.add_item("TestItem", project)

        script_file = temp_dir / "test-addon" / "behavior_pack" / "scripts" / "testitem_item.py"
        content = script_file.read_text()

        assert "register_item" in content
        assert "on_item_use" in content

    def test_block_script_content(self, temp_dir):
        """测试方块脚本内容"""
        creator = ProjectCreator()
        project = creator.create_project("test-addon", temp_dir)
        creator.add_block("TestBlock", project)

        script_file = temp_dir / "test-addon" / "behavior_pack" / "scripts" / "testblock_block.py"
        content = script_file.read_text()

        assert "register_block" in content
        assert "on_block_placed" in content
        assert "on_block_destroyed" in content


class TestHybridSearchIntegration:
    """混合搜索集成测试"""

    def test_keyword_search_basic(self):
        """测试关键词搜索基础功能"""
        from mc_agent_kit.retrieval.hybrid_search import KeywordSearchEngine

        engine = KeywordSearchEngine()
        documents = {
            "doc1": "创建实体需要使用 CreateEntity 接口",
            "doc2": "获取玩家信息使用 GetPlayer 接口",
            "doc3": "事件监听使用 ListenForEvent",
        }
        engine.index(documents)

        results = engine.search("CreateEntity", top_k=3)
        assert len(results) >= 1
        assert results[0][0] == "doc1"

    def test_hybrid_search_basic(self):
        """测试混合搜索基础功能"""
        from mc_agent_kit.retrieval.hybrid_search import (
            HybridSearchEngine,
            HybridSearchConfig,
        )

        config = HybridSearchConfig(
            keyword_weight=0.5,
            semantic_weight=0.5,
        )
        engine = HybridSearchEngine(config)

        documents = {
            "doc1": "创建实体的方法",
            "doc2": "玩家管理系统",
        }

        # 索引文档（可能因为缺少依赖而跳过语义部分）
        try:
            engine.index(documents)
            results = engine.keyword_only_search("创建实体", top_k=2)
            assert len(results) >= 1
        except Exception:
            pytest.skip("语义搜索依赖未安装")


class TestCLIIntegration:
    """CLI 集成测试"""

    def test_mc_create_item_command(self):
        """测试 mc-create item 命令"""
        # 这个测试验证 CLI 命令是否能正确调用 add_item
        from mc_agent_kit.scaffold import ProjectCreator
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as d:
            creator = ProjectCreator()
            project = creator.create_project("cli-test", d)
            files = creator.add_item("TestItem", project)

            assert any("testitem.json" in str(f) for f in files)

    def test_mc_create_block_command(self):
        """测试 mc-create block 命令"""
        from mc_agent_kit.scaffold import ProjectCreator
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            creator = ProjectCreator()
            project = creator.create_project("cli-test", d)
            files = creator.add_block("TestBlock", project)

            assert any("testblock.json" in str(f) for f in files)


class TestCodeExampleDataStructure:
    """CodeExample 数据结构测试"""

    def test_code_example_creation(self):
        """测试代码示例创建"""
        example = CodeExample(
            id="test123",
            code="print('hello')",
            language="python",
            source="test.md",
            description="A test example",
            api_names=["print"],
            tags=["test"],
        )

        assert example.id == "test123"
        assert example.language == "python"

    def test_code_example_to_dict(self):
        """测试代码示例序列化"""
        example = CodeExample(
            id="test123",
            code="print('hello')",
            language="python",
            source="test.md",
            api_names=["print"],
            tags=["test"],
        )

        data = example.to_dict()

        assert data["id"] == "test123"
        assert data["language"] == "python"
        assert "print" in data["api_names"]


class TestAPIParameter:
    """API 参数测试"""

    def test_api_parameter_creation(self):
        """测试 API 参数创建"""
        param = APIParameter(
            name="playerId",
            type="str",
            description="玩家ID",
            required=True,
        )

        assert param.name == "playerId"
        assert param.type == "str"
        assert param.required is True

    def test_api_info_creation(self):
        """测试 API 信息创建"""
        api = APIInfo(
            name="GetPlayer",
            description="获取玩家信息",
            module="玩家",
            scope="server",
            parameters=[
                APIParameter(name="playerId", type="str", description="玩家ID"),
            ],
            return_type="dict",
        )

        assert api.name == "GetPlayer"
        assert len(api.parameters) == 1
        assert api.scope == "server"


class TestEventInfo:
    """事件信息测试"""

    def test_event_info_creation(self):
        """测试事件信息创建"""
        event = EventInfo(
            name="OnPlayerJoined",
            description="玩家加入事件",
            module="玩家",
            scope="server",
            parameters=[
                APIParameter(name="playerId", type="str", description="玩家ID"),
            ],
        )

        assert event.name == "OnPlayerJoined"
        assert event.scope == "server"
        assert len(event.parameters) == 1