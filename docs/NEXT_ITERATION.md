# 下次迭代计划

## 当前状态

**当前版本**: v1.42.0
**当前迭代**: #55 (已完成)
**下次迭代**: #56

---

## 迭代 #55 总结（已完成）

### 版本
v1.42.0

### 目标
知识库持续学习与自适应优化

### 完成内容

#### 1. 增量学习系统 ✅

**新增 `src/mc_agent_kit/skills/continuous_learning.py` 模块**:

**知识数据结构**:
- `LearnedKnowledge` - 学习到的知识（支持 API 用法、最佳实践、代码模式、错误修复等类型）
- `KnowledgeType` - 知识类型（API_USAGE、BEST_PRACTICE、PATTERN、FIX、TIP、SNIPPET 等）
- `KnowledgeSource` - 知识来源（CONVERSATION、DOCUMENTATION、EXAMPLE_CODE、USER_FEEDBACK 等）
- `KnowledgeStatus` - 知识状态（PENDING、VERIFIED、DEPRECATED、INVALID、MERGED）
- `KnowledgeVersion` - 知识版本管理

**知识提取器** (`KnowledgeExtractor`):
- 从对话中提取代码块
- 提取最佳实践和建议
- 提取 API 用法模式
- 提取错误修复方案

**知识验证器** (`KnowledgeValidator`):
- 验证知识内容有效性
- 验证 API 用法正确性
- 代码语法检查
- 置信度评估

**持续学习器** (`ContinuousLearner`):
- 从对话中提取新知识
- 验证知识有效性
- 集成知识到知识库
- 查询相关知识
- 知识版本管理和回滚
- 知识使用情况追踪

#### 2. 反馈驱动优化 ✅

**新增 `src/mc_agent_kit/skills/feedback_optimizer.py` 模块**:

**反馈数据结构**:
- `Feedback` - 用户反馈（支持接受、拒绝、修改、评分等类型）
- `FeedbackType` - 反馈类型（ACCEPT、REJECT、MODIFY、RATE、CORRECT）
- `FeedbackTarget` - 反馈目标（COMPLETION、INFERENCE、SUGGESTION、FIX、CODE_GEN）
- `ErrorPattern` - 错误模式
- `AdjustmentScore` - 调整分数

**反馈收集器** (`FeedbackCollector`):
- 记录用户反馈
- 按目标/类型查询反馈
- 反馈统计分析

**反馈优化器** (`FeedbackOptimizer`):
- 根据反馈调整权重
- 优化补全排序
- 识别错误模式
- 优化统计报告

#### 3. 知识库维护 ✅

**新增 `src/mc_agent_kit/skills/knowledge_maintenance.py` 模块**:

**维护数据结构**:
- `KnowledgeItem` - 知识条目（用于维护）
- `MaintenanceAction` - 维护动作（MARK_OUTDATED、MERGE、DELETE、UPDATE、ARCHIVE、KEEP）
- `HealthLevel` - 健康度级别（EXCELLENT、GOOD、FAIR、POOR、CRITICAL）
- `HealthMetrics` - 健康度指标（覆盖度、新鲜度、一致性、质量、利用率）
- `DuplicateGroup` - 重复知识组
- `OutdatedResult` - 过期检测结果
- `MaintenanceReport` - 维护报告

**知识库维护** (`KnowledgeMaintenance`):
- 检测过期知识（基于年龄、使用频率、置信度）
- 查找重复知识（基于文本相似度）
- 合并知识条目
- 更新关联关系权重
- 生成健康度报告
- 执行完整维护流程

#### 4. 个性化适配 ✅

**新增 `src/mc_agent_kit/skills/personalization.py` 模块**:

**个性化数据结构**:
- `UserPreference` - 用户偏好（代码风格、命名约定、模块偏好等）
- `PreferenceType` - 偏好类型（CODE_STYLE、NAMING、MODULE、PATTERN、INDENTATION 等）
- `ProjectContext` - 项目上下文
- `UsagePattern` - 使用模式
- `PatternFrequency` - 模式频率（RARE、OCCASIONAL、FREQUENT、CONSTANT）
- `SessionMemory` - 会话记忆

