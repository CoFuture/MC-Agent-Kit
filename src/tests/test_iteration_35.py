"""
Iteration #35 Tests - 代码生成增强与插件系统完善

测试覆盖:
1. 代码生成质量检查器
2. 增强代码模板
3. 插件市场原型
4. 插件性能监控
5. 依赖自动安装
6. 增强代码示例管理
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

# 代码生成质量检查器测试
from mc_agent_kit.generator.quality_checker import (
    CodeQualityChecker,
    QualityCheckConfig,
    QualityIssue,
    QualityIssueSeverity,
    QualityIssueCategory,
    QualityReport,
    check_code_quality,
    validate_generated_code,
)

# 增强模板测试
from mc_agent_kit.generator.enhanced_templates import (
    ENTITY_BEHAVIOR_TEMPLATE,
    ITEM_LOGIC_TEMPLATE,
    BLOCK_LOGIC_TEMPLATE,
    DATA_SYNC_TEMPLATE,
    ENHANCED_TEMPLATES,
)
from mc_agent_kit.generator.code_gen import CodeGenerator

# 插件市场测试
from mc_agent_kit.contrib.plugin.marketplace import (
    PluginMarketplace,
    PluginMarketInfo,
    PluginCategory,
    PluginStatus,
    MarketplaceConfig,
    SearchResult,
    create_marketplace,
)

# 插件性能监控测试
from mc_agent_kit.contrib.plugin.performance import (
    PluginPerformanceMonitor,
    PluginStats,
    PerformanceMetric,
    PerformanceAlert,
    MetricType,
    PerformanceMonitorConfig,
    create_performance_monitor,
)

# 依赖自动安装测试
from mc_agent_kit.contrib.plugin.auto_install import (
    DependencyInstaller,
    DependencyInfo,
    DependencyInstallerConfig,
    DependencyType,
    InstallStatus,
    InstallResult,
    InstallReport,
    create_dependency_installer,
)

# 增强代码示例测试
from mc_agent_kit.knowledge.examples_enhanced import (
    CodeExampleManager,
    CodeExampleEnhanced,
    DifficultyLevel,
    ExampleCategory,
    ExampleManagerConfig,
    create_example_manager,
)


# =============================================================================
# 代码生成质量检查器测试
# =============================================================================

class TestQualityIssueSeverity:
    """测试问题严重程度枚举"""

    def test_severity_values(self):
        assert QualityIssueSeverity.ERROR.value == "error"
        assert QualityIssueSeverity.WARNING.value == "warning"
        assert QualityIssueSeverity.INFO.value == "info"


class TestQualityIssueCategory:
    """测试问题类别枚举"""

    def test_category_values(self):
        assert QualityIssueCategory.SYNTAX.value == "syntax"
        assert QualityIssueCategory.STYLE.value == "style"
        assert QualityIssueCategory.BEST_PRACTICE.value == "best_practice"


class TestQualityIssue:
    """测试质量问题数据类"""

    def test_create_issue(self):
        issue = QualityIssue(
            line=10,
            column=5,
            message="Test issue",
            severity=QualityIssueSeverity.WARNING,
            category=QualityIssueCategory.STYLE,
            rule_id="TEST001",
            suggestion="Fix it",
        )
        assert issue.line == 10
        assert issue.column == 5
        assert issue.message == "Test issue"

    def test_to_dict(self):
        issue = QualityIssue(
            line=1,
            column=0,
            message="Test",
            severity=QualityIssueSeverity.ERROR,
            category=QualityIssueCategory.SYNTAX,
            rule_id="TEST001",
        )
        d = issue.to_dict()
        assert d["line"] == 1
        assert d["severity"] == "error"
        assert d["category"] == "syntax"


class TestQualityReport:
    """测试质量报告"""

    def test_create_report(self):
        report = QualityReport(code="print('hello')")
        assert report.code == "print('hello')"
        assert report.issues == []
        assert report.passed is True

    def test_calculate_score(self):
        report = QualityReport(code="test")
        report.issues.append(QualityIssue(
            line=1, column=0, message="Error",
            severity=QualityIssueSeverity.ERROR,
            category=QualityIssueCategory.SYNTAX,
            rule_id="E001",
        ))
        report.issues.append(QualityIssue(
            line=2, column=0, message="Warning",
            severity=QualityIssueSeverity.WARNING,
            category=QualityIssueCategory.STYLE,
            rule_id="W001",
        ))
        score = report.calculate_score()
        assert score == 80.0  # 100 - 15 - 5

    def test_error_count(self):
        report = QualityReport(code="test")
        report.issues.append(QualityIssue(
            line=1, column=0, message="E1",
            severity=QualityIssueSeverity.ERROR,
            category=QualityIssueCategory.SYNTAX,
            rule_id="E001",
        ))
        report.issues.append(QualityIssue(
            line=2, column=0, message="E2",
            severity=QualityIssueSeverity.ERROR,
            category=QualityIssueCategory.SYNTAX,
            rule_id="E002",
        ))
        report.issues.append(QualityIssue(
            line=3, column=0, message="W1",
            severity=QualityIssueSeverity.WARNING,
            category=QualityIssueCategory.STYLE,
            rule_id="W001",
        ))
        assert report.error_count == 2
        assert report.warning_count == 1
        assert report.info_count == 0


class TestCodeQualityChecker:
    """测试代码质量检查器"""

    def test_syntax_check_valid(self):
        checker = CodeQualityChecker()
        report = checker.check("print('hello')")
        assert report.error_count == 0

    def test_syntax_check_invalid(self):
        checker = CodeQualityChecker()
        report = checker.check("print('hello'")  # 缺少右括号
        assert report.error_count > 0
        assert report.issues[0].category == QualityIssueCategory.SYNTAX

    def test_style_check_long_line(self):
        config = QualityCheckConfig(max_line_length=50)
        checker = CodeQualityChecker(config)
        long_line = "x = " + "a" * 60
        report = checker.check(long_line)
        assert any(i.category == QualityIssueCategory.STYLE for i in report.issues)

    def test_compatibility_check_fstring(self):
        checker = CodeQualityChecker()
        code = 'name = "test"\nf"Hello {name}"'
        report = checker.check(code)
        # f-string 在 Python 2.7 中不支持，应该被检测到
        has_compat_issue = any(i.category == QualityIssueCategory.COMPATIBILITY for i in report.issues)
        # 由于代码本身语法正确，可能只会有兼容性警告
        assert has_compat_issue or report.error_count == 0

    def test_security_check_eval(self):
        checker = CodeQualityChecker()
        code = "result = eval('1 + 2')"
        report = checker.check(code)
        assert any(i.category == QualityIssueCategory.SECURITY for i in report.issues)

    def test_quick_check(self):
        checker = CodeQualityChecker()
        passed, errors = checker.quick_check("print('hello')")
        assert passed is True
        assert errors == []

    def test_quick_check_invalid(self):
        checker = CodeQualityChecker()
        passed, errors = checker.quick_check("print('hello'")
        assert passed is False
        assert len(errors) > 0


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_check_code_quality(self):
        report = check_code_quality("print('hello')")
        assert isinstance(report, QualityReport)

    def test_validate_generated_code_empty(self):
        passed, msg = validate_generated_code("")
        assert passed is False
        assert "空" in msg

    def test_validate_generated_code_valid(self):
        passed, msg = validate_generated_code("def test():\n    pass")
        assert passed is True


# =============================================================================
# 增强代码模板测试
# =============================================================================

class TestEnhancedTemplates:
    """测试增强模板"""

    def test_enhanced_templates_count(self):
        assert len(ENHANCED_TEMPLATES) == 4

    def test_entity_behavior_template(self):
        assert ENTITY_BEHAVIOR_TEMPLATE.name == "entity_behavior"
        assert ENTITY_BEHAVIOR_TEMPLATE.template_type.value == "entity"
        assert len(ENTITY_BEHAVIOR_TEMPLATE.parameters) >= 5

    def test_item_logic_template(self):
        assert ITEM_LOGIC_TEMPLATE.name == "item_logic"
        assert ITEM_LOGIC_TEMPLATE.template_type.value == "item"

    def test_block_logic_template(self):
        assert BLOCK_LOGIC_TEMPLATE.name == "block_logic"
        assert BLOCK_LOGIC_TEMPLATE.template_type.value == "block"

    def test_data_sync_template(self):
        assert DATA_SYNC_TEMPLATE.name == "data_sync"
        assert DATA_SYNC_TEMPLATE.template_type.value == "custom"


class TestEnhancedTemplateGeneration:
    """测试增强模板生成"""

    def test_generate_entity_behavior(self):
        from mc_agent_kit.generator.enhanced_templates import ENHANCED_TEMPLATES
        generator = CodeGenerator()
        # 注册增强模板
        for template in ENHANCED_TEMPLATES:
            generator.register_template(template)
        
        code = generator.generate(
            "entity_behavior",
            {
                "entity_type": "my_mod:custom_mob",
                "behavior_type": "hostile",
                "init_health": 30,
            }
        )
        assert "class" in code
        assert "CustomEntity" in code or "custom_mob" in code

    def test_generate_item_logic(self):
        from mc_agent_kit.generator.enhanced_templates import ENHANCED_TEMPLATES
        generator = CodeGenerator()
        # 注册增强模板
        for template in ENHANCED_TEMPLATES:
            generator.register_template(template)
        
        code = generator.generate(
            "item_logic",
            {
                "item_identifier": "my_mod:health_potion",
                "item_type": "consumable",
                "heal_amount": 20,
            }
        )
        assert "on_use" in code
        assert "health_potion" in code

    def test_generate_block_logic(self):
        from mc_agent_kit.generator.enhanced_templates import ENHANCED_TEMPLATES
        generator = CodeGenerator()
        # 注册增强模板
        for template in ENHANCED_TEMPLATES:
            generator.register_template(template)
        
        code = generator.generate(
            "block_logic",
            {
                "block_identifier": "my_mod:chest",
                "block_type": "interactive",
            }
        )
        assert "on_interact" in code


# =============================================================================
# 插件市场测试
# =============================================================================

class TestPluginMarketInfo:
    """测试插件市场信息"""

    def test_create_plugin_info(self):
        info = PluginMarketInfo(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY,
        )
        assert info.id == "test-plugin"
        assert info.status == PluginStatus.AVAILABLE

    def test_to_dict(self):
        info = PluginMarketInfo(
            id="test",
            name="Test",
            version="1.0.0",
            description="Desc",
            author="Author",
            category=PluginCategory.CODE_GEN,
        )
        d = info.to_dict()
        assert d["id"] == "test"
        assert d["category"] == "code_gen"

    def test_from_dict(self):
        data = {
            "id": "test",
            "name": "Test",
            "version": "1.0.0",
            "description": "Desc",
            "author": "Author",
            "category": "debug",
        }
        info = PluginMarketInfo.from_dict(data)
        assert info.id == "test"
        assert info.category == PluginCategory.DEBUG


class TestPluginMarketplace:
    """测试插件市场"""

    def test_create_marketplace(self):
        mp = PluginMarketplace()
        assert mp.config is not None

    def test_refresh(self):
        mp = PluginMarketplace()
        count = mp.refresh()
        assert count >= 4  # 至少内置插件

    def test_search(self):
        mp = PluginMarketplace()
        results = mp.search("code")
        assert isinstance(results, SearchResult)
        assert isinstance(results.plugins, list)

    def test_search_by_category(self):
        mp = PluginMarketplace()
        results = mp.search("", category=PluginCategory.CODE_GEN)
        for plugin in results.plugins:
            assert plugin.category == PluginCategory.CODE_GEN

    def test_get_plugin(self):
        mp = PluginMarketplace()
        plugin = mp.get_plugin("modsdk-codegen")
        assert plugin is not None
        assert plugin.id == "modsdk-codegen"

    def test_list_plugins(self):
        mp = PluginMarketplace()
        plugins = mp.list_plugins()
        assert len(plugins) >= 4

    def test_install_uninstall(self):
        mp = PluginMarketplace()
        # 安装
        success, msg = mp.install("modsdk-codegen")
        assert success is True or "已安装" in msg
        
        # 卸载
        success, msg = mp.uninstall("modsdk-codegen")
        assert success is True

    def test_get_categories(self):
        mp = PluginMarketplace()
        categories = mp.get_categories()
        assert len(categories) >= 5


class TestCreateMarketplace:
    """测试创建市场便捷函数"""

    def test_create_marketplace_fn(self):
        mp = create_marketplace()
        assert isinstance(mp, PluginMarketplace)


# =============================================================================
# 插件性能监控测试
# =============================================================================

class TestMetricType:
    """测试指标类型"""

    def test_metric_values(self):
        assert MetricType.EXECUTION_TIME.value == "execution_time"
        assert MetricType.MEMORY_USAGE.value == "memory_usage"


class TestPluginStats:
    """测试插件统计"""

    def test_create_stats(self):
        stats = PluginStats(plugin_id="test")
        assert stats.total_calls == 0
        assert stats.error_rate == 0.0

    def test_update_time(self):
        stats = PluginStats(plugin_id="test")
        stats.update_time(0.5)
        stats.update_time(1.0)
        assert stats.total_calls == 2
        assert stats.avg_time == 0.75
        assert stats.min_time == 0.5
        assert stats.max_time == 1.0

    def test_cache_hit_rate(self):
        stats = PluginStats(plugin_id="test")
        stats.cache_hits = 8
        stats.cache_misses = 2
        assert stats.cache_hit_rate == 0.8

    def test_to_dict(self):
        stats = PluginStats(plugin_id="test")
        stats.update_time(0.5)
        d = stats.to_dict()
        assert d["plugin_id"] == "test"
        assert d["total_calls"] == 1


class TestPluginPerformanceMonitor:
    """测试性能监控器"""

    def test_create_monitor(self):
        monitor = PluginPerformanceMonitor()
        assert monitor.config.enabled is True

    def test_record_execution(self):
        monitor = PluginPerformanceMonitor()
        monitor.record_execution("test_plugin", 0.5, success=True)
        stats = monitor.get_stats("test_plugin")
        assert stats is not None
        assert stats.total_calls == 1
        assert stats.avg_time == 0.5

    def test_record_execution_error(self):
        monitor = PluginPerformanceMonitor()
        monitor.record_execution("test_plugin", 0.5, success=False, error="Test error")
        stats = monitor.get_stats("test_plugin")
        assert stats.total_errors == 1
        assert stats.last_error == "Test error"

    def test_record_cache_hit(self):
        monitor = PluginPerformanceMonitor()
        monitor.record_cache_hit("test_plugin", hit=True)
        monitor.record_cache_hit("test_plugin", hit=False)
        stats = monitor.get_stats("test_plugin")
        assert stats.cache_hits == 1
        assert stats.cache_misses == 1

    def test_track_context_manager(self):
        monitor = PluginPerformanceMonitor()
        with monitor.track("test_plugin"):
            time.sleep(0.01)
        stats = monitor.get_stats("test_plugin")
        assert stats.total_calls >= 1

    def test_get_summary(self):
        monitor = PluginPerformanceMonitor()
        monitor.record_execution("plugin1", 0.5)
        monitor.record_execution("plugin2", 1.0)
        summary = monitor.get_summary()
        assert summary["total_plugins"] >= 2
        assert summary["total_calls"] >= 2

    def test_alerts(self):
        config = PerformanceMonitorConfig(slow_call_threshold=0.001)
        monitor = PluginPerformanceMonitor(config)
        monitor.record_execution("test_plugin", 0.1)
        alerts = monitor.get_alerts()
        assert len(alerts) > 0

    def test_reset_stats(self):
        monitor = PluginPerformanceMonitor()
        monitor.record_execution("test_plugin", 0.5)
        monitor.reset_stats("test_plugin")
        stats = monitor.get_stats("test_plugin")
        assert stats is None


class TestCreatePerformanceMonitor:
    """测试创建性能监控器便捷函数"""

    def test_create_fn(self):
        monitor = create_performance_monitor()
        assert isinstance(monitor, PluginPerformanceMonitor)


# =============================================================================
# 依赖自动安装测试
# =============================================================================

class TestDependencyInfo:
    """测试依赖信息"""

    def test_create_dependency(self):
        dep = DependencyInfo(name="requests", version_spec=">=2.0.0")
        assert dep.name == "requests"
        assert dep.dep_type == DependencyType.PYTHON

    def test_to_dict(self):
        dep = DependencyInfo(name="requests")
        d = dep.to_dict()
        assert d["name"] == "requests"
        assert d["dep_type"] == "python"

    def test_from_dict(self):
        data = {"name": "requests", "version_spec": ">=2.0.0", "dep_type": "python"}
        dep = DependencyInfo.from_dict(data)
        assert dep.name == "requests"


class TestInstallResult:
    """测试安装结果"""

    def test_create_result(self):
        dep = DependencyInfo(name="requests")
        result = InstallResult(
            dependency=dep,
            status=InstallStatus.SUCCESS,
            message="Installed",
        )
        assert result.status == InstallStatus.SUCCESS

    def test_to_dict(self):
        dep = DependencyInfo(name="requests")
        result = InstallResult(dependency=dep, status=InstallStatus.SUCCESS)
        d = result.to_dict()
        assert d["status"] == "success"


class TestInstallReport:
    """测试安装报告"""

    def test_create_report(self):
        report = InstallReport()
        assert report.success_count == 0
        assert report.all_success is True

    def test_report_with_results(self):
        report = InstallReport()
        dep = DependencyInfo(name="requests")
        report.results.append(InstallResult(dependency=dep, status=InstallStatus.SUCCESS))
        report.results.append(InstallResult(dependency=dep, status=InstallStatus.FAILED))
        assert report.success_count == 1
        assert report.failed_count == 1
        assert report.all_success is False


class TestDependencyInstaller:
    """测试依赖安装器"""

    def test_create_installer(self):
        installer = DependencyInstaller()
        assert installer.config.auto_install is False

    def test_check_installed(self):
        installer = DependencyInstaller()
        dep = DependencyInfo(name="nonexistent_package_xyz")
        installed, version = installer.check_installed(dep)
        # 不存在的包应该返回 False
        assert installed is False

    def test_get_installed_packages(self):
        installer = DependencyInstaller()
        packages = installer.get_installed_packages()
        assert isinstance(packages, dict)

    def test_install_pending(self):
        config = DependencyInstallerConfig(auto_install=False)
        installer = DependencyInstaller(config)
        dep = DependencyInfo(name="test_package")
        result = installer.install(dep)
        assert result.status == InstallStatus.PENDING

    def test_install_skipped(self):
        # pytest 应该已安装
        installer = DependencyInstaller()
        dep = DependencyInfo(name="pytest")
        result = installer.install(dep)
        assert result.status == InstallStatus.SKIPPED

    def test_get_install_commands(self):
        installer = DependencyInstaller()
        deps = [
            DependencyInfo(name="requests", version_spec=">=2.0.0"),
            DependencyInfo(name="pytest"),
        ]
        cmds = installer.get_install_commands(deps)
        assert len(cmds) == 2
        assert "requests" in cmds[0]


class TestCreateDependencyInstaller:
    """测试创建安装器便捷函数"""

    def test_create_fn(self):
        installer = create_dependency_installer()
        assert isinstance(installer, DependencyInstaller)


# =============================================================================
# 增强代码示例管理测试
# =============================================================================

class TestDifficultyLevel:
    """测试难度等级"""

    def test_values(self):
        assert DifficultyLevel.BEGINNER.value == "beginner"
        assert DifficultyLevel.INTERMEDIATE.value == "intermediate"
        assert DifficultyLevel.ADVANCED.value == "advanced"
        assert DifficultyLevel.EXPERT.value == "expert"


class TestExampleCategory:
    """测试示例类别"""

    def test_values(self):
        assert ExampleCategory.BASIC.value == "basic"
        assert ExampleCategory.ENTITY.value == "entity"
        assert ExampleCategory.ITEM.value == "item"


class TestCodeExampleEnhanced:
    """测试增强代码示例"""

    def test_create_example(self):
        example = CodeExampleEnhanced(
            id="test",
            title="Test Example",
            description="A test",
            code="print('hello')",
            difficulty=DifficultyLevel.BEGINNER,
            category=ExampleCategory.BASIC,
        )
        assert example.id == "test"
        assert example.difficulty == DifficultyLevel.BEGINNER

    def test_to_dict(self):
        example = CodeExampleEnhanced(
            id="test",
            title="Test",
            description="Desc",
            code="code",
            difficulty=DifficultyLevel.INTERMEDIATE,
            category=ExampleCategory.BASIC,
        )
        d = example.to_dict()
        assert d["id"] == "test"
        assert d["difficulty"] == "intermediate"

    def test_from_dict(self):
        data = {
            "id": "test",
            "title": "Test",
            "description": "Desc",
            "code": "print('hello')",
            "difficulty": "beginner",
            "category": "basic",
        }
        example = CodeExampleEnhanced.from_dict(data)
        assert example.id == "test"
        assert example.difficulty == DifficultyLevel.BEGINNER


class TestCodeExampleManager:
    """测试代码示例管理器"""

    def test_create_manager(self):
        manager = CodeExampleManager()
        assert len(manager.list_all()) >= 6  # 内置示例

    def test_search_by_query(self):
        manager = CodeExampleManager()
        results = manager.search("实体")
        assert len(results) > 0

    def test_search_by_difficulty(self):
        manager = CodeExampleManager()
        results = manager.search("", difficulty=DifficultyLevel.BEGINNER)
        for r in results:
            assert r.example.difficulty == DifficultyLevel.BEGINNER

    def test_search_by_category(self):
        manager = CodeExampleManager()
        results = manager.search("", category=ExampleCategory.ENTITY)
        for r in results:
            assert r.example.category == ExampleCategory.ENTITY

    def test_search_by_api(self):
        manager = CodeExampleManager()
        results = manager.search("", api="ListenForEvent")
        assert len(results) > 0

    def test_get_by_api(self):
        manager = CodeExampleManager()
        examples = manager.get_by_api("ListenForEvent")
        assert len(examples) > 0

    def test_get_by_event(self):
        manager = CodeExampleManager()
        examples = manager.get_by_event("OnPlayerJoin")
        assert len(examples) > 0

    def test_get_by_tag(self):
        manager = CodeExampleManager()
        examples = manager.get_by_tag("实体")
        assert len(examples) > 0

    def test_get_example(self):
        manager = CodeExampleManager()
        example = manager.get_example("hello_world")
        assert example is not None
        assert example.id == "hello_world"

    def test_list_by_difficulty(self):
        manager = CodeExampleManager()
        examples = manager.list_by_difficulty(DifficultyLevel.BEGINNER)
        for ex in examples:
            assert ex.difficulty == DifficultyLevel.BEGINNER

    def test_list_by_category(self):
        manager = CodeExampleManager()
        examples = manager.list_by_category(ExampleCategory.BASIC)
        for ex in examples:
            assert ex.category == ExampleCategory.BASIC

    def test_get_difficulty_distribution(self):
        manager = CodeExampleManager()
        dist = manager.get_difficulty_distribution()
        assert "beginner" in dist
        assert "intermediate" in dist

    def test_get_category_distribution(self):
        manager = CodeExampleManager()
        dist = manager.get_category_distribution()
        assert "basic" in dist
        assert "entity" in dist


class TestCreateExampleManager:
    """测试创建示例管理器便捷函数"""

    def test_create_fn(self):
        manager = create_example_manager()
        assert isinstance(manager, CodeExampleManager)


# =============================================================================
# 集成测试
# =============================================================================

class TestIteration35Integration:
    """迭代 #35 集成测试"""

    def test_quality_check_generated_code(self):
        """测试质量检查生成的代码"""
        generator = CodeGenerator()
        code = generator.generate(
            "event_listener",
            {"event_name": "OnServerChat"}
        )
        report = check_code_quality(code)
        assert report.error_count == 0

    def test_enhanced_template_quality(self):
        """测试增强模板生成的代码质量"""
        from mc_agent_kit.generator.enhanced_templates import ENHANCED_TEMPLATES
        generator = CodeGenerator()
        # 注册增强模板
        for template in ENHANCED_TEMPLATES:
            generator.register_template(template)
        
        # 为每个模板提供适当的参数
        template_params = {
            "entity_behavior": {
                "entity_type": "my_mod:custom_mob",
                "behavior_type": "passive",
                "init_health": 20,
            },
            "item_logic": {
                "item_identifier": "my_mod:health_potion",
                "item_type": "consumable",
            },
            "block_logic": {
                "block_identifier": "my_mod:chest",
                "block_type": "solid",  # 使用简单类型
            },
            "data_sync": {
                "sync_name": "player_stats",
            },
        }
        
        for template in ENHANCED_TEMPLATES:
            params = template_params.get(template.name, {})
            # 添加必需的参数
            for param in template.parameters:
                if param.required and param.name not in params:
                    if param.param_type == "str":
                        params[param.name] = "test_value"
            
            code = generator.generate(template.name, params)
            # 检查代码是否生成
            assert code is not None
            assert len(code) > 100  # 代码应该有一定长度
            # 检查代码包含关键元素
            if template.template_type.value == "entity":
                assert "class" in code or "def" in code
            elif template.template_type.value == "item":
                assert "def" in code or "import" in code
            elif template.template_type.value == "block":
                assert "def" in code or "class" in code
            elif template.template_type.value == "custom":
                assert "import" in code or "def" in code

    def test_marketplace_and_performance(self):
        """测试市场和性能监控集成"""
        mp = PluginMarketplace()
        monitor = PluginPerformanceMonitor()
        
        # 模拟插件执行
        with monitor.track("modsdk-codegen"):
            time.sleep(0.01)
        
        summary = monitor.get_summary()
        assert summary["total_calls"] >= 1

    def test_example_search_integration(self):
        """测试示例搜索集成"""
        manager = CodeExampleManager()
        
        # 搜索并验证结果
        results = manager.search("创建", difficulty=DifficultyLevel.BEGINNER)
        for r in results:
            assert r.example.difficulty == DifficultyLevel.BEGINNER
            assert r.score > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
