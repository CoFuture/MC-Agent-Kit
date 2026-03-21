# ModSDK 代码重构 Skill

提供 ModSDK 代码异味检测和重构建议功能。

## 工具说明

### mc_detect_smells

检测代码中的异味和问题。

**参数**:
- `code` (string): 源代码

**返回**: 检测到的代码异味列表，包含：
- `type`: 异味类型
- `message`: 描述信息
- `line`: 行号
- `severity`: 严重程度（info/minor/major/critical）
- `category`: 类别（naming/complexity/duplication/structure/modsdk/quality）
- `suggestion`: 修复建议

**示例**:
```
用户: 检查这段代码的问题
代码:
def f(x):
    for i in range(100):
        for j in range(100):
            for k in range(100):
                process(i,j,k)

助手: 检测到以下问题：

1. [minor] 第 1 行：函数名 'f' 过短
   建议：使用更具描述性的名称

2. [major] 第 2 行：嵌套过深 (3 层)
   建议：使用提前返回或提取嵌套逻辑到独立函数
```

### mc_suggest_refactor

根据代码异味生成重构建议。

**参数**:
- `code` (string): 源代码

**返回**: 重构建议列表，包含：
- `type`: 重构类型
- `message`: 描述信息
- `line`: 行号
- `original_code`: 原始代码
- `suggested_code`: 建议代码
- `explanation`: 解释说明

**示例**:
```
用户: 给我重构建议
助手: 重构建议：

1. [行 3] 指定具体的异常类型
   原始: except:
   建议: except Exception as e:
   解释：裸 except 会捕获所有异常，包括系统退出和键盘中断
```

### mc_analyze_complexity

分析代码复杂度。

**参数**:
- `code` (string): 源代码

**返回**: 复杂度分析报告，包含：
- `total_functions`: 函数总数
- `high_complexity_functions`: 高复杂度函数列表
- `max_nesting_depth`: 最大嵌套深度
- `suggestions`: 优化建议

## 支持的代码异味类型

### 命名问题
- `long_name`: 名称过长
- `short_name`: 名称过短
- `misleading_name`: 误导性命名

### 复杂度问题
- `long_function`: 函数过长
- `many_parameters`: 参数过多
- `deeply_nested`: 嵌套过深
- `high_complexity`: 圈复杂度过高

### ModSDK 特定
- `hardcoded_path`: 硬编码路径
- `magic_number`: 魔法数字
- `missing_error_handler`: 缺少错误处理
- `bare_except`: 裸 except
- `print_debug`: print 调试语句

### 代码质量
- `commented_code`: 注释掉的代码
- `todo_comment`: TODO 注释
- `missing_docstring`: 缺少文档字符串

## 使用场景

- 代码审查前检查
- 重构前分析
- 代码质量改进
- 学习最佳实践