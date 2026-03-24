# 配置文件详解

本指南详细介绍 MC-Agent-Kit 的配置选项和最佳实践。

## 配置文件位置

默认配置文件路径：`~/.mc-agent-kit/config.yaml`

也可通过环境变量指定：

```bash
export MC_AGENT_KIT_CONFIG_PATH="/path/to/config.yaml"
```

## 配置文件格式

支持 YAML 和 JSON 两种格式：

### YAML 格式（推荐）

```yaml
# ~/.mc-agent-kit/config.yaml

# 默认 LLM 提供商
default_provider: mock

# 流式输出
stream_output: true

# 详细输出
verbose: false

# 提供商配置
providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4o
    temperature: 0.7
    max_tokens: 4096
  
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-sonnet-4-20250514
    temperature: 0.7
  
  gemini:
    api_key: ${GEMINI_API_KEY}
    model: gemini-1.5-pro
  
  ollama:
    base_url: http://localhost:11434
    model: llama3

# 代码生成配置
code_generation:
  default_type: custom
  default_target: server
  style: pep8
  include_docstrings: true
  include_type_hints: true

# 代码审查配置
code_review:
  min_score: 60
  categories:
    - security
    - performance
    - modsdk
  max_suggestions: 10

# 历史记录配置
history_file: ~/.mc-agent-kit/chat_history.json
max_history_entries: 100
```

### JSON 格式

```json
{
  "default_provider": "mock",
  "stream_output": true,
  "verbose": false,
  "providers": {
    "openai": {
      "api_key": "${OPENAI_API_KEY}",
      "model": "gpt-4o",
      "temperature": 0.7
    }
  },
  "code_generation": {
    "default_type": "custom",
    "default_target": "server",
    "style": "pep8"
  },
  "code_review": {
    "min_score": 60,
    "categories": ["security", "performance", "modsdk"]
  }
}
```

## 配置项详解

### 全局配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `default_provider` | string | `mock` | 默认 LLM 提供商 |
| `stream_output` | bool | `true` | 是否启用流式输出 |
| `verbose` | bool | `false` | 是否显示详细信息 |
| `history_file` | string | `~/.mc-agent-kit/chat_history.json` | 聊天历史文件路径 |
| `max_history_entries` | int | `100` | 最大历史记录条数 |

### 提供商配置 (`providers`)

每个提供商支持以下配置：

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `api_key` | string | API 密钥（推荐使用环境变量） |
| `model` | string | 模型名称 |
| `base_url` | string | API 地址（Ollama 等） |
| `temperature` | float | 温度参数（0-1） |
| `max_tokens` | int | 最大 Token 数 |

### 代码生成配置 (`code_generation`)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `default_type` | string | `custom` | 默认生成类型 |
| `default_target` | string | `server` | 默认目标环境 |
| `style` | string | `pep8` | 代码风格 |
| `include_docstrings` | bool | `true` | 包含文档字符串 |
| `include_type_hints` | bool | `true` | 包含类型注解 |

### 代码审查配置 (`code_review`)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `min_score` | int | `60` | 最低通过分数 |
| `categories` | list | `["security", "performance", "modsdk"]` | 审查类别 |
| `max_suggestions` | int | `10` | 最大建议数量 |

## 环境变量

MC-Agent-Kit 支持通过环境变量配置：

| 环境变量 | 说明 |
|----------|------|
| `MC_AGENT_KIT_CONFIG_PATH` | 配置文件路径 |
| `MC_AGENT_KIT_LLM_PROVIDER` | 默认提供商 |
| `MC_AGENT_KIT_STREAM_OUTPUT` | 流式输出 |
| `MC_AGENT_KIT_VERBOSE` | 详细输出 |
| `OPENAI_API_KEY` | OpenAI API Key |
| `ANTHROPIC_API_KEY` | Anthropic API Key |
| `GEMINI_API_KEY` | Gemini API Key |
| `OLLAMA_BASE_URL` | Ollama 服务地址 |

## 安全最佳实践

### 1. 使用环境变量存储密钥

```yaml
# ✅ 推荐
providers:
  openai:
    api_key: ${OPENAI_API_KEY}

# ❌ 不推荐
providers:
  openai:
    api_key: sk-your-actual-key-here
```

### 2. 配置文件权限

```bash
# 设置配置文件权限（仅所有者可读写）
chmod 600 ~/.mc-agent-kit/config.yaml
```

### 3. 不要提交敏感配置

```gitignore
# .gitignore
.mc-agent-kit/
*.yaml
```

## 配置验证

验证配置是否正确：

```bash
# 列出可用提供商
mc-llm providers

# 测试配置
mc-llm chat --test
```

## 下一步

- 🌍 [环境变量配置](./environment.md) - 使用环境变量
- 🔄 [多环境配置](./multi-environment.md) - 管理多个环境
- 💡 [最佳实践](../best-practices.md) - 开发建议

---

*最后更新: 2026-03-25*