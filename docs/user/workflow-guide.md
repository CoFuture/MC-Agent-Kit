# MC-Agent-Kit 工作流使用指南

> 版本: v1.0.0
> 最后更新: 2026-03-23

---

## 概述

MC-Agent-Kit 提供了一套完整的工作流系统，帮助开发者自动化完成 ModSDK 开发流程。工作流系统支持：

- **端到端自动化**: 从查文档到创建项目、启动测试、诊断错误的完整闭环
- **重试机制**: 可配置的重试策略，提高操作成功率
- **进度追踪**: 实时进度回调，了解任务执行状态
- **缓存优化**: 智能缓存减少重复操作

---

## 快速开始

### CLI 使用

```bash
# 运行完整开发周期工作流
mc-agent workflow run -q "创建自定义实体" -n my_entity

# 单独运行搜索步骤
mc-agent workflow search -q "如何创建实体"

# 单独运行创建项目步骤
mc-agent workflow create -n my_addon -o ./output

# 单独运行诊断步骤
mc-agent workflow diagnose --addon-path ./my_addon

# 查看缓存状态
mc-agent workflow cache status

# 清空缓存
mc-agent workflow cache clear
```

### Python API 使用

```python
from mc_agent_kit.workflow import (
    create_workflow,
    WorkflowStep,
    run_development_cycle
)

# 方式一：使用便捷函数
result = run_development_cycle(
    query="如何创建自定义实体",
    project_name="my_entity",
    output_dir="./output"
)

# 方式二：使用工作流管理器
workflow = create_workflow(
    query="如何创建自定义实体",
    project_name="my_entity"
)
result = workflow.run()

# 检查结果
if result.success:
    print(f"工作流完成，耗时 {result.duration:.2f}s")
    for step_result in result.step_results:
        print(f"  - {step_result.step}: {step_result.status}")
else:
    print(f"工作流失败: {result.error}")
```

---

## 工作流步骤

工作流系统包含以下步骤：

| 步骤 | 描述 | 输入 | 输出 |
|------|------|------|------|
| SEARCH | 查询文档 | 查询字符串 | API/事件文档 |
| CREATE | 创建项目 | 项目名称、输出目录 | 项目文件 |
| LAUNCH | 启动测试 | Addon 路径 | 游戏进程 |
| DIAGNOSE | 诊断错误 | 日志内容 | 错误分析 |
| FIX | 修复错误 | 错误信息 | 修复建议 |

### 步骤状态

每个步骤有以下状态：

- `PENDING`: 等待执行
- `RUNNING`: 正在执行
- `SUCCESS`: 执行成功
- `FAILED`: 执行失败
- `SKIPPED`: 跳过执行

---

## 重试机制

工作流支持可配置的重试机制，提高操作成功率。

### 重试配置

```python
from mc_agent_kit.workflow import (
    RetryConfig,
    RetryPolicy,
    create_enhanced_workflow
)

# 配置重试策略
retry_config = RetryConfig(
    max_retries=3,              # 最大重试次数
    retry_delay=1.0,            # 重试延迟（秒）
    retry_policy=RetryPolicy.EXPONENTIAL  # 重试策略
)

# 创建带重试的工作流
workflow = create_enhanced_workflow(
    query="创建实体",
    project_name="my_entity",
    retry_config=retry_config
)
```

### 重试策略

| 策略 | 描述 | 延迟计算 |
|------|------|----------|
| `NONE` | 不重试 | N/A |
| `LINEAR` | 线性延迟 | delay * retry_count |
| `EXPONENTIAL` | 指数延迟 | delay * (2 ** retry_count) |

### CLI 重试选项

```bash
# 使用指数退避重试，最多 5 次
mc-agent workflow run -q "查询" --retry 5 --retry-policy exponential

# 使用线性延迟重试
mc-agent workflow run -q "查询" --retry 3 --retry-policy linear
```

---

## 进度追踪

工作流支持实时进度回调，帮助追踪任务执行状态。

### 进度信息

```python
from mc_agent_kit.workflow import EnhancedWorkflow, ProgressInfo

def on_progress(info: ProgressInfo):
    """进度回调函数"""
    print(f"进度: {info.completed_steps}/{info.total_steps}")
    print(f"百分比: {info.percentage:.1f}%")
    print(f"当前步骤: {info.current_step}")
    if info.estimated_remaining:
        print(f"预计剩余时间: {info.estimated_remaining:.1f}s")

workflow = EnhancedWorkflow()
workflow.set_progress_callback(on_progress)
workflow.run()
```

### 进度信息字段

| 字段 | 类型 | 描述 |
|------|------|------|
| `completed_steps` | int | 已完成步骤数 |
| `total_steps` | int | 总步骤数 |
| `percentage` | float | 完成百分比 |
| `current_step` | str | 当前步骤名称 |
| `estimated_remaining` | float | 预计剩余时间（秒） |

### CLI 进度显示

