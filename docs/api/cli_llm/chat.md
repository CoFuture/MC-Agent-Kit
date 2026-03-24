# cli_llm.chat - 聊天会话 API

聊天会话模块，提供交互式聊天功能。

## 类

### SessionMessage

会话消息数据类。

```python
@dataclass
class SessionMessage:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
```

#### 属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `role` | `str` | - | 角色（user/assistant/system） |
| `content` | `str` | - | 消息内容 |
| `timestamp` | `datetime` | `datetime.now()` | 时间戳 |
| `metadata` | `dict` | `{}` | 元数据 |

#### 方法

##### to_dict()

转换为字典。

```python
def to_dict(self) -> dict[str, Any]
```

**返回**: `dict` - 消息字典

##### from_dict()

从字典创建。

```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> "SessionMessage"
```

**参数**:
- `data`: 消息字典

**返回**: `SessionMessage` - 消息实例

##### to_llm_message()

转换为 LLM 消息格式。

```python
def to_llm_message(self) -> ChatMessage
```

**返回**: `ChatMessage` - LLM 消息

---

### ChatSessionConfig

会话配置数据类。

```python
@dataclass
class ChatSessionConfig:
    max_history: int = 100
    system_prompt: str = ""
    context_window: int = 10
    save_history: bool = True
    history_file: str = ""
```

#### 属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_history` | `int` | `100` | 最大历史条目 |
| `system_prompt` | `str` | `""` | 系统提示 |
| `context_window` | `int` | `10` | 上下文窗口大小 |
| `save_history` | `bool` | `True` | 是否保存历史 |
| `history_file` | `str` | `""` | 历史文件路径 |

---

### ChatSession

聊天会话类。

```python
class ChatSession:
    DEFAULT_SYSTEM_PROMPT = """你是 MC-Agent-Kit 的 AI 助手..."""
    
    def __init__(
        self,
        config: LLMCliConfig,
        session_config: ChatSessionConfig | None = None,
    )
```

#### 方法

##### initialize()

初始化会话。

```python
def initialize(self) -> None
```

##### send()

发送消息并获取响应。

```python
def send(
    self,
    message: str,
    stream: bool = False,
) -> Iterator[str] | str
```

**参数**:
- `message`: 用户消息
- `stream`: 是否流式输出

**返回**: `str` 或 `Iterator[str]` - 响应

##### clear_history()

清除历史。

```python
def clear_history(self) -> None
```

##### get_history()

获取历史记录。

```python
def get_history(self) -> list[SessionMessage]
```

**返回**: `list[SessionMessage]` - 消息列表

##### set_system_prompt()

设置系统提示。

```python
def set_system_prompt(self, prompt: str) -> None
```

**参数**:
- `prompt`: 系统提示

---

## 函数

### create_chat_session()

创建聊天会话。

```python
def create_chat_session(
    config: LLMCliConfig | None = None,
    session_config: ChatSessionConfig | None = None,
) -> ChatSession
```

**参数**:
- `config`: LLM CLI 配置（可选）
- `session_config`: 会话配置（可选）

**返回**: `ChatSession` - 会话实例

### chat_interactive()

运行交互式聊天。

```python
def chat_interactive(
    session: ChatSession,
    prompt: str = "mc-llm> ",
    welcome: str | None = None,
) -> None
```

**参数**:
- `session`: 聊天会话
- `prompt`: 输入提示符
- `welcome`: 欢迎消息（可选）

## 示例

### 创建会话

```python
from mc_agent_kit.cli_llm import (
    ChatSession,
    ChatSessionConfig,
    create_chat_session,
)

# 使用默认配置创建
session = create_chat_session()

# 使用自定义配置创建
session_config = ChatSessionConfig(
    max_history=50,
    context_window=5,
    system_prompt="你是一个 ModSDK 专家",
)
session = create_chat_session(session_config=session_config)
```

### 发送消息

```python
# 非流式
response = session.send("如何创建实体？")
print(response)

# 流式
for chunk in session.send("生成代码", stream=True):
    print(chunk, end="", flush=True)
```

### 管理历史

```python
# 获取历史
history = session.get_history()
for msg in history:
    print(f"{msg.role}: {msg.content}")

# 清除历史
session.clear_history()
```

### 交互式聊天

```python
from mc_agent_kit.cli_llm import chat_interactive

# 运行交互式聊天
chat_interactive(
    session,
    prompt="mc> ",
    welcome="欢迎使用 MC-Agent-Kit!"
)
```

---

*API 版本: v1.54.0*