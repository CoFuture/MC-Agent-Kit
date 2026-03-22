# MC-Agent-Kit 故障排除指南

本文档提供了 MC-Agent-Kit 使用过程中常见问题的诊断和解决方法。

---

## 目录

1. [启动器问题](#启动器问题)
2. [配置文件问题](#配置文件问题)
3. [Addon 加载问题](#addon-加载问题)
4. [日志捕获问题](#日志捕获问题)
5. [知识库问题](#知识库问题)
6. [CLI 命令问题](#cli-命令问题)

---

## 启动器问题

### 问题：游戏启动后立即崩溃

**症状**：
- 游戏窗口闪现后立即关闭
- 控制台输出 "Assertion failed: We failed to allocate XXX bytes"
- 错误日志显示 "NO LOG FILE!" 或 "Device Lost"

**可能原因**：
1. 配置文件格式不正确
2. 游戏版本与 Addon 不兼容
3. 系统内存不足
4. 显卡驱动过旧

**诊断步骤**：

```bash
# 使用诊断工具检查配置
mc-agent launcher diagnose --addon-path <your-addon> --game-path <game-path>

# 或使用配置文件对比
mc-agent launcher compare --config-path <config-file>
```

**解决方案**：

1. **检查内存**：
   - 确保系统可用内存 > 4GB
   - 关闭其他占用内存的应用程序

2. **检查配置文件**：
   ```bash
   # 自动修复配置文件
   mc-agent launcher fix --config-path <config-file>
   ```

3. **检查显卡驱动**：
   - 更新显卡驱动到最新版本
   - 确保显卡支持游戏要求的 DirectX 版本

---

### 问题：找不到游戏路径

**症状**：
- 错误信息：`未找到游戏可执行文件`
- 诊断报告显示 `GAME_PATH_NOT_FOUND`

**解决方案**：

1. **手动指定路径**：
   ```bash
   mc-agent run <addon-path> --game-path "C:\path\to\Minecraft.Windows.exe"
   ```

2. **检查默认路径**：
   MC-Agent-Kit 会在以下位置查找游戏：
   - `%LOCALAPPDATA%\Netease\MCStudio\x64_mc\Minecraft.Windows.exe`
   - `%LOCALAPPDATA%\Netease\MCStudio\Minecraft.Windows.exe`
   - `C:\Program Files\Netease\MCStudio\x64_mc\Minecraft.Windows.exe`

3. **验证 MC Studio 安装**：
   - 确保 MC Studio 已正确安装
   - 检查环境变量 `LOCALAPPDATA` 是否正确设置

---

### 问题：游戏启动但 Addon 未加载

**症状**：
- 游戏正常启动，但 Addon 内容未出现
- 行为包/资源包未生效

**诊断步骤**：

```bash
# 检查 Addon 结构
mc-agent launcher diagnose --addon-path <your-addon>
```

**解决方案**：

1. **检查 Addon 目录结构**：
   ```
   my-addon/
   ├── behavior_pack/
   │   ├── manifest.json
   │   └── scripts/
   └── resource_pack/
       └── manifest.json
   ```

2. **验证 manifest.json**：
   - 确保 `format_version` 正确
   - 确保 `header` 包含 `uuid` 和 `version`
   - 确保 `modules` 正确定义

3. **检查配置文件中的 Pack 配置**：
   ```json
   "world_info": {
     "behavior_packs": ["behavior_pack"],
     "resource_packs": ["resource_pack"]
   }
   ```

---

## 配置文件问题

### 问题：配置文件缺少必要字段

**症状**：
- 错误信息：`配置文件缺少必要字段: xxx`
- 游戏无法启动或行为异常

**解决方案**：

1. **使用自动修复**：
   ```bash
   mc-agent launcher fix --config-path <config-file>
   ```

2. **手动添加字段**：
   参考 [配置文件模板](#配置文件模板) 补充缺失字段

3. **重新生成配置**：
   ```bash
   mc-agent run <addon-path> --output-dir <output-dir>
   ```

---

### 问题：配置文件路径无效

**症状**：
- 错误信息：`配置文件中的 Addon 路径无效`
- 路径指向不存在的目录

**解决方案**：

1. **检查路径配置**：
   ```json
   "LocalComponentPathsDict": {
     "addon_id": {
       "cfg_path": "/correct/path/to/addon",
       "work_path": "/correct/path/to/addon"
     }
   }
   ```

2. **使用绝对路径**：
   - 确保路径存在
   - 避免使用相对路径
   - 注意 Windows 路径分隔符 (`\` 或 `/`)

---

### 配置文件模板

```json
{
  "version": "1.0.0",
  "client_type": 0,
  "MainComponentId": "your-addon-id",
  "LocalComponentPathsDict": {
    "your-addon-id": {
      "cfg_path": "C:/path/to/addon",
      "work_path": "C:/path/to/addon"
    }
  },
  "world_info": {
    "level_id": "your-addon-id",
    "game_type": 1,
    "difficulty": 2,
    "permission_level": 1,
    "cheat": true,
    "cheat_info": {
      "pvp": true,
      "show_coordinates": false,
      "always_day": false,
      "daylight_cycle": true,
      "fire_spreads": true,
      "tnt_explodes": true,
      "keep_inventory": true,
      "mob_spawn": true,
      "natural_regeneration": true,
      "mob_loot": true,
      "mob_griefing": true,
      "tile_drops": true,
      "entities_drop_loot": true,
      "weather_cycle": true,
      "command_blocks_enabled": true,
      "random_tick_speed": 1,
      "experimental_holiday": false,
      "experimental_biomes": false,
      "fancy_bubbles": false
    },
    "resource_packs": ["resource_pack"],
    "behavior_packs": ["behavior_pack"],
    "name": "Your Addon Name",
    "world_type": 2,
    "start_with_map": false,
    "bonus_items": false,
    "seed": ""
  },
  "room_info": {
    "ip": "",
    "port": 0,
    "muiltClient": false,
    "room_name": "",
    "token": "",
    "room_id": 0,
    "host_id": 0,
    "allow_pe": true,
    "max_player": 0,
    "visibility_mode": 0,
    "is_pe": true
  },
  "player_info": {
    "user_id": 0,
    "user_name": "",
    "urs": ""
  },
  "anti_addiction_info": {
    "enable": false,
    "left_time": 0,
    "exp_multiplier": 1.0,
    "block_multplier": 1.0,
    "first_message": ""
  },
  "misc": {
    "multiplayer_game_type": 0,
    "is_store_enabled": 1
  },
  "vip_using_mod": [],
  "isCloud": false
}
```

---

## Addon 加载问题

### 问题：manifest.json 解析错误

**症状**：
- 错误信息：`manifest.json 格式错误`
- JSON 解析失败

**解决方案**：

1. **验证 JSON 格式**：
   ```bash
   # 使用 Python 验证 JSON
   python -m json.tool manifest.json
   ```

2. **检查常见错误**：
   - 缺少逗号
   - 多余的尾随逗号
   - 未转义的引号
   - 缺少闭合括号

3. **使用诊断工具**：
   ```bash
   mc-agent launcher diagnose --addon-path <your-addon>
   ```

---

### 问题：UUID 冲突

**症状**：
- Addon 无法加载
- 多个 Addon 使用相同 UUID

**解决方案**：

1. **生成新的 UUID**：
   ```python
   import uuid
   print(str(uuid.uuid4()))
   ```

2. **确保唯一性**：
   - behavior_pack 和 resource_pack 使用不同的 UUID
   - 不同 Addon 使用不同的 UUID

---

## 日志捕获问题

### 问题：无法启动日志服务器

**症状**：
- 警告：`无法启动日志服务器`
- 端口被占用

**解决方案**：

1. **指定其他端口**：
   ```bash
   mc-agent run <addon-path> --log-port 9999
   ```

2. **禁用日志捕获**：
   ```bash
   mc-agent run <addon-path> --no-logs
   ```

3. **检查防火墙**：
   - 确保 127.0.0.1 的端口未被阻止
   - 检查是否有其他程序占用端口

---

### 问题：日志分析无结果

**症状**：
- `mc-agent logs analyze` 返回空结果
- 无法解析日志内容

**解决方案**：

1. **检查日志格式**：
   - 确保日志内容是文本格式
   - 检查日志是否来自正确的游戏版本

2. **使用详细输出**：
   ```bash
   mc-agent logs analyze --file <log-file> --verbose
   ```

---

## 知识库问题

### 问题：知识库索引未找到

**症状**：
- 错误信息：`知识库索引文件不存在`
- `mc-kb search` 无法使用

**解决方案**：

1. **构建知识库索引**：
   ```bash
   python build_knowledge_base.py
   ```

2. **检查索引文件**：
   - 确认 `data/knowledge_base.json` 存在
   - 检查文件权限

---

### 问题：搜索结果不准确

**症状**：
- 搜索 "创建实体" 未返回相关结果
- 结果与查询不相关

**解决方案**：

1. **使用更精确的关键词**：
   ```bash
   mc-kb api -n CreateEngineEntity
   ```

2. **按模块过滤**：
   ```bash
   mc-kb search "实体" -m "实体模块"
   ```

---

## CLI 命令问题

### 问题：命令未找到

**症状**：
- `mc-agent: command not found`
- 命令无法执行

**解决方案**：

1. **检查安装**：
   ```bash
   pip show mc-agent-kit
   ```

2. **重新安装**：
   ```bash
   pip install -e .
   ```

3. **检查 PATH**：
   - 确保 Python scripts 目录在 PATH 中
   - Windows: `%APPDATA%\Python\Scripts`
   - Linux/macOS: `~/.local/bin`

---

### 问题：命令参数错误

**症状**：
- `error: unrecognized arguments`
- 参数不生效

**解决方案**：

1. **查看帮助**：
   ```bash
   mc-agent <command> --help
   ```

2. **检查参数格式**：
   - JSON 参数需要用引号包裹
   - 路径参数注意转义

---

## 获取更多帮助

如果以上方案无法解决问题：

1. **查看详细文档**：`docs/` 目录
2. **运行诊断**：`mc-agent launcher diagnose`
3. **提交 Issue**：GitHub Issues
4. **联系开发团队**：通过飞书群组

---

*文档版本: v1.0.0*
*最后更新: 2026-03-22*