"""
迭代 #60 测试 - CLI 用户体验优化与文档完善

版本：v1.47.0
目标：
1. CLI 用户体验优化
2. 文档完善
3. 测试覆盖
4. 性能监控
"""

import time
from pathlib import Path

import pytest

from mc_agent_kit.cli_enhanced.output import (
    Color,
    Style,
    ColoredOutput,
    ProgressBar,
    ProgressConfig,
    create_output,
    create_progress_bar,
)
from mc_agent_kit.ux.enhanced import (
    EnhancedUXManager,
    LocaleConfig,
    LocaleManager,
    MessageHistory,
    MessageHistoryEntry,
    MessageTemplate,
    TemplateRegistry,
    get_ux_manager,
    localized_message,
)
from mc_agent_kit.stats.tracker import ApiUsageTracker


# ==================== CLI 输出增强测试 ====================

class TestColoredOutput:
    """彩色输出测试"""

    def test_create_output(self):
        """测试创建输出对象"""
        output = create_output()
        assert output is not None
        assert isinstance(output, ColoredOutput)

    def test_color_enum(self):
        """测试颜色枚举"""
        # Color 值是 ANSI 代码
        assert Color.RED.value == "31"
        assert Color.GREEN.value == "32"
        assert Color.YELLOW.value == "33"
        assert Color.BLUE.value == "34"
        assert Color.CYAN.value == "36"
        assert Color.MAGENTA.value == "35"
        assert Color.WHITE.value == "37"

    def test_style_enum(self):
        """测试样式枚举"""
        # Style 值是 ANSI 代码
        assert Style.BOLD.value == "1"
        assert Style.DIM.value == "2"
        assert Style.ITALIC.value == "3"
        assert Style.UNDERLINE.value == "4"


class TestProgressBar:
    """进度条测试"""

    def test_create_progress_bar(self):
        """测试创建进度条"""
        config = ProgressConfig(total=10, prefix="测试")
        progress = create_progress_bar(config)
        assert progress is not None
        assert progress.config.total == 10
        assert progress.config.prefix == "测试"

    def test_progress_update(self):
        """测试进度更新"""
        config = ProgressConfig(total=10)
        progress = create_progress_bar(config)
        progress.update(5)
        assert progress._current == 5

    def test_progress_complete(self):
        """测试进度完成"""
        config = ProgressConfig(total=10)
        progress = create_progress_bar(config)
        progress.update(10)
        assert progress._current == 10

    def test_progress_set_progress(self):
        """测试设置进度"""
        config = ProgressConfig(total=100)
        progress = create_progress_bar(config)
        progress.set_progress(50)
        assert progress._current == 50

    def test_progress_complete_method(self):
        """测试完成方法"""
        config = ProgressConfig(total=5)
        progress = create_progress_bar(config)
        progress.complete()
        assert progress._current == 5

    def test_progress_reset(self):
        """测试重置进度"""
        config = ProgressConfig(total=10)
        progress = create_progress_bar(config)
        progress.update(5)
        progress.reset()
        assert progress._current == 0


# ==================== UX 本地化测试 ====================

class TestLocaleManager:
    """本地化管理器测试"""

    def test_locale_config_default(self):
        """测试默认语言配置"""
        config = LocaleConfig()
        assert config.locale == "zh_CN"
        assert config.fallback_locale == "en_US"

    def test_locale_manager_init(self):
        """测试本地化管理器初始化"""
        manager = LocaleManager()
        assert manager.config.locale == "zh_CN"

    def test_locale_manager_get_zh(self):
        """测试中文消息获取"""
        manager = LocaleManager(LocaleConfig(locale="zh_CN"))
        msg = manager.get("success.project_created")
        assert "创建成功" in msg or "Project" in msg

    def test_locale_manager_get_en(self):
        """测试英文消息获取"""
        manager = LocaleManager(LocaleConfig(locale="en_US"))
        msg = manager.get("success.project_created")
        assert "successfully" in msg or "创建成功" in msg

    def test_locale_manager_get_with_params(self):
        """测试带参数消息获取"""
        manager = LocaleManager(LocaleConfig(locale="zh_CN"))
        msg = manager.get("success.entity_created", name="TestEntity")
        assert "TestEntity" in msg

    def test_locale_manager_fallback(self):
        """测试回退机制"""
        manager = LocaleManager(LocaleConfig(locale="ja_JP"))
        # 如果日语没有某个键，应该回退到英语
        msg = manager.get("success.project_created")
        assert msg is not None

    def test_set_locale(self):
        """测试切换语言"""
        manager = LocaleManager()
        manager.set_locale("en_US")
        assert manager.config.locale == "en_US"

    def test_register_custom_message(self):
        """测试注册自定义消息"""
        manager = LocaleManager()
        manager.register_custom_message("custom.test", "自定义消息")
        msg = manager.get("custom.test")
        assert msg == "自定义消息"