```bash
# 启用进度显示
mc-agent workflow run -q "查询" --progress

# 输出示例
# [1/5] SEARCH 正在查询文档...
# [2/5] CREATE 正在创建项目...
# [3/5] LAUNCH 正在启动测试...
```

---

## 工作流控制

工作流支持暂停、恢复、取消等控制操作。

### 暂停与恢复

```python
from mc_agent_kit.workflow import WorkflowControl, WorkflowState

control = WorkflowControl()

# 暂停工作流
control.pause()
print(f"状态: {control.state}")  # PAUSED

# 恢复工作流
control.resume()
print(f"状态: {control.state}")  # RUNNING

# 取消工作流
control.cancel()
print(f"状态: {control.state}")  # CANCELLED
```

### 状态检查

```python
# 检查工作流状态
if control.is_paused():
    print("工作流已暂停")

if control.is_cancelled():
    print("工作流已取消")

if control.is_running():
    print("工作流正在运行")
```

---

## 缓存系统

工作流使用智能缓存减少重复操作，提升性能。

### 缓存类型

1. **知识库索引缓存**: 缓存解析后的知识库索引
2. **搜索结果缓存**: 缓存 API/事件搜索结果
3. **模板缓存**: 缓存代码生成模板

### 缓存配置

```python
from mc_agent_kit.workflow import (
    EnhancedCache,
    CacheMetrics
)

# 创建增强缓存
cache = EnhancedCache(
    max_size=1000,      # 最大缓存条目数
    ttl_seconds=3600    # 缓存过期时间（秒）
)

# 获取缓存指标
metrics: CacheMetrics = cache.get_metrics()
print(f"命中率: {metrics.hit_rate:.1%}")
print(f"总请求: {metrics.total_requests}")
print(f"命中次数: {metrics.hits}")
```

### 缓存预热

```python
from mc_agent_kit.workflow import WarmupConfig

# 配置缓存预热
warmup_config = WarmupConfig(
    enabled=True,
    warmup_on_startup=True,
    warmup_keys=["common_api", "common_events"]
)

cache.configure_warmup(warmup_config)
cache.warmup()
```

### 批量操作

```python
# 批量设置缓存
cache.set_batch({
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
})

# 批量获取缓存
values = cache.get_batch(["key1", "key2", "key3"])

# 按标签失效
cache.invalidate_by_tag("search_results")
```

### CLI 缓存命令

```bash
# 查看缓存状态
mc-agent workflow cache status
# 输出:
# 缓存状态: 活跃
# 条目数量: 150
# 命中率: 75.3%
# 内存使用: 2.5 MB

# 清空缓存
mc-agent workflow cache clear
# 输出:
# 缓存已清空
```

---

## 本地化支持

工作流系统支持多语言消息输出。

### 支持的语言

| 语言 | 代码 | 状态 |
|------|------|------|
| 中文 | zh | ✅ 支持 |
| 英文 | en | ✅ 支持 |
| 日语 | ja | 🔜 计划中 |
| 韩语 | ko | 🔜 计划中 |

### 使用本地化

```python
from mc_agent_kit.ux import LocaleManager, get_ux_manager

# 获取本地化管理器
locale_manager = LocaleManager()
locale_manager.set_locale("en")  # 设置为英文

# 获取本地化消息
msg = locale_manager.get_message("workflow.started")
print(msg)  # "Workflow started"

# 切换语言
locale_manager.set_locale("zh")
msg = locale_manager.get_message("workflow.started")
print(msg)  # "工作流已启动"
```

### CLI 本地化选项

```bash
# 使用英文输出
mc-agent workflow run -q "query" --locale en

# 使用中文输出
mc-agent workflow run -q "查询" --locale zh
```

---

## 消息模板

工作流系统提供预定义的消息模板，确保消息格式一致。

### 内置模板

| 模板名称 | 描述 | 中文示例 |
|----------|------|----------|
| `workflow_started` | 工作流启动 | 工作流已启动 |
| `workflow_completed` | 工作流完成 | 工作流完成，耗时 5.2s |
| `workflow_paused` | 工作流暂停 | 工作流已暂停 |
| `workflow_resumed` | 工作流恢复 | 工作流已恢复 |
| `workflow_cancelled` | 工作流取消 | 工作流已取消 |
| `cache_status` | 缓存状态 | 缓存条目: 150, 命中率: 75% |
| `progress_update` | 进度更新 | 进度: 3/5 (60%) |
| `retry_attempt` | 重试尝试 | 第 2 次重试... |
| `step_skipped` | 步骤跳过 | 步骤 DIAGNOSE 已跳过 |

### 使用模板

```python
from mc_agent_kit.ux import TemplateRegistry, get_ux_manager

# 获取模板注册表
registry = TemplateRegistry()

# 获取模板
template = registry.get("workflow_completed")
msg = template.render(duration=5.2, steps_completed=5)
print(msg)  # "工作流完成，耗时 5.2s，完成 5 个步骤"

# 使用 UX 管理器
ux = get_ux_manager()
ux.send_workflow_started()
ux.send_progress_update(completed=3, total=5)
ux.send_workflow_completed(duration=5.2)
```

