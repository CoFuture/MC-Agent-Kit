# 下次迭代计划

## 当前状态

**当前版本**: v1.41.0
**当前迭代**: #54 (已完成)
**下次迭代**: #55

---

## 迭代 #54 总结（已完成）

### 版本
v1.41.0

### 目标
知识图谱与智能推理

### 完成内容

#### 1. 知识图谱构建 ✅

**新增 `src/mc_agent_kit/skills/knowledge_graph.py` 模块**:

**图谱数据结构**:
- `GraphNode` - 图谱节点（支持 API、事件、实体、物品、方块、组件、模块等类型）
- `GraphEdge` - 图谱边（支持调用、触发、监听、依赖、相关等关系类型）
- `GraphPath` - 图谱路径
- `GraphStats` - 图谱统计

**节点类型** (`NodeType`):
- `API` - API 接口
- `EVENT` - 事件
- `ENTITY` - 实体
- `ITEM` - 物品
- `BLOCK` - 方块
- `COMPONENT` - 组件
- `MODULE` - 模块
- `PARAMETER` - 参数
- `RETURN_VALUE` - 返回值
- `EXAMPLE` - 示例
- `CONCEPT` - 概念

**关系类型** (`RelationType`):
- `CALLS` - 调用
- `TRIGGERS` - 触发
- `LISTENS` - 监听
- `RETURNS` - 返回
- `TAKES` - 接受参数
- `BELONGS_TO` - 属于模块
- `DEPENDS_ON` - 依赖
- `RELATED_TO` - 相关
- `EXTENDS` - 继承
- `IMPLEMENTS` - 实现
- `CONTAINS` - 包含
- `USES` - 使用
- `CREATES` - 创建
- `MODIFIES` - 修改
- `EXAMPLE_OF` - 示例
- `SIMILAR_TO` - 相似

**知识图谱功能**:
- 节点管理（添加、查询、更新、删除）
- 边管理（添加关系、查询邻居）
- 路径查找（BFS 算法）
- 子图提取
- 重要节点识别（基于连接度）
- 统计信息
- Mermaid 图表导出
- JSON 导入导出

**知识图谱构建器** (`KnowledgeGraphBuilder`):
- 从 API 列表构建图谱
- 从事件列表构建图谱
- 推断关系（基于名称相似性、同模块）
- 添加示例关系

#### 2. 智能推理引擎 ✅

**新增 `src/mc_agent_kit/skills/inference_engine.py` 模块**:

**推理规则系统**:
- `InferenceRule` - 推理规则
- `RuleType` - 规则类型（IF_THEN、IMPLIES、EQUIVALENT、EXCLUDES、REQUIRES）
- `RuleEngine` - 规则推理引擎
- 内置规则：实体创建需要设置位置、事件监听需要注册、物品需要注册

**图谱推理引擎** (`GraphInferenceEngine`):
- 推断相关 API
- 推断 API 使用方式
- 推断 API 依赖
- 基于图谱路径的推理

**因果推理引擎** (`CausalInferenceEngine`):
- `CausalChain` - 因果链
- 推断原因（溯因推理）
- 推断结果（演绎推理）
- 内置因果规则：未注册事件监听→事件回调不执行、mod.json 配置错误→Addon 加载失败、客户端调用服务端 API→API 调用失败

**综合推理引擎** (`InferenceEngine`):
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
