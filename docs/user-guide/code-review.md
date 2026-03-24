# 代码审查

MC-Agent-Kit 的代码审查功能帮助你发现代码问题并提供改进建议。

## 基本用法

### 审查文件

```bash
# 审查单个文件
mc-llm review main.py

# 审查多个文件
mc-llm review *.py

# 审查目录
mc-llm review behavior_pack/scripts/
```

### 审查代码片段

```bash
# 从 stdin 读取
echo "def hello(): print('hello')" | mc-llm review -

# 直接指定代码
mc-llm review --code "def test(): pass"
```

## 审查结果

### 结果格式

```
✅ Code Review Passed (Score: 85, Grade: B)

Issues (2):

  ⚠️ [style] Line 15: Missing docstring for function
     Suggestion: Add a docstring explaining the function's purpose

  💡 [hint] Line 20: Consider using get() for safer dict access
     Suggestion: Use dict.get('key', default) instead of dict['key']

Summary: Good code structure with minor improvements possible.
```

### 分数和等级

| 分数范围 | 等级 | 说明 |
|----------|------|------|
| 90-100 | A | 优秀 |
| 80-89 | B | 良好 |
| 70-79 | C | 及格 |
| 60-69 | D | 需改进 |
| 0-59 | F | 不合格 |

### 问题严重程度

| 图标 | 级别 | 说明 |
|------|------|------|
| 🔴 | critical | 严重问题，必须修复 |
| ❌ | error | 错误，应该修复 |
| ⚠️ | warning | 警告，建议修复 |
| ℹ️ | info | 信息，可选修复 |
| 💡 | hint | 提示，改进建议 |

## 审查类别

### 安全审查

检测潜在的安全问题：

- 敏感信息泄露
- 不安全的输入处理
- 危险函数调用（eval, exec）

### 性能审查

检测性能问题：

- 低效循环
- 重复计算
- 内存泄漏风险

### ModSDK 规范

检测 ModSDK 特定问题：

- 客户端/服务端 API 混用
- 缺少必要的事件注销
- 不正确的 API 调用

### 代码风格

检测代码风格问题：

- 命名规范
- 注释缺失
- 代码结构

## 配置选项

### 最低分数

```bash
# 设置最低通过分数
mc-llm review main.py --min-score 80
```

### 审查类别

```bash
# 只审查安全和性能
mc-llm review main.py --categories security,performance

# 审查所有类别
mc-llm review main.py --categories all
```

### 最大建议数

```bash
# 限制建议数量
mc-llm review main.py --max-suggestions 5
```

## 输出格式

### 文本格式（默认）

```bash
mc-llm review main.py --format text
```

### JSON 格式

```bash
mc-llm review main.py --format json
```

```json
{
  "passed": true,
  "score": 85,
  "grade": "B",
  "issues": [
    {
      "severity": "warning",
      "category": "style",
      "line": 15,
      "message": "Missing docstring",
      "suggestion": "Add a docstring"
    }
  ],
  "summary": "Good code structure"
}
```

### Markdown 格式

```bash
mc-llm review main.py --format markdown
```

## 工作流集成

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: mc-review
        name: MC-Agent-Kit Review
        entry: mc-llm review
        language: system
        types: [python]
```

### CI/CD 集成

```yaml
# .github/workflows/review.yml
name: Code Review
on: [push, pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install MC-Agent-Kit
        run: pip install mc-agent-kit
      - name: Run Review
        run: mc-llm review behavior_pack/scripts/ --min-score 70
```

## 常见问题处理

### 问题：缺少文档字符串

```python
# ❌ 问题代码
def process_event(args):
    return args.get('data')

# ✅ 修复后
def process_event(args):
    """处理事件数据
    
    Args:
        args: 事件参数字典
        
    Returns:
        事件数据或 None
    """
    return args.get('data')
```

### 问题：不安全的字典访问

```python
# ❌ 问题代码
value = data['key']  # 可能抛出 KeyError

# ✅ 修复后
value = data.get('key', default_value)  # 安全访问
```

### 问题：ModSDK API 混用

```python
# ❌ 问题代码（在服务端使用了客户端 API）
# ServerSystem 中
self.CreateUIScreen(...)  # 这是客户端 API

# ✅ 修复后
# 确保在正确的环境中使用正确的 API
# 服务端：使用 ServerSystem 的方法
# 客户端：使用 ClientSystem 的方法
```

## 下一步

- 🐛 [错误诊断](./error-diagnosis.md) - 诊断和修复错误
- 🔧 [自定义提示词](./custom-prompts.md) - 自定义审查规则
- 💡 [最佳实践](../best-practices.md) - 代码质量建议

---

*最后更新: 2026-03-25*