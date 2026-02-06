# System Architecture

This document provides a visual overview of empathySync's architecture. For detailed technical reference, see [CLAUDE.md](../CLAUDE.md).

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User's Machine                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     empathySync                               │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │   │
│  │  │ Streamlit   │    │ Conversa-   │    │   Ollama    │       │   │
│  │  │   or CLI    │───▶│   tion      │───▶│   (LLM)     │       │   │
│  │  │ (Adapters)  │    │  Session    │    │ (Streaming) │       │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘       │   │
│  │         │                  │                                  │   │
│  │         │           ┌──────┴──────┐                          │   │
│  │         ▼           ▼             ▼                          │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐             │   │
│  │  │   Trusted   │ │    Risk     │ │   Wellness  │             │   │
│  │  │   Network   │ │  Classifier │ │   Tracker   │             │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘             │   │
│  │         │                │               │                    │   │
│  │         ▼                ▼               ▼                    │   │
│  │  ┌───────────────────────────────────────────────────────┐   │   │
│  │  │              Storage Backend (Write-Gated)             │   │   │
│  │  │  ┌─────────────────┐    ┌──────────────────────────┐  │   │   │
│  │  │  │  JSON Backend   │ OR │     SQLite Backend       │  │   │   │
│  │  │  │  (default)      │    │   (USE_SQLITE=true)      │  │   │   │
│  │  │  └─────────────────┘    └──────────────────────────┘  │   │   │
│  │  │       ↑ Write Gate blocks if another device has lock  │   │   │
│  │  └───────────────────────────────────────────────────────┘   │   │
│  │                              │                                │   │
│  │                              ▼                                │   │
│  │  ┌───────────────────────────────────────────────────────┐   │   │
│  │  │               Lock File (.empathySync.lock)            │   │   │
│  │  │           Heartbeat-based multi-device sync            │   │   │
│  │  └───────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      Ollama Server                            │   │
│  │                    (localhost:11434)                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│             ❌ No external API calls. Everything stays local.        │
└─────────────────────────────────────────────────────────────────────┘
```

## Request Flow (Safety Pipeline)

When a user sends a message, it passes through multiple safety checks:

```
User Input
    │
    ▼
┌─────────────────────────────────────────────┐
│  1. POST-CRISIS CHECK                       │
│     If previous turn was crisis intervention│
│     Handle deflection ("just joking") with  │
│     firm, non-apologetic response           │
│     Never apologize for crisis intervention │
└─────────────────────────────────────────────┘
    │ Pass
    ▼
┌─────────────────────────────────────────────┐
│  2. COOLDOWN CHECK                          │
│     WellnessTracker.should_enforce_cooldown │
│     - 7+ sessions today? → Block            │
│     - 120+ minutes today? → Block           │
│     - Dependency score ≥8? → Block          │
└─────────────────────────────────────────────┘
    │ Pass
    ▼
┌─────────────────────────────────────────────┐
│  3. RISK ASSESSMENT                         │
│     RiskClassifier.classify()               │
│     Returns: domain, emotional_intensity,   │
│              dependency_risk, risk_weight   │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  4. MODE SELECTION                          │
│     domain == "logistics" → Practical Mode  │
│     OR is_practical_technique → Practical   │
│     else → Reflective Mode                  │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  5. HARD STOP CHECK                         │
│     domain in [crisis, harmful] → Immediate │
│     intervention with resources             │
└─────────────────────────────────────────────┘
    │ Pass
    ▼
┌─────────────────────────────────────────────┐
│  6. TURN LIMIT CHECK                        │
│     Each domain has max turns:              │
│     logistics:20, money:8, health:8,        │
│     relationships:10, spirituality:5        │
└─────────────────────────────────────────────┘
    │ Pass
    ▼
┌─────────────────────────────────────────────┐
│  7. DEPENDENCY INTERVENTION                 │
│     If dependency_score > threshold:        │
│     Inject graduated intervention message   │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  8. IDENTITY REMINDER (Reflective only)     │
│     Every 6 turns: "I'm software,           │
│     not a person..."                        │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  PROMPT COMPOSITION                         │
│     Base rules + Style modifier +           │
│     Mode-specific rules + Risk context      │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  OLLAMA API CALL (Streaming)                │
│     Local LLM generates response            │
│     Tokens stream as generated              │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  SAFETY CHECK                               │
│     _contains_harmful_content()             │
│     Verify response is safe before display  │
└─────────────────────────────────────────────┘
    │
    ▼
