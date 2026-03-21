# ModSDK 游戏执行器 Skill

## 概述

在 Minecraft 游戏环境中执行 ModSDK 代码，支持实时调试和结果反馈。

## 使用场景

- 游戏内代码执行
- 实时代码测试
- 调试脚本运行
- 热重载测试

## 工具说明

### mc_game_execute

在游戏环境中执行代码。

**参数**:
- `code` (str): 要执行的 Python 代码
- `context` (dict, optional): 执行上下文变量
- `timeout` (int, optional): 超时时间（秒），默认 30

**返回**:
- `success` (bool): 是否成功
- `result`: 执行结果
- `stdout`: 标准输出
- `stderr`: 错误输出

### mc_game_launch

启动 Minecraft 游戏实例。

**参数**:
- `addon_path` (str): Addon 目录路径
- `game_path` (str, optional): 游戏安装路径
- `log_port` (int, optional): 日志服务器端口

**返回**:
- `success` (bool): 是否成功
- `session_id` (str): 游戏会话 ID
- `logs`: 启动日志

### mc_game_stop

停止游戏实例。

**参数**:
- `session_id` (str): 游戏会话 ID

**返回**:
- `success` (bool): 是否成功

### mc_game_status

获取游戏实例状态。

**参数**:
- `session_id` (str): 游戏会话 ID

**返回**:
- `status` (str): 游戏状态 (running/stopped/starting/error)
- `uptime` (int): 运行时间（秒）
- `memory_usage` (int): 内存使用量

## 使用示例

### 示例 1: 启动游戏并执行代码

```
# 启动游戏
mc_game_launch(
    addon_path="./my_addon",
    log_port=9000
)

# 执行代码
mc_game_execute(
    code="print(GetConfig('server', 'max_players'))"
)

# 停止游戏
mc_game_stop(session_id="xxx")
```

### 示例 2: 测试实体创建

```
mc_game_execute(
    code='''
entity_id = CreateEntity("custom:my_entity", (0, 64, 0))
print("Created entity:", entity_id)
'''
)
```

### 示例 3: 调试事件监听器

```
mc_game_execute(
    code='''
def on_chat(args):
    print("Chat:", args.get('message'))
    
RegisterOnServerChat(on_chat)
print("Chat listener registered")
'''
)
```

### 示例 4: 检查游戏状态

```
status = mc_game_status(session_id="xxx")
print(f"Game status: {status['status']}")
print(f"Uptime: {status['uptime']}s")
```

## 执行环境

### 可用变量

游戏执行环境中预置以下变量：

| 变量 | 类型 | 说明 |
|------|------|------|
| `serverApi` | module | 服务端 API 模块 |
| `clientApi` | module | 客户端 API 模块 |
| `GetConfig` | function | 获取配置 |
| `CreateEntity` | function | 创建实体 |
| `GetPlayerId` | function | 获取玩家 ID |

### 执行限制

- 默认超时时间: 30 秒
- 最大执行次数: 100 次/分钟
- 内存限制: 128MB

## 安全说明

1. 只执行可信代码
2. 沙箱模式阻止危险操作
3. 敏感 API 需要额外授权

## 最佳实践

1. 执行前先验证代码语法
2. 使用 try-except 捕获错误
3. 及时清理创建的资源
4. 记录执行日志便于调试

## 故障排除

### 执行超时

- 检查代码是否有死循环
- 增加 timeout 参数
- 分步执行复杂操作

### 连接失败

- 确认游戏已启动
- 检查端口是否被占用
- 验证 addon 路径正确

### 权限不足

- 确认 Addon 配置正确
- 检查 API 权限设置

---

*Skill 版本: 1.0.0*
*最后更新: 2026-03-22*