# 下次迭代计划

## 当前状态

**当前版本**: v1.22.0
**当前迭代**: #35 (已完成)
**下次迭代**: #36

---

## 迭代 #35 总结（已完成）

### 版本
v1.22.0

### 目标
代码生成增强与插件系统完善

### 完成内容

#### 1. 代码生成器增强 ✅

**新增 `src/mc_agent_kit/generator/quality_checker.py` 模块**:
- `CodeQualityChecker` - 代码质量检查器
- `QualityReport` - 质量报告
- `QualityIssue` - 质量问题
- `QualityIssueSeverity` - 问题严重程度枚举
- `QualityIssueCategory` - 问题类别枚举
- `QualityCheckConfig` - 质量检查配置
- `check_code_quality()` - 便捷检查函数
- `validate_generated_code()` - 验证生成代码

**功能特性**:
- 语法检查（AST 分析）
- 代码风格检查（行长度、函数长度、尾随空格）
- 最佳实践检查（TODO 注释、ModSDK 最佳实践）
- 安全检查（eval、exec 等危险函数）
- 性能检查（低效代码模式）
- 兼容性检查（Python 2.7/ModSDK 兼容性）

**新增 `src/mc_agent_kit/generator/enhanced_templates.py` 模块**:
- `ENTITY_BEHAVIOR_TEMPLATE` - 实体行为模板
- `ITEM_LOGIC_TEMPLATE` - 物品逻辑模板
- `BLOCK_LOGIC_TEMPLATE` - 方块逻辑模板
- `DATA_SYNC_TEMPLATE` - 数据同步模板
- `ENHANCED_TEMPLATES` - 增强模板列表

**模板功能**:
- 实体行为：支持 passive/neutral/hostile 三种行为类型
- 物品逻辑：支持 consumable/tool/weapon 三种物品类型
- 方块逻辑：支持 solid/interactive/redstone/functional 四种方块类型
- 数据同步：客户端 - 服务端数据同步代码生成

#### 2. 插件系统完善 ✅

**新增 `src/mc_agent_kit/contrib/plugin/marketplace.py` 模块**:
- `PluginMarketplace` - 插件市场主类
- `PluginMarketInfo` - 插件市场信息
- `PluginCategory` - 插件类别枚举
- `PluginStatus` - 插件状态枚举
- `MarketplaceConfig` - 市场配置
- `SearchResult` - 搜索结果
- `create_marketplace()` - 便捷创建函数

**功能特性**:
- 插件搜索（关键词、类别、标签过滤）
- 插件安装/卸载/更新
- 插件依赖检查
- 兼容性检查
- 内置 4 个示例插件

**新增 `src/mc_agent_kit/contrib/plugin/performance.py` 模块**:
- `PluginPerformanceMonitor` - 性能监控器
- `PluginStats` - 插件统计信息
- `PerformanceMetric` - 性能指标
- `PerformanceAlert` - 性能告警
- `MetricType` - 指标类型枚举
- `PerformanceMonitorConfig` - 监控配置
- `create_performance_monitor()` - 便捷创建函数

**功能特性**:
- 执行时间追踪
- 内存使用监控
- 缓存命中率统计
- 错误率统计
- 慢调用告警
- 高错误率告警

**新增 `src/mc_agent_kit/contrib/plugin/auto_install.py` 模块**:
- `DependencyInstaller` - 依赖安装器
- `DependencyInfo` - 依赖信息
- `DependencyInstallerConfig` - 安装器配置
- `InstallReport` - 安装报告
- `InstallResult` - 安装结果
- `InstallStatus` - 安装状态枚举
- `create_dependency_installer()` - 便捷创建函数

**功能特性**:
- 依赖检测（已安装包查询）
- 版本兼容性检查
- 自动安装（支持 pip/uv）
- 安装命令生成
- 必需/可选依赖区分

#### 3. 知识库内容扩充 ✅

**新增 `src/mc_agent_kit/knowledge/examples_enhanced.py` 模块**:
- `CodeExampleManager` - 代码示例管理器
- `CodeExampleEnhanced` - 增强代码示例
- `DifficultyLevel` - 难度等级枚举
- `ExampleCategory` - 示例类别枚举
- `ExampleManagerConfig` - 管理器配置
- `create_example_manager()` - 便捷创建函数

**功能特性**:
- 6 个内置示例（Hello World、创建实体、自定义物品、交互式方块、数据同步、性能优化）
- 难度分级（beginner/intermediate/advanced/expert）
- 类别分类（basic/entity/item/block/ui/network/performance/advanced）
- API/事件关联
- 标签搜索
- 前置知识标记
- 预计学习时间

#### 4. 测试完善 ✅

- 新增 88 个测试
- 总测试数：1725 个 (1725 passed, 2 skipped)
- 测试覆盖率保持 90%+

### 验收标准
- [x] 代码生成器增强完成 ✅
- [x] 插件系统完善完成 ✅
- [x] 知识库内容扩充完成 ✅
- [x] 测试覆盖率 90%+ ✅

---

## 迭代 #36 计划

### 版本
v1.23.0

### 目标
CLI 工具增强与用户体验优化

### 任务清单

#### 1. CLI 交互增强 🔥

