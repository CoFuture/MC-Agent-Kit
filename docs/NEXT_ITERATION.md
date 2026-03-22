# 下次迭代计划

## 当前状态

**当前版本**: v1.14.0
**当前迭代**: #27 (已完成)
**下次迭代**: #28

---

## 迭代 #27 计划（已完成）

### 版本
v1.14.0

### 目标
完善核心 CLI 工具

### 任务清单

#### 1. CLI 命令实现 ✅
- [x] `mc-create project` 命令
- [x] `mc-create entity` 命令
- [x] `mc-create item` 命令（标记为未实现）
- [x] `mc-create block` 命令（标记为未实现）
- [x] `mc-kb search` 命令
- [x] `mc-kb api` 命令
- [x] `mc-kb event` 命令
- [x] `mc-kb status` 命令

#### 2. 测试完善 ✅
- [x] 新增 `test_cli_new_commands.py` (15 个测试)
- [x] 所有测试通过 (1415 passed, 2 skipped)

#### 3. 模块兼容性修复 ✅
- [x] 创建 plugin/completion/performance 顶层模块别名
- [x] 保持向后兼容，测试全部通过

### 验收标准
- [x] mc-create 命令可用 ✅
- [x] mc-kb 命令可用 ✅
- [x] 所有测试通过 ✅

---

## 迭代 #28 计划

### 版本
v1.15.0

### 目标
游戏启动器修复与知识检索增强

### 任务清单

#### 1. 游戏启动器修复 🔥 (最高优先级)

**问题现象**:
- 游戏启动后出现内存分配错误：`Assertion failed: We failed to allocate XXX bytes`
- 官方参考脚本 (mc_launcher.py) 同样有问题
- 错误信息："NO LOG FILE!", "Device Lost"

**调查方向**:
- [ ] 对比 MC Studio 启动游戏时的完整命令行
- [ ] 检查 MC Studio 的初始化流程
- [ ] 尝试不同的 Addon 和游戏版本
- [ ] 分析游戏错误日志
- [ ] 查阅 MC 开发者社区是否有类似问题
- [ ] 配置生成器增强（对比 MC Studio 生成的配置）

#### 2. 知识检索增强
- [ ] 优化文档解析器
- [ ] 提取 API 文档中的示例代码
- [ ] 集成本地 embedding (bge-large-zh)
- [ ] 实现混合检索（语义 + 关键词）
- [ ] 构建统一索引结构 (UnifiedEntry)

#### 3. CLI 增强
- [ ] `mc-run` 结构化输出
- [ ] `mc-logs` 日志分析
- [ ] 完善 `mc-create item/block` 实现

### 验收标准
- [ ] 启动器能稳定启动游戏（无内存错误）或明确问题原因
- [ ] 知识检索返回准确结果
- [ ] 新增代码有测试覆盖

---

## 里程碑状态

| 里程碑 | 验收标准 | 状态 |
|--------|----------|------|
| M1: 启动器可用 | 能稳定启动游戏并加载 Addon，无内存错误 | 🔄 进行中 |
| M2: 知识检索有效 | 搜索 "创建实体" 能返回 CreateEntity API 和示例 | ⏳ 待开始 |
| M3: 创建项目可用 | `mc-create project` 能生成可运行的项目 | ✅ 已完成 |
| M4: 闭环打通 | Agent 能完成：查文档 → 创建项目 → 启动测试 → 诊断错误 | ⏳ 待开始 |

---

## 项目结构说明

### 核心模块（MVP 重点）
- `knowledge_base/` - 知识库（P0）
- `retrieval/` - 检索引擎（P0）
- `launcher/` - 游戏启动器（P0）
- `log_capture/` - 日志捕获（P0）
- `scaffold/` - 项目脚手架（P0）✅ 已完成
- `generator/` - 代码生成（P1）
- `autofix/` - 自动修复（P1）

### 贡献模块（后续迭代）
- `contrib/completion/` - 代码补全
- `contrib/performance/` - 性能优化
- `contrib/plugin/` - 插件系统

---

*文档版本：v2.1.0*
*最后更新：2026-03-22*
