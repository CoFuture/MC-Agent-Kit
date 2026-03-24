# MC-Agent-Kit API 文档

本目录包含 MC-Agent-Kit 的详细 API 参考。

## 模块索引

### CLI LLM 模块

- [config](./cli_llm/config.md) - 配置管理 API
- [output](./cli_llm/output.md) - 输出格式化 API
- [chat](./cli_llm/chat.md) - 聊天会话 API
- [commands](./cli_llm/commands.md) - 命令处理 API

### LLM 模块

- [base](./llm/base.md) - LLM 基础接口
- [providers](./llm/providers.md) - LLM 提供商实现
- [manager](./llm/manager.md) - LLM 管理器
- [code_generation](./llm/code_generation.md) - 代码生成
- [code_review](./llm/code_review.md) - 代码审查
- [intelligent_fix](./llm/intelligent_fix.md) - 智能修复

### 其他模块

- [knowledge_base](./knowledge_base.md) - 知识库 API
- [launcher](./launcher.md) - 游戏启动器 API
- [scaffold](./scaffold.md) - 项目脚手架 API

## 快速开始

### 配置管理

```python
from mc_agent_kit.cli_llm import (
    LLMCliConfig,
    LLMCliConfigManager,
    load_llm_cli_config,
)

# 加载配置
config = load_llm_cli_config()

# 或使用管理器
manager = LLMCliConfigManager()
config = manager.load()

# 访问配置
print(config.default_provider)
print(config.providers['openai'].model)
```

### 聊天会话

```python
from mc_agent_kit.cli_llm import (
    ChatSession,
    ChatSessionConfig,
    create_chat_session,
)

# 创建会话
session = create_chat_session()

# 发送消息
response = session.send("如何创建实体？")
print(response)

# 流式输出
for chunk in session.send("生成代码", stream=True):
    print(chunk, end="")
```

### 代码生成

```python
from mc_agent_kit.cli_llm import generate_command

result = generate_command(
    prompt="创建一个监听玩家加入事件的监听器",
    generation_type="event_listener",
    target="server",
)

if result['success']:
    print(result['code'])
```

### 代码审查

```python
from mc_agent_kit.cli_llm import review_command

result = review_command(
    code="def hello(): print('hello')",
    categories=["security", "performance"],
    min_score=60,
)

print(f"Score: {result['score']}")
print(f"Grade: {result['grade']}")
for issue in result['issues']:
    print(f"- {issue['message']}")
```

### 错误诊断

```python
from mc_agent_kit.cli_llm import diagnose_command, fix_command

# 诊断错误
diagnosis = diagnose_command(
    error_message="KeyError: 'speed'",
    code="speed = config['speed']",
)

for suggestion in diagnosis['suggestions']:
    print(f"Fix: {suggestion['description']}")

# 自动修复
fix = fix_command(
    error_message="KeyError: 'speed'",
    code="speed = config['speed']",
    apply=False,  # 只生成修复，不应用
)

print(fix['fixed_code'])
```

## 版本信息

- API 版本: v1.54.0
- Python 版本: 3.13+
- 最后更新: 2026-03-25

---

*详细 API 文档请查看各模块页面*