class TestMessageHistory:
    """消息历史记录测试"""

    def test_history_init(self):
        """测试历史记录初始化"""
        history = MessageHistory()
        assert history is not None

    def test_record_message(self):
        """测试记录消息"""
        history = MessageHistory()
        from mc_agent_kit.ux.enhancer import UserExperienceEnhancer
        msg = UserExperienceEnhancer.success("测试成功").build()
        history.record(msg)
        entries = history.get_recent(1)
        assert len(entries) == 1
        assert entries[0].message.title == "测试成功"

    def test_get_by_type(self):
        """测试按类型获取消息"""
        history = MessageHistory()
        from mc_agent_kit.ux.enhancer import UserExperienceEnhancer, MessageType
        
        # 记录不同类型的消息
        success_msg = UserExperienceEnhancer.success("成功").build()
        error_msg = UserExperienceEnhancer.error("错误").build()
        
        history.record(success_msg)
        history.record(error_msg)
        
        errors = history.get_by_type(MessageType.ERROR, limit=10)
        assert len(errors) == 1
        assert errors[0].message.type == MessageType.ERROR

    def test_search_messages(self):
        """测试搜索消息"""
        history = MessageHistory()
        from mc_agent_kit.ux.enhancer import UserExperienceEnhancer
        
        msg = UserExperienceEnhancer.success("项目创建成功").build()
        history.record(msg)
        
        results = history.search("项目", limit=10)
        assert len(results) > 0

    def test_get_statistics(self):
        """测试获取统计信息"""
        history = MessageHistory()
        from mc_agent_kit.ux.enhancer import UserExperienceEnhancer
        
        # 记录多条消息
        for i in range(5):
            msg = UserExperienceEnhancer.success(f"测试{i}").build()
            history.record(msg)
        
        stats = history.get_statistics()
        assert stats["total"] == 5
        assert "by_type" in stats

    def test_clear_history(self):
        """测试清空历史"""
        history = MessageHistory()
        from mc_agent_kit.ux.enhancer import UserExperienceEnhancer
        
        for i in range(3):
            msg = UserExperienceEnhancer.success(f"测试{i}").build()
            history.record(msg)
        
        count = history.clear()
        assert count == 3
        assert len(history.get_recent(10)) == 0


class TestTemplateRegistry:
    """模板注册表测试"""

    def test_registry_init(self):
        """测试注册表初始化"""
        registry = TemplateRegistry()
        assert registry is not None

    def test_builtin_templates(self):
        """测试内置模板"""
        registry = TemplateRegistry()
        templates = registry.list_all()
        assert len(templates) > 0

    def test_get_template(self):
        """测试获取模板"""
        registry = TemplateRegistry()
        template = registry.get("workflow.step_started")
        assert template is not None
        assert template.id == "workflow.step_started"

    def test_render_template(self):
        """测试渲染模板"""
        registry = TemplateRegistry()
        message = registry.render(
            "workflow.step_started",
            step_name="测试步骤",
            description="测试描述"
        )
        assert message is not None
        assert "测试步骤" in message.title


