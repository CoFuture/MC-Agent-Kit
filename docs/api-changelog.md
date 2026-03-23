# MC-Agent-Kit API 变更日志

> 版本: v1.0.0
> 最后更新: 2026-03-23

本文档记录 MC-Agent-Kit API 的变更历史，包括新增、修改、废弃和移除的 API。

---

## 变更类型说明

| 类型 | 说明 |
|------|------|
| ✨ Added | 新增 API |
| 🔧 Changed | 修改 API（可能影响兼容性） |
| ⚠️ Deprecated | 废弃 API（将在未来版本移除） |
| ❌ Removed | 移除 API |
| 🐛 Fixed | 修复 API 问题 |

---

## [v1.34.0] - 2026-03-23

### ✨ Added

#### CI/CD 集成

- 新增 `.github/workflows/ci.yml` CI/CD 工作流
  - 自动测试（支持覆盖率报告）
  - Ruff 代码检查
  - MyPy 类型检查
  - 自动构建和发布到 PyPI

#### 文档

- 新增 `docs/developer-guide.md` 开发者指南
- 新增 `docs/error-codes.md` 错误代码参考
- 新增 `docs/api-changelog.md` API 变更日志

---

## [v1.33.0] - 2026-03-23

### 🔧 Changed

#### 类型检查

- 核心模块启用严格类型检查
- 修复 327 个 mypy 类型错误
- 添加 `types-PyYAML` 依赖

#### 受影响的模块

- `mc_agent_kit.ux.enhanced`: 修复 MESSAGE_TEMPLATES 类型声明
- `mc_agent_kit.autofix.fixer`: 修复 Callable 导入
- `mc_agent_kit.launcher.*`: 添加变量类型注解
- `mc_agent_kit.knowledge_base.*`: 添加返回类型注解
- `mc_agent_kit.generator.lint`: 添加类型注解
- `mc_agent_kit.skills.base`: 添加方法类型注解

---

## [v1.32.0] - 2026-03-23

### ✨ Added

#### 端到端测试

- 新增 `src/tests/e2e/test_workflow_e2e.py`
  - `TestSearchDocsE2E`: 文档搜索测试
  - `TestCreateProjectE2E`: 项目创建测试
  - `TestDiagnoseE2E`: 诊断流程测试
  - `TestWorkflowE2E`: 完整工作流测试

#### 性能基准测试

- 新增 `src/tests/benchmark/test_performance.py`
  - 知识搜索性能基准
  - 项目创建性能基准
  - 代码生成性能基准

#### 文档国际化

- 新增 `docs/en/README.md` 英文 README
- 新增 `docs/en/VISION.md` 英文愿景文档
- 新增 `docs/en/PRINCIPLES.md` 英文原则文档

---

## [v1.31.0] - 2026-03-23

### ✨ Added

#### 工作流文档

- 新增 `docs/user/workflow-guide.md` 工作流使用指南

#### CLI 增强

- `workflow run` 命令新增选项：
  - `--retry <n>`: 重试次数
  - `--retry-policy <linear|exponential>`: 重试策略
  - `--progress`: 启用进度显示
  - `--locale <zh_CN|en_US|ja_JP|ko_KR>`: 语言设置

#### 本地化

- 新增日语 (`ja_JP`) 消息模板
- 新增韩语 (`ko_KR`) 消息模板

---

## [v1.30.0] - 2026-03-23

### ✨ Added

#### 工作流增强

- 新增 `RetryConfig` 重试配置类
- 新增 `RetryPolicy` 重试策略枚举 (NONE/LINEAR/EXPONENTIAL)
- 新增 `ProgressInfo` 进度信息类
- 新增 `WorkflowControl` 工作流控制（暂停/恢复/取消）

#### 缓存增强

- 新增 `EnhancedCache` 增强缓存管理器
- 新增 `CacheMetrics` 缓存指标
- 新增缓存预热功能

#### UX 增强

- 新增 `EnhancedUXManager` 增强 UX 管理器
- 新增 `LocaleManager` 本地化管理器
- 新增 `MessageTemplate` 消息模板

---

## [v1.29.0] - 2026-03-22

### ✨ Added

#### 工作流 CLI

- 新增 `mc-agent workflow` 命令组
  - `workflow run`: 运行完整工作流
  - `workflow search`: 搜索文档
  - `workflow create`: 创建项目
  - `workflow diagnose`: 诊断问题
  - `workflow cache`: 缓存管理

