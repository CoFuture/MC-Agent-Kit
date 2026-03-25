"""
示例代码库模块测试

迭代 #71: 知识库增强与检索优化
"""

import pytest
import tempfile
from pathlib import Path

from mc_agent_kit.knowledge.example_library import (
    CodeBlock,
    DifficultyLevel,
    EntryScope,
    ExampleCategory,
    ExampleCode,
    ExampleLibrary,
    ExampleMetadata,
    get_example_library,
    search_examples,
    list_examples,
)


class TestExampleMetadata:
    """ExampleMetadata 测试"""

    def test_create_metadata(self) -> None:
        """测试创建元数据"""
        meta = ExampleMetadata(
            name="test_example",
            title="测试示例",
            description="这是一个测试示例",
            category=ExampleCategory.BASIC,
            difficulty=DifficultyLevel.BEGINNER,
            tags=["test", "demo"],
        )
        assert meta.name == "test_example"
        assert meta.category == ExampleCategory.BASIC
        assert meta.difficulty == DifficultyLevel.BEGINNER
        assert "test" in meta.tags

    def test_metadata_to_dict(self) -> None:
        """测试元数据转字典"""
        meta = ExampleMetadata(
            name="test",
            title="Test",
            description="Test description",
            category=ExampleCategory.ENTITY,
            difficulty=DifficultyLevel.INTERMEDIATE,
            author="Test Author",
            verified=True,
            rating=4.5,
            downloads=100,
        )
        data = meta.to_dict()
        assert data["name"] == "test"
        assert data["category"] == "entity"
        assert data["difficulty"] == "intermediate"
        assert data["author"] == "Test Author"
        assert data["verified"] is True
        assert data["rating"] == 4.5
        assert data["downloads"] == 100

    def test_metadata_from_dict(self) -> None:
        """测试从字典创建元数据"""
        data = {
            "name": "test",
            "title": "Test Example",
            "description": "Test",
            "category": "network",
            "difficulty": "advanced",
            "tags": ["test"],
            "apis_used": ["API1", "API2"],
            "events_used": ["Event1"],
        }
        meta = ExampleMetadata.from_dict(data)
        assert meta.name == "test"
        assert meta.category == ExampleCategory.NETWORK
        assert meta.difficulty == DifficultyLevel.ADVANCED
        assert "API1" in meta.apis_used
        assert "Event1" in meta.events_used


class TestExampleCode:
    """ExampleCode 测试"""

    def test_create_example_code(self) -> None:
        """测试创建示例代码"""
        meta = ExampleMetadata(
            name="hello_world",
            title="Hello World",
            description="简单示例",
            category=ExampleCategory.BASIC,
            difficulty=DifficultyLevel.BEGINNER,
        )
        example = ExampleCode(
            metadata=meta,
            code_blocks=[
                CodeBlock(
                    language="python",
                    code="print('hello')",
                )
            ],
            explanation="这是一个简单示例",
            tips=["提示 1", "提示 2"],
        )
        assert example.name == "hello_world"
        assert len(example.code_blocks) == 1
        assert len(example.tips) == 2

    def test_get_main_code(self) -> None:
        """测试获取主要代码"""
        meta = ExampleMetadata(
            name="test",
            title="Test",
            description="Test",
            category=ExampleCategory.BASIC,
            difficulty=DifficultyLevel.BEGINNER,
        )
        example = ExampleCode(
            metadata=meta,
            code_blocks=[
                CodeBlock(language="python", code="code1"),
                CodeBlock(language="python", code="code2"),
            ],
        )
        assert example.get_main_code() == "code1"

    def test_get_all_code(self) -> None:
        """测试获取所有代码"""
        meta = ExampleMetadata(
            name="test",
            title="Test",
            description="Test",
            category=ExampleCategory.BASIC,
            difficulty=DifficultyLevel.BEGINNER,
        )
        example = ExampleCode(
            metadata=meta,
            code_blocks=[
                CodeBlock(language="python", code="code1"),
                CodeBlock(language="python", code="code2"),
            ],
        )
        all_code = example.get_all_code()
        assert "code1" in all_code
        assert "code2" in all_code

    def test_to_unified_entry(self) -> None:
        """测试转换为统一条目"""
        meta = ExampleMetadata(
            name="test_example",
            title="Test",
            description="Test description",
            category=ExampleCategory.ENTITY,
            difficulty=DifficultyLevel.INTERMEDIATE,
            tags=["test"],
            apis_used=["API1"],
            events_used=["Event1"],
        )
        example = ExampleCode(
            metadata=meta,
            code_blocks=[
                CodeBlock(language="python", code="print('test')")
            ],
        )
        entry = example.to_unified_entry()
        assert entry.name == "test_example"
        assert entry.type.value == "example"
        assert entry.example_category == ExampleCategory.ENTITY
        assert entry.difficulty == DifficultyLevel.INTERMEDIATE

    def test_example_roundtrip(self) -> None:
        """测试示例序列化往返"""
        meta = ExampleMetadata(
            name="test",
            title="Test",
            description="Test",
            category=ExampleCategory.BASIC,
            difficulty=DifficultyLevel.BEGINNER,
        )
        example = ExampleCode(
            metadata=meta,
            code_blocks=[
                CodeBlock(language="python", code="print('test')")
            ],
            explanation="Test explanation",
            warnings=["Warning 1"],
            tips=["Tip 1"],
        )
        data = example.to_dict()
        restored = ExampleCode.from_dict(data)
        assert restored.name == example.name
        assert len(restored.code_blocks) == len(example.code_blocks)
        assert restored.explanation == example.explanation


