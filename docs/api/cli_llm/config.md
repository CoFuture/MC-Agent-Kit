# cli_llm.config - 配置管理 API

配置管理模块，提供 LLM CLI 的配置文件和环境变量支持。

## 类

### ProviderConfig

提供商配置数据类。

```python
@dataclass
class ProviderConfig:
    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
```

#### 属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | `str \| None` | `None` | API 密钥 |
| `model` | `str \| None` | `None` | 模型名称 |
| `base_url` | `str \| None` | `None` | API 基础 URL |
| `temperature` | `float` | `0.7` | 温度参数 |
| `max_tokens` | `int` | `4096` | 最大 Token 数 |

#### 方法

##### to_dict()

转换为字典。

```python
def to_dict(self) -> dict[str, Any]
```

**返回**: `dict[str, Any]` - 配置字典

##### from_dict()

从字典创建。

```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> "ProviderConfig"
```

**参数**:
- `data`: 配置字典

**返回**: `ProviderConfig` - 配置实例

---

### CodeGenerationConfig

代码生成配置数据类。

```python
@dataclass
class CodeGenerationConfig:
    default_type: str = "custom"
    default_target: str = "server"
    style: str = "pep8"
    include_docstrings: bool = True
    include_type_hints: bool = True
```

#### 属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `default_type` | `str` | `"custom"` | 默认生成类型 |
| `default_target` | `str` | `"server"` | 默认目标环境 |
| `style` | `str` | `"pep8"` | 代码风格 |
| `include_docstrings` | `bool` | `True` | 包含文档字符串 |
| `include_type_hints` | `bool` | `True` | 包含类型注解 |

---

### CodeReviewConfig

代码审查配置数据类。

```python
@dataclass
class CodeReviewConfig:
    min_score: int = 60
    categories: list[str] = field(
        default_factory=lambda: ["security", "performance", "modsdk"]
    )
    max_suggestions: int = 10
```

#### 属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `min_score` | `int` | `60` | 最低通过分数 |
| `categories` | `list[str]` | `["security", "performance", "modsdk"]` | 审查类别 |
| `max_suggestions` | `int` | `10` | 最大建议数量 |

---

### LLMCliConfig

完整的 LLM CLI 配置。

```python
@dataclass
class LLMCliConfig:
    default_provider: str = "mock"
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    code_generation: CodeGenerationConfig = field(default_factory=CodeGenerationConfig)
    code_review: CodeReviewConfig = field(default_factory=CodeReviewConfig)
    history_file: str = "~/.mc-agent-kit/chat_history.json"
    max_history_entries: int = 100
    stream_output: bool = True
    verbose: bool = False
```

#### 属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `default_provider` | `str` | `"mock"` | 默认提供商 |
| `providers` | `dict[str, ProviderConfig]` | `{}` | 提供商配置 |
| `code_generation` | `CodeGenerationConfig` | - | 代码生成配置 |
| `code_review` | `CodeReviewConfig` | - | 代码审查配置 |
| `history_file` | `str` | `"~/.mc-agent-kit/chat_history.json"` | 历史文件路径 |
| `max_history_entries` | `int` | `100` | 最大历史条目 |
| `stream_output` | `bool` | `True` | 流式输出 |
| `verbose` | `bool` | `False` | 详细输出 |

#### 方法

##### get_provider_config()

获取指定提供商的配置。

```python
def get_provider_config(self, provider: str) -> ProviderConfig
```

**参数**:
- `provider`: 提供商名称

**返回**: `ProviderConfig` - 提供商配置

---

### LLMCliConfigManager

配置管理器类。

```python
class LLMCliConfigManager:
    DEFAULT_CONFIG_PATH = "~/.mc-agent-kit/config.yaml"
    ENV_PREFIX = "MC_AGENT_KIT_"
```

#### 方法

##### __init__()

初始化配置管理器。

```python
def __init__(self, config_path: str | None = None)
```

**参数**:
- `config_path`: 配置文件路径（可选）

##### load()

从文件和环境变量加载配置。

```python
def load(self) -> LLMCliConfig
```

**返回**: `LLMCliConfig` - 加载的配置

##### save()

保存配置到文件。

```python
def save(self, config: LLMCliConfig) -> None
```

**参数**:
- `config`: 要保存的配置

##### get()

获取当前配置。

```python
def get(self) -> LLMCliConfig
```

**返回**: `LLMCliConfig` - 当前配置

##### set_provider()

设置提供商配置。

```python
def set_provider(self, provider: str, config: ProviderConfig) -> None
```

**参数**:
- `provider`: 提供商名称
- `config`: 提供商配置

##### set_default_provider()

设置默认提供商。

```python
def set_default_provider(self, provider: str) -> None
```

**参数**:
- `provider`: 提供商名称

---

## 函数

### create_llm_cli_config()

创建默认配置。

```python
def create_llm_cli_config() -> LLMCliConfig
```

**返回**: `LLMCliConfig` - 默认配置实例

### load_llm_cli_config()

加载配置。

```python
def load_llm_cli_config(config_path: str | None = None) -> LLMCliConfig
```

**参数**:
- `config_path`: 配置文件路径（可选）

**返回**: `LLMCliConfig` - 加载的配置

## 环境变量

| 变量名 | 说明 |
|--------|------|
| `MC_AGENT_KIT_CONFIG_PATH` | 配置文件路径 |
| `MC_AGENT_KIT_LLM_PROVIDER` | 默认提供商 |
| `MC_AGENT_KIT_STREAM_OUTPUT` | 流式输出 |
| `MC_AGENT_KIT_VERBOSE` | 详细输出 |
| `OPENAI_API_KEY` | OpenAI API Key |
| `ANTHROPIC_API_KEY` | Anthropic API Key |
| `GEMINI_API_KEY` | Gemini API Key |
| `OLLAMA_BASE_URL` | Ollama 服务地址 |

## 示例

### 加载配置

```python
from mc_agent_kit.cli_llm import load_llm_cli_config

# 从默认路径加载
config = load_llm_cli_config()

# 从指定路径加载
config = load_llm_cli_config("/path/to/config.yaml")
```

### 使用管理器

```python
from mc_agent_kit.cli_llm import LLMCliConfigManager, ProviderConfig

manager = LLMCliConfigManager()

# 加载配置
config = manager.load()

# 修改配置
config.stream_output = False

# 添加提供商
manager.set_provider("openai", ProviderConfig(
    api_key="your-key",
    model="gpt-4o",
))

# 设置默认提供商
manager.set_default_provider("openai")

# 保存配置
manager.save(config)
```

---

*API 版本: v1.54.0*