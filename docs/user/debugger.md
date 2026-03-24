# 调试器使用指南

> 版本: v1.45.0
> 最后更新: 2026-03-24

---

## 概述

游戏调试器提供了 Minecraft 网易版 ModSDK Addon 的调试功能，包括：

- 游戏进程附加
- 断点设置
- 变量监视
- 日志捕获和分析
- 热重载支持

---

## 快速开始

### 基本使用

```python
from mc_agent_kit.debugger.game_debug import create_game_debugger

# 创建调试器实例
debugger = create_game_debugger()

# 附加到游戏进程
if debugger.attach(pid=12345):  # 替换为实际进程 ID
    print("已连接到游戏进程")
```

---

## 调试会话管理

### 附加到进程

```python
# 通过进程 ID 附加
debugger.attach(pid=12345)

# 通过进程名附加
debugger.attach_by_name("Minecraft.Windows")
```

### 断开连接

```python
debugger.detach()
```

### 检查状态

```python
from mc_agent_kit.debugger.game_debug import DebugState

if debugger.state == DebugState.CONNECTED:
    print("调试器已连接")
elif debugger.state == DebugState.PAUSED:
    print("调试器已暂停")
```

---

## 断点管理

### 设置断点

```python
# 基础断点
bp = debugger.set_breakpoint("main.py", line=42)

# 条件断点
bp = debugger.set_breakpoint(
    "main.py",
    line=50,
    condition="player.health < 10",  # 条件表达式
)

# 日志断点（不暂停执行，只记录日志）
bp = debugger.set_breakpoint(
    "main.py",
    line=30,
    bp_type=BreakpointType.LOG,
    log_message="Player position: {pos}",
)
```

### 移除断点

```python
# 移除单个断点
debugger.remove_breakpoint(bp.id)

# 移除所有断点
debugger.clear_breakpoints()
```

### 切换断点状态

```python
# 禁用断点
debugger.toggle_breakpoint(bp.id, enabled=False)

# 启用断点
debugger.toggle_breakpoint(bp.id, enabled=True)
```

---

## 变量监视

### 添加监视

```python
# 监视变量
watch = debugger.add_watch("player_health", expression="player.health")

# 监视表达式
watch = debugger.add_watch("distance", expression="calc_distance(pos1, pos2)")
```

### 获取监视值

```python
variables = debugger.get_variables()

for name, value in variables.items():
    print(f"{name} = {value}")
```

### 移除监视

```python
debugger.remove_watch("player_health")
```

---

## 执行控制

### 单步执行

```python
# 单步跳过（Step Over）
debugger.step_over()

# 单步进入（Step Into）
debugger.step_into()

# 单步跳出（Step Out）
debugger.step_out()
```

### 继续和暂停

```python
# 继续执行
debugger.continue_execution()

# 暂停执行
debugger.pause()
```

---

## 调用栈查看

```python
stack = debugger.get_call_stack()

for frame in stack:
    print(f"文件: {frame.file}")
    print(f"函数: {frame.function}")
    print(f"行号: {frame.line}")
    print(f"局部变量: {frame.locals}")
    print("---")
```

---

## 日志捕获

### 获取日志

```python
logs = debugger.get_logs()

for log in logs:
    print(f"[{log.level}] {log.message}")
```

### 分析日志

```python
result = debugger.analyze_logs()

print(f"错误数: {result['errors']}")
print(f"警告数: {result['warnings']}")

for pattern in result['patterns']:
    print(f"模式: {pattern['type']}")
    print(f"次数: {pattern['count']}")
    print(f"建议: {pattern['suggestion']}")
```

---

## 热重载

### 重载单个文件

```python
success = debugger.hot_reload("scripts/main.py")

if success:
    print("文件已重新加载")
```

### 重载所有文件

```python
results = debugger.hot_reload_all()

for file, success in results.items():
    status = "成功" if success else "失败"
    print(f"{file}: {status}")
```

---

## 错误模式识别

调试器可以自动识别常见错误模式：

| 模式 | 描述 | 建议 |
|------|------|------|
| `KeyError` | 字典键不存在 | 检查键名是否正确 |
| `AttributeError` | 属性不存在 | 检查对象类型 |
| `TypeError` | 类型错误 | 检查参数类型 |
| `NameError` | 名称未定义 | 检查变量是否声明 |
| `ImportError` | 导入失败 | 检查模块路径 |

---

## CLI 命令

### 启动调试会话

```bash
mc-agent debug attach --pid 12345
```

### 设置断点

```bash
mc-agent debug break --file main.py --line 42
```

### 查看变量

```bash
mc-agent debug vars
```

### 查看调用栈

```bash
mc-agent debug stack
```

### 单步执行

```bash
mc-agent debug step       # 单步跳过
mc-agent debug step-into  # 单步进入
mc-agent debug step-out   # 单步跳出
mc-agent debug continue   # 继续执行
```

---

## 最佳实践

### 1. 使用条件断点

避免频繁暂停，只在特定条件下触发：

```python
debugger.set_breakpoint(
    "combat.py",
    line=100,
    condition="enemy.health < 20",  # 只在敌人血量低于 20 时触发
)
```

### 2. 合理使用日志断点

在需要追踪但不希望暂停的地方使用日志断点：

```python
debugger.set_breakpoint(
    "movement.py",
    line=50,
    bp_type=BreakpointType.LOG,
    log_message="Position: {x}, {y}, {z}",
)
```

### 3. 使用监视表达式

监视复杂表达式以便快速诊断：

```python
debugger.add_watch("total_damage", "base_damage * multiplier + bonus")
```

### 4. 定期分析日志

在开发过程中定期分析日志，及早发现问题：

```python
result = debugger.analyze_logs()

if result['errors'] > 0:
    print("发现错误，请检查：")
    for pattern in result['patterns']:
        if pattern['type'] == 'error':
            print(f"  - {pattern['message']}")
```

---

## 常见问题

### Q: 无法附加到游戏进程？

检查：
1. 游戏是否正在运行
2. 进程 ID 是否正确
3. 是否有足够的权限

### Q: 断点不触发？

确保：
1. 断点所在行是可执行代码
2. 断点已启用
3. 条件表达式语法正确

### Q: 热重载失败？

可能原因：
1. 文件有语法错误
2. 模块依赖发生变化
3. 游戏版本不支持

---

## 参考链接

- [ModSDK 增强技能使用指南](./modsdk-enhanced.md)
- [代码分析器使用指南](./code-analysis.md)
- [项目模板使用指南](./templates.md)

---

*文档版本: v1.45.0*
*最后更新: 2026-03-24*