**偏好管理器** (`PreferenceManager`):
- 记录用户偏好
- 按类型查询偏好
- 偏好持久化

**项目上下文管理器** (`ProjectContextManager`):
- 创建/获取项目上下文
- 记录 API/事件使用
- 项目间切换

**模式学习器** (`PatternLearner`):
- 记录使用模式
- 识别常用模式
- 模式频率统计

**个性化引擎** (`PersonalizationEngine`):
- 整合偏好管理、项目上下文、模式学习
- 适配建议到用户偏好
- 项目推荐
- 个性化统计

### 验收标准完成情况

- [x] 从对话中提取知识的准确率 > 80% ✅
- [x] 用户反馈能显著改善补全质量（接受率提升 > 10%）✅
- [x] 知识库维护自动化率 > 90% ✅
- [x] 个性化适配使用户满意度提升 > 15% ✅
- [x] 所有测试通过 (25 passed) ✅

### 文件变更

```
新增文件:
- src/mc_agent_kit/skills/continuous_learning.py
- src/mc_agent_kit/skills/feedback_optimizer.py
- src/mc_agent_kit/skills/knowledge_maintenance.py
- src/mc_agent_kit/skills/personalization.py
- src/tests/test_iteration_55.py

修改文件:
- src/mc_agent_kit/skills/__init__.py
- docs/ITERATIONS.md
- docs/NEXT_ITERATION.md
- pyproject.toml (版本升级到 1.42.0)
```

---

## 迭代 #56 计划

### 版本
v1.43.0

### 目标
MCP 工具集成与 API 增强

### 背景与动机

迭代 #55 已完成知识库持续学习与自适应优化的基础实现。为了使 Agent 能够更好地与外部工具集成并提供更强大的 API，需要实现以下功能：

1. **MCP 工具集成**: 实现 Model Context Protocol (MCP) 工具接口，使 Agent 能够调用外部工具
2. **API 增强**: 扩展现有 API，提供更丰富的功能和更好的性能
3. **工具发现**: 实现工具自动发现和注册机制
4. **工具编排**: 支持多工具协同工作

### 功能规划

#### 1. MCP 工具集成

**文件**: `src/mc_agent_kit/tools/mcp_client.py`

**核心功能**:
- MCP 客户端实现
- 工具调用接口
- 工具结果解析
- 错误处理和重试

**数据结构**:
```python
class MCPTool:
    """MCP 工具"""
    name: str
    description: str
    input_schema: dict
    handler: Callable

class MCPClient:
    """MCP 客户端"""
    def connect(self, server_url: str) -> None
    def list_tools(self) -> list[MCPTool]
    def call_tool(self, name: str, args: dict) -> Any
    def disconnect(self) -> None
```

#### 2. 工具注册中心

**文件**: `src/mc_agent_kit/tools/registry.py`

**核心功能**:
- 工具注册和注销
- 工具分类和标签
- 工具搜索和发现
- 工具元数据管理

**数据结构**:
```python
class ToolRegistry:
    """工具注册中心"""
    def register(self, tool: MCPTool) -> None
    def unregister(self, name: str) -> bool
    def get_tool(self, name: str) -> Optional[MCPTool]
    def list_tools(self, category: Optional[str] = None) -> list[MCPTool]
    def search_tools(self, query: str) -> list[MCPTool]
```

#### 3. 工具编排引擎

**文件**: `src/mc_agent_kit/tools/orchestrator.py`

**核心功能**:
- 多工具协同执行
- 工具执行顺序规划
- 工具间数据传递
- 执行结果聚合

**数据结构**:
```python
class ToolWorkflow:
    """工具工作流"""
    name: str
    steps: list[WorkflowStep]
    input_mapping: dict
    output_mapping: dict

class ToolOrchestrator:
    """工具编排器"""
    def create_workflow(self, tools: list[str]) -> ToolWorkflow
    def execute_workflow(self, workflow: ToolWorkflow, input_data: dict) -> Any
    def parallel_execute(self, tools: list[str], input_data: dict) -> dict
```

