# 自定义 UI 示例模组

演示如何创建自定义 UI 界面。

## 功能

- 创建简单的 UI 界面
- 响应按钮点击事件
- 显示动态内容

## 文件结构

```
custom-ui/
├── mod.json
├── ui_demo.py
└── ui/
    └── demo_screen.json
```

## 使用方法

1. 将此目录复制到 ModSDK 开发目录
2. 重启游戏服务器
3. 使用命令打开 UI: `/function open_demo_ui`

## 测试

```bash
# 检查代码
mc-agent check -f ui_demo.py

# 搜索 UI 相关 API
mc-agent api -q "CreateUI"

# 搜索 UI 事件
mc-agent event -q "UI"
```