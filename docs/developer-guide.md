# MC-Agent-Kit 开发者指南

> 版本: v1.0.0
> 最后更新: 2026-03-23

本文档为 MC-Agent-Kit 的开发者提供详细的开发指南，包括项目架构、开发流程、测试规范等内容。

---

## 目录

- [项目概述](#项目概述)
- [开发环境设置](#开发环境设置)
- [项目架构](#项目架构)
- [开发流程](#开发流程)
- [测试规范](#测试规范)
- [代码规范](#代码规范)
- [发布流程](#发布流程)

---

## 项目概述

MC-Agent-Kit 是一个 AI Agent 工具集，用于 Minecraft 网易版 ModSDK 开发。项目的核心目标是让 AI Agent 能够自主完成 ModSDK Addon 的开发闭环：

```
需求分析 → 代码开发 → 测试验证 → 迭代修复
```

### 核心能力

| 能力模块 | 形式 | 核心功能 |
|---------|------|----------|
| **知识检索** | Skill + CLI | API/事件文档检索、示例代码搜索 |
| **项目脚手架** | CLI | 创建标准 Addon 项目结构 |
| **游戏启动器** | CLI | 启动游戏+Addon、捕获日志 |
| **错误诊断** | Skill | 分析日志、定位错误、给出修复建议 |
| **代码生成** | Skill | 事件监听、API 调用等基础模板 |

---

## 开发环境设置

### 系统要求

- Python 3.13+
- uv 包管理器
- Git

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/mc-agent-kit.git
cd mc-agent-kit

# 2. 安装 uv（如果未安装）
pip install uv

# 3. 创建虚拟环境并安装依赖
uv sync --extra dev

# 4. 安装语义搜索依赖（可选）
uv sync --extra semantic
```

### 验证安装

```bash
# 运行测试
uv run pytest

# 运行 CLI
uv run mc-agent --help
```

---

## 项目架构

### 目录结构

```
MC-Agent-Kit/
├── .github/
│   └── workflows/           # GitHub Actions 工作流
├── docs/                    # 文档
│   ├── user/               # 用户文档
│   ├── en/                 # 英文文档
│   └── *.md                # 项目文档
├── examples/               # 示例项目
├── skills/                 # OpenClaw Skills
├── src/
│   ├── mc_agent_kit/      # 主包
│   │   ├── launcher/      # 游戏启动器
│   │   ├── knowledge/     # 知识库管理
│   │   ├── knowledge_base/ # 知识库数据模型
│   │   ├── generator/     # 代码生成
│   │   ├── scaffold/      # 项目脚手架
│   │   ├── execution/     # 代码执行
│   │   ├── autofix/       # 自动修复
│   │   ├── ux/            # 用户体验
│   │   ├── workflow/      # 端到端工作流
│   │   └── skills/        # Agent Skills
│   └── tests/             # 测试文件
│       ├── e2e/           # 端到端测试
│       ├── benchmark/     # 性能基准测试
│       └── *.py           # 单元测试
├── pyproject.toml         # 项目配置
├── LICENSE                # MIT 许可证
├── CHANGELOG.md           # 变更日志
└── CONTRIBUTING.md        # 贡献指南
```

### 核心模块说明

#### 1. launcher/ - 游戏启动器

- `addon_scanner.py`: 扫描 Addon 目录结构
- `config_generator.py`: 生成游戏配置文件
- `game_launcher.py`: 启动游戏进程
- `diagnoser.py`: 诊断启动问题
- `auto_fixer.py`: 自动修复配置问题

#### 2. knowledge/ - 知识库管理

- `knowledge_base.py`: 知识库主类
- `parsers/`: 文档解析器
  - `markdown_parser.py`: Markdown 解析
  - `code_extractor.py`: 代码示例提取
- `retrieval.py`: 知识检索

#### 3. knowledge_base/ - 知识库数据模型

- `models.py`: 数据模型定义
- `parser.py`: 文档解析
- `indexer.py`: 索引构建
- `retriever.py`: 检索器

#### 4. generator/ - 代码生成

- `code_gen.py`: 代码生成器
- `templates.py`: 模板管理
- `template_loader.py`: 自定义模板加载
- `lint.py`: 代码质量检查
- `quality_checker.py`: 质量检查器

#### 5. scaffold/ - 项目脚手架

- `creator.py`: 项目创建器
- `templates.py`: 项目模板

#### 6. autofix/ - 自动修复

- `diagnoser.py`: 错误诊断
- `fixer.py`: 自动修复器

#### 7. ux/ - 用户体验

- `enhanced.py`: 增强消息管理

#### 8. workflow/ - 端到端工作流

- `end_to_end.py`: 完整开发流程
- `cache.py`: 缓存管理
- `enhanced.py`: 增强工作流

#### 9. skills/ - Agent Skills

- `base.py`: Skill 基类
- `modsdk/`: ModSDK 相关 Skills
  - `api_search.py`: API 检索
  - `event_search.py`: 事件检索
  - `code_gen.py`: 代码生成
  - `debug.py`: 调试辅助

---

## 开发流程

### 分支管理

```
main (稳定版本)
  └── feature/* (功能分支)
  └── fix/* (修复分支)
  └── docs/* (文档分支)
```

### 开发步骤

1. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **编写代码**
   - 遵循代码规范
   - 添加类型注解
   - 编写文档字符串

3. **编写测试**
   ```bash
   # 为新功能编写测试
   # 测试文件放在 src/tests/
   ```

4. **运行测试**
   ```bash
   uv run pytest
   ```

5. **代码检查**
   ```bash
   uv run ruff check src/
   uv run mypy src/
   ```

6. **提交代码**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

7. **推送并创建 PR**
   ```bash
   git push origin feature/your-feature-name
   ```

---

## 测试规范

### 测试目录结构

```
src/tests/
├── test_*.py           # 单元测试
├── test_iteration_*.py # 迭代测试
├── e2e/               # 端到端测试
│   └── test_*.py
└── benchmark/         # 性能基准测试
    └── test_*.py
```

### 测试命名规范

- 测试文件: `test_<module_name>.py`
- 测试类: `Test<FeatureName>`
- 测试函数: `test_<scenario>`

### 测试覆盖要求

- 所有新代码必须有测试
- 测试覆盖率目标: 90%+
- 关键路径必须有测试覆盖

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest src/tests/test_launcher.py

# 运行并显示覆盖率
uv run pytest --cov=src/mc_agent_kit --cov-report=term-missing

# 运行端到端测试
uv run pytest src/tests/e2e/

# 运行性能基准测试
uv run pytest src/tests/benchmark/ -m benchmark
```

### 测试示例

```python
import pytest
from mc_agent_kit.launcher.addon_scanner import AddonScanner, AddonInfo


class TestAddonScanner:
    """AddonScanner 测试"""

    def test_scan_empty_directory(self, tmp_path):
        """测试扫描空目录"""
        scanner = AddonScanner(str(tmp_path))
        result = scanner.scan()
        assert result is None

    def test_scan_valid_addon(self, tmp_path):
        """测试扫描有效 Addon"""
        # 创建测试 Addon 结构
        bp_dir = tmp_path / "behavior_pack"
        bp_dir.mkdir()
        (bp_dir / "manifest.json").write_text('{"format_version": 2}')

        scanner = AddonScanner(str(tmp_path))
        result = scanner.scan()
        assert result is not None
        assert result.behavior_pack is not None
```

---

## 代码规范

### Python 版本

- 最低版本: Python 3.13
- 使用 Python 3.10+ 语法（如 `str | None`）

### 类型注解

```python
from typing import Any
from dataclasses import dataclass


def search_api(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """搜索 API 文档
    
    Args:
        query: 搜索关键词
        limit: 返回数量限制
        
    Returns:
        匹配的 API 列表
    """
    ...


@dataclass
class APIInfo:
    """API 信息"""
    name: str
    description: str
    module: str
    scope: str
```

### 文档字符串

使用 Google 风格的文档字符串：

```python
def diagnose_error(logs: str) -> DiagnosisResult:
    """诊断错误日志
    
    分析日志内容，识别错误类型，提供修复建议。
    
    Args:
        logs: 日志内容字符串
        
    Returns:
        DiagnosisResult 包含:
            - error_type: 错误类型
            - error_message: 错误信息
            - fix_suggestions: 修复建议列表
            
    Raises:
        ValueError: 当 logs 为空时
        
    Example:
        >>> result = diagnose_error("KeyError: 'speed'")
        >>> print(result.error_type)
        'KeyError'
    """
    ...
```

### 代码格式化

```bash
# 检查格式
uv run ruff format src/ --check

# 自动格式化
uv run ruff format src/
```

### Lint 检查

```bash
# 检查问题
uv run ruff check src/

# 自动修复
uv run ruff check src/ --fix

# 类型检查
uv run mypy src/
```

---

## 发布流程

### 版本号规范

遵循语义化版本规范：

- 主版本号: 不兼容的 API 变更
- 次版本号: 向后兼容的功能新增
- 修订号: 向后兼容的问题修复

### 发布步骤

1. **更新版本号**
   ```bash
   # 更新 pyproject.toml 中的 version
   ```

2. **更新 CHANGELOG.md**
   ```markdown
   ## [1.34.0] - 2026-03-23
   
   ### Added
   - 新功能描述
   
   ### Fixed
   - 修复描述
   ```

3. **提交变更**
   ```bash
   git add .
   git commit -m "chore: bump version to 1.34.0"
   ```

4. **创建标签**
   ```bash
   git tag v1.34.0
   git push origin v1.34.0
   ```

5. **创建 Release**
   - 在 GitHub 上创建 Release
   - CI/CD 自动发布到 PyPI

### CI/CD 流程

1. **Push/PR**: 运行测试和 lint 检查
2. **Release**: 自动构建并发布到 PyPI

---

## 常见问题

### Q: 如何添加新的 Skill?

1. 在 `src/mc_agent_kit/skills/modsdk/` 创建新文件
2. 继承 `BaseSkill` 类
3. 实现 `execute` 方法
4. 在 `__init__.py` 中导出
5. 在 `skills/` 目录创建 OpenClaw Skill 文档

### Q: 如何添加新的代码模板?

1. 在 `src/mc_agent_kit/generator/templates.py` 添加模板定义
2. 或在自定义模板目录创建 `.jinja2` 文件

### Q: 如何调试 CI/CD 问题?

1. 查看 GitHub Actions 日志
2. 本地运行相同的命令
3. 检查依赖版本

---

## 联系方式

- 提交 Issue: https://github.com/your-username/mc-agent-kit/issues
- 提交 PR: https://github.com/your-username/mc-agent-kit/pulls

---

*文档版本: v1.0.0*
*最后更新: 2026-03-23*