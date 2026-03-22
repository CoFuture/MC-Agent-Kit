"""
迭代 #42 测试：工作流 CLI 命令、UX 集成和性能优化

测试目标:
1. 工作流 CLI 命令 (mc-agent workflow run/search/create/diagnose/cache)
2. UX 模块 CLI 集成
3. 性能优化（工作流缓存）
"""

import pytest
from pathlib import Path
import tempfile
import json
import time

# 导入被测模块
from mc_agent_kit.workflow import (
    EndToEndWorkflow,
    WorkflowConfig,
    WorkflowResult,
    WorkflowStep,
    WorkflowStepStatus,
    WorkflowStepResult,
    WorkflowCache,
    CacheEntry,
    create_workflow,
    get_workflow_cache,
    clear_workflow_cache,
)
from mc_agent_kit.ux import (
    UserMessage,
    UserMessageBuilder,
    UserExperienceEnhancer,
    CLIOutputFormatter,
    MessageType,
    OutputFormat,
)


# ============================================================
# 工作流缓存测试
# ============================================================

class TestWorkflowCache:
    """工作流缓存测试"""

    def test_cache_creation(self):
        """测试缓存创建"""
        cache = WorkflowCache()
        assert cache.get_stats()["entries"] == 0

    def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        cache = WorkflowCache()

        # 设置缓存
        cache.set("test_value", "key1", param="value1")

        # 获取缓存
        result = cache.get("key1", param="value1")
        assert result == "test_value"

    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = WorkflowCache()

        result = cache.get("nonexistent_key")
        assert result is None

        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0

    def test_cache_hit_rate(self):
        """测试缓存命中率"""
        cache = WorkflowCache()

        cache.set("value1", "key1")
        cache.get("key1")  # 命中
        cache.get("key2")  # 未命中

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_cache_invalidate(self):
        """测试缓存失效"""
        cache = WorkflowCache()

        cache.set("value1", "key1")
        assert cache.get("key1") == "value1"

        # 使缓存失效
        result = cache.invalidate("key1")
        assert result is True
        assert cache.get("key1") is None

    def test_cache_clear(self):
        """测试缓存清空"""
        cache = WorkflowCache()

        cache.set("value1", "key1")
        cache.set("value2", "key2")

        count = cache.clear()
        assert count == 2
        assert cache.get_stats()["entries"] == 0

    def test_cache_max_entries(self):
        """测试缓存最大条目限制"""
        cache = WorkflowCache(max_entries=3)

        cache.set("value1", "key1")
        cache.set("value2", "key2")
        cache.set("value3", "key3")
        cache.set("value4", "key4")  # 应该触发 LRU 淘汰

        stats = cache.get_stats()
        assert stats["entries"] <= 3

    def test_cache_ttl(self):
        """测试缓存 TTL"""
        cache = WorkflowCache(default_ttl=1)  # 1 秒 TTL

        cache.set("value1", "key1")

        # 立即获取应该成功
        result = cache.get("key1")
        assert result == "value1"

        # 等待过期
        time.sleep(1.1)

        # 过期后应该返回 None
        result = cache.get("key1")
        assert result is None

    def test_cache_cleanup_expired(self):
        """测试清理过期条目"""
        cache = WorkflowCache(default_ttl=1)

        cache.set("value1", "key1")
        cache.set("value2", "key2", ttl_seconds=10)  # 长 TTL

        time.sleep(1.1)

        count = cache.cleanup_expired()
        assert count == 1  # 只有过期的被清理

    def test_cache_with_dict_value(self):
        """测试缓存字典值"""
        cache = WorkflowCache()

        value = {"name": "test", "data": [1, 2, 3]}
        cache.set(value, "dict_key")

        result = cache.get("dict_key")
        assert result == value