Response to User (streamed in real-time)
```

## Component Relationships

```
┌────────────────────────────────────────────────────────────────┐
│                    Interface Adapters                           │
│         app.py (Streamlit)  │  cli_adapter.py (Terminal)        │
│                                                                 │
│   Responsibilities:                                             │
│   - UI rendering (chat, sidebar, panels)                        │
│   - User input handling                                         │
│   - Response display (streaming supported)                      │
└───────────────────────────┬────────────────────────────────────┘
                            │ uses
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    ConversationSession                          │
│               (Framework-Agnostic Orchestrator)                 │
│                                                                 │
│   - Owns all session state (turns, domains, risk history)       │
│   - Single entry: process_message() → ConversationResult        │
│   - Streaming: process_message_stream() + finalize_stream()     │
└───────────────────────────┬────────────────────────────────────┘
                            │ uses
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
┌───────────────────┐ ┌───────────────┐ ┌───────────────────────┐
│   WellnessGuide   │ │WellnessTracker│ │    TrustedNetwork     │
│                   │ │               │ │                       │
│ - Response gen    │ │ - Sessions    │ │ - Trusted people      │
│ - Safety pipeline │ │ - Check-ins   │ │ - Domain suggestions  │
│ - Streaming API   │ │ - Policy log  │ │ - Reach-out history   │
│ - Policy actions  │ │ - Dependency  │ │ - Message templates   │
└─────────┬─────────┘ └───────────────┘ └───────────────────────┘
          │ uses
          ▼
┌───────────────────────────────────────────────────────────────┐
│                       RiskClassifier                           │
│                                                                 │
│   - Domain detection (8 domains)                                │
│   - Emotional intensity (0-10)                                  │
│   - Emotional weight (for practical tasks)                      │
│   - Dependency risk scoring                                     │
│   - Intent detection (practical/processing/emotional/connection)│
│   - Intent shift detection                                      │
│   - Connection-seeking detection                                │
└─────────────────────────────┬─────────────────────────────────┘
                              │ uses
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                       ScenarioLoader                           │
│                        (Singleton)                              │
│                                                                 │
│   - Loads YAML knowledge base                                   │
│   - Caching with hot-reload support                             │
│   - Domain rules, triggers, responses                           │
│   - Emotional markers                                           │
│   - Intervention configurations                                 │
│   - Intent indicators                                           │
│   - Connection building signposts (Phase 12)                    │
└─────────────────────────────┬─────────────────────────────────┘
                              │ reads
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                     scenarios/                                  │
│                  (YAML Knowledge Base)                          │
│                                                                 │
│   domains/             - Risk domains and triggers              │
│   emotional_markers/   - Intensity detection                    │
│   connection_building/ - Signposts, first-contact (Phase 12)   │
│   interventions/       - Dependency, boundaries, graduation     │
│   prompts/             - Check-ins, mindfulness, styles         │
│   responses/           - Fallbacks, base prompt                 │
│   intents/             - Session intent configuration           │
└───────────────────────────────────────────────────────────────┘
```

## Two Operating Modes

```
┌─────────────────────────────────────────────────────────────────┐
│                       PRACTICAL MODE                            │
│       (domain == "logistics" OR is_practical_technique)         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Triggered by:                                                 │
│   - logistics domain: writing requests, coding, explanations    │
│   - is_practical_technique=true: "How do I X?" in any domain    │
│                                                                 │
│   Behavior:                                                     │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ ✓ Full response length (up to 2000 tokens)              │   │
│   │ ✓ Markdown formatting allowed                           │   │
│   │ ✓ Code blocks, lists, headers                           │   │
│   │ ✓ No identity reminders                                 │   │
│   │ ✓ No therapeutic framing                                │   │
│   │ ✓ Complete the task thoroughly                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   Examples:                                                     │
│   - "Help me write an email" → Full draft                       │
│   - "How do I meditate?" → Full technique instructions          │
│   - "What are some budgeting methods?" → Full practical list    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      REFLECTIVE MODE                            │
│    (sensitive domain AND is_practical_technique=false)          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Triggered by: guidance questions in sensitive domains         │
│   - "Should I X?" / "Is this right?" / "What does X want?"      │
│   - emotional, health, money, relationships, spirituality       │
│                                                                 │
│   Behavior:                                                     │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ ✗ Word limits enforced (50-150 words)                   │   │
│   │ ✗ Plain prose only, no formatting                       │   │
│   │ ✓ Redirects to human support                            │   │
│   │ ✓ Identity reminders every 6 turns                      │   │
│   │ ✓ Brief, restrained responses                           │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   Examples:                                                     │
│   - "I'm worried about my marriage" → Brief + human redirect    │
│   - "Should I get this surgery?" → Brief + doctor redirect      │
│   - "Is this my spiritual calling?" → Brief + mentor redirect   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                PRACTICAL TECHNIQUE DETECTION                    │
│                       (Phase 9.1)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   The LLM classifier distinguishes:                             │
│   - Technique questions: "How do I X?" → is_practical_technique │
│   - Guidance questions: "Should I X?" → reflective mode         │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Domain       │ Technique (✓)          │ Guidance (✗)    │   │
│   │──────────────│────────────────────────│─────────────────│   │
│   │ Spirituality │ "How to meditate?"     │ "Is this God's  │   │
│   │              │                        │  will for me?"  │   │
│   │ Health       │ "How to do a squat?"   │ "Should I get   │   │
│   │              │                        │  this surgery?" │   │
│   │ Money        │ "How to budget?"       │ "Should I       │   │
│   │              │                        │  invest?"       │   │
│   │ Relationships│ "How to write a        │ "Should I       │   │
│   │              │  wedding toast?"       │  break up?"     │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Prompt Composition (3 Layers)

