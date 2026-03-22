# MC-Agent-Kit 项目愿景与设计

> 版本: v1.0.0
> 最后更新: 2026-03-22

---

## 一、项目愿景

### 核心定位

**让 AI Agent 能够自主完成 Minecraft 网易版 ModSDK Addon 的开发闭环**

```
需求分析 → 代码开发 → 测试验证 → 迭代修复
```

### 设计原则

1. **Agent First** - 能力设计优先考虑 LLM 调用便利性
2. **最小闭环** - 早期聚焦核心流程，不贪多
3. **渐进增强** - 先可用，再好用，最后智能

### 目标用户

- AI Agent（通过 OpenClaw 等平台调用）
- ModSDK 开发者（通过 CLI 工具使用）

---

## 二、核心能力规划

### MVP 能力闭环

```
┌─────────────────────────────────────────────────────────────────┐
│                      MVP 能力闭环                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│   │   检索      │ ──→ │   开发      │ ──→ │   测试      │      │
│   │ Knowledge   │     │ Scaffold    │     │ Launcher    │      │
│   └─────────────┘     └─────────────┘     └─────────────┘      │
│         │                   │                   │              │
│         ▼                   ▼                   ▼              │
│   查 API/事件          创建项目结构        启动游戏验证          │
│   找示例代码          生成基础代码        捕获日志诊断          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 能力清单

| 能力模块 | 形式 | 核心功能 | 优先级 |
|---------|------|----------|--------|
| **知识检索** | Skill + CLI | API/事件文档检索、示例代码搜索 | P0 |
| **项目脚手架** | CLI | 创建标准 Addon 项目结构 | P0 |
| **游戏启动器** | CLI | 启动游戏+Addon、捕获日志 | P0 |
| **错误诊断** | Skill | 分析日志、定位错误、给出修复建议 | P1 |
| **代码生成** | Skill | 事件监听、API 调用等基础模板 | P1 |

---

## 三、架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          Agent Interface Layer                  │
│                     (Agent 直接调用的接口层)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────────────┐    ┌─────────────────────┐   │
│   │      OpenClaw Skills        │    │      CLI Tools      │   │
│   │    (原子能力，自然语言触发)   │    │  (复杂操作的简化封装) │   │
│   ├─────────────────────────────┤    ├─────────────────────┤   │
│   │ modsdk-search               │    │ mc-kb search        │   │
│   │ modsdk-diagnose             │    │ mc-create project   │   │
│   │ modsdk-code-gen             │    │ mc-create entity    │   │
│   └─────────────────────────────┘    │ mc-run              │   │
│                                       │ mc-logs             │   │
│                                       └─────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Core Capability Layer                  │
│                          (核心能力实现层)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Launcher      Scaffold       KnowledgeBase      Diagnoser    │
│   (游戏启动)     (项目脚手架)    (知识检索)         (错误诊断)    │
│                                                                 │
│   Generator     LogCapture     ConfigGen         Autofix       │
│   (代码生成)     (日志捕获)      (配置生成)         (自动修复)    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、模块详细设计

### 4.1 知识检索 (Knowledge)

#### Skill: `modsdk-search`

```
用途: 语义搜索 ModSDK 文档

输入:
  query: string      # 查询内容，如 "如何创建自定义实体"
  top_k: int         # 返回结果数量，默认 5

输出:
  {
    "apis": [          # 相关 API 列表
      {
        "name": "CreateEngineEntity",
        "description": "创建实体",
        "module": "实体",
        "scope": "server",
        "parameters": [...],
        "example": "..."
      }
    ],
    "events": [...],   # 相关事件列表
    "examples": [...], # 示例代码
    "guide": "..."     # 实现建议（可选）
  }
```

#### CLI: `mc-kb`

```bash
mc-kb search <query>           # 语义搜索
mc-kb api <name>               # 精确查 API
mc-kb event <name>             # 精确查事件
mc-kb build [--full]           # 构建/重建索引
mc-kb update                   # 增量更新索引
mc-kb status                   # 查看状态
```

#### 技术方案

- **Embedding**: 本地 bge-large-zh-v1.5（可切换到 API）
- **检索策略**: 混合检索，语义 60% + 关键词 40%
- **数据源**: 
  - 官方文档 (resources/docs/mcdocs)
  - 内嵌示例代码
  - Demo 项目（后续扩展）

#### 数据模型

```python
@dataclass
class UnifiedEntry:
    """统一索引条目"""
    id: str                          # 唯一标识
    type: str                        # api | event | example
    name: str                        # 名称
    description: str                 # 描述
    module: str                      # 模块：实体/物品/方块/UI
    scope: str                       # 作用域：client/server/both
    content: str                     # 主要内容
    code_examples: list[str]         # 代码示例
    parameters: list[dict]           # 参数说明
    related_apis: list[str]          # 相关 API
    related_events: list[str]        # 相关事件
    source: str                      # 来源
    source_path: str                 # 原始文件路径
    version: str                     # 文档版本
```

---

### 4.2 项目脚手架 (Scaffold)

#### CLI: `mc-create`

```bash
# 创建新项目
mc-create project <name> [--template <template>]
# 生成:
# my-addon/
# ├── behavior_pack/
# │   ├── manifest.json
# │   ├── entities/
# │   └── scripts/
# │       └── main.py
# └── resource_pack/
#     ├── manifest.json
#     └── textures/

