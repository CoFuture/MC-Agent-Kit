# 下次迭代计划

## 当前迭代 #3 (v0.2.0)

### 版本目标
v0.2.0 - 知识库设计与构建工具

### 迭代目标
分析 ModSDK 文档结构，设计知识库架构，实现文档解析和索引构建工具

### 任务清单

#### 高优先级 🔥

**任务 1: ModSDK 文档分析**
- [ ] 分析 `resources/docs/mcdocs/` 文档结构
- [ ] 分析 `resources/docs/mcguide/` 开发指南
- [ ] 分析 `resources/docs/mconline/` 在线教程
- [ ] 提取 API 文档结构
- [ ] 提取代码示例结构

**任务 2: 知识库设计**
- [ ] 设计知识库数据模型
- [ ] 设计索引结构 (API、事件、示例)
- [ ] 设计检索接口
- [ ] 确定存储方案 (SQLite/JSON/向量数据库)

**任务 3: 文档解析器实现**
- [ ] 实现 Markdown 解析器
- [ ] 实现 API 文档提取器
- [ ] 实现代码示例提取器
- [ ] 实现元数据提取

**任务 4: 索引构建工具**
- [ ] 实现索引生成器
- [ ] 实现增量更新机制
- [ ] 编写测试用例

#### 技术细节

**文档结构分析**:
```
resources/docs/mcdocs/
├── 1-ModAPI/          # 核心 API 文档
│   ├── 事件/          # 事件列表
│   ├── 接口/          # API 接口
│   └── 枚举值/        # 枚举定义
├── 2-Apollo/          # Apollo 框架
└── 3-PresetAPI/       # 预设 API
```

**知识库模型**:
```python
@dataclass
class APIEntry:
    name: str           # API 名称
    module: str         # 所属模块
    description: str    # 描述
    parameters: list    # 参数列表
    return_type: str    # 返回类型
    examples: list      # 示例代码
    source_path: str    # 文档来源
```

### 预期产出
```
MC-Agent-Kit/
├── src/mc_agent_kit/
│   └── knowledge_base/
│       ├── __init__.py
│       ├── models.py          # 数据模型
│       ├── parser.py          # 文档解析器
│       ├── indexer.py         # 索引构建器
│       └── retriever.py       # 检索接口
└── tests/
    └── test_knowledge_base.py
```

### 验收标准
- [ ] 能够解析 ModSDK 文档
- [ ] 能够提取 API 信息
- [ ] 能够构建检索索引
- [ ] 单元测试全部通过

### 预计时间
2-3 个迭代周期

---

## 后续迭代预览

### 迭代 #4 (v0.2.1)
- 实现知识库检索工具
- 语义搜索实现
- 搜索结果排序

### 迭代 #5 (v0.3.0)
- ModSDK 场景分析
- Agent 角色划分
- Skill 接口设计

---

*文档版本: v0.1.2*
*最后更新: 2026-03-22*