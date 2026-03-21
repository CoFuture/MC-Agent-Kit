"""
测试模板加载器、API绑定生成器、事件生成器和代码质量工具
"""

import tempfile
from pathlib import Path

import pytest

from mc_agent_kit.generator.bindings import APIBindingGenerator
from mc_agent_kit.generator.event_gen import EventGenerator, EventListenerConfig
from mc_agent_kit.generator.lint import (
    CodeQualityTool,
    ComplexityReport,
    LintIssue,
    analyze_file_complexity,
    check_code_quality,
)
from mc_agent_kit.generator.template_loader import TemplateLoader, load_templates_from_directory
from mc_agent_kit.generator.templates import CodeTemplate, TemplateManager, TemplateType
from mc_agent_kit.knowledge_base.models import (
    APIEntry,
    APIParameter,
    EventEntry,
    EventParameter,
    KnowledgeBase,
    Scope,
)


# ========== TemplateLoader Tests ==========


class TestTemplateLoader:
    """模板加载器测试"""

    def test_init(self):
        """测试初始化"""
        loader = TemplateLoader()
        assert loader.get_manager() is not None

    def test_init_with_manager(self):
        """测试使用现有管理器初始化"""
        manager = TemplateManager()
        loader = TemplateLoader(manager)
        assert loader.get_manager() is manager

    def test_load_directory_empty(self):
        """测试加载空目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = TemplateLoader()
            count = loader.load_directory(tmpdir)
            assert count == 0

    def test_load_directory_with_templates(self):
        """测试加载包含模板的目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建模板文件
            template_content = """---
name: test_template
type: custom
description: Test template
tags:
  - test
---
# {{ name }}
Hello, {{ name }}!
"""
            template_path = Path(tmpdir) / "test.j2"
            template_path.write_text(template_content, encoding="utf-8")

            loader = TemplateLoader()
            count = loader.load_directory(tmpdir)
            assert count >= 1

            # 验证模板已加载
            manager = loader.get_manager()
            template = manager.get("test_template")
            assert template is not None
            assert template.description == "Test template"

    def test_load_directory_recursive(self):
        """测试递归加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建子目录
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()

            # 在子目录创建模板
            template_content = """---
name: nested_template
type: custom
---
Nested content
"""
            (subdir / "nested.j2").write_text(template_content, encoding="utf-8")

            loader = TemplateLoader()
            count = loader.load_directory(tmpdir, recursive=True)
            assert count >= 1

    def test_reload(self):
        """测试热重载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_content = """---
name: reload_test
---
Content
"""
            template_path = Path(tmpdir) / "reload.j2"
            template_path.write_text(template_content, encoding="utf-8")

            loader = TemplateLoader()
            loader.load_directory(tmpdir)

            # 修改文件
            new_content = """---
name: reload_test
---
New Content
"""
            template_path.write_text(new_content, encoding="utf-8")

            # 重载
            count = loader.reload()
            # 应该检测到变更并重载

    def test_parse_simple_frontmatter(self):
        """测试简单 frontmatter 解析"""
        loader = TemplateLoader()
        frontmatter = """name: test
description: Test template
tags:
  - tag1
  - tag2
"""
        metadata = loader._parse_simple_frontmatter(frontmatter)
        assert metadata.get("name") == "test"
        assert metadata.get("description") == "Test template"
        assert metadata.get("tags") == ["tag1", "tag2"]


# ========== APIBindingGenerator Tests ==========


