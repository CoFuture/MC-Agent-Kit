# 下次迭代计划

## 当前迭代 #7 (v0.4.0) ✅

### 版本目标
v0.4.0 - 模板系统增强与 API 绑定生成

### 迭代目标
增强代码生成能力，支持更多模板类型和 API 绑定生成

### 任务清单

#### 高优先级 🔥

**任务 1: 模板系统增强**
- [x] 支持从文件系统加载自定义模板
- [x] 实现模板热重载
- [x] 添加更多内置模板（方块、维度）
- [x] 支持模板继承和组合

**任务 2: API 绑定生成**
- [x] 解析 ModSDK API 元数据
- [x] 生成类型注解存根文件 (.pyi)
- [x] 生成 API 文档索引
- [x] 支持自动补全建议

**任务 3: 事件处理生成**
- [x] 解析事件列表
- [x] 生成事件监听器模板
- [x] 支持参数验证代码生成
- [x] 生成事件文档索引

#### 中优先级

**任务 4: 代码质量工具**
- [x] 实现代码格式化检查
- [x] 集成 ruff 检查
- [x] 生成代码复杂度报告

### 预期产出
```
MC-Agent-Kit/
├── src/mc_agent_kit/
│   └── generator/
│       ├── templates.py
│       ├── code_gen.py
│       ├── template_loader.py  # 新增
│       ├── bindings.py         # 新增
│       ├── event_gen.py        # 新增
│       └── lint.py             # 新增
├── templates/                  # 用户自定义模板目录
└── skills/
    └── modsdk-code-gen/
        └── SKILL.md
```

### 验收标准
- [x] 支持自定义模板加载
- [x] 生成类型存根文件
- [x] 新增 2 种内置模板（block_register, dimension_config）
- [x] 单元测试全部通过（205 passed, 2 skipped）

### 实际结果
- 所有任务完成
- 新增 4 个模块文件
- 新增 40 个单元测试
- 总测试数：205 passed, 2 skipped

---

## 下次迭代 #8 (v0.5.0)

### 版本目标
v0.5.0 - 向量检索集成与语义搜索增强

### 迭代目标
集成向量数据库，实现语义搜索和知识库增量更新

### 任务清单

#### 高优先级 🔥

**任务 1: 向量检索集成**
- [ ] 集成 ChromaDB 向量数据库
- [ ] 实现文档向量化（使用 sentence-transformers）
- [ ] 实现语义搜索功能
- [ ] 支持混合搜索（关键词 + 语义）

**任务 2: LlamaIndex 集成**
- [ ] 集成 LlamaIndex 框架
- [ ] 实现向量存储（ChromaDB）
- [ ] 实现文档加载器
- [ ] 实现查询引擎

**任务 3: 知识库增量更新**
- [ ] 支持增量构建知识库
- [ ] 实现文档变更检测
- [ ] 支持增量向量化
- [ ] 实现向量索引更新

#### 中优先级

**任务 4: 搜索增强**
- [ ] 实现搜索结果重排序
- [ ] 支持多路召回
- [ ] 实现搜索结果解释
- [ ] 支持相关度评分

#### 技术细节

**向量检索架构**:
```python
class VectorRetriever:
    def __init__(self, chroma_path: str, embedding_model: str):
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_or_create_collection("modsdk")
        self.embedding_model = embedding_model
    
    def add_documents(self, docs: list[Document]) -> None:
        """添加文档到向量库"""
        pass
    
    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """语义搜索"""
        pass
    
    def hybrid_search(
        self,
        query: str,
        keyword_weight: float = 0.5,
        semantic_weight: float = 0.5,
    ) -> list[SearchResult]:
        """混合搜索"""
        pass
```

**LlamaIndex 集成**:
```python
class LlamaIndexRetriever:
    def __init__(self, chroma_path: str):
        self.vector_store = ChromaVectorStore(chroma_path)
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        self.index = VectorStoreIndex.from_documents(
            documents=[],
            storage_context=self.storage_context,
        )
    
    def query(self, query_str: str) -> Response:
        """查询"""
        pass
```

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
- [ ] ChromaDB 集成完成
- [ ] LlamaIndex 集成完成
- [ ] 语义搜索可用
- [ ] 混合搜索可用
- [ ] 知识库增量更新可用
- [ ] 单元测试全部通过

### 预计时间
1 个迭代周期

---

## 后续迭代预览

### 迭代 #9 (v0.6.0)
- 游戏内代码执行
- 实时调试支持
- 性能分析工具

### 迭代 #10 (v0.7.0)
- 智能代码补全
- 代码重构建议
- 最佳实践推荐

### 迭代 #11 (v1.0.0)
- 完整用户文档
- 示例项目
- 正式发布

---

*文档版本：v0.1.7*
*最后更新：2026-03-22*
