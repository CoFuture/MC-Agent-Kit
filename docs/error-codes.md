# MC-Agent-Kit 错误代码参考

> 版本: v1.0.0
> 最后更新: 2026-03-23

本文档列出 MC-Agent-Kit 中可能出现的错误代码、原因和解决方案。

---

## 错误代码分类

| 前缀 | 类别 | 说明 |
|------|------|------|
| `E0xx` | 启动器错误 | 游戏启动相关错误 |
| `E1xx` | 知识库错误 | 知识检索相关错误 |
| `E2xx` | 代码生成错误 | 代码生成相关错误 |
| `E3xx` | 项目创建错误 | 脚手架相关错误 |
| `E4xx` | 执行错误 | 代码执行相关错误 |
| `E5xx` | 配置错误 | 配置文件相关错误 |

---

## 启动器错误 (E0xx)

### E001: 游戏路径不存在

**错误信息**: `Game path does not exist: {path}`

**原因**: 指定的游戏安装路径不存在

**解决方案**:
1. 检查游戏是否已正确安装
2. 使用 `--game-path` 指定正确的游戏路径
3. 检查路径格式是否正确（Windows 使用 `\\` 或 `/`）

**示例**:
```bash
# 正确用法
mc-run ./my-addon --game-path "C:/Games/Minecraft"
```

---

### E002: Addon 目录无效

**错误信息**: `Invalid addon directory: {path}`

**原因**: Addon 目录缺少必要文件

**解决方案**:
1. 确保 Addon 目录包含 `behavior_pack/` 或 `resource_pack/`
2. 确保每个 pack 包含 `manifest.json`
3. 使用 `mc-launcher diagnose` 诊断问题

**示例目录结构**:
```
my-addon/
├── behavior_pack/
│   ├── manifest.json
│   └── scripts/
└── resource_pack/
    └── manifest.json
```

---

### E003: manifest.json 格式错误

**错误信息**: `Invalid manifest.json: {error}`

**原因**: manifest.json 文件格式不正确

**解决方案**:
1. 检查 JSON 语法是否正确
2. 确保包含必要字段：`format_version`, `header`, `modules`
3. 使用 JSON 验证工具检查

**正确的 manifest.json 格式**:
```json
{
    "format_version": 2,
    "header": {
        "name": "My Addon",
        "description": "Description",
        "uuid": "xxx-xxx-xxx",
        "version": [1, 0, 0]
    },
    "modules": [
        {
            "type": "data",
            "uuid": "xxx-xxx-xxx",
            "version": [1, 0, 0]
        }
    ]
}
```

---

### E004: 配置文件生成失败

**错误信息**: `Failed to generate config file: {error}`

**原因**: 无法生成游戏配置文件 (.cppconfig)

**解决方案**:
1. 检查文件权限
2. 确保目标目录可写
3. 使用 `mc-launcher fix` 自动修复

---

### E005: 游戏进程启动失败

**错误信息**: `Failed to start game process: {error}`

**原因**: 无法启动游戏进程

**解决方案**:
1. 检查游戏是否已经在运行
2. 检查系统资源是否充足
3. 检查杀毒软件是否阻止

---

## 知识库错误 (E1xx)

### E101: 知识库未初始化

**错误信息**: `Knowledge base not initialized`

**原因**: 知识库索引文件不存在或未构建

**解决方案**:
```bash
# 构建知识库索引
mc-kb build

# 或指定知识库路径
mc-kb search "创建实体" --kb-path ./knowledge_base.json
```

---

### E102: 知识库索引损坏

**错误信息**: `Knowledge base index corrupted`

**原因**: 知识库索引文件损坏或不完整

**解决方案**:
```bash
# 重建索引
mc-kb build --full
```

---

### E103: API 未找到

**错误信息**: `API not found: {name}`

**原因**: 搜索的 API 不存在于知识库中

**解决方案**:
1. 检查 API 名称拼写
2. 使用模糊搜索：`mc-kb search "{name}"`
3. 查看可用 API：`mc-kb api --list`

---

### E104: 事件未找到

**错误信息**: `Event not found: {name}`

**原因**: 搜索的事件不存在于知识库中

**解决方案**:
1. 检查事件名称拼写
2. 使用模糊搜索：`mc-kb search "{name}"`
3. 查看可用事件：`mc-kb event --list`

---

## 代码生成错误 (E2xx)

### E201: 模板不存在

**错误信息**: `Template not found: {name}`

**原因**: 请求的代码模板不存在

**解决方案**:
1. 查看可用模板：`mc-agent gen --list-templates`
2. 检查模板名称拼写
3. 使用自定义模板目录

**可用模板**:
- `event_listener`: 事件监听器
- `api_call`: API 调用
- `entity_create`: 创建实体
- `item_register`: 注册物品
- `ui_screen`: UI 界面
- `block_register`: 注册方块
- `dimension_config`: 维度配置

---

### E202: 模板参数缺失

**错误信息**: `Missing required parameter: {param}`

**原因**: 模板需要的参数未提供

**解决方案**:
1. 检查模板需要哪些参数：`mc-agent gen --info {template}`
2. 提供所有必需参数

**示例**:
```bash
# 事件监听器需要 event_name 参数
mc-agent gen event_listener --params '{"event_name": "OnServerChat"}'
```

