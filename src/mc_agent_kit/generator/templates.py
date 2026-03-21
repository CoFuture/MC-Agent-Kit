"""
代码模板系统

定义代码模板的数据结构和模板管理器。
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class TemplateType(Enum):
    """模板类型"""

    EVENT_LISTENER = "event_listener"  # 事件监听器
    API_CALL = "api_call"  # API 调用
    ENTITY = "entity"  # 实体相关
    ITEM = "item"  # 物品相关
    BLOCK = "block"  # 方块相关
    UI = "ui"  # UI 相关
    CUSTOM = "custom"  # 自定义模板


@dataclass
class TemplateParameter:
    """模板参数定义"""

    name: str  # 参数名
    description: str  # 参数描述
    param_type: str = "str"  # 参数类型 (str, int, bool, list, dict)
    required: bool = True  # 是否必需
    default: Any = None  # 默认值
    choices: list[str] | None = None  # 可选值列表


@dataclass
class CodeTemplate:
    """代码模板"""

    name: str  # 模板名称（唯一标识）
    template_type: TemplateType  # 模板类型
    description: str  # 模板描述
    template: str  # Jinja2 模板内容
    parameters: list[TemplateParameter] = field(default_factory=list)  # 参数定义
    tags: list[str] = field(default_factory=list)  # 标签
    examples: list[str] = field(default_factory=list)  # 使用示例
    scope: str = "both"  # 作用域 (client, server, both)

    def get_parameter(self, name: str) -> TemplateParameter | None:
        """获取指定参数"""
        for param in self.parameters:
            if param.name == name:
                return param
        return None

    def validate_params(self, params: dict[str, Any]) -> tuple[bool, list[str]]:
        """验证参数

        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []

        # 检查必需参数
        for param in self.parameters:
            if param.required and param.name not in params:
                if param.default is None:
                    errors.append(f"缺少必需参数: {param.name}")
                continue

            # 检查参数值是否在可选范围内
            if param.name in params and param.choices:
                if params[param.name] not in param.choices:
                    errors.append(
                        f"参数 {param.name} 的值必须是: {', '.join(param.choices)}"
                    )

        return len(errors) == 0, errors