**实施内容**:
- [ ] 交互式 CLI 模式（REPL）
- [ ] 命令历史记录的持久化
- [ ] 命令别名和快捷方式
- [ ] 彩色输出和进度条

**验收标准**:
- [ ] 支持交互式命令输入
- [ ] 历史记录可查询
- [ ] 常用命令有快捷方式
- [ ] 输出有颜色和进度提示

#### 2. 配置管理增强

**实施内容**:
- [ ] 配置文件模板生成
- [ ] 配置验证和迁移
- [ ] 环境变量覆盖配置
- [ ] 配置热重载

**验收标准**:
- [ ] 可生成默认配置文件
- [ ] 配置变更自动验证
- [ ] 环境变量优先级正确
- [ ] 配置修改无需重启

#### 3. 文档生成器

**实施内容**:
- [ ] 从代码生成 API 文档
- [ ] 从模板生成使用示例
- [ ] 文档版本管理
- [ ] 多语言文档支持

**验收标准**:
- [ ] 自动生成 API 参考文档
- [ ] 示例代码自动更新
- [ ] 支持文档版本切换
- [ ] 支持中英文文档

#### 4. 测试覆盖率提升

**实施内容**:
- [ ] 新增 CLI 交互测试
- [ ] 新增配置管理测试
- [ ] 新增文档生成测试
- [ ] 边界条件和异常测试

**验收标准**:
- [ ] 测试覆盖率保持 90%+
- [ ] 新增功能测试覆盖率 100%
- [ ] 关键路径集成测试覆盖

### 验收标准
- [ ] CLI 交互增强完成
- [ ] 配置管理增强完成
- [ ] 文档生成器完成
- [ ] 测试覆盖率 90%+

---

## 里程碑状态

| 里程碑 | 验收标准 | 状态 |
|--------|----------|------|
| M1: 启动器可用 | 能稳定启动游戏并加载 Addon，无内存错误 | 🟢 基本完成 |
| M2: 知识检索有效 | 搜索 "创建实体" 能返回 CreateEntity API 和示例 | ✅ 已完成 |
| M3: 创建项目可用 | `mc-create project` 能生成可运行的项目 | ✅ 已完成 |
| M4: 闭环打通 | Agent 能完成：查文档 → 创建项目 → 启动测试 → 诊断错误 | 🟢 基本完成 |
| M5: CLI 工具完善 | 所有核心功能有 CLI 命令，支持 JSON 输出 | ✅ 已完成 |
| M6: 性能优化 | 缓存命中率 > 50%，搜索响应 < 100ms | 🟡 进行中 |
| M7: 代码生成增强 | 新增 4+ 种模板，支持质量检查 | ✅ 已完成 |
| M8: 插件系统完善 | 插件市场、性能监控、依赖安装可用 | ✅ 已完成 |

**说明**: 
- M1: 迭代 #31-33 添加了内存诊断、自动修复和分析工具
- M4: 现在支持完整的开发闭环
- M5: 迭代 #33 完成了 CLI 工具增强
- M6: 迭代 #34 实现了缓存系统，需要实际使用数据验证命中率
- M7: 迭代 #35 实现了代码生成增强和质量检查
- M8: 迭代 #35 实现了插件市场、性能监控和依赖自动安装

---

## 项目结构说明

### 核心模块（MVP 重点）
- `knowledge_base/` - 知识库（P0）✅
- `knowledge/` - 知识检索（P0）✅
- `launcher/` - 游戏启动器（P0）✅
- `log_capture/` - 日志捕获（P0）✅
- `scaffold/` - 项目脚手架（P0）✅
- `generator/` - 代码生成（P1）✅

### 新增模块（迭代 #31-35）
- `launcher/diagnoser.py` - 内存诊断工具 ✅
- `launcher/auto_fixer.py` - 内存自动修复 ✅
- `stats/tracker.py` - API 使用统计 ✅
- `knowledge/retrieval.py` - 增强检索 ✅
- `knowledge/index_cache.py` - 索引缓存 ✅
- `knowledge/search_cache.py` - 搜索缓存 ✅
- `knowledge/examples_enhanced.py` - 增强示例管理 ✅
- `cli_optimize.py` - CLI 性能优化 ✅
- `generator/quality_checker.py` - 代码质量检查 ✅
- `generator/enhanced_templates.py` - 增强模板 ✅
- `contrib/plugin/marketplace.py` - 插件市场 ✅
- `contrib/plugin/performance.py` - 性能监控 ✅
- `contrib/plugin/auto_install.py` - 依赖安装 ✅

### 贡献模块（后续迭代）
- `contrib/completion/` - 代码补全
- `contrib/performance/` - 性能优化
- `contrib/plugin/` - 插件系统

---

## 性能目标

| 指标 | 当前值 | 目标值 | 优先级 |
|------|--------|--------|--------|
| 索引构建时间 | ~5s → ~1s (缓存命中) | < 3s | 高 |
| 搜索响应时间 | ~200ms → ~10ms (缓存命中) | < 100ms | 高 |
| CLI 启动时间 | ~500ms | < 200ms | 中 |
| 缓存命中率 | N/A | > 50% | 中 |
| 代码生成质量 | N/A | 90%+ 通过检查 | 中 |
| 插件加载时间 | N/A | < 1s | 低 |

---

*文档版本：v2.9.0*
*最后更新：2026-03-22*
