# cli_llm.commands - 命令处理 API

命令处理模块，提供代码生成、审查、诊断、修复命令。

## 函数

### generate_command()

生成代码。

```python
def generate_command(
    prompt: str,
    generation_type: str = "custom",
    target: str = "server",
    context: dict[str, Any] | None = None,
    config: LLMCliConfig | None = None,
    stream: bool = False,
    format: OutputFormat = OutputFormat.TEXT,
) -> dict[str, Any]
```

#### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `prompt` | `str` | - | 需求描述 |
| `generation_type` | `str` | `"custom"` | 生成类型 |
| `target` | `str` | `"server"` | 目标环境 |
| `context` | `dict \| None` | `None` | 上下文 |
| `config` | `LLMCliConfig \| None` | `None` | 配置 |
| `stream` | `bool` | `False` | 是否流式 |
| `format` | `OutputFormat` | `TEXT` | 输出格式 |

#### 返回

```python
{
    "success": bool,           # 是否成功
    "code": str | None,        # 生成的代码
    "raw_response": str,       # 原始响应
    "generation_type": str,    # 生成类型
    "target": str,             # 目标环境
    "error": str | None,       # 错误信息
}
```

#### 生成类型

| 类型 | 说明 |
|------|------|
| `event_listener` | 事件监听器 |
| `entity_behavior` | 实体行为 |
| `item_logic` | 物品逻辑 |
| `ui_screen` | UI 界面 |
| `network_sync` | 网络同步 |
| `config_handler` | 配置处理 |
| `error_handler` | 错误处理 |
| `custom` | 自定义 |

---

### review_command()

审查代码。

```python
def review_command(
    code: str,
    categories: list[str] | None = None,
    min_score: int = 60,
    config: LLMCliConfig | None = None,
    format: OutputFormat = OutputFormat.TEXT,
) -> dict[str, Any]
```

#### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `code` | `str` | - | 待审查代码 |
| `categories` | `list \| None` | `None` | 审查类别 |
| `min_score` | `int` | `60` | 最低分数 |
| `config` | `LLMCliConfig \| None` | `None` | 配置 |
| `format` | `OutputFormat` | `TEXT` | 输出格式 |

#### 返回

```python
{
    "success": bool,           # 是否成功
    "passed": bool,            # 是否通过
    "score": int,              # 分数 (0-100)
    "grade": str,              # 等级 (A-F)
    "issues": list[dict],      # 问题列表
    "summary": str,            # 摘要
    "error": str | None,       # 错误信息
}
```

#### 审查类别

| 类别 | 说明 |
|------|------|
| `security` | 安全审查 |
| `performance` | 性能审查 |
| `modsdk` | ModSDK 规范 |
| `style` | 代码风格 |
| `maintainability` | 可维护性 |

---

### diagnose_command()

诊断错误。

```python
def diagnose_command(
    error_message: str,
    code: str | None = None,
    stack_trace: str | None = None,
    config: LLMCliConfig | None = None,
    format: OutputFormat = OutputFormat.TEXT,
) -> dict[str, Any]
```

#### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `error_message` | `str` | - | 错误消息 |
| `code` | `str \| None` | `None` | 相关代码 |
| `stack_trace` | `str \| None` | `None` | 堆栈跟踪 |
| `config` | `LLMCliConfig \| None` | `None` | 配置 |
| `format` | `OutputFormat` | `TEXT` | 输出格式 |

#### 返回

```python
{
    "success": bool,           # 是否成功
    "error_type": str,         # 错误类型
    "error_message": str,      # 错误消息
    "possible_causes": list,   # 可能原因
    "suggestions": list[dict], # 修复建议
    "related_docs": list,      # 相关文档
    "error": str | None,       # 诊断错误
}
```

---

### fix_command()

修复代码。

```python
def fix_command(
    error_message: str,
    code: str,
    apply: bool = False,
    config: LLMCliConfig | None = None,
    format: OutputFormat = OutputFormat.TEXT,
) -> dict[str, Any]
```

#### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `error_message` | `str` | - | 错误消息 |
| `code` | `str` | - | 待修复代码 |
| `apply` | `bool` | `False` | 是否应用修复 |
| `config` | `LLMCliConfig \| None` | `None` | 配置 |
| `format` | `OutputFormat` | `TEXT` | 输出格式 |

#### 返回

```python
{
    "success": bool,           # 是否成功
    "fixed_code": str | None,  # 修复后的代码
    "original_code": str,      # 原始代码
    "fix_description": str,    # 修复描述
    "confidence": float,       # 置信度
    "error": str | None,       # 错误信息
}
```

## 示例

### 生成代码

```python
from mc_agent_kit.cli_llm import generate_command, OutputFormat

# 生成事件监听器
result = generate_command(
    prompt="创建一个监听玩家加入事件的监听器",
    generation_type="event_listener",
    target="server",
)

if result["success"]:
    print(result["code"])
else:
    print(f"Error: {result['error']}")
```

### 审查代码

```python
from mc_agent_kit.cli_llm import review_command

code = """
def hello():
    print("hello")
"""

result = review_command(
    code=code,
    categories=["security", "performance"],
    min_score=60,
)

print(f"Score: {result['score']}")
print(f"Grade: {result['grade']}")

for issue in result["issues"]:
    print(f"- {issue['severity']}: {issue['message']}")
```

### 诊断错误

```python
from mc_agent_kit.cli_llm import diagnose_command

result = diagnose_command(
    error_message="KeyError: 'speed'",
    code="speed = config['speed']",
)

print(f"Error type: {result['error_type']}")

for cause in result["possible_causes"]:
    print(f"- {cause}")

for suggestion in result["suggestions"]:
    print(f"Fix: {suggestion['description']}")
    print(f"Code: {suggestion['code']}")
```

### 修复代码

```python
from mc_agent_kit.cli_llm import fix_command

result = fix_command(
    error_message="KeyError: 'speed'",
    code="speed = config['speed']",
    apply=False,  # 只生成修复，不应用
)

if result["success"]:
    print("Fixed code:")
    print(result["fixed_code"])
    print(f"Confidence: {result['confidence']}")
```

---

*API 版本: v1.54.0*