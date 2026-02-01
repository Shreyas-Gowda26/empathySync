<div align="center">

<img src="assets/logo.png" alt="empathySync logo" width="180" style="border-radius: 50%;"/>

# empathySync

**Help that knows when to stop.**

*Most chatbots want you to keep talking.*
*This one wants you to leave and go live your life.*

[![v0.9-beta](https://img.shields.io/badge/release-v0.9--beta-orange.svg)](https://github.com/Olawoyin007/empathySync/releases/tag/v0.9-beta)
[![CI](https://github.com/Olawoyin007/empathySync/actions/workflows/ci.yml/badge.svg)](https://github.com/Olawoyin007/empathySync/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Local-First](https://img.shields.io/badge/Privacy-Local--First-blue.svg)](#)

</div>

## What It Is

An open-source, local-first AI assistant that provides full help for practical tasks but applies restraint on sensitive topics. Everything runs on your machine via Ollama, no cloud APIs, no data harvesting, no telemetry.

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
empathysync
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
- **Streamlit UI**: Clean, simple interface
- **YAML-Driven**: All prompts, rules, and thresholds configurable
- **LLM Classification**: Optional intelligent classification for nuanced context detection

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

**Core Complete.** 14 phases shipped — safety systems, dual-mode operation, dependency tracking, human handoff, transparency, LLM classification, persistence hardening, connection building, and startup health checks.

**Distribution Ready.** Three installation methods available: install script, pip, and Docker Compose.

**323 tests passing.**

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
