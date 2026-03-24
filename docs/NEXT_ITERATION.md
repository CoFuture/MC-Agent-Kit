# 下次迭代计划

## 当前状态

**当前版本**: v1.48.0
**当前迭代**: #61 (已完成)
**下次迭代**: #62

---

## 迭代 #61 总结（已完成）

### 版本
v1.48.0

### 目标
AI 能力增强与智能代码生成

### 完成内容

#### 1. AI 能力增强 ✅

**新增 LLM 提供者支持**:
- `AnthropicClient` - 支持 Claude 3 系列模型（Opus/Sonnet/Haiku）
- `GeminiClient` - 支持 Google Gemini 系列模型（1.5 Pro/Flash/1.0 Pro）
- `EnhancedLLMClientFactory` - 增强的工厂类，统一所有 LLM 提供者

**模型选择器**:
- `ClaudeModelSelector` - 根据任务类型自动选择 Claude 模型
- `GeminiModelSelector` - 根据任务类型自动选择 Gemini 模型
- 支持任务类型：code_gen, analysis, creative, simple
- 支持优先级：quality, speed, cost, balanced

**验收标准**:
- Anthropic Claude 支持 ✅
- Google Gemini 支持 ✅
- 增强的工厂类 ✅
- 模型推荐功能 ✅

#### 2. 测试覆盖 ✅

**新增 `src/tests/test_iteration_61.py` (45 个测试)**:

**配置测试**:
- TestAnthropicConfig: Anthropic 配置测试 (2 个)
- TestGeminiConfig: Gemini 配置测试 (3 个)

**模型选择器测试**:
- TestClaudeModelSelector: Claude 模型选择器测试 (7 个)
- TestGeminiModelSelector: Gemini 模型选择器测试 (5 个)

**工厂类测试**:
- TestEnhancedLLMClientFactory: 增强工厂类测试 (6 个)
- TestCreateLLMClient: 创建客户端便捷函数测试 (2 个)
- TestGetRecommendedModel: 推荐模型函数测试 (6 个)

**客户端测试**:
- TestAnthropicClient: Anthropic 客户端测试 (3 个)
- TestGeminiClient: Gemini 客户端测试 (2 个)

**集成与验收测试**:
- TestIteration61Integration: 集成测试 (3 个)
- TestIteration61AcceptanceCriteria: 验收标准测试 (4 个)
- TestIteration61Performance: 性能测试 (2 个)

**测试验证**:
- 新增 45 个测试 ✅
- 所有测试通过 (45 passed) ✅
- 性能指标达标 ✅

### 验收标准完成情况

- [x] Anthropic Claude 支持完成 ✅
- [x] Google Gemini 支持完成 ✅
- [x] 增强的工厂类完成 ✅
- [x] 模型推荐功能完成 ✅
- [x] 所有测试通过 (45 passed) ✅

### 文件变更

```
新增文件:
- src/mc_agent_kit/skills/llm_providers/__init__.py
- src/mc_agent_kit/skills/llm_providers/anthropic_client.py    (~450 行)
- src/mc_agent_kit/skills/llm_providers/gemini_client.py       (~450 行)
- src/mc_agent_kit/skills/llm_providers/enhanced_factory.py    (~200 行)
- src/tests/test_iteration_61.py                               (45 个测试)

修改文件:
- docs/ITERATIONS.md                                           (迭代记录)
- docs/NEXT_ITERATION.md                                       (下次迭代计划)
- pyproject.toml                                               (版本升级到 1.48.0)
```

---

## 迭代 #62 计划

### 版本
v1.49.0

### 目标
知识库增强与检索优化

### 背景与动机

迭代 #61 已完成 AI 能力增强，支持了更多 LLM 提供者。为了进一步提升知识检索能力和智能推理水平，需要进行以下工作：

1. **知识库增强**: 优化知识检索算法和索引结构
2. **检索优化**: 改进混合检索策略，提升检索准确率
3. **推理能力**: 增强知识图谱推理和因果关系推理
4. **性能优化**: 优化检索性能，减少响应时间

### 功能规划

#### 1. 知识库增强

**索引优化**:
- 改进文档分块策略（按语义边界分块）
- 优化向量索引结构（HNSW 索引）
- 支持增量索引更新
- 索引压缩与缓存

**检索策略**:
- 改进混合检索算法（语义 70% + 关键词 30%）
- 添加重排序（Rerank）机制
- 支持多路召回
- 添加检索结果过滤

#### 2. 检索优化

**语义检索**:
- 支持多种 Embedding 模型（bge, m3e, text2vec）
- Embedding 模型切换与回退
- 批量 Embedding 生成
- Embedding 缓存

**关键词检索**:
- BM25 算法优化
- 支持中文分词优化
- 添加同义词扩展
- 支持模糊匹配

**结果融合**:
- RRF（Reciprocal Rank Fusion）融合算法
- 加权评分融合
- 多样性去重
- 结果解释性增强

#### 3. 推理能力增强

**知识图谱**:
- 扩展现有知识图谱模块
- 添加更多节点类型和关系类型
- 图谱路径查找优化
- 图谱推理规则增强

**因果推理**:
- 扩展因果规则库
- 支持多跳因果推理
- 因果链可视化
- 错误诊断推理增强

**上下文推理**:
- 上下文窗口优化
- 关键信息提取增强
- 上下文压缩算法改进
- 多轮对话推理

#### 4. 性能优化

**检索性能**:
- 检索响应时间 < 500ms
- 批量检索吞吐量提升
- 缓存命中率 > 80%
- 并发检索支持

**索引性能**:
- 索引构建时间优化
- 增量更新性能
- 索引大小优化
- 内存使用优化

### 验收标准

#### 功能验收
- [ ] 知识库索引优化完成
- [ ] 混合检索算法改进完成
- [ ] 知识图谱推理增强完成
- [ ] 性能指标达标

#### 测试验收
- [ ] 所有测试通过
- [ ] 测试覆盖率 > 85%
- [ ] 性能基准测试通过
- [ ] 无回归问题

#### 性能指标
- [ ] 检索响应时间 < 500ms
- [ ] 批量检索（10 次）< 3s
- [ ] 缓存命中率 > 80%
- [ ] 索引构建时间优化 30%

### 依赖项

- 依赖迭代 #61 的 LLM 集成优化
- 需要 Embedding 模型支持
- 需要知识图谱数据

### 时间估算

- 知识库增强：3-4 天
- 检索优化：2-3 天
- 推理能力增强：2-3 天
- 性能优化：2 天
- 测试与文档：2 天

**总计**: 11-14 天

---

## 迭代历史

| 迭代 | 版本 | 主题 | 状态 |
|------|------|------|------|
| #61 | v1.48.0 | AI 能力增强与智能代码生成 | ✅ 已完成 |
| #60 | v1.47.0 | CLI 用户体验优化与文档完善 | ✅ 已完成 |
| #59 | v1.46.0 | Bug 修复与用户体验优化 | ✅ 已完成 |
| #58 | v1.45.0 | 测试覆盖率提升与性能优化 | ✅ 已完成 |
| #57 | v1.44.0 | Agent 技能增强与 ModSDK 深度集成 | ✅ 已完成 |
| #56 | v1.43.0 | MCP 工具集成与 API 增强 | ✅ 已完成 |
| #55 | v1.42.0 | 知识库持续学习与自适应优化 | ✅ 已完成 |
