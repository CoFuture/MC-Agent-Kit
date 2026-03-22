# MC-Agent-Kit CLI 命令参考

本文档详细介绍了 MC-Agent-Kit 提供的所有 CLI 命令。

---

## 全局选项

| 选项 | 说明 |
|------|------|
| `--format`, `-f` | 输出格式：`text`（默认）或 `json` |
| `--help`, `-h` | 显示帮助信息 |

---

## 命令概览

| 命令 | 说明 |
|------|------|
| `mc-agent list` | 列出所有已注册的 Skills |
| `mc-agent api` | 搜索 ModSDK API 文档 |
| `mc-agent event` | 搜索 ModSDK 事件文档 |
| `mc-agent gen` | 生成 ModSDK 代码 |
| `mc-agent debug` | 调试 ModSDK 错误 |
| `mc-agent complete` | 代码补全建议 |
| `mc-agent refactor` | 代码重构建议 |
| `mc-agent check` | 最佳实践检查 |
| `mc-agent autofix` | 自动修复代码错误 |
| `mc-agent create` | 创建 Addon 项目 |
| `mc-agent kb` | 知识库管理 |
| `mc-agent run` | 运行游戏并加载 Addon |
| `mc-agent logs` | 日志分析 |
| `mc-agent launcher` | 启动器诊断 |

---

## mc-agent list

列出所有已注册的 Skills。

### 用法

```bash
mc-agent list [选项]
```

### 选项

| 选项 | 说明 |
|------|------|
| `--format`, `-f` | 输出格式：`text` 或 `json` |

### 示例

```bash
# 列出所有 Skills
mc-agent list

# JSON 格式输出
mc-agent list --format json
```

---

## mc-agent api

搜索 ModSDK API 文档。

### 用法

```bash
mc-agent api [选项]
```

### 选项

| 选项 | 说明 |
|------|------|
| `-q`, `--query` | 搜索关键词 |
| `-n`, `--name` | 精确匹配 API 名称 |
| `-m`, `--module` | 按模块过滤 |
| `-s`, `--scope` | 按作用域过滤：`client` 或 `server` |
| `-l`, `--limit` | 返回结果数量，默认 10 |
| `--format`, `-f` | 输出格式：`text` 或 `json` |

### 示例

```bash
# 关键词搜索
mc-agent api -q "创建实体"

# 精确匹配
mc-agent api -n CreateEngineEntity

# 按模块过滤
mc-agent api -m "实体模块" -l 5

# 按作用域过滤
mc-agent api -q "玩家" -s server
```

---

## mc-agent event

搜索 ModSDK 事件文档。

### 用法

```bash
mc-agent event [选项]
```

### 选项

| 选项 | 说明 |
|------|------|
| `-q`, `--query` | 搜索关键词 |
| `-n`, `--name` | 精确匹配事件名称 |
| `-m`, `--module` | 按模块过滤 |
| `-s`, `--scope` | 按作用域过滤：`client` 或 `server` |
| `-l`, `--limit` | 返回结果数量，默认 10 |
| `--format`, `-f` | 输出格式：`text` 或 `json` |

### 示例

```bash
# 关键词搜索
mc-agent event -q "玩家加入"

# 精确匹配
mc-agent event -n OnServerChat

# 按模块过滤
mc-agent event -m "聊天模块"
```

---

## mc-agent gen

生成 ModSDK 代码。

### 用法

```bash
mc-agent gen [选项]
```

### 选项

| 选项 | 说明 |
|------|------|
| `-t`, `--template` | 模板名称 |
| `-p`, `--params` | 模板参数（JSON 格式） |
| `-a`, `--action` | 操作类型：`generate`、`list`、`search` |
| `-k`, `--keyword` | 搜索关键词 |
| `--format`, `-f` | 输出格式：`text` 或 `json` |

### 内置模板

| 模板 | 说明 |
|------|------|
| `event_listener` | 事件监听器 |
| `api_call` | API 调用 |
| `entity_create` | 创建实体 |
| `item_register` | 注册物品 |
| `ui_screen` | UI 界面 |

### 示例

```bash
# 列出可用模板
mc-agent gen -a list

# 生成事件监听器
mc-agent gen -t event_listener -p '{"event_name": "OnServerChat", "callback": "on_chat"}'

# 生成 API 调用
mc-agent gen -t api_call -p '{"api_name": "CreateEngineEntity", "params": {"type": "minecraft:zombie"}}'
```

