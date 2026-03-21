# 配置指南

本指南说明如何配置 MC-Agent-Kit 以适应您的开发环境。

## 配置文件

MC-Agent-Kit 支持通过配置文件自定义行为。

### 配置文件位置

配置文件按以下顺序查找（优先级从高到低）：

1. `./mc-agent-kit.yaml` - 当前目录
2 `./mc-agent-kit.json` - 当前目录
3. `~/.mc-agent-kit.yaml` - 用户目录
4. `~/.mc-agent-kit.json` - 用户目录

### 配置文件格式

#### YAML 格式

```yaml
# mc-agent-kit.yaml
knowledge_base:
  data_dir: ./data
  auto_load: true
  
launcher:
  game_path: "C:/Games/Minecraft"
  log_port: 9000
  
log_capture:
  buffer_size: 1000
  auto_flush: true
  
generation:
  template_dir: ./templates
  output_dir: ./output
  
cli:
  output_format: text
  color_output: true
```

#### JSON 格式

```json
{
  "knowledge_base": {
    "data_dir": "./data",
    "auto_load": true
  },
  "launcher": {
    "game_path": "C:/Games/Minecraft",
    "log_port": 9000
  },
  "log_capture": {
    "buffer_size": 1000,
    "auto_flush": true
  },
  "generation": {
    "template_dir": "./templates",
    "output_dir": "./output"
  },
  "cli": {
    "output_format": "text",
    "color_output": true
  }
}
```

## 配置项说明

### knowledge_base 配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `data_dir` | string | `./data` | 知识库数据目录 |
| `auto_load` | bool | `true` | 是否自动加载知识库 |
| `index_file` | string | `knowledge_base.json` | 索引文件名 |
| `cache_enabled` | bool | `true` | 是否启用缓存 |

### launcher 配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `game_path` | string | - | 游戏安装路径 |
| `log_port` | int | `9000` | 日志服务器端口 |
| `auto_start` | bool | `false` | 是否自动启动游戏 |
| `timeout` | int | `30` | 启动超时时间（秒） |

### log_capture 配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `buffer_size` | int | `1000` | 日志缓冲区大小 |
| `auto_flush` | bool | `true` | 是否自动刷新缓冲区 |
| `flush_interval` | int | `5` | 刷新间隔（秒） |
| `error_patterns` | list | 见下方 | 错误模式列表 |

### generation 配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `template_dir` | string | `./templates` | 模板目录 |
| `output_dir` | string | `./output` | 输出目录 |
| `default_author` | string | - | 默认作者名 |
| `indent_style` | string | `space` | 缩进风格 (space/tab) |
| `indent_size` | int | `4` | 缩进大小 |

### cli 配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `output_format` | string | `text` | 输出格式 (text/json) |
| `color_output` | bool | `true` | 是否彩色输出 |
| `pager` | bool | `false` | 是否使用分页器 |
| `verbose` | bool | `false` | 详细输出模式 |

## 环境变量

MC-Agent-Kit 支持通过环境变量覆盖配置：

```bash
# 游戏路径
export MC_AGENT_GAME_PATH="/path/to/minecraft"

# 日志端口
export MC_AGENT_LOG_PORT=9000

# 知识库数据目录
export MC_AGENT_DATA_DIR="./data"

# 输出格式
export MC_AGENT_OUTPUT_FORMAT=json
```

## 代码配置

您也可以在代码中直接配置：

```python
from mc_agent_kit import knowledge_base, launcher, log_capture

# 配置知识库
kb = knowledge_base.KnowledgeBase()
kb.load("./data/knowledge_base.json")

# 配置启动器
config = launcher.LauncherConfig(
    game_path="C:/Games/Minecraft",
    log_port=9000,
    timeout=30
)
game_launcher = launcher.GameLauncher(config)

# 配置日志捕获
log_config = log_capture.LogCaptureConfig(
    buffer_size=1000,
    auto_flush=True
)
capture = log_capture.LogCapture(log_config)
```

## 最佳实践

### 1. 使用版本控制

将配置文件加入版本控制，方便团队协作：

```bash
git add mc-agent-kit.yaml
git commit -m "Add project configuration"
```

### 2. 敏感信息分离

敏感信息（如游戏路径）使用环境变量：

```yaml
launcher:
  game_path: ${MC_AGENT_GAME_PATH}
```

### 3. 环境区分

为不同环境创建不同配置：

```bash
# 开发环境
mc-agent-kit.dev.yaml

# 生产环境
mc-agent-kit.prod.yaml
```

### 4. 团队共享

在项目中包含 `mc-agent-kit.yaml.example` 作为配置模板：

```yaml
# mc-agent-kit.yaml.example
knowledge_base:
  data_dir: ./data
  auto_load: true

launcher:
  game_path: "YOUR_GAME_PATH"  # 修改为你的游戏路径
  log_port: 9000
```

## 故障排除

### 配置文件未生效

1. 检查配置文件位置是否正确
2. 检查配置文件格式是否正确（YAML 缩进、JSON 语法）
3. 使用环境变量覆盖测试

### 游戏路径配置错误

1. 确保路径存在
2. Windows 路径使用正斜杠或双反斜杠
3. 路径不要包含中文字符

---

*最后更新：2026-03-22*