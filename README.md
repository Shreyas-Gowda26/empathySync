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
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-yellow.svg)](https://buymeacoffee.com/olawoyin007)

</div>

<!-- Screenshot: place image in assets/ and uncomment the line below once available -->
<!-- ![empathySync interface showing the transparency panel](assets/screenshot.png) -->

## What It Is

empathySync is a local-first AI assistant - full help for practical tasks, deliberate restraint on personal ones. Everything runs on your hardware via Ollama. No cloud APIs, no data harvesting, no telemetry.

Your inner life deserves something that knows the difference.

## The Belief Behind It

Every person should have the right to an AI system that is entirely their own. Not rented. Not monitored. Not optimised for someone else's engagement metrics. Yours - running on your hardware, answering only to you, storing nothing it doesn't need to.

For sensitive, personal things - how you're feeling, your relationships, your health, your money - you deserve something local, private, and restrained. For complex tasks that need serious compute, use the cloud AIs. That's a reasonable division.

But the part of AI that touches your inner life should belong to you.

This isn't a feature. It's the point.

## Who Is This For?

If you're a **developer** who wants a privacy-respecting AI assistant with no API keys, no subscriptions, and no data leaving your hardware - this is for you.

If you're building **ethical AI tooling** and want a reference implementation that optimises for user autonomy rather than engagement, the architecture is fully documented and embeddable.

If you're a **therapist, counsellor, or domain expert** who wants to shape how an AI responds to emotional content - see [HELP-SHAPE-THIS.md](HELP-SHAPE-THIS.md).

empathySync is **not** for people who want a companion AI or always-on assistant. It's for people who want useful help that doesn't try to become a habit.

## The Philosophy

We optimise for exit, not engagement.

| Practical Tasks | Sensitive Topics |
|-----------------|------------------|
| Writing emails, coding, explanations | Emotional, health, financial, relationships |
| Full assistance, no limits | Brief responses, redirects to humans |
| Complete the task thoroughly | Encourage human connection |

## What Makes It Different

### Safety & restraint

- **Crisis detection**: immediate redirect to professional resources, no exceptions
- **Post-crisis protection**: never apologises for safety interventions

### Awareness & honesty

- **Tracks dependency patterns** and warns you if you're relying on it too much
- **Transparency panel** showing exactly why it responded the way it did
- **Anti-engagement metrics**: fewer sensitive sessions = success

### Human connection

- **Suggests real humans** to talk to, and helps you find them if you don't have anyone yet

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
> `docker exec empathysync-ollama ollama pull llama3.2`
>
> **Model choice matters here.** empathySync's restraint behaviour depends on the model understanding nuance - llama3.2 or mistral:7b are recommended minimums. Older models like llama2 will produce noticeably weaker classification and responses.

### Requirements

- Python 3.9+
- [Ollama](https://ollama.com/) running locally (or via Docker)
- 8GB RAM recommended (4GB minimum)
- GPU optional but improves response time

**Lower-spec machine?** Smaller models like `qwen2.5:3b` or `tinyllama` run comfortably on 4GB RAM. Classification quality trades off slightly, but the safety pipeline remains intact. You can also set a separate smaller model just for classification via `OLLAMA_CLASSIFIER_MODEL` in your `.env`.

## How It Works

**It reads the room.** Every message is classified before a response is generated - is this practical or personal? Heavy or light? A task or a feeling? The response changes accordingly.

**It watches for patterns.** If you're coming back too often, or asking the same things repeatedly, it notices. It says something. It won't pretend that's fine.

**It keeps a door open to real people.** You can build a list of people in your life to reach out to, with templates for hard conversations. No network yet? It helps you think about where to find one.

**It steps aside in a crisis.** When it detects crisis content, it redirects immediately to professional resources. It never engages. It never apologises for that.

**It shows its reasoning.** Every response comes with a transparency panel explaining what it classified, what it decided, and why.

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
OLLAMA_MODEL=llama3.2
OLLAMA_TEMPERATURE=0.7

# Optional
LLM_CLASSIFICATION_ENABLED=true  # Intelligent context-aware classification
STORE_CONVERSATIONS=true         # Local storage only
USE_SQLITE=false                 # SQLite backend (better concurrency)
ENABLE_DEVICE_LOCK=false         # Multi-device sync safety
```

## Documentation

- [CLAUDE.md](CLAUDE.md) - Architecture and development guide
- [ROADMAP.md](ROADMAP.md) - Detailed feature implementation plan
- [MANIFESTO.md](MANIFESTO.md) - Design principles and philosophy
- [scenarios/README.md](scenarios/README.md) - Knowledge base editing guide
- [docs/](docs/) - Additional documentation

## Contributing

empathySync is shaped by more than code. Engineers build the pipeline. But whether the words actually land - whether a response to "I feel lonely" feels human or hollow - that's a different kind of knowledge.

If you're a therapist, counsellor, social worker, or UX writer, see [HELP-SHAPE-THIS.md](HELP-SHAPE-THIS.md). The responses, interventions, and connection-building guidance are plain text files. No programming required.

If you're an engineer, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Built By

[@Olawoyin007](https://github.com/Olawoyin007) - Specialist data engineer, building technology that serves human flourishing
## License

MIT License - Built for everyone's benefit and maximum accessibility.

---

*The goal isn't a better chatbot. It's a world where you need chatbots less.*