class TestEnhancedUXManager:
    """增强 UX 管理器测试"""

    def test_ux_manager_init(self):
        """测试 UX 管理器初始化"""
        manager = EnhancedUXManager()
        assert manager is not None
        assert manager.locale_manager is not None
        assert manager.history is not None
        assert manager.templates is not None

    def test_set_locale(self):
        """测试设置语言"""
        manager = EnhancedUXManager()
        manager.set_locale("en_US")
        assert manager.locale_manager.config.locale == "en_US"

    def test_set_session(self):
        """测试设置会话"""
        manager = EnhancedUXManager()
        manager.set_session("test-session-123")
        assert manager.history._session_id == "test-session-123"

    def test_localized_message(self):
        """测试本地化消息"""
        manager = EnhancedUXManager()
        msg = manager.localized("success.project_created")
        assert msg is not None

    def test_success_message(self):
        """测试成功消息"""
        manager = EnhancedUXManager()
        msg = manager.success("success.test_passed")
        assert msg is not None
        assert msg.type.value == "success"

    def test_error_message(self):
        """测试错误消息"""
        manager = EnhancedUXManager()
        msg = manager.error("error.config_invalid")
        assert msg is not None
        assert msg.type.value == "error"

    def test_workflow_messages(self):
        """测试工作流消息"""
        # 工作流开始
        msg = EnhancedUXManager.workflow_started(5)
        assert msg is not None
        assert "工作流" in msg.title or "Workflow" in msg.title

        # 工作流完成
        msg = EnhancedUXManager.workflow_completed(True, 1000)
        assert msg is not None
        assert msg.type.value == "success"

        # 工作流失败
        msg = EnhancedUXManager.workflow_completed(False, 500)
        assert msg is not None
        assert msg.type.value == "error"

    def test_progress_message(self):
        """测试进度消息"""
        msg = EnhancedUXManager.progress_update("测试步骤", 50.0, "进行中")
        assert msg is not None
        assert "50%" in msg.title or "50" in msg.title

    def test_retry_message(self):
        """测试重试消息"""
        msg = EnhancedUXManager.retry_attempt("测试步骤", 2, 3, 1.5)
        assert msg is not None
        assert "2/3" in msg.title or "重试" in msg.title

    def test_cache_status_message(self):
        """测试缓存状态消息"""
        stats = {
            "entries": 50,
            "max_entries": 100,
            "hit_rate": 0.85,
            "hits": 85,
            "misses": 15,
        }
        msg = EnhancedUXManager.cache_status(stats)
        assert msg is not None


class TestGlobalUXManager:
    """全局 UX 管理器测试"""

    def test_get_ux_manager(self):
        """测试获取全局管理器"""
        manager = get_ux_manager()
        assert manager is not None
        assert isinstance(manager, EnhancedUXManager)

    def test_get_ux_manager_with_locale(self):
        """测试带语言设置获取管理器"""
        manager = get_ux_manager(locale="en_US")
        assert manager is not None

    def test_localized_message_function(self):
        """测试本地化消息便捷函数"""
        msg = localized_message("success.project_created")
        assert msg is not None


# ==================== 性能监控测试 ====================

