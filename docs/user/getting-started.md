# 快速入门

欢迎使用 MC-Agent-Kit！本指南将帮助您快速上手，开始使用 AI Agent 辅助 ModSDK 开发。

## 什么是 MC-Agent-Kit？

MC-Agent-Kit 是一套 AI Agent 辅助工具包，专门为网易 Minecraft ModSDK 开发设计。它提供了：

- **知识库检索**：快速查找 API 文档和事件文档
- **代码生成**：基于模板自动生成 ModSDK 代码
- **调试辅助**：分析错误日志，提供修复建议
- **代码补全**：智能补全 API 名称和参数
- **最佳实践检查**：自动检测代码问题并提供建议

## 5 分钟快速开始

### 1. 安装

```bash
# 使用 pip 安装
pip install mc-agent-kit

# 或使用 uv（推荐）
uv pip install mc-agent-kit
```

### 2. 验证安装

```bash
# 查看帮助
mc-agent --help

# 列出所有可用 Skills
mc-agent list
```

### 3. 搜索 API

```bash
# 搜索 "GetConfig" 相关 API
mc-agent api -q "GetConfig"

# 搜索 "entity" 相关 API
mc-agent api -q "entity" -l 5
```

### 4. 搜索事件

```bash
# 搜索 "OnCreate" 相关事件
mc-agent event -q "OnCreate"

# 按模块过滤
mc-agent event -q "OnCreate" -m "entity"
```

### 5. 生成代码

```bash
# 生成事件监听器
mc-agent gen -t event_listener -p '{"event_name": "OnServerChat", "callback": "handle_chat"}'

# 生成 API 调用
mc-agent gen -t api_call -p '{"api_name": "GetConfig", "module": "game"}'
```

### 6. 调试错误

```bash
# 诊断错误日志
mc-agent debug -l "NameError: name 'GetConfig' is not defined"

# 从文件读取日志
mc-agent debug -f error.log
```

## 下一步

- 阅读 [安装指南](installation.md) 了解详细安装步骤
- 阅读 [配置指南](configuration.md) 了解如何配置项目
- 学习 [Hello World 教程](tutorial/hello-world.md) 创建你的第一个 Mod
- 学习 [自定义实体教程](tutorial/custom-entity.md) 创建自定义实体
- 查看 [常见问题](faq.md) 解决常见问题

## 在 OpenClaw 中使用

MC-Agent-Kit 提供了 OpenClaw Skills，可以让 AI Agent 自动调用：

### 配置 Skills

将 `skills/` 目录下的 Skills 复制到你的 OpenClaw skills 目录：

```bash
cp -r skills/* ~/.openclaw/skills/
```

### 使用 Skills

在 OpenClaw 中，你可以直接询问：

```
搜索 GetConfig API 的用法
```

```
帮我生成一个 OnServerChat 事件监听器
```

```
分析这个错误日志：NameError: name 'GetConfig' is not defined
```

AI Agent 会自动调用相应的 Skill 来完成任务。

## CLI 命令速查

| 命令 | 描述 |
|------|------|
| `mc-agent list` | 列出所有 Skills |
| `mc-agent api` | 搜索 API 文档 |
| `mc-agent event` | 搜索事件文档 |
| `mc-agent gen` | 生成代码 |
| `mc-agent debug` | 调试错误 |
| `mc-agent complete` | 代码补全 |
| `mc-agent refactor` | 代码重构建议 |
| `mc-agent check` | 最佳实践检查 |
| `mc-agent autofix` | 自动修复错误 |

---

*最后更新：2026-03-22*