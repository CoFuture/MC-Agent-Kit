# 内存优化指南

> MC-Agent-Kit 提供了一套完整的内存分析和优化工具，帮助开发者识别和解决 ModSDK Addon 中的内存问题。

## 目录

1. [快速开始](#快速开始)
2. [内存分析工具](#内存分析工具)
3. [常见内存问题](#常见内存问题)
4. [优化技巧](#优化技巧)
5. [最佳实践](#最佳实践)

---

## 快速开始

### 使用 CLI 分析 Addon

```bash
# 分析 Addon 内存问题
mc-agent launcher analyze --addon-path ./my-addon

# 以 JSON 格式输出
mc-agent launcher analyze --addon-path ./my-addon --format json

# 获取内存优化技巧
mc-agent launcher tips
```

### 使用 Python API

```python
from mc_agent_kit.launcher.auto_fixer import analyze_addon_memory, get_memory_optimization_tips

# 分析 Addon
report = analyze_addon_memory("./my-addon")

# 检查结果
if report.has_critical_issues:
    print(f"发现 {report.critical_issues} 个严重问题")
    for suggestion in report.suggestions:
        if suggestion.severity.value in ("critical", "high"):
            print(f"  - {suggestion.title}: {suggestion.description}")

# 获取优化技巧
tips = get_memory_optimization_tips()
for tip in tips:
    print(f"[{tip['category']}] {tip['tip']}")
```

---

## 内存分析工具

### MemoryAutoFixer

内存自动修复器可以分析 Addon 的资源文件，识别潜在的内存问题。

```python
from mc_agent_kit.launcher.auto_fixer import MemoryAutoFixer

fixer = MemoryAutoFixer("./my-addon")
report = fixer.analyze()

# 报告属性
print(f"总问题数: {report.total_issues}")
print(f"严重问题: {report.critical_issues}")
print(f"可自动修复: {report.auto_fixable_issues}")

# 修复建议
for suggestion in report.suggestions:
    print(f"类型: {suggestion.fix_type.value}")
    print(f"严重程度: {suggestion.severity.value}")
    print(f"标题: {suggestion.title}")
    print(f"描述: {suggestion.description}")
    print(f"位置: {suggestion.location}")
    if suggestion.estimated_savings:
        print(f"预计节省: {suggestion.estimated_savings}")
```

### 分析器类型

| 分析器 | 功能 | 检测的问题 |
|--------|------|-----------|
| TextureAnalyzer | 纹理文件分析 | 大纹理、非标准尺寸 |
| ModelAnalyzer | 模型文件分析 | 复杂模型、顶点过多 |
| ScriptAnalyzer | 脚本文件分析 | 大脚本、性能问题 |

---

## 常见内存问题

### 1. 纹理问题

#### 大纹理
**问题**: 纹理尺寸超过 1024x1024 像素

**影响**: 
- 占用大量显存和内存
- 加载时间变长
- 可能导致崩溃

**解决方案**:
- 使用 256x256 或 512x512 尺寸
- 使用纹理压缩工具
- 合并小纹理到纹理图集

#### 非标准尺寸
**问题**: 纹理尺寸不是 2 的幂次

**影响**:
- GPU 处理效率低
- 可能出现渲染问题

**解决方案**:
- 使用 16, 32, 64, 128, 256, 512 等尺寸
- 使用图像编辑工具调整

### 2. 模型问题

#### 高复杂度模型
**问题**: 模型顶点数超过 1000

**影响**:
- 渲染性能下降
- 内存占用增加
- 加载时间变长

**解决方案**:
- 使用 Blockbench 简化模型
- 删除不可见的面
- 使用 LOD 技术

### 3. 脚本问题

#### 大脚本文件
**问题**: 脚本文件超过 500 行

**影响**:
- 内存占用增加
- 维护困难
- 可能隐藏性能问题

**解决方案**:
- 将相关功能拆分到独立模块
- 使用类封装相关逻辑
- 移除调试代码

#### 全局变量过多
**问题**: 使用大量全局变量

**影响**:
- 可能导致内存泄漏
- 代码难以维护

**解决方案**:
- 使用类或模块封装
- 使用配置对象

---

## 优化技巧

### 纹理优化

| 技巧 | 说明 |
|------|------|
| 使用标准尺寸 | 16, 32, 64, 128, 256, 512 |
| 限制纹理大小 | 不超过 1024x1024 |
| 使用纹理图集 | 合并小纹理减少切换开销 |
| 压缩纹理 | 使用 PNG 压缩工具 |

### 模型优化

| 技巧 | 说明 |
|------|------|
| 限制顶点数 | 每个模型不超过 1000 顶点 |
| 删除隐藏面 | 移除不可见的立方体 |
| 使用 LOD | 远距离使用简化模型 |
| 合并相似模型 | 减少模型数量 |

### 脚本优化

| 技巧 | 说明 |
|------|------|
| 拆分大文件 | 每个文件不超过 500 行 |
| 使用对象池 | 复用频繁创建的对象 |
| 避免全局变量 | 使用类或模块封装 |
| 及时清理资源 | 在不需要时释放引用 |

---

## 最佳实践

### 1. 开发阶段

- 定期运行内存分析
- 使用版本控制跟踪变更
- 测试不同设备上的性能

### 2. 发布前检查

```bash
# 运行内存分析
mc-agent launcher analyze --addon-path ./my-addon

# 检查结果
# - 确保没有严重问题
# - 解决中等问题
# - 记录低优先级问题
```

### 3. 持续优化

- 监控游戏性能
- 收集用户反馈
- 定期更新优化

---

## 参考资源

- [Minecraft 性能优化指南](https://mc.163.com/developer/)
- [Blockbench 模型优化](https://blockbench.net/)
- [Python 性能优化](https://wiki.python.org/moin/PythonSpeed)

---

*最后更新: 2026-03-22*