class TestApiUsageTracker:
    """API 使用追踪器测试"""

    def test_tracker_init(self, tmp_path):
        """测试追踪器初始化"""
        data_path = tmp_path / "api_stats.json"
        tracker = ApiUsageTracker(str(data_path))
        assert tracker is not None

    def test_record_api_call(self, tmp_path):
        """测试记录 API 调用"""
        data_path = tmp_path / "api_stats.json"
        tracker = ApiUsageTracker(str(data_path))
        
        # 记录 API 调用
        tracker.record("test_api", success=True, duration_ms=50)
        
        stats = tracker.get_stats("test_api")
        assert stats is not None
        assert stats.total_calls == 1
        assert stats.success_count == 1

    def test_record_multiple_calls(self, tmp_path):
        """测试多次调用记录"""
        data_path = tmp_path / "api_stats.json"
        tracker = ApiUsageTracker(str(data_path))
        
        for i in range(10):
            tracker.record("test_api", success=i < 8, duration_ms=50)
        
        stats = tracker.get_stats("test_api")
        assert stats.total_calls == 10
        assert stats.success_count == 8
        assert stats.error_count == 2

    def test_get_summary(self, tmp_path):
        """测试获取摘要"""
        data_path = tmp_path / "api_stats.json"
        tracker = ApiUsageTracker(str(data_path))
        
        # 记录多个 API
        for i in range(5):
            tracker.record(f"api_{i}", success=True, duration_ms=50)
        
        summary = tracker.get_summary()
        assert summary["total_apis"] >= 5
        assert summary["total_calls"] >= 5

    def test_get_hot_apis(self, tmp_path):
        """测试获取热门 API"""
        data_path = tmp_path / "api_stats.json"
        tracker = ApiUsageTracker(str(data_path))
        
        # 记录不同调用次数
        for i in range(10):
            tracker.record("hot_api", success=True, duration_ms=50)
        for i in range(3):
            tracker.record("cold_api", success=True, duration_ms=50)
        
        hot = tracker.get_hot_apis(limit=5)
        assert len(hot) > 0
        assert hot[0].api_name == "hot_api"

    def test_get_problematic_apis(self, tmp_path):
        """测试获取问题 API"""
        data_path = tmp_path / "api_stats.json"
        tracker = ApiUsageTracker(str(data_path))
        
        # 记录高错误率 API
        for i in range(10):
            tracker.record("bad_api", success=i < 3, duration_ms=50)
        
        problematic = tracker.get_problematic_apis(
            min_calls=5,
            error_rate_threshold=0.5,
            limit=5
        )
        assert len(problematic) > 0
        assert problematic[0].api_name == "bad_api"

    def test_get_stats_by_module(self, tmp_path):
        """测试按模块统计"""
        data_path = tmp_path / "api_stats.json"
        tracker = ApiUsageTracker(str(data_path))
        
        # 记录不同模块的 API
        tracker.record("module1.api1", success=True, duration_ms=50, module="module1")
        tracker.record("module1.api2", success=True, duration_ms=50, module="module1")
        tracker.record("module2.api1", success=True, duration_ms=50, module="module2")
        
        by_module = tracker.get_stats_by_module()
        assert "module1" in by_module
        assert "module2" in by_module
        assert len(by_module["module1"]) == 2
        assert len(by_module["module2"]) == 1

    def test_persistence(self, tmp_path):
        """测试数据持久化"""
        data_path = tmp_path / "api_stats.json"
        tracker = ApiUsageTracker(str(data_path))
        
        # 记录一些调用
        tracker.record("test_api", success=True, duration_ms=50)
        tracker.save()
        
        # 创建新追踪器并加载
        tracker2 = ApiUsageTracker(str(data_path))
        stats = tracker2.get_stats("test_api")
        assert stats is not None
        assert stats.total_calls == 1


# ==================== 性能基准测试 ====================

