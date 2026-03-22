# MC-Agent-Kit 开发路线图

> 基于 [VISION.md](./VISION.md) 的实施计划
> 版本: v2.0.0
> 最后更新: 2026-03-22

---

## 当前阶段：MVP 基础闭环

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   检索      │ ──→ │   开发      │ ──→ │   测试      │
│ Knowledge   │     │ Scaffold    │     │ Launcher    │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## Phase 1: 基础设施 (Week 1-2)

### 1.1 游戏启动器修复 🔥 最高优先级

**目标**: 解决启动器的内存分配错误，实现稳定启动

- [ ] 对比 MC Studio 生成的配置文件
- [ ] 分析启动参数差异
- [ ] 修复配置生成逻辑
- [ ] 多版本兼容性测试
- [ ] 文档记录正确的启动方式

**验收标准**: 能稳定启动游戏并加载 Addon，无内存错误

---

### 1.2 知识库索引构建

**目标**: 完善知识库的索引和检索能力

- [ ] 优化 Markdown 文档解析器
- [ ] 提取 API 文档中的示例代码
- [ ] 构建统一索引结构 (UnifiedEntry)
- [ ] 集成本地 embedding (bge-large-zh)
- [ ] 实现混合检索 (语义 + 关键词)

**CLI 命令**:
```bash
mc-kb build [--full]    # 构建索引
mc-kb status            # 查看状态
```

---

### 1.3 基础检索功能

**目标**: 实现 `mc-kb search` 基础功能

- [ ] 实现语义搜索接口
- [ ] 实现精确 API/事件查询
- [ ] 返回结构化结果
- [ ] 集成到 `modsdk-search` Skill

**CLI 命令**:
```bash
mc-kb search <query>    # 语义搜索
mc-kb api <name>        # 精确查 API
mc-kb event <name>      # 精确查事件
```

---

## Phase 2: 核心闭环 (Week 3-4)

### 2.1 项目脚手架 🔥

**目标**: 实现 `mc-create` 创建标准项目结构

- [x] 创建 scaffold 模块
- [x] 实现 ProjectCreator 基础框架
- [ ] 实现 `mc-create project`
- [ ] 实现 `mc-create entity`
- [ ] 实现 `mc-create item`
- [ ] 实现 `mc-create block`

**CLI 命令**:
```bash
mc-create project <name>        # 创建项目
mc-create entity <name> [--in]  # 添加实体
```

---

### 2.2 启动器结构化输出

**目标**: `mc-run` 返回结构化 JSON 结果

- [ ] 定义输出 JSON Schema
- [ ] 捕获并解析游戏日志
- [ ] 提取错误和警告信息
- [ ] 超时控制
- [ ] 进程管理

**CLI 命令**:
```bash
mc-run <addon-path> [--timeout 60]
```

**输出示例**:
```json
{
  "success": true,
  "pid": 12345,
  "duration": 45,
  "logs": "path/to/logs.txt",
  "errors": [],
  "warnings": []
}
```

---

### 2.3 Skills 集成

**目标**: 将核心能力封装为 OpenClaw Skills

- [ ] `modsdk-search` - 知识检索
- [ ] `modsdk-diagnose` - 错误诊断
- [ ] Skill 文档编写
- [ ] 集成测试

---

## Phase 3: 增强 & 打磨 (Week 5-6)

### 3.1 错误诊断

- [ ] 日志解析器
- [ ] 错误模式识别
- [ ] 修复建议生成
- [ ] 关联文档推荐

---

### 3.2 示例代码增强

- [ ] Demo 项目解析
- [ ] 代码片段索引
- [ ] 代码关联到 API/事件

---

### 3.3 文档与测试

- [ ] 用户文档
- [ ] API 文档
- [ ] 单元测试完善
- [ ] 端到端测试

---

## 里程碑验收标准

| 里程碑 | 验收标准 | 状态 |
|--------|----------|------|
| M1: 启动器可用 | 能稳定启动游戏并加载 Addon，无内存错误 | 🔄 进行中 |
| M2: 知识检索有效 | 搜索 "创建实体" 能返回 CreateEntity API 和示例 | ⏳ 待开始 |
| M3: 创建项目可用 | `mc-create project` 能生成可运行的项目 | ⏳ 待开始 |
| M4: 闭环打通 | Agent 能完成：查文档 → 创建项目 → 启动测试 → 诊断错误 | ⏳ 待开始 |

---

## 后续迭代 (Phase 2+)

详见 [VISION.md](./VISION.md) 第八章「扩展方向」

- 热重载支持
- 需求分析与方案设计
- 自动化测试场景
- Git 操作集成
- 社区生态

---

*本文档采用敏捷迭代方式，每周更新进度。*