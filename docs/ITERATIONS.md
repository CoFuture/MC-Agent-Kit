# MC-Agent-Kit 迭代记录

本文档记录项目的每次迭代历史，包括完成内容、遇到的问题和经验总结。

---

## 迭代索引

| 迭代 | 版本 | 日期 | 主要内容 | 状态 |
|------|------|------|----------|------|
| #1 | v0.1.0 | 2026-03-22 | 项目初始化与文档框架 | ✅ 完成 |
| #2 | v0.1.1 | 2026-03-22 | 游戏启动器与日志捕获 | ✅ 完成 |

---

## 迭代 #1 (2026-03-22)

### 版本
v0.1.0

### 目标
- 初始化项目文档结构
- 建立开发规范和原则
- 配置 Git 仓库

### 完成内容
1. 创建 `docs/` 目录结构
2. 编写 `DESIGN.md` - 项目设计文档
3. 编写 `ROADMAP.md` - 开发路线图
4. 编写 `PRINCIPLES.md` - 项目原则
5. 编写 `ITERATIONS.md` - 迭代记录
6. 编写 `NEXT_ITERATION.md` - 下次迭代计划

### 遇到的问题
- 无

### 经验总结
- 文档先行有助于明确项目方向
- 渐进式迭代可以降低开发风险

### 文件变更
- 新增: `docs/DESIGN.md`
- 新增: `docs/ROADMAP.md`
- 新增: `docs/PRINCIPLES.md`
- 新增: `docs/ITERATIONS.md`
- 新增: `docs/NEXT_ITERATION.md`

---

## 迭代 #2 (2026-03-22)

### 版本
v0.1.1

### 目标
- 实现自动化拉起 Minecraft 开发调试程序
- 实现日志捕获和解析
- 配置定时迭代 Cron 任务

### 进行中
- [ ] 游戏启动器实现
- [ ] 日志捕获实现
- [ ] 测试验证

### 已完成
- [x] 更新 ROADMAP.md 重新规划任务优先级
- [x] 更新 NEXT_ITERATION.md 设置迭代计划
- [x] 创建 Cron 任务 (每30分钟执行迭代)
- [x] 创建项目包结构 `src/mc_agent_kit/`
- [x] 实现 Addon 扫描模块 `launcher/addon_scanner.py`
- [x] 实现配置生成模块 `launcher/config_generator.py`
- [x] 实现游戏启动模块 `launcher/game_launcher.py`
- [x] 实现 TCP 日志服务器 `log_capture/tcp_server.py`
- [x] 实现日志解析器 `log_capture/parser.py`
- [x] 编写单元测试 (18个测试全部通过)
- [x] 代码格式检查通过 (ruff)

### 遇到的问题
- ruff 检查发现裸 except 问题，已修复为 `except Exception`

### 经验总结
- 使用 dataclass 简化数据结构定义
- 日志解析需要处理多种格式

### 文件变更
- 新增: `src/mc_agent_kit/__init__.py`
- 新增: `src/mc_agent_kit/launcher/__init__.py`
- 新增: `src/mc_agent_kit/launcher/addon_scanner.py`
- 新增: `src/mc_agent_kit/launcher/config_generator.py`
- 新增: `src/mc_agent_kit/launcher/game_launcher.py`
- 新增: `src/mc_agent_kit/log_capture/__init__.py`
- 新增: `src/mc_agent_kit/log_capture/tcp_server.py`
- 新增: `src/mc_agent_kit/log_capture/parser.py`
- 新增: `src/tests/test_launcher.py`
- 新增: `src/tests/test_parser.py`
- 修改: `pyproject.toml`

---

## 迭代模板

```markdown
## 迭代 #N (YYYY-MM-DD)

### 版本
vX.Y.Z

### 目标
- 目标 1
- 目标 2

### 完成内容
1. 完成项 1
2. 完成项 2

### 遇到的问题
- 问题描述及解决方案

### 经验总结
- 经验 1
- 经验 2

### 文件变更
- 新增: path/to/file
- 修改: path/to/file
- 删除: path/to/file
```

---

*文档版本: v0.1.0*
*最后更新: 2026-03-22*