# Hello World Tutorial

This tutorial will guide you through creating your first ModSDK mod using MC-Agent-Kit.

## Prerequisites

- MC-Agent-Kit installed
- Basic Python knowledge

## Step 1: Create Mod Configuration

Create a `mod.json` file:

```json
{
    "format_version": 1,
    "header": {
        "name": "Hello World Mod",
        "description": "My first ModSDK mod",
        "uuid": "generate-a-uuid",
        "version": [1, 0, 0]
    },
    "modules": [
        {
            "type": "python",
            "uuid": "generate-another-uuid",
            "version": [1, 0, 0],
            "entry": "main.py"
        }
    ]
}
```

## Step 2: Generate Event Handler

Use MC-Agent-Kit to generate an event handler:

```bash
mc-agent gen template event_listener --params event_name=onPlayerJoin
```

This generates:

```python
def onPlayerJoin(args):
    """
    Called when a player joins the server.
    
    Args:
        args: Event arguments containing player info
    """
    player_name = args.get('player', 'Unknown')
    print(f"Player joined: {player_name}")
```

## Step 3: Create Main Script

Create `main.py`:

```python
# Register event handler
import mod_sdk

def onPlayerJoin(args):
    """Welcome message when player joins."""
    player_name = args.get('player', 'Unknown')
    
    # Send welcome message
    mod_sdk.DisplayClientMessage(
        player_name,
        f"Welcome to the server, {player_name}!"
    )

# Register the event
mod_sdk.RegisterEventListener("onPlayerJoin", onPlayerJoin)

print("Hello World Mod loaded!")
```

## Step 4: Check Your Code

Run the code checker:

```bash
mc-agent check check --file main.py
```

Fix any issues found.

## Step 5: Test Your Mod

1. Copy your mod to the game's `development_behavior_packs` folder
2. Launch Minecraft
3. Join a world
4. Check console for "Hello World Mod loaded!"
5. Have another player join and see the welcome message

## Next Steps

- [Custom Entity Tutorial](custom-entity.md)
- [Custom Item Tutorial](custom-item.md)
- [API Reference](../api/index.md)