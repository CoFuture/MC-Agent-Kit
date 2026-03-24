# 代码生成

MC-Agent-Kit 的 AI 代码生成功能帮助你快速生成 ModSDK 代码。

## 基本用法

### 命令行方式

```bash
# 基本语法
mc-llm gen "<需求描述>"

# 示例：生成事件监听器
mc-llm gen "创建一个监听玩家加入事件的监听器"

# 示例：生成实体代码
mc-llm gen "创建一个跟随玩家的宠物实体" --type entity_behavior

# 示例：生成 UI 代码
mc-llm gen "创建一个显示玩家属性的 UI 界面" --type ui_screen
```

### 交互模式

```bash
# 启动聊天模式
mc-llm chat

# 在聊天中请求代码
mc-llm> 请帮我写一个定时广播消息的功能

# AI 会生成代码并解释
```

## 生成类型

MC-Agent-Kit 支持多种代码生成类型：

| 类型 | 说明 | 示例需求 |
|------|------|----------|
| `event_listener` | 事件监听器 | "监听玩家死亡事件" |
| `entity_behavior` | 实体行为 | "创建一个巡逻的守卫" |
| `item_logic` | 物品逻辑 | "创建一个传送卷轴物品" |
| `ui_screen` | UI 界面 | "创建一个商店 UI" |
| `network_sync` | 网络同步 | "同步玩家金币数据" |
| `config_handler` | 配置处理 | "读取配置文件" |
| `error_handler` | 错误处理 | "全局异常处理器" |
| `custom` | 自定义 | 任意需求 |

## 生成参数

### 目标环境

```bash
# 服务端代码（默认）
mc-llm gen "创建定时器" --target server

# 客户端代码
mc-llm gen "创建 UI 界面" --target client
```

### 代码风格

```bash
# 指定代码风格
mc-llm gen "创建事件监听器" --style pep8
```

### 流式输出

```bash
# 实时显示生成过程
mc-llm gen "创建复杂的实体 AI" --stream
```

## 生成结果解读

### 成功生成

```
✅ Code Generated Successfully

Code:
```python
from mod.server.extraServerApi import serverApi

ServerSystem = serverApi.GetServerSystemCls()

class MySystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        # ... 代码内容
```

Required imports:
  from mod.server.extraServerApi import serverApi

Notes:
  💡 需要在服务端运行
  💡 记得注册事件监听

Confidence: 0.85
```

### 生成失败

```
❌ Code Generation Failed

Error: Unable to connect to LLM provider

Possible solutions:
1. Check your API key
2. Verify network connection
3. Try a different provider
```

## 提高生成质量

### 1. 提供详细需求

```bash
# ❌ 模糊需求
mc-llm gen "创建实体"

# ✅ 详细需求
mc-llm gen "创建一个名为 FrostGhost 的冰雪幽灵实体，具有以下特性：
- 在雪地生物群系生成
- 发射冰冻投射物
- 掉落冰块和雪球"
```

### 2. 指定上下文

```bash
# 提供项目上下文
mc-llm gen "添加物品使用功能" --context "项目名: MyAddon, 模块: items"
```

### 3. 使用自定义提示词

```yaml
# ~/.mc-agent-kit/config.yaml
code_generation:
  custom_prompt: |
    你是一个 ModSDK 专家。
    请生成高质量、可维护的代码。
    遵循以下规则：
    - 使用有意义的变量名
    - 添加详细注释
    - 处理所有可能的错误
```

## 生成后处理

### 代码审查

```bash
# 生成后立即审查
mc-llm gen "创建复杂功能" | mc-llm review -
```

### 应用修复

```bash
# 如果代码有问题，请求修复
mc-llm fix "KeyError: 'entity'" --code generated_code.py
```

## 最佳实践

### 1. 迭代生成

复杂功能分步生成：

```bash
# 第一步：生成基础结构
mc-llm gen "创建实体基础框架" > entity_base.py

# 第二步：添加行为
mc-llm gen "为实体添加巡逻行为" >> entity_base.py

# 第三步：添加交互
mc-llm gen "添加玩家交互功能" >> entity_base.py
```

### 2. 组合使用

```bash
# 先搜索相关 API
mc-kb search "实体移动"

# 然后生成代码
mc-llm gen "实现实体移动功能"
```

### 3. 验证生成代码

```bash
# 审查代码质量
mc-llm review generated.py

# 诊断潜在问题
mc-llm diagnose --code generated.py
```

## 下一步

- 🔍 [代码审查](./code-review.md) - 审查生成代码
- 🐛 [错误诊断](./error-diagnosis.md) - 诊断和修复错误
- 💡 [自定义提示词](./custom-prompts.md) - 优化生成效果

---

*最后更新: 2026-03-25*