class TestCacheEntry:
    """缓存条目测试"""

    def test_entry_creation(self):
        """测试条目创建"""
        entry = CacheEntry(key="test_key", value="test_value")
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.hits == 0

    def test_entry_not_expired(self):
        """测试条目未过期"""
        entry = CacheEntry(key="test", value="value", ttl_seconds=3600)
        assert not entry.is_expired()

    def test_entry_expired(self):
        """测试条目过期"""
        entry = CacheEntry(
            key="test",
            value="value",
            ttl_seconds=1,  # 1 秒 TTL
        )
        # 调整创建时间为过去
        entry.created_at = 0
        assert entry.is_expired()

    def test_entry_to_dict(self):
        """测试条目序列化"""
        entry = CacheEntry(key="test", value="value", ttl_seconds=3600)
        data = entry.to_dict()

        assert data["key"] == "test"
        assert data["value"] == "value"
        assert "created_at" in data


class TestGlobalCache:
    """全局缓存测试"""

    def test_get_workflow_cache(self):
        """测试获取全局缓存"""
        cache1 = get_workflow_cache()
        cache2 = get_workflow_cache()

        # 应该返回同一个实例
        assert cache1 is cache2

    def test_clear_workflow_cache(self):
        """测试清空全局缓存"""
        cache = get_workflow_cache()
        cache.set("value1", "key1")

        count = clear_workflow_cache()
        assert count >= 1


# ============================================================
# 工作流步骤测试
# ============================================================

class TestWorkflowStepResultEnhanced:
    """工作流步骤结果增强测试"""

    def test_step_result_with_suggestions(self):
        """测试步骤结果包含建议"""
        result = WorkflowStepResult(
            step=WorkflowStep.SEARCH_DOCS,
            status=WorkflowStepStatus.SUCCESS,
            suggestions=["建议1", "建议2"],
        )

        assert len(result.suggestions) == 2
        assert result.step == WorkflowStep.SEARCH_DOCS

    def test_step_result_to_dict(self):
        """测试步骤结果序列化"""
        result = WorkflowStepResult(
            step=WorkflowStep.CREATE_PROJECT,
            status=WorkflowStepStatus.SUCCESS,
            output={"project_path": "/test/path"},
        )

        data = result.to_dict()
        assert data["step"] == "create_project"
        assert data["status"] == "success"
        assert data["output"]["project_path"] == "/test/path"


class TestWorkflowResultEnhanced:
    """工作流结果增强测试"""

    def test_workflow_result_failed_steps(self):
        """测试获取失败步骤"""
        result = WorkflowResult(
            success=False,
            steps=[
                WorkflowStepResult(step=WorkflowStep.SEARCH_DOCS, status=WorkflowStepStatus.SUCCESS),
                WorkflowStepResult(step=WorkflowStep.CREATE_PROJECT, status=WorkflowStepStatus.FAILED),
            ],
        )

        assert len(result.failed_steps) == 1
        assert result.failed_steps[0].step == WorkflowStep.CREATE_PROJECT

    def test_workflow_result_success_steps(self):
        """测试获取成功步骤"""
        result = WorkflowResult(
            success=True,
            steps=[
                WorkflowStepResult(step=WorkflowStep.SEARCH_DOCS, status=WorkflowStepStatus.SUCCESS),
                WorkflowStepResult(step=WorkflowStep.CREATE_PROJECT, status=WorkflowStepStatus.SUCCESS),
            ],
        )

        assert len(result.success_steps) == 2


# ============================================================
# UX 模块增强测试
# ============================================================

class TestUserMessageEnhanced:
    """用户消息增强测试"""

    def test_message_with_multiple_suggestions(self):
        """测试多建议消息"""
        msg = (
            UserMessageBuilder(MessageType.ERROR, "发生错误")
            .content("详细错误信息")
            .suggestion("建议1")
            .suggestion("建议2")
            .suggestion("建议3")
            .build()
        )

        assert len(msg.suggestions) == 3
        text = msg.to_text()
        assert "建议1" in text
        assert "建议2" in text

    def test_message_to_markdown(self):
        """测试消息转换为 Markdown"""
        msg = (
            UserMessageBuilder(MessageType.SUCCESS, "操作成功")
            .content("操作完成")
            .detail("详情1")
            .build()
        )

        md = msg.to_markdown()
        assert "##" in md
        assert "操作成功" in md

    def test_message_to_json(self):
        """测试消息转换为 JSON"""
        msg = UserMessage(
            type=MessageType.INFO,
            title="测试消息",
            content="内容",
        )

        data = msg.to_json()
        assert data["type"] == "info"
        assert data["title"] == "测试消息"


