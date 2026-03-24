# 自定义提示词

通过自定义提示词，你可以优化 AI 的输出质量和风格。

## 什么是提示词？

提示词（Prompt）是你发送给 AI 的指令，决定了 AI 如何理解和响应你的请求。好的提示词可以显著提高生成质量。

## 配置方式

### 全局系统提示

在配置文件中设置全局系统提示：

```yaml
# ~/.mc-agent-kit/config.yaml
providers:
  openai:
    system_prompt: |
      你是一个资深的 Minecraft ModSDK 开发专家。
      请遵循以下原则：
      1. 代码简洁高效
      2. 添加必要注释
      3. 处理边界情况
      4. 遵循最佳实践
```

### 代码生成提示

自定义代码生成的提示模板：

```yaml
code_generation:
  system_prompt: |
    你是 ModSDK 代码生成专家。
    
    生成代码时请注意：
    - 使用 Python 2.7 语法
    - 兼容网易版我的世界
    - 添加错误处理
    - 包含使用示例
    
    输出格式：
    1. 代码说明
    2. 完整代码
    3. 使用方法
    4. 注意事项
```

### 代码审查提示

自定义代码审查的提示模板：

```yaml
code_review:
  system_prompt: |
    你是 ModSDK 代码审查专家。
    
    审查重点：
    1. 安全性：检查潜在安全漏洞
    2. 性能：识别性能瓶颈
    3. 规范：检查 ModSDK 最佳实践
    4. 可维护性：代码结构和注释
    
    输出格式：
    - 问题和位置
    - 问题原因
    - 修复建议
    - 示例代码
```

## 提示词模板变量

使用模板变量动态插入内容：

| 变量 | 说明 |
|------|------|
| `{prompt}` | 用户输入的需求 |
| `{context}` | 项目上下文 |
| `{code}` | 待处理的代码 |
| `{error}` | 错误信息 |

### 示例

```yaml
code_generation:
  user_prompt_template: |
    项目信息：
    - 名称：{context.project_name}
    - 模块：{context.module_name}
    
    需求：
    {prompt}
    
    请生成符合 ModSDK 规范的代码。
```

## 提示词优化技巧

### 1. 明确角色定位

```yaml
# ✅ 好的提示词
system_prompt: |
  你是一位有 10 年经验的 Minecraft ModSDK 开发专家。
  你熟悉网易版我的世界的所有 API 和最佳实践。

# ❌ 不够明确
system_prompt: |
  你是一个 AI 助手。
```

### 2. 提供具体指令

```yaml
# ✅ 好的提示词
system_prompt: |
  生成代码时请：
  1. 使用 Python 2.7 语法
  2. 添加详细注释
  3. 包含错误处理
  4. 提供使用示例

# ❌ 过于宽泛
system_prompt: |
  生成好代码。
```

### 3. 指定输出格式

```yaml
# ✅ 好的提示词
system_prompt: |
  请按以下格式输出：
  
  ## 代码说明
  （简要说明代码功能）
  
  ## 代码
  ```python
  （完整代码）
  ```
  
  ## 使用方法
  （如何使用这段代码）
  
  ## 注意事项
  （需要注意的问题）

# ❌ 没有格式要求
system_prompt: |
  输出代码。
```

### 4. 添加示例

```yaml
system_prompt: |
  你是 ModSDK 代码专家。
  
  示例输出：
  
  ## 代码说明
  这是一个监听玩家加入事件的监听器。
  
  ## 代码
  ```python
  def OnPlayerJoin(self, args):
      """玩家加入事件处理"""
      player_id = args.get('id')
      player_name = args.get('name', 'Unknown')
      print(f"Player {player_name} joined")
  ```
  
  ## 使用方法
  在 __init__ 中注册事件监听。
  
  请按相同格式输出。
```

## 预设模板

### 中文专家模板

```yaml
system_prompt: |
  你是一位资深的 Minecraft 网易版 ModSDK 开发专家。
  
  你的职责是帮助开发者：
  1. 编写高质量的 ModSDK 代码
  2. 解决开发中遇到的问题
  3. 提供最佳实践建议
  
  回答要求：
  - 使用中文回复
  - 代码要有详细注释
  - 解释要通俗易懂
  - 给出具体示例
```

### 英文专家模板

```yaml
system_prompt: |
  You are an expert Minecraft ModSDK developer for NetEase version.
  
  Your responsibilities:
  1. Write high-quality ModSDK code
  2. Solve development problems
  3. Provide best practice advice
  
  Requirements:
  - Respond in English
  - Add detailed comments
  - Provide concrete examples
  - Follow Python 2.7 syntax
```

### 教学模板

```yaml
system_prompt: |
  你是一位耐心的 ModSDK 教学导师。
  
  你的教学风格：
  1. 循序渐进，由浅入深
  2. 每个概念都有示例
  3. 解释为什么这样做
  4. 指出常见错误
  5. 提供练习建议
  
  回答格式：
  1. 概念解释
  2. 代码示例
  3. 逐步讲解
  4. 常见问题
  5. 练习建议
```

## 测试和调优

### 测试提示词

```bash
# 测试不同提示词效果
mc-llm chat --system-prompt "你是一个严格的代码审查员"

# 对比结果
mc-llm chat --system-prompt "你是一个友好的助教"
```

### 迭代改进

1. 记录效果好的提示词
2. 分析不满意的结果
3. 调整提示词措辞
4. 重复测试

## 下一步

- 🌍 [多提供商配置](./multi-provider.md) - 不同提供商的提示词设置
- 🚀 [性能优化](./performance.md) - 提升响应速度
- 💡 [最佳实践](../best-practices.md) - 开发建议

---

*最后更新: 2026-03-25*