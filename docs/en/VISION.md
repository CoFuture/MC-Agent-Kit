# MC-Agent-Kit Project Vision & Design

> Version: v1.0.0
> Last Updated: 2026-03-22

---

## 1. Project Vision

### Core Positioning

**Enable AI Agents to autonomously complete the Minecraft NetEase ModSDK Addon development lifecycle**

```
Requirements Analysis → Code Development → Testing & Verification → Iterative Fixes
```

### Design Principles

1. **Agent First** - Design capabilities prioritizing LLM usability
2. **Minimum Viable Loop** - Focus on core workflow early
3. **Progressive Enhancement** - First make it work, then make it good, finally make it smart

### Target Users

- AI Agents (via OpenClaw and similar platforms)
- ModSDK Developers (via CLI tools)

---

## 2. Core Capability Planning

### MVP Capability Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                      MVP Capability Loop                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│   │   Search    │ ──→ │   Develop   │ ──→ │    Test     │      │
│   │ Knowledge   │     │ Scaffold    │     │ Launcher    │      │
│   └─────────────┘     └─────────────┘     └─────────────┘      │
│         │                   │                   │              │
│         ▼                   ▼                   ▼              │
│   Query API/events     Create project      Launch game         │
│   Find examples        Generate code       Capture logs        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Capability List

| Module | Form | Core Functions | Priority |
|--------|------|----------------|----------|
| **Knowledge Search** | Skill + CLI | API/Event docs search, Example code search | P0 |
| **Project Scaffold** | CLI | Create standard Addon project structure | P0 |
| **Game Launcher** | CLI | Launch game+Addon, Capture logs | P0 |
| **Error Diagnosis** | Skill | Analyze logs, Identify errors, Suggest fixes | P1 |
| **Code Generation** | Skill | Event listeners, API call templates | P1 |

---

## 3. Architecture Design

### Overall Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Agent Interface Layer                  │
│                     (Interface for Agent calls)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────────────┐    ┌─────────────────────┐   │
│   │      OpenClaw Skills        │    │      CLI Tools      │   │
│   │    (Atomic capabilities)    │    │  (Simplified CLI)   │   │
│   ├─────────────────────────────┤    ├─────────────────────┤   │
│   │ modsdk-search               │    │ mc-kb search        │   │
│   │ modsdk-diagnose             │    │ mc-create project   │   │
│   │ modsdk-code-gen             │    │ mc-create entity    │   │
│   └─────────────────────────────┘    │ mc-run              │   │
│                                       │ mc-logs             │   │
│                                       └─────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Core Capability Layer                  │
│                          (Core implementations)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Launcher      Scaffold       KnowledgeBase      Diagnoser    │
│   (Game launch) (Scaffold)     (Search)           (Diagnosis)  │
│                                                                 │
│   Generator     LogCapture     ConfigGen         Autofix       │
│   (Code gen)    (Log capture)  (Config)          (Auto-fix)    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Module Detailed Design

### 4.1 Knowledge Search (Knowledge)

#### Skill: `modsdk-search`

```
Purpose: Semantic search of ModSDK documentation

Input:
  query: string      # Query content, e.g., "how to create custom entity"
  top_k: int         # Number of results, default 5

Output:
  {
    "apis": [          # Related API list
      {
        "name": "CreateEngineEntity",
        "description": "Create entity",
        "module": "Entity",
        "scope": "server",
        "parameters": [...],
        "example": "..."
      }
    ],
    "events": [...],   # Related events list
    "examples": [...], # Example code
    "guide": "..."     # Implementation guide (optional)
  }
```

#### CLI: `mc-kb`

```bash
mc-kb search <query>           # Semantic search
mc-kb api <name>               # Exact API lookup
mc-kb event <name>             # Exact event lookup
mc-kb build [--full]           # Build/rebuild index
mc-kb update                   # Incremental index update
mc-kb status                   # View status
```

#### Technical Approach

- **Embedding**: Local bge-large-zh-v1.5 (switchable to API)
- **Retrieval Strategy**: Hybrid search, semantic 60% + keyword 40%
- **Data Sources**:
  - Official docs (resources/docs/mcdocs)
  - Embedded example code
  - Demo projects (future extension)

---

### 4.2 Project Scaffold

#### CLI: `mc-create`

