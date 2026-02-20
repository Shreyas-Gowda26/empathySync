<div align="center">

<img src="assets/logo.png" alt="empathySync logo" width="180" style="border-radius: 50%;"/>

# empathySync

**Help that knows when to stop.**

*Most chatbots want you to keep talking.*
*This one wants you to leave and go live your life.*

[![v1.3](https://img.shields.io/badge/release-v1.3-orange.svg)](https://github.com/Olawoyin007/empathySync/releases/tag/v1.3)
[![CI](https://github.com/Olawoyin007/empathySync/actions/workflows/ci.yml/badge.svg)](https://github.com/Olawoyin007/empathySync/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Local-First](https://img.shields.io/badge/Privacy-Local--First-blue.svg)](#)

</div>

## What It Is

An open-source, local-first AI assistant that provides full help for practical tasks but applies restraint on sensitive topics. Everything runs on your machine via Ollama — no cloud APIs, no data harvesting, no telemetry.

## The Belief Behind It

Every person should have the right to an AI system that is entirely their own. Not rented. Not monitored. Not optimized for someone else's engagement metrics. Yours — running on your hardware, answering only to you, storing nothing it doesn't need to.

The AI industry is racing toward centralization. Your conversations, your emotional state, your patterns — flowing through servers you don't control, training models you'll never own, feeding dashboards you'll never see.

empathySync goes the other direction.

For sensitive, personal things — how you're feeling, your relationships, your health, your money — you deserve something local, private, and restrained. For complex tasks that need serious compute, use the cloud AIs. That's a reasonable division. But the part of AI that touches your inner life should belong to you.

This isn't a feature. It's the point.

## The Philosophy

We optimize for exit, not engagement.

| Practical Tasks | Sensitive Topics |
|-----------------|------------------|
| Writing emails, coding, explanations | Emotional, health, financial, relationships |
| Full assistance, no limits | Brief responses, redirects to humans |
| Complete the task thoroughly | Encourage human connection |

## What Makes It Different

- **Tracks dependency patterns** and warns you if you're relying on it too much
- **Suggests real humans** to talk to, and helps you find them if you don't have anyone yet
- **Crisis detection** that redirects to helplines, never engages with crisis content
- **Transparency panel** showing exactly why it responded the way it did
- **Anti-engagement metrics**: fewer sensitive sessions = success
- **Post-crisis protection**: never apologizes for safety interventions

## Quick Start

### Option 1: One-Command Setup (recommended)

```bash
git clone https://github.com/Olawoyin007/empathySync.git
cd empathySync
bash install.sh
```

The install script checks Python, creates a virtual environment, installs dependencies, configures `.env`, and verifies Ollama is ready.

Then launch:
```bash
venv/bin/python -m streamlit run src/app.py
```

### Option 2: pip install

```bash
git clone https://github.com/Olawoyin007/empathySync.git
cd empathySync
pip install -e ".[dev]"
cp .env.example .env
empathysync          # Launches Streamlit web UI
empathysync --mode cli  # Direct terminal mode
```

### Option 3: Docker

```bash
git clone https://github.com/Olawoyin007/empathySync.git
cd empathySync
cp .env.example .env
docker compose up
```

This starts both empathySync and Ollama together. Open `http://localhost:8501`.

> **Note:** You'll still need to pull a model into the Ollama container:
> `docker exec empathysync-ollama ollama pull llama2`

### Requirements

- Python 3.9+
- [Ollama](https://ollama.com/) running locally (or via Docker)
- 8GB RAM recommended (4GB minimum)
- GPU optional but improves response time

## Features

### Dual-Mode Intelligence
Full assistance for practical tasks (emails, code, explanations). Restraint on sensitive topics (relationships, finances, health, spirituality).

### Session Intent Check-In
"What brings you here?" helps calibrate responses and detects connection-seeking behavior.

### Emotional Weight Awareness
Recognizes emotionally heavy tasks (resignation emails, difficult conversations) and adds brief human acknowledgment without being therapeutic.

### Trusted Network & Connection Building
Build your list of real humans to reach out to, with pre-written templates for hard conversations. Don't have anyone yet? The "Building Your Network" guide helps you find your people — with signposts for types of places to connect (support groups, volunteering, community groups) and first-contact templates for initiating new connections.

### Dependency Detection
Monitors usage patterns across sessions. Gently intervenes when over-reliance is detected.

### My Patterns Dashboard
Track your usage, sensitive vs practical. Week-over-week comparisons. The goal: sensitive sessions going *down*.

### "What Would You Tell a Friend?"
For tough decisions, helps you access your own wisdom instead of asking AI for answers.

### Human Connection Gate
"Have you talked to someone about this?" Encourages real human contact before continuing AI conversations on sensitive topics.

### Crisis Intervention
Immediate redirect to professional resources. Never engages with crisis content. Never apologizes for intervening.

## Technical Foundation

- **Local LLM**: Runs entirely on your hardware via Ollama
- **Privacy-First**: Zero external API calls, complete data sovereignty
- **Dual Interface**: Streamlit web UI or direct CLI mode (`empathysync --mode cli`)
- **Streaming Responses**: Real-time token streaming for faster perceived response times
- **YAML-Driven**: All prompts, rules, and thresholds configurable
- **LLM Classification**: Optional intelligent classification for nuanced context detection
- **Framework-Agnostic Core**: `ConversationSession` class can be embedded in any Python project

## Configuration

See `.env.example` for all configuration options:

```bash
# Required
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TEMPERATURE=0.7

# Optional
LLM_CLASSIFICATION_ENABLED=true  # Intelligent context-aware classification
STORE_CONVERSATIONS=true         # Local storage only
USE_SQLITE=false                 # SQLite backend (better concurrency)
ENABLE_DEVICE_LOCK=false         # Multi-device sync safety
```

## Project Status

**v1.3 — Hardening Release.** 16 phases + 6 hardening sub-phases shipped. Safety systems, dual-mode operation, dependency tracking, human handoff, transparency, LLM classification, persistence hardening, connection building, core decoupling, streaming, httpx migration, god class decomposition, security hardening, and centralized configuration.

**Distribution Ready.** Three installation methods plus CLI mode.

**443 tests passing** across Python 3.9, 3.10, 3.11, 3.12.

See [ROADMAP.md](ROADMAP.md) for detailed implementation status.

## Documentation

- [CLAUDE.md](CLAUDE.md) - Architecture and development guide
- [ROADMAP.md](ROADMAP.md) - Detailed feature implementation plan
- [MANIFESTO.md](MANIFESTO.md) - Design principles and philosophy
- [scenarios/README.md](scenarios/README.md) - Knowledge base editing guide
- [docs/](docs/) - Additional documentation

## Contributing

We welcome contributions from developers who care about digital wellness and ethical AI. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - Built for everyone's benefit and maximum accessibility.

---

*Building technology that serves human flourishing.*

*The goal isn't a better chatbot. It's a world where you need chatbots less.*
