# 安装指南

本指南详细说明如何安装和配置 MC-Agent-Kit。

## 系统要求

- **操作系统**：Windows 10/11、macOS 10.15+、Linux
- **Python 版本**：3.13 或更高版本
- **包管理器**：pip 或 uv（推荐）

## 安装方式

### 方式一：使用 pip 安装

```bash
# 基础安装
pip install mc-agent-kit

# 安装开发依赖
pip install mc-agent-kit[dev]

# 安装知识库依赖（向量搜索功能）
pip install mc-agent-kit[knowledge]

# 完整安装
pip install mc-agent-kit[all]
```

### 方式二：使用 uv 安装（推荐）

uv 是更快的 Python 包管理器：

```bash
# 安装 uv
pip install uv

# 基础安装
uv pip install mc-agent-kit

# 完整安装
uv pip install mc-agent-kit[all]
```

### 方式三：从源码安装

```bash
# 克隆仓库
git clone https://github.com/your-repo/MC-Agent-Kit.git
cd MC-Agent-Kit

# 安装依赖
uv pip install -e ".[all]"
```

## 验证安装

### 检查命令行工具

```bash
# 查看版本
mc-agent --help

# 列出 Skills
mc-agent list
```

### 检查 Python 模块

```python
# 在 Python 中导入
from mc_agent_kit import knowledge_base, skills
print("MC-Agent-Kit 已成功安装！")
```

## 依赖说明

### 核心依赖

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | >=3.13 | 运行环境 |
| Jinja2 | >=3.1.0 | 模板引擎 |

### 开发依赖（可选）

| 依赖 | 版本 | 说明 |
|------|------|------|
| pytest | >=8.0.0 | 测试框架 |
| pytest-asyncio | >=0.23.0 | 异步测试支持 |
| ruff | >=0.3.0 | 代码格式化和检查 |
| mypy | >=1.8.0 | 类型检查 |

### 知识库依赖（可选）

| 依赖 | 版本 | 说明 |
|------|------|------|
| chromadb | >=0.5.0 | 向量数据库 |
| sentence-transformers | >=3.0.0 | 文本向量化 |
| llama-index | >=0.12.0 | RAG 框架 |

## 配置 OpenClaw Skills

MC-Agent-Kit 提供了 OpenClaw Skills，让 AI Agent 能够自动调用工具。

### 安装 Skills

```bash
# 复制 Skills 到 OpenClaw 目录
cp -r skills/* ~/.openclaw/skills/
```

### 验证 Skills

在 OpenClaw 中运行：

```
列出所有可用的 ModSDK Skills
```

## 常见问题

### 问题：pip 安装速度慢

**解决方案**：使用国内镜像源

```bash
pip install mc-agent-kit -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题：uv 找不到命令

**解决方案**：确保 uv 已添加到 PATH

```bash
# 检查 uv 是否安装
uv --version

# 如果未安装，使用 pip 安装
pip install uv
```

### 问题：Python 版本不兼容

**解决方案**：使用 pyenv 或 conda 管理多版本 Python

```bash
# 使用 conda 创建 Python 3.13 环境
conda create -n mc-agent python=3.13
conda activate mc-agent
```

### 问题：chromadb 安装失败

**解决方案**：chromadb 依赖较多，可能需要安装系统依赖

```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install

# Windows
# 通常无需额外操作
```

## 下一步

- 阅读 [配置指南](configuration.md) 了解如何配置项目
- 阅读 [快速入门](getting-started.md) 开始使用

---

*最后更新：2026-03-22*