class TestExampleLibrary:
    """ExampleLibrary 测试"""

    def test_create_library(self) -> None:
        """测试创建示例库"""
        library = ExampleLibrary()
        assert library._examples == {}
        assert library._loaded is False

    def test_add_example(self) -> None:
        """测试添加示例"""
        library = ExampleLibrary()
        meta = ExampleMetadata(
            name="test_example",
            title="Test",
            description="Test",
            category=ExampleCategory.BASIC,
            difficulty=DifficultyLevel.BEGINNER,
        )
        example = ExampleCode(
            metadata=meta,
            code_blocks=[
                CodeBlock(language="python", code="print('test')")
            ],
        )
        library.add_example(example)
        assert "test_example" in library._examples
        assert len(library._by_category[ExampleCategory.BASIC]) == 1

    def test_get_example(self) -> None:
        """测试获取示例"""
        library = ExampleLibrary()
        meta = ExampleMetadata(
            name="test_example",
            title="Test",
            description="Test",
            category=ExampleCategory.BASIC,
            difficulty=DifficultyLevel.BEGINNER,
        )
        example = ExampleCode(
            metadata=meta,
            code_blocks=[
                CodeBlock(language="python", code="print('test')")
            ],
        )
        library.add_example(example)
        
        retrieved = library.get_example("test_example")
        assert retrieved is not None
        assert retrieved.name == "test_example"

    def test_list_examples(self) -> None:
        """测试列出示例"""
        library = ExampleLibrary()
        
        # 添加多个示例
        for i in range(5):
            meta = ExampleMetadata(
                name=f"test_example_{i}",
                title=f"Example {i}",
                description="Test",
                category=ExampleCategory.BASIC,
                difficulty=DifficultyLevel.BEGINNER,
            )
            example = ExampleCode(
                metadata=meta,
                code_blocks=[
                    CodeBlock(language="python", code=f"print('test {i}')")
                ],
            )
            library.add_example(example)
        
        # 限制为只获取我们添加的示例（排除内置示例）
        examples = library.list_examples(limit=20)
        # 至少有我们添加的 5 个
        assert len(examples) >= 5

    def test_list_examples_with_filter(self) -> None:
        """测试按过滤条件列出示例"""
        library = ExampleLibrary()
        
        # 添加不同分类的示例（使用唯一名称避免与内置示例冲突）
        for cat in [ExampleCategory.BASIC, ExampleCategory.ENTITY, ExampleCategory.NETWORK]:
            meta = ExampleMetadata(
                name=f"test_example_{cat.value}",
                title=f"Example {cat.value}",
                description="Test",
                category=cat,
                difficulty=DifficultyLevel.BEGINNER,
            )
            example = ExampleCode(
                metadata=meta,
                code_blocks=[
                    CodeBlock(language="python", code="print('test')")
                ],
            )
            library.add_example(example)
        
        # 按分类过滤
        basic_examples = library.list_examples(category=ExampleCategory.BASIC, limit=100)
        # 至少有我们添加的 1 个（可能有内置示例）
        assert len(basic_examples) >= 1
        # 验证我们添加的示例在其中
        assert any(e.name == "test_example_basic" for e in basic_examples)

    def test_search_examples(self) -> None:
        """测试搜索示例"""
        library = ExampleLibrary()
        
        meta = ExampleMetadata(
            name="test_unique_entity_example",
            title="实体示例",
            description="创建实体的示例代码",
            category=ExampleCategory.ENTITY,
            difficulty=DifficultyLevel.INTERMEDIATE,
            tags=["entity", "create"],
            apis_used=["CreateEngineEntity"],
        )
        example = ExampleCode(
            metadata=meta,
            code_blocks=[
                CodeBlock(language="python", code="print('entity')")
            ],
        )
        library.add_example(example)
        
        # 按名称搜索（使用唯一名称）
        results = library.search("test_unique_entity_example")
        assert len(results) >= 1
        
        # 按 API 搜索
        results = library.search("", api="CreateEngineEntity")
        assert len(results) >= 1

    def test_get_examples_by_api(self) -> None:
        """测试按 API 获取示例"""
        library = ExampleLibrary()
        
        meta = ExampleMetadata(
            name="test_example",
            title="Test",
            description="Test",
            category=ExampleCategory.BASIC,
            difficulty=DifficultyLevel.BEGINNER,
            apis_used=["TestAPI"],
        )
        example = ExampleCode(
            metadata=meta,
            code_blocks=[
                CodeBlock(language="python", code="print('test')")
            ],
        )
        library.add_example(example)
        
        examples = library.get_examples_by_api("TestAPI")
        assert len(examples) == 1

    def test_get_examples_by_event(self) -> None:
        """测试按事件获取示例"""
        library = ExampleLibrary()
        
        meta = ExampleMetadata(
            name="test_example",
            title="Test",
            description="Test",
            category=ExampleCategory.BASIC,
            difficulty=DifficultyLevel.BEGINNER,
            events_used=["TestEvent"],
        )
        example = ExampleCode(
            metadata=meta,
            code_blocks=[
                CodeBlock(language="python", code="print('test')")
            ],
        )
        library.add_example(example)
        
        examples = library.get_examples_by_event("TestEvent")
        assert len(examples) == 1

    def test_get_stats(self) -> None:
        """测试获取统计信息"""
        library = ExampleLibrary()
        
        # 添加示例
        for cat in [ExampleCategory.BASIC, ExampleCategory.ENTITY]:
            meta = ExampleMetadata(
                name=f"test_stats_{cat.value}",
                title=f"Example",
                description="Test",
                category=cat,
                difficulty=DifficultyLevel.BEGINNER,
            )
            example = ExampleCode(
                metadata=meta,
                code_blocks=[
                    CodeBlock(language="python", code="print('test')")
                ],
            )
            library.add_example(example)
        
        stats = library.get_stats()
        # 至少有我们添加的 2 个（可能有内置示例）
        assert stats["total_examples"] >= 2
        assert "basic" in stats["by_category"]
        assert "entity" in stats["by_category"]

    def test_get_categories(self) -> None:
        """测试获取分类列表"""
        library = ExampleLibrary()
        
        meta = ExampleMetadata(
            name="test",
            title="Test",
            description="Test",
            category=ExampleCategory.BASIC,
            difficulty=DifficultyLevel.BEGINNER,
        )
        example = ExampleCode(
            metadata=meta,
            code_blocks=[
                CodeBlock(language="python", code="print('test')")
            ],
        )
        library.add_example(example)
        
        categories = library.get_categories()
        assert ExampleCategory.BASIC in categories

    def test_builtin_examples(self) -> None:
        """测试内置示例加载"""
        library = ExampleLibrary()
        library.load()
        
        # 应该有内置示例
        stats = library.get_stats()
        assert stats["total_examples"] > 0

    def test_library_with_path(self, tmp_path: Path) -> None:
        """测试带路径的示例库"""
        library = ExampleLibrary(str(tmp_path))
        assert library.library_path == tmp_path


class TestGlobalFunctions:
    """全局函数测试"""

    def test_get_example_library(self) -> None:
        """测试获取全局示例库"""
        library = get_example_library()
        assert library is not None

    def test_search_examples_global(self) -> None:
        """测试全局搜索函数"""
        # 确保库已加载
        library = get_example_library()
        library.load()
        
        # 搜索应该返回结果或空列表
        results = search_examples("test", limit=5)
        assert isinstance(results, list)

    def test_list_examples_global(self) -> None:
        """测试全局列出函数"""
        library = get_example_library()
        library.load()
        
        examples = list_examples(limit=5)
        assert isinstance(examples, list)