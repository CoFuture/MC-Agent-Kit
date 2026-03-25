"""
示例代码库模块

提供示例代码的管理、分类和检索功能。
迭代 #71: 知识库增强与检索优化
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .unified_index import (
    CodeBlock,
    DifficultyLevel,
    EntryScope,
    ExampleCategory,
    UnifiedEntry,
)


@dataclass
class ExampleMetadata:
    """示例元数据"""
    name: str
    title: str
    description: str
    category: ExampleCategory
    difficulty: DifficultyLevel
    tags: list[str] = field(default_factory=list)
    author: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    version: str = "1.0.0"
    
    # 关联信息
    apis_used: list[str] = field(default_factory=list)
    events_used: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    
    # 质量指标
    rating: float = 0.0
    downloads: int = 0
    verified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "difficulty": self.difficulty.value,
            "tags": self.tags,
            "author": self.author,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version,
            "apis_used": self.apis_used,
            "events_used": self.events_used,
            "prerequisites": self.prerequisites,
            "rating": self.rating,
            "downloads": self.downloads,
            "verified": self.verified,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExampleMetadata":
        return cls(
            name=data.get("name", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            category=ExampleCategory(data.get("category", "basic")),
            difficulty=DifficultyLevel(data.get("difficulty", "beginner")),
            tags=data.get("tags", []),
            author=data.get("author"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            version=data.get("version", "1.0.0"),
            apis_used=data.get("apis_used", []),
            events_used=data.get("events_used", []),
            prerequisites=data.get("prerequisites", []),
            rating=data.get("rating", 0.0),
            downloads=data.get("downloads", 0),
            verified=data.get("verified", False),
        )


@dataclass
class ExampleCode:
    """示例代码"""
    metadata: ExampleMetadata
    code_blocks: list[CodeBlock] = field(default_factory=list)
    explanation: str = ""
    warnings: list[str] = field(default_factory=list)
    tips: list[str] = field(default_factory=list)
    scope: EntryScope = EntryScope.BOTH
    
    @property
    def name(self) -> str:
        return self.metadata.name

    def get_main_code(self) -> str:
        """获取主要代码块"""
        if self.code_blocks:
            return self.code_blocks[0].code
        return ""

    def get_all_code(self) -> str:
        """获取所有代码（合并）"""
        return "\n\n".join(block.code for block in self.code_blocks)

    def to_unified_entry(self) -> UnifiedEntry:
        """转换为统一索引条目"""
        return UnifiedEntry.create_example(
            name=self.metadata.name,
            description=self.metadata.description,
            category=self.metadata.category,
            difficulty=self.metadata.difficulty,
            content=self.get_all_code(),
            code_blocks=self.code_blocks,
            tags=self.metadata.tags,
            keywords=self.metadata.tags + [self.metadata.name],
            related_apis=[
                {"name": api, "relationship": "used_by"}
                for api in self.metadata.apis_used
            ],
            related_events=self.metadata.events_used,
            prerequisites=self.metadata.prerequisites,
            scope=self.scope,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "code_blocks": [b.to_dict() for b in self.code_blocks],
            "explanation": self.explanation,
            "warnings": self.warnings,
            "tips": self.tips,
            "scope": self.scope.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExampleCode":
        return cls(
            metadata=ExampleMetadata.from_dict(data.get("metadata", {})),
            code_blocks=[CodeBlock.from_dict(b) for b in data.get("code_blocks", [])],
            explanation=data.get("explanation", ""),
            warnings=data.get("warnings", []),
            tips=data.get("tips", []),
            scope=EntryScope(data.get("scope", "both")),
        )


class ExampleLibrary:
    """
    示例代码库
    
    管理内置示例和用户自定义示例。
    """

    def __init__(self, library_path: str | None = None):
        """
        初始化示例库
        
        Args:
            library_path: 示例库存储路径
        """
        self.library_path = Path(library_path) if library_path else None
        self._examples: dict[str, ExampleCode] = {}
        self._by_category: dict[ExampleCategory, list[str]] = {}
        self._by_api: dict[str, list[str]] = {}
        self._by_event: dict[str, list[str]] = {}
        self._loaded = False

        # 初始化分类索引
        for cat in ExampleCategory:
            self._by_category[cat] = []

    def load(self) -> None:
        """加载示例库"""
        if self._loaded:
            return

        # 加载内置示例
        self._load_builtin_examples()

        # 加载用户示例
        if self.library_path and self.library_path.exists():
            self._load_from_directory(self.library_path)

        self._loaded = True

    def add_example(self, example: ExampleCode) -> None:
        """添加示例"""
        self._examples[example.name] = example
        
        # 更新分类索引
        cat = example.metadata.category
        if cat not in self._by_category:
            self._by_category[cat] = []
        if example.name not in self._by_category[cat]:
            self._by_category[cat].append(example.name)

        # 更新 API 索引
        for api in example.metadata.apis_used:
            if api not in self._by_api:
                self._by_api[api] = []
            if example.name not in self._by_api[api]:
                self._by_api[api].append(example.name)

        # 更新事件索引
        for event in example.metadata.events_used:
            if event not in self._by_event:
                self._by_event[event] = []
            if example.name not in self._by_event[event]:
                self._by_event[event].append(example.name)

    def get_example(self, name: str) -> ExampleCode | None:
        """获取示例"""
        if not self._loaded:
            self.load()
        return self._examples.get(name)

    def list_examples(
        self,
        category: ExampleCategory | None = None,
        difficulty: DifficultyLevel | None = None,
        limit: int = 20,
    ) -> list[ExampleCode]:
        """列出示例"""
        if not self._loaded:
            self.load()

        examples = list(self._examples.values())

        # 过滤分类
        if category:
            examples = [e for e in examples if e.metadata.category == category]

        # 过滤难度
        if difficulty:
            examples = [e for e in examples if e.metadata.difficulty == difficulty]

        # 排序（按评分和下载量）
        examples.sort(key=lambda e: (e.metadata.rating, e.metadata.downloads), reverse=True)

        return examples[:limit]

    def search(
        self,
        query: str,
        category: ExampleCategory | None = None,
        api: str | None = None,
        event: str | None = None,
        limit: int = 10,
    ) -> list[ExampleCode]:
        """搜索示例"""
        if not self._loaded:
            self.load()

        results: list[ExampleCode] = []
        query_lower = query.lower()

        # 按 API 搜索
        if api and api in self._by_api:
            for name in self._by_api[api]:
                if name in self._examples:
                    results.append(self._examples[name])

        # 按事件搜索
        if event and event in self._by_event:
            for name in self._by_event[event]:
                if name in self._examples and self._examples[name] not in results:
                    results.append(self._examples[name])

        # 按关键词搜索
        if query:
            for example in self._examples.values():
                if example in results:
                    continue
                
                # 检查名称、标题、描述、标签
                if query_lower in example.name.lower():
                    results.append(example)
                elif query_lower in example.metadata.title.lower():
                    results.append(example)
                elif query_lower in example.metadata.description.lower():
                    results.append(example)
                elif any(query_lower in tag.lower() for tag in example.metadata.tags):
                    results.append(example)

        # 过滤分类
        if category:
            results = [e for e in results if e.metadata.category == category]

        # 去重并限制数量
        seen = set()
        unique_results = []
        for example in results:
            if example.name not in seen:
                seen.add(example.name)
                unique_results.append(example)
                if len(unique_results) >= limit:
                    break

        return unique_results

    def get_examples_by_api(self, api_name: str) -> list[ExampleCode]:
        """获取使用指定 API 的示例"""
        if not self._loaded:
            self.load()

        examples = []
        for name in self._by_api.get(api_name, []):
            if name in self._examples:
                examples.append(self._examples[name])
        return examples

    def get_examples_by_event(self, event_name: str) -> list[ExampleCode]:
        """获取使用指定事件的示例"""
        if not self._loaded:
            self.load()

        examples = []
        for name in self._by_event.get(event_name, []):
            if name in self._examples:
                examples.append(self._examples[name])
        return examples

    def get_categories(self) -> list[ExampleCategory]:
        """获取所有分类"""
        return [cat for cat, names in self._by_category.items() if names]

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        if not self._loaded:
            self.load()

        by_category = {
            cat.value: len(names)
            for cat, names in self._by_category.items()
            if names
        }

        by_difficulty: dict[str, int] = {}
        for example in self._examples.values():
            diff = example.metadata.difficulty.value
            by_difficulty[diff] = by_difficulty.get(diff, 0) + 1

        return {
            "total_examples": len(self._examples),
            "by_category": by_category,
            "by_difficulty": by_difficulty,
            "total_apis_indexed": len(self._by_api),
            "total_events_indexed": len(self._by_event),
        }

    def _load_builtin_examples(self) -> None:
        """加载内置示例"""
        builtin_examples = self._create_builtin_examples()
        for example in builtin_examples:
            self.add_example(example)

    def _create_builtin_examples(self) -> list[ExampleCode]:
        """创建内置示例"""
        examples = []

        # 示例 1: Hello World
        examples.append(ExampleCode(
            metadata=ExampleMetadata(
                name="hello_world",
                title="Hello World",
                description="最简单的 ModSDK 脚本，在服务端启动时打印消息",
                category=ExampleCategory.BASIC,
                difficulty=DifficultyLevel.BEGINNER,
                tags=["basic", "server", "hello-world"],
                apis_used=[],
                events_used=["OnServerStarted"],
                prerequisites=[],
                verified=True,
            ),
            code_blocks=[
                CodeBlock(
                    language="python",
                    code='''# 服务端入口
import mod.server.extraServerApi as serverApi

# 获取服务端引擎
ServerSystem = serverApi.GetServerSystem()

def OnServerStarted(args):
    """服务端启动事件"""
    print("Hello, Minecraft!")

# 注册事件监听
ServerSystem.ListenForEvent("OnServerStarted", OnServerStarted)
''',
                    description="服务端代码",
                ),
            ],
            explanation="这是最简单的 ModSDK 脚本。它在服务端启动时注册一个事件监听器，当服务端启动完成时打印一条消息。",
            tips=[
                "所有服务端代码都需要在服务端入口文件中编写",
                "使用 ListenForEvent 注册事件监听",
                "print 输出会显示在游戏日志中",
            ],
            scope=EntryScope.SERVER,
        ))

        # 示例 2: 创建自定义实体
        examples.append(ExampleCode(
            metadata=ExampleMetadata(
                name="create_custom_entity",
                title="创建自定义实体",
                description="创建一个简单的自定义实体，包含基本的行为",
                category=ExampleCategory.ENTITY,
                difficulty=DifficultyLevel.INTERMEDIATE,
                tags=["entity", "custom", "behavior"],
                apis_used=["CreateEngineEntity", "DestroyEntity"],
                events_used=["OnServerStarted", "OnEntityCreated"],
                prerequisites=["了解实体概念"],
                verified=True,
            ),
            code_blocks=[
                CodeBlock(
                    language="python",
                    code='''# 创建自定义实体示例
import mod.server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystem()
engineType = serverApi.GetEngineType()

def CreateCustomEntity(pos):
    """创建自定义实体"""
    # 定义实体配置
    entityConfig = {
        "identifier": "my_mod:custom_mob",
        "type": engineType.Mob,
        "pos": pos,
    }
    
    # 创建实体
    entityId = ServerSystem.CreateEngineEntity(entityConfig)
    
    if entityId:
        print(f"实体创建成功: {entityId}")
        return entityId
    else:
        print("实体创建失败")
        return None

def OnServerStarted(args):
    """服务端启动时创建实体"""
    # 在 (0, 64, 0) 位置创建实体
    CreateCustomEntity((0, 64, 0))

ServerSystem.ListenForEvent("OnServerStarted", OnServerStarted)
''',
                    description="服务端实体创建代码",
                ),
            ],
            explanation="这个示例展示了如何创建一个自定义实体。首先定义实体配置，然后调用 CreateEngineEntity 创建实体。",
            warnings=[
                "实体标识符需要与实体定义文件匹配",
                "实体位置需要在有效的区块内",
            ],
            tips=[
                "使用 identifier 指定实体类型",
                "可以通过事件监听 OnEntityCreated 获取实体创建回调",
                "使用 DestroyEntity 可以销毁实体",
            ],
            scope=EntryScope.SERVER,
        ))

        # 示例 3: 聊天事件监听
        examples.append(ExampleCode(
            metadata=ExampleMetadata(
                name="chat_listener",
                title="聊天事件监听",
                description="监听玩家聊天消息并处理自定义命令",
                category=ExampleCategory.BASIC,
                difficulty=DifficultyLevel.BEGINNER,
                tags=["chat", "command", "event"],
                apis_used=[],
                events_used=["OnServerChat"],
                prerequisites=[],
                verified=True,
            ),
            code_blocks=[
                CodeBlock(
                    language="python",
                    code='''# 聊天事件监听示例
import mod.server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystem()

def OnServerChat(args):
    """聊天事件处理"""
    message = args.get("message", "")
    player = args.get("player", "")
    
    # 检查是否为命令
    if message.startswith("!"):
        HandleCommand(message[1:], player)
    else:
        print(f"[聊天] {player}: {message}")

def HandleCommand(cmd, player):
    """处理自定义命令"""
    parts = cmd.split()
    command = parts[0].lower()
    
    if command == "help":
        print("可用命令: !help, !info, !pos")
    elif command == "info":
        print(f"玩家: {player}")
    elif command == "pos":
        # 获取玩家位置需要额外 API
        print("获取位置功能需要实现")
    else:
        print(f"未知命令: {command}")

ServerSystem.ListenForEvent("OnServerChat", OnServerChat)
''',
                    description="聊天事件处理代码",
                ),
            ],
            explanation="监听服务端聊天事件，当玩家发送消息时触发。可以用于实现自定义命令系统。",
            tips=[
                "消息以 ! 开头的视为命令",
                "args 包含消息内容和发送者信息",
                "可以实现类似游戏内命令系统",
            ],
            scope=EntryScope.SERVER,
        ))

        # 示例 4: 网络同步
        examples.append(ExampleCode(
            metadata=ExampleMetadata(
                name="network_sync",
                title="客户端-服务端数据同步",
                description="展示客户端和服务端之间的数据同步",
                category=ExampleCategory.NETWORK,
                difficulty=DifficultyLevel.ADVANCED,
                tags=["network", "sync", "client-server"],
                apis_used=["NotifyToClient", "NotifyToServer"],
                events_used=["OnServerStarted", "OnClientStarted", "OnCustomEvent"],
                prerequisites=["了解客户端-服务端架构"],
                verified=True,
            ),
            code_blocks=[
                CodeBlock(
                    language="python",
                    code='''# 服务端代码 - network_sync_server.py
import mod.server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystem()

# 存储玩家数据
playerData = {}

def OnServerStarted(args):
    """服务端启动"""
    print("服务端网络同步示例已启动")

def OnPlayerJoin(args):
    """玩家加入"""
    playerId = args.get("playerId")
    playerData[playerId] = {
        "coins": 0,
        "level": 1,
    }
    # 同步数据到客户端
    ServerSystem.NotifyToClient(playerId, "PlayerDataSync", playerData[playerId])

def OnClientRequest(args):
    """处理客户端请求"""
    playerId = args.get("playerId")
    action = args.get("action")
    
    if action == "getCoins":
        ServerSystem.NotifyToClient(playerId, "CoinUpdate", {
            "coins": playerData.get(playerId, {}).get("coins", 0)
        })

ServerSystem.ListenForEvent("OnServerStarted", OnServerStarted)
ServerSystem.ListenForEvent("OnPlayerJoin", OnPlayerJoin)
ServerSystem.ListenForEvent("OnClientRequest", OnClientRequest)
''',
                    description="服务端网络同步代码",
                ),
                CodeBlock(
                    language="python",
                    code='''# 客户端代码 - network_sync_client.py
import mod.client.extraClientApi as clientApi

ClientSystem = clientApi.GetClientSystem()

def OnClientStarted(args):
    """客户端启动"""
    print("客户端网络同步示例已启动")
    # 请求初始数据
    RequestPlayerData()

def RequestPlayerData():
    """请求玩家数据"""
    ClientSystem.NotifyToServer("ClientRequest", {
        "action": "getCoins"
    })

def OnPlayerDataSync(args):
    """接收服务端数据"""
    coins = args.get("coins", 0)
    level = args.get("level", 1)
    print(f"同步数据: 金币={coins}, 等级={level}")

def OnCoinUpdate(args):
    """金币更新"""
    coins = args.get("coins", 0)
    print(f"金币更新: {coins}")

ClientSystem.ListenForEvent("OnClientStarted", OnClientStarted)
ClientSystem.ListenForEvent("PlayerDataSync", OnPlayerDataSync)
ClientSystem.ListenForEvent("CoinUpdate", OnCoinUpdate)
''',
                    description="客户端网络同步代码",
                ),
            ],
            explanation="展示客户端和服务端之间的网络通信。服务端存储玩家数据，客户端可以请求数据，服务端通过 NotifyToClient 同步数据。",
            warnings=[
                "网络消息名称必须在两端一致",
                "避免频繁发送大量数据",
            ],
            tips=[
                "使用 NotifyToClient 发送数据到客户端",
                "使用 NotifyToServer 发送数据到服务端",
                "自定义事件名需要两端注册",
            ],
            scope=EntryScope.BOTH,
        ))

        # 示例 5: 性能优化
        examples.append(ExampleCode(
            metadata=ExampleMetadata(
                name="performance_tips",
                title="性能优化示例",
                description="展示常用的性能优化技巧",
                category=ExampleCategory.PERFORMANCE,
                difficulty=DifficultyLevel.ADVANCED,
                tags=["performance", "optimization", "best-practices"],
                apis_used=[],
                events_used=[],
                prerequisites=["了解 Python 基础"],
                verified=True,
            ),
            code_blocks=[
                CodeBlock(
                    language="python",
                    code='''# 性能优化示例

# ❌ 不好的做法：频繁调用 API
def BadLoop():
    for i in range(1000):
        # 每次循环都获取玩家
        player = GetPlayerById(playerId)
        DoSomething(player)

# ✅ 好的做法：缓存结果
def GoodLoop():
    player = GetPlayerById(playerId)  # 只获取一次
    for i in range(1000):
        DoSomething(player)

# ❌ 不好的做法：创建大量定时器
def BadTimers():
    for entity in entities:
        CreateTimer(1.0, lambda: UpdateEntity(entity))

# ✅ 好的做法：合并更新
def GoodTimers():
    CreateTimer(1.0, UpdateAllEntities)

def UpdateAllEntities():
    for entity in entities:
        UpdateEntity(entity)

# ❌ 不好的做法：深拷贝大对象
def BadCopy():
    global largeData
    data = CopyDeep(largeData)  # 耗时操作
    ProcessData(data)

# ✅ 好的做法：使用引用或浅拷贝
def GoodCopy():
    global largeData
    data = largeData  # 直接引用
    ProcessData(data)

# ❌ 不好的做法：在事件处理中做复杂计算
def OnUpdateSlow(args):
    # 每帧都计算
    result = ComplexCalculation()
    ProcessResult(result)

# ✅ 好的做法：缓存计算结果
cachedResult = None
lastCalcTime = 0

def OnUpdateFast(args):
    global cachedResult, lastCalcTime
    currentTime = GetTime()
    
    # 每秒更新一次缓存
    if currentTime - lastCalcTime > 1.0:
        cachedResult = ComplexCalculation()
        lastCalcTime = currentTime
    
    ProcessResult(cachedResult)
''',
                    description="性能优化代码示例",
                ),
            ],
            explanation="展示常见的性能优化技巧：缓存、批量处理、避免频繁操作等。",
            tips=[
                "缓存频繁访问的数据",
                "合并批量操作",
                "避免在循环中调用 API",
                "使用定时器控制更新频率",
            ],
            scope=EntryScope.BOTH,
        ))

        return examples

    def _load_from_directory(self, path: Path) -> None:
        """从目录加载示例"""
        for example_file in path.rglob("*.json"):
            try:
                with open(example_file, encoding="utf-8") as f:
                    data = json.load(f)
                example = ExampleCode.from_dict(data)
                self.add_example(example)
            except Exception as e:
                print(f"加载示例失败: {example_file}, 错误: {e}")

    def save_example(self, example: ExampleCode) -> None:
        """保存示例到文件"""
        if not self.library_path:
            return

        self.library_path.mkdir(parents=True, exist_ok=True)
        example_file = self.library_path / f"{example.name}.json"

        with open(example_file, "w", encoding="utf-8") as f:
            json.dump(example.to_dict(), f, ensure_ascii=False, indent=2)


# 全局示例库实例
_library: ExampleLibrary | None = None


def get_example_library(library_path: str | None = None) -> ExampleLibrary:
    """获取全局示例库实例"""
    global _library
    if _library is None:
        _library = ExampleLibrary(library_path)
    return _library


def search_examples(query: str, limit: int = 10) -> list[ExampleCode]:
    """搜索示例（便捷函数）"""
    library = get_example_library()
    return library.search(query, limit=limit)


def get_example(name: str) -> ExampleCode | None:
    """获取示例（便捷函数）"""
    library = get_example_library()
    return library.get_example(name)


def list_examples(
    category: ExampleCategory | None = None,
    difficulty: DifficultyLevel | None = None,
    limit: int = 20,
) -> list[ExampleCode]:
    """列出示例（便捷函数）"""
    library = get_example_library()
    return library.list_examples(category=category, difficulty=difficulty, limit=limit)