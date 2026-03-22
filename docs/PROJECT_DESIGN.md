# MC-Agent-Kit 项目设计文档

> 版本: v1.0.0
> 最后更新: 2026-03-22
> 作者: MC-Agent-Kit Team

---

## 目录

1. [项目概述](#一项目概述)
2. [系统架构](#二系统架构)
3. [核心模块设计](#三核心模块设计)
4. [接口规范](#四接口规范)
5. [数据模型](#五数据模型)
6. [部署与配置](#六部署与配置)
7. [测试策略](#七测试策略)

---

## 一、项目概述

### 1.1 项目背景

Minecraft 网易版 ModSDK 为开发者提供了丰富的 API 和事件接口，用于创建自定义游戏内容（实体、物品、方块、UI 等）。然而，ModSDK 开发面临以下挑战：

- **文档分散**：API 文档、事件文档、示例代码分散在不同位置
- **开发调试困难**：需要通过 MC Studio 启动游戏，流程繁琐
- **错误定位复杂**：游戏日志格式复杂，错误难以定位
- **缺乏智能辅助**：无法利用 AI 能力提升开发效率

### 1.2 项目目标

**让 AI Agent 能够自主完成 Minecraft 网易版 ModSDK Addon 的开发闭环**

```
需求分析 → 代码开发 → 测试验证 → 迭代修复
```

### 1.3 目标用户

| 用户类型 | 使用方式 | 主要需求 |
|---------|---------|---------|
| AI Agent | 通过 OpenClaw Skills 调用 | 原子能力、结构化输入输出 |
| 开发者 | 通过 CLI 工具使用 | 简化操作、提高效率 |

### 1.4 核心价值

1. **降低开发门槛** - 自动化繁琐的配置和启动流程
2. **提升开发效率** - 知识检索、代码生成、自动诊断
3. **实现智能闭环** - AI 可以自主完成开发迭代

---

## 二、系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Agent Interface Layer                           │
│                           (Agent 直接调用的接口层)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────────────────────────────┐    ┌───────────────────────────┐   │
│   │          OpenClaw Skills          │    │         CLI Tools         │   │
│   │       (原子能力，自然语言触发)      │    │    (复杂操作的简化封装)    │   │
│   ├───────────────────────────────────┤    ├───────────────────────────┤   │
│   │ • modsdk-search                   │    │ • mc-kb search            │   │
│   │ • modsdk-diagnose                 │    │ • mc-create project       │   │
│   │ • modsdk-code-gen                 │    │ • mc-create entity        │   │
│   │ • modsdk-autofix                  │    │ • mc-run                  │   │
│   │ • modsdk-best-practices           │    │ • mc-logs                 │   │
│   └───────────────────────────────────┘    └───────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Core Capability Layer                             │
│                              (核心能力实现层)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
│   │  Launcher   │ │  Scaffold   │ │ Knowledge   │ │  Diagnoser  │         │
│   │  (游戏启动)  │ │ (项目脚手架) │ │ Base(检索)  │ │  (错误诊断)  │         │
│   └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘         │
│                                                                             │
│   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
│   │  Generator  │ │ LogCapture  │ │ ConfigGen   │ │  Autofix    │         │
│   │  (代码生成)  │ │ (日志捕获)  │ │ (配置生成)  │ │  (自动修复)  │         │
│   └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           External Dependencies                              │
│                                (外部依赖)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐         │
│   │  Minecraft  │ │  MC Studio  │ │ ModSDK Docs │ │   Vector    │         │
│   │   (游戏)    │ │  (开发环境)  │ │  (官方文档)  │ │   Store     │         │
│   └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 模块依赖关系

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                                │
│                    (mc-kb, mc-create, mc-run)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Skill Layer                               │
│               (modsdk-search, modsdk-diagnose)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
│  Launcher  │  │  Scaffold  │  │ Knowledge  │  │ Diagnoser  │
│            │  │            │  │   Base     │  │            │
└────────────┘  └────────────┘  └────────────┘  └────────────┘
      │               │               │               │
      ▼               ▼               ▼               ▼
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
│ ConfigGen  │  │ Templates  │  │  Retrieval │  │ LogParser  │
│            │  │            │  │            │  │            │
└────────────┘  └────────────┘  └────────────┘  └────────────┘
                      │               │
                      ▼               ▼
                ┌────────────┐  ┌────────────┐
                │  Generator │  │ VectorStore│
                └────────────┘  └────────────┘
```

### 2.3 目录结构

```
mc-agent-kit/
├── src/
│   └── mc_agent_kit/
│       ├── __init__.py
│       ├── cli.py                    # CLI 入口
│       ├── launcher/                 # 游戏启动器
│       │   ├── __init__.py
│       │   ├── game_launcher.py      # 启动逻辑
│       │   ├── config_generator.py   # 配置生成
│       │   └── addon_scanner.py      # Addon 扫描
│       ├── scaffold/                 # 项目脚手架
│       │   ├── __init__.py
│       │   ├── project_creator.py    # 项目创建
│       │   └── templates/            # 项目模板
│       ├── knowledge_base/           # 知识库
│       │   ├── __init__.py
│       │   ├── models.py             # 数据模型
│       │   ├── indexer.py            # 索引构建
│       │   ├── parser.py             # 文档解析
│       │   └── retriever.py          # 检索器
│       ├── retrieval/                # 检索引擎
│       │   ├── __init__.py
│       │   ├── hybrid_search.py      # 混合搜索
│       │   ├── semantic_search.py    # 语义搜索
│       │   └── vector_store.py       # 向量存储
│       ├── generator/                # 代码生成
│       │   ├── __init__.py
│       │   ├── templates.py          # 代码模板
│       │   └── generator.py          # 生成器
│       ├── diagnoser/                # 错误诊断
│       │   ├── __init__.py
│       │   ├── log_parser.py         # 日志解析
│       │   ├── error_matcher.py      # 错误匹配
│       │   └── fix_suggester.py      # 修复建议
│       └── log_capture/              # 日志捕获
│           ├── __init__.py
│           └── tcp_server.py         # TCP 日志服务器
├── resources/
│   ├── docs/                         # ModSDK 文档
│   │   └── mcdocs/
│   └── templates/                    # 项目模板
├── tests/
│   ├── test_launcher.py
│   ├── test_knowledge_base.py
│   └── ...
├── docs/                             # 项目文档
│   ├── VISION.md                     # 项目愿景
│   ├── PROJECT_DESIGN.md             # 项目设计（本文档）
│   ├── ROADMAP.md                    # 开发路线图
│   └── user/                         # 用户文档
├── pyproject.toml
└── README.md
```

---

## 三、核心模块设计

### 3.1 知识检索模块 (Knowledge Base)

#### 职责

- 解析 ModSDK 官方文档
- 构建结构化索引
- 提供语义和关键词检索

#### 核心类

```python
class KnowledgeBase:
    """知识库核心类"""
    
    apis: dict[str, APIEntry]      # API 索引
    events: dict[str, EventEntry]  # 事件索引
    enums: dict[str, EnumEntry]    # 枚举索引
    
    def search(self, query: str, top_k: int = 5) -> SearchResult
    def get_api(self, name: str) -> APIEntry | None
    def get_event(self, name: str) -> EventEntry | None

class KnowledgeIndexer:
    """索引构建器"""
    
    def build(self, docs_dir: str) -> KnowledgeBase
    def save(self, path: str) -> None
    def load(self, path: str) -> KnowledgeBase

class HybridSearchEngine:
    """混合搜索引擎"""
    
    def index(self, documents: dict[str, str]) -> int
    def search(self, query: str, top_k: int = 10) -> list[SearchResult]
```

#### 检索流程

```
输入查询 → 意图识别 → 并行检索 → 融合排序 → 结果增强
    │           │           │           │           │
    ▼           ▼           ▼           ▼           ▼
 "创建实体"  API/方案    关键词+语义  加权评分    关联文档
```

#### 技术选型

| 组件 | 选型 | 说明 |
|------|------|------|
| Embedding | bge-large-zh-v1.5 | 本地运行，中文效果好 |
| Vector Store | ChromaDB | 轻量级，支持持久化 |
| 关键词搜索 | BM25 | 经典算法，效果稳定 |
| 分块策略 | 512 tokens | 句子边界分割 |

---

### 3.2 游戏启动器模块 (Launcher)

#### 职责

- 扫描 Addon 结构
- 生成游戏配置文件
- 启动游戏进程
- 捕获游戏日志

#### 核心类

```python
class GameLauncher:
    """游戏启动器"""
    
    def __init__(self, game_path: str, mc_studio_root: str)
    
    def launch(self, addon_path: str, timeout: int = 60) -> LaunchResult
    def stop(self) -> None
    def get_logs(self) -> list[str]

class AddonScanner:
    """Addon 扫描器"""
    
    def scan(self, addon_path: str) -> AddonInfo
    def get_behavior_packs(self) -> list[BehaviorPack]
    def get_resource_packs(self) -> list[ResourcePack]

class ConfigGenerator:
    """配置生成器"""
    
    def generate(self, addon: AddonInfo, options: dict) -> str
    # 生成 .cppconfig 文件
```

#### 启动流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 扫描 Addon  │ ──→ │ 生成配置    │ ──→ │ 启动游戏    │
└─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │
      ▼                   ▼                   ▼
 识别 BP/RP          .cppconfig          Minecraft.exe
   UUID 列表         启动参数            + 日志捕获
```

#### 配置文件结构

```json
{
  "version": "3.7.0.222545",
  "MainComponentId": "addon-uuid",
  "LocalComponentPathsDict": {
    "addon-uuid": {
      "cfg_path": "path/to/addon",
      "work_path": "path/to/addon"
    }
  },
  "world_info": {
    "level_id": "addon-uuid",
    "behavior_packs": ["BehaviorPackDir"],
    "resource_packs": ["ResourcePackDir"],
    "game_type": 1,
    "cheat": true
  },
  "player_info": {
    "user_id": 12345,
    "user_name": "Developer"
  },
  "misc": {
    "launcher_port": 12345,
    "auth_server_url": "https://..."
  }
}
```

---

### 3.3 项目脚手架模块 (Scaffold)

#### 职责

- 创建标准 Addon 项目结构
- 生成基础配置文件
- 提供开发模板

#### 核心类

```python
class ProjectCreator:
    """项目创建器"""
    
    def create_project(self, name: str, template: str = "empty") -> str
    def add_entity(self, name: str, project_path: str) -> list[str]
    def add_item(self, name: str, project_path: str) -> list[str]
    def add_block(self, name: str, project_path: str) -> list[str]

class TemplateManager:
    """模板管理器"""
    
    def get_template(self, name: str) -> Template
    def list_templates(self) -> list[str]
    def render(self, template: Template, params: dict) -> str
```

#### 项目结构模板

```
my-addon/
├── behavior_pack/
│   ├── manifest.json           # 行为包清单
│   ├── entities/               # 实体定义
│   │   └── *.json
│   ├── items/                  # 物品定义
│   │   └── *.json
│   ├── blocks/                 # 方块定义
│   │   └── *.json
│   └── scripts/                # Python 脚本
│       ├── __init__.py
│       └── main.py
├── resource_pack/
│   ├── manifest.json           # 资源包清单
│   ├── textures/               # 纹理资源
│   │   ├── entity/
│   │   ├── items/
│   │   └── blocks/
│   ├── models/                 # 模型文件
│   │   └── entity/
│   │       └── *.geo.json
│   └── animations/             # 动画文件
│       └── *.animation.json
└── README.md
```

---

### 3.4 错误诊断模块 (Diagnoser)

#### 职责

- 解析游戏日志
- 识别错误模式
- 生成修复建议

#### 核心类

```python
class LogParser:
    """日志解析器"""
    
    def parse(self, log_content: str) -> list[LogEntry]
    def extract_errors(self, logs: list[LogEntry]) -> list[ErrorInfo]

class ErrorMatcher:
    """错误匹配器"""
    
    def match(self, error: ErrorInfo) -> ErrorPattern | None

class FixSuggester:
    """修复建议生成器"""
    
    def suggest(self, error: ErrorInfo, context: dict) -> FixSuggestion
```

#### 错误诊断流程

```
游戏日志 → 解析结构化 → 错误提取 → 模式匹配 → 修复建议
    │           │           │           │           │
    ▼           ▼           ▼           ▼           ▼
 原始文本    LogEntry    ErrorInfo  ErrorPattern  FixSuggestion
```

#### 常见错误模式

| 错误类型 | 示例 | 诊断 |
|---------|------|------|
| KeyError | `KeyError: 'speed'` | 变量/字典键不存在 |
| AttributeError | `AttributeError: 'NoneType'` | 空对象调用属性 |
| ImportError | `ImportError: No module named 'xxx'` | 模块导入失败 |
| SyntaxError | `SyntaxError: invalid syntax` | 语法错误 |

---

## 四、接口规范

### 4.1 CLI 接口

#### mc-kb (知识库管理)

```bash
mc-kb search <query> [options]

Options:
  --type {api|event|example}    结果类型过滤
  --module <module>             模块过滤
  --top-k <n>                   返回数量 (default: 5)
  --format {json|text}          输出格式 (default: text)

Examples:
  mc-kb search "创建实体"
  mc-kb search "OnServerChat" --type event
  mc-kb api CreateEngineEntity
```

#### mc-create (项目脚手架)

```bash
mc-create project <name> [options]
mc-create entity <name> [options]
mc-create item <name> [options]
mc-create block <name> [options]

Options:
  --in <path>                   目标目录
  --template <name>             模板名称
  --force                       覆盖已存在的文件

Examples:
  mc-create project my-addon
  mc-create entity Dragon --in ./my-addon
```

#### mc-run (游戏启动器)

```bash
mc-run <addon-path> [options]

Options:
  --timeout <seconds>           超时时间 (default: 60)
  --verbose                     详细输出
  --log-file <path>             日志保存路径

Output (JSON):
{
  "success": true,
  "pid": 12345,
  "duration": 45,
  "logs": "path/to/logs.txt",
  "errors": [],
  "warnings": []
}

Examples:
  mc-run ./my-addon --timeout 120
```

#### mc-logs (日志管理)

```bash
mc-logs [options]

Options:
  --analyze                     分析日志
  --tail                        显示最后 N 行
  --follow                      实时跟踪
  --errors-only                 仅显示错误

Examples:
  mc-logs --analyze
  mc-logs --tail 100
```

---

### 4.2 Skills 接口

#### modsdk-search

```yaml
name: modsdk-search
description: 搜索 ModSDK 文档、API、事件
inputs:
  query:
    type: string
    description: 搜索查询
    required: true
  top_k:
    type: integer
    description: 返回结果数量
    default: 5
  type:
    type: string
    description: 结果类型过滤
    enum: [all, api, event, example]
    default: all
outputs:
  apis:
    type: array
    description: 相关 API 列表
  events:
    type: array
    description: 相关事件列表
  examples:
    type: array
    description: 示例代码列表
  guide:
    type: string
    description: 实现建议
```

#### modsdk-diagnose

```yaml
name: modsdk-diagnose
description: 分析游戏日志，诊断错误，给出修复建议
inputs:
  logs:
    type: string
    description: 日志内容
    required: true
  error:
    type: string
    description: 错误信息（可选）
outputs:
  error_type:
    type: string
    description: 错误类型
  error_message:
    type: string
    description: 错误信息
  possible_causes:
    type: array
    description: 可能的原因
  fix_suggestions:
    type: array
    description: 修复建议
  related_docs:
    type: array
    description: 相关文档
```

#### modsdk-code-gen

```yaml
name: modsdk-code-gen
description: 生成 ModSDK 代码片段
inputs:
  template:
    type: string
    description: 模板类型
    enum: [event_listener, api_call, entity_create, item_register]
    required: true
  params:
    type: object
    description: 模板参数
outputs:
  code:
    type: string
    description: 生成的代码
  imports:
    type: array
    description: 需要的导入
  dependencies:
    type: array
    description: 依赖项
  notes:
    type: array
    description: 注意事项
```

---

## 五、数据模型

### 5.1 知识库模型

```python
@dataclass
class APIEntry:
    """API 条目"""
    name: str                          # API 名称
    module: str                        # 所属模块
    description: str                   # 描述
    method_path: str                   # 完整方法路径
    scope: Scope                       # 作用域
    parameters: list[APIParameter]     # 参数列表
    return_type: str | None            # 返回类型
    return_description: str | None     # 返回值描述
    examples: list[CodeExample]        # 代码示例
    remarks: list[str]                 # 备注
    source_path: str | None            # 来源文件
    related_apis: list[str]            # 相关 API
    related_events: list[str]          # 相关事件

@dataclass
class EventEntry:
    """事件条目"""
    name: str                          # 事件名称
    module: str                        # 所属模块
    description: str                   # 描述
    scope: Scope                       # 作用域
    parameters: list[EventParameter]   # 参数列表
    examples: list[CodeExample]        # 代码示例
    remarks: list[str]                 # 备注
    source_path: str | None            # 来源文件
    related_apis: list[str]            # 相关 API

@dataclass
class UnifiedEntry:
    """统一索引条目（用于检索）"""
    id: str                            # 唯一标识
    type: str                          # api | event | example
    name: str                          # 名称
    description: str                   # 描述
    module: str                        # 模块
    scope: str                         # 作用域
    content: str                       # 主要内容
    code_examples: list[str]           # 代码示例
    parameters: list[dict]             # 参数说明
    related_apis: list[str]            # 相关 API
    related_events: list[str]          # 相关事件
    source: str                        # 来源
    source_path: str                   # 原始文件路径
    version: str                       # 文档版本
```

### 5.2 Addon 模型

```python
@dataclass
class AddonInfo:
    """Addon 信息"""
    id: str                            # Addon ID
    name: str                          # 名称
    path: str                          # 路径
    behavior_packs: list[BehaviorPack] # 行为包
    resource_packs: list[ResourcePack] # 资源包

@dataclass
class BehaviorPack:
    """行为包"""
    dir_name: str                      # 目录名
    uuid: str                          # UUID
    version: list[int]                 # 版本
    scripts: list[str]                 # 脚本文件

@dataclass
class ResourcePack:
    """资源包"""
    dir_name: str                      # 目录名
    uuid: str                          # UUID
    version: list[int]                 # 版本
    textures: list[str]                # 纹理文件
    models: list[str]                  # 模型文件
```

### 5.3 启动结果模型

```python
@dataclass
class LaunchResult:
    """启动结果"""
    success: bool                      # 是否成功
    pid: int | None                    # 进程 ID
    duration: int                      # 运行时长（秒）
    logs: str                          # 日志文件路径
    errors: list[ErrorInfo]            # 错误列表
    warnings: list[str]                # 警告列表
    config_path: str                   # 配置文件路径

@dataclass
class ErrorInfo:
    """错误信息"""
    type: str                          # 错误类型
    message: str                       # 错误信息
    file: str | None                   # 文件名
    line: int | None                   # 行号
    stack_trace: str | None            # 堆栈信息
```

---

## 六、部署与配置

### 6.1 安装方式

```bash
# 从 PyPI 安装
pip install mc-agent-kit

# 从源码安装
git clone https://github.com/your-org/mc-agent-kit.git
cd mc-agent-kit
uv sync
```

### 6.2 配置文件

```yaml
# ~/.mc-agent-kit/config.yaml
minecraft:
  game_path: "D:/MCStudioDownload/game/MinecraftPE_Netease/3.7.0.222545"
  mc_studio_root: "D:/MCStudioDownload"
  account: "your@email.com"

knowledge_base:
  docs_path: "./resources/docs/mcdocs"
  index_path: "./data/knowledge_index"
  embedding:
    provider: "local"                  # local | openai
    model: "bge-large-zh-v1.5"
  update_policy:
    auto_detect: true
    schedule: "weekly"

launcher:
  timeout: 60
  log_capture: true
  log_path: "./logs"
```

### 6.3 环境要求

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Python | >= 3.11 | 运行环境 |
| Minecraft 网易版 | >= 3.7.0 | 游戏客户端 |
| MC Studio | 最新版 | 开发环境（可选） |

---

## 七、测试策略

### 7.1 测试金字塔

```
           ┌─────────────┐
           │  E2E Tests  │    少量，验证完整流程
           │     (5%)    │
           ├─────────────┤
           │ Integration │    中等，验证模块交互
           │    (20%)    │
           ├─────────────┤
           │    Unit     │    大量，验证单个功能
           │    (75%)    │
           └─────────────┘
```

### 7.2 测试覆盖目标

| 模块 | 目标覆盖率 | 说明 |
|------|-----------|------|
| 知识库 | >= 90% | 核心功能，高覆盖 |
| 启动器 | >= 80% | 依赖外部环境 |
| 脚手架 | >= 90% | 文件操作，易测试 |
| 诊断器 | >= 85% | 模式匹配逻辑 |

### 7.3 测试命令

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/test_knowledge_base.py

# 生成覆盖率报告
pytest --cov=mc_agent_kit --cov-report=html

# 运行 E2E 测试
pytest tests/e2e/ --run-e2e
```

---

## 附录

### A. 参考资料

- [Minecraft ModSDK 官方文档](https://mc.163.com/developer/)
- [OpenClaw 文档](https://docs.openclaw.ai)
- [ChromaDB 文档](https://docs.trychroma.com/)

### B. 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| v1.0.0 | 2026-03-22 | 初始版本 |

---

*本文档将随项目迭代持续更新。*