```bash
# Create new project
mc-create project <name> [--template <template>]
# Generates:
# my-addon/
# ├── behavior_pack/
# │   ├── manifest.json
# │   ├── entities/
# │   └── scripts/
# │       └── main.py
# └── resource_pack/
#     ├── manifest.json
#     └── textures/

# Add entity to existing project
mc-create entity <name> [--in <path>]
# Generates:
# - behavior_pack/entities/<name>.json
# - behavior_pack/scripts/<name>.py
# - resource_pack/entity/<name>.geo.json
# - resource_pack/textures/entity/<name>.png

# Add item
mc-create item <name> [--in <path>]

# Add block
mc-create block <name> [--in <path>]
```

#### Template Types

| Template | Description |
|----------|-------------|
| `empty` | Empty project with basic structure only |
| `entity` | Includes entity development template |
| `item` | Includes item development template |
| `block` | Includes block development template |

---

### 4.3 Game Launcher

#### CLI: `mc-run`

```bash
mc-run <addon-path> [--timeout <seconds>] [--verbose]

# JSON output
{
  "success": true,
  "pid": 12345,
  "duration": 45,
  "logs": "path/to/logs.txt",
  "errors": [],
  "warnings": ["deprecated API: xxx"]
}
```

#### CLI: `mc-logs`

```bash
mc-logs [--analyze] [--tail] [--follow]
```

---

### 4.4 Error Diagnosis (Diagnoser)

#### Skill: `modsdk-diagnose`

```
Purpose: Analyze logs, diagnose errors, suggest fixes

Input:
  logs: string       # Log content
  error: string      # Error message (optional)

Output:
  {
    "error_type": "KeyError",
    "error_message": "'speed' not found",
    "location": {
      "file": "main.py",
      "line": 42
    },
    "possible_causes": [
      "Variable speed not defined",
      "Dictionary missing speed key"
    ],
    "fix_suggestions": [
      {
        "description": "Check if variable is defined",
        "code": "if 'speed' in config:\n    speed = config['speed']"
      }
    ],
    "related_docs": [
      "modsdk-search result..."
    ]
  }
```

---

### 4.5 Code Generation (Generator)

#### Skill: `modsdk-code-gen`

```
Purpose: Generate code snippets based on requirements

Input:
  template: string   # Template type: event_listener, api_call, entity_create
  params: dict       # Template parameters

Output:
  {
    "code": "...",
    "imports": ["from mod.common import ..."],
    "dependencies": ["Event: OnServerChat"],
    "notes": ["Needs to run on server side"]
  }
```

#### Built-in Templates

| Template | Description | Parameters |
|----------|-------------|------------|
| `event_listener` | Event listener | event_name, callback |
| `api_call` | API call | api_name, params |
| `entity_create` | Create entity | entity_name, behaviors |
| `item_register` | Register item | item_name, properties |

---

## 5. Implementation Roadmap

### Week 1-2: Infrastructure

- [x] Fix launcher compatibility issues
- [x] Complete knowledge base index building
- [x] Implement `mc-kb search` basic functionality
- [x] Unit test coverage

### Week 3-4: Core Loop

- [x] Implement `mc-create project`
- [x] Implement `mc-run` structured output
- [x] Integrate `modsdk-search` Skill
- [x] End-to-end testing

### Week 5-6: Enhancement & Polish

- [x] Error diagnosis capabilities
- [x] Example code retrieval enhancement
- [x] Documentation completion
- [x] Performance optimization

---

## 6. Success Criteria

| Milestone | Acceptance Criteria |
|-----------|---------------------|
| M1: Launcher Usable | Can stably launch game and load Addon, no memory errors |
| M2: Knowledge Search Effective | Searching "create entity" returns CreateEntity API and examples |
| M3: Create Project Usable | `mc-create project` generates runnable project |
| M4: Loop Connected | Agent can complete: search docs → create project → launch test → diagnose errors |

---

## 7. Extension Directions (Future Iterations)

### Phase 2: Enhanced Development Experience

- Hot reload support
- More scaffold templates
- Code completion enhancement
- Performance analysis

### Phase 3: Intelligence Enhancement

- Requirements analysis and solution design
- Automated test scenarios
- Regression testing
- Best practice checking

### Phase 4: Ecosystem Integration

- Git operation integration
- Team collaboration
- Template marketplace
- Community contributions

---

*This document will be continuously updated with project iterations.*