class TestUserExperienceEnhancerEnhanced:
    """用户体验增强器增强测试"""

    def test_project_created_message(self):
        """测试项目创建消息"""
        msg = UserExperienceEnhancer.project_created("/path/to/project")

        assert msg.type == MessageType.SUCCESS
        assert "项目创建成功" in msg.title
        assert len(msg.suggestions) >= 1

    def test_entity_created_message(self):
        """测试实体创建消息"""
        msg = UserExperienceEnhancer.entity_created("TestEntity", "/path/to/entity")

        assert msg.type == MessageType.SUCCESS
        assert "TestEntity" in msg.title
        assert msg.code_example is not None

    def test_search_result_message(self):
        """测试搜索结果消息"""
        msg = UserExperienceEnhancer.search_result("测试查询", 5, 3)

        assert msg.type == MessageType.INFO
        assert "测试查询" in msg.title
        assert len(msg.suggestions) >= 1

    def test_diagnostic_issue_message(self):
        """测试诊断问题消息"""
        msg = UserExperienceEnhancer.diagnostic_issue(
            "内存",
            "内存不足",
            "增加内存配置",
        )

        assert msg.type == MessageType.ERROR
        assert "内存" in msg.title

    def test_memory_issue_message(self):
        """测试内存问题消息"""
        msg = UserExperienceEnhancer.memory_issue("texture", "纹理过大")

        assert msg.type == MessageType.WARNING
        assert "texture" in msg.title

    def test_api_not_found_message(self):
        """测试 API 未找到消息"""
        msg = UserExperienceEnhancer.api_not_found("UnknownAPI")

        assert msg.type == MessageType.WARNING
        assert "UnknownAPI" in msg.title
        assert len(msg.suggestions) >= 1

    def test_config_invalid_message(self):
        """测试配置无效消息"""
        msg = UserExperienceEnhancer.config_invalid(
            "/path/to/config.json",
            ["错误1", "错误2"],
        )

        assert msg.type == MessageType.ERROR
        assert "配置文件无效" in msg.title

    def test_game_launch_failed_message(self):
        """测试游戏启动失败消息"""
        msg = UserExperienceEnhancer.game_launch_failed("路径不存在")

        assert msg.type == MessageType.ERROR
        assert "游戏启动失败" in msg.title
        assert len(msg.suggestions) >= 1


class TestCLIOutputFormatterEnhanced:
    """CLI 输出格式化器增强测试"""

    def test_format_table_with_title(self):
        """测试带标题的表格格式化"""
        output = CLIOutputFormatter.format_table(
            headers=["名称", "类型"],
            rows=[["API1", "api"], ["Event1", "event"]],
            title="测试表格",
        )

        assert "测试表格" in output
        assert "API1" in output
        assert "Event1" in output

    def test_format_list_numbered(self):
        """测试编号列表格式化"""
        output = CLIOutputFormatter.format_list(
            items=["项目1", "项目2", "项目3"],
            title="列表",
            numbered=True,
        )

        assert "1." in output
        assert "2." in output
        assert "3." in output

    def test_format_list_bulleted(self):
        """测试项目符号列表格式化"""
        output = CLIOutputFormatter.format_list(
            items=["项目1", "项目2"],
            numbered=False,
        )

        assert "•" in output

    def test_format_key_value_with_nested(self):
        """测试嵌套键值对格式化"""
        output = CLIOutputFormatter.format_key_value(
            data={
                "name": "test",
                "items": [1, 2, 3],
                "config": {"key": "value"},
            },
            title="配置",
        )

        assert "name" in output
        assert "items" in output
        assert "config" in output


# ============================================================
# 集成测试
# ============================================================

