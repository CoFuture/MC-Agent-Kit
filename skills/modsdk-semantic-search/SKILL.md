# ModSDK 语义搜索 Skill

## 概述

提供基于语义理解的 ModSDK 文档搜索功能。支持自然语言查询，结合关键词和语义搜索，提供更准确的检索结果。

## 工具说明

### mc_semantic_search

语义搜索 ModSDK 知识库。

**参数**:
- `query` (string, required): 自然语言查询
- `top_k` (integer, optional): 返回结果数量，默认 5
- `doc_type` (string, optional): 文档类型过滤 (api/event/guide/demo/all)，默认 all
- `search_mode` (string, optional): 搜索模式 (hybrid/semantic/keyword)，默认 hybrid

**返回**: 搜索结果列表，每个结果包含内容、分数和来源

### mc_index_documents

索引新文档到知识库。

**参数**:
- `documents` (array, required): 文档内容数组
- `metadatas` (array, optional): 文档元数据数组

**返回**: 索引状态

## 使用场景

1. **自然语言查询**: 用户用日常语言描述问题，系统理解意图并返回相关文档
2. **混合搜索**: 结合关键词精确匹配和语义相似度，提供更全面的结果
3. **增量更新**: 支持增量添加新文档，无需重建整个索引

## 示例用法

### 自然语言查询

```
用户: "如何创建一个可以移动的自定义实体？"

调用: mc_semantic_search(query="创建可移动的自定义实体", top_k=5)
```

### API 搜索

```
用户: "获取玩家坐标的 API 是什么？"

调用: mc_semantic_search(query="获取玩家坐标", doc_type="api", top_k=3)
```

### 混合搜索

```
用户: "实体碰撞检测相关的事件"

调用: mc_semantic_search(query="实体碰撞检测", doc_type="event", search_mode="hybrid")
```

## 搜索模式说明

### hybrid (混合搜索，推荐)
- 结合关键词和语义搜索
- 权重: 关键词 40%, 语义 60%
- 适合大多数查询场景

### semantic (纯语义搜索)
- 仅使用向量语义相似度
- 适合概念性查询
- 需要理解查询意图的场景

### keyword (纯关键词搜索)
- 仅使用 BM25 关键词匹配
- 适合精确术语查询
- 不依赖语义理解

## 依赖

- chromadb >= 0.5.0
- sentence-transformers >= 3.0.0

安装命令:
```bash
uv pip install mc-agent-kit[knowledge]
```

## 配置

可通过环境变量配置:
- `MC_KNOWLEDGE_PERSIST_DIR`: 知识库持久化目录
- `MC_EMBEDDING_MODEL`: Embedding 模型名称

---

*Skill 版本: v0.5.0*
*最后更新: 2026-03-22*