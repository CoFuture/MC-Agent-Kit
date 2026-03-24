"""Code examples for MC-Agent-Kit ModSDK development.

This module provides a collection of code examples:
- Basic usage examples
- Entity creation examples
- Event handling examples
- UI development examples
- Network examples
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExampleCategory(Enum):
    """Categories of examples."""
    BASIC = "basic"
    ENTITY = "entity"
    ITEM = "item"
    BLOCK = "block"
    UI = "ui"
    NETWORK = "network"
    EVENT = "event"
    ADVANCED = "advanced"
    PERFORMANCE = "performance"


@dataclass
class CodeExample:
    """A code example."""
    name: str
    category: ExampleCategory
    description: str
    code: str
    explanation: str = ""
    difficulty: str = "beginner"
    time_estimate: str = "10 min"
    tags: list[str] | None = None


# Basic Examples
BASIC_EXAMPLES: list[CodeExample] = [
    CodeExample(
        name="Hello World",
        category=ExampleCategory.BASIC,
        description="A simple hello world example",
        code="""# main.py - Hello World example
# This is the most basic ModSDK script

def main():
    # Print to game console
    print("Hello, Minecraft!")

if __name__ == "__main__":
    main()
""",
        explanation="This is the simplest ModSDK script. It demonstrates the basic structure of a Python script in the game environment.",
        difficulty="beginner",
        time_estimate="5 min",
        tags=["basic", "getting-started"],
    ),
    CodeExample(
        name="Event Listener",
        category=ExampleCategory.EVENT,
        description="Listen to server chat events",
        code="""# Listen to player chat messages
from mod.common import minecraftEnum
import mod.server.extraServerApi as serverApi

# Get server system
ServerSystem = serverApi.GetServerSystemCls()

class MySystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        
    def OnDestroy(self):
        # Clean up when system is destroyed
        pass

    def OnChat(self, args):
        # Handle chat event
        player_name = args.get('name', 'Unknown')
        message = args.get('message', '')
        
        print(f"[Chat] {player_name}: {message}")
        
        # Respond to specific commands
        if message.startswith('!hello'):
            # Send a message back to the player
            self.NotifyToClient(args['playerId'], 'OnServerMessage', {
                'message': 'Hello from server!'
            })

# Register the system
def create_system(namespace, systemName):
    return MySystem(namespace, systemName)
""",
        explanation="This example shows how to listen to player chat events and respond to commands. The OnChat method is called whenever a player sends a message.",
        difficulty="beginner",
        time_estimate="15 min",
        tags=["event", "chat", "server"],
    ),
    CodeExample(
        name="Timer Example",
        category=ExampleCategory.BASIC,
        description="Create a repeating timer",
        code="""# Timer example for delayed/repeated actions
from mod.common import minecraftEnum
import mod.server.extraServerApi as serverApi
import time

ServerSystem = serverApi.GetServerSystemCls()

class TimerSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        
        # Store timer IDs
        self.timers = {}
        
        # Create a repeating timer (every 5 seconds)
        self timers['repeat'] = self.CreateRepeatedTimer(
            5.0,  # 5 seconds
            self.OnTimerTick
        )
        
        # Create a one-shot timer (after 10 seconds)
        self.timers['oneshot'] = self.CreateDelayedTimer(
            10.0,  # 10 seconds
            self.OnDelayedAction
        )
        
    def OnDestroy(self):
        # Clean up timers
        for timer_id in self.timers.values():
            self.CancelTimer(timer_id)
    
    def OnTimerTick(self):
        # Called every 5 seconds
        print("Timer tick!")
    
    def OnDelayedAction(self):
        # Called once after 10 seconds
        print("Delayed action executed!")
""",
        explanation="This example demonstrates how to use timers for delayed and repeating actions. Timers are useful for game loops, periodic checks, and scheduled events.",
        difficulty="beginner",
        time_estimate="10 min",
        tags=["timer", "scheduling"],
    ),
]

# Entity Examples
ENTITY_EXAMPLES: list[CodeExample] = [
    CodeExample(
        name="Create Custom Entity",
        category=ExampleCategory.ENTITY,
        description="Create a custom entity with behaviors",
        code="""# Create a custom entity
from mod.common import minecraftEnum
import mod.server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystemCls()

class EntitySystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            'OnServerChat',
            self, self.OnChat
        )
        
    def OnChat(self, args):
        message = args.get('message', '')
        
        # Command to spawn entity
        if message == '!spawn':
            self.SpawnCustomEntity(args['playerId'])
    
    def SpawnCustomEntity(self, player_id):
        # Get player position
        pos = self.GetPos(player_id)
        
        # Create entity
        engine_type = {
            'identifier': 'myaddon:custom_entity',
            'type': 'custom_entity',
        }
        
        # Create entity at player position
        entity_id = self.CreateEngineEntity(
            engine_type,
            pos,
            0  # dimension ID
        )
        
        if entity_id:
            print(f"Spawned entity: {entity_id}")
            
            # Set entity properties
            self.SetEntityAttr(entity_id, 'speed', 1.5)
            self.SetEntityAttr(entity_id, 'health', 100)
        else:
            print("Failed to spawn entity")
""",
        explanation="This example shows how to create a custom entity in response to a chat command. The entity is created at the player's position with custom attributes.",
        difficulty="intermediate",
        time_estimate="30 min",
        tags=["entity", "spawn", "custom"],
    ),
    CodeExample(
        name="Entity Movement",
        category=ExampleCategory.ENTITY,
        description="Control entity movement",
        code="""# Control entity movement
from mod.common import minecraftEnum
import mod.server.extraServerApi as serverApi
import math

ServerSystem = serverApi.GetServerSystemCls()

class MovementSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        
        # Store tracked entities
        self.tracked_entities = {}
        
        # Create movement timer
        self.CreateRepeatedTimer(0.1, self.OnMovementTick)
        
    def OnMovementTick(self):
        # Update movement for all tracked entities
        for entity_id, data in self.tracked_entities.items():
            self.UpdateEntityMovement(entity_id, data)
    
    def UpdateEntityMovement(self, entity_id, data):
        # Get current position
        pos = self.GetPos(entity_id)
        if not pos:
            return
            
        # Calculate new position (simple patrol)
        target = data.get('target', pos)
        speed = data.get('speed', 1.0)
        
        # Move towards target
        dx = target[0] - pos[0]
        dz = target[2] - pos[2]
        distance = math.sqrt(dx*dx + dz*dz)
        
        if distance < 1.0:
            # Reached target, pick new target
            data['target'] = self.GetRandomTarget(pos)
        else:
            # Move towards target
            move_x = pos[0] + (dx / distance) * speed * 0.1
            move_z = pos[2] + (dz / distance) * speed * 0.1
            
            # Set new position
            self.SetPos(entity_id, (move_x, pos[1], move_z))
    
    def GetRandomTarget(self, current_pos):
        import random
        offset_x = random.uniform(-10, 10)
        offset_z = random.uniform(-10, 10)
        return (current_pos[0] + offset_x, current_pos[1], current_pos[2] + offset_z)
""",
        explanation="This example demonstrates how to control entity movement programmatically. Entities can follow targets, patrol areas, or respond to player actions.",
        difficulty="intermediate",
        time_estimate="45 min",
        tags=["entity", "movement", "ai"],
    ),
    CodeExample(
        name="Entity Collision Detection",
        category=ExampleCategory.ENTITY,
        description="Detect collisions between entities",
        code="""# Entity collision detection
from mod.common import minecraftEnum
import mod.server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystemCls()

class CollisionSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        
        # Listen for collision events
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            'OnEntityCollide',
            self, self.OnEntityCollide
        )
        
    def OnEntityCollide(self, args):
        entity1 = args.get('entityId1')
        entity2 = args.get('entityId2')
        collision_point = args.get('position')
        
        # Get entity types
        type1 = self.GetEntityType(entity1)
        type2 = self.GetEntityType(entity2)
        
        # Handle specific collision types
        if type1 == 'myaddon:custom_entity' and type2 == 'minecraft:player':
            self.OnEntityPlayerCollision(entity1, entity2, collision_point)
        elif type1 == 'myaddon:custom_entity' and type2 == 'myaddon:custom_entity':
            self.OnEntityEntityCollision(entity1, entity2, collision_point)
    
    def OnEntityPlayerCollision(self, entity, player, point):
        # Player touched entity
        print(f"Player {player} touched entity {entity}")
        
        # Example: Give player an item
        self.GiveItemToPlayer(player, 'minecraft:diamond', 1)
        
        # Example: Remove entity
        self.DestroyEntity(entity)
    
    def OnEntityEntityCollision(self, entity1, entity2, point):
        # Two entities collided
        print(f"Entities {entity1} and {entity2} collided")
""",
        explanation="This example shows how to detect and handle collisions between entities. You can use this for projectiles, pickups, triggers, and more.",
        difficulty="intermediate",
        time_estimate="30 min",
        tags=["entity", "collision", "physics"],
    ),
]

# UI Examples
UI_EXAMPLES: list[CodeExample] = [
    CodeExample(
        name="Simple UI Screen",
        category=ExampleCategory.UI,
        description="Create a simple UI screen",
        code="""# Simple UI screen example
