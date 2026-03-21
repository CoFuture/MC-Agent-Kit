# 下次迭代计划

## 当前迭代 #5 (v0.3.0)

### 版本目标
v0.3.0 - Agent 技能封装

### 迭代目标
分析 ModSDK 开发场景，设计 Agent 角色和 Skill 接口

### 任务清单

#### 高优先级 🔥

**任务 1: 场景分析**
- [ ] 分析 ModSDK 开发流程
- [ ] 识别关键开发场景
- [ ] 定义 Agent 角色职责

**任务 2: Skill 接口设计**
- [ ] 设计 Skill 基类
- [ ] 定义 Skill 元数据格式
- [ ] 设计 Skill 注册机制

**任务 3: 核心 Skills 实现**
- [ ] `modsdk-api-search` - API 文档检索
- [ ] `modsdk-event-search` - 事件文档检索
- [ ] 测试验证

#### 技术细节

**Skill 基类设计**:
```python
class BaseSkill:
    name: str
    description: str
    version: str
    
    def execute(self, *args, **kwargs) -> SkillResult:
        """执行 Skill"""
        pass
```

**Skill 元数据**:
```yaml
name: modsdk-api-search
description: 搜索 ModSDK API 文档
version: 1.0.0
author: MC-Agent-Kit
```

### 预期产出
```
MC-Agent-Kit/
├── src/mc_agent_kit/
│   └── skills/
│       ├── __init__.py
│       ├── base.py
│       └── modsdk/
│           ├── __init__.py
│           ├── api_search.py
│           └── event_search.py
└── skills/                    # OpenClaw Skill 目录
    └── modsdk-api-search/
        └── SKILL.md
```

### 验收标准
- [ ] Skill 基类实现完成
- [ ] API 检索 Skill 可用
- [ ] 事件检索 Skill 可用
- [ ] 单元测试全部通过

### 预计时间
1 个迭代周期

---

## 后续迭代预览

### 迭代 #6 (v0.3.1)
- `modsdk-code-gen` - 代码生成
- `modsdk-debug` - 调试辅助

### 迭代 #7 (v0.4.0)
- 模板系统
- API 绑定生成
- 类型注解生成

---

*文档版本: v0.1.4*
*最后更新: 2026-03-22*