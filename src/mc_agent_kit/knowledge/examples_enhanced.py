"""
增强代码示例管理

管理代码示例，支持难度分级、API 关联和搜索优化。
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DifficultyLevel(Enum):
    """难度等级"""

    BEGINNER = "beginner"  # 初级 - 基础概念
    INTERMEDIATE = "intermediate"  # 中级 - 常用功能
    ADVANCED = "advanced"  # 高级 - 复杂功能
    EXPERT = "expert"  # 专家 - 特殊场景


class ExampleCategory(Enum):
    """示例类别"""

    BASIC = "basic"  # 基础示例
    ENTITY = "entity"  # 实体相关
    ITEM = "item"  # 物品相关
    BLOCK = "block"  # 方块相关
    UI = "ui"  # UI 相关
    NETWORK = "network"  # 网络相关
    PERFORMANCE = "performance"  # 性能相关
    ADVANCED = "advanced"  # 高级功能


@dataclass
class CodeExampleEnhanced:
    """增强代码示例"""

    id: str  # 示例唯一标识
    title: str  # 标题
    description: str  # 描述
    code: str  # 代码内容
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    category: ExampleCategory = ExampleCategory.BASIC
    estimated_time: int = 5  # 预计学习时间 (分钟)
    prerequisites: list[str] = field(default_factory=list)  # 前置知识
    related_apis: list[str] = field(default_factory=list)  # 相关 API
    related_events: list[str] = field(default_factory=list)  # 相关事件
    tags: list[str] = field(default_factory=list)  # 标签
    scope: str = "server"  # 作用域 (client/server/both)
    author: str | None = None
    version: str = "1.0.0"
    created_at: str | None = None
    updated_at: str | None = None
    views: int = 0
    rating: float = 0.0
    notes: list[str] = field(default_factory=list)  # 注意事项
    references: list[str] = field(default_factory=list)  # 参考链接

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "code": self.code,
            "difficulty": self.difficulty.value,
            "category": self.category.value,
            "estimated_time": self.estimated_time,
            "prerequisites": self.prerequisites,
            "related_apis": self.related_apis,
            "related_events": self.related_events,
            "tags": self.tags,
            "scope": self.scope,
            "author": self.author,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "views": self.views,
            "rating": self.rating,
            "notes": self.notes,
            "references": self.references,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CodeExampleEnhanced":
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            code=data["code"],
            difficulty=DifficultyLevel(data.get("difficulty", "beginner")),
            category=ExampleCategory(data.get("category", "basic")),
            estimated_time=data.get("estimated_time", 5),
            prerequisites=data.get("prerequisites", []),
            related_apis=data.get("related_apis", []),
            related_events=data.get("related_events", []),
            tags=data.get("tags", []),
            scope=data.get("scope", "server"),
            author=data.get("author"),
            version=data.get("version", "1.0.0"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            views=data.get("views", 0),
            rating=data.get("rating", 0.0),
            notes=data.get("notes", []),
            references=data.get("references", []),
        )


@dataclass
class SearchResult:
    """搜索结果"""

    example: CodeExampleEnhanced
    score: float
    match_type: str  # title, description, code, api, event, tag

    def to_dict(self) -> dict[str, Any]:
        return {
            "example": self.example.to_dict(),
            "score": self.score,
            "match_type": self.match_type,
        }


@dataclass
class ExampleManagerConfig:
    """示例管理器配置"""

    examples_dir: Path | None = None
    auto_load: bool = True
    max_results: int = 50


class CodeExampleManager:
    """代码示例管理器

    管理代码示例，支持搜索、过滤和推荐。

    使用示例:
        manager = CodeExampleManager()
        results = manager.search("创建实体", difficulty="beginner")
        for result in results:
            print(f"{result.example.title}: {result.score}")
    """

    # 内置示例
    BUILTIN_EXAMPLES: list[dict[str, Any]] = [
        {
            "id": "hello_world",
            "title": "Hello World - 玩家加入欢迎",
            "description": "监听玩家加入事件，发送欢迎消息",
            "code": '''# 监听玩家加入事件
import mod.server.extraServerApi as serverApi

def OnPlayerJoin(args):
    \"\"\"玩家加入事件回调\"\"\"
    player_name = args.get('playerName', '玩家')
    player_id = args.get('id')

    # 发送欢迎消息
    comp = serverApi.GetEngineCompFactory().CreateGame()
    comp.NotifyToClient(player_id, {
        'type': 'chat',
        'message': f'欢迎 {player_name} 来到服务器！'
    })

# 注册事件监听
serverApi.ListenForEvent('Minecraft', 'OnPlayerJoin', OnPlayerJoin)
''',
            "difficulty": "beginner",
            "category": "basic",
            "estimated_time": 5,
            "prerequisites": ["Python 基础", "事件概念"],
            "related_apis": ["ListenForEvent", "NotifyToClient"],
            "related_events": ["OnPlayerJoin"],
            "tags": ["事件", "玩家", "消息"],
            "scope": "server",
            "notes": ["需要在服务端脚本中使用", "消息格式需要客户端解析"],
        },
        {
            "id": "create_entity",
            "title": "创建自定义实体",
            "description": "在指定位置创建一个自定义实体",
            "code": '''# 创建实体
import mod.server.extraServerApi as serverApi

def create_custom_entity(pos, dimension_id=0):
    \"\"\"创建自定义实体

    Args:
        pos: 位置坐标 (x, y, z)
        dimension_id: 维度 ID

    Returns:
        str: 实体 ID，失败返回 None
    \"\"\"
    comp = serverApi.GetEngineCompFactory().CreateGame()

    # 创建实体
    entity_id = comp.CreateEngineEntityByType(
        'my_mod:custom_entity',  # 实体类型
        pos,
        dimension_id
    )

    if entity_id:
        print(f"[Entity] 创建成功: {entity_id}")
        return entity_id
    else:
        print("[Entity] 创建失败")
        return None

# 调用示例
# entity_id = create_custom_entity((0, 64, 0))
''',
            "difficulty": "intermediate",
            "category": "entity",
            "estimated_time": 10,
            "prerequisites": ["实体概念", "坐标系统"],
            "related_apis": ["CreateEngineEntityByType"],
            "related_events": ["OnEntityCreated"],
            "tags": ["实体", "创建"],
            "scope": "server",
            "notes": ["实体类型需要先在实体定义文件中定义"],
        },
        {
            "id": "custom_item",
            "title": "自定义物品使用",
            "description": "创建可使用的自定义物品",
            "code": '''# 自定义物品逻辑
import mod.server.extraServerApi as serverApi

ITEM_ID = "my_mod:magic_wand"

def OnItemUse(args):
    \"\"\"物品使用事件\"\"\"
    entity_id = args.get('entityId')
    item_stack = args.get('itemStack')

    # 检查是否是我们的物品
    if not item_stack or item_stack.get('newItemName') != ITEM_ID:
        return

    # 获取玩家位置
    comp = serverApi.GetEngineCompFactory().CreatePos(entity_id)
    pos = comp.GetPos()

    if pos:
        # 在玩家位置创建效果
        create_magic_effect(pos)

def create_magic_effect(pos):
    \"\"\"创建魔法效果\"\"\"
    import random

    comp = serverApi.GetEngineCompFactory().CreateGame()

    # 创建粒子效果
    for _ in range(10):
        offset = (random.uniform(-2, 2), random.uniform(0, 3), random.uniform(-2, 2))
        effect_pos = (pos[0] + offset[0], pos[1] + offset[1], pos[2] + offset[2])
        # 添加粒子效果 (示例)
        print(f"Particle at {effect_pos}")

# 注册事件
serverApi.ListenForEvent('Minecraft', 'OnItemUse', OnItemUse)
''',
            "difficulty": "intermediate",
            "category": "item",
            "estimated_time": 15,
            "prerequisites": ["物品概念", "事件处理"],
            "related_apis": ["ListenForEvent", "GetPos"],
            "related_events": ["OnItemUse"],
            "tags": ["物品", "自定义", "效果"],
            "scope": "server",
        },
        {
            "id": "block_interactive",
            "title": "交互式方块",
            "description": "创建可以交互的自定义方块",
            "code": '''# 交互式方块
import mod.server.extraServerApi as serverApi

BLOCK_ID = "my_mod:interactive_block"

class InteractiveBlock:
    \"\"\"交互式方块逻辑\"\"\"

    @staticmethod
    def on_placed(pos, dimension_id, player_id):
        \"\"\"方块放置\"\"\"
        print(f"[Block] 放置于 {pos}")
        # 初始化方块状态
        InteractiveBlock._set_block_data(pos, {"uses": 0})

    @staticmethod
    def on_interact(pos, dimension_id, player_id, item_stack):
        \"\"\"玩家交互\"\"\"
        # 获取方块数据
        data = InteractiveBlock._get_block_data(pos)
        data["uses"] = data.get("uses", 0) + 1

        print(f"[Block] 交互次数: {data['uses']}")

        # 执行交互效果
        if data["uses"] % 5 == 0:
            InteractiveBlock._give_reward(player_id)

        # 更新数据
        InteractiveBlock._set_block_data(pos, data)

        return False  # 不拦截默认行为

    @staticmethod
    def _give_reward(player_id):
        \"\"\"给予奖励\"\"\"
        comp = serverApi.GetEngineCompFactory().CreateGame()
        # 给予玩家物品
        print(f"[Block] 给予 {player_id} 奖励")

    @staticmethod
    def _set_block_data(pos, data):
        \"\"\"存储方块数据\"\"\"
        # 实现数据存储
        pass

    @staticmethod
    def _get_block_data(pos):
        \"\"\"获取方块数据\"\"\"
        return {"uses": 0}

# 注册事件
def OnBlockPlaced(args):
    if args.get('blockName') == BLOCK_ID:
        InteractiveBlock.on_placed(
            args.get('pos'),
            args.get('dimensionId', 0),
            args.get('entityId')
        )

def OnBlockInteract(args):
    if args.get('blockName') == BLOCK_ID:
        result = InteractiveBlock.on_interact(
            args.get('pos'),
            args.get('dimensionId', 0),
            args.get('entityId'),
            args.get('itemStack')
        )
        args['returnValue'] = result

serverApi.ListenForEvent('Minecraft', 'OnBlockPlaced', OnBlockPlaced)
serverApi.ListenForEvent('Minecraft', 'OnBlockInteract', OnBlockInteract)
''',
            "difficulty": "advanced",
            "category": "block",
            "estimated_time": 20,
            "prerequisites": ["方块概念", "数据存储", "事件处理"],
            "related_apis": ["ListenForEvent"],
            "related_events": ["OnBlockPlaced", "OnBlockInteract"],
            "tags": ["方块", "交互", "存储"],
            "scope": "server",
        },
        {
            "id": "client_server_sync",
            "title": "客户端-服务端数据同步",
            "description": "实现客户端和服务端之间的数据同步",
            "code": '''# 客户端-服务端数据同步
# === 服务端代码 ===
import mod.server.extraServerApi as serverApi

SYNC_EVENT = "my_mod:player_data_sync"

class PlayerDataManager:
    \"\"\"玩家数据管理器\"\"\"

    def __init__(self):
        self.player_data = {}  # playerId -> data

    def set_data(self, player_id, key, value):
        \"\"\"设置数据并同步到客户端\"\"\"
        if player_id not in self.player_data:
            self.player_data[player_id] = {}

        self.player_data[player_id][key] = value
        self._sync_to_client(player_id)

    def get_data(self, player_id, key=None):
        \"\"\"获取数据\"\"\"
        if player_id not in self.player_data:
            return None
        if key:
            return self.player_data[player_id].get(key)
        return self.player_data[player_id]

    def _sync_to_client(self, player_id):
        \"\"\"同步数据到客户端\"\"\"
        comp = serverApi.GetEngineCompFactory().CreateGame(player_id)
        comp.NotifyToClient(player_id, {
            'type': SYNC_EVENT,
            'data': self.player_data.get(player_id, {})
        })

data_manager = PlayerDataManager()

# === 客户端代码 ===
import mod.client.extraClientApi as clientApi

class ClientDataReceiver:
    \"\"\"客户端数据接收器\"\"\"

    def __init__(self):
        self.data = {}

    def on_notify(self, args):
        \"\"\"接收服务端通知\"\"\"
        if args.get('type') == SYNC_EVENT:
            self.data = args.get('data', {})
            print(f"[Client] 收到数据: {self.data}")

client_receiver = ClientDataReceiver()
clientApi.ListenForEvent('Minecraft', 'OnClientNotify', client_receiver.on_notify)
''',
            "difficulty": "advanced",
            "category": "network",
            "estimated_time": 25,
            "prerequisites": ["客户端-服务端架构", "事件系统"],
            "related_apis": ["NotifyToClient", "ListenForEvent"],
            "related_events": ["OnClientNotify"],
            "tags": ["网络", "同步", "客户端"],
            "scope": "both",
        },
        {
            "id": "performance_optimization",
            "title": "性能优化技巧",
            "description": "ModSDK 代码性能优化的常用技巧",
            "code": '''# 性能优化技巧

# 1. 缓存组件工厂
# 不推荐：
# def some_function():
#     comp = serverApi.GetEngineCompFactory().CreateGame()
#     ...

# 推荐：
COMP_FACTORY = serverApi.GetEngineCompFactory()

def some_function():
    comp = COMP_FACTORY.CreateGame()
    ...

# 2. 批量操作
# 不推荐：逐个处理
# for entity_id in entities:
#     comp = COMP_FACTORY.CreatePos(entity_id)
#     pos = comp.GetPos()

# 推荐：批量获取
positions = {}
for entity_id in entities:
    comp = COMP_FACTORY.CreatePos(entity_id)
    positions[entity_id] = comp.GetPos()

# 3. 事件监听优化
# 使用 tick 计数避免每帧执行
tick_count = 0
CHECK_INTERVAL = 20  # 每秒检查一次 (20 ticks)

def on_tick(args):
    global tick_count
    tick_count += 1

    if tick_count % CHECK_INTERVAL == 0:
        # 执行检查逻辑
        check_something()

serverApi.ListenForEvent('Minecraft', 'OnServerTick', on_tick)

# 4. 减少不必要的计算
# 缓存计算结果
cached_result = None
cache_time = 0

def get_expensive_result():
    global cached_result, cache_time
    import time
    current_time = time.time()

    if cached_result and (current_time - cache_time) < 60:
        return cached_result

    # 执行昂贵计算
    cached_result = expensive_calculation()
    cache_time = current_time
    return cached_result
''',
            "difficulty": "advanced",
            "category": "performance",
            "estimated_time": 15,
            "prerequisites": ["Python 基础", "性能概念"],
            "related_apis": ["GetEngineCompFactory", "ListenForEvent"],
            "related_events": ["OnServerTick"],
            "tags": ["性能", "优化", "缓存"],
            "scope": "server",
        },
    ]

    def __init__(self, config: ExampleManagerConfig | None = None):
        """初始化示例管理器

        Args:
            config: 配置
        """
        self.config = config or ExampleManagerConfig()
        self._examples: dict[str, CodeExampleEnhanced] = {}
        self._api_index: dict[str, list[str]] = {}  # api_name -> example_ids
        self._event_index: dict[str, list[str]] = {}  # event_name -> example_ids
        self._tag_index: dict[str, list[str]] = {}  # tag -> example_ids

        if self.config.auto_load:
            self._load_builtin_examples()

    def _load_builtin_examples(self) -> None:
        """加载内置示例"""
        for data in self.BUILTIN_EXAMPLES:
            example = CodeExampleEnhanced.from_dict(data)
            self._add_example(example)

    def _add_example(self, example: CodeExampleEnhanced) -> None:
        """添加示例并更新索引"""
        self._examples[example.id] = example

        # 更新 API 索引
        for api in example.related_apis:
            if api not in self._api_index:
                self._api_index[api] = []
            self._api_index[api].append(example.id)

        # 更新事件索引
        for event in example.related_events:
            if event not in self._event_index:
                self._event_index[event] = []
            self._event_index[event].append(example.id)

        # 更新标签索引
        for tag in example.tags:
            tag_lower = tag.lower()
            if tag_lower not in self._tag_index:
                self._tag_index[tag_lower] = []
            self._tag_index[tag_lower].append(example.id)

    def search(
        self,
        query: str,
        difficulty: DifficultyLevel | str | None = None,
        category: ExampleCategory | str | None = None,
        scope: str | None = None,
        api: str | None = None,
        event: str | None = None,
        tags: list[str] | None = None,
        max_results: int | None = None,
    ) -> list[SearchResult]:
        """搜索示例

        Args:
            query: 搜索关键词
            difficulty: 难度过滤
            category: 类别过滤
            scope: 作用域过滤
            api: 相关 API 过滤
            event: 相关事件过滤
            tags: 标签过滤
            max_results: 最大结果数

        Returns:
            搜索结果列表
        """
        max_results = max_results or self.config.max_results
        query_lower = query.lower() if query else ""

        results: list[SearchResult] = []

        for example in self._examples.values():
            # 应用过滤器
            if difficulty:
                diff_val = difficulty.value if isinstance(difficulty, DifficultyLevel) else difficulty
                if example.difficulty.value != diff_val:
                    continue

            if category:
                cat_val = category.value if isinstance(category, ExampleCategory) else category
                if example.category.value != cat_val:
                    continue

            if scope and example.scope != scope and example.scope != "both":
                continue

            if api and api not in example.related_apis:
                continue

            if event and event not in example.related_events:
                continue

            if tags and not any(tag in example.tags for tag in tags):
                continue

            # 计算匹配分数
            score = 0.0
            match_type = ""

            if query_lower:
                # 标题匹配 (最高权重)
                if query_lower in example.title.lower():
                    score = 1.0
                    match_type = "title"

                # 描述匹配
                elif query_lower in example.description.lower():
                    score = 0.8
                    match_type = "description"

                # 代码匹配
                elif query_lower in example.code.lower():
                    score = 0.6
                    match_type = "code"

                # 标签匹配
                elif any(query_lower in tag.lower() for tag in example.tags):
                    score = 0.5
                    match_type = "tag"

                # API 匹配
                elif any(query_lower in api.lower() for api in example.related_apis):
                    score = 0.7
                    match_type = "api"

                # 事件匹配
                elif any(query_lower in evt.lower() for evt in example.related_events):
                    score = 0.7
                    match_type = "event"

                else:
                    continue
            else:
                score = 1.0
                match_type = "filter"

            results.append(SearchResult(example=example, score=score, match_type=match_type))

        # 按分数排序
        results.sort(key=lambda r: (-r.score, r.example.title))

        return results[:max_results]

    def get_by_api(self, api_name: str) -> list[CodeExampleEnhanced]:
        """获取使用指定 API 的示例"""
        example_ids = self._api_index.get(api_name, [])
        return [self._examples[eid] for eid in example_ids if eid in self._examples]

    def get_by_event(self, event_name: str) -> list[CodeExampleEnhanced]:
        """获取使用指定事件的示例"""
        example_ids = self._event_index.get(event_name, [])
        return [self._examples[eid] for eid in example_ids if eid in self._examples]

    def get_by_tag(self, tag: str) -> list[CodeExampleEnhanced]:
        """获取指定标签的示例"""
        example_ids = self._tag_index.get(tag.lower(), [])
        return [self._examples[eid] for eid in example_ids if eid in self._examples]

    def get_example(self, example_id: str) -> CodeExampleEnhanced | None:
        """获取示例"""
        return self._examples.get(example_id)

    def list_all(self) -> list[CodeExampleEnhanced]:
        """列出所有示例"""
        return list(self._examples.values())

    def list_by_difficulty(self, difficulty: DifficultyLevel) -> list[CodeExampleEnhanced]:
        """按难度列出示例"""
        return [e for e in self._examples.values() if e.difficulty == difficulty]

    def list_by_category(self, category: ExampleCategory) -> list[CodeExampleEnhanced]:
        """按类别列出示例"""
        return [e for e in self._examples.values() if e.category == category]

    def get_difficulty_distribution(self) -> dict[str, int]:
        """获取难度分布"""
        distribution = {d.value: 0 for d in DifficultyLevel}
        for example in self._examples.values():
            distribution[example.difficulty.value] += 1
        return distribution

    def get_category_distribution(self) -> dict[str, int]:
        """获取类别分布"""
        distribution = {c.value: 0 for c in ExampleCategory}
        for example in self._examples.values():
            distribution[example.category.value] += 1
        return distribution


def create_example_manager(config: ExampleManagerConfig | None = None) -> CodeExampleManager:
    """创建示例管理器的便捷函数"""
    return CodeExampleManager(config)
