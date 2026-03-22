"""
迭代 #43 测试

测试工作流增强、缓存增强和 UX 增强功能
"""

import pytest
import time
import threading
from unittest.mock import MagicMock, patch

from mc_agent_kit.workflow.enhanced import (
    EnhancedWorkflow,
    ProgressCallback,
    ProgressInfo,
    RetryConfig,
    RetryPolicy,
    SkipCondition,
    WorkflowControl,
    WorkflowState,
    create_enhanced_workflow,
)
from mc_agent_kit.workflow.end_to_end import (
    WorkflowConfig,
    WorkflowStep,
    WorkflowStepStatus,
)
from mc_agent_kit.workflow.cache_enhanced import (
    CacheEntryEnhanced,
    CacheMetrics,
    EnhancedCache,
    WarmupConfig,
    get_enhanced_cache,
    clear_enhanced_cache,
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
from mc_agent_kit.ux import MessageType, UserMessage


# === RetryConfig Tests ===

class TestRetryConfig:
    """重试配置测试"""

    def test_default_values(self):
        """测试默认值"""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.policy == RetryPolicy.LINEAR
        assert config.base_delay_seconds == 1.0
        assert config.max_delay_seconds == 30.0

    def test_linear_delay(self):
        """测试线性延迟"""
        config = RetryConfig(policy=RetryPolicy.LINEAR, base_delay_seconds=2.0)
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0
        assert config.get_delay(3) == 6.0

    def test_exponential_delay(self):
        """测试指数延迟"""
        config = RetryConfig(policy=RetryPolicy.EXPONENTIAL, base_delay_seconds=1.0)
        assert config.get_delay(1) == 1.0
        assert config.get_delay(2) == 2.0
        assert config.get_delay(3) == 4.0

    def test_max_delay_cap(self):
        """测试最大延迟限制"""
        config = RetryConfig(
            policy=RetryPolicy.EXPONENTIAL,
            base_delay_seconds=10.0,
            max_delay_seconds=30.0
        )
        assert config.get_delay(1) == 10.0
        assert config.get_delay(2) == 20.0
        assert config.get_delay(3) == 30.0  # capped
        assert config.get_delay(10) == 30.0  # capped

    def test_none_policy_delay(self):
        """测试无重试策略延迟"""
        config = RetryConfig(policy=RetryPolicy.NONE)
        assert config.get_delay(1) == 0
        assert config.get_delay(10) == 0


# === WorkflowControl Tests ===

class TestWorkflowControl:
    """工作流控制测试"""

    def test_initial_state(self):
        """测试初始状态"""
        control = WorkflowControl()
        assert control.state == WorkflowState.IDLE
        assert not control.is_cancelled()

    def test_pause_and_resume(self):
        """测试暂停和恢复"""
        control = WorkflowControl()
        
        # 暂停
        control.pause()
        assert control.state == WorkflowState.PAUSED
        
        # 恢复
        control.resume()
        assert control.state == WorkflowState.RUNNING

    def test_cancel(self):
        """测试取消"""
        control = WorkflowControl()
        control.cancel()
        assert control.state == WorkflowState.CANCELLED
        assert control.is_cancelled()


# === ProgressInfo Tests ===

class TestProgressInfo:
    """进度信息测试"""

    def test_to_dict(self):
        """测试转换为字典"""
        info = ProgressInfo(
            current_step=WorkflowStep.SEARCH_DOCS,
            total_steps=5,
            completed_steps=2,
            percentage=40.0,
            elapsed_seconds=10.0,
            estimated_remaining_seconds=15.0,
            message="正在搜索...",
        )
        data = info.to_dict()
        
        assert data["current_step"] == "search_docs"
        assert data["total_steps"] == 5
        assert data["completed_steps"] == 2
        assert data["percentage"] == 40.0
        assert data["elapsed_seconds"] == 10.0
        assert data["estimated_remaining_seconds"] == 15.0
        assert data["message"] == "正在搜索..."


# === EnhancedWorkflow Tests ===

class TestEnhancedWorkflow:
    """增强工作流测试"""

    def test_create_with_defaults(self):
        """测试默认创建"""
        config = WorkflowConfig()
        workflow = EnhancedWorkflow(config)
        
        assert workflow.config == config
        assert workflow.control.state == WorkflowState.IDLE

    def test_add_skip_condition(self):
        """测试添加跳过条件"""
        config = WorkflowConfig()
        workflow = EnhancedWorkflow(config)
        
        workflow.add_skip_condition(
            WorkflowStep.SEARCH_DOCS,
            lambda ctx: not ctx.get("search_query"),
            "未提供搜索查询"
        )
        
        assert WorkflowStep.SEARCH_DOCS in workflow._skip_conditions

    def test_progress_callback(self):
        """测试进度回调"""
        config = WorkflowConfig()
        progress_messages = []
        
        def callback(info: ProgressInfo):
            progress_messages.append(info.message)
        
        workflow = EnhancedWorkflow(config, progress_callback=callback)
        workflow._report_progress(WorkflowStep.SEARCH_DOCS, "test", 5)
        
        assert len(progress_messages) == 1
        assert progress_messages[0] == "test"


# === CacheMetrics Tests ===

class TestCacheMetrics:
    """缓存指标测试"""

    def test_hit_rate_zero(self):
        """测试零命中率"""
        metrics = CacheMetrics()
        assert metrics.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        """测试命中率计算"""
        metrics = CacheMetrics(hits=3, misses=1)
        assert metrics.hit_rate == 0.75

    def test_to_dict(self):
        """测试转换为字典"""
        metrics = CacheMetrics(hits=10, misses=5, evictions=2)
        data = metrics.to_dict()
        
        assert data["hits"] == 10
        assert data["misses"] == 5
        assert data["evictions"] == 2
        assert abs(data["hit_rate"] - (10 / 15)) < 0.001


# === CacheEntryEnhanced Tests ===

class TestCacheEntryEnhanced:
    """增强缓存条目测试"""

    def test_default_values(self):
        """测试默认值"""
        entry = CacheEntryEnhanced(key="test", value="data")
        assert entry.key == "test"
        assert entry.value == "data"
        assert entry.ttl_seconds == 3600
        assert entry.hits == 0
        assert entry.is_warmup == False

    def test_is_expired(self):
        """测试过期判断"""
        entry = CacheEntryEnhanced(key="test", value="data", ttl_seconds=1)
        assert not entry.is_expired()
        
        time.sleep(1.1)
        assert entry.is_expired()

    def test_touch(self):
        """测试访问更新"""
        entry = CacheEntryEnhanced(key="test", value="data")
        old_updated_at = entry.updated_at
        time.sleep(0.01)
        entry.touch()
        
        assert entry.hits == 1
        assert entry.updated_at > old_updated_at

    def test_to_dict(self):
        """测试转换为字典"""
        entry = CacheEntryEnhanced(
            key="test",
            value="data",
            tags={"api", "search"}
        )
        data = entry.to_dict()
        
        assert data["key"] == "test"
        assert "api" in data["tags"]
        assert "search" in data["tags"]


# === EnhancedCache Tests ===

class TestEnhancedCache:
    """增强缓存测试"""

    def test_set_and_get(self):
        """测试设置和获取"""
        cache = EnhancedCache()
        cache.set("value1", "key1")
        
        result = cache.get("key1")
        assert result == "value1"

    def test_miss(self):
        """测试未命中"""
        cache = EnhancedCache()
        result = cache.get("nonexistent")
        assert result is None
        
        stats = cache.get_stats()
        assert stats["misses"] == 1

    def test_batch_operations(self):
        """测试批量操作"""
        cache = EnhancedCache()
        
        # 批量设置
        items = [
            ("value1", ("key1",), {}),
            ("value2", ("key2",), {}),
            ("value3", ("key3",), {}),
        ]
        count = cache.set_batch(items)
        assert count == 3
        
        # 批量获取
        keys = [(("key1",), {}), (("key2",), {})]
        results = cache.get_batch(keys)
        assert len(results) == 2

    def test_invalidate_by_tag(self):
        """测试按标签失效"""
        cache = EnhancedCache()
        
        cache.set("value1", "key1", tags={"api"})
        cache.set("value2", "key2", tags={"api"})
        cache.set("value3", "key3", tags={"event"})
        
        count = cache.invalidate_by_tag("api")
        assert count == 2
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"

    def test_warmup(self):
        """测试预热"""
        def warmup_func():
            return {"warm_key": "warm_value"}
        
        config = WarmupConfig(warmup_functions={"test": warmup_func})
        cache = EnhancedCache(warmup_config=config)
        
        count = cache.warmup()
        assert count == 1
        
        result = cache.get("warm_key")
        assert result == "warm_value"

    def test_metrics(self):
        """测试指标统计"""
        cache = EnhancedCache()
        
        cache.set("value1", "key1")
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("nonexistent")  # miss
        
        metrics = cache.get_metrics()
        assert metrics.hits == 2
        assert metrics.misses == 1
        assert abs(metrics.hit_rate - 0.6666) < 0.01

    def test_size_limit(self):
        """测试大小限制"""
        cache = EnhancedCache(max_entries=2)
        
        cache.set("value1", "key1")
        cache.set("value2", "key2")
        cache.set("value3", "key3")  # 应该触发淘汰
        
        stats = cache.get_stats()
        assert stats["entries"] <= 2
        assert stats["evictions"] >= 1


# === LocaleManager Tests ===

class TestLocaleManager:
    """本地化管理器测试"""

    def test_default_locale(self):
        """测试默认语言"""
        manager = LocaleManager()
        assert manager.config.locale == "zh_CN"

    def test_get_message_zh(self):
        """测试中文消息"""
        manager = LocaleManager(LocaleConfig(locale="zh_CN"))
        msg = manager.get("success.project_created")
        assert msg == "项目创建成功"

    def test_get_message_en(self):
        """测试英文消息"""
        manager = LocaleManager(LocaleConfig(locale="en_US"))
        msg = manager.get("success.project_created")
        assert msg == "Project created successfully"

    def test_format_message(self):
        """测试格式化消息"""
        manager = LocaleManager(LocaleConfig(locale="zh_CN"))
        msg = manager.get("success.entity_created", name="test_entity")
        assert msg == "实体 'test_entity' 创建成功"

    def test_fallback_locale(self):
        """测试后备语言"""
        manager = LocaleManager(LocaleConfig(locale="unknown", fallback_locale="en_US"))
        msg = manager.get("success.project_created")
        assert msg == "Project created successfully"

    def test_custom_message(self):
        """测试自定义消息"""
        manager = LocaleManager()
        manager.register_custom_message("custom.key", "自定义消息")
        
        msg = manager.get("custom.key")
        assert msg == "自定义消息"


# === MessageHistory Tests ===

class TestMessageHistory:
    """消息历史测试"""

    def test_record_and_retrieve(self):
        """测试记录和获取"""
        history = MessageHistory()
        msg = UserMessage(type=MessageType.SUCCESS, title="测试")
        
        history.record(msg)
        entries = history.get_recent()
        
        assert len(entries) == 1
        assert entries[0].message.title == "测试"

    def test_max_entries(self):
        """测试最大条目数"""
        history = MessageHistory(max_entries=5)
        
        for i in range(10):
            msg = UserMessage(type=MessageType.INFO, title=f"消息{i}")
            history.record(msg)
        
        entries = history.get_recent(20)
        assert len(entries) == 5

    def test_get_by_type(self):
        """测试按类型获取"""
        history = MessageHistory()
        
        history.record(UserMessage(type=MessageType.SUCCESS, title="成功1"))
        history.record(UserMessage(type=MessageType.ERROR, title="错误1"))
        history.record(UserMessage(type=MessageType.SUCCESS, title="成功2"))
        
        success_entries = history.get_by_type(MessageType.SUCCESS)
        error_entries = history.get_by_type(MessageType.ERROR)
        
        assert len(success_entries) == 2
        assert len(error_entries) == 1

    def test_search(self):
        """测试搜索"""
        history = MessageHistory()
        
        history.record(UserMessage(type=MessageType.INFO, title="搜索API"))
        history.record(UserMessage(type=MessageType.INFO, title="搜索事件"))
        history.record(UserMessage(type=MessageType.INFO, title="创建项目"))
        
        results = history.search("搜索")
        assert len(results) == 2

    def test_statistics(self):
        """测试统计"""
        history = MessageHistory()
        
        history.record(UserMessage(type=MessageType.SUCCESS, title="成功"))
        history.record(UserMessage(type=MessageType.SUCCESS, title="成功"))
        history.record(UserMessage(type=MessageType.ERROR, title="错误"))
        
        stats = history.get_statistics()
        assert stats["total"] == 3
        assert stats["by_type"]["success"] == 2
        assert stats["by_type"]["error"] == 1


# === MessageTemplate Tests ===

class TestMessageTemplate:
    """消息模板测试"""

    def test_render(self):
        """测试渲染"""
        template = MessageTemplate(
            id="test.template",
            type=MessageType.SUCCESS,
            title_template="操作 {name} 成功",
            content_template="耗时 {duration}ms",
        )
        
        msg = template.render(name="测试", duration=100)
        
        assert msg.title == "操作 测试 成功"
        assert msg.content == "耗时 100ms"

    def test_render_with_suggestions(self):
        """测试带建议的渲染"""
        template = MessageTemplate(
            id="test.template",
            type=MessageType.ERROR,
            title_template="错误: {error}",
            suggestion_templates=["建议1: {fix}", "建议2"],
        )
        
        msg = template.render(error="语法错误", fix="检查语法")
        
        assert msg.title == "错误: 语法错误"
        assert len(msg.suggestions) == 2
        assert "检查语法" in msg.suggestions[0]


# === TemplateRegistry Tests ===

class TestTemplateRegistry:
    """模板注册表测试"""

    def test_builtin_templates(self):
        """测试内置模板"""
        registry = TemplateRegistry()
        templates = registry.list_all()
        
        assert len(templates) > 0
        assert registry.get("workflow.step_started") is not None

    def test_register_and_get(self):
        """测试注册和获取"""
        registry = TemplateRegistry()
        
        template = MessageTemplate(
            id="custom.test",
            type=MessageType.INFO,
            title_template="自定义模板",
        )
        registry.register(template)
        
        assert registry.get("custom.test") is not None

    def test_render(self):
        """测试渲染"""
        registry = TemplateRegistry()
        
        msg = registry.render("workflow.step_started", step_name="测试", description="描述")
        
        assert msg is not None
        assert "测试" in msg.title


# === EnhancedUXManager Tests ===

class TestEnhancedUXManager:
    """增强 UX 管理器测试"""

    def test_create(self):
        """测试创建"""
        manager = EnhancedUXManager()
        assert manager.is_enabled()

    def test_enable_disable(self):
        """测试启用/禁用"""
        manager = EnhancedUXManager()
        
        manager.disable()
        assert not manager.is_enabled()
        
        manager.enable()
        assert manager.is_enabled()

    def test_localized(self):
        """测试本地化"""
        manager = EnhancedUXManager(LocaleConfig(locale="zh_CN"))
        
        msg = manager.localized("success.project_created")
        assert msg == "项目创建成功"

    def test_message_recording(self):
        """测试消息记录"""
        manager = EnhancedUXManager()
        
        manager.success("success.project_created")
        
        stats = manager.history.get_statistics()
        assert stats["total"] == 1

    def test_from_template(self):
        """测试从模板创建"""
        manager = EnhancedUXManager()
        
        msg = manager.from_template("workflow.step_started", step_name="测试", description="描述")
        
        assert msg is not None
        assert "测试" in msg.title

    def test_set_session(self):
        """测试设置会话"""
        manager = EnhancedUXManager()
        manager.set_session("test_session")
        
        manager.success("success.project_created")
        
        entries = manager.history.get_by_session("test_session")
        assert len(entries) == 1


# === Convenience Functions Tests ===

class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_get_ux_manager(self):
        """测试获取 UX 管理器"""
        manager = get_ux_manager()
        assert manager is not None

    def test_localized_message(self):
        """测试本地化消息函数"""
        msg = localized_message("success.project_created")
        assert msg == "项目创建成功"

    def test_get_enhanced_cache(self):
        """测试获取增强缓存"""
        cache = get_enhanced_cache()
        assert cache is not None


# === Integration Tests ===

class TestIteration43Integration:
    """集成测试"""

    def test_workflow_with_progress_and_skip(self):
        """测试带进度和跳过的工作流"""
        progress_messages = []
        
        def callback(info):
            progress_messages.append(info.current_step)
        
        config = WorkflowConfig(project_name="test_project")
        workflow = EnhancedWorkflow(config, progress_callback=callback)
        
        # 添加跳过条件
        workflow.add_skip_condition(
            WorkflowStep.SEARCH_DOCS,
            lambda ctx: True,  # 总是跳过
            "测试跳过"
        )
        
        # 执行
        result = workflow.run_full_cycle(search_query="test")
        
        # 验证搜索步骤被跳过
        search_result = next(
            (s for s in result.steps if s.step == WorkflowStep.SEARCH_DOCS),
            None
        )
        assert search_result is not None
        assert search_result.status == WorkflowStepStatus.SKIPPED

    def test_cache_with_workflow_context(self):
        """测试缓存与工作流上下文"""
        cache = EnhancedCache()
        
        # 模拟工作流步骤结果缓存
        cache.set(
            {"apis": ["CreateEntity"], "events": ["OnServerChat"]},
            "search", "create_entity", tags={"workflow", "search"}
        )
        
        # 获取缓存
        result = cache.get("search", "create_entity")
        assert result is not None
        assert "CreateEntity" in result["apis"]
        
        # 按标签失效
        cache.invalidate_by_tag("workflow")
        
        result = cache.get("search", "create_entity")
        assert result is None

    def test_ux_with_workflow_messages(self):
        """测试 UX 与工作流消息"""
        manager = EnhancedUXManager()
        
        # 工作流开始
        msg = EnhancedUXManager.workflow_started(5)
        manager.message(msg)
        
        # 步骤进度
        msg = EnhancedUXManager.progress_update("搜索文档", 20.0, "正在执行")
        manager.message(msg)
        
        # 工作流完成
        msg = EnhancedUXManager.workflow_completed(True, 1500)
        manager.message(msg)
        
        stats = manager.history.get_statistics()
        assert stats["total"] == 3

    def test_retry_with_enhanced_workflow(self):
        """测试增强工作流的重试功能"""
        config = WorkflowConfig(project_name="test")
        retry_config = RetryConfig(max_retries=2, policy=RetryPolicy.LINEAR)
        
        workflow = EnhancedWorkflow(config, retry_config=retry_config)
        
        assert workflow.retry_config.max_retries == 2
        assert workflow.retry_config.policy == RetryPolicy.LINEAR


# === Performance Tests ===

class TestIteration43Performance:
    """性能测试"""

    def test_cache_performance(self):
        """测试缓存性能"""
        cache = EnhancedCache()
        
        # 100 次操作应在 1 秒内完成
        start = time.time()
        for i in range(100):
            cache.set(f"value_{i}", f"key_{i}")
            cache.get(f"key_{i}")
        duration = time.time() - start
        
        assert duration < 1.0

    def test_message_history_performance(self):
        """测试消息历史性能"""
        history = MessageHistory()
        
        # 100 次记录应在 1 秒内完成
        start = time.time()
        for i in range(100):
            history.record(UserMessage(type=MessageType.INFO, title=f"消息{i}"))
        duration = time.time() - start
        
        assert duration < 1.0


# === Acceptance Criteria Tests ===

class TestIteration43AcceptanceCriteria:
    """验收标准测试"""

    def test_retry_mechanism_configurable(self):
        """重试机制可配置"""
        config = RetryConfig(max_retries=5, policy=RetryPolicy.EXPONENTIAL)
        assert config.max_retries == 5
        assert config.policy == RetryPolicy.EXPONENTIAL

    def test_skip_condition_customizable(self):
        """跳过条件可自定义"""
        workflow = EnhancedWorkflow(WorkflowConfig())
        
        custom_condition = lambda ctx: ctx.get("skip_me", False)
        workflow.add_skip_condition(WorkflowStep.SEARCH_DOCS, custom_condition, "自定义原因")
        
        assert WorkflowStep.SEARCH_DOCS in workflow._skip_conditions

    def test_progress_callback_available(self):
        """进度回调可用"""
        calls = []
        
        def callback(info):
            calls.append(info)
        
        workflow = EnhancedWorkflow(WorkflowConfig(), progress_callback=callback)
        workflow._report_progress(WorkflowStep.SEARCH_DOCS, "test", 5)
        
        assert len(calls) == 1

    def test_pause_resume_functional(self):
        """暂停/恢复功能正常"""
        control = WorkflowControl()
        
        control.pause()
        assert control.state == WorkflowState.PAUSED
        
        control.resume()
        assert control.state == WorkflowState.RUNNING

    def test_cache_warmup_configurable(self):
        """缓存预热可配置"""
        def warmup():
            return {"key": "value"}
        
        config = WarmupConfig(warmup_functions={"test": warmup})
        cache = EnhancedCache(warmup_config=config)
        
        count = cache.warmup()
        assert count == 1

    def test_batch_operations_improved(self):
        """批量操作性能提升"""
        cache = EnhancedCache()
        
        # 批量设置 100 个条目
        items = [(f"value_{i}", (f"key_{i}",), {}) for i in range(100)]
        
        start = time.time()
        cache.set_batch(items)
        duration = time.time() - start
        
        assert duration < 0.5  # 批量操作应很快

    def test_hit_rate_monitoring_available(self):
        """命中率监控可用"""
        cache = EnhancedCache()
        
        cache.set("v1", "k1")
        cache.get("k1")
        cache.get("k1")
        cache.get("missing")
        
        metrics = cache.get_metrics()
        assert metrics.hits == 2
        assert metrics.misses == 1
        assert metrics.hit_rate > 0

    def test_localization_supports_zh_en(self):
        """本地化支持中英文"""
        zh_manager = LocaleManager(LocaleConfig(locale="zh_CN"))
        en_manager = LocaleManager(LocaleConfig(locale="en_US"))
        
        zh_msg = zh_manager.get("success.project_created")
        en_msg = en_manager.get("success.project_created")
        
        assert zh_msg == "项目创建成功"
        assert en_msg == "Project created successfully"

    def test_message_history_queryable(self):
        """消息历史可查询"""
        history = MessageHistory()
        
        history.record(UserMessage(type=MessageType.SUCCESS, title="成功消息"))
        history.record(UserMessage(type=MessageType.ERROR, title="错误消息"))
        
        stats = history.get_statistics()
        assert stats["total"] == 2
        assert stats["by_type"]["success"] == 1
        assert stats["by_type"]["error"] == 1

    def test_custom_templates_available(self):
        """自定义模板可用"""
        registry = TemplateRegistry()
        
        custom = MessageTemplate(
            id="my.custom.template",
            type=MessageType.INFO,
            title_template="自定义: {value}",
        )
        registry.register(custom)
        
        msg = registry.render("my.custom.template", value="test")
        assert msg is not None
        assert "test" in msg.title