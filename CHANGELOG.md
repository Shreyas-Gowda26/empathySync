# Changelog

All notable changes to empathySync are documented here.

## v1.0 (2026-02-06) — Core Decoupling & Streaming

**"The soul as a library."**

Phase 16 complete. The conversation engine is now framework-agnostic and can be embedded in any Python project. Streaming support for real-time response delivery.

### Core Decoupling (Phase 16)
- **ConversationSession class**: Framework-agnostic session manager that owns all conversation state. Single entry point: `process_message()` → `ConversationResult`.
- **InterfaceAdapter protocol**: Minimal contract for UI adapters. Any interface can drive the conversation engine.
- **CLIAdapter**: Direct terminal interface (`empathysync --mode cli`) proving the abstraction works.
- **Streamlit refactored**: `app.py` now uses `ConversationSession` instead of scattered `st.session_state`.

### Streaming Support
- **Real-time token streaming**: Responses stream as they're generated instead of blocking for completion.
- **`generate_response_stream()`**: Generator method in `WellnessGuide` that yields tokens progressively.
- **`process_message_stream()`**: Session-level streaming API with `finalize_stream()` for post-stream metadata.
- **CLI streaming**: Tokens appear in terminal as generated (`sys.stdout.write` + flush).
- **Streamlit streaming**: Uses `st.write_stream()` for progressive display.
- **Safety preserved**: Pre-LLM pipeline runs synchronously. Crisis/harmful returns complete immediately.

### Fixes
- **LLM classifier false positive**: Geopolitical questions ("Do you think war is upon us?") no longer classified as crisis.
- **Black formatting**: Pre-commit hook added to catch formatting issues before CI.

### Stats
- **360 tests passing** (up from 323)
- **15 new streaming tests**
- All existing functionality preserved

---

## v0.9-beta (2026-02-01) — First Public Release

**"Help that knows when to stop."**

This is the first tagged release of empathySync — a local-first AI assistant that provides full help for practical tasks while applying restraint on sensitive topics. 14 phases of development, 323 tests passing.

### Core Engine
- **Dual-mode operation**: Full assistance for practical tasks (emails, code, explanations). Brief, restrained responses for sensitive topics (relationships, health, finances, spirituality) with human redirect.
- **LLM-based classification** (Phase 9): Context-aware domain detection via Ollama replaces brittle keyword matching. Hybrid system: fast-path for safety-critical, LLM for nuance, keyword fallback.
- **Practical technique detection** (Phase 9.1): "How do I meditate?" gets full help. "Is this God's will?" gets restraint + human redirect. Works across all sensitive domains.
- **7-step safety pipeline**: Cooldown check → risk assessment → hard stop → turn limits → dependency intervention → identity reminder → response generation.
- **Crisis intervention**: Immediate redirect to professional resources. Never engages with crisis content. Never apologizes for safety interventions. Post-crisis deflection handling ("just joking") stays firm.

### Anti-Dependency Systems
- **Dependency scoring** (12-message lookback): Tracks frequency and repetition patterns. Graduated interventions at 5 levels.
- **Anti-engagement metrics** (Phase 7): Tracks sensitive topic usage only — practical tasks are neutral. Week-over-week comparison where fewer sensitive sessions = success.
- **"What Would You Tell a Friend?"** (Phase 8): Flips the question on sensitive topics to help users access their own wisdom.
- **"Before You Send" pause** (Phase 8): Suggests sleeping on high-stakes messages (resignations, difficult conversations).
- **"Have You Talked to Someone?" gate** (Phase 8): Asks if you've talked to a human before continuing on heavy topics.
- **Competence graduation** (Phase 3): Notices when you're using the same task type repeatedly and gently suggests building that skill yourself.
- **Cooldown enforcement**: Blocks sessions after 7+ sessions/day, 120+ minutes/day, or dependency score >= 8.

### Human Connection
- **Trusted network management** (Phase 5): Add your real humans. Domain-specific suggestions for who to talk to.
- **Context-aware handoff templates**: Pre-written messages for reaching out — "need to talk", "reconnecting", "hard conversation", "asking for help". Auto-suggested based on session content.
- **Connection building** (Phase 12): For users with empty networks — signpost categories (community groups, volunteering, support groups, classes) and first-contact templates for initiating new connections.
- **Handoff tracking**: "Did you reach out?" → "How did it go?" with success metrics.

### Transparency & Tracking
- **Decision transparency panel** (Phase 6): "Why this response?" shows domain detected, mode, word limit, policy actions.
- **Session summaries** with JSON export.
- **"My Patterns" dashboard** (Phase 7): Sensitive topics ↓ = good. Human reach-outs ↑ = good. Practical tasks = neutral.
- **Policy event logging**: Every safety decision is recorded with reasons.

### Context & Intelligence
- **Context persistence** (Phase 6.5): System maintains emotional context across turns. "Caught my boyfriend cheating" → "let's brainstorm" still gets appropriate handling.
- **Topic threading**: Detects continuation messages via pronouns, affirmatives, topic hints.
- **Context decay**: High-weight context persists 5-7 turns, then fades naturally.
- **Emotional weight awareness** (Phase 2): Recognizes heavy practical tasks (resignation emails, apologies, condolences) and adds brief human acknowledgment.
- **Session intent check-in** (Phase 4): "What brings you here?" with connection-seeking detection.

### Data & Persistence
- **Local-first**: All data stored on your machine. No external API calls, no telemetry.
- **Atomic JSON writes** (Phase 11): Write to temp file → fsync → atomic rename. No data corruption on crash.
- **Optional SQLite backend**: WAL mode, full transactions, schema migrations. Enable with `USE_SQLITE=true`.
- **Multi-device sync safety** (Phase 11): Heartbeat-based lock file prevents data conflicts. Write gate blocks all mutations when another device has the lock.
- **Schema versioning**: Automatic migration on load.

### Distribution
- **One-command setup**: `bash install.sh` — checks Python, creates venv, installs deps, configures .env, verifies Ollama.
- **pip install**: `pip install -e ".[dev]"` with `empathysync` CLI entry point.
- **Docker Compose**: `docker compose up` starts both empathySync and Ollama together.
- **Startup health checks** (Phase 13): Validates Ollama connectivity, model availability, data directory, SQLite — with actionable error messages.

### Known Limitations
- Requires Ollama running locally (no cloud LLM support by design).
- Classification quality depends on the local model — larger models give better results.
- Single-user design. No multi-user or authentication system.

### Requirements
- Python 3.9+
- [Ollama](https://ollama.com/) with a downloaded model
- 8GB RAM recommended (4GB minimum)

---

*"We optimize exits, not engagement."*