---

## mc-agent debug

调试 ModSDK 错误。

### 用法

```bash
mc-agent debug [选项]
```

### 选项

| 选项 | 说明 |
|------|------|
| `-l`, `--log` | 日志内容 |
| `--file` | 日志文件路径 |
| `-a`, `--action` | 操作类型：`diagnose`、`list_errors` |
| `--format`, `-f` | 输出格式：`text` 或 `json` |

### 示例

```bash
# 诊断错误
mc-agent debug --file error.log

# 列出已知错误模式
mc-agent debug -a list_errors

# 直接分析日志内容
mc-agent debug -l "KeyError: 'speed'"
```

---

## mc-agent complete

代码补全建议。

### 用法

```bash
mc-agent complete [选项]
```

### 选项

| 选项 | 说明 |
|------|------|
| `-c`, `--code` | 代码内容 |
| `--file` | 代码文件路径 |
| `-l`, `--line` | 光标行号，默认 1 |
| `-C`, `--column` | 光标列号，默认 0 |
| `-p`, `--prefix` | 补全前缀 |
| `--format`, `-f` | 输出格式：`text` 或 `json` |

### 示例

```bash
# 从文件补全
mc-agent complete --file main.py --line 10 --column 15

# 补全 API 名称
mc-agent complete -c "Create" -p "Create"
```

---

## mc-agent refactor

代码重构建议。

### 用法

```bash
mc-agent refactor [选项]
```

### 选项

| 选项 | 说明 |
|------|------|
| `-c`, `--code` | 代码内容 |
| `--file` | 代码文件路径 |
| `-a`, `--action` | 操作类型：`detect`（检测）、`suggest`（建议） |
| `--format`, `-f` | 输出格式：`text` 或 `json` |

### 示例

```bash
# 检测代码异味
mc-agent refactor --file main.py -a detect

# 生成重构建议
mc-agent refactor --file main.py -a suggest
```

---

## mc-agent check

最佳实践检查。

### 用法

```bash
mc-agent check [选项]
```

### 选项

| 选项 | 说明 |
|------|------|
| `-c`, `--code` | 代码内容 |
| `--file` | 代码文件路径 |
| `-a`, `--action` | 操作类型：`check`（检查）、`list`（列出所有实践） |
| `--format`, `-f` | 输出格式：`text` 或 `json` |

### 示例

```bash
# 检查代码
mc-agent check --file main.py

# 列出所有最佳实践
mc-agent check -a list
```

---

## mc-agent autofix

自动修复代码错误。

### 用法

```bash
mc-agent autofix [选项]
```

### 选项

| 选项 | 说明 |
|------|------|
| `-c`, `--code` | 代码内容 |
| `--file` | 代码文件路径 |
| `-e`, `--error` | 错误日志内容 |
| `-E`, `--error-file` | 错误日志文件路径 |
| `-a`, `--action` | 操作类型：`diagnose`、`fix`、`preview` |
| `--format`, `-f` | 输出格式：`text` 或 `json` |

### 示例

```bash
# 诊断错误
mc-agent autofix --file main.py --error-file error.log -a diagnose

# 预览修复
mc-agent autofix --file main.py -e "KeyError: 'speed'" -a preview

# 应用修复
mc-agent autofix --file main.py -e "KeyError: 'speed'" -a fix
```

---

## mc-agent create

创建 Addon 项目。

### 用法

```bash
mc-agent create <类型> <名称> [选项]
```

### 参数

| 参数 | 说明 |
|------|------|
| `类型` | 创建类型：`project`、`entity`、`item`、`block` |
| `名称` | 项目/实体/物品/方块名称 |

### 选项

| 选项 | 说明 |
|------|------|
| `-p`, `--path` | 目标路径 |
| `-t`, `--template` | 项目模板：`empty`、`entity`、`item`、`block` |
| `--force` | 覆盖已存在的项目 |
| `--format`, `-f` | 输出格式：`text` 或 `json` |

### 示例

```bash
# 创建新项目
mc-agent create project my-addon -p ./projects

# 使用模板创建
mc-agent create project my-entity-addon -t entity

# 添加实体
mc-agent create entity my_entity -p ./projects/my-addon

# 添加物品
mc-agent create item my_item -p ./projects/my-addon

# 添加方块
mc-agent create block my_block -p ./projects/my-addon
```