```
┌─────────────────────────────────────────────────────────────────┐
│                     FINAL SYSTEM PROMPT                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ LAYER 1: Base Rules (responses/base_prompt.yaml)          │  │
│  │ - Core identity and behavior                              │  │
│  │ - Always applied                                          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          +                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ LAYER 2: Style Modifier (prompts/styles.yaml)             │  │
│  │ - Balanced (default)                                      │  │
│  │ - Auto-adjusts based on detected domain                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          +                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ LAYER 3: Risk Context                                     │  │
│  │ - Mode-specific rules (practical vs reflective)           │  │
│  │ - Domain-specific instructions                            │  │
│  │ - Emotional intensity adjustments                         │  │
│  │ - Intervention messages (if triggered)                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Storage

All data is stored locally with **write-gated backends** and **defense-in-depth** protection. See [persistence.md](persistence.md) for details.

### Storage Backends

| Backend | Enable | Files |
|---------|--------|-------|
| **JSON** (default) | `USE_SQLITE=false` | `wellness_data.json`, `trusted_network.json` |
| **SQLite** | `USE_SQLITE=true` | `empathySync.db`, `.db-wal`, `.db-shm` |

### Multi-Device Sync

| Setting | Enable | Purpose |
|---------|--------|---------|
| **Device Lock** | `ENABLE_DEVICE_LOCK=true` | Prevents concurrent writes |
| **Write Gate** | Automatic | Blocks writes when another device has lock |

```
data/
├── wellness_data.json          # (JSON backend) Atomic writes, schema v1
├── trusted_network.json        # (JSON backend) Atomic writes, schema v1
├── empathySync.db              # (SQLite backend) WAL mode, schema v2
├── empathySync.db-wal          # (SQLite) Write-ahead log
├── empathySync.db-shm          # (SQLite) Shared memory
├── .empathySync.lock           # Lock file (if ENABLE_DEVICE_LOCK=true)
└── .device_id                  # Persistent device identifier

