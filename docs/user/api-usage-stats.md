# API 使用统计说明

> MC-Agent-Kit 提供了 API 使用统计功能，帮助开发者了解 API 调用情况，识别热门 API 和问题 API。

## 目录

1. [概述](#概述)
2. [CLI 命令](#cli-命令)
3. [Python API](#python-api)
4. [使用场景](#使用场景)

---

## 概述

API 使用统计功能可以：

- 追踪 API 调用次数和成功率
- 识别热门 API（调用次数最多）
- 发现问题 API（错误率高）
- 按模块分组查看统计

---

## CLI 命令

### 查看统计摘要

```bash
mc-agent stats summary
```

输出示例：
```
API 使用统计摘要

==================================================
总 API 数: 25
总调用次数: 1000
成功次数: 950
错误次数: 50
成功率: 95.00%

热门 API (Top 5):
  1. CreateEngineEntity (150 次调用)
  2. GetEngineTime (120 次调用)
  3. SetEntityPos (100 次调用)

问题 API (错误率高):
  - GetPlayerName (错误率: 35.00%)
```

### 获取热门 API

```bash
# 默认显示 Top 10
mc-agent stats hot

# 指定数量
mc-agent stats hot --limit 20
```

### 获取问题 API

```bash
# 默认阈值：最小调用 5 次，错误率 30%
mc-agent stats problems

# 自定义阈值
mc-agent stats problems --min-calls 10 --error-rate 0.5
```

### 按模块查看

```bash
# 查看所有模块概览
mc-agent stats module

# 查看指定模块
mc-agent stats module --module entity
```

### 查看指定 API

```bash
mc-agent stats api --api-name CreateEngineEntity
```

### JSON 格式输出

```bash
mc-agent stats summary --format json
```

---

## Python API

### 基本使用

```python
from mc_agent_kit.stats import ApiUsageTracker

# 创建追踪器
tracker = ApiUsageTracker("data/api_stats.json")

# 记录 API 调用
tracker.record(
    api_name="CreateEngineEntity",
    success=True,
    module="entity",
    scope="server",
    duration_ms=15.5,
)

# 记录失败的调用
tracker.record(
    api_name="GetPlayerName",
    success=False,
    error_message="Player not found",
)

# 保存统计数据
tracker.save()
```

### 获取统计

```python
# 获取指定 API 的统计
stats = tracker.get_stats("CreateEngineEntity")
print(f"调用次数: {stats.total_calls}")
print(f"成功率: {stats.success_rate:.2%}")

# 获取热门 API
hot_apis = tracker.get_hot_apis(limit=10)
for api in hot_apis:
    print(f"{api.api_name}: {api.total_calls} 次调用")

# 获取问题 API
problematic = tracker.get_problematic_apis(
    min_calls=5,
    error_rate_threshold=0.3,
)
for api in problematic:
    print(f"{api.api_name}: 错误率 {api.error_rate:.2%}")

# 按模块分组
by_module = tracker.get_stats_by_module()
for module, apis in by_module.items():
    print(f"{module}: {len(apis)} 个 API")

# 获取摘要
summary = tracker.get_summary()
print(f"总调用次数: {summary['total_calls']}")
```

### 数据模型

#### UsageRecord

```python
@dataclass
class UsageRecord:
    api_name: str           # API 名称
    timestamp: str          # 时间戳
    success: bool           # 是否成功
    error_message: str      # 错误信息
    module: str             # 所属模块
    scope: str              # 作用域
    duration_ms: float      # 调用耗时
```

#### ApiUsageStats

```python
@dataclass
class ApiUsageStats:
    api_name: str           # API 名称
    total_calls: int        # 总调用次数
    success_count: int      # 成功次数
    error_count: int        # 错误次数
    success_rate: float     # 成功率
    error_rate: float       # 错误率
    last_used: str          # 最近使用时间
    avg_duration_ms: float  # 平均耗时
    common_errors: list     # 常见错误
```

---

## 使用场景

### 1. 性能监控

```python
# 在关键 API 调用前后记录
import time

start = time.time()
result = some_api_call()
duration = (time.time() - start) * 1000

tracker.record(
    api_name="some_api_call",
    success=result is not None,
    duration_ms=duration,
)
```

### 2. 错误追踪

```python
try:
    result = risky_api_call()
    tracker.record("risky_api_call", success=True)
except Exception as e:
    tracker.record("risky_api_call", success=False, error_message=str(e))
    raise
```

### 3. 使用分析

```python
# 定期分析 API 使用情况
summary = tracker.get_summary()

# 识别需要优化的 API
for api in tracker.get_problematic_apis():
    print(f"需要关注: {api.api_name}")
    print(f"  错误率: {api.error_rate:.2%}")
    print(f"  常见错误: {api.common_errors}")
```

### 4. 文档改进

```python
# 识别需要更好文档的 API
hot_apis = tracker.get_hot_apis(limit=20)
print("热门 API，建议完善文档：")
for api in hot_apis:
    print(f"  - {api.api_name}")
```

---

## 数据存储

统计数据默认保存在 `data/api_stats.json`，包含：

```json
{
  "stats": {
    "CreateEngineEntity": {
      "api_name": "CreateEngineEntity",
      "total_calls": 100,
      "success_count": 95,
      "error_count": 5,
      "success_rate": 0.95,
      "error_rate": 0.05,
      "common_errors": ["Entity limit reached"],
      "category": "entity"
    }
  },
  "records": [...],
  "module_mapping": {
    "CreateEngineEntity": "entity"
  }
}
```

---

*最后更新: 2026-03-22*