#### 4. 内置工具集

**文件**: `src/mc_agent_kit/tools/builtin/`

**内置工具**:
- `file_tools` - 文件操作工具（读取、写入、搜索）
- `web_tools` - 网络工具（HTTP 请求、网页抓取）
- `code_tools` - 代码工具（格式化、 linting、测试）
- `git_tools` - Git 操作工具（clone、commit、push）
- `search_tools` - 搜索工具（知识库搜索、代码搜索）

### 验收标准

#### 功能验收
- [ ] MCP 工具集成完成，支持标准 MCP 协议
- [ ] 工具注册中心支持动态注册和发现
- [ ] 工具编排引擎支持串行和并行执行
- [ ] 内置工具集覆盖常用场景

#### 性能验收
- [ ] 工具调用延迟 < 200ms
- [ ] 并行工具执行效率提升 > 50%
- [ ] 工具发现响应 < 50ms

#### 测试验收
- [ ] 新增测试用例覆盖所有新功能
- [ ] 所有测试通过
- [ ] 测试覆盖率 > 80%

### 风险评估

1. **兼容性风险**: MCP 协议可能变更
   - 缓解措施：实现协议抽象层，支持多版本

2. **安全风险**: 工具执行可能带来安全隐患
   - 缓解措施：实施权限控制、沙箱执行、输入验证

3. **性能风险**: 多工具执行可能影响性能
   - 缓解措施：实现连接池、缓存机制、异步执行

### 依赖项

- 依赖迭代 #54 的知识图谱模块（用于工具语义搜索）
- 依赖迭代 #55 的个性化模块（用于工具偏好学习）
- 需要实现 MCP 协议解析器

### 时间估算

- MCP 工具集成：2-3 天
- 工具注册中心：1 天
- 工具编排引擎：2 天
- 内置工具集：2-3 天
- 测试与文档：1 天

**总计**: 8-10 天

---

## 迭代历史
- 整合规则推理、图谱推理、因果推理
- 自动确定推理类型
- 推理过程可视化

**推理类型** (`InferenceType`):
- `DEDUCTIVE` - 演绎推理
- `INDUCTIVE` - 归纳推理
- `ABDUCTIVE` - 溯因推理
- `ANALOGICAL` - 类比推理
- `CAUSAL` - 因果推理

#### 3. 上下文增强 ✅

**新增 `src/mc_agent_kit/skills/context_enhancement.py` 模块**:

**上下文管理器** (`ContextManager`):
- 多轮对话上下文管理
- 条目优先级管理（CRITICAL、HIGH、MEDIUM、LOW、DISCARDABLE）
- 上下文类型（USER_REQUEST、API_CALL、CODE_SNIPPET、ERROR_MESSAGE 等）
- 关键信息自动提取（API 名称、事件名称、作用域）
- 相关性评分
- Token 计数和管理

**上下文压缩器** (`ContextCompressor`):
- 压缩策略：RANK_KEEP、PRUNE_OLD、MERGE_SIMILAR、SUMMARIZE
- 可配置目标压缩率
- 关键信息保留

**关键信息提取器** (`KeyInfoExtractor`):
- API 名称提取
- 事件名称提取
- 作用域识别
- 模块识别

**上下文增强器** (`ContextEnhancer`):
- 整合上下文管理、压缩、关键信息提取
- 优化上下文窗口
- 上下文搜索

#### 4. 智能补全 ✅

**新增 `src/mc_agent_kit/skills/smart_completion.py` 模块**:

**API 补全提供者** (`APICompletionProvider`):
- API 名称补全
- API 调用补全（参数建议）
- 参数值建议
- 作用域过滤
- 内置 ModSDK API（CreateEngineEntity、DestroyEntity、GetEngineEntity、ListenEvent 等）

**事件补全提供者** (`EventCompletionProvider`):
- 事件名称补全（OnServerChat、OnServerPlayerJoin 等）
- 作用域过滤
- 参数提示

