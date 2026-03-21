# 下次迭代计划

## 迭代 #2 规划

### 版本目标
v0.1.1 - 开发环境配置

### 迭代目标
- 配置 Python 开发环境
- 搭建测试框架
- 配置代码质量工具

### 任务清单

#### 必须完成
- [ ] 配置开发依赖 (pytest, ruff, mypy)
- [ ] 创建 `src/mc_agent_kit/` 包结构
- [ ] 配置 pytest 测试框架
- [ ] 编写第一个测试用例
- [ ] 配置 ruff 代码格式化
- [ ] 更新 pyproject.toml

#### 可选完成
- [ ] 配置 pre-commit hooks
- [ ] 配置 VS Code 调试配置
- [ ] 添加 Makefile 或 justfile

### 预期产出
```
MC-Agent-Kit/
├── src/
│   ├── mc_agent_kit/
│   │   └── __init__.py
│   └── tests/
│       └── test_init.py
└── pyproject.toml (更新)
```

### 验收标准
- [ ] `uv run pytest` 执行成功
- [ ] `uv run ruff check src/` 无错误
- [ ] 测试用例全部通过

### 预计时间
1 个迭代周期

---

## 后续迭代预览

### 迭代 #3 (v0.2.0)
- 迁移 mc_launcher.py
- 重构为模块化设计
- 添加配置验证

### 迭代 #4 (v0.2.1)
- 日志捕获模块
- 日志解析器
- 错误检测与分类

---

*文档版本: v0.1.0*
*最后更新: 2026-03-22*