# MC-Agent-Kit 知识库模块设计

## 1. 概述

知识库模块为 AI Agent 提供 MC ModSDK 开发知识的检索能力，支持：
- API 文档查询
- 代码示例检索
- 开发指南问答
- 错误诊断辅助

## 2. 技术选型

### 2.1 核心依赖

| 组件 | 包名 | 版本 | 用途 |
|------|------|------|------|
| RAG 框架 | llama-index | ^0.12.x | 文档索引与检索 |
| 向量存储 | chromadb | ^0.5.x | 向量数据库 |
| Embedding | sentence-transformers | ^3.0.x | 文本向量化 |
| 文档解析 | unstructured | ^0.15.x | 多格式文档解析 |

### 2.2 为什么选择 LlamaIndex？

1. **专注文档 RAG** - 核心优势是文档理解和检索
2. **丰富的索引策略** - 支持向量索引、关键词索引、混合索引
3. **Agent 集成** - 原生支持 LLM Agent 调用
4. **本地运行** - 无需外部 API，保护隐私
5. **活跃社区** - 持续更新，文档完善

## 3. 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Agent (调用方)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    KnowledgeBase (主接口)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   query()   │  │  search()   │  │  get_code() │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   ModAPIIndex   │ │   GuideIndex    │ │   DemoIndex     │
│  (API 文档索引)  │ │  (教程指南索引)  │ │  (示例代码索引)  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    VectorStore (ChromaDB)                    │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ modapi_chunks │  │ guide_chunks  │  │ demo_chunks   │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               EmbeddingModel (sentence-transformers)         │
│                    all-MiniLM-L6-v2 (轻量级)                  │
│                  或 text2vec-chinese (中文优化)              │
└─────────────────────────────────────────────────────────────┘
```

## 4. 模块设计

### 4.1 目录结构

```
src/mc_agent_kit/knowledge/
├── __init__.py
├── base.py              # 基础类定义
├── knowledge_base.py    # 主知识库类
├── indexes/
│   ├── __init__.py
│   ├── modapi.py        # ModAPI 索引
│   ├── guide.py         # 开发指南索引
│   └── demo.py          # Demo 示例索引
├── loaders/
│   ├── __init__.py
│   ├── markdown.py      # Markdown 加载器
│   ├── code.py          # 代码文件加载器
│   └── structured.py    # 结构化数据加载器
├── parsers/
│   ├── __init__.py
│   ├── api_table.py     # API 表格解析器
│   └── code_block.py    # 代码块提取器
└── utils/
    ├── __init__.py
    └── chunking.py      # 文档分块工具
```

### 4.2 核心接口

```python
from mc_agent_kit.knowledge import KnowledgeBase

# 初始化知识库
kb = KnowledgeBase(
    docs_path="resources/docs",
    persist_dir="data/knowledge_db"
)

# 语义搜索
results = kb.search("如何创建自定义实体", top_k=5)

# API 查询
api_info = kb.get_api("GetEngineType")

# 获取代码示例
code = kb.get_code_example("自定义物品", language="python")

# Agent 工具调用
tool_result = kb.query("AddEntityClientEvent 事件什么时候触发？")
```

## 5. 文档处理策略

### 5.1 文档分块策略

| 文档类型 | 分块策略 | 块大小 |
|----------|----------|--------|
| API 文档 | 按接口分块 | 每个接口一块 |
| 教程文档 | 按段落分块 | 512 tokens |
| 代码示例 | 按函数/类分块 | 完整代码块 |

### 5.2 元数据设计

每个文档块包含元数据：

```python
{
    "source": "mcdocs/1-ModAPI/接口/实体/GetEngineType.md",
    "doc_type": "api",  # api | guide | demo | event | enum
    "category": "实体",  # 分类
    "name": "GetEngineType",  # API 名称
    "language": "python",  # 代码语言（如适用）
    "chunk_index": 0,  # 分块索引
    "total_chunks": 1  # 总块数
}
```

## 6. Agent 集成

### 6.1 作为工具函数

```python
from mc_agent_kit.knowledge import create_knowledge_tool

# 创建 Agent 工具
tool = create_knowledge_tool(kb)

# 工具定义
{
    "name": "mc_knowledge_search",
    "description": "搜索 MC ModSDK 开发知识库，包括 API 文档、教程、示例代码",
    "parameters": {
        "query": "搜索关键词或问题",
        "doc_type": "api|guide|demo|all",
        "top_k": 5
    }
}
```

### 6.2 与 OpenClaw Skill 集成

```markdown
# SKILL.md

## 工具说明

mc_knowledge_search - 搜索 MC ModSDK 知识库

## 使用场景

- 查询 ModAPI 接口用法
- 查找开发教程
- 获取示例代码
- 错误诊断辅助

## 参数

- query (str): 搜索查询
- doc_type (str): 文档类型，可选 api/guide/demo/all
- top_k (int): 返回结果数量
```

## 7. 使用流程

### 7.1 首次构建索引

```python
from mc_agent_kit.knowledge import KnowledgeBase

kb = KnowledgeBase(
    docs_path="resources/docs",
    persist_dir="data/knowledge_db",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)

# 构建索引（首次运行）
kb.build_index()

# 持久化存储
kb.persist()
```

### 7.2 后续使用

```python
# 加载已有索引
kb = KnowledgeBase.load("data/knowledge_db")

# 搜索
results = kb.search("如何注册自定义物品")
```

## 8. 性能优化

### 8.1 增量更新

- 检测文档变更，只更新修改的部分
- 使用文件哈希判断是否需要重新索引

### 8.2 缓存策略

- 热门查询结果缓存
- Embedding 结果缓存

### 8.3 混合检索

- 向量检索 + 关键词检索
- 重排序提高相关性

## 9. 后续扩展

- [ ] 支持在线文档抓取更新
- [ ] 支持多语言（中/英）
- [ ] 支持图像文档（截图识别）
- [ ] 支持错误日志智能诊断
- [ ] 支持代码补全

---

*文档版本: v0.1.0*
*最后更新: 2026-03-22*