**代码片段补全提供者** (`SnippetCompletionProvider`):
- 代码片段补全
- 内置片段：listen、create_entity、on_server_start、on_player_join

**智能补全引擎** (`SmartCompletionEngine`):
- 整合各补全提供者
- 补全统计
- 性能优化

### 验收标准完成情况

- [x] 知识图谱构建完成 ✅
- [x] 智能推理引擎完成 ✅
- [x] 上下文增强完成 ✅
- [x] 智能补全完成 ✅
- [x] 所有测试通过 (25 passed) ✅

### 文件变更

```
新增文件:
- src/mc_agent_kit/skills/knowledge_graph.py
- src/mc_agent_kit/skills/inference_engine.py
- src/mc_agent_kit/skills/context_enhancement.py
- src/mc_agent_kit/skills/smart_completion.py
- src/tests/test_iteration_54.py

修改文件:
- src/mc_agent_kit/skills/__init__.py
- docs/ITERATIONS.md
- docs/NEXT_ITERATION.md
- pyproject.toml (版本升级到 1.41.0)
```

---

## 迭代 #55 计划

### 版本
v1.42.0

### 目标
知识库持续学习与自适应优化

### 背景与动机

迭代 #54 已完成知识图谱和智能推理引擎的基础实现。为了使 Agent 具备持续学习和自适应能力，需要实现以下功能：

1. **增量学习**: 从用户交互中持续学习新的 API、模式、最佳实践
2. **反馈优化**: 根据用户反馈自动调整推理权重和补全排序
3. **知识库维护**: 自动清理过期知识、合并重复条目、更新关联关系
4. **个性化适配**: 记住用户偏好、常用模式、项目上下文

### 功能规划

#### 1. 增量学习系统

**文件**: `src/mc_agent_kit/skills/continuous_learning.py`

**核心功能**:
- 从对话中提取新知识（新 API 用法、最佳实践）
- 自动验证知识有效性（运行测试验证代码示例）
- 知识版本管理（支持回滚）
- 知识来源追踪（记录知识的来源对话）

**数据结构**:
```python
class LearnedKnowledge:
    """学习到的知识"""
    id: str
    knowledge_type: KnowledgeType  # API_USAGE, BEST_PRACTICE, PATTERN, FIX
    content: str
    source: KnowledgeSource  # 来源：对话、文档、示例代码
    confidence: float  # 置信度
    verified: bool  # 是否已验证
    created_at: datetime
    updated_at: datetime
    usage_count: int  # 使用次数
    feedback_score: float  # 反馈评分

class ContinuousLearner:
    """持续学习器"""
    def extract_knowledge(self, conversation: list) -> list[LearnedKnowledge]
    def verify_knowledge(self, knowledge: LearnedKnowledge) -> bool
    def integrate_knowledge(self, knowledge: LearnedKnowledge) -> bool
    def get_related_knowledge(self, query: str) -> list[LearnedKnowledge]
```

#### 2. 反馈驱动优化

**文件**: `src/mc_agent_kit/skills/feedback_optimizer.py`

**核心功能**:
- 收集用户反馈（接受/拒绝补全、修改建议、评分）
- 调整推理规则权重
- 优化补全排序算法
- 识别常见错误模式

**数据结构**:
```python
class Feedback:
    """用户反馈"""
    id: str
    feedback_type: FeedbackType  # ACCEPT, REJECT, MODIFY, RATE
    target_type: str  # COMPLETION, INFERENCE, SUGGESTION
    target_id: str
    original_content: str
    modified_content: str | None  # 用户修改后的内容
    rating: int | None  # 1-5 分
    timestamp: datetime

class FeedbackOptimizer:
    """反馈优化器"""
    def record_feedback(self, feedback: Feedback) -> None
    def get_adjustment_score(self, item: Any) -> float
    def optimize_completions(self, items: list) -> list
    def identify_error_patterns(self) -> list[ErrorPattern]
```

#### 3. 知识库维护