class TestAPIBindingGenerator:
    """API 绑定生成器测试"""

    @pytest.fixture
    def sample_kb(self):
        """创建示例知识库"""
        kb = KnowledgeBase()

        # 添加 API
        api = APIEntry(
            name="GetPlayerPosition",
            module="玩家",
            description="获取玩家位置",
            method_path="mod.server.component.playerCompServer.PlayerCompServer",
            scope=Scope.SERVER,
            parameters=[
                APIParameter(
                    name="entityId",
                    data_type="str",
                    description="实体ID",
                )
            ],
            return_type="tuple",
            return_description="坐标 (x, y, z)",
        )
        kb.add_api(api)

        # 添加事件
        event = EventEntry(
            name="OnPlayerDeath",
            module="玩家",
            description="玩家死亡事件",
            scope=Scope.SERVER,
            parameters=[
                EventParameter(
                    name="entityId",
                    data_type="str",
                    description="实体ID",
                )
            ],
        )
        kb.add_event(event)

        return kb

    def test_init(self):
        """测试初始化"""
        generator = APIBindingGenerator()
        assert generator._kb is None

    def test_init_with_kb(self, sample_kb):
        """测试使用知识库初始化"""
        generator = APIBindingGenerator(sample_kb)
        assert generator._kb is sample_kb

    def test_set_knowledge_base(self, sample_kb):
        """测试设置知识库"""
        generator = APIBindingGenerator()
        generator.set_knowledge_base(sample_kb)
        assert generator._kb is sample_kb

    def test_generate_stubs(self, sample_kb):
        """测试生成类型存根"""
        generator = APIBindingGenerator(sample_kb)
        stubs = generator.generate_stubs()

        assert "GetPlayerPosition" in stubs
        assert "def GetPlayerPosition" in stubs
        assert "entityId: str" in stubs

    def test_generate_stubs_without_kb(self):
        """测试无知识库时生成存根"""
        generator = APIBindingGenerator()
        with pytest.raises(ValueError, match="知识库未设置"):
            generator.generate_stubs()

    def test_generate_doc_index_markdown(self, sample_kb):
        """测试生成 Markdown 文档索引"""
        generator = APIBindingGenerator(sample_kb)
        index = generator.generate_doc_index(format="markdown")

        assert "# ModSDK API 文档索引" in index
        assert "GetPlayerPosition" in index
        assert "OnPlayerDeath" in index

    def test_generate_doc_index_json(self, sample_kb):
        """测试生成 JSON 文档索引"""
        generator = APIBindingGenerator(sample_kb)
        index = generator.generate_doc_index(format="json")

        import json

        data = json.loads(index)
        assert "GetPlayerPosition" in data["apis"]
        assert "OnPlayerDeath" in data["events"]

    def test_generate_completion_suggestions(self, sample_kb):
        """测试生成自动补全建议"""
        generator = APIBindingGenerator(sample_kb)
        suggestions = generator.generate_completion_suggestions()

        assert len(suggestions) >= 2

        # 过滤测试
        filtered = generator.generate_completion_suggestions("Player")
        assert len(filtered) >= 1

    def test_map_type_to_stub(self, sample_kb):
        """测试类型映射"""
        generator = APIBindingGenerator(sample_kb)

        assert generator._map_type_to_stub("int") == "int"
        assert generator._map_type_to_stub("str") == "str"
        assert generator._map_type_to_stub("dict") == "Dict[str, Any]"
        assert generator._map_type_to_stub("list") == "List[Any]"

    def test_module_to_class_name(self, sample_kb):
        """测试模块名转类名"""
        generator = APIBindingGenerator(sample_kb)

        assert generator._module_to_class_name("玩家") == "玩家"
        assert generator._module_to_class_name("entity/behavior") == "EntityBehavior"
        assert generator._module_to_class_name("block-item") == "BlockItem"


# ========== EventGenerator Tests ==========


