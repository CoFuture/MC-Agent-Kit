# 下次迭代计划

## 当前迭代 #6 (v0.3.1) ✅

### 版本目标
v0.3.1 - 代码生成与调试辅助

### 迭代目标
实现代码生成和调试辅助 Skills

### 任务清单

#### 高优先级 🔥

**任务 1: 代码生成 Skill**
- [x] 设计代码模板系统
- [x] 实现 `modsdk-code-gen` Skill
- [x] 支持常见代码模板（事件监听器、API 调用）
- [x] 测试验证

**任务 2: 调试辅助 Skill**
- [x] 设计错误诊断逻辑
- [x] 实现 `modsdk-debug` Skill
- [x] 集成日志解析器
- [x] 提供错误解决方案建议

**任务 3: Skill CLI 工具**
- [x] 实现 Skill 命令行入口
- [x] 支持交互式 Skill 调用
- [x] 支持批量操作

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
- [x] 代码生成 Skill 可用
- [x] 调试辅助 Skill 可用
- [x] CLI 工具可用
- [x] 单元测试全部通过

### 预计时间
1 个迭代周期

---

## 下次迭代 #7 (v0.4.0)

### 版本目标
v0.4.0 - 模板系统增强与 API 绑定生成

### 迭代目标
增强代码生成能力，支持更多模板类型和 API 绑定生成

### 任务清单

#### 高优先级 🔥

**任务 1: 模板系统增强**
- [ ] 支持从文件系统加载自定义模板
- [ ] 实现模板热重载
- [ ] 添加更多内置模板（方块、生物、维度）
- [ ] 支持模板继承和组合

**任务 2: API 绑定生成**
- [ ] 解析 ModSDK API 元数据
- [ ] 生成类型注解存根文件 (.pyi)
- [ ] 生成 API 文档索引
- [ ] 支持自动补全建议

**任务 3: 事件处理生成**
- [ ] 解析事件列表
- [ ] 生成事件监听器模板
- [ ] 支持参数验证代码生成
- [ ] 生成事件文档索引

#### 中优先级

**任务 4: 代码质量工具**
- [ ] 实现代码格式化检查
- [ ] 集成 ruff 检查
- [ ] 生成代码复杂度报告

#### 技术细节

**模板文件系统**:
```
templates/
├── builtin/          # 内置模板
├── custom/           # 用户自定义模板
└── cache/            # 模板缓存
```

**API 绑定生成**:
```python
class APIBindingGenerator:
    def generate_stubs(self, api_list: list[APIEntry]) -> str:
        """生成类型存根"""
        pass
    
    def generate_docs(self, api_list: list[APIEntry]) -> str:
        """生成文档"""
        pass
```

### 预期产出
```
MC-Agent-Kit/
├── src/mc_agent_kit/
│   └── generator/
│       ├── templates.py
│       ├── code_gen.py
│       └── bindings.py  # 新增
├── templates/           # 新增
│   └── builtin/
└── skills/
    └── modsdk-code-gen/
        └── SKILL.md
```

### 验收标准
- [ ] 支持自定义模板加载
- [ ] 生成类型存根文件
- [ ] 新增 5+ 内置模板
- [ ] 单元测试全部通过

### 预计时间
1 个迭代周期

---

## 后续迭代预览

### 迭代 #8 (v0.5.0)
- 向量检索集成（ChromaDB + LlamaIndex）
- 语义搜索增强
- 知识库增量更新

### 迭代 #9 (v0.6.0)
- 游戏内代码执行
- 实时调试支持
- 性能分析工具

---

*文档版本：v0.1.6*
*最后更新：2026-03-22*
