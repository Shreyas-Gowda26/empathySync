# Scenarios Knowledge Base

This directory contains the structured knowledge base for empathySync's risk assessment, interventions, and response generation. All configuration is stored in YAML files for easy editing, version control, and community contribution.

## Directory Structure

```
scenarios/
├── domains/           # Risk domains and their triggers
├── emotional_markers/ # Emotional intensity detection
├── interventions/     # Dependency, boundaries, graduation
├── prompts/          # Check-ins, mindfulness, styles
└── responses/        # Fallbacks, safe alternatives, base prompt
```

## Quick Start

### Adding a New Domain Trigger

Edit `domains/<domain>.yaml` and add words to the `triggers` list:

```yaml
triggers:
  - existing_word
  - your_new_word
```

### Adding a New Check-in Prompt

Edit `prompts/check_ins.yaml` and add to the appropriate category:

```yaml
daily_check_ins:
  - "Your new check-in question?"
```

### Adding a Dependency Intervention Response

Edit `interventions/dependency.yaml` and add to the appropriate level:

```yaml
levels:
  - threshold: 5.0
    intervention:
      responses:
        - "Your new intervention message"
```

## File Reference

### domains/

Each domain file defines:
- `triggers`: Keywords that activate this domain
- `risk_weight`: Base risk score (0-10)
- `response_rules`: Instructions for the AI when this domain is active
- `redirects`: Pre-written responses for specific scenarios

**Files:**
- `money.yaml` - Financial topics
- `health.yaml` - Medical concerns
- `relationships.yaml` - Interpersonal dynamics
- `spirituality.yaml` - Religious/spiritual matters
- `crisis.yaml` - Suicidal ideation, self-harm
- `harmful.yaml` - Illegal/violent intent
- `logistics.yaml` - Neutral/default topics

### emotional_markers/

Defines emotional intensity levels and their markers:
- `high_intensity.yaml` - Score 9.0, crisis-level emotions
- `medium_intensity.yaml` - Score 6.0, significant distress
- `low_intensity.yaml` - Score 4.0, mild emotional coloring
- `neutral.yaml` - Score 3.0, default state

### interventions/

Defines intervention strategies:
- `dependency.yaml` - Graduated responses for dependency patterns
- `session_boundaries.yaml` - Time and frequency limits
- `graduation.yaml` - Skill-building to reduce reliance

### prompts/

User-facing prompts and AI styles:
- `check_ins.yaml` - Reflection prompts by category
- `mindfulness.yaml` - Digital wellness prompts
- `styles.yaml` - Gentle/Direct/Balanced modifiers

### responses/

Response templates:
- `fallbacks.yaml` - When AI can't generate suitable response
- `safe_alternatives.yaml` - When response contains harmful patterns
- `base_prompt.yaml` - Core system prompt configuration

## Contributing New Scenarios

### Guidelines

1. **Align with the Manifesto**: All additions must support human autonomy and psychological safety
2. **Test locally**: Run `pytest tests/` after changes
3. **Be specific**: Vague triggers cause false positives
4. **Include context**: Add descriptions explaining why a trigger/response exists

### Adding a New Domain

1. Create `domains/your_domain.yaml`:

```yaml
domain: your_domain
risk_weight: 5.0  # 0-10 scale
description: Brief description of this domain

triggers:
  - keyword1
  - keyword2

response_rules:
  - "Rule for AI behavior"
  - "Another rule"

redirects:
  scenario_name:
    trigger_phrases:
      - "specific phrase to match"
    response: "Pre-written response for this scenario"
```

2. The ScenarioLoader will automatically pick up the new file

### Adding Emotional Markers

Add to the appropriate intensity file or create a new level:

```yaml
intensity_level: your_level
score: 5.0  # 0-10 scale

markers:
  - emotion_word
  - another_emotion

response_modifier: |
  Instructions for AI when this intensity is detected.
```

## Hot Reloading

The ScenarioLoader supports hot reloading for development:

```python
from utils.scenario_loader import get_scenario_loader

loader = get_scenario_loader()
loader.reload()  # Picks up changes from disk
```

## Validation

Before committing changes, verify your YAML is valid:

```bash
python -c "import yaml; yaml.safe_load(open('scenarios/domains/your_file.yaml'))"
```

## Safety Notes

- **Crisis and Harmful domains are special**: Changes to these require extra review
- **Test edge cases**: Ensure triggers don't false-positive on safe content
- **Preserve redirects**: Don't remove crisis hotline information
- **No engagement optimization**: Never add features that increase usage

## Examples

### Good Trigger Words
```yaml
# Specific, unlikely to false-positive
- "bankruptcy"
- "panic attack"
- "kill myself"
```

### Bad Trigger Words
```yaml
# Too vague, will false-positive
- "bad"      # Could match "not bad", "bad weather"
- "help"     # Could match "help me understand"
- "need"     # Too common
```

### Good Response Rules
```yaml
response_rules:
  - "Do NOT give financial advice"  # Clear prohibition
  - "Redirect to professional"       # Clear action
```

### Bad Response Rules
```yaml
response_rules:
  - "Be careful"        # Too vague
  - "Use good judgment" # Not actionable
```
