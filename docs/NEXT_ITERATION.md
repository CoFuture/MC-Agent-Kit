# 下次迭代计划

## 当前迭代 #4 (v0.2.1)

### 版本目标
v0.2.1 - 知识库检索工具

### 迭代目标
实现知识库检索功能，支持语义搜索和关键词搜索

### 任务清单

#### 高优先级 🔥

**任务 1: 实现检索器**
- [ ] 实现 `Retriever` 类
- [ ] 支持关键词搜索
- [ ] 支持模块过滤
- [ ] 支持作用域过滤

**任务 2: 构建完整知识库**
- [ ] 解析 `resources/docs/mcdocs/` 全部文档
- [ ] 生成知识库索引文件
- [ ] 测试解析完整性

**任务 3: 测试验证**
- [ ] 编写检索器测试用例
- [ ] 验证搜索结果准确性

#### 技术细节

**检索接口设计**:
```python
class KnowledgeRetriever:
    def search(self, query: str, entry_type: str = "all") -> list:
        """搜索知识库"""
        pass
    
    def search_api(self, keyword: str, scope: Scope = None) -> list[APIEntry]:
        """搜索 API"""
        pass
    
    def search_event(self, keyword: str, scope: Scope = None) -> list[EventEntry]:
        """搜索事件"""
        pass
```

**知识库文件位置**:
```
data/knowledge_base.json
```

### 预期产出
```
MC-Agent-Kit/
├── src/mc_agent_kit/
│   └── knowledge_base/
│       ├── __init__.py
│       ├── models.py
│       ├── parser.py
│       ├── indexer.py
│       └── retriever.py    # 新增
└── data/
    └── knowledge_base.json  # 新增
```

### 验收标准
- [ ] 能够搜索 API 和事件
- [ ] 能够按模块过滤
- [ ] 能够按作用域过滤
- [ ] 单元测试全部通过

### 预计时间
1 个迭代周期

---

## 后续迭代预览

### 迭代 #5 (v0.3.0)
- ModSDK 场景分析
- Agent 角色划分
- Skill 接口设计

### 迭代 #6 (v0.3.1)
- 核心 Skills 实现
- `modsdk-api-search` - API 文档检索
- `modsdk-code-gen` - 代码生成

---

*文档版本: v0.1.3*
*最后更新: 2026-03-22*