# 内置模板定义
BUILTIN_TEMPLATES: list[CodeTemplate] = [
    # 事件监听器模板
    CodeTemplate(
        name="event_listener",
        template_type=TemplateType.EVENT_LISTENER,
        description="生成事件监听器代码",
        template="""# {{ event_name }} 事件监听器
# {{ description | default('事件监听器') }}
# 作用域: {{ scope | default('服务端') }}

import mod.client.extraClientApi as clientApi
import mod.server.extraServerApi as serverApi

# 获取引擎类型
EngineType = clientApi.GetEngineVersion()[0]

# 获取 {{ scope | default('服务端') }} 系统名称
{% if scope == '客户端' %}
SystemName = clientApi.GetSystemName()
{% else %}
SystemName = serverApi.GetSystemName()
{% endif %}

def On{{ event_name }}(args):
    \"\"\"
    {{ event_name }} 事件回调
    
    参数:
    {% for param in event_params %}
    - {{ param.name }} ({{ param.type }}): {{ param.desc }}
    {% endfor %}
    \"\"\"
    # TODO: 实现事件处理逻辑
    {{ event_name | snake_case }}_id = args.get('{{ id_field | default('id') }}')
    print("[{{ event_name }}] 触发事件, id:", {{ event_name | snake_case }}_id)
    
    # 返回值控制事件传播
    # return True  # 继续传播
    # return False  # 取消传播

# 注册事件监听
{% if scope == '客户端' %}
clientApi.ListenForEvent('{{ event_namespace | default('Minecraft') }}', '{{ event_name }}', On{{ event_name }})
{% else %}
serverApi.ListenForEvent('{{ event_namespace | default('Minecraft') }}', '{{ event_name }}', On{{ event_name }})
{% endif %}
""",
        parameters=[
            TemplateParameter(
                name="event_name",
                description="事件名称",
                param_type="str",
                required=True,
            ),
            TemplateParameter(
                name="scope",
                description="作用域（客户端/服务端）",
                param_type="str",
                required=False,
                default="服务端",
                choices=["客户端", "服务端"],
            ),
            TemplateParameter(
                name="event_params",
                description="事件参数列表",
                param_type="list",
                required=False,
                default=[],
            ),
            TemplateParameter(
                name="description",
                description="事件描述",
                param_type="str",
                required=False,
            ),
            TemplateParameter(
                name="event_namespace",
                description="事件命名空间",
                param_type="str",
                required=False,
                default="Minecraft",
            ),
        ],
        tags=["event", "listener"],
        examples=[
            "event_listener(event_name='OnServerChat')",
            "event_listener(event_name='OnPlayerDeath', scope='服务端')",
        ],
        scope="both",
    ),
    # API 调用模板
    CodeTemplate(
        name="api_call",
        template_type=TemplateType.API_CALL,
        description="生成 API 调用代码",
        template="""# {{ api_name }} API 调用
# {{ description | default('API 调用示例') }}
# 模块: {{ module | default('通用') }}
# 作用域: {{ scope | default('服务端') }}

import mod.client.extraClientApi as clientApi
import mod.server.extraServerApi as serverApi

# 获取组件
{% if scope == '客户端' %}
comp = clientApi.GetEngineCompFactory().{{ component_factory | default('CreateComp') }}()
{% else %}
comp = serverApi.GetEngineCompFactory().{{ component_factory | default('CreateComp') }}()
{% endif %}

def call_{{ api_name | snake_case }}({% for param in api_params %}{{ param.name }}{% if not param.required %}={{ param.default }}{% endif %}, {% endfor %}):
    \"\"\"
    调用 {{ api_name }} API
    
    {% for param in api_params %}
    Args:
        {{ param.name }} ({{ param.type }}): {{ param.desc }}
    {% endfor %}
    
    Returns:
        {{ return_type | default('None') }}: {{ return_desc | default('返回值') }}
    \"\"\"
    {% if scope == '客户端' %}
    result = comp.{{ api_name }}({% for param in api_params %}{{ param.name }}, {% endfor %})
    {% else %}
    result = comp.{{ api_name }}({% for param in api_params %}{{ param.name }}, {% endfor %})
    {% endif %}
    return result

# 调用示例
# result = call_{{ api_name | snake_case }}({% for param in api_params[:2] %}{{ param.default or '...' }}, {% endfor %})
# print("{{ api_name }} result:", result)
""",
        parameters=[
            TemplateParameter(
                name="api_name",
                description="API 名称",
                param_type="str",
                required=True,
            ),
            TemplateParameter(
                name="scope",
                description="作用域",
                param_type="str",
                required=False,
                default="服务端",
                choices=["客户端", "服务端"],
            ),
            TemplateParameter(
                name="component_factory",
                description="组件工厂方法名",
                param_type="str",
                required=False,
            ),
            TemplateParameter(
                name="api_params",
                description="API 参数列表",
                param_type="list",
                required=False,
                default=[],
            ),
            TemplateParameter(
                name="return_type",
                description="返回类型",
                param_type="str",
                required=False,
            ),
        ],
        tags=["api", "call"],
        examples=[
            "api_call(api_name='GetEngineType', scope='服务端')",
        ],
        scope="both",
    ),
    # 实体创建模板
    CodeTemplate(
        name="entity_create",
        template_type=TemplateType.ENTITY,
        description="生成创建实体代码",
        template="""# 创建实体
# 实体类型: {{ entity_type | default('minecraft:pig') }}
# 作用域: {{ scope | default('服务端') }}

import mod.server.extraServerApi as serverApi

def create_entity(pos, dimensionId=0):
    \"\"\"
    创建实体
    
    Args:
        pos (tuple): 坐标 (x, y, z)
        dimensionId (int): 维度 ID
        
    Returns:
        str: 实体 ID
    \"\"\"
    comp = serverApi.GetEngineCompFactory().CreateGame()
    
    # 创建实体
    entity_id = comp.CreateEngineEntityByType(
        '{{ entity_type | default('minecraft:pig') }}',
        pos,
        dimensionId
    )
    
    if entity_id:
        print(f"[Entity] 创建成功: {entity_id}")
        return entity_id
    else:
        print("[Entity] 创建失败")
        return None

# 调用示例
# entity_id = create_entity((0, 64, 0))
""",
        parameters=[
            TemplateParameter(
                name="entity_type",
                description="实体类型标识符",
                param_type="str",
                required=False,
                default="minecraft:pig",
            ),
            TemplateParameter(
                name="scope",
                description="作用域",
                param_type="str",
                required=False,
                default="服务端",
            ),
        ],
        tags=["entity", "create"],
        examples=[
            "entity_create(entity_type='minecraft:zombie')",
        ],
        scope="server",
    ),
    # 物品注册模板
    CodeTemplate(
        name="item_register",
        template_type=TemplateType.ITEM,
        description="生成注册自定义物品代码",
        template="""# 注册自定义物品
# 物品名称: {{ item_name | default('custom_item') }}
# 物品标识符: {{ item_identifier | default('my_mod:custom_item') }}

import mod.server.extraServerApi as serverApi

# 物品配置
ITEM_CONFIG = {
    'itemName': '{{ item_name | default('custom_item') }}',
    'itemIdentifier': '{{ item_identifier | default('my_mod:custom_item') }}',
    'itemCategory': '{{ item_category | default('Equipment') }}',
    'maxStackSize': {{ max_stack | default(64) }},
}

def register_custom_item():
    \"\"\"
    注册自定义物品
    
    Returns:
        bool: 是否注册成功
    \"\"\"
    comp = serverApi.GetEngineCompFactory().CreateItem()
    
    # TODO: 调用物品注册 API
    # result = comp.RegisterItem(ITEM_CONFIG)
    # return result
    
    print(f"[Item] 注册物品: {ITEM_CONFIG['itemName']}")
    return True

# 服务端初始化时注册
# register_custom_item()
""",
        parameters=[
            TemplateParameter(
                name="item_name",
                description="物品名称",
                param_type="str",
                required=True,
            ),
            TemplateParameter(
                name="item_identifier",
                description="物品标识符 (namespace:item_name)",
                param_type="str",
                required=True,
            ),
            TemplateParameter(
                name="item_category",
                description="物品分类",
                param_type="str",
                required=False,
                default="Equipment",
            ),
            TemplateParameter(
                name="max_stack",
                description="最大堆叠数量",
                param_type="int",
                required=False,
                default=64,
            ),
        ],
        tags=["item", "register"],
        examples=[
            "item_register(item_name='magic_sword', item_identifier='my_mod:magic_sword')",
        ],
        scope="server",
    ),
    # UI 创建模板
    CodeTemplate(
        name="ui_screen",
        template_type=TemplateType.UI,
        description="生成 UI 屏幕代码",
        template="""# UI 屏幕
# UI 名称: {{ ui_name | default('MyUI') }}
# 作用域: 客户端

import mod.client.extraClientApi as clientApi

class {{ ui_name }}Screen:
    \"\"\"
    {{ ui_name }} UI 屏幕
    {{ description | default('自定义 UI 屏幕') }}
    \"\"\"
    
    def __init__(self):
        self.screenNode = None
        self.uiNode = None
        
    def Create(self):
        \"\"\"创建 UI\"\"\"
        # 获取 UI 组件
        comp = clientApi.GetEngineCompFactory().CreateUI()
        
        # 创建屏幕节点
        # TODO: 实现 UI 创建逻辑
        pass
    
    def Destroy(self):
        \"\"\"销毁 UI\"\"\"
        if self.screenNode:
            # TODO: 实现 UI 销毁逻辑
            pass
    
    def OnButtonClick(self, buttonName):
        \"\"\"
        按钮点击回调
        
        Args:
            buttonName (str): 按钮名称
        \"\"\"
        print(f"[UI] Button clicked: {buttonName}")
        
        {% for button in buttons %}
        if buttonName == '{{ button }}':
            print(f"[UI] {{ button }} 按钮被点击")
            # TODO: 处理 {{ button }} 按钮点击
        {% endfor %}

# 创建 UI 实例
# ui_screen = {{ ui_name }}Screen()
# ui_screen.Create()
""",
        parameters=[
            TemplateParameter(
                name="ui_name",
                description="UI 名称",
                param_type="str",
                required=True,
            ),
            TemplateParameter(
                name="description",
                description="UI 描述",
                param_type="str",
                required=False,
            ),
            TemplateParameter(
                name="buttons",
                description="按钮名称列表",
                param_type="list",
                required=False,
                default=[],
            ),
        ],
        tags=["ui", "screen"],
        examples=[
            "ui_screen(ui_name='InventoryUI', buttons=['open', 'close', 'sort'])",
        ],
        scope="client",
    ),
]


