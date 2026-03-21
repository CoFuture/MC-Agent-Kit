# 下次迭代计划

## 当前迭代 #8 (v0.5.0) ✅

### 版本目标
v0.5.0 - 向量检索集成与语义搜索增强

### 迭代目标
集成向量数据库，实现语义搜索和知识库增量更新

### 任务清单

#### 高优先级 🔥

**任务 1: 向量检索集成**
- [x] 集成 ChromaDB 向量数据库
- [x] 实现文档向量化（使用 sentence-transformers）
- [x] 实现语义搜索功能
- [x] 支持混合搜索（关键词 + 语义）

**任务 2: LlamaIndex 集成**
- [x] 集成 LlamaIndex 框架
- [x] 实现向量存储（ChromaDB）
- [x] 实现文档加载器
- [x] 实现查询引擎

**任务 3: 知识库增量更新**
- [x] 支持增量构建知识库
- [x] 实现文档变更检测
- [x] 支持增量向量化
- [x] 实现向量索引更新

#### 中优先级

**任务 4: 搜索增强**
- [x] 实现搜索结果重排序
- [x] 支持多路召回
- [x] 实现搜索结果解释
- [x] 支持相关度评分

### 预期产出
```
MC-Agent-Kit/
├── src/mc_agent_kit/
│   └── retrieval/            # 新增检索模块
│       ├── vector_store.py   # 向量存储
│       ├── semantic_search.py # 语义搜索
│       ├── hybrid_search.py  # 混合搜索
│       └── llama_index.py    # LlamaIndex 集成
├── pyproject.toml            # 添加 chromadb, llama-index 依赖
└── skills/
    └── modsdk-semantic-search/ # 新增语义搜索 Skill
        └── SKILL.md
```

### 验收标准
- [x] ChromaDB 集成完成
- [x] LlamaIndex 集成完成
- [x] 语义搜索可用
- [x] 混合搜索可用
- [x] 知识库增量更新可用
- [x] 单元测试全部通过（257 passed, 2 skipped）

### 实际结果
- 所有任务完成
- 新增 5 个模块文件（retrieval/ 目录）
- 新增 1 个知识库模块（incremental.py）
- 新增 62 个单元测试
- 总测试数：257 passed, 2 skipped

---

## 下次迭代 #9 (v0.6.0)

### 版本目标
v0.6.0 - 游戏内代码执行与实时调试

### 迭代目标
实现游戏内代码执行、实时调试支持和性能分析工具

### 任务清单

#### 高优先级 🔥

**任务 1: 游戏内代码执行**
- [ ] 实现代码热重载机制
- [ ] 支持 Python 代码执行
- [ ] 实现执行结果捕获
- [ ] 支持错误反馈

**任务 2: 实时调试支持**
- [ ] 实现断点调试接口
- [ ] 支持变量监视
- [ ] 实现调用栈追踪
- [ ] 支持条件断点

**任务 3: 日志分析增强**
- [ ] 实现日志实时解析
- [ ] 支持错误模式匹配
- [ ] 实现性能日志分析
- [ ] 支持日志过滤

#### 中优先级

**任务 4: 性能分析工具**
- [ ] 实现代码性能分析
- [ ] 支持内存使用监控
- [ ] 生成性能报告
- [ ] 支持性能对比

#### 技术细节

**代码执行架构**:
```python
class CodeExecutor:
    def __init__(self, launcher: GameLauncher):
        self.launcher = launcher
        self.log_capture = LogCapture()
    
    async def execute(self, code: str) -> ExecutionResult:
        """执行代码并返回结果"""
        pass
    
    async def hot_reload(self, file_path: str) -> bool:
        """热重载代码文件"""
        pass
```

**调试器架构**:
```python
class Debugger:
    def __init__(self, game_process):
        self.breakpoints: dict[str, list[Breakpoint]] = {}
        self.watch_vars: dict[str, Any] = {}
    
    def set_breakpoint(self, file: str, line: int, condition: str = None) -> None:
        """设置断点"""
        pass
    
    def watch_variable(self, name: str) -> Any:
        """监视变量"""
        pass
```

### 预期产出
```
MC-Agent-Kit/
├── src/mc_agent_kit/
│   └── execution/            # 新增执行模块
│       ├── executor.py       # 代码执行器
│       ├── debugger.py       # 调试器
│       ├── hot_reload.py     # 热重载
│       └── performance.py    # 性能分析
└── skills/
    └── modsdk-debug-enhanced/ # 增强调试 Skill
        └── SKILL.md
```

### 验收标准
- [ ] 代码执行可用
- [ ] 实时调试可用
- [ ] 性能分析可用
- [ ] 单元测试全部通过

### 预计时间
1 个迭代周期

---

## 后续迭代预览

### 迭代 #10 (v0.7.0)
- 智能代码补全
- 代码重构建议
- 最佳实践推荐

### 迭代 #11 (v1.0.0)
- 完整用户文档
- 示例项目
- 正式发布

---

*文档版本：v0.1.8*
*最后更新：2026-03-22*