# 代码分析器使用指南

> 版本: v1.45.0
> 最后更新: 2026-03-24

---

## 概述

代码分析器提供了 Minecraft 网易版 ModSDK 代码的智能分析功能，包括：

- 语法检查
- API 使用分析
- 性能问题检测
- 最佳实践检查
- 代码风格检查
- 改进建议生成

---

## 快速开始

### 基本使用

```python
from mc_agent_kit.analysis.code_analyzer import create_code_analyzer

# 创建分析器实例
analyzer = create_code_analyzer()

# 分析代码
code = '''
def hello():
    print("Hello, World!")
'''

result = analyzer.analyze(code, "hello.py")

print(f"代码质量分数: {result.score}")
print(f"问题数: {len(result.issues)}")
```

---

## 代码分析

### 完整分析

```python
result = analyzer.analyze(code, "my_script.py")

# 基本信息
print(f"文件: {result.file}")
print(f"分数: {result.score}")
print(f"统计: {result.statistics}")

# 问题列表
for issue in result.issues:
    print(f"行 {issue.line}: [{issue.severity.value}] {issue.message}")
```

### 分析结果结构

```python
@dataclass
class AnalysisResult:
    file: str                    # 文件名
    issues: list[Issue]          # 问题列表
    suggestions: list[str]       # 改进建议
    score: float                 # 质量分数 (0-100)
    statistics: dict             # 统计信息
```

---

## 问题检测

### 问题类型

| 类型 | 描述 |
|------|------|
| `SYNTAX` | 语法错误 |
| `API_USAGE` | API 使用问题 |
| `PERFORMANCE` | 性能问题 |
| `SECURITY` | 安全问题 |
| `STYLE` | 代码风格问题 |
| `BEST_PRACTICE` | 最佳实践违反 |
| `COMPATIBILITY` | 兼容性问题 |

### 问题严重程度

| 级别 | 描述 |
|------|------|
| `ERROR` | 错误，必须修复 |
| `WARNING` | 警告，建议修复 |
| `INFO` | 信息提示 |
| `HINT` | 改进建议 |

### 检测问题

```python
issues = analyzer.detect_issues(code, "script.py")

for issue in issues:
    print(f"类型: {issue.type}")
    print(f"严重程度: {issue.severity}")
    print(f"行号: {issue.line}")
    print(f"消息: {issue.message}")
    if issue.suggestion:
        print(f"建议: {issue.suggestion}")
```

---

## 语法检查

### 检测语法错误

```python
broken_code = '''
def broken(
    print("missing parenthesis")
'''

result = analyzer.analyze(broken_code, "broken.py")

# 语法错误会降低分数到 0
assert result.score == 0.0

# 获取语法错误
syntax_errors = [i for i in result.issues if i.type == IssueType.SYNTAX]
```

---

## API 使用分析

### 查找 API 使用

```python
code = '''
entity_id = CreateEngineEntity("test", (0, 0, 0))
SetEntityPos(entity_id, 10, 20, 30)
health = GetEntityHealth(entity_id)
'''

usages = analyzer.find_api_usage(code, "script.py")

for usage in usages:
    print(f"API: {usage.name}")
    print(f"行号: {usage.line}")
    print(f"参数: {usage.arguments}")
```

### 检测错误 API 使用

```python
code = '''
# 参数数量错误
entity_id = CreateEngineEntity("test")  # 缺少位置参数
'''

result = analyzer.analyze(code, "script.py")

# 检测 API 使用问题
api_issues = [i for i in result.issues if i.type == IssueType.API_USAGE]
```

---

## 性能问题检测

### 常见性能问题

分析器可以检测以下性能问题：

| 问题 | 描述 | 建议 |
|------|------|------|
| 循环内字符串拼接 | 使用 `+=` 拼接字符串 | 使用 `join()` |
| 列表重复扩展 | 循环内 `list += [item]` | 使用 `append()` |
| 低效格式化 | 使用 `str.format()` | 使用 f-string |
| 重复计算 | 循环内重复计算 | 提取到循环外 |

### 示例

```python
inefficient_code = '''
items = []
for i in range(1000):
    items += [i]  # 低效
    result = "{}".format(i)  # 低效格式化
'''

issues = analyzer.detect_issues(inefficient_code, "slow.py")
perf_issues = [i for i in issues if i.type == IssueType.PERFORMANCE]

for issue in perf_issues:
    print(f"性能问题: {issue.message}")
    print(f"建议: {issue.suggestion}")
```

---

## 最佳实践检查

### 检测最佳实践违反

