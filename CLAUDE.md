# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

empathySync is a local-first AI assistant that provides **full help for practical tasks** while applying **restraint on sensitive topics**. It runs entirely on local hardware via Ollama integration - no external API calls.

**Core Philosophy**: "Help that knows when to stop"
- **Practical tasks** (writing emails, coding, explaining concepts): Full assistant capability, no word limits
- **Sensitive topics** (emotional, financial decisions, health, relationships): Brief responses, redirects to humans

The system actively works to reduce user dependency on AI for emotional support while being genuinely helpful for everyday practical tasks.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run src/app.py

# Run tests (100+ tests covering all core components)
pytest tests/

# Run tests with coverage
pytest tests/ --cov=src

# Linting and formatting
black src/
flake8 src/
mypy src/

# Validate YAML scenarios
python -c "import yaml; yaml.safe_load(open('scenarios/domains/money.yaml'))"
```

## Required Environment Variables

Configure in `.env` file (see `.env.example`):

**Required:**
- `OLLAMA_HOST` - Ollama server URL (e.g., `http://localhost:11434`)
- `OLLAMA_MODEL` - Model name to use (e.g., `llama2`)
- `OLLAMA_TEMPERATURE` - Temperature for responses (default: 0.7)

**Optional:**
- `ENVIRONMENT` - development/production
- `DEBUG` - true/false
- `LOG_LEVEL` - DEBUG/INFO/WARNING/ERROR
- `STORE_CONVERSATIONS` - true/false
- `CONVERSATION_RETENTION_DAYS` - integer (default: 30)
- `LLM_CLASSIFICATION_ENABLED` - true/false (default: true) - enables LLM-based intelligent classification (Phase 9)

**Storage Backend (Phase 11):**
- `USE_SQLITE` - true/false (default: false) - enables SQLite backend with WAL mode
- `ENABLE_DEVICE_LOCK` - true/false (default: false) - enables heartbeat-based lock file for multi-device sync
- `LOCK_STALE_TIMEOUT` - integer (default: 300) - seconds until a lock is considered stale

