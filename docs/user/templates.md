# 项目模板使用指南

> 版本: v1.45.0
> 最后更新: 2026-03-24

---

## 概述

项目模板系统提供了 Minecraft 网易版 ModSDK Addon 的项目模板生成功能，包括：

- 18 种内置模板
- 模板变量渲染
- 项目结构生成
- 文件写入支持

---

## 快速开始

### 基本使用

```python
from mc_agent_kit.templates.project_templates import create_project_templates

# 创建模板系统实例
templates = create_project_templates()

# 生成项目
project = templates.generate(
    template_type=TemplateType.PROJECT_EMPTY,
    name="MyAddon",
    output_dir="./my-addon",
)

print(f"项目已生成: {project.output_dir}")
```

---

## 模板类型

### 项目模板

| 模板 | 描述 |
|------|------|
| `PROJECT_EMPTY` | 空项目，只有基础结构 |
| `PROJECT_FULL` | 完整项目，包含示例代码 |

### 实体模板

| 模板 | 描述 |
|------|------|
| `ENTITY_BASIC` | 基础实体 |
| `ENTITY_COMPLEX` | 复杂实体（带行为和组件） |
| `ENTITY_NPC` | NPC 实体 |

### 物品模板

| 模板 | 描述 |
|------|------|
| `ITEM_CONSUMABLE` | 消耗品物品 |
| `ITEM_TOOL` | 工具物品 |
| `ITEM_WEAPON` | 武器物品 |
| `ITEM_ARMOR` | 护甲物品 |

### 方块模板

| 模板 | 描述 |
|------|------|
| `BLOCK_BASIC` | 基础方块 |
| `BLOCK_INTERACTIVE` | 交互方块 |
| `BLOCK_FUNCTIONAL` | 功能方块 |

### UI 模板

| 模板 | 描述 |
|------|------|
| `UI_FORM` | UI 表单 |
| `UI_DIALOG` | 对话框 |
| `UI_HUD` | HUD 界面 |

### 网络模板

| 模板 | 描述 |
|------|------|
| `NET_SYNC` | 网络同步 |
| `NET_EVENT` | 网络事件 |

---

## 生成项目

### 空项目

```python
from mc_agent_kit.templates.project_templates import TemplateType

project = templates.generate(
    TemplateType.PROJECT_EMPTY,
    "MyAddon",
    output_dir="./my-addon",
)

# 项目结构:
# my-addon/
# ├── behavior_pack/
# │   ├── manifest.json
# │   └── scripts/
# │       └── main.py
# └── resource_pack/
#     └── manifest.json
```

### 完整项目

```python
project = templates.generate(
    TemplateType.PROJECT_FULL,
    "FullAddon",
    output_dir="./full-addon",
    variables={
        "author": "Your Name",
        "description": "My awesome addon",
        "version": "1.0.0",
    },
)
```

---

## 生成实体

### 基础实体

```python
project = templates.generate(
    TemplateType.ENTITY_BASIC,
    "CustomZombie",
    namespace="myaddon",
)

# 生成文件:
# - behavior_pack/entities/customzombie.json
# - behavior_pack/scripts/customzombie.py
# - resource_pack/entity/customzombie.geo.json
```

### 复杂实体

```python
project = templates.generate(
    TemplateType.ENTITY_COMPLEX,
    "BossMonster",
    namespace="myaddon",
    variables={
        "health": 100,
        "damage": 10,
        "speed": 1.5,
    },
)
```

### NPC 实体

```python
project = templates.generate(
    TemplateType.ENTITY_NPC,
    "VillagerNPC",
    namespace="myaddon",
    variables={
        "npc_name": "Old Man",
        "dialogue": ["Hello, traveler!", "Welcome to our village."],
    },
)
```

---

## 生成物品

### 消耗品

```python
project = templates.generate(
    TemplateType.ITEM_CONSUMABLE,
    "HealthPotion",
    namespace="myaddon",
    variables={
        "effect": "heal",
        "value": 10,
    },
)
```

### 工具

```python
project = templates.generate(
    TemplateType.ITEM_TOOL,
    "MagicPickaxe",
    namespace="myaddon",
    variables={
        "durability": 1000,
        "speed": 10,
    },
)
```

### 武器

```python
project = templates.generate(
    TemplateType.ITEM_WEAPON,
    "FireSword",
    namespace="myaddon",
    variables={
        "damage": 15,
        "enchantment": "fire_aspect",
    },
)
```

### 护甲

```python
project = templates.generate(
    TemplateType.ITEM_ARMOR,
    "DiamondHelmet",
    namespace="myaddon",
    variables={
        "armor_type": "helmet",
        "protection": 5,
        "durability": 500,
    },
)
```

---

## 生成方块

### 基础方块

```python
project = templates.generate(
    TemplateType.BLOCK_BASIC,
    "CustomStone",
    namespace="myaddon",
)
```

### 交互方块

```python
project = templates.generate(
    TemplateType.BLOCK_INTERACTIVE,
    "MagicChest",
    namespace="myaddon",
    variables={
        "slots": 27,
        "open_sound": "random.chestopen",
    },
)
```

### 功能方块