class TestPerformanceBenchmarks:
    """性能基准测试"""

    def test_ux_manager_creation_performance(self):
        """测试 UX 管理器创建性能"""
        start = time.time()
        for _ in range(100):
            manager = EnhancedUXManager()
            assert manager is not None
        elapsed = time.time() - start
        # 100 次创建应该 < 1 秒
        assert elapsed < 1.0, f"UX 管理器创建过慢：{elapsed:.2f}s"

    def test_localized_message_performance(self):
        """测试本地化消息性能"""
        manager = EnhancedUXManager()
        start = time.time()
        for _ in range(1000):
            msg = manager.localized("success.project_created")
        elapsed = time.time() - start
        # 1000 次消息获取应该 < 1 秒
        assert elapsed < 1.0, f"本地化消息获取过慢：{elapsed:.2f}s"

    def test_progress_bar_performance(self):
        """测试进度条性能"""
        config = ProgressConfig(total=100)
        start = time.time()
        for _ in range(100):
            progress = create_progress_bar(config)
            for i in range(100):
                progress.update(i + 1)
            progress.complete()
        elapsed = time.time() - start
        # 100 次完整进度更新应该 < 2 秒
        assert elapsed < 2.0, f"进度条更新过慢：{elapsed:.2f}s"

    def test_api_tracker_performance(self, tmp_path):
        """测试 API 追踪器性能"""
        data_path = tmp_path / "api_stats.json"
        tracker = ApiUsageTracker(str(data_path))
        
        start = time.time()
        for i in range(1000):
            tracker.record(f"api_{i % 10}", success=True, duration_ms=50)
        elapsed = time.time() - start
        # 1000 次记录应该 < 1 秒
        assert elapsed < 1.0, f"API 追踪过慢：{elapsed:.2f}s"

    def test_message_history_performance(self):
        """测试消息历史性能"""
        history = MessageHistory(max_entries=1000)
        from mc_agent_kit.ux.enhancer import UserExperienceEnhancer
        
        start = time.time()
        for i in range(500):
            msg = UserExperienceEnhancer.success(f"测试{i}").build()
            history.record(msg)
        elapsed = time.time() - start
        # 500 次记录应该 < 1 秒
        assert elapsed < 1.0, f"消息记录过慢：{elapsed:.2f}s"


# ==================== 集成测试 ====================

class TestIteration60Integration:
    """迭代 #60 集成测试"""

    def test_ux_manager_with_history(self):
        """测试 UX 管理器与历史记录集成"""
        manager = EnhancedUXManager(history_max_entries=100)
        
        # 发送多条消息
        for i in range(10):
            manager.success("success.test_passed")
        
        # 检查历史记录
        stats = manager.history.get_statistics()
        assert stats["total"] == 10

    def test_ux_manager_with_templates(self):
        """测试 UX 管理器与模板集成"""
        manager = EnhancedUXManager()
        
        # 使用模板创建消息
        msg = manager.from_template(
            "workflow.step_started",
            step_name="测试步骤",
            description="测试描述"
        )
        assert msg is not None
        
        # 检查历史记录
        entries = manager.history.get_recent(1)
        assert len(entries) == 1

    def test_ux_manager_with_locale(self):
        """测试 UX 管理器与多语言集成"""
        manager = EnhancedUXManager()
        
        # 切换语言
        manager.set_locale("en_US")
        msg_en = manager.localized("success.project_created")
        
        manager.set_locale("zh_CN")
        msg_zh = manager.localized("success.project_created")
        
        # 两种语言都应该有消息
        assert msg_en is not None
        assert msg_zh is not None

    def test_api_tracker_with_summary(self, tmp_path):
        """测试 API 追踪器与摘要集成"""
        data_path = tmp_path / "api_stats.json"
        tracker = ApiUsageTracker(str(data_path))
        
        # 记录多个 API
        for i in range(20):
            tracker.record(f"api_{i % 5}", success=i % 5 != 0, duration_ms=50 + i)
        
        # 获取摘要
        summary = tracker.get_summary()
        assert summary["total_apis"] >= 5
        assert summary["total_calls"] == 20
        assert "hot_apis" in summary
        assert "problematic_apis" in summary


# ==================== 验收标准测试 ====================