---

## [v1.28.0] - 2026-03-22

### ✨ Added

#### 端到端工作流

- 新增 `EndToEndWorkflow` 工作流管理器
- 新增 `WorkflowConfig` 工作流配置
- 新增 `WorkflowResult` 工作流结果
- 新增 `WorkflowStep` 步骤枚举

#### UX 模块

- 新增 `UserMessage` 用户消息类
- 新增 `UserMessageBuilder` 消息构建器
- 新增 `CLIOutputFormatter` CLI 输出格式化器

---

## [v1.27.0] - 2026-03-22

### ✨ Added

#### 测试覆盖率提升

- 新增 `CodeExampleManager` 测试
- 新增缓存模块测试
- 新增插件兼容性测试

---

## [v1.26.0] - 2026-03-22

### ✨ Added

#### API 搜索 Skill 增强

- 新增 `KnowledgeRetrieval` 测试
- 新增 `LauncherDiagnoser` 测试
- 新增 `ConfigAutoFixer` 测试

---

## [v1.25.0] - 2026-03-22

### ✨ Added

#### MVP 闭环完善

- 新增端到端工作流测试
- 新增性能基准测试

---

## [v1.24.0] - 2026-03-22

### ✨ Added

#### CLI 命令增强

- 新增 `mc-agent repl` 交互式 REPL 模式
- 新增 `mc-agent config` 配置管理命令
- 新增 `mc-agent docs` 文档生成命令
- 新增 `mc-agent wizard` 向导命令
- 新增 `mc-agent batch` 批量操作命令

#### 配置管理

- 新增 `ConfigManager` 配置管理器
- 新增 `ConfigValidator` 配置验证器
- 新增 `TemplateGenerator` 模板生成器

---

## [v1.23.0] - 2026-03-22

### ✨ Added

#### CLI 交互增强

- 新增 `CLIRepl` REPL 类
- 新增 `CommandHistory` 命令历史
- 新增 `ColoredOutput` 彩色输出
- 新增 `CommandAlias` 命令别名

---

## [v1.22.0] - 2026-03-22

### ✨ Added

#### 代码生成增强

- 新增 `CodeQualityChecker` 代码质量检查器
- 新增增强模板：ENTITY_BEHAVIOR, ITEM_LOGIC, BLOCK_LOGIC, DATA_SYNC

#### 插件系统完善

- 新增 `PluginMarketplace` 插件市场
- 新增 `PluginPerformanceMonitor` 性能监控
- 新增 `DependencyInstaller` 依赖安装器

#### 知识库扩充

- 新增 `CodeExampleManager` 代码示例管理器
- 新增 6 个内置示例

---

## [v1.17.0] - 2026-03-22

### ✨ Added

#### 配置文件诊断

- 新增 `ConfigAutoFixer` 配置自动修复器
- 新增 `mc-launcher fix` 命令

---

## [v1.14.0] - 2026-03-22

### ✨ Added

#### CLI 工具

- 新增 `mc-create project` 命令
- 新增 `mc-create entity` 命令
- 新增 `mc-kb search` 命令
- 新增 `mc-kb api` 命令
- 新增 `mc-kb event` 命令

---

## [v1.13.0] - 2026-03-22

### 🔧 Changed

#### 项目结构重组

- 移动 `completion/`, `performance/`, `plugin/` 到 `contrib/` 目录
- 新增 `scaffold/` 模块作为核心能力

---

## [v1.0.0] - 2026-03-22

### ✨ Added

#### 初始发布

- 知识检索系统
- 项目脚手架
- 游戏启动器
- 代码生成器
- CLI 工具

---

## 废弃 API 列表

以下 API 已废弃，将在未来版本移除：

| API | 废弃版本 | 计划移除版本 | 替代方案 |
|-----|---------|-------------|----------|
| 无 | - | - | - |

---

## 迁移指南

### v1.33.x → v1.34.0

无需迁移，完全向后兼容。

### v1.32.x → v1.33.0

**类型检查增强**：

如果您之前在核心模块中使用了无类型注解的代码，可能需要添加类型注解：

```python
# 之前
def process_items(items):
    result = []
    for item in items:
        result.append(item)
    return result

# 之后
def process_items(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        result.append(item)
    return result
```

---

*文档版本: v1.0.0*
*最后更新: 2026-03-23*