```python
project = templates.generate(
    TemplateType.BLOCK_FUNCTIONAL,
    "PowerGenerator",
    namespace="myaddon",
    variables={
        "power_output": 100,
        "fuel_consumption": 1,
    },
)
```

---

## 生成 UI

### 表单

```python
project = templates.generate(
    TemplateType.UI_FORM,
    "CustomForm",
    namespace="myaddon",
    variables={
        "title": "Settings",
        "buttons": ["Option 1", "Option 2", "Cancel"],
    },
)
```

### 对话框

```python
project = templates.generate(
    TemplateType.UI_DIALOG,
    "ConfirmDialog",
    namespace="myaddon",
    variables={
        "title": "Confirm",
        "content": "Are you sure?",
    },
)
```

### HUD

```python
project = templates.generate(
    TemplateType.UI_HUD,
    "HealthBar",
    namespace="myaddon",
    variables={
        "position": "top_left",
        "color": "#FF0000",
    },
)
```

---

## 生成网络代码

### 网络同步

```python
project = templates.generate(
    TemplateType.NET_SYNC,
    "PlayerDataSync",
    namespace="myaddon",
)
```

### 网络事件

```python
project = templates.generate(
    TemplateType.NET_EVENT,
    "CustomNetworkEvent",
    namespace="myaddon",
)
```

---

## 模板变量

### 内置变量

所有模板支持以下内置变量：

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `name` | 项目/实体/物品名称 | 必填 |
| `namespace` | 命名空间 | `myaddon` |
| `author` | 作者名 | `Unknown` |
| `version` | 版本号 | `1.0.0` |
| `description` | 描述 | `My addon` |

### 自定义变量

```python
project = templates.generate(
    TemplateType.PROJECT_FULL,
    "MyAddon",
    variables={
        "custom_var1": "value1",
        "custom_var2": "value2",
    },
)
```

### 变量渲染

模板中使用 `{{variable_name}}` 语法：

```json
{
    "name": "{{name}}",
    "version": "{{version}}",
    "author": "{{author}}"
}
```

---

## 列出模板

```python
template_list = templates.list_templates()

for template in template_list:
    print(f"类型: {template.template_type}")
    print(f"名称: {template.name}")
    print(f"描述: {template.description}")
    print(f"文件数: {len(template.files)}")
    print("---")
```

---

## 获取模板详情

```python
template = templates.get_template(TemplateType.ENTITY_BASIC)

print(f"模板名称: {template.name}")
print(f"描述: {template.description}")
print(f"支持变量: {template.variables}")
print(f"依赖: {template.dependencies}")

for file in template.files:
    print(f"文件: {file.path}")
    print(f"内容预览: {file.content[:100]}...")
```

---

## CLI 命令

### 创建项目

```bash
mc-agent create project MyAddon --template empty
mc-agent create project MyAddon --template full
```

### 创建实体

```bash
mc-agent create entity CustomZombie --namespace myaddon
```

### 创建物品

```bash
mc-agent create item HealthPotion --type consumable --namespace myaddon
```

### 创建方块

```bash
mc-agent create block MagicChest --type interactive --namespace myaddon
```

### 列出模板

```bash
mc-agent templates list
```

### 查看模板详情

```bash
mc-agent templates show entity_basic
```

---

## 最佳实践

### 1. 使用有意义的命名空间

避免命名冲突：

```python
# 不好
namespace = "test"

# 好
namespace = "my_unique_addon_name"
```

### 2. 提供完整的变量

确保所有必需变量都已提供：

```python
project = templates.generate(
    TemplateType.PROJECT_FULL,
    "MyAddon",
    variables={
        "author": "Your Name",
        "version": "1.0.0",
        "description": "A clear description",
    },
)
```

### 3. 验证生成的项目

生成后检查项目结构：

```python
for path in project.files.keys():
    print(f"生成文件: {path}")
```

### 4. 组合使用模板

可以组合多个模板创建完整项目：

```python
# 先创建基础项目
project = templates.generate(
    TemplateType.PROJECT_EMPTY,
    "MyAddon",
)

# 然后添加实体
entity_project = templates.generate(
    TemplateType.ENTITY_BASIC,
    "CustomMob",
    output_dir=project.output_dir,
)

# 再添加物品
item_project = templates.generate(
    TemplateType.ITEM_CONSUMABLE,
    "HealthPotion",
    output_dir=project.output_dir,
)
```

---

## 常见问题

### Q: 生成的文件在哪里？

默认在当前目录创建子目录，或通过 `output_dir` 参数指定：

```python
project = templates.generate(
    TemplateType.PROJECT_EMPTY,
    "MyAddon",
    output_dir="E:/addons/my-addon",
)
```

### Q: 如何自定义模板？

目前使用内置模板。自定义模板功能计划在后续版本中提供。

### Q: 生成的代码可以直接使用吗？

是的，生成的代码是有效的 ModSDK 代码，但可能需要根据具体需求调整。

---

## 参考链接

- [ModSDK 增强技能使用指南](./modsdk-enhanced.md)
- [调试器使用指南](./debugger.md)
- [代码分析器使用指南](./code-analysis.md)

---

*文档版本: v1.45.0*
*最后更新: 2026-03-24*