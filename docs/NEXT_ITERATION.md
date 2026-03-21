# 下次迭代计划

## 当前迭代 #2 (v0.1.1)

### 版本目标
v0.1.1 - 游戏启动器与日志捕获

### 迭代目标
实现自动化拉起 Minecraft 开发调试程序，加载指定 Addon 脚本，获取运行时日志

### 任务清单

#### 高优先级 🔥

**任务 1: 游戏启动器实现**
- [ ] 分析 `resources/mc_hook/mc_launcher.py` 参考代码
- [ ] 分析 `resources/run_test_command` 启动命令
- [ ] 设计模块化架构
- [ ] 实现 Addon 扫描功能
- [ ] 实现配置生成功能
- [ ] 实现游戏进程启动功能

**任务 2: 日志捕获实现**
- [ ] 实现 TCP 日志服务器
- [ ] 实现日志解析器
- [ ] 实现日志结构化存储
- [ ] 实现错误检测

**任务 3: 测试验证**
- [ ] 编写单元测试
- [ ] 本地测试验证
- [ ] 文档更新

#### 技术细节

**启动命令参考**:
```
Minecraft.Windows.exe
  config=<cppconfig路径>
  errorlog=<错误日志路径>
  dc_tag1=studio_no_launcher
  dc_web=<网关地址>
  dc_uid=<用户ID>
  loggingIP=<日志接收IP>
  loggingPort=<日志接收端口>
```

**日志捕获**:
- 通过 TCP Server 接收游戏日志
- 解析日志内容
- 识别错误和警告
- 结构化存储

### 预期产出
```
MC-Agent-Kit/
├── src/
│   └── mc_agent_kit/
│       ├── __init__.py
│       ├── launcher/
│       │   ├── __init__.py
│       │   ├── addon_scanner.py    # Addon 扫描
│       │   ├── config_generator.py # 配置生成
│       │   └── game_launcher.py    # 游戏启动
│       └── log_capture/
│           ├── __init__.py
│           ├── tcp_server.py       # TCP 日志服务
│           ├── parser.py           # 日志解析
│           └── storage.py          # 日志存储
└── tests/
    └── test_launcher.py
```

### 验收标准
- [ ] 能够扫描 Addon 目录
- [ ] 能够生成启动配置
- [ ] 能够启动游戏进程
- [ ] 能够捕获游戏日志
- [ ] 单元测试全部通过

### 预计时间
1-2 个迭代周期

---

## 后续迭代预览

### 迭代 #3 (v0.2.0)
- 知识库设计
- 文档解析器
- 索引结构设计

### 迭代 #4 (v0.3.0)
- ModSDK 场景分析
- Agent 角色划分
- Skill 接口设计

---

*文档版本: v0.1.1*
*最后更新: 2026-03-22*