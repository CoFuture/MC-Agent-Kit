# 故障排查

本指南帮助你解决使用 MC-Agent-Kit 时遇到的常见问题。

## 安装问题

### 问题：pip 安装失败

**症状**：
```
Failed to build wheel for xxx
error: Microsoft Visual C++ 14.0 is required
```

**解决方案**：
1. 安装 Visual Studio Build Tools
   ```bash
   # 下载并安装
   # https://visualstudio.microsoft.com/visual-cpp-build-tools/
   ```
2. 或使用预编译包
   ```bash
   pip install --prefer-binary mc-agent-kit
   ```

### 问题：命令未找到

**症状**：
```
'mc-agent' is not recognized as an internal or external command
```

**解决方案**：
1. 确认安装成功
   ```bash
   pip show mc-agent-kit
   ```
2. 检查 PATH 环境变量包含 Python Scripts 目录
3. 重新安装
   ```bash
   pip install --force-reinstall mc-agent-kit
   ```

## 配置问题

### 问题：配置文件加载失败

**症状**：
```
Warning: Could not load config file
```

**解决方案**：
1. 检查配置文件格式
   ```bash
   # 验证 YAML 格式
   python -c "import yaml; yaml.safe_load(open('~/.mc-agent-kit/config.yaml'))"
   ```
2. 检查文件权限
   ```bash
   # Linux/macOS
   chmod 600 ~/.mc-agent-kit/config.yaml
   ```
3. 检查文件路径
   ```bash
   echo $MC_AGENT_KIT_CONFIG_PATH
   ```

### 问题：API Key 无效

**症状**：
```
Error: Invalid API key
```

**解决方案**：
1. 检查 API Key 格式
   ```bash
   echo $OPENAI_API_KEY
   ```
2. 确认 API Key 有效
   ```bash
   curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
   ```
3. 检查是否正确配置
   ```yaml
   providers:
     openai:
       api_key: ${OPENAI_API_KEY}  # 确保使用环境变量
   ```

## LLM 连接问题

### 问题：连接超时

**症状**：
```
Error: Connection timeout
```

**解决方案**：
1. 检查网络连接
2. 设置代理
   ```bash
   export OPENAI_PROXY="http://your-proxy:port"
   ```
3. 增加超时时间
   ```yaml
   providers:
     openai:
       timeout: 60  # 60 秒
   ```

### 问题：响应缓慢

**症状**：AI 响应时间过长

**解决方案**：
1. 使用更快的模型
   ```yaml
   providers:
     openai:
       model: gpt-3.5-turbo  # 比 gpt-4 更快
   ```
2. 启用流式输出
   ```yaml
   stream_output: true
   ```
3. 减少 max_tokens
   ```yaml
   providers:
     openai:
       max_tokens: 1024
   ```

### 问题：配额超限

**症状**：
```
Error: Rate limit exceeded
```

**解决方案**：
1. 检查使用量
2. 升级套餐
3. 添加重试逻辑
4. 使用备用提供商
   ```yaml
   default_provider: anthropic  # 切换到备用
   ```

## 知识库问题

### 问题：搜索无结果

**症状**：
```
No results found for query
```

**解决方案**：
1. 重建索引
   ```bash
   mc-kb build --full
   ```
2. 检查知识库状态
   ```bash
   mc-kb status
   ```
3. 尝试不同关键词
   ```bash
   mc-kb search "创建实体"  # 而不是 "怎么生成"
   ```

### 问题：索引构建失败

**症状**：
```
Error: Failed to build index
```

**解决方案**：
1. 检查磁盘空间
2. 检查内存使用
3. 清理旧索引
   ```bash
   rm -rf ~/.mc-agent-kit/index/
   mc-kb build
   ```

## 项目创建问题

### 问题：项目创建失败

**症状**：
```
Error: Failed to create project
```

**解决方案**：
1. 检查目录权限
   ```bash
   ls -la /path/to/create
   ```
2. 检查路径是否存在同名目录
3. 使用绝对路径
   ```bash
   mc-create project /absolute/path/to/project
   ```

### 问题：模板加载失败

**症状**：
```
Error: Template not found
```

**解决方案**：
1. 列出可用模板
   ```bash
   mc-create templates
   ```
2. 使用正确模板名
   ```bash
   mc-create project my-addon --template empty
   ```

## 运行问题

### 问题：游戏启动失败

**症状**：
```
Error: Failed to start game
```

**解决方案**：
1. 确认游戏已安装
   ```bash
   mc-run --check
   ```
2. 检查游戏路径
   ```yaml
   game_path: "C:/Games/Minecraft"
   ```
3. 检查 Addon 路径
   ```bash
   mc-run ./my-addon --verbose
   ```

### 问题：Addon 加载失败

**症状**：
```
Error: Failed to load addon
```

**解决方案**：
1. 检查 manifest.json 格式
   ```bash
   python -c "import json; json.load(open('manifest.json'))"
   ```
2. 检查文件结构
   ```bash
   tree my-addon
   ```
3. 查看详细错误
   ```bash
   mc-run ./my-addon --verbose
   ```

## 日志分析问题

### 问题：日志文件过大

**症状**：日志文件占用大量磁盘空间

**解决方案**：
1. 清理旧日志
   ```bash
   mc-logs --clean
   ```
2. 设置日志轮转
   ```yaml
   logging:
     max_size: 10MB
     backup_count: 5
   ```
3. 过滤日志
   ```bash
   mc-logs --level ERROR
   ```

### 问题：日志分析不准确

**症状**：错误诊断结果不准确

**解决方案**：
1. 提供更多上下文
   ```bash
   mc-llm diagnose "error" --code main.py --trace full_trace.txt
   ```
2. 使用交互模式
   ```bash
   mc-llm chat
   mc-llm> 详细描述你遇到的问题...
   ```

## 性能问题

### 问题：内存占用过高

**症状**：程序内存占用过大

**解决方案**：
1. 减少缓存大小
   ```yaml
   cache:
     max_size: 100MB
   ```
2. 禁用不需要的功能
   ```yaml
   semantic_search:
     enabled: false
   ```
3. 定期重启服务

### 问题：CPU 占用过高

**症状**：程序 CPU 使用率持续很高

**解决方案**：
1. 检查后台任务
   ```bash
   mc-kb status
   ```
2. 减少并发数
   ```yaml
   concurrent_requests: 2
   ```
3. 使用更小的模型

## 获取帮助

### 日志收集

收集诊断信息：

```bash
# 收集系统信息
mc-agent --version
mc-agent --info

# 收集日志
mc-logs --export > diagnostic.log
```

### 提交问题

提交问题时请包含：

1. 系统信息
   ```bash
   mc-agent --version
   python --version
   uname -a  # Linux/macOS
   # 或 systeminfo  # Windows
   ```

2. 错误信息
   ```
   完整的错误消息和堆栈跟踪
   ```

3. 重现步骤
   ```
   1. 执行 xxx 命令
   2. 输入 xxx
   3. 观察到 xxx 错误
   ```

4. 配置文件
   ```yaml
   # 脱敏后的配置
   providers:
     openai:
       api_key: "***"  # 隐藏敏感信息
   ```

### 社区支持

- 📖 [文档](./README.md)
- 💬 [GitHub Discussions](https://github.com/your-repo/discussions)
- 🐛 [Issue Tracker](https://github.com/your-repo/issues)

---

*最后更新: 2026-03-25*