**Optional PostgreSQL** (all or none): `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

## Architecture

### Directory Structure

```
empathySync/
├── src/                          # Application source code
│   ├── app.py                   # Streamlit entry point (~1500 lines)
│   ├── config/settings.py       # Environment configuration
│   ├── models/
│   │   ├── ai_wellness_guide.py # Core conversation engine (~800 lines)
│   │   ├── risk_classifier.py   # Risk assessment + intent detection (~600 lines)
│   │   └── llm_classifier.py    # LLM-based classification (Phase 9)
│   ├── prompts/
│   │   └── wellness_prompts.py  # Dynamic prompt generation (~350 lines)
│   └── utils/
│       ├── helpers.py           # Logging and utilities
│       ├── wellness_tracker.py  # Session/check-in/metrics tracking (~1400 lines)
│       ├── trusted_network.py   # Human network management (~500 lines)
│       └── scenario_loader.py   # YAML knowledge base loader (~1300 lines)
├── scenarios/                    # Knowledge base (32 YAML files)
│   ├── domains/                 # 8 risk domains (crisis, harmful, health, money, emotional, relationships, spirituality, logistics)
│   ├── emotional_markers/       # 4 intensity levels
│   ├── emotional_weight/        # Task weight detection (high/medium/low)
│   ├── classification/          # LLM classifier prompts and config
│   ├── graduation/              # Competence graduation prompts
│   ├── handoff/                 # Human handoff templates
│   ├── intents/                 # Session intent configuration
│   ├── interventions/           # Dependency, boundaries
│   ├── metrics/                 # Success metrics configuration
│   ├── prompts/                 # Check-ins, mindfulness, styles
│   ├── responses/               # Fallbacks, safe alternatives, base prompt
│   ├── transparency/            # Explanation templates
│   └── wisdom/                  # Immunity building prompts
├── tests/                       # Pytest test suite (100+ tests)
├── data/                        # Local user data (JSON files)
├── docs/                        # Documentation
└── logs/                        # Application logs
```

### Core Components

**Entry Point**: [src/app.py](src/app.py) - Streamlit application with:
- Chat interface (communication style auto-adjusts based on detected domain)
- Wellness sidebar with usage health indicators
- Reality check panel showing dependency signals
- Trusted network setup and human handoff templates
- Session tracking, export, and policy action transparency

**Models**:
- [src/models/ai_wellness_guide.py](src/models/ai_wellness_guide.py) - `WellnessGuide` class: main conversation engine with 7-step safety pipeline, session state tracking, context persistence, and identity reminder injection
- [src/models/risk_classifier.py](src/models/risk_classifier.py) - `RiskClassifier` class: detects conversation domain (8 domains), measures emotional intensity (0-10), assesses dependency risk, intent detection, and provides domain-specific rules
- [src/models/llm_classifier.py](src/models/llm_classifier.py) - `LLMClassifier` class: LLM-based intelligent classification with caching, used for context-aware domain detection when `LLM_CLASSIFICATION_ENABLED=true`

**Prompts**:
- [src/prompts/wellness_prompts.py](src/prompts/wellness_prompts.py) - `WellnessPrompts` class: builds system prompts via 3-layer composition (base rules + style modifier + risk context)

**Utils**:
- [src/utils/wellness_tracker.py](src/utils/wellness_tracker.py) - `WellnessTracker` class: tracks sessions, check-ins, policy events; calculates dependency signals; enforces cooldowns
- [src/utils/trusted_network.py](src/utils/trusted_network.py) - `TrustedNetwork` class: manages trusted contacts, domain-specific suggestions, reach-out history, connection health metrics
- [src/utils/scenario_loader.py](src/utils/scenario_loader.py) - `ScenarioLoader` class: singleton loader for YAML knowledge base with caching and hot-reload support
- [src/utils/helpers.py](src/utils/helpers.py) - Logging setup and environment validation
- [src/utils/database.py](src/utils/database.py) - SQLite database layer with WAL mode, transactions, schema migrations (Phase 11)
- [src/utils/storage_backend.py](src/utils/storage_backend.py) - Unified storage abstraction for JSON/SQLite backends with write gate protection (Phase 11)
- [src/utils/lockfile.py](src/utils/lockfile.py) - Heartbeat-based lock file for multi-device sync safety (Phase 11)
- [src/utils/write_gate.py](src/utils/write_gate.py) - Centralized write permission control for read-only mode (Phase 11)

**Config**:
- [src/config/settings.py](src/config/settings.py) - `Settings` class: environment-based configuration with validation

### Two Operating Modes

**1. Practical Mode** (logistics domain)
- Triggered by: writing requests, coding, explanations, general questions
- Behavior: Full assistant capability
  - No word limits (up to 2000 tokens)
  - Markdown formatting, code blocks, lists allowed
  - Complete the task thoroughly
  - No identity reminders or therapeutic framing

**2. Reflective Mode** (sensitive domains)
- Triggered by: emotional content, financial decisions, health concerns, relationships, spirituality
- Behavior: Brief, restrained responses
  - Word limits enforced (50-150 words)
  - Plain prose, no formatting
  - Redirects to human support
  - Identity reminders every 6 turns

### Data Flow (Safety Pipeline)

1. User input received in Streamlit chat
2. **Post-Crisis Check**: If previous turn was a crisis intervention, handle deflection patterns ("just joking") with firm, non-apologetic response. Never apologize for crisis interventions.
3. **Cooldown Check**: `WellnessTracker.should_enforce_cooldown()` blocks if usage limits exceeded
4. **Risk Assessment**: `RiskClassifier.classify()` returns domain, emotional intensity, dependency risk, and combined risk weight
5. **Mode Selection**: `logistics` domain → Practical Mode, other domains → Reflective Mode
6. **Hard Stop Check**: Crisis/harmful domains trigger immediate intervention
7. **Turn Limit Check**: Domain-specific turn limits enforced:
   - `logistics`: 20 turns (practical tasks)
   - `money`: 8 turns
   - `health`: 8 turns
   - `relationships`: 10 turns
   - `spirituality`: 5 turns
   - `crisis/harmful`: 1 turn
8. **Dependency Intervention**: Graduated responses if dependency score exceeds thresholds
9. **Identity Reminder**: Injected every 6 turns (only in Reflective Mode)
10. System prompt composed (base + style + mode-specific rules + post-crisis context if applicable), Ollama called locally
11. Response safety-checked via `_contains_harmful_content()` before display

### Risk Assessment

The `RiskClassifier` produces:
```python
{
    "domain": str,                  # money, health, relationships, spirituality, crisis, harmful, emotional, logistics
    "emotional_weight": str,        # high_weight, medium_weight, low_weight (for practical tasks)
    "emotional_weight_score": float,  # 0-10 scale
    "emotional_intensity": float,   # 0-10 scale
    "dependency_risk": float,       # 0-10 scale (from conversation patterns)
    "risk_weight": float,           # Combined 0-10 risk score
    "classification_method": str,   # "llm" or "keyword" (Phase 9)
    "is_personal_distress": bool,   # LLM-detected personal vs general topic (Phase 9)
    "llm_confidence": float,        # 0-1 confidence score (when LLM used)
    "intervention": dict            # Present if dependency threshold met
}
```

### Emotional Weight (Practical Tasks Only)

Separate from emotional intensity, emotional weight measures how "heavy" a practical task is:
- **Emotional intensity**: How emotionally charged is the USER right now?
- **Emotional weight**: How emotionally heavy is the TASK itself?

| Weight Level | Score | Examples | Acknowledgment |
|--------------|-------|----------|----------------|
| high_weight | 8.0 | Resignation, breakup, apology, condolence | Warm acknowledgment appended |
| medium_weight | 5.0 | Negotiation, complaint, asking for help | Brief acknowledgment (optional) |
| low_weight | 2.0 | Grocery list, code help, general questions | None |

For high-weight practical tasks, a brief human acknowledgment is appended:
> "Here's your resignation email.\n\n---\n\nThese transitions are hard. You'll find your words when the time comes."

**Dependency Scoring** (12-message lookback):
- Base factor: frequency × 0.7 (capped at 6.0)
- Repetition boost: unique prefix ratio × 4.0 max
- Final score capped at 10.0

### Scenarios Knowledge Base

All domain rules, prompts, and interventions are defined in YAML files under `scenarios/`. See [scenarios/README.md](scenarios/README.md) for editing guidelines.

**Domain Files** (`scenarios/domains/`):
| Domain | Risk Weight | Description |
|--------|-------------|-------------|
| crisis | 10.0 | Suicidal ideation, self-harm |
| harmful | 10.0 | Illegal/violent intent |
| health | 7.0 | Medical concerns (symptoms, medications) |
| money | 6.0 | Financial topics (loans, debt, investments) |
| emotional | 5.0 | General emotional expressions |
| relationships | 5.0 | Interpersonal dynamics (partner, family) |
| spirituality | 4.0 | Religious/spiritual matters |
| logistics | 1.0 | Neutral/default topics |

**Hot Reloading** (for development):
```python
from src.utils.scenario_loader import get_scenario_loader
loader = get_scenario_loader()
loader.reload()  # Picks up changes from disk
```

### Data Persistence

All user data is stored locally with **atomic writes**, **schema versioning**, and optional **SQLite backend**.

For detailed multi-device sync documentation, see [docs/persistence.md](docs/persistence.md).

**Storage Backends:**
- **JSON Backend** (default): Simple, human-readable files with atomic writes
- **SQLite Backend** (`USE_SQLITE=true`): WAL mode, transactions, better concurrency

**Write Safety (JSON):**
- Writes to temp file (`.wellness_data_*.tmp`)
- Flushes and fsyncs to disk
- Atomic rename via `os.replace()` (POSIX-guaranteed atomic)
- Corrupted files backed up as `.corrupted.{timestamp}.json`

**Write Safety (SQLite):**
- WAL mode (`PRAGMA journal_mode=WAL`) for crash safety
- `PRAGMA synchronous=FULL` for durability
- `PRAGMA foreign_keys=ON` enforced per-connection
- Checkpoint on close (`wal_checkpoint(TRUNCATE)`)
- Schema v2: `ON DELETE CASCADE` for reach_outs → trusted_people

**Write Gate (Phase 11):**
When another device holds the lock (`ENABLE_DEVICE_LOCK=true`), all write operations are blocked:
- `src/utils/write_gate.py` provides centralized control
- All storage backend write methods check permission before executing
- Checkpoint is skipped in read-only mode
- UI shows "Writes blocked" indicator in sidebar

**`data/wellness_data.json`** (or SQLite `empathySync.db`):
```json
{
  "schema_version": 1,    // For safe migrations
  "check_ins": [...],       // Daily wellness scores (1-5 scale)
  "usage_sessions": [...],  // Session metadata (duration, turns, domains, risk)
  "policy_events": [...],   // Transparency log of policy actions
  "created_at": "datetime"
}
```

**`data/trusted_network.json`** (or SQLite tables):
```json
{
  "schema_version": 1,    // For safe migrations
  "people": [...],      // Trusted contacts with domains and relationship info
  "reach_outs": [...],  // History of human connection attempts (cascade delete on person removal)
  "created_at": "datetime"
}
```

**Schema Versions:**
- v1: Initial schema with all required fields
- v2 (SQLite): Added `ON DELETE CASCADE` to reach_outs foreign key

**Schema Migration:** On load, files/databases are automatically migrated from older schema versions. Migration functions run sequentially (v0→v1→v2...) and save the updated data.

### Cooldown Enforcement

`WellnessTracker.should_enforce_cooldown()` returns true when:
- 7+ sessions today
- 120+ minutes today
- Dependency score >= 8

### Key Design Constraints (from MANIFESTO.md)

- All processing must remain local - no external API calls
- No telemetry, engagement metrics, or behavior tracking
- User data belongs to the user - stored only in local JSON files
- Features must center human wellbeing and psychological safety
- Reject any feature that enables manipulation or exploits user vulnerability
- Never optimize for engagement or increased usage

### UI Components (app.py)

- **Chat Interface**: Main conversation area with message history
- **Wellness Sidebar**: Health indicators, check-in prompts, toggle panels
- **Reality Check Panel**: Dependency signals with human-readable warnings
- **Trusted Network Setup**: Add/manage trusted contacts by domain
- **Bring Someone In**: Pre-written templates for human handoff (need_to_talk, reconnecting, checking_in, hard_conversation, asking_for_help)
- **Session Export**: Download conversation as JSON
- **Policy Transparency**: Displays last policy action with explanation

### Testing

Tests are in [tests/test_wellness_guide.py](tests/test_wellness_guide.py) with 100+ tests covering:
- `TestScenarioLoader`: YAML loading and caching
- `TestRiskClassifier`: Domain detection, emotional intensity, dependency scoring
- `TestWellnessPrompts`: Prompt composition and style modifiers
- `TestWellnessGuide`: Response generation, safety pipeline, error handling

### Key Patterns

- **Singleton Pattern**: `ScenarioLoader` via `get_scenario_loader()`, `StorageBackend` via `get_storage_backend()`
- **3-Layer Prompt Composition**: Base rules + style modifier + risk context
- **Graduated Interventions**: 5 dependency levels (none, early_pattern, mild, concerning, high)
- **Session State Tracking**: Turns, domains, max risk, last policy action, post-crisis turn
- **Post-Crisis Protection**: Tracks when crisis intervention occurred, prevents LLM from apologizing for safety actions
- **Hot Reload Support**: `loader.reload()` and `loader.clear_cache()`
- **Transparency Logging**: All policy decisions logged with reasons
- **Defense-in-Depth Write Protection**: UI disabling → write gate flag → storage method checks (Phase 11)
- **Heartbeat-Based Lock**: Device lock uses timestamp heartbeats, not PIDs, for stale detection (Phase 11)
- **Storage Backend Abstraction**: Unified interface for JSON/SQLite with automatic migration (Phase 11)

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the phased implementation plan covering:
- Phase 1: Foundation Fixes ✅
- Phase 2: Emotional Weight Layer ✅
- Phase 2.5: Robustness & Classification Fixes ✅
- Phase 3: Competence Graduation ✅
- Phase 4: "Why Are You Here?" Check-In ✅
- Phase 5: Enhanced Human Handoff ✅
- Phase 6: Transparency & Explainability ✅
- Phase 6.5: Context Persistence ✅
- Phase 7: Success Metrics (Local-First) ✅
- Phase 8: Immunity Building & Wisdom Prompts ✅ (Core)
- Phase 9: LLM-Based Intelligent Classification ✅
- Phase 10: Advanced Detection (Long-term)
- Phase 11: Persistence Hardening & Multi-Device Sync ✅ (Core)
