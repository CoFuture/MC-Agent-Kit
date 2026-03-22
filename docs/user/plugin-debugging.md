# 插件调试指南

本指南介绍如何调试 MC-Agent-Kit 插件，包括常见问题诊断、调试工具使用和错误处理。

## 目录

1. [调试工具](#调试工具)
2. [常见问题诊断](#常见问题诊断)
3. [日志分析](#日志分析)
4. [性能调试](#性能调试)
5. [错误处理](#错误处理)

---

## 调试工具

### 1. 内置调试插件

MC-Agent-Kit 提供了一个调试插件示例，位于 `examples/plugins/debug_plugin/`。

```python
from mc_agent_kit.plugin import PluginBase, PluginMetadata

class DebugPlugin(PluginBase):
    """调试辅助插件"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="debug",
            version="1.0.0",
            description="调试辅助工具"
        )
    
    def analyze_error(self, error_log: str) -> dict:
        """分析错误日志"""
        # 实现错误分析逻辑
        pass
```

### 2. 调试器集成

MC-Agent-Kit 提供了内置调试器支持：

```python
from mc_agent_kit.execution import Debugger, Breakpoint

# 创建调试器
debugger = Debugger()

# 设置断点
debugger.add_breakpoint(Breakpoint(
    file_path="plugin.py",
    line_number=42,
    condition="x > 10"  # 可选条件
))

# 添加变量监视
debugger.add_watch("my_variable")

# 启动调试会话
session = debugger.start_session("plugin.py")
```

### 3. 日志级别配置

配置日志级别以获取更详细的调试信息：

```python
import logging

# 设置全局日志级别
logging.basicConfig(level=logging.DEBUG)

# 设置特定模块日志级别
logging.getLogger("mc_agent_kit.plugin").setLevel(logging.DEBUG)
```

---

## 常见问题诊断

### 问题 1: 插件加载失败

**症状**: 插件无法加载或启动

**诊断步骤**:

1. 检查插件清单文件 `plugin.json` 格式：

```bash
mc-agent plugin validate /path/to/plugin
```

2. 检查依赖是否满足：

```python
from mc_agent_kit.plugin import DependencyManager

manager = DependencyManager()
report = manager.check_dependencies(plugin_info)
print(report)
```

3. 查看详细错误信息：

```python
from mc_agent_kit.plugin import PluginLoader

loader = PluginLoader()
result = loader.load_from_path("/path/to/plugin")
if not result.success:
    print(f"加载失败: {result.error}")
```

### 问题 2: 插件执行错误

**症状**: 插件执行时抛出异常

**诊断步骤**:

1. 检查错误日志：

```python
from mc_agent_kit.log_capture import LogAnalyzer

analyzer = LogAnalyzer()
patterns = analyzer.detect_error_patterns(log_content)
for pattern in patterns:
    print(f"错误类型: {pattern.category}")
    print(f"建议: {pattern.suggestion}")
```

2. 使用沙箱模式测试：

```python
from mc_agent_kit.plugin import PluginSandbox, SandboxConfig

config = SandboxConfig(permission_level="RESTRICTED")
sandbox = PluginSandbox(config)

# 在沙箱中执行代码
result = sandbox.execute(plugin_code)
```

### 问题 3: 插件冲突

**症状**: 多个插件之间存在冲突

**诊断步骤**:

1. 检查插件依赖关系：

```python
from mc_agent_kit.plugin import PluginLoader

loader = PluginLoader()
loader.load_directory("/path/to/plugins")

# 检查依赖冲突
conflicts = loader.registry.check_conflicts()
for conflict in conflicts:
    print(f"冲突: {conflict}")
```

2. 使用版本兼容性检查：

```python
from mc_agent_kit.plugin import VersionChecker

checker = VersionChecker()
report = checker.check_compatibility("1.0.0", ">=0.9.0,<2.0.0")
print(f"兼容性: {report.level}")
```

---

## 日志分析

### 1. 实时日志监控

```python
from mc_agent_kit.log_capture import LogAnalyzer, AlertSeverity

analyzer = LogAnalyzer()

# 添加告警规则
analyzer.add_alert_rule(
    pattern="ERROR",
    severity=AlertSeverity.ERROR,
    callback=lambda alert: print(f"告警: {alert.message}")
)

# 启动实时监控
analyzer.start_streaming()
```

### 2. 错误模式匹配

内置的错误模式包括：

| 错误类型 | 模式 | 建议 |
|---------|------|------|
| SyntaxError | `SyntaxError: .*` | 检查语法错误 |
| NameError | `NameError: name '.*' is not defined` | 检查变量定义 |
| TypeError | `TypeError: .*` | 检查类型匹配 |
| KeyError | `KeyError: '.*'` | 使用 `.get()` 方法 |
| AttributeError | `AttributeError: .*` | 使用 `getattr()` 方法 |

### 3. 日志统计

```python
stats = analyzer.get_statistics()
print(f"总日志数: {stats.total_count}")
print(f"错误数: {stats.error_count}")
print(f"警告数: {stats.warning_count}")
```

---

## 性能调试

### 1. 性能分析

```python
from mc_agent_kit.execution import PerformanceAnalyzer, PerformanceConfig

config = PerformanceConfig(
    enable_cpu_profiling=True,
    enable_memory_monitoring=True
)

analyzer = PerformanceAnalyzer(config)

# 分析代码性能
result = analyzer.profile(lambda: plugin.execute())
print(f"执行时间: {result.total_time_ms}ms")
print(f"内存使用: {result.memory_peak_mb}MB")
```

### 2. 热点分析

```python
# 获取热点函数
hotspots = analyzer.get_hotspots(top_n=10)
for func in hotspots:
    print(f"{func.name}: {func.total_time_ms}ms ({func.call_count} 次调用)")
```

### 3. 优化建议

```python
suggestions = analyzer.get_optimization_suggestions()
for sug in suggestions:
    print(f"建议: {sug.description}")
    print(f"预期收益: {sug.expected_improvement}")
```

---

## 错误处理

### 1. 自动诊断

```python
from mc_agent_kit.autofix import ErrorDiagnoser

diagnoser = ErrorDiagnoser()
result = diagnoser.diagnose(error_log)

print(f"错误类型: {result.error_type}")
print(f"修复建议: {result.suggestions}")
```

### 2. 自动修复

```python
from mc_agent_kit.autofix import AutoFixer

fixer = AutoFixer()

# 预览修复
diff = fixer.preview_fix(code, error_info)
print(diff)

# 应用修复
fixed_code = fixer.fix(code, error_info)
```

### 3. 错误恢复

```python
from mc_agent_kit.plugin import PluginManager

manager = PluginManager()

try:
    manager.execute("my_plugin", {"action": "run"})
except Exception as e:
    # 自动回滚到上一个稳定版本
    manager.rollback("my_plugin")
    manager.reload_plugin("my_plugin")
```

---

## 最佳实践

### 调试流程

1. **复现问题**: 确保问题可以稳定复现
2. **收集日志**: 启用详细日志记录
3. **分析错误**: 使用错误诊断工具
4. **定位代码**: 根据错误信息定位问题代码
5. **验证修复**: 测试修复是否有效

### 调试技巧

- 使用断点调试而非 `print` 语句
- 保持测试用例覆盖关键逻辑
- 使用版本控制系统回滚问题代码
- 记录调试过程以便后续参考

---

## 相关文档

- [插件开发指南](plugin-development.md)
- [热重载功能](hot-reload.md)
- [插件最佳实践](plugin-best-practices.md)
- [常见问题](faq.md)

---

*文档版本: v1.0.0*
*最后更新: 2026-03-22*