# Data structure (both backends):
├── check_ins[]                 # Daily 1-5 wellness scores
├── usage_sessions[]            # Session metadata
│   ├── duration                # Minutes
│   ├── turn_count              # Conversation turns
│   ├── domains_touched[]       # Which domains came up
│   └── max_risk_weight         # Highest risk in session
├── policy_events[]             # Transparency log
├── session_intents[]           # Intent check-in data
├── trusted_people[]            # Trusted contacts
└── reach_outs[]                # Connection attempts (cascade delete with person)
```

### Write Safety

**JSON Backend:**
- Writes to temp file, flushed to disk (`fsync`), atomically renamed
- Corrupted files backed up with timestamp

**SQLite Backend:**
- WAL mode for crash safety
- `PRAGMA synchronous=FULL` for durability
- `PRAGMA foreign_keys=ON` enforced per-connection
- Schema v2: `ON DELETE CASCADE` for reach_outs

**Write Gate (defense-in-depth):**
1. UI disables inputs when read-only
2. `write_gate.py` flag blocks at module level
3. All 31 write methods check `_ensure_write_allowed()`
4. Checkpoint skipped in read-only mode

## Key Design Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                    DESIGN PRINCIPLES                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. LOCAL-FIRST                                                │
│      All processing on user's machine                           │
│      No external API calls                                      │
│      Data never leaves the device                               │
│                                                                 │
│   2. OPTIMIZE FOR EXIT                                          │
│      Turn limits, cooldowns, dependency detection               │
│      Bridge to human connection, don't replace it               │
│      Success = user needs this less                             │
│                                                                 │
│   3. TRANSPARENCY                                               │
│      Every policy action is logged and explained                │
│      Users see why guardrails fire                              │
│      No hidden manipulation                                     │
│                                                                 │
│   4. GRADUATED RESPONSE                                         │
│      5 dependency levels with increasing intervention           │
│      Warnings before blocks                                     │
│      Never abrupt cutoffs (except crisis)                       │
│                                                                 │
│   5. HUMAN-CENTRIC                                              │
│      Trusted Network is core feature, not afterthought          │
│      Handoff templates reduce friction to real connection       │
│      Connection building helps users find people (Phase 12)    │
│      AI usage tracked alongside human connection                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
empathySync/
├── src/                          # Application source code
│   ├── app.py                   # Streamlit entry point
│   ├── cli.py                   # CLI entry point (--mode web|cli)
│   ├── config/
│   │   └── settings.py          # Environment configuration
│   ├── models/
│   │   ├── ai_wellness_guide.py # Core conversation engine + streaming
│   │   ├── risk_classifier.py   # Risk assessment
│   │   ├── llm_classifier.py    # LLM-based classification (Phase 9)
│   │   ├── conversation_session.py # Framework-agnostic session manager
│   │   └── conversation_result.py  # Structured result dataclass
│   ├── interfaces/              # Interface adapters (Phase 16)
│   │   ├── adapter.py           # InterfaceAdapter protocol
│   │   └── cli_adapter.py       # Terminal interface
│   ├── prompts/
│   │   └── wellness_prompts.py  # Dynamic prompt generation
│   └── utils/
│       ├── helpers.py           # Logging and utilities
│       ├── wellness_tracker.py  # Session/check-in tracking
│       ├── trusted_network.py   # Human network management
│       ├── scenario_loader.py   # YAML knowledge base loader
│       ├── database.py          # SQLite layer (Phase 11)
│       ├── storage_backend.py   # JSON/SQLite abstraction (Phase 11)
│       ├── lockfile.py          # Multi-device lock (Phase 11)
│       └── write_gate.py        # Write permission control (Phase 11)
│
├── scenarios/                    # Knowledge base (YAML)
│   ├── domains/                 # 8 risk domains
│   ├── emotional_markers/       # 4 intensity levels
│   ├── classification/          # LLM classifier config (Phase 9)
│   ├── connection_building/     # Signposts, first-contact (Phase 12)
│   ├── interventions/           # Dependency, boundaries
│   ├── prompts/                 # Check-ins, styles
│   ├── responses/               # Fallbacks, base prompt
│   └── intents/                 # Session intent config
│
├── data/                        # Local user data (JSON/SQLite)
├── logs/                        # Application logs
├── tests/                       # Pytest test suite (360 tests)
└── docs/                        # Documentation
```

---

For detailed code-level documentation, see [CLAUDE.md](../CLAUDE.md).
