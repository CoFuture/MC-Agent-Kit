# 常见问题 (FAQ)

本页面收集了 MC-Agent-Kit 使用过程中的常见问题和解决方案。

## 安装问题

### Q: pip 安装速度很慢怎么办？

**A**: 使用国内镜像源加速：

```bash
pip install mc-agent-kit -i https://pypi.tuna.tsinghua.edu.cn/simple
```

或配置永久镜像：

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: Python 版本不兼容怎么办？

**A**: MC-Agent-Kit 需要 Python 3.13 或更高版本。使用以下方法管理多版本 Python：

```bash
# 使用 conda
conda create -n mc-agent python=3.13
conda activate mc-agent

# 或使用 pyenv
pyenv install 3.13
pyenv local 3.13
```

### Q: chromadb 安装失败？

**A**: chromadb 依赖较多系统库，可能需要安装额外依赖：

```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install

# Windows - 通常无需额外操作
# 如果失败，尝试安装 Visual Studio Build Tools
```

### Q: uv 找不到命令？

**A**: 确保 uv 已正确安装并添加到 PATH：

```bash
# 安装 uv
pip install uv

# 验证安装
uv --version
```

## CLI 使用问题

### Q: `mc-agent` 命令找不到？

**A**: 确保：

1. MC-Agent-Kit 已正确安装
2. Python Scripts 目录在 PATH 中
3. 重新打开终端窗口

```bash
# 验证安装
pip show mc-agent-kit

# 查看 Scripts 目录
pip show -f mc-agent-kit | grep Scripts
```

### Q: CLI 输出乱码？

**A**: 设置终端编码为 UTF-8：

```bash
# Windows CMD
chcp 65001

# PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 或使用 JSON 输出格式
mc-agent api -q "test" -f json
```

### Q: 命令执行报错？

**A**: 使用 `--help` 查看命令用法：

```bash
mc-agent --help
mc-agent api --help
mc-agent gen --help
```

## 知识库问题

### Q: 知识库搜索无结果？

**A**: 可能原因：

1. 知识库数据文件不存在
2. 搜索关键词不正确
3. 知识库未正确加载

```bash
# 检查知识库文件
ls data/knowledge_base.json

# 使用更通用的关键词
mc-agent api -q "get"
mc-agent event -q "on"
```

### Q: 如何更新知识库？

**A**: 知识库数据基于 `resources/docs/` 目录构建：

```bash
# 重新构建知识库
python build_knowledge_base.py
```

### Q: 知识库加载很慢？

**A**: 可以启用缓存或使用增量更新：

```python
# 启用缓存
from mc_agent_kit.knowledge import KnowledgeBase
kb = KnowledgeBase(cache_enabled=True)
```

## 代码生成问题

### Q: 生成的代码有语法错误？

**A**: 使用代码检查工具：

```bash
# 检查语法
python -m py_compile generated_code.py

# 使用 autofix 修复
mc-agent autofix -f generated_code.py -a diagnose
```

### Q: 模板找不到？

**A**: 查看可用模板列表：

```bash
mc-agent gen -a list
```

### Q: 如何添加自定义模板？

**A**: 创建模板文件并放置在模板目录：

```bash
# 创建模板目录
mkdir -p templates

# 创建自定义模板
# templates/my_template.yaml
```

模板文件格式：

```yaml
name: my_template
description: 我的自定义模板
params:
  - name: param1
    type: string
    required: true
template: |
  # 生成的代码
  def {{ param1 }}():
      pass
```

## 调试问题

### Q: 错误诊断不准确？

**A**: 提供更详细的错误日志：

```bash
# 使用完整的错误堆栈
mc-agent debug -l "$(cat error.log)"

# 从文件读取
mc-agent debug -f error.log
```

### Q: 自动修复失败？

**A**: 检查错误类型是否支持：

```bash
# 查看支持的错误类型
mc-agent debug -a patterns

# 预览修复
mc-agent autofix -f code.py -e error.log -a preview
```

## 性能问题

### Q: CLI 响应很慢？

**A**: 可能原因：

1. 知识库文件过大
2. 首次加载需要初始化
3. 系统资源不足

优化方法：

```bash
# 使用 JSON 输出（更快）
mc-agent api -q "test" -f json

# 减少返回结果数量
mc-agent api -q "test" -l 5
```

### Q: 内存占用过高？

**A**: 知识库数据可能占用较多内存。可以：

1. 使用增量加载
2. 减少缓存大小
3. 重启进程释放内存

## OpenClaw 集成问题

### Q: Skills 无法加载？

**A**: 确保 Skills 目录正确：

```bash
# 检查 Skills 目录
ls ~/.openclaw/skills/

# 复制 Skills
cp -r skills/* ~/.openclaw/skills/
```

### Q: Agent 不调用 Skills？

**A**: 检查 Skill 描述是否匹配：

1. 确保 SKILL.md 文件存在
2. 检查 description 是否清晰
3. 确保触发条件匹配用户请求

## ModSDK 开发问题

### Q: API 名称找不到？

**A**: ModSDK API 有命名规范：

```bash
# 搜索 API
mc-agent api -q "GetConfig"  # 服务端 API 通常以 Get 开头
mc-agent api -q "SetConfig"  # 设置 API 通常以 Set 开头
mc-agent api -q "Create"     # 创建类 API
```

### Q: 事件不触发？

**A**: 检查：

1. 事件名称大小写正确
2. 事件注册在正确的时机
3. 客户端/服务端事件区分

```bash
# 搜索事件
mc-agent event -q "OnCreate" -s server  # 服务端事件
mc-agent event -q "OnCreate" -s client  # 客户端事件
```

### Q: 代码运行报错？

**A**: 使用调试命令分析：

```bash
# 诊断错误
mc-agent debug -l "NameError: name 'GetConfig' is not defined"

# 自动修复
mc-agent autofix -f code.py -e error.log -a fix
```

## 其他问题

### Q: 如何报告 Bug？

**A**: 请在 GitHub Issues 提交：

1. 描述问题现象
2. 提供复现步骤
3. 附上错误日志和系统信息

### Q: 如何贡献代码？

**A**: 欢迎提交 Pull Request：

1. Fork 项目仓库
2. 创建功能分支
3. 编写代码和测试
4. 提交 PR

### Q: 如何获取帮助？

**A**: 通过以下方式：

1. 查看 [用户文档](getting-started.md)
2. 查看 [API 参考](api-reference.md)
3. 提交 GitHub Issue
4. 加入社区讨论

---

*最后更新：2026-03-22*