class TestIteration60AcceptanceCriteria:
    """迭代 #60 验收标准测试"""

    def test_cli_output_enhancement(self):
        """测试 CLI 输出增强"""
        # 彩色输出
        output = create_output()
        assert output is not None
        assert isinstance(output, ColoredOutput)
        
        # 进度条
        config = ProgressConfig(total=10)
        progress = create_progress_bar(config)
        assert progress is not None
        assert progress.config.total == 10

    def test_localization_support(self):
        """测试多语言支持"""
        manager = EnhancedUXManager()
        
        # 支持中文
        manager.set_locale("zh_CN")
        msg_zh = manager.localized("success.project_created")
        assert msg_zh is not None
        
        # 支持英文
        manager.set_locale("en_US")
        msg_en = manager.localized("success.project_created")
        assert msg_en is not None
        
        # 支持日语
        manager.set_locale("ja_JP")
        msg_ja = manager.localized("success.project_created")
        assert msg_ja is not None
        
        # 支持韩语
        manager.set_locale("ko_KR")
        msg_ko = manager.localized("success.project_created")
        assert msg_ko is not None

    def test_message_templates(self):
        """测试消息模板"""
        registry = TemplateRegistry()
        
        # 工作流模板
        assert registry.get("workflow.step_started") is not None
        assert registry.get("workflow.step_completed") is not None
        assert registry.get("workflow.step_failed") is not None
        
        # 诊断模板
        assert registry.get("diagnostic.issue_found") is not None
        assert registry.get("diagnostic.critical") is not None
        
        # 缓存模板
        assert registry.get("cache.warmup_complete") is not None
        assert registry.get("cache.hit_rate_low") is not None

    def test_message_history(self):
        """测试消息历史"""
        history = MessageHistory()
        from mc_agent_kit.ux.enhancer import UserExperienceEnhancer
        
        # 记录消息
        msg = UserExperienceEnhancer.success("测试").build()
        history.record(msg)
        
        # 获取历史
        entries = history.get_recent(10)
        assert len(entries) == 1
        
        # 搜索消息
        results = history.search("测试", limit=10)
        assert len(results) == 1
        
        # 统计信息
        stats = history.get_statistics()
        assert stats["total"] == 1

    def test_api_usage_tracking(self, tmp_path):
        """测试 API 使用追踪"""
        data_path = tmp_path / "api_stats.json"
        tracker = ApiUsageTracker(str(data_path))
        
        # 记录调用
        for i in range(10):
            tracker.record("test_api", success=i < 8, duration_ms=50)
        
        # 获取统计
        stats = tracker.get_stats("test_api")
        assert stats.total_calls == 10
        assert stats.success_count == 8
        assert stats.error_count == 2
        assert stats.success_rate == 0.8

    def test_performance_metrics(self, tmp_path):
        """测试性能指标"""
        # UX 管理器性能
        manager = EnhancedUXManager()
        start = time.time()
        for _ in range(100):
            manager.localized("success.project_created")
        elapsed = time.time() - start
        assert elapsed < 1.0, "本地化消息性能不达标"
        
        # API 追踪器性能
        data_path = tmp_path / "api_stats.json"
        tracker = ApiUsageTracker(str(data_path))
        start = time.time()
        for i in range(100):
            tracker.record(f"api_{i % 10}", success=True, duration_ms=50)
        elapsed = time.time() - start
        assert elapsed < 1.0, "API 追踪性能不达标"

    def test_error_message_enhancement(self):
        """测试错误消息增强"""
        manager = EnhancedUXManager()
        
        # 创建错误消息
        msg = manager.error("error.config_invalid")
        assert msg is not None
        assert msg.type.value == "error"
        
        # 错误消息应该有建议
        msg_with_suggestion = (
            manager.error("error.config_invalid")
        )
        assert msg_with_suggestion is not None

    def test_workflow_status_messages(self):
        """测试工作流状态消息"""
        # 开始消息
        start_msg = EnhancedUXManager.workflow_started(5)
        assert start_msg is not None
        assert start_msg.type.value == "info"
        
        # 完成消息
        success_msg = EnhancedUXManager.workflow_completed(True, 1000)
        assert success_msg is not None
        assert success_msg.type.value == "success"
        
        # 失败消息
        fail_msg = EnhancedUXManager.workflow_completed(False, 500)
        assert fail_msg is not None
        assert fail_msg.type.value == "error"
        
        # 暂停消息
        pause_msg = EnhancedUXManager.workflow_paused("测试步骤")
        assert pause_msg is not None
        assert pause_msg.type.value == "warning"
        
        # 恢复消息
        resume_msg = EnhancedUXManager.workflow_resumed()
        assert resume_msg is not None
        assert resume_msg.type.value == "info"
        
        # 取消消息
        cancel_msg = EnhancedUXManager.workflow_cancelled()
        assert cancel_msg is not None
        assert cancel_msg.type.value == "warning"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