# 在现有项目中添加实体
mc-create entity <name> [--in <path>]
# 生成:
# - behavior_pack/entities/<name>.json
# - behavior_pack/scripts/<name>.py
# - resource_pack/entity/<name>.geo.json
# - resource_pack/textures/entity/<name>.png

# 添加物品
mc-create item <name> [--in <path>]

# 添加方块
mc-create block <name> [--in <path>]
```

#### 模板类型

| 模板 | 描述 |
|------|------|
| `empty` | 空项目，只有基础结构 |
| `entity` | 包含实体开发模板 |
| `item` | 包含物品开发模板 |
| `block` | 包含方块开发模板 |

---

### 4.3 游戏启动器 (Launcher)

#### CLI: `mc-run`

```bash
mc-run <addon-path> [--timeout <seconds>] [--verbose]

# 输出 JSON 结果
{
  "success": true,
  "pid": 12345,
  "duration": 45,
  "logs": "path/to/logs.txt",
  "errors": [],
  "warnings": ["deprecated API: xxx"]
}
```

#### CLI: `mc-logs`

```bash
mc-logs [--analyze] [--tail] [--follow]
```

#### 配置管理

启动器需要生成正确的游戏配置文件 (.cppconfig)，包含：

- Addon 路径映射
- Behavior Pack / Resource Pack 列表
- 玩家信息
- 游戏设置

#### 待解决问题

- [ ] 内存分配错误修复
- [ ] 对比 MC Studio 生成的配置
- [ ] 不同游戏版本兼容性测试

---

### 4.4 错误诊断 (Diagnoser)

#### Skill: `modsdk-diagnose`

```
用途: 分析日志，诊断错误，给出修复建议

输入:
  logs: string       # 日志内容
  error: string      # 错误信息（可选）

输出:
  {
    "error_type": "KeyError",
    "error_message": "'speed' not found",
    "location": {
      "file": "main.py",
      "line": 42
    },
    "possible_causes": [
      "变量 speed 未定义",
      "字典中缺少 speed 键"
    ],
    "fix_suggestions": [
      {
        "description": "检查变量是否已定义",
        "code": "if 'speed' in config:\n    speed = config['speed']"
      }
    ],
    "related_docs": [
      "modsdk-search result..."
    ]
  }
```

---

### 4.5 代码生成 (Generator)

#### Skill: `modsdk-code-gen`

```
用途: 根据需求生成代码片段

输入:
  template: string   # 模板类型: event_listener, api_call, entity_create
  params: dict       # 模板参数

输出:
  {
    "code": "...",
    "imports": ["from mod.common import ..."],
    "dependencies": ["事件: OnServerChat"],
    "notes": ["需要在服务端运行"]
  }
```

#### 内置模板

| 模板 | 描述 | 参数 |
|------|------|------|
| `event_listener` | 事件监听器 | event_name, callback |
| `api_call` | API 调用 | api_name, params |
| `entity_create` | 创建实体 | entity_name, behaviors |
| `item_register` | 注册物品 | item_name, properties |

---

## 五、版本更新机制

### 配置

```yaml
# config/knowledge.yaml
knowledge_base:
  sources:
    - type: official_docs
      path: resources/docs/mcdocs
      version_file: VERSION.md
    
    - type: demos
      paths:
        - resources/docs/6-1DemoMod
      file_hash: true
  
  update_policy:
    auto_detect: true      # 启动时检测更新
    schedule: weekly       # 每周检查官方更新
    incremental: true      # 增量更新
```

### 更新流程

```
1. 检查版本文件 / 文件哈希
2. 识别变更：新增 / 修改 / 删除
3. 增量更新索引
4. 重新生成向量 embedding
5. 保存更新日志
```

---

## 六、实施路线图

### Week 1-2: 基础设施

- [ ] 修复启动器兼容性问题
- [ ] 完善知识库索引构建
- [ ] 实现 `mc-kb search` 基础功能
- [ ] 单元测试覆盖

### Week 3-4: 核心闭环

- [ ] 实现 `mc-create project`
- [ ] 实现 `mc-run` 结构化输出
- [ ] 集成 `modsdk-search` Skill
- [ ] 端到端测试

### Week 5-6: 增强 & 打磨

- [ ] 错误诊断能力
- [ ] 示例代码检索增强
- [ ] 文档完善
- [ ] 性能优化

---

## 七、成功标准

| 里程碑 | 验收标准 |
|--------|----------|
| M1: 启动器可用 | 能稳定启动游戏并加载 Addon，无内存错误 |
| M2: 知识检索有效 | 搜索 "创建实体" 能返回 CreateEntity API 和示例 |
| M3: 创建项目可用 | `mc-create project` 能生成可运行的项目 |
| M4: 闭环打通 | Agent 能完成：查文档 → 创建项目 → 启动测试 → 诊断错误 |

---

## 八、扩展方向（后续迭代）

### Phase 2: 增强开发体验

- 热重载支持
- 更多脚手架模板
- 代码补全增强
- 性能分析

### Phase 3: 智能化增强

- 需求分析与方案设计
- 自动化测试场景
- 回归测试
- 最佳实践检查

### Phase 4: 生态集成

- Git 操作集成
- 团队协作
- 模版市场
- 社区贡献

---

*本文档将随项目迭代持续更新。*