```python
bad_practice_code = '''
# 裸 except
try:
    do_something()
except:
    pass

# 使用 == None 而不是 is None
if x == None:
    pass

# 未使用的导入
import os
import sys  # 未使用
'''

issues = analyzer.detect_issues(bad_practice_code, "bad.py")

for issue in issues:
    if issue.type == IssueType.BEST_PRACTICE:
        print(f"最佳实践问题: {issue.message}")
```

### 常见最佳实践检查

| 检查项 | 描述 |
|--------|------|
| 裸 `except` | 应指定具体异常 |
| `== None` | 应使用 `is None` |
| 未使用导入 | 移除未使用的导入 |
| 硬编码路径 | 使用配置或常量 |
| 缺少文档字符串 | 添加函数文档 |

---

## 代码风格检查

### 检查代码风格

```python
style_code = '''
def foo():
    x=1+2  # 缺少空格
    y = [1,2,3]  # 逗号后缺少空格
'''

issues = analyzer.detect_issues(style_code, "style.py")

style_issues = [i for i in issues if i.type == IssueType.STYLE]
```

---

## 改进建议

### 生成改进建议

```python
code = '''
x = None
if x == None:
    print("is none")
'''

suggestions = analyzer.suggest_improvements(code, "script.py")

for suggestion in suggestions:
    print(f"建议: {suggestion}")
```

---

## 代码质量评分

### 分数计算规则

代码质量分数 (0-100) 基于以下因素：

| 因素 | 权重 |
|------|------|
| 语法正确性 | 基础分 |
| 问题数量 | 扣分 |
| 问题严重程度 | 加权扣分 |
| 代码复杂度 | 调整 |

### 分数等级

| 分数 | 等级 | 描述 |
|------|------|------|
| 90-100 | A | 优秀 |
| 80-89 | B | 良好 |
| 70-79 | C | 一般 |
| 60-69 | D | 较差 |
| 0-59 | F | 需要改进 |

### 获取分数

```python
result = analyzer.analyze(code, "script.py")

if result.score >= 80:
    print("代码质量良好")
elif result.score >= 60:
    print("代码需要改进")
else:
    print("代码质量较差，请修复问题")
```

---

## 严格模式

启用严格模式可以检测更多问题：

```python
strict_analyzer = create_code_analyzer(strict_mode=True)

result = strict_analyzer.analyze(code, "script.py")
# 严格模式会检测更多潜在问题
```

---

## CLI 命令

### 分析单个文件

```bash
mc-agent analyze script.py
```

### 分析目录

```bash
mc-agent analyze ./scripts/
```

### 指定输出格式

```bash
mc-agent analyze script.py --format json
mc-agent analyze script.py --format markdown
```

### 严格模式

```bash
mc-agent analyze script.py --strict
```

---

## 最佳实践

### 1. 定期分析代码

在开发过程中定期分析代码，及早发现问题：

```python
# 在每次保存文件后分析
result = analyzer.analyze(code, "my_script.py")
if result.issues:
    print("发现问题，请检查")
```

### 2. 关注高优先级问题

优先修复 ERROR 级别的问题：

```python
for issue in result.issues:
    if issue.severity == IssueSeverity.ERROR:
        print(f"必须修复: {issue.message}")
```

### 3. 结合代码生成器使用

分析生成的代码并优化：

```python
from mc_agent_kit.skills.modsdk_enhanced import create_modsdk_skill

skill = create_modsdk_skill()
entity = skill.generate_entity("TestMob")

# 分析生成的代码
result = analyzer.analyze(entity.script_code, "entity.py")
print(f"生成代码质量分数: {result.score}")
```

### 4. 集成到开发流程

将代码分析集成到开发流程：

```bash
# 在 git pre-commit hook 中运行
mc-agent analyze ./scripts/ --fail-on-error
```

---

## 常见问题

### Q: 分析结果不准确？

尝试启用严格模式：
```python
analyzer = create_code_analyzer(strict_mode=True)
```

### Q: 检测到太多警告？

过滤只关注 ERROR 级别：
```python
errors = [i for i in result.issues if i.severity == IssueSeverity.ERROR]
```

### Q: 想要自定义检查规则？

目前支持的标准检查规则。自定义规则功能计划在后续版本中提供。

---

## 参考链接

- [ModSDK 增强技能使用指南](./modsdk-enhanced.md)
- [调试器使用指南](./debugger.md)
- [项目模板使用指南](./templates.md)

---

*文档版本: v1.45.0*
*最后更新: 2026-03-24*