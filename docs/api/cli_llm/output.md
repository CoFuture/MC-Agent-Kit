# cli_llm.output - 输出格式化 API

输出格式化模块，提供代码和审查结果的格式化功能。

## 枚举

### OutputFormat

输出格式枚举。

```python
class OutputFormat(Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    ANSI = "ansi"
```

## 类

### StreamChunk

流式输出块。

```python
@dataclass
class StreamChunk:
    content: str
    is_final: bool = False
    metadata: dict[str, Any] | None = None
```

#### 属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `content` | `str` | - | 内容 |
| `is_final` | `bool` | `False` | 是否最后一块 |
| `metadata` | `dict \| None` | `None` | 元数据 |

---

### CodeFormatter

代码格式化器。

```python
class CodeFormatter:
    def __init__(
        self,
        format: OutputFormat = OutputFormat.TEXT,
        use_colors: bool = True,
    )
```

#### 方法

##### format_code()

格式化代码。

```python
def format_code(
    self,
    code: str,
    language: str = "python",
    filename: str | None = None,
) -> str
```

**参数**:
- `code`: 代码内容
- `language`: 编程语言
- `filename`: 文件名（可选）

**返回**: `str` - 格式化后的代码

##### format_imports()

格式化导入语句。

```python
def format_imports(self, imports: list[str]) -> str
```

**参数**:
- `imports`: 导入语句列表

**返回**: `str` - 格式化后的导入

##### format_dependencies()

格式化依赖。

```python
def format_dependencies(self, dependencies: list[str]) -> str
```

**参数**:
- `dependencies`: 依赖列表

**返回**: `str` - 格式化后的依赖

##### format_notes()

格式化注释。

```python
def format_notes(self, notes: list[str]) -> str
```

**参数**:
- `notes`: 注释列表

**返回**: `str` - 格式化后的注释

##### format_warnings()

格式化警告。

```python
def format_warnings(self, warnings: list[str]) -> str
```

**参数**:
- `warnings`: 警告列表

**返回**: `str` - 格式化后的警告

---

### StreamOutput

流式输出处理器。

```python
class StreamOutput:
    def __init__(
        self,
        file: Any = None,
        use_colors: bool = True,
        prefix: str = "",
    )
```

#### 方法

##### write()

写入块。

```python
def write(self, chunk: StreamChunk) -> None
```

**参数**:
- `chunk`: 流式块

##### write_line()

写入一行。

```python
def write_line(self, text: str = "") -> None
```

**参数**:
- `text`: 行内容

##### write_styled()

写入样式文本。

```python
def write_styled(
    self,
    text: str,
    color: str = "white",
    bold: bool = False,
) -> None
```

**参数**:
- `text`: 文本内容
- `color`: 颜色名称
- `bold`: 是否加粗

##### clear_line()

清除当前行。

```python
def clear_line(self) -> None
```

##### update_line()

更新当前行。

```python
def update_line(self, text: str) -> None
```

**参数**:
- `text`: 新内容

##### get_buffer()

获取缓冲区内容。

```python
def get_buffer(self) -> str
```

**返回**: `str` - 缓冲区内容

##### reset_buffer()

重置缓冲区。

```python
def reset_buffer(self) -> None
```

---

## 函数

### format_code_result()

格式化代码生成结果。

```python
def format_code_result(
    result: dict[str, Any],
    format: OutputFormat = OutputFormat.TEXT,
    use_colors: bool = True,
) -> str
```

**参数**:
- `result`: 生成结果字典
- `format`: 输出格式
- `use_colors`: 是否使用颜色

**返回**: `str` - 格式化后的结果

#### 结果字典结构

```python
{
    "success": bool,           # 是否成功
    "code": str,               # 生成的代码
    "imports": list[str],      # 导入语句
    "dependencies": list[str], # 依赖
    "notes": list[str],        # 注释
    "warnings": list[str],     # 警告
    "confidence": float,       # 置信度
}
```

### format_review_result()

格式化代码审查结果。

```python
def format_review_result(
    result: dict[str, Any],
    format: OutputFormat = OutputFormat.TEXT,
    use_colors: bool = True,
) -> str
```

**参数**:
- `result`: 审查结果字典
- `format`: 输出格式
- `use_colors`: 是否使用颜色

**返回**: `str` - 格式化后的结果

#### 结果字典结构

```python
{
    "passed": bool,        # 是否通过
    "score": int,          # 分数 (0-100)
    "grade": str,          # 等级 (A-F)
    "issues": list[dict],  # 问题列表
    "summary": str,        # 摘要
}
```

### create_code_formatter()

创建代码格式化器。

```python
def create_code_formatter(
    format: OutputFormat = OutputFormat.TEXT,
    use_colors: bool = True,
) -> CodeFormatter
```

**参数**:
- `format`: 输出格式
- `use_colors`: 是否使用颜色

**返回**: `CodeFormatter` - 格式化器实例

### create_stream_output()

创建流式输出处理器。

```python
def create_stream_output(
    file: Any = None,
    use_colors: bool = True,
    prefix: str = "",
) -> StreamOutput
```

**参数**:
- `file`: 输出文件
- `use_colors`: 是否使用颜色
- `prefix`: 行前缀

**返回**: `StreamOutput` - 流式输出实例

## 示例

### 格式化代码

```python
from mc_agent_kit.cli_llm import CodeFormatter, OutputFormat

# 创建格式化器
formatter = CodeFormatter(OutputFormat.MARKDOWN)

# 格式化代码
result = formatter.format_code(
    code="def hello(): print('hello')",
    language="python",
    filename="main.py"
)

print(result)
```

### 流式输出

```python
from mc_agent_kit.cli_llm import StreamOutput, StreamChunk

# 创建流式输出
stream = StreamOutput(use_colors=True)

# 写入内容
stream.write_line("Starting...")
for i in range(5):
    stream.update_line(f"Progress: {i+1}/5")

stream.write_line("Done!")
```

### 格式化生成结果

```python
from mc_agent_kit.cli_llm import format_code_result, OutputFormat

result = {
    "success": True,
    "code": "def hello(): pass",
    "imports": ["from mod.server import serverApi"],
    "confidence": 0.85,
}

# 格式化为 Markdown
output = format_code_result(result, OutputFormat.MARKDOWN)
print(output)
```

### 格式化审查结果

```python
from mc_agent_kit.cli_llm import format_review_result, OutputFormat

result = {
    "passed": True,
    "score": 85,
    "grade": "B",
    "issues": [
        {"severity": "warning", "message": "Missing docstring", "line": 10}
    ],
    "summary": "Good code quality",
}

# 格式化为文本
output = format_review_result(result, OutputFormat.TEXT)
print(output)
```

---

*API 版本: v1.54.0*