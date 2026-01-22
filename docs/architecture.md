# System Architecture

This document provides a visual overview of empathySync's architecture. For detailed technical reference, see [CLAUDE.md](../CLAUDE.md).

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User's Machine                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     empathySync                               │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │   │
│  │  │  Streamlit  │───▶│  Wellness   │───▶│   Ollama    │       │   │
│  │  │    (UI)     │    │    Guide    │    │   (LLM)     │       │   │
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
│  │  │                   Local JSON Storage                   │   │   │
│  │  │   data/trusted_network.json    data/wellness_data.json │   │   │
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

## Request Flow (7-Step Safety Pipeline)

When a user sends a message, it passes through multiple safety checks:

```
User Input
    │
    ▼
┌─────────────────────────────────────────────┐
│  1. COOLDOWN CHECK                          │
│     WellnessTracker.should_enforce_cooldown │
│     - 7+ sessions today? → Block            │
│     - 120+ minutes today? → Block           │
│     - Dependency score ≥8? → Block          │
└─────────────────────────────────────────────┘
    │ Pass
    ▼
┌─────────────────────────────────────────────┐
│  2. RISK ASSESSMENT                         │
│     RiskClassifier.classify()               │
│     Returns: domain, emotional_intensity,   │
│              dependency_risk, risk_weight   │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  3. MODE SELECTION                          │
│     domain == "logistics" → Practical Mode  │
│     else → Reflective Mode                  │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  4. HARD STOP CHECK                         │
│     domain in [crisis, harmful] → Immediate │
│     intervention with resources             │
└─────────────────────────────────────────────┘
    │ Pass
    ▼
┌─────────────────────────────────────────────┐
│  5. TURN LIMIT CHECK                        │
│     Each domain has max turns:              │
│     logistics:20, money:8, health:8,        │
│     relationships:10, spirituality:5        │
└─────────────────────────────────────────────┘
    │ Pass
    ▼
┌─────────────────────────────────────────────┐
│  6. DEPENDENCY INTERVENTION                 │
│     If dependency_score > threshold:        │
│     Inject graduated intervention message   │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  7. IDENTITY REMINDER (Reflective only)     │
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
│  OLLAMA API CALL                            │
│     Local LLM generates response            │
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
Response to User
```

## Component Relationships

```
┌────────────────────────────────────────────────────────────────┐
│                          app.py                                 │
│                     (Streamlit Entry)                           │
│                                                                 │
│   Responsibilities:                                             │
│   - UI rendering (chat, sidebar, panels)                        │
│   - Session state management                                    │
│   - Routing between UI modes                                    │
└───────────────────────────┬────────────────────────────────────┘
                            │ uses
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
┌───────────────────┐ ┌───────────────┐ ┌───────────────────────┐
│   WellnessGuide   │ │WellnessTracker│ │    TrustedNetwork     │
│                   │ │               │ │                       │
│ - Response gen    │ │ - Sessions    │ │ - Trusted people      │
│ - Safety pipeline │ │ - Check-ins   │ │ - Domain suggestions  │
│ - Session state   │ │ - Policy log  │ │ - Reach-out history   │
│ - Policy actions  │ │ - Dependency  │ │ - Message templates   │
└─────────┬─────────┘ └───────────────┘ └───────────────────────┘
          │ uses
          ▼
┌───────────────────────────────────────────────────────────────┐
│                       RiskClassifier                           │
│                                                                 │
│   - Domain detection (7 domains)                                │
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
└─────────────────────────────┬─────────────────────────────────┘
                              │ reads
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                     scenarios/                                  │
│                  (YAML Knowledge Base)                          │
│                                                                 │
│   domains/          - Risk domains and triggers                 │
│   emotional_markers/ - Intensity detection                      │
│   interventions/    - Dependency, boundaries, graduation        │
│   prompts/          - Check-ins, mindfulness, styles            │
│   responses/        - Fallbacks, base prompt                    │
│   intents/          - Session intent configuration              │
└───────────────────────────────────────────────────────────────┘
```

## Two Operating Modes

```
┌─────────────────────────────────────────────────────────────────┐
│                       PRACTICAL MODE                            │
│                   (domain == "logistics")                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Triggered by: writing requests, coding, explanations          │
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
│   Example: "Help me write an email to my landlord"              │
│   → Full email draft with formatting                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      REFLECTIVE MODE                            │
│              (domain in sensitive domains)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Triggered by: emotional, health, money, relationships,        │
│                 spirituality content                            │
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
│   Example: "I'm worried about my marriage"                      │
│   → Brief acknowledgment + redirect to therapist/friend         │
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
│  │ - Gentle / Direct / Balanced                              │  │
│  │ - Selected by user                                        │  │
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

```
data/
├── wellness_data.json          # User wellness tracking
│   ├── check_ins[]             # Daily 1-5 wellness scores
│   ├── usage_sessions[]        # Session metadata
│   │   ├── duration            # Minutes
│   │   ├── turn_count          # Conversation turns
│   │   ├── domains_touched[]   # Which domains came up
│   │   └── max_risk_weight     # Highest risk in session
│   ├── policy_events[]         # Transparency log
│   │   ├── type                # What guardrail fired
│   │   ├── domain              # Related domain
│   │   ├── action_taken        # What happened
│   │   └── timestamp           # When
│   └── session_intents[]       # Intent check-in data (Phase 4)
│
└── trusted_network.json        # Human connection network
    ├── people[]                # Trusted contacts
    │   ├── name                # Display name
    │   ├── relationship        # "friend", "therapist", etc.
    │   ├── domains[]           # What they're good for
    │   └── contact             # How to reach them
    └── reach_outs[]            # Connection attempts
        ├── person_name         # Who they reached out to
        ├── method              # How (call, text, etc.)
        └── timestamp           # When
```

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
│      AI usage tracked alongside human connection                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
empathySync/
├── src/                          # Application source code
│   ├── app.py                   # Streamlit entry point
│   ├── config/
│   │   └── settings.py          # Environment configuration
│   ├── models/
│   │   ├── ai_wellness_guide.py # Core conversation engine
│   │   └── risk_classifier.py   # Risk assessment
│   ├── prompts/
│   │   └── wellness_prompts.py  # Dynamic prompt generation
│   └── utils/
│       ├── helpers.py           # Logging and utilities
│       ├── wellness_tracker.py  # Session/check-in tracking
│       ├── trusted_network.py   # Human network management
│       └── scenario_loader.py   # YAML knowledge base loader
│
├── scenarios/                    # Knowledge base (YAML)
│   ├── domains/                 # 7 risk domains
│   ├── emotional_markers/       # 4 intensity levels
│   ├── interventions/           # Dependency, boundaries
│   ├── prompts/                 # Check-ins, styles
│   ├── responses/               # Fallbacks, base prompt
│   └── intents/                 # Session intent config
│
├── data/                        # Local user data (JSON)
├── logs/                        # Application logs
├── tests/                       # Pytest test suite
└── docs/                        # Documentation
```

---

For detailed code-level documentation, see [CLAUDE.md](../CLAUDE.md).