class TestIteration42Integration:
    """迭代 #42 集成测试"""

    def test_workflow_with_cache(self):
        """测试工作流与缓存集成"""
        # 创建缓存
        cache = WorkflowCache()

        # 设置一些缓存数据
        cache.set({"cached": "data"}, "search", query="test")

        # 验证缓存可用
        result = cache.get("search", query="test")
        assert result == {"cached": "data"}

    def test_workflow_result_formatting(self):
        """测试工作流结果格式化"""
        # 创建工作流结果
        result = WorkflowResult(
            success=True,
            steps=[
                WorkflowStepResult(
                    step=WorkflowStep.SEARCH_DOCS,
                    status=WorkflowStepStatus.SUCCESS,
                    output={"api_count": 5, "event_count": 3},
                ),
                WorkflowStepResult(
                    step=WorkflowStep.CREATE_PROJECT,
                    status=WorkflowStepStatus.SUCCESS,
                    output={"project_path": "/test/project"},
                ),
            ],
            total_duration_ms=1500,
        )

        # 格式化输出
        data = result.to_dict()

        assert data["success"] is True
        assert data["total_duration_ms"] == 1500
        assert len(data["steps"]) == 2

    def test_ux_message_from_workflow_result(self):
        """测试从工作流结果创建 UX 消息"""
        # 模拟项目创建步骤
        step_result = WorkflowStepResult(
            step=WorkflowStep.CREATE_PROJECT,
            status=WorkflowStepStatus.SUCCESS,
            output={"project_path": "/test/project"},
        )

        # 创建 UX 消息
        if step_result.status == WorkflowStepStatus.SUCCESS:
            msg = UserExperienceEnhancer.project_created(
                step_result.output.get("project_path")
            )

            assert msg.type == MessageType.SUCCESS
            assert "项目创建成功" in msg.title


class TestIteration42Performance:
    """迭代 #42 性能测试"""

    def test_cache_performance(self):
        """测试缓存性能"""
        cache = WorkflowCache()

        start_time = time.time()

        # 执行 100 次缓存操作
        for i in range(100):
            cache.set(f"value_{i}", f"key_{i}")

        for i in range(100):
            cache.get(f"key_{i}")

        elapsed = time.time() - start_time

        # 100 次操作应该在 1 秒内完成
        assert elapsed < 1.0

    def test_message_formatting_performance(self):
        """测试消息格式化性能"""
        start_time = time.time()

        # 创建并格式化 100 条消息
        for i in range(100):
            msg = UserExperienceEnhancer.project_created(f"/project/{i}")
            msg.to_text()

        elapsed = time.time() - start_time

        # 100 条消息应该在 1 秒内完成
        assert elapsed < 1.0


class TestIteration42AcceptanceCriteria:
    """迭代 #42 验收标准测试"""

    def test_workflow_cli_command_available(self):
        """测试工作流 CLI 命令可用"""
        from mc_agent_kit.cli import cmd_workflow
        import argparse

        # 创建测试参数
        args = argparse.Namespace(
            action="cache",
            cache_action="status",
            format="json",
        )

        # 命令应该能执行
        result = cmd_workflow(args)
        assert result == 0

    def test_ux_module_integration(self):
        """测试 UX 模块集成"""
        # 验证 UserExperienceEnhancer 可用
        msg = UserExperienceEnhancer.project_created("/test")
        assert msg is not None
        assert msg.type == MessageType.SUCCESS

    def test_workflow_cache_available(self):
        """测试工作流缓存可用"""
        cache = get_workflow_cache()
        assert cache is not None

        stats = cache.get_stats()
        assert "entries" in stats
        assert "hit_rate" in stats

    def test_all_workflow_steps_have_messages(self):
        """测试所有工作流步骤有对应消息"""
        # 搜索步骤
        search_msg = UserExperienceEnhancer.search_result("test", 1, 1)
        assert search_msg is not None

        # 创建步骤
        create_msg = UserExperienceEnhancer.project_created("/test")
        assert create_msg is not None

        # 诊断步骤
        diag_msg = UserExperienceEnhancer.diagnostic_issue("test", "msg", "suggestion")
        assert diag_msg is not None