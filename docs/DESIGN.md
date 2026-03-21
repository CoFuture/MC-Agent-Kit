# MC-Agent-Kit 项目设计文档

## 1. 项目概述

### 1.1 项目名称
MC-Agent-Kit

### 1.2 项目愿景
构建一套 AI Agent 辅助工具包，赋能 AI Agent 参与网易 Minecraft ModSDK 的玩法 Addon 开发，降低开发门槛，提升开发效率。

### 1.3 项目定位
- **目标用户**: 网易 Minecraft ModSDK 开发者
- **核心价值**: 让 AI Agent 能够理解 ModSDK API、生成代码、调试测试、自动化开发流程
- **差异化**: 专注于网易版 Minecraft 的特殊性和本地开发环境

## 2. 技术架构

### 2.1 技术栈
| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 运行环境 | Python 3.13 | 项目主语言 |
| 包管理 | uv | 现代 Python 包管理器 |
| AI Agent | OpenClaw Skills | 技能扩展系统 |
| 游戏启动 | mc_launcher | 独立启动器，脱离 MC Studio |
| 日志采集 | TCP Server | 实时捕获游戏日志 |

### 2.2 目录结构
```
MC-Agent-Kit/
├── docs/                    # 项目文档 (本目录)
│   ├── DESIGN.md            # 设计文档
│   ├── ROADMAP.md           # 开发路线图
│   ├── PRINCIPLES.md        # 项目原则
│   ├── ITERATIONS.md        # 迭代记录
│   └── NEXT_ITERATION.md    # 下次迭代计划
├── resources/               # 参考资料 (只读，不上传git)
│   ├── docs/               # 官方文档
│   │   ├── mcdocs/         # ModAPI & Apollo 文档
│   │   ├── mcguide/        # 开发指南
│   │   ├── mconline/       # 在线教程
│   │   └── 6-1DemoMod/     # Demo 示例
│   └── mc_hook/            # 自动化工具原型
│       ├── config/         # 配置文件
│       └── mc_launcher.py  # 游戏启动器
├── src/                    # 源代码
│   ├── mc_agent_kit/       # 主包
│   │   ├── launcher/       # 游戏启动模块
│   │   ├── parser/         # 日志解析模块
│   │   ├── generator/      # 代码生成模块
│   │   └── skills/         # Agent Skills
│   └── tests/              # 测试用例
├── pyproject.toml          # 项目配置
└── README.md               # 项目说明
```

### 2.3 核心模块设计

#### 2.3.1 launcher 模块
游戏启动器模块，负责：
- 扫描 Addon 目录
- 生成启动配置
- 启动游戏进程
- 管理生命周期

参考: `resources/mc_hook/mc_launcher.py`

#### 2.3.2 parser 模块
日志解析模块，负责：
- 实时捕获游戏日志
- 解析错误信息
- 结构化日志数据
- 提供查询接口

#### 2.3.3 generator 模块
代码生成模块，负责：
- ModSDK 代码生成
- API 模板管理
- 代码片段复用

#### 2.3.4 skills 模块
Agent 技能模块，负责：
- OpenClaw Skill 封装
- API 文档检索
- 代码辅助生成
- 调试辅助功能

## 3. 数据流

```
用户指令 → AI Agent → Skill 调用
                          ↓
                    代码生成 / 游戏启动
                          ↓
                    日志捕获 → 错误分析 → 反馈用户
```

## 4. 与 ModSDK 的关系

### 4.1 ModSDK 特点
- 网易版 Minecraft 专用
- Python 2.7 运行环境 (游戏内)
- 基于 Apollo 框架
- 玩法 Addon 开发

### 4.2 本项目定位
本项目**不是** ModSDK 本身，而是：
- 辅助开发的工具链
- AI Agent 的能力扩展
- 自动化测试和调试

**注意区分**:
| 项目 | Python 版本 | 运行环境 |
|------|-------------|----------|
| ModSDK (游戏内) | Python 2.7 | MC 游戏进程 |
| MC-Agent-Kit (本项目) | Python 3.13 | 开发机器 |

## 5. 依赖关系

```
MC-Agent-Kit
    ├── Python 3.13
    ├── uv (包管理)
    └── OpenClaw (AI Agent 框架)

resources/ (参考，不打包)
    ├── ModSDK 文档
    ├── Apollo 文档
    └── mc_launcher 原型
```

## 6. 扩展性设计

### 6.1 Skill 扩展
每个 Skill 独立目录，包含：
- `SKILL.md` - Skill 说明
- `scripts/` - 脚本工具
- `templates/` - 代码模板

### 6.2 插件机制
支持动态加载：
- 自定义解析器
- 自定义生成器
- 自定义启动器

## 7. 安全考量

- 用户配置文件不入库 (含账号信息)
- resources/ 目录不上传 git
- 敏感信息通过环境变量管理

---

*文档版本: v0.1.0*
*最后更新: 2026-03-22*