---

### E203: 模板参数类型错误

**错误信息**: `Invalid parameter type for {param}: expected {expected}, got {actual}`

**原因**: 参数类型与预期不符

**解决方案**:
1. 检查参数类型要求
2. 使用正确的 JSON 格式

---

## 项目创建错误 (E3xx)

### E301: 项目目录已存在

**错误信息**: `Project directory already exists: {path}`

**原因**: 尝试创建的项目目录已存在

**解决方案**:
1. 使用不同的项目名称
2. 删除现有目录
3. 使用 `--force` 覆盖（会删除现有目录）

---

### E302: 模板目录不存在

**错误信息**: `Template directory not found: {path}`

**原因**: 指定的模板目录不存在

**解决方案**:
1. 检查模板目录路径
2. 使用默认模板

---

### E303: 实体创建失败

**错误信息**: `Failed to create entity: {error}`

**原因**: 无法创建实体文件

**解决方案**:
1. 确保在项目目录中运行
2. 检查文件权限
3. 确保实体名称有效（只包含字母、数字、下划线）

---

### E304: 物品创建失败

**错误信息**: `Failed to create item: {error}`

**原因**: 无法创建物品文件

**解决方案**:
1. 确保在项目目录中运行
2. 检查文件权限
3. 确保物品名称有效

---

## 执行错误 (E4xx)

### E401: 代码执行超时

**错误信息**: `Code execution timeout after {seconds} seconds`

**原因**: 代码执行超过最大时间限制

**解决方案**:
1. 增加超时时间：`--timeout 60`
2. 优化代码减少执行时间
3. 检查是否存在无限循环

---

### E402: 沙箱违规

**错误信息**: `Sandbox violation: {operation}`

**原因**: 代码尝试执行被禁止的操作

**解决方案**:
1. 检查代码是否使用了危险操作（如 `eval`, `exec`）
2. 检查是否尝试导入被禁止的模块
3. 使用非沙箱模式（需要信任代码）

---

### E403: 代码语法错误

**错误信息**: `Syntax error in code: {error}`

**原因**: 提供的代码包含语法错误

**解决方案**:
1. 检查代码语法
2. 使用 Python 语法检查器
3. 确保使用正确的 Python 版本语法

---

## 配置错误 (E5xx)

### E501: 配置文件不存在

**错误信息**: `Configuration file not found: {path}`

**原因**: 配置文件不存在

**解决方案**:
```bash
# 生成默认配置文件
mc-agent config generate --output config.yaml
```

---

### E502: 配置文件格式错误

**错误信息**: `Invalid configuration file: {error}`

**原因**: 配置文件格式不正确

**解决方案**:
1. 检查 YAML/JSON 语法
2. 使用配置验证：`mc-agent config validate config.yaml`
3. 重新生成配置文件

---

### E503: 配置验证失败

**错误信息**: `Configuration validation failed: {errors}`

**原因**: 配置值不符合要求

**解决方案**:
1. 检查配置项类型和范围
2. 参考配置文档

---

## 通用错误处理

### 获取详细错误信息

```bash
# 使用 --verbose 获取详细信息
mc-run ./my-addon --verbose

# 查看日志文件
mc-logs --tail
```

### 诊断问题

```bash
# 运行诊断
mc-launcher diagnose --addon-path ./my-addon

# 自动修复
mc-launcher fix --config-path ./config.yaml
```

### 报告问题

如果遇到无法解决的问题，请：

1. 收集错误信息和日志
2. 在 GitHub Issues 中搜索类似问题
3. 创建新 Issue 并附上：
   - 错误代码
   - 完整错误信息
   - 复现步骤
   - 环境信息（Python 版本、操作系统）

---

## 错误代码速查表

| 错误代码 | 描述 | 解决方案 |
|---------|------|----------|
| E001 | 游戏路径不存在 | 检查路径，使用 --game-path |
| E002 | Addon 目录无效 | 添加必要的文件和目录 |
| E003 | manifest.json 格式错误 | 修复 JSON 格式 |
| E004 | 配置文件生成失败 | 检查权限 |
| E005 | 游戏进程启动失败 | 检查资源和冲突 |
| E101 | 知识库未初始化 | 运行 mc-kb build |
| E102 | 知识库索引损坏 | 重建索引 |
| E103 | API 未找到 | 检查拼写或使用搜索 |
| E104 | 事件未找到 | 检查拼写或使用搜索 |
| E201 | 模板不存在 | 检查模板名称 |
| E202 | 模板参数缺失 | 提供必需参数 |
| E203 | 模板参数类型错误 | 使用正确的类型 |
| E301 | 项目目录已存在 | 使用不同名称或 --force |
| E302 | 模板目录不存在 | 检查路径 |
| E303 | 实体创建失败 | 检查权限和名称 |
| E304 | 物品创建失败 | 检查权限和名称 |
| E401 | 代码执行超时 | 增加超时或优化代码 |
| E402 | 沙箱违规 | 移除危险操作 |
| E403 | 代码语法错误 | 修复语法 |
| E501 | 配置文件不存在 | 生成配置文件 |
| E502 | 配置文件格式错误 | 修复格式 |
| E503 | 配置验证失败 | 检查配置值 |

---

*文档版本: v1.0.0*
*最后更新: 2026-03-23*