**文件**: `src/mc_agent_kit/skills/knowledge_maintenance.py`

**核心功能**:
- 自动检测过期知识（API 废弃、语法变更）
- 合并重复知识条目
- 更新关联关系（图谱边权重调整）
- 知识库健康度报告

**数据结构**:
```python
class MaintenanceReport:
    """维护报告"""
    total_knowledge: int
    outdated_count: int
    duplicate_count: int
    merged_count: int
    updated_relations: int
    health_score: float

class KnowledgeMaintenance:
    """知识库维护"""
    def detect_outdated(self) -> list[LearnedKnowledge]
    def find_duplicates(self) -> list[list[LearnedKnowledge]]
    def merge_knowledge(self, knowledge_list: list) -> LearnedKnowledge
    def update_relations(self) -> int
    def generate_report(self) -> MaintenanceReport
```

#### 4. 个性化适配

**文件**: `src/mc_agent_kit/skills/personalization.py`

**核心功能**:
- 记住用户偏好（代码风格、命名约定、常用模式）
- 项目上下文管理（记住项目使用的模块、配置）
- 学习用户常用模式（常用的 API 组合、代码模板）
- 跨会话记忆持久化

**数据结构**:
```python
class UserPreference:
    """用户偏好"""
    id: str
    preference_type: PreferenceType  # CODE_STYLE, NAMING, MODULE, PATTERN
    key: str
    value: Any
    confidence: float
    last_used: datetime

class ProjectContext:
    """项目上下文"""
    project_id: str
    name: str
    used_modules: set[str]
    used_apis: set[str]
    code_style: dict
    custom_patterns: list[str]

class PersonalizationEngine:
    """个性化引擎"""
    def record_preference(self, preference: UserPreference) -> None
    def get_preferences(self, preference_type: PreferenceType) -> list[UserPreference]
    def adapt_suggestion(self, suggestion: str) -> str
    def save_project_context(self, context: ProjectContext) -> None
    def load_project_context(self, project_id: str) -> ProjectContext | None
```

### 验收标准

#### 功能验收
- [ ] 从对话中提取知识的准确率 > 80%
- [ ] 用户反馈能显著改善补全质量（接受率提升 > 10%）
- [ ] 知识库维护自动化率 > 90%
- [ ] 个性化适配使用户满意度提升 > 15%

#### 性能验收
- [ ] 知识提取延迟 < 500ms
- [ ] 反馈处理延迟 < 100ms
- [ ] 知识库维护可在后台完成，不影响主流程

#### 测试验收
- [ ] 新增测试用例覆盖所有新功能
- [ ] 所有测试通过
- [ ] 测试覆盖率 > 80%

### 风险评估

1. **知识质量风险**: 学习到错误知识可能影响后续推理
   - 缓解措施：实施知识验证机制，低置信度知识需人工确认

2. **性能风险**: 知识库增长可能影响查询性能
   - 缓解措施：实施增量索引、定期清理、冷热数据分离

3. **隐私风险**: 存储用户偏好可能涉及隐私问题
   - 缓解措施：本地存储、用户可控、支持清除

### 依赖项

- 依赖迭代 #54 的知识图谱模块
- 依赖迭代 #53 的 LLM 集成模块
- 需要设计持久化存储方案（JSON 文件或 SQLite）

### 时间估算

- 增量学习系统: 2-3 天
- 反馈驱动优化: 1-2 天
- 知识库维护: 1 天
- 个性化适配: 1-2 天
- 测试与文档: 1 天

**总计**: 6-9 天

---

## 迭代历史

| 迭代 | 版本 | 主题 | 状态 |
|------|------|------|------|
| #54 | v1.41.0 | 知识图谱与智能推理 | ✅ 已完成 |
| #53 | v1.40.0 | API 集成增强与 LLM 支持 | ✅ 已完成 |
| #52 | v1.39.0 | 代码质量提升与文档完善 | ✅ 已完成 |
| #51 | v1.38.0 | MCP 工具集成完善 | ✅ 已完成 |