from mod.common import minecraftEnum
import mod.client.extraClientApi as clientApi

ClientSystem = clientApi.GetClientSystemCls()

class UISystem(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        
        # Create UI screen
        self.ui_screen = None
        
        # Listen for events
        self.ListenForEvent(
            clientApi.GetEngineNamespace(),
            clientApi.GetEngineSystemName(),
            'OnKeyPress',
            self, self.OnKeyPress
        )
    
    def OnKeyPress(self, args):
        key = args.get('key')
        
        # Open UI on specific key press
        if key == 'E':  # E key
            if self.ui_screen:
                self.CloseUI()
            else:
                self.OpenUI()
    
    def OpenUI(self):
        # Create UI screen
        self.ui_screen = self.CreateUIScreen('myaddon:main_ui')
        
        # Set UI properties
        self.SetUIScreenProperty(self.ui_screen, 'title', 'My Addon UI')
        self.SetUIScreenProperty(self.ui_screen, 'visible', True)
        
        # Bind button callbacks
        self.BindUICallback(self.ui_screen, 'on_button_click', self.OnButtonClick)
    
    def CloseUI(self):
        if self.ui_screen:
            self.DestroyUIScreen(self.ui_screen)
            self.ui_screen = None
    
    def OnButtonClick(self, args):
        button_name = args.get('button', '')
        print(f"Button clicked: {button_name}")
        
        # Handle button actions
        if button_name == 'close':
            self.CloseUI()
        elif button_name == 'action':
            # Perform action
            self.NotifyToServer('OnClientAction', {'action': 'test'})
""",
        explanation="This example demonstrates creating a simple UI screen with button interactions. UI is client-side only and communicates with the server through events.",
        difficulty="intermediate",
        time_estimate="45 min",
        tags=["ui", "screen", "client"],
    ),
    CodeExample(
        name="Dynamic UI Updates",
        category=ExampleCategory.UI,
        description="Update UI dynamically with data",
        code="""# Dynamic UI updates example
from mod.common import minecraftEnum
import mod.client.extraClientApi as clientApi
import json

ClientSystem = clientApi.GetClientSystemCls()

class DynamicUISystem(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        
        self.ui_screen = None
        self.player_data = {
            'coins': 100,
            'level': 1,
            'items': ['sword', 'shield', 'potion']
        }
        
        # Listen for server updates
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            'OnDataUpdate',
            self, self.OnDataUpdate
        )
    
    def OnDataUpdate(self, args):
        # Update local data
        self.player_data.update(args)
        
        # Update UI if visible
        if self.ui_screen:
            self.RefreshUI()
    
    def RefreshUI(self):
        if not self.ui_screen:
            return
            
        # Update UI with current data
        self.SetUIScreenProperty(self.ui_screen, 'coins', self.player_data['coins'])
        self.SetUIScreenProperty(self.ui_screen, 'level', self.player_data['level'])
        
        # Update list (requires JSON serialization)
        items_json = json.dumps(self.player_data['items'])
        self.SetUIScreenProperty(self.ui_screen, 'items_json', items_json)
        
        # Trigger UI refresh
        self.NotifyToUI(self.ui_screen, 'OnRefresh', {})
""",
        explanation="This example shows how to update UI dynamically when data changes. This is useful for inventory screens, stats displays, and real-time updates.",
        difficulty="intermediate",
        time_estimate="30 min",
        tags=["ui", "dynamic", "data"],
    ),
]

# Performance Examples
PERFORMANCE_EXAMPLES: list[CodeExample] = [
    CodeExample(
        name="Optimized Event Handling",
        category=ExampleCategory.PERFORMANCE,
        description="Best practices for event performance",
        code="""# Optimized event handling
from mod.common import minecraftEnum
import mod.server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystemCls()

class OptimizedSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        
        # ✅ GOOD: Only register events you actually use
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            'OnServerChat',
            self, self.OnChat
        )
        
        # Cache frequently accessed data
        self.player_cache = {}
        
        # Batch processing for better performance
        self.pending_updates = []
        self.CreateRepeatedTimer(1.0, self.ProcessBatch)
        
    def OnChat(self, args):
        # ✅ GOOD: Quick validation first
        message = args.get('message', '')
        if not message:
            return
            
        # ✅ GOOD: Use cached data when possible
        player_id = args['playerId']
        if player_id not in self.player_cache:
            # Only query when not cached
            self.player_cache[player_id] = self.GetPlayerName(player_id)
        
        player_name = self.player_cache[player_id]
        
        # ✅ GOOD: Batch updates instead of immediate
        self.pending_updates.append({
            'player': player_name,
            'message': message,
            'time': self.GetServerTime()
        })
    
    def ProcessBatch(self):
        # Process all pending updates at once
        if not self.pending_updates:
            return
            
        # Process batch
        for update in self.pending_updates:
            self.ProcessUpdate(update)
        
        # Clear batch
        self.pending_updates = []
    
    def ProcessUpdate(self, update):
        # Individual update processing
        print(f"[{update['time']}] {update['player']}: {update['message']}")