---

## 最佳实践

### 1. 合理配置重试

- 对于网络请求操作，使用指数退避重试
- 对于本地文件操作，使用线性延迟重试
- 重试次数不宜过多，建议 3-5 次

```python
# 推荐：网络请求使用指数退避
retry_config = RetryConfig(
    max_retries=5,
    retry_delay=1.0,
    retry_policy=RetryPolicy.EXPONENTIAL
)

# 推荐：文件操作使用线性延迟
retry_config = RetryConfig(
    max_retries=3,
    retry_delay=0.5,
    retry_policy=RetryPolicy.LINEAR
)
```

### 2. 使用缓存提升性能

- 启用缓存预热减少冷启动时间
- 定期检查缓存命中率，优化缓存策略
- 使用标签管理缓存失效

```python
# 推荐：启用缓存预热
cache = EnhancedCache(max_size=1000, ttl_seconds=3600)
cache.configure_warmup(WarmupConfig(enabled=True))
cache.warmup()

# 定期检查命中率
metrics = cache.get_metrics()
if metrics.hit_rate < 0.5:
    print("缓存命中率较低，考虑增加缓存大小或 TTL")
```

### 3. 进度回调最佳实践

- 避免在回调中执行耗时操作
- 使用回调更新 UI 或日志
- 注意线程安全

```python
# 推荐：简洁的进度回调
def on_progress(info: ProgressInfo):
    # 仅更新状态，不执行耗时操作
    update_progress_bar(info.percentage)

# 不推荐：在回调中执行耗时操作
def bad_progress(info: ProgressInfo):
    time.sleep(1)  # 不要这样做
    send_email_notification(info)  # 不要这样做
```

### 4. 工作流控制

- 在长时间运行的工作流中提供暂停/恢复功能
- 实现优雅取消，避免资源泄漏
- 记录工作流状态便于恢复

```python
# 推荐：实现优雅取消
workflow = EnhancedWorkflow()
control = WorkflowControl()

try:
    result = workflow.run()
except KeyboardInterrupt:
    control.cancel()
    workflow.cleanup()  # 清理资源
```

---

## 性能调优

### 缓存优化

| 指标 | 推荐值 | 说明 |
|------|--------|------|
| 缓存大小 | 500-2000 | 根据内存限制调整 |
| TTL | 1800-7200 秒 | 根据数据更新频率调整 |
| 命中率目标 | > 50% | 低于此值考虑优化 |

### 性能基准

| 操作 | 目标时间 | 说明 |
|------|----------|------|
| 索引构建（缓存命中） | < 3s | 从缓存加载知识库索引 |
| 搜索响应（缓存命中） | < 100ms | API/事件搜索 |
| CLI 启动 | < 200ms | 懒加载模块 |
| 工作流完整执行 | < 30s | 完整开发周期 |

---

## 故障排除

### 常见问题

#### 1. 缓存命中率低

**原因**: 缓存大小不足或 TTL 过短

**解决方案**:
```python
# 增加缓存大小
cache = EnhancedCache(max_size=2000)

# 延长 TTL
cache = EnhancedCache(ttl_seconds=7200)
```

#### 2. 工作流执行超时

**原因**: 单个步骤耗时过长

**解决方案**:
```python
# 配置步骤超时
workflow = EnhancedWorkflow()
workflow.set_step_timeout(WorkflowStep.SEARCH, 30)  # 30 秒超时
```

#### 3. 重试过多导致延迟

**原因**: 重试策略配置不当

**解决方案**:
```python
# 减少重试次数，使用指数退避
retry_config = RetryConfig(
    max_retries=3,
    retry_policy=RetryPolicy.EXPONENTIAL
)
```

---

## API 参考

### 主要类

| 类名 | 模块 | 描述 |
|------|------|------|
| `EnhancedWorkflow` | workflow.enhanced | 增强工作流管理器 |
| `WorkflowControl` | workflow.enhanced | 工作流控制器 |
| `RetryConfig` | workflow.enhanced | 重试配置 |
| `ProgressInfo` | workflow.enhanced | 进度信息 |
| `EnhancedCache` | workflow.cache_enhanced | 增强缓存管理器 |
| `LocaleManager` | ux.enhanced | 本地化管理器 |
| `TemplateRegistry` | ux.enhanced | 模板注册表 |

### 便捷函数

| 函数 | 描述 |
|------|------|
| `create_workflow()` | 创建基础工作流 |
| `create_enhanced_workflow()` | 创建增强工作流 |
| `run_development_cycle()` | 运行开发周期 |
| `get_enhanced_cache()` | 获取全局缓存实例 |
| `get_ux_manager()` | 获取 UX 管理器 |

---

*文档版本: v1.0.0*
*最后更新: 2026-03-23*