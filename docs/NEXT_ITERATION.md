# 下次迭代计划

## 当前状态

**当前版本**: v1.12.0
**当前迭代**: #26 (进行中)
**下次迭代**: #27

---

## 迭代 #26 计划（当前）

### 版本
v1.13.0

### 目标
根据 VISION.md 调整项目结构，聚焦 MVP 核心能力

### 任务清单

#### 1. 项目结构重组 ✅ (已完成)
- [x] 将 completion、performance、plugin 移到 contrib 目录
- [x] 创建 scaffold 模块（P0 核心能力）
- [x] 更新文档说明

#### 2. 游戏启动器修复 🔥 (最高优先级)
- [ ] 分析 MC Studio 生成的配置文件
- [ ] 对比独立启动器配置差异
- [ ] 修复内存分配错误
- [ ] 验证不同 Addon 的启动稳定性

#### 3. 知识检索增强
- [ ] 优化文档解析器
- [ ] 提取 API 文档中的示例代码
- [ ] 集成本地 embedding (bge-large-zh)
- [ ] 实现混合检索

### 验收标准
- [ ] 启动器能稳定启动游戏（无内存错误）
- [ ] scaffold 模块可创建基础项目结构
- [ ] 知识检索返回准确结果

---

## 迭代 #27 计划

### 版本
v1.14.0

### 目标
完善核心 CLI 工具

### 任务清单

#### 1. CLI 命令实现
- [ ] `mc-create project` 命令
- [ ] `mc-create entity` 命令
- [ ] `mc-run` 结构化输出
- [ ] `mc-kb search` 命令

#### 2. Skills 集成
- [ ] `modsdk-search` Skill
- [ ] `modsdk-diagnose` Skill

#### 3. 测试
- [ ] scaffold 模块测试
- [ ] CLI 命令测试
- [ ] 集成测试

---

## 里程碑状态

| 里程碑 | 验收标准 | 状态 |
|--------|----------|------|
| M1: 启动器可用 | 能稳定启动游戏并加载 Addon，无内存错误 | 🔄 进行中 |
| M2: 知识检索有效 | 搜索 "创建实体" 能返回 CreateEntity API 和示例 | ⏳ 待开始 |
| M3: 创建项目可用 | `mc-create project` 能生成可运行的项目 | ⏳ 待开始 |
| M4: 闭环打通 | Agent 能完成：查文档 → 创建项目 → 启动测试 → 诊断错误 | ⏳ 待开始 |

---

## 项目结构说明

### 核心模块（MVP 重点）
- `knowledge_base/` - 知识库（P0）
- `retrieval/` - 检索引擎（P0）
- `launcher/` - 游戏启动器（P0）
- `log_capture/` - 日志捕获（P0）
- `scaffold/` - 项目脚手架（P0）⭐ 新增
- `generator/` - 代码生成（P1）
- `autofix/` - 自动修复（P1）

### 贡献模块（后续迭代）
- `contrib/completion/` - 代码补全
- `contrib/performance/` - 性能优化
- `contrib/plugin/` - 插件系统

---

*文档版本：v2.0.0*
*最后更新：2026-03-22*