""",
        explanation="This example demonstrates performance best practices: caching data, batching updates, and validating early. These patterns significantly improve performance in busy servers.",
        difficulty="advanced",
        time_estimate="45 min",
        tags=["performance", "optimization", "events"],
    ),
    CodeExample(
        name="Memory Management",
        category=ExampleCategory.PERFORMANCE,
        description="Proper memory management in ModSDK",
        code="""# Memory management best practices
from mod.common import minecraftEnum
import mod.server.extraServerApi as serverApi

ServerSystem = serverApi.GetServerSystemCls()

class MemoryAwareSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        
        # Store entity data with cleanup tracking
        self.entity_data = {}  # entity_id -> data
        self.player_sessions = {}  # player_id -> session data
        
        # Listen for entity/player destruction
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            'OnEntityDestruct',
            self, self.OnEntityDestruct
        )
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            'OnPlayerLeave',
            self, self.OnPlayerLeave
        )
    
    def OnDestroy(self):
        # ✅ IMPORTANT: Clean up all data when system is destroyed
        self.entity_data.clear()
        self.player_sessions.clear()
        print("System destroyed, memory cleared")
    
    def OnEntityDestruct(self, args):
        entity_id = args.get('entityId')
        
        # ✅ IMPORTANT: Remove entity data when entity is destroyed
        if entity_id in self.entity_data:
            del self.entity_data[entity_id]
            print(f"Cleaned up data for entity {entity_id}")
    
    def OnPlayerLeave(self, args):
        player_id = args.get('playerId')
        
        # ✅ IMPORTANT: Clean up player session data
        if player_id in self.player_sessions:
            del self.player_sessions[player_id]
            print(f"Cleaned up session for player {player_id}")
    
    def StoreEntityData(self, entity_id, data):
        # Store with automatic cleanup tracking
        self.entity_data[entity_id] = data
        
        # Optional: Limit memory usage
        MAX_ENTITIES = 1000
        if len(self.entity_data) > MAX_ENTITIES:
            # Remove oldest entries
            oldest = list(self.entity_data.keys())[:100]
            for eid in oldest:
                del self.entity_data[eid]
""",
        explanation="Memory management is critical in Python 2.7 environment. This example shows how to properly clean up data when entities or players are removed from the game.",
        difficulty="advanced",
        time_estimate="30 min",
        tags=["memory", "cleanup", "performance"],
    ),
]

# Get all examples by category
def get_examples_by_category(category: ExampleCategory) -> list[CodeExample]:
    """Get all examples for a category.

    Args:
        category: Category to filter by

    Returns:
        List of CodeExample objects
    """
    all_examples = BASIC_EXAMPLES + ENTITY_EXAMPLES + UI_EXAMPLES + PERFORMANCE_EXAMPLES
    return [ex for ex in all_examples if ex.category == category]


def get_all_examples() -> list[CodeExample]:
    """Get all available examples.

    Returns:
        List of all CodeExample objects
    """
    return BASIC_EXAMPLES + ENTITY_EXAMPLES + UI_EXAMPLES + PERFORMANCE_EXAMPLES


def get_example_by_name(name: str) -> CodeExample | None:
    """Get an example by name.

    Args:
        name: Example name

    Returns:
        CodeExample or None if not found
    """
    for ex in get_all_examples():
        if ex.name.lower() == name.lower():
            return ex
    return None


def search_examples(query: str) -> list[CodeExample]:
    """Search examples by query.

    Args:
        query: Search query

    Returns:
        List of matching CodeExample objects
    """
    query = query.lower()
    results = []
    
    for ex in get_all_examples():
        # Search in name, description, and tags
        if (query in ex.name.lower() or 
            query in ex.description.lower() or
            query in ex.code.lower() or
            (ex.tags and any(query in tag.lower() for tag in ex.tags))):
            results.append(ex)
    
    return results