class TestEventGenerator:
    """事件生成器测试"""

    @pytest.fixture
    def sample_kb(self):
        """创建示例知识库"""
        kb = KnowledgeBase()

        event = EventEntry(
            name="OnServerChat",
            module="玩家",
            description="服务端聊天事件",
            scope=Scope.SERVER,
            parameters=[
                EventParameter(
                    name="message",
                    data_type="str",
                    description="聊天消息",
                ),
                EventParameter(
                    name="sender",
                    data_type="str",
                    description="发送者ID",
                ),
            ],
        )
        kb.add_event(event)

        return kb

    def test_init(self):
        """测试初始化"""
        generator = EventGenerator()
        assert generator._kb is None

    def test_init_with_kb(self, sample_kb):
        """测试使用知识库初始化"""
        generator = EventGenerator(sample_kb)
        assert generator._kb is sample_kb

    def test_generate_listener(self, sample_kb):
        """测试生成事件监听器"""
        generator = EventGenerator(sample_kb)
        code = generator.generate_listener("OnServerChat")

        assert "OnServerChat" in code
        assert "ListenForEvent" in code
        assert "message" in code

    def test_generate_listener_with_config(self, sample_kb):
        """测试使用配置生成监听器"""
        generator = EventGenerator(sample_kb)
        config = EventListenerConfig(
            event_name="OnServerChat",
            include_validation=True,
            include_logging=True,
            custom_code='print("Custom code")',
        )
        code = generator.generate_listener("OnServerChat", config=config)

        assert "validate_" in code
        assert "Custom code" in code

    def test_generate_validation_code(self, sample_kb):
        """测试生成参数验证代码"""
        generator = EventGenerator(sample_kb)
        code = generator.generate_validation_code("OnServerChat")

        assert "validate_" in code
        assert "message" in code
        assert "sender" in code

    def test_generate_event_index_markdown(self, sample_kb):
        """测试生成事件索引"""
        generator = EventGenerator(sample_kb)
        index = generator.generate_event_index(format="markdown")

        assert "# ModSDK 事件索引" in index
        assert "OnServerChat" in index

    def test_generate_event_index_json(self, sample_kb):
        """测试生成 JSON 事件索引"""
        generator = EventGenerator(sample_kb)
        index = generator.generate_event_index(format="json")

        import json

        data = json.loads(index)
        assert data["total"] >= 1

    def test_list_events(self, sample_kb):
        """测试列出事件"""
        generator = EventGenerator(sample_kb)
        events = generator.list_events()

        assert len(events) >= 1

        # 关键词过滤
        filtered = generator.list_events(keyword="Chat")
        assert len(filtered) >= 1

    def test_generate_listener_unknown_event(self):
        """测试生成未知事件的监听器"""
        generator = EventGenerator()
        code = generator.generate_listener(
            "UnknownEvent",
            event_params=[{"name": "data", "type": "str", "desc": "数据"}],
        )

        assert "UnknownEvent" in code
        assert "ListenForEvent" in code


# ========== CodeQualityTool Tests ==========


class TestCodeQualityTool:
    """代码质量工具测试"""

    @pytest.fixture
    def sample_code(self):
        """创建示例代码"""
        return '''
def hello():
    """Say hello"""
    print("Hello, World!")

def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

class Calculator:
    """Simple calculator"""
    
    def multiply(self, a: int, b: int) -> int:
        return a * b
'''

    def test_init(self):
        """测试初始化"""
        tool = CodeQualityTool(use_ruff=False)
        assert tool._use_ruff is False

    def test_check_file(self, sample_code):
        """测试检查文件"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(sample_code)
            f.flush()

            tool = CodeQualityTool(use_ruff=False)
            issues = tool.check_file(f.name)

            assert isinstance(issues, list)

    def test_check_file_with_syntax_error(self):
        """测试检查有语法错误的文件"""
        code = "def broken(\n"  # 语法错误

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            f.flush()

            tool = CodeQualityTool(use_ruff=False)
            issues = tool.check_file(f.name)

            # 应该检测到语法错误
            assert any(i.code == "E999" for i in issues)

    def test_analyze_complexity(self, sample_code):
        """测试分析复杂度"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(sample_code)
            f.flush()

            tool = CodeQualityTool(use_ruff=False)
            report = tool.analyze_complexity(f.name)

            assert isinstance(report, ComplexityReport)
            assert report.functions >= 2
            assert report.classes >= 1
            assert report.total_lines > 0

    def test_check_directory(self, sample_code):
        """测试检查目录"""
        # 创建有问题的代码
        problematic_code = "def test():\n    pass    \n"  # 有尾随空白

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建多个 Python 文件
            for i in range(2):
                py_file = Path(tmpdir) / f"file{i}.py"
                py_file.write_text(problematic_code, encoding="utf-8")

            tool = CodeQualityTool(use_ruff=False)
            results = tool.check_directory(tmpdir)

            assert isinstance(results, dict)
            # 检查返回结果格式正确
            for file_path, issues in results.items():
                assert isinstance(issues, list)

    def test_generate_complexity_report_text(self, sample_code):
        """测试生成文本复杂度报告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text(sample_code, encoding="utf-8")

            tool = CodeQualityTool(use_ruff=False)
            report = tool.generate_complexity_report(tmpdir, output_format="text")

            assert "代码复杂度报告" in report

    def test_generate_complexity_report_markdown(self, sample_code):
        """测试生成 Markdown 复杂度报告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text(sample_code, encoding="utf-8")

            tool = CodeQualityTool(use_ruff=False)
            report = tool.generate_complexity_report(tmpdir, output_format="markdown")

            assert "# 代码复杂度报告" in report
            assert "| 文件数量 |" in report

    def test_generate_complexity_report_json(self, sample_code):
        """测试生成 JSON 复杂度报告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "test.py"
            py_file.write_text(sample_code, encoding="utf-8")

            tool = CodeQualityTool(use_ruff=False)
            report = tool.generate_complexity_report(tmpdir, output_format="json")

            import json

            data = json.loads(report)
            assert "summary" in data
            assert "files" in data

    def test_calculate_cyclomatic_complexity(self):
        """测试圈复杂度计算"""
        import ast

        tool = CodeQualityTool(use_ruff=False)

        # 简单函数
        code1 = "def simple(): return 1"
        tree1 = ast.parse(code1)
        func1 = tree1.body[0]
        assert tool._calculate_cyclomatic_complexity(func1) == 1

        # 带分支的函数
        code2 = """
def with_branch(x):
    if x > 0:
        return 1
    else:
        return 2
"""
        tree2 = ast.parse(code2)
        func2 = tree2.body[0]
        assert tool._calculate_cyclomatic_complexity(func2) >= 2


# ========== Convenience Functions Tests ==========


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_load_templates_from_directory(self):
        """测试便捷函数"""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_content = """---
name: conv_template
---
Content
"""
            (Path(tmpdir) / "conv.j2").write_text(template_content, encoding="utf-8")

            manager, count = load_templates_from_directory(tmpdir)
            assert count >= 1
            assert manager.get("conv_template") is not None

    def test_check_code_quality(self):
        """测试代码质量检查便捷函数"""
        code = "def test(): pass\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            f.flush()

            passed, issues = check_code_quality(f.name, use_ruff=False)
            assert isinstance(passed, bool)
            assert isinstance(issues, list)

    def test_analyze_file_complexity(self):
        """测试文件复杂度分析便捷函数"""
        code = """
def func1(): pass
def func2(): pass
class MyClass: pass
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            f.flush()

            report = analyze_file_complexity(f.name)
            assert isinstance(report, ComplexityReport)
            assert report.functions == 2
            assert report.classes == 1


# ========== LintIssue and ComplexityReport Tests ==========


class TestDataClasses:
    """数据类测试"""

    def test_lint_issue(self):
        """测试 LintIssue 数据类"""
        issue = LintIssue(
            file_path="test.py",
            line=10,
            column=5,
            code="E501",
            message="Line too long",
            severity="warning",
            fixable=False,
        )
        assert issue.file_path == "test.py"
        assert issue.line == 10
        assert issue.code == "E501"

    def test_complexity_report(self):
        """测试 ComplexityReport 数据类"""
        report = ComplexityReport(
            file_path="test.py",
            total_lines=100,
            code_lines=80,
            comment_lines=10,
            blank_lines=10,
            functions=5,
            classes=2,
            max_complexity=8,
            avg_complexity=3.5,
        )
        assert report.total_lines == 100
        assert report.functions == 5
        assert report.max_complexity == 8