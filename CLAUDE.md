# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

empathySync is a local-first AI wellness companion that helps users develop healthier relationships with AI technology. It runs entirely on local hardware via Ollama integration - no external API calls.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run src/app.py

# Run tests
pytest tests/

# Linting and formatting
black src/
flake8 src/
mypy src/
```

## Required Environment Variables

Configure in `.env` file:
- `OLLAMA_HOST` - Ollama server URL (e.g., `http://localhost:11434`)
- `OLLAMA_MODEL` - Model name to use (e.g., `llama2`)
- `OLLAMA_TEMPERATURE` - Temperature for responses (default: 0.7)

Optional database settings (PostgreSQL): `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

## Architecture

### Core Components

**Entry Point**: [src/app.py](src/app.py) - Streamlit application with chat interface and wellness sidebar

**Models**:
- [src/models/ai_wellness_guide.py](src/models/ai_wellness_guide.py) - `WellnessGuide` class: main conversation engine that calls Ollama API, builds context from history, and processes responses with safety checks
- [src/models/risk_classifier.py](src/models/risk_classifier.py) - `RiskClassifier` class: detects conversation domain (money, health, relationships, spirituality, crisis), measures emotional intensity, and assesses dependency risk

**Prompts**:
- [src/prompts/wellness_prompts.py](src/prompts/wellness_prompts.py) - `WellnessPrompts` class: system prompts for three conversation modes (Gentle, Direct, Balanced)

**Utils**:
- [src/utils/wellness_tracker.py](src/utils/wellness_tracker.py) - `WellnessTracker` class: local JSON storage for daily check-ins and usage sessions in `data/wellness_data.json`
- [src/utils/helpers.py](src/utils/helpers.py) - Logging setup and environment validation

**Config**:
- [src/config/settings.py](src/config/settings.py) - `Settings` class: environment-based configuration with validation

### Data Flow

1. User input received in Streamlit chat
2. `WellnessGuide.generate_response()` called with input, wellness mode, and conversation history
3. `RiskClassifier.classify()` assesses domain and risk (logged, not surfaced to user in current phase)
4. System prompt selected based on wellness mode (Gentle/Direct/Balanced)
5. Context built from last 10 messages (limited to 200 chars each)
6. Ollama API called locally
7. Response safety-checked via `_contains_harmful_content()` before display

### Key Design Constraints (from MANIFESTO.md)

- All processing must remain local - no external API calls
- No telemetry, engagement metrics, or behavior tracking
- User data belongs to the user - stored only in local JSON files
- Features must center human wellbeing and psychological safety
- Reject any feature that enables manipulation or exploits user vulnerability
