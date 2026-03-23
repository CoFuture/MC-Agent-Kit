# 下次迭代计划

## 当前状态

**当前版本**: v1.43.0
**当前迭代**: #56 (已完成)
**下次迭代**: #57

---

## 迭代 #56 总结（已完成）

### 版本
v1.43.0

### 目标
MCP 工具集成与 API 增强

### 完成内容

#### 1. MCP 工具集成 ✅

**新增 `src/mc_agent_kit/tools/` 模块目录**:

**MCP 客户端** (`mcp_client.py`):
- `MCPClient` - MCP 工具客户端
- `MCPTool` - 工具定义
- `MCPToolResult` - 执行结果
- 支持同步/异步调用
- 内置缓存机制

#### 2. 工具注册中心 ✅

**新增 `src/mc_agent_kit/tools/registry.py`**:
- `ToolRegistry` - 注册中心
- `ToolMetadata` - 元数据
- `ToolCategory` - 类别枚举
- 支持动态注册和发现

#### 3. 工具编排引擎 ✅

**新增 `src/mc_agent_kit/tools/orchestrator.py`**:
- `ToolOrchestrator` - 编排器
- `ToolWorkflow` - 工作流
- 支持顺序/并行/条件执行

#### 4. 内置工具集 ✅

**新增 `src/mc_agent_kit/tools/builtin/`**:
- 文件工具 (file_tools.py)
- 网络工具 (web_tools.py)
- 代码工具 (code_tools.py)
- 搜索工具 (search_tools.py)
- Git 工具 (git_tools.py)

### 验收标准完成情况

- [x] MCP 工具集成完成 ✅
- [x] 工具注册中心支持动态注册和发现 ✅
- [x] 工具编排引擎支持串行和并行执行 ✅
- [x] 内置工具集覆盖常用场景 ✅
- [x] 所有测试通过 (71 passed) ✅

### 文件变更

```
新增文件:
- src/mc_agent_kit/tools/__init__.py
- src/mc_agent_kit/tools/mcp_client.py
- src/mc_agent_kit/tools/registry.py
- src/mc_agent_kit/tools/orchestrator.py
- src/mc_agent_kit/tools/builtin/__init__.py
- src/mc_agent_kit/tools/builtin/file_tools.py
- src/mc_agent_kit/tools/builtin/web_tools.py
- src/mc_agent_kit/tools/builtin/code_tools.py
- src/mc_agent_kit/tools/builtin/search_tools.py
- src/mc_agent_kit/tools/builtin/git_tools.py
- src/tests/test_iteration_56.py

修改文件:
- docs/ITERATIONS.md
- docs/NEXT_ITERATION.md
- pyproject.toml (版本升级到 1.43.0)
```

---

## 迭代 #57 计划

### 版本
v1.44.0

### 目标
Agent 技能增强与 ModSDK 深度集成

### 背景与动机

迭代 #56 已完成 MCP 工具集成和 API 增强。为了使 Agent 能够更好地与 ModSDK 集成并提供更智能的开发辅助，需要实现以下功能：

1. **Agent 技能增强**: 扩展现有技能，提供更丰富的 ModSDK 开发辅助
2. **ModSDK 深度集成**: 实现与 ModSDK 的深度集成，支持游戏内调试
3. **智能代码分析**: 增强代码分析能力，提供更准确的建议
4. **项目模板系统**: 完善项目模板，支持更多 Addon 类型

### 功能规划

#### 1. Agent 技能增强

**文件**: `src/mc_agent_kit/skills/modsdk_enhanced.py`

**核心功能**:
- ModSDK API 智能补全
- 事件监听器自动生成
- 实体/物品/方块模板生成
- 配置生成和验证

**数据结构**:
```python
class ModSDKSkill:
    """ModSDK 增强技能"""
    def generate_entity(self, name: str, behaviors: list) -> GeneratedEntity
    def generate_item(self, name: str, properties: dict) -> GeneratedItem
    def generate_block(self, name: str, properties: dict) -> GeneratedBlock
    def validate_config(self, config: dict) -> ValidationResult
```

#### 2. 游戏内调试集成

**文件**: `src/mc_agent_kit/debugger/game_debug.py`

**核心功能**:
- 游戏内日志实时捕获
- 断点调试支持
- 变量监视
- 热重载支持

**数据结构**:
```python
class GameDebugger:
    """游戏调试器"""
    def attach(self, game_pid: int) -> bool
    def set_breakpoint(self, file: str, line: int) -> bool
    def get_variables(self) -> dict
    def step_over(self) -> None
    def continue_execution(self) -> None
```

#### 3. 智能代码分析

**文件**: `src/mc_agent_kit/analysis/code_analyzer.py`

**核心功能**:
- ModSDK API 使用分析
- 性能瓶颈识别
- 潜在错误检测
- 最佳实践建议

**数据结构**:
```python
class CodeAnalyzer:
    """代码分析器"""
    def analyze(self, code: str) -> AnalysisResult
    def find_api_usage(self, code: str) -> list[APIUsage]
    def detect_issues(self, code: str) -> list[Issue]
    def suggest_improvements(self, code: str) -> list[Suggestion]
```

#### 4. 项目模板系统

**文件**: `src/mc_agent_kit/templates/project_templates.py`

**核心功能**:
- 实体开发模板
- 物品开发模板
- 方块开发模板
- UI 开发模板
- 网络同步模板

**模板类型**:
- `entity_basic` - 基础实体模板
- `entity_complex` - 复杂实体模板（带 AI）
- `item_consumable` - 消耗品模板
- `item_tool` - 工具模板
- `block_interactive` - 交互方块模板
- `ui_form` - UI 表单模板

### 验收标准

#### 功能验收
- [ ] Agent 技能支持 ModSDK API 智能补全
- [ ] 游戏内调试集成可用
- [ ] 代码分析提供准确建议
- [ ] 项目模板覆盖主要 Addon 类型

#### 性能验收
- [ ] 代码生成延迟 < 500ms
- [ ] 分析响应 < 1s
- [ ] 调试器连接 < 2s

#### 测试验收
- [ ] 新增测试用例覆盖所有新功能
- [ ] 所有测试通过
- [ ] 测试覆盖率 > 80%

### 风险评估

1. **兼容性风险**: ModSDK 版本变更可能影响集成
   - 缓解措施：实现版本检测，支持多版本适配

2. **调试器风险**: 游戏内调试可能影响游戏性能
   - 缓解措施：调试模式可选，生产环境禁用

3. **复杂度风险**: 代码分析可能误报
   - 缓解措施：提供配置选项，允许用户调整规则

### 依赖项

- 依赖迭代 #56 的工具模块（用于文件操作等）
- 依赖迭代 #54 的知识图谱（用于 API 分析）
- 需要 ModSDK 文档支持

### 时间估算

- Agent 技能增强：2-3 天
- 游戏内调试集成：2-3 天
- 智能代码分析：2 天
- 项目模板系统：1-2 天
- 测试与文档：1 天

**总计**: 8-11 天

---

## 迭代历史

| 迭代 | 版本 | 主题 | 状态 |
|------|------|------|------|
| #56 | v1.43.0 | MCP 工具集成与 API 增强 | ✅ 已完成 |
| #55 | v1.42.0 | 知识库持续学习与自适应优化 | ✅ 已完成 |
| #54 | v1.41.0 | 知识图谱与智能推理 | ✅ 已完成 |
| #53 | v1.40.0 | API 集成增强与 LLM 支持 | ✅ 已完成 |
| #52 | v1.39.0 | 工作流自动化与 CLI 增强 | ✅ 已完成 |