class TemplateManager:
    """模板管理器

    管理代码模板的注册、查询和渲染。
    """

    def __init__(self):
        """初始化模板管理器"""
        self._templates: dict[str, CodeTemplate] = {}
        self._templates_by_type: dict[TemplateType, list[str]] = {
            t: [] for t in TemplateType
        }

        # 注册内置模板
        for template in BUILTIN_TEMPLATES:
            self.register(template)

    def register(self, template: CodeTemplate) -> None:
        """注册模板

        Args:
            template: 要注册的模板
        """
        self._templates[template.name] = template
        self._templates_by_type[template.template_type].append(template.name)

    def unregister(self, name: str) -> bool:
        """注销模板

        Args:
            name: 模板名称

        Returns:
            是否成功注销
        """
        if name not in self._templates:
            return False

        template = self._templates[name]
        del self._templates[name]
        self._templates_by_type[template.template_type].remove(name)
        return True

    def get(self, name: str) -> CodeTemplate | None:
        """获取模板

        Args:
            name: 模板名称

        Returns:
            模板对象，不存在则返回 None
        """
        return self._templates.get(name)

    def list_all(self) -> list[CodeTemplate]:
        """列出所有模板"""
        return list(self._templates.values())

    def list_by_type(self, template_type: TemplateType) -> list[CodeTemplate]:
        """按类型列出模板"""
        names = self._templates_by_type.get(template_type, [])
        return [self._templates[name] for name in names if name in self._templates]

    def search(self, keyword: str) -> list[CodeTemplate]:
        """搜索模板

        搜索范围：名称、描述、标签

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的模板列表
        """
        keyword_lower = keyword.lower()
        results = []

        for template in self._templates.values():
            # 名称匹配
            if keyword_lower in template.name.lower():
                results.append(template)
                continue
            # 描述匹配
            if keyword_lower in template.description.lower():
                results.append(template)
                continue
            # 标签匹配
            for tag in template.tags:
                if keyword_lower in tag.lower():
                    results.append(template)
                    break

        return results

    def load_from_directory(self, directory: str | Path) -> int:
        """从目录加载模板

        Args:
            directory: 模板目录路径

        Returns:
            加载的模板数量
        """
        # TODO: 实现从文件系统加载模板
        return 0