---

## mc-agent kb

知识库管理。

### 用法

```bash
mc-agent kb <操作> [选项]
```

### 操作

| 操作 | 说明 |
|------|------|
| `status` | 查看知识库状态 |
| `search` | 语义搜索 |
| `api` | 精确查 API |
| `event` | 精确查事件 |

### 选项

| 选项 | 说明 |
|------|------|
| `-q`, `--query` | 搜索查询 |
| `-n`, `--name` | API/事件名称 |
| `-l`, `--limit` | 返回结果数量，默认 5 |
| `--format`, `-f` | 输出格式：`text` 或 `json` |

### 示例

```bash
# 查看状态
mc-agent kb status

# 语义搜索
mc-agent kb search -q "创建实体" -l 10

# 精确查 API
mc-agent kb api -n CreateEngineEntity

# 精确查事件
mc-agent kb event -n OnServerChat
```

---

## mc-agent run

运行游戏并加载 Addon。

### 用法

```bash
mc-agent run <addon路径> [选项]
```

### 参数

| 参数 | 说明 |
|------|------|
| `addon路径` | Addon 目录路径 |

### 选项

| 选项 | 说明 |
|------|------|
| `--game-path` | 游戏可执行文件路径 |
| `--version` | 游戏版本 |
| `-o`, `--output-dir` | 配置输出目录 |
| `--log-port` | 日志接收端口 |
| `--no-logs` | 禁用日志捕获 |
| `--wait` | 等待游戏退出 |
| `-v`, `--verbose` | 详细输出 |
| `--format`, `-f` | 输出格式：`text` 或 `json` |

### 示例

```bash
# 启动游戏
mc-agent run ./my-addon

# 指定游戏路径
mc-agent run ./my-addon --game-path "C:\Games\Minecraft.Windows.exe"

# 启动并等待
mc-agent run ./my-addon --wait --verbose

# JSON 格式输出
mc-agent run ./my-addon --format json
```

---

## mc-agent logs

日志分析。

### 用法

```bash
mc-agent logs <操作> [选项]
```

### 操作

| 操作 | 说明 |
|------|------|
| `analyze` | 分析日志内容 |
| `errors` | 提取错误信息 |
| `patterns` | 列出错误模式 |

### 选项

| 选项 | 说明 |
|------|------|
| `-l`, `--log` | 日志内容 |
| `--file` | 日志文件路径 |
| `--limit` | 返回结果数量，默认 20 |
| `--format`, `-f` | 输出格式：`text` 或 `json` |

### 示例

```bash
# 分析日志
mc-agent logs analyze --file game.log

# 提取错误
mc-agent logs errors --file game.log

# 列出错误模式
mc-agent logs patterns
```

---

## mc-agent launcher

启动器诊断。

### 用法

```bash
mc-agent launcher <操作> [选项]
```

### 操作

| 操作 | 说明 |
|------|------|
| `diagnose` | 诊断启动器配置 |
| `compare` | 对比配置文件 |

### 选项

| 选项 | 说明 |
|------|------|
| `--addon-path` | Addon 目录路径 |
| `--config-path` | 配置文件路径 |
| `--game-path` | 游戏可执行文件路径 |
| `--mc-studio-config` | MC Studio 配置文件路径（用于对比） |
| `--format`, `-f` | 输出格式：`text` 或 `json` |

### 示例

```bash
# 诊断 Addon
mc-agent launcher diagnose --addon-path ./my-addon

# 诊断配置文件
mc-agent launcher diagnose --config-path ./config.cppconfig

# 完整诊断
mc-agent launcher diagnose --addon-path ./my-addon --config-path ./config.cppconfig --game-path "C:\Games\Minecraft.Windows.exe"

# 对比配置文件
mc-agent launcher compare --config-path ./my-config.cppconfig
```

---

## 退出码

所有命令返回以下退出码：

| 退出码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1 | 失败或错误 |

---

## 输出格式

### text 格式（默认）

人类可读的文本格式，包含表情符号和格式化输出。

### json 格式

结构化的 JSON 格式，适合程序处理。

```json
{
  "success": true,
  "message": "操作成功",
  "data": { ... }
}
```

---

*文档版本: v1.0.0*
*最后更新: 2026-03-22*