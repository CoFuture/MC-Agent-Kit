# 安装指南

本指南将帮助你在本地环境中安装和配置 MC-Agent-Kit。

## 系统要求

### 必需条件
- **Python**: 3.13 或更高版本
- **操作系统**: Windows 10/11（推荐）、macOS、Linux
- **内存**: 至少 4GB RAM（推荐 8GB+）
- **磁盘空间**: 至少 500MB

### 可选依赖
- **Minecraft 网易版**: 用于测试 Addon
- **Git**: 用于版本控制
- **Docker**: 用于容器化部署

## 安装方式

### 方式一：使用 pip 安装（推荐）

```bash
# 安装核心功能
pip install mc-agent-kit

# 安装 LLM 支持（可选）
pip install mc-agent-kit[llm]

# 安装语义检索支持（可选）
pip install mc-agent-kit[semantic]

# 安装所有功能
pip install mc-agent-kit[all]
```

### 方式二：使用 uv 安装

```bash
# 使用 uv 安装（更快）
uv pip install mc-agent-kit

# 安装所有功能
uv pip install mc-agent-kit[all]
```

### 方式三：从源码安装

```bash
# 克隆仓库
git clone https://github.com/your-repo/mc-agent-kit.git
cd mc-agent-kit

# 安装依赖
uv sync

# 安装项目
uv pip install -e .
```

## 验证安装

安装完成后，验证是否成功：

```bash
# 检查版本
mc-agent --version

# 查看帮助
mc-agent --help

# 测试核心命令
mc-kb status
```

## 配置 LLM 提供商

### OpenAI

```bash
# 设置 API Key
export OPENAI_API_KEY="sk-your-api-key"

# 或在配置文件中设置
# ~/.mc-agent-kit/config.yaml
```

```yaml
default_provider: openai
providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4o
    temperature: 0.7
```

### Anthropic Claude

```bash
# 设置 API Key
export ANTHROPIC_API_KEY="sk-ant-your-api-key"
```

```yaml
providers:
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-sonnet-4-20250514
```

### Google Gemini

```bash
# 设置 API Key
export GEMINI_API_KEY="your-api-key"
```

```yaml
providers:
  gemini:
    api_key: ${GEMINI_API_KEY}
    model: gemini-1.5-pro
```

### Ollama（本地部署）

```bash
# 安装 Ollama
# 参考: https://ollama.ai

# 拉取模型
ollama pull llama3

# 设置服务地址
export OLLAMA_BASE_URL="http://localhost:11434"
```

```yaml
providers:
  ollama:
    base_url: http://localhost:11434
    model: llama3
```

## 下一步

- 📖 [5 分钟上手](./quick-start.md) - 快速体验核心功能
- 🔧 [配置文件详解](./configuration.md) - 深入了解配置选项
- 🎯 [第一个项目](./first-project.md) - 创建你的第一个项目

## 常见问题

### 安装失败

**问题**: pip 安装时报错 `Failed to build wheel for xxx`

**解决**: 确保安装了编译工具：
- Windows: 安装 Visual Studio Build Tools
- macOS: 安装 Xcode Command Line Tools
- Linux: 安装 `build-essential` 和 `python3-dev`

### 命令未找到

**问题**: 运行 `mc-agent` 提示命令未找到

**解决**: 
1. 确认 Python Scripts 目录在 PATH 中
2. 重新安装: `pip install --force-reinstall mc-agent-kit`

### LLM 连接失败

**问题**: 使用 OpenAI/Anthropic 时连接失败

**解决**:
1. 检查 API Key 是否正确
2. 检查网络连接
3. 尝试设置代理: `export OPENAI_PROXY="http://your-proxy:port"`

---

*最后更新: 2026-03-25*