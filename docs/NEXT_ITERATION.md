# 下次迭代计划

## 当前迭代 #6 (v0.3.1)

### 版本目标
v0.3.1 - 代码生成与调试辅助

### 迭代目标
实现代码生成和调试辅助 Skills

### 任务清单

#### 高优先级 🔥

**任务 1: 代码生成 Skill**
- [ ] 设计代码模板系统
- [ ] 实现 `modsdk-code-gen` Skill
- [ ] 支持常见代码模板（事件监听、API 调用）
- [ ] 测试验证

**任务 2: 调试辅助 Skill**
- [ ] 设计错误诊断逻辑
- [ ] 实现 `modsdk-debug` Skill
- [ ] 集成日志解析器
- [ ] 提供错误解决方案建议

**任务 3: Skill CLI 工具**
- [ ] 实现 Skill 命令行入口
- [ ] 支持交互式 Skill 调用
- [ ] 支持批量操作

#### 技术细节

**代码模板设计**:
```python
class CodeTemplate:
    name: str
    description: str
    parameters: list[TemplateParameter]
    template: str  # Jinja2 模板
    
    def render(self, **kwargs) -> str:
        """渲染模板"""
        pass
```

**调试辅助设计**:
```python
class DebugSkill(BaseSkill):
    def diagnose(self, error_log: str) -> DebugResult:
        """诊断错误日志"""
        pass
    
    def suggest_solution(self, error: Error) -> list[Suggestion]:
        """提供解决方案建议"""
        pass
```

### 预期产出
```
MC-Agent-Kit/
├── src/mc_agent_kit/
│   └── skills/
│       └── modsdk/
│           ├── code_gen.py
│           └── debug.py
└── skills/
    ├── modsdk-code-gen/
    │   └── SKILL.md
    └── modsdk-debug/
        └── SKILL.md
```

### 验收标准
- [ ] 代码生成 Skill 可用
- [ ] 调试辅助 Skill 可用
- [ ] CLI 工具可用
- [ ] 单元测试全部通过

### 预计时间
1 个迭代周期

---

## 后续迭代预览

### 迭代 #7 (v0.4.0)
- 模板系统增强
- API 绑定生成
- 类型注解生成

### 迭代 #8 (v0.5.0)
- 向量检索集成（ChromaDB + LlamaIndex）
- 语义搜索增强
- 知识库增量更新

---

## 已完成迭代

### 迭代 #5 (v0.3.0) ✅

**完成内容**:
- [x] 场景分析
- [x] Skill 接口设计
- [x] `modsdk-api-search` Skill
- [x] `modsdk-event-search` Skill
- [x] 知识库集成
- [x] 单元测试 (34 个)

---

*文档版本：v0.1.5*
*最后更新：2026-03-22*
