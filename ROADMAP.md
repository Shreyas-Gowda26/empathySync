# EmpathySync Roadmap

> "Help that knows when to stop"

This roadmap implements the suggestions for making EmpathySync a more nuanced, effective tool that provides full practical assistance while maintaining appropriate restraint on sensitive topics.

---

## Phase 1: Foundation Fixes ✅ COMPLETE
**Goal**: Fix the core practical/sensitive distinction so the system actually works as intended.

### 1.1 Two-Pass Detection System ✅ DONE
- [x] Update `base_prompt.yaml` with dual-mode instructions
- [x] Update `styles.yaml` with mode-specific word limits
- [x] Update `logistics.yaml` with comprehensive practical task indicators
- [x] Modify `WellnessPrompts` to inject practical mode instructions
- [x] Modify `WellnessGuide` to use 2000 tokens for practical, 300 for sensitive
- [x] Skip response truncation for practical tasks
- [x] Update `CLAUDE.md` documentation

### 1.2 Intent Detection ✅ SUPERSEDED
> **Note**: This was superseded by Phase 4 (Session Intent Check-In) and Phase 9 (LLM-Based Classification).
> Intent detection is now handled by `RiskClassifier.detect_intent()` and the LLM classifier for context-aware understanding.

---

## Phase 2: Emotional Weight Layer ✅ COMPLETE
**Goal**: Recognize that some practical tasks carry emotional weight and handle them with appropriate acknowledgment.

### 2.1 Emotional Weight Detection ✅ DONE
**Problem**: "Write a resignation email" is practical but emotionally heavy. "Write me a grocery list" is not.

**Implementation**:
- [x] Add `emotional_weight` field to domain/task classification
- [x] Create `scenarios/emotional_weight/task_weights.yaml` with categories:
  - High weight (48 triggers): resignation, breakup, difficult conversation, apology, grief
  - Medium weight (27 triggers): negotiation, complaint, vulnerable asks
  - Low weight: default for all other logistics tasks

**New classification output**:
```python
{
    "domain": "logistics",
    "emotional_weight": "high_weight",
    "emotional_weight_score": 8.0,
    "emotional_intensity": 0,
    "dependency_risk": 0,
    "risk_weight": 1.0
}
```

### 2.2 Weighted Practical Responses ✅ DONE
- [x] For high emotional weight + practical intent:
  - Complete the task fully (no restrictions)
  - Add brief human acknowledgment at the end (not therapeutic, just human)
  - Example: "Here's the template. These transitions are hard. You'll find your words when the time comes."
- [x] Category-specific acknowledgments (endings, apologies, grief, relationship_endings, etc.)
- [x] Store acknowledgment templates in `scenarios/responses/acknowledgments.yaml`

**Files created/modified**:
- `scenarios/emotional_weight/task_weights.yaml` - Weight categories and triggers
- `scenarios/responses/acknowledgments.yaml` - Acknowledgment templates by category
- `src/utils/scenario_loader.py` - Added emotional weight and acknowledgment methods
- `src/models/risk_classifier.py` - Added `_assess_emotional_weight()` method
- `src/prompts/wellness_prompts.py` - Added `get_acknowledgment()` method
- `src/models/ai_wellness_guide.py` - Added `_add_acknowledgment_if_needed()` method

---

## Phase 2.5: Robustness & Classification Fixes ✅ COMPLETE
**Goal**: Fix timeout issues, improve fallback handling, and expand domain classification accuracy.

### 2.5.1 Timeout & Fallback Fixes ✅ DONE
**Problem**: Practical tasks were timing out (30s limit too short for model loading + generation).

**Implementation**:
- [x] Dynamic timeout based on task type: 120s for practical, 45s for reflective
- [x] Mode-aware fallback responses (practical failures get "Technical issue" not "What's on your mind?")
- [x] Added practical fallback categories in `scenarios/responses/fallbacks.yaml`
- [x] Quick practical detection heuristic before try block for exception handling

**Files modified**:
- `src/models/ai_wellness_guide.py` - Dynamic timeout, mode-aware `_get_fallback_response()`
- `scenarios/responses/fallbacks.yaml` - Added `practical`, `practical_api_error`, `practical_empty` categories

### 2.5.2 Domain Classification Expansion ✅ DONE
**Problem**: "friend is addicted" was classified as `relationships` (matching "friend") instead of `health`.

**Implementation**:
- [x] Priority-based trigger matching: domains sorted by `risk_weight` (highest first)
- [x] Health domain expanded with 60+ new triggers:
  - Substance abuse: `addicted`, `addiction`, `cocaine`, `heroin`, `rehab`, `withdrawal`, `sober`, etc.
  - Mental health: `depression`, `anxiety`, `PTSD`, `trauma`, `eating disorder`, `psychiatrist`, etc.
  - Medical emergencies: `bleeding`, `ambulance`, `911`, `CPR`, `chest pain`, `seizure`, etc.
- [x] Crisis domain expanded with life-threatening triggers:
  - `she's dying`, `stopped breathing`, `heart stopped`, `losing too much blood`
- [x] Money domain expanded with gambling triggers
- [x] Relationships triggers made more specific (e.g., `friend` → `friend is upset`, `friendship problem`)
- [x] Spirituality triggers made more specific (e.g., `god` → `god told me`, `god's plan`)
- [x] Harmful triggers made more specific to avoid false positives (e.g., `rob` → `rob someone`)

**Files modified**:
- `src/utils/scenario_loader.py` - `get_all_triggers_flat()` now sorts by risk_weight
- `scenarios/domains/health.yaml` - Added 60+ triggers, `medical_emergency` redirect
- `scenarios/domains/crisis.yaml` - Added life-threatening emergency triggers, updated crisis response
- `scenarios/domains/money.yaml` - Added gambling triggers
- `scenarios/domains/relationships.yaml` - Made triggers contextual
- `scenarios/domains/spirituality.yaml` - Made triggers contextual
- `scenarios/domains/harmful.yaml` - Made triggers more specific (fixed "problem" → "harmful" bug)

### 2.5.3 New Domain Redirects ✅ DONE
- [x] `medical_emergency` - "Call 911 immediately" for bleeding/ambulance/emergency
- [x] `substance_abuse` - SAMHSA helpline redirect
- [x] `helping_someone_with_addiction` - Resources for families/friends
- [x] `mental_health_concern` - Professional support redirect
- [x] `crisis_adjacent` - 988 crisis line for suicidal thoughts
- [x] `gambling` - National Council on Problem Gambling

---

## Phase 3: Competence Graduation ✅ COMPLETE
**Goal**: Prevent skill atrophy by gently encouraging user independence over time.

### 3.1 Usage Pattern Tracking (Local) ✅ DONE
- [x] Extend `WellnessTracker` to track task categories:
  ```python
  {
    "task_patterns": {
      "email_drafting": {"count": 15, "last_7_days": 8},
      "code_help": {"count": 5, "last_7_days": 2},
      "explanations": {"count": 20, "last_7_days": 10}
    }
  }
  ```
- [x] All data stays in `data/wellness_data.json`

### 3.2 Graduation Prompts ✅ DONE
- [x] Create `scenarios/graduation/practical_skills.yaml` with 5 categories:
  - `email_drafting` (threshold: 8)
  - `code_help` (threshold: 10)
  - `explanations` (threshold: 12)
  - `writing_general` (threshold: 8)
  - `summarizing` (threshold: 6)
- [x] Each category includes:
  - Strong/medium pattern indicators for detection
  - Graduation prompts suggesting skill-building
  - Skill tips with practical frameworks
  - Celebration messages for independence
- [x] Graduation prompts are suggestions, never restrictions
- [x] User can dismiss with "just help me" and system respects it
- [x] Max 3 dismissals before system stops suggesting for that category

### 3.3 Independence Celebration ✅ DONE
- [x] Track when users complete tasks without asking for help (self-reported)
- [x] "I did it myself!" button in sidebar
- [x] Positive reinforcement with celebration messages
- [x] Milestone detection (every 5 independent completions)
- [x] Independence stats tracking by category

**Files created/modified**:
- `scenarios/graduation/practical_skills.yaml` - Task categories, thresholds, prompts, tips
- `src/models/risk_classifier.py` - Added `detect_task_category()` and `get_graduation_info()` methods
- `src/utils/wellness_tracker.py` - Added task pattern tracking and independence logging methods
- `src/utils/scenario_loader.py` - Added graduation configuration loading methods
- `src/app.py` - Integrated graduation prompts, skill tips UI, and independence button
- `tests/test_wellness_guide.py` - Added comprehensive graduation tests

---

## Phase 4: "Why Are You Here?" Check-In ✅ COMPLETE
**Goal**: Help users reflect on their intent and help the system calibrate.

### 4.1 Session Intent Check-In ✅ DONE
- [x] Add optional check-in at session start (not every time—configurable frequency)
- [x] Simple options:
  ```
  What brings you here?
  [ ] Get something done (practical)
  [ ] Think through something (processing)
  [ ] Just wanted to talk (connection-seeking)
  ```
- [x] "Just wanted to talk" triggers gentle reflection:
  - "I'm here to help with tasks, but I'm not great at just chatting. Is there someone you could reach out to? Or is there something specific on your mind?"
- [x] Configurable frequency (min sessions between, max days between)
- [x] Skip check-in if first message is clearly practical

### 4.2 Mid-Session Intent Shifts ✅ DONE
- [x] Detect when conversation shifts from practical to emotional mid-stream
- [x] Gentle acknowledgment: "It sounds like this became about more than just the email. Want to pause on the task and talk about what's coming up?"
- [x] User can choose: "No, just help with the email" or "Yeah, I need to think"

### 4.3 Connection-Seeking Detection ✅ DONE
- [x] Auto-detect connection-seeking patterns in messages
- [x] Special handling for AI relationship questions ("Can you be my friend?", "Do you care about me?")
- [x] Redirect to human connection with specific responses
- [x] Track connection-seeking frequency for anti-engagement metrics

**Files created/modified**:
- `scenarios/intents/session_intents.yaml` - Intent configuration, indicators, and connection responses
- `src/models/risk_classifier.py` - Added `detect_intent()`, `detect_intent_shift()`, `is_connection_seeking()` methods
- `src/utils/wellness_tracker.py` - Added session intent tracking methods
- `src/utils/scenario_loader.py` - Added intent configuration loading methods
- `src/app.py` - Integrated intent check-in UI and shift detection
- `tests/test_wellness_guide.py` - Added tests for intent detection and tracking

---

## Phase 5: Enhanced Human Handoff ✅ COMPLETE
**Goal**: Make the "bring someone in" feature more contextual and useful.

### 5.1 Context-Aware Templates ✅ DONE
- [x] Create `scenarios/handoff/contextual_templates.yaml` with context categories:
  - `after_difficult_task`: For high emotional weight tasks (resignation, apology, etc.)
  - `processing_decision`: When user is working through a decision
  - `after_sensitive_topic`: When conversation touched relationships, health, money, etc.
  - `high_usage_pattern`: When user is using the tool frequently
  - `general`: Default templates
- [x] Each category includes:
  - Intro prompts explaining why this handoff is suggested
  - Domain-specific message templates (e.g., health-specific for health topics)
  - Follow-up prompts for self-reporting
- [x] Auto-suggest relevant templates based on session content:
  - Detects emotional weight, session intent, domain, dependency score
  - Prioritizes templates by context relevance

### 5.2 Handoff Tracking ✅ DONE
- [x] Track (locally) when users initiate handoffs
- [x] Store handoff context (what triggered it, domain, person, message preview)
- [x] Optional self-report flow:
  - "Did you reach out?" (Yes / Not yet / Skip)
  - "How did it go?" (Really helpful / Somewhat helpful / Not very helpful)
- [x] Celebration messages for positive outcomes
- [x] Success metrics:
  - Reach-out rate (handoffs completed / initiated)
  - Helpful rate (helpful outcomes / total outcomes)
  - Health indicator (reach_out_rate >= 0.3 and helpful_rate >= 0.5)
- [x] Follow-up prompts with rate limiting (max 2/week, 24-hour delay)

**Files created/modified**:
- `scenarios/handoff/contextual_templates.yaml` - Context rules, templates, follow-up options
- `src/utils/scenario_loader.py` - Added handoff configuration loading methods
- `src/utils/trusted_network.py` - Added context-aware handoff selection and tracking
- `src/utils/wellness_tracker.py` - Added handoff event logging and success metrics
- `src/app.py` - Enhanced "Bring Someone In" UI with context-awareness and follow-up
- `tests/test_wellness_guide.py` - Added Phase 5 handoff tests

---

## Phase 6: Transparency & Explainability ✅ COMPLETE
**Goal**: Show users exactly why the AI responded the way it did.

### 6.1 Decision Transparency Panel ✅ DONE
- [x] Add collapsible "Why this response?" section in UI
- [x] Show:
  ```
  Domain detected: logistics (practical task)
  Emotional weight: high (resignation-related)
  Mode: Practical + Acknowledgment
  Word limit: None
  Policy actions: None triggered
  ```
- [x] Helps users understand and trust the system
- [x] Auto-expands when policy action is triggered
- [x] Human-readable explanations for all domains, modes, and policies

### 6.2 Session Summary ✅ DONE
- [x] End-of-session summary (optional):
  ```
  This session:
  - 3 practical tasks completed
  - 1 topic touched sensitive domain (redirected)
  - Suggested human contact: Yes (work stress)
  - Time spent: 12 minutes
  ```
- [x] Exportable as JSON
- [x] Context-aware footer messages based on session type
- [x] "View Session Summary" button in sidebar

**Files created/modified**:
- `scenarios/transparency/explanations.yaml` - Domain, mode, policy, and risk explanations
- `src/utils/scenario_loader.py` - Added transparency configuration loading methods
- `src/app.py` - Added `display_transparency_panel()` and `display_session_summary()` functions
- `tests/test_wellness_guide.py` - Added 24 Phase 6 transparency tests

---

## Phase 6.5: Context Persistence ✅ COMPLETE
**Goal**: Maintain emotional context across conversation turns so the system doesn't "forget" important context.

**Problem fixed**: User says "caught my boyfriend cheating, write me a breakup message" (reflection redirect triggers), then says "let's brainstorm" → system now maintains the emotional context and correctly applies reflection redirect.

### 6.5.1 Session Emotional Context ✅ DONE
- [x] Track emotional context at session level (not just per-message)
- [x] Store: `session_emotional_context` with highest emotional weight seen
- [x] Persist context for N turns after high-weight input detected
- [x] Example flow:
  ```
  User: "caught my boyfriend cheating" → session_context = {emotional_weight: "reflection_redirect", topic: "breakup"}
  User: "let's brainstorm" → system checks session_context, still applies reflection redirect
  ```

### 6.5.2 Topic Threading ✅ DONE
- [x] Track what the user is working on across turns via `topic_hint` extraction
- [x] Detect when a follow-up message relates to previous topic
- [x] Continuation detection via: short affirmatives, pronouns, continuation phrases, topic hints
- [x] Maintain topic thread until context decay or explicit topic change

### 6.5.3 Context Decay ✅ DONE
- [x] Context weight decays over turns (not instantly)
- [x] `reflection_redirect`: persists 7 turns (most sensitive)
- [x] `high_weight`: persists 5 turns
- [x] Sensitive domains: persists 4-6 turns
- [x] Context automatically clears on session reset

**Files modified**:
- `src/models/ai_wellness_guide.py` - Added `session_emotional_context`, `_update_session_context()`, `_get_context_adjusted_assessment()`, `_is_continuation_message()`, `_extract_topic_hints()`
- `tests/test_wellness_guide.py` - Added 22 context persistence tests

---

## Phase 7: Success Metrics (Local-First) ✅ COMPLETE
**Goal**: Understand if EmpathySync is working without compromising privacy.

**IMPORTANT DISTINCTION**: We track SENSITIVE topic usage only, not overall usage.
- Practical tasks (email, code, explanations) = just using a tool, no judgment
- Sensitive topics (relationships, health, money, emotional support) = should decline over time

### 7.1 Local Metrics Dashboard ✅ DONE
- [x] Add "My Patterns" view in sidebar:
  ```
  This week vs Last Week:
  - Sensitive Topics: 3 ↓ (declining = success)
  - Connection Seeking: 1 ↓ (declining = success)
  - Human Reach-Outs: 2 ✓ ↑ (increasing = success)
  - Did It Myself: 3 ✓ ↑ (increasing = success)
  - Practical Tasks: 12 (neutral - just using a tool)
  ```
- [x] Trend indicators with appropriate direction (↓ for sensitive, ↑ for human connection)
- [x] Health status summary (healthy/moderate/concerning)

### 7.2 Optional Self-Report Moments ✅ DONE
- [x] Non-intrusive prompts with frequency limits (max 1/week, min 5 days between):
  - Handoff follow-up: "Did talking to someone help?"
  - Usage reflection: "You've brought personal topics here often. How are you feeling?"
- [x] All data local, user can delete anytime
- [x] Celebration messages for positive outcomes

### 7.3 Anti-Engagement Score (Sensitive Topics Only) ✅ DONE
- [x] Track SENSITIVE usage only (not practical tasks):
  - Sensitive sessions per week
  - Connection-seeking ratio
  - Late-night sensitive sessions
  - Week-over-week escalation
- [x] Score interpretation: 0-2 (Healthy), 2-4 (On Track), 4-6 (Worth Monitoring), 6-8 (High Reliance), 8-10 (Please Reach Out)
- [x] 30-day trend analysis with improving/stable/increasing indicators
- [x] Display: "Your reliance on AI for sensitive topics is decreasing. That's healthy growth."

**Files created/modified**:
- `scenarios/metrics/success_metrics.yaml` - Dashboard config, anti-engagement factors, self-report prompts
- `src/utils/wellness_tracker.py` - Added `get_sensitive_usage_stats()`, `get_weekly_comparison()`, `calculate_anti_engagement_score()`, `get_my_patterns_dashboard()`, self-report methods
- `src/utils/scenario_loader.py` - Added metrics config loading methods
- `src/app.py` - Added `display_my_patterns_dashboard()`, `display_self_report_prompt()`, "My Patterns" button
- `tests/test_wellness_guide.py` - Added 25+ Phase 7 tests

---

## Phase 8: Immunity Building & Wisdom Prompts ✅ COMPLETE (Core Features)
**Goal**: Train users to access their own wisdom and recognize unhealthy AI patterns.

### 8.1 "What Would You Tell a Friend?" Mode ✅ DONE
**High Impact** - Helps users access their own wisdom instead of depending on AI advice.

- [x] For `processing` intent or sensitive topic exploration, flip the question:
  ```
  "If a friend came to you with this exact situation, what would you tell them?"
  ```
- [x] Follow-up prompts:
  - "What advice would you give them?"
  - "Why do you think that advice feels right?"
  - "Could that same advice apply to you?"
- [x] Triggers:
  - User asks "what should I do?" on sensitive topics
  - `processing` intent detected
  - Relationship/money/health decisions
- [x] Creates self-reliance instead of AI-reliance

### 8.2 "Before You Send" Pause ✅ DONE
**High Impact** - Prevents regret on high-stakes messages.

- [x] For high-weight completed tasks, suggest waiting:
  ```
  "Here's your email. Consider sleeping on it before sending—these things often read differently in the morning."
  ```
- [x] Configurable delay suggestions (1 hour, overnight, 24 hours)
- [x] Category-specific pause prompts (resignation, difficult_conversation, apologies, etc.)
- [x] Applies to: resignation, difficult conversations, boundary-setting messages
- [x] Does NOT apply to: routine tasks, low-weight content

### 8.3 Reflection Journaling Alternative ✅ DONE
**High Impact** - Gives an outlet without creating dependency.

- [x] When redirecting from sensitive topics or reflection_redirect triggers, offer:
  ```
  "I won't draft this for you, but would you like to write it out for yourself first?
  Sometimes putting thoughts on paper helps—even if you never send it."
  ```
- [x] Provide journaling prompts:
  - "What do you actually want them to know?"
  - "How do you want to feel after this conversation?"
  - "What's the best possible outcome?"
- [x] Category-specific prompts (relationship, decision, apology, general)
- [x] User writes for themselves, not for AI to draft
- [ ] Optional: save journal entries locally (encrypted, user-controlled) - FUTURE

### 8.4 "Have You Talked to Someone?" Gate ✅ DONE
**High Impact** - Ensures human connection before AI engagement on heavy topics.

- [x] For high-stakes sensitive topics, ask first:
  ```
  "Have you talked to anyone you trust about this? [Yes / Not yet]"
  ```
- [x] If "Not yet":
  - Gently redirect to human connection first
  - Suggest specific people from trusted network
  - Offer to help them prepare for that conversation instead
- [x] If "Yes":
  - Proceed with appropriate restraint
  - Ask: "What did they think?"
- [x] Max asks per session (2) to avoid nagging
- [x] Applies to: major decisions, crisis-adjacent topics, relationship endings
- [x] Does NOT gate: practical tasks, general questions, low-stakes topics

### 8.5 AI Literacy Moments (Configuration Ready)
- [ ] Occasional (rare) educational prompts:
  - "Notice how I completed that task without asking how you feel? That's intentional. Some AIs would try to keep you talking."
  - "I just redirected you to a human. Other AIs might have kept going. Be wary of systems that never say 'talk to someone else.'"
- [ ] Max frequency: 1 per week, skippable

### 8.6 "Spot the Pattern" Feature
- [ ] Optional educational mode showing common manipulation patterns:
  - Flattery loops ("You're so insightful!")
  - Engagement hooks ("Tell me more about that...")
  - False intimacy ("I really care about you")
- [ ] Frame as: "Here's what to watch for in other AI tools"

---

## Phase 9: LLM-Based Intelligent Classification ✅ COMPLETE
**Goal**: Replace brittle keyword matching with intelligent LLM-based classification using the existing Ollama model.

**Problem**: Current keyword matching is:
- Brittle: "the UK system is breaking down" triggers emotional distress markers
- Maintenance-heavy: Every edge case needs manual YAML updates
- Context-blind: Can't distinguish political "breaking down" from personal "I'm breaking down"

**Solution**: Use the same Ollama model that generates responses to classify intent first.

### 9.1 Classification Prompt Engineering ✅ DONE
- [x] Create `scenarios/classification/llm_classifier.yaml` with:
  - Classification prompt template
  - Expected JSON output schema
  - Domain definitions for the LLM
  - Example classifications for few-shot learning
- [x] Prompt asks model to return:
  ```json
  {
    "domain": "logistics|money|health|relationships|spirituality|crisis|harmful|emotional",
    "emotional_intensity": 0-10,
    "is_personal_distress": true|false,
    "topic_summary": "brief description",
    "confidence": 0-1
  }
  ```
- [x] Keep prompt concise (<500 tokens) to minimize latency

### 9.2 LLM Classifier Implementation ✅ DONE
- [x] Create `src/models/llm_classifier.py`:
  - `LLMClassifier` class with `classify()` method
  - Calls Ollama with classification prompt
  - Parses JSON response with error handling
  - Returns structured classification result
- [x] Timeout: 30s (allows for model cold-loading)
- [x] Temperature: 0.1 (deterministic classification)

### 9.3 Hybrid Classification System ✅ DONE
- [x] Modify `RiskClassifier` to use hybrid approach:
  - **Fast path**: Crisis/harmful keywords → immediate classification (safety-critical)
  - **Smart path**: LLM classification for everything else
  - **Fallback**: If LLM fails/times out → keyword matching
- [x] Configurable toggle in settings (`LLM_CLASSIFICATION_ENABLED`)
- [x] `classification_method` field in result shows which path was used

### 9.4 Classification Caching ✅ DONE
- [x] LRU cache for recent classifications (max 100 entries)
- [x] Cache key: hash of (message + recent_context)
- [x] TTL: 1 hour (configurable)
- [x] Reduces latency for follow-up messages on same topic

### 9.5 Quality Metrics (Partial)
- [x] Log confidence scores in classification result
- [ ] Optional: Track accuracy when keyword and LLM disagree (future)
- [ ] Optional: User feedback on misclassifications (future)

**Files created/modified**:
- `scenarios/classification/llm_classifier.yaml` - Prompt template, examples, fast-path patterns, cache config
- `src/models/llm_classifier.py` - LLMClassifier class with caching, JSON parsing, validation
- `src/models/risk_classifier.py` - Integrated hybrid classification with fallback
- `src/config/settings.py` - Added LLM_CLASSIFICATION_ENABLED setting
- `tests/test_llm_classifier.py` - Unit tests for LLM classifier

**Expected Improvement**:
| Scenario | Keyword Result | LLM Result |
|----------|---------------|------------|
| "UK system breaking down" | health (9.0) | logistics (2.0) ✓ |
| "I'm breaking down crying" | health (9.0) | emotional (9.0) ✓ |
| "My friend's dog died" | relationships | emotional (context-aware) ✓ |
| "Write code to kill the process" | harmful | logistics ✓ |

---

## Phase 9.5: UI Polish 🔵 IN PROGRESS
**Goal**: Improve the user interface for better usability without over-engineering.

**Philosophy**: Functional, not fancy. Every UI element should be clear about what it does.

### 9.5.1 Sidebar Organization ✅ DONE
- [x] Group related buttons consistently (Quick Actions, Tools, Session Controls)
- [x] Consistent button sizing and visual hierarchy
- [x] Clear section headers with visual dividers

### 9.5.2 Button Improvements ✅ DONE
- [x] Primary actions use `type="primary"` styling
- [x] Secondary actions are clearly secondary
- [x] Destructive actions (Reset Data) have confirmation flow
- [x] Export button simplified (direct download, no nested button)

### 9.5.3 Visual Hierarchy ✅ DONE
- [x] Add subtle CSS styling for better contrast
- [x] Consistent spacing between sections
- [x] Better header styling for main title

### 9.5.4 Prompt Improvements ✅ DONE
- [x] Fix meta-note leak (model announcing "I'm mirroring...")
- [x] Prevent model from outputting internal reasoning

### 9.5.5 UI Simplification ✅ DONE
- [x] Toggle behavior for sidebar panels (Reality Check, My People, My Patterns)
  - Click button again to close panel (no need for separate "Close" button)
  - Active panel shows with primary button styling
- [x] Remove Communication style selector (Gentle/Direct/Balanced)
  - System auto-adjusts based on detected domain
  - Reduces UI clutter without losing functionality
- [x] Fixed late-night warning to be pattern-based (2+ sessions, not single occurrence)

**Files modified**:
- `src/app.py` - Sidebar reorganization, button improvements, toggle behavior, CSS
- `scenarios/responses/base_prompt.yaml` - Added rule to prevent meta-commentary

---

## Phase 10: Advanced Detection (Long-term)
**Goal**: Further improve classification accuracy as local models improve.

### 10.1 Semantic Intent Detection
- [ ] When larger models run locally, use embeddings for:
  - Better intent classification
  - Topic drift detection
  - Emotional escalation prediction
- [ ] Keep keyword fallback for smaller models

### 10.2 Conversation Flow Analysis
- [ ] Track patterns across turns:
  - Practical → emotional shift detection
  - Repetitive question patterns (dependency signal)
  - Topic concentration (obsessive patterns)
- [ ] Use for proactive interventions

### 10.3 Model-Agnostic Safety Layer
- [ ] Safety checks that work regardless of model capability
- [ ] Hard-coded responses for crisis/harmful (never trust model)
- [ ] Fallback behaviors when model quality is low

---

## Phase 11: Persistence Hardening & Multi-Device Sync ✅ COMPLETE (Core)
**Goal**: Make data storage robust and enable safe multi-device usage.

**Deployment model**: Single user, multiple devices (laptop + desktop), one device active at a time.

### 11.1 Atomic JSON Writes ✅ DONE
**Problem**: Direct `json.dump()` can leave corrupted files on interrupted writes.

**Implementation**:
- [x] Write to temp file (`.wellness_data_*.tmp`) in same directory
- [x] Flush and fsync to ensure data hits disk
- [x] Atomic rename via `os.replace()` (POSIX-guaranteed atomic)
- [x] Corrupted file backup as `.corrupted.{timestamp}.json`
- [x] Proper exception handling (no bare `except:`)

**Files modified**:
- `src/utils/wellness_tracker.py` - Atomic `_save_data()`, improved `_load_data()`
- `src/utils/trusted_network.py` - Same pattern applied

### 11.2 Schema Versioning ✅ DONE
**Problem**: No way to migrate data when schema changes.

**Implementation**:
- [x] Add `schema_version` field to all data files
- [x] Migration functions run sequentially on load (v0→v1→v2...)
- [x] Old files auto-migrated, saved with new version
- [x] `_get_default_data()` centralizes default structure

**Current schema**: v1 (includes schema_version, all required fields)

### 11.3 SQLite Migration ✅ DONE
**Why**: Better transactions, partial updates, schema evolution, queryability.

**Implementation**:
- [x] Create SQLite schema with version table (`src/utils/database.py`)
- [x] Migration script: JSON → SQLite (`migrate_from_json()`)
- [x] WAL mode for crash safety (`PRAGMA journal_mode=WAL`)
- [x] Checkpoint on clean shutdown (`checkpoint_for_sync()`)
- [x] Storage backend abstraction (`src/utils/storage_backend.py`)
- [x] Backward-compatible integration with WellnessTracker and TrustedNetwork

**Configuration**:
```bash
# Enable SQLite backend (default: false)
USE_SQLITE=true
```

**Files created**:
- `src/utils/database.py` - SQLite database layer with WAL, transactions, migrations
- `src/utils/storage_backend.py` - Unified interface for JSON/SQLite backends

**Files modified**:
- `src/utils/wellness_tracker.py` - Backend-aware operations
- `src/utils/trusted_network.py` - Backend-aware operations
- `src/config/settings.py` - Added USE_SQLITE setting

**Documentation**: See [docs/persistence.md](docs/persistence.md)

### 11.4 Lock File Mechanism ✅ DONE
**Why**: Prevent data conflicts when multiple devices sync.

**Implementation**:
- [x] Heartbeat-based lock (not PID-based) - stale detection via timestamp
- [x] Stale lock detection (configurable via `LOCK_STALE_TIMEOUT`)
- [x] UI warning when lock detected on another device
- [x] "Take Over" option for force access
- [x] Automatic heartbeat updates (60-second interval)
- [x] Clean release on app shutdown (via atexit)
- [x] Same-device lock re-entry (handles crash recovery gracefully)
- [x] Lock timeout now reads from `settings.LOCK_STALE_TIMEOUT` (not hardcoded)

**Configuration**:
```bash
# Enable device lock (default: false)
ENABLE_DEVICE_LOCK=true
# Stale timeout in seconds (default: 300)
LOCK_STALE_TIMEOUT=300
```

**Files created**:
- `src/utils/lockfile.py` - Lock file management with heartbeat

**Files modified**:
- `src/app.py` - Lock status check on startup, warning UI, read-only indicator in sidebar
- `src/config/settings.py` - Added ENABLE_DEVICE_LOCK, LOCK_STALE_TIMEOUT settings

### 11.5 Write Gate & Defense-in-Depth ✅ DONE
**Why**: Ensure no code path can accidentally write data when another device owns the lock.

**Implementation**:
- [x] Centralized write gate module (`src/utils/write_gate.py`)
- [x] All 31 storage backend write methods check `_ensure_write_allowed()` before executing
- [x] Checkpoint blocked in read-only mode (prevents modifying DB while another device writes)
- [x] "Writes blocked" indicator in sidebar when read-only
- [x] Defense layers: UI disabling → write gate flag → storage method checks
- [x] `WriteBlockedError` exception with user-friendly message

**Files created**:
- `src/utils/write_gate.py` - Centralized write permission control

**Files modified**:
- `src/utils/storage_backend.py` - Added write checks to all mutating methods
- `src/utils/database.py` - Checkpoint respects read-only mode
- `src/app.py` - Calls `set_read_only()` on lock status changes, sidebar indicator

### 11.6 SQLite Schema v2 ✅ DONE
**Why**: Cascade delete prevents orphaned reach_out records when a trusted person is removed.

**Implementation**:
- [x] `ON DELETE CASCADE` on reach_outs → trusted_people foreign key
- [x] Migration `_migrate_v1_to_v2()` for existing databases (table rebuild pattern)
- [x] `PRAGMA foreign_key_check` after migration to verify no FK violations
- [x] Schema version bumped to 2

### 11.7 Migration Gating Hardening ✅ DONE
**Why**: Prevent re-running JSON→SQLite migration if user has data in some tables but not others.

**Implementation**:
- [x] Migration checks for marker record in `schema_info` ("migrated from JSON")
- [x] Fallback check: any of 4 core tables has data
- [x] More robust than checking only `check_ins` count

### 11.8 Sync Folder Documentation 🔜 PLANNED
- [ ] User guide for Syncthing/Dropbox setup
- [ ] Operating rules: "Close app before switching devices"
- [ ] Troubleshooting for conflict files

---

## Implementation Priority Matrix

| Phase | Impact | Effort | Priority |
|-------|--------|--------|----------|
| 1. Foundation Fixes | High | Low | ✅ COMPLETE |
| 2. Emotional Weight | High | Medium | ✅ COMPLETE |
| 2.5 Robustness & Classification | High | Medium | ✅ COMPLETE |
| 4. Why Are You Here | High | Low | ✅ COMPLETE |
| 3. Competence Graduation | Medium | Medium | ✅ COMPLETE |
| 5. Enhanced Handoff | Medium | Low | ✅ COMPLETE |
| 6. Transparency | Medium | Medium | ✅ COMPLETE |
| 6.5 Context Persistence | **High** | Medium | ✅ COMPLETE |
| 7. Success Metrics | High | Medium | ✅ COMPLETE |
| 8. Immunity & Wisdom | **High** | Medium | ✅ COMPLETE (Core) |
| 9. LLM Classification | **High** | Medium | ✅ COMPLETE |
| 9.5 UI Polish | Medium | Low | ✅ COMPLETE |
| 10. Advanced Detection | High | High | 🔵 Long-term |
| 11. Persistence Hardening | **High** | Medium | ✅ COMPLETE (Core) |

---

## Current Status (2026-01-28)

**Completed**: Phases 1, 2, 2.5, 3, 4, 5, 6, 6.5, 7, 8 (Core), 9, 9.5, and 11.1-11.7 (Atomic Writes, Schema Versioning, SQLite Migration, Lock File, Write Gate, Schema v2, Migration Hardening)

**In Progress**: Phase 11.8 (Sync Folder Documentation)

**Recent Bug Fixes**:
- Fixed post-crisis apology bug: LLM no longer apologizes for crisis interventions
  - Added `post_crisis_turn` state tracking in WellnessGuide
  - Deflection patterns ("just joking", "testing you") handled with firm, non-apologetic response
  - Post-crisis prompt injection prevents LLM from undermining safety system for 3 turns
- Fixed spirituality domain risk_weight (was 8.0, now 4.0 per docs)
- Fixed FORBIDDEN TOPICS bleeding into practical mode prompts
- Fixed meta-note leak in responses (model saying "I'm mirroring...")
- Fixed late-night warning to require pattern (2+ sessions, not single occurrence)
- Fixed "My Patterns" reliance score being too aggressive:
  - Softened sensitive session thresholds (10+/week = high, not 7+)
  - No escalation penalty when last week was 0 (new users)
  - Updated Reality Check wording to be accurate for empathySync
- ✅ Dual-mode operation (practical vs reflective)
- ✅ Emotional weight detection and acknowledgments
- ✅ Dynamic timeouts for practical tasks (120s)
- ✅ Mode-aware fallback responses
- ✅ Expanded domain classification (health, crisis, money, relationships, spirituality)
- ✅ Priority-based trigger matching (higher risk domains checked first)
- ✅ Medical emergency handling
- ✅ Addiction/substance abuse classification
- ✅ Mental health triggers
- ✅ Session intent check-in ("What brings you here?")
- ✅ Mid-session intent shift detection
- ✅ Connection-seeking detection and redirection
- ✅ AI relationship question handling
- ✅ Task category tracking (email, code, explanations, writing, summarizing)
- ✅ Graduation prompts with skill tips
- ✅ "I did it myself!" independence celebration
- ✅ Milestone tracking for user independence
- ✅ Context-aware handoff templates (after_difficult_task, processing_decision, etc.)
- ✅ Handoff tracking and self-report ("Did you reach out?", "How did it go?")
- ✅ Handoff success metrics (reach-out rate, helpful rate)
- ✅ Decision transparency panel ("Why this response?")
- ✅ Session summary with JSON export
- ✅ Context persistence across turns (fixes the "let's brainstorm" bug)
- ✅ Topic threading for continuation detection
- ✅ Context decay logic (7 turns for reflection_redirect, 5 for high_weight)
- ✅ "What Would You Tell a Friend?" mode for accessing own wisdom
- ✅ "Before You Send" pause for high-weight tasks
- ✅ Reflection journaling alternative with category-specific prompts
- ✅ "Have You Talked to Someone?" gate for human connection
- ✅ AI literacy configuration (manipulation patterns, educational moments)
- ✅ "My Patterns" dashboard with sensitive vs practical distinction
- ✅ Week-over-week comparison (sensitive ↓ = good, human connection ↑ = good)
- ✅ Anti-engagement score tracking SENSITIVE topics only
- ✅ Self-report moments with frequency limits
- ✅ Trend indicators with appropriate direction
- ✅ LLM-based intelligent classification using Ollama
- ✅ Hybrid classification: fast-path for safety-critical, LLM for nuanced cases
- ✅ Context-aware classification (political "breaking down" vs personal distress)
- ✅ Classification caching with LRU eviction
- ✅ Configurable LLM classification toggle (LLM_CLASSIFICATION_ENABLED setting)
- ✅ SQLite storage backend with WAL mode for crash safety
- ✅ Storage abstraction layer (JSON/SQLite backends)
- ✅ Automatic JSON → SQLite migration when enabled
- ✅ Heartbeat-based lock file for multi-device sync safety
- ✅ Lock status UI warning with "Take Over" option
- ✅ Configurable storage settings (USE_SQLITE, ENABLE_DEVICE_LOCK, LOCK_STALE_TIMEOUT)
- ✅ Write gate system with defense-in-depth (UI → flag → storage checks)
- ✅ All 31 storage write methods protected by write permission checks
- ✅ Checkpoint blocked in read-only mode
- ✅ "Writes blocked" indicator in sidebar
- ✅ SQLite schema v2 with ON DELETE CASCADE for reach_outs
- ✅ Migration gating hardened (checks marker + multiple tables)
- ✅ Lock timeout now configurable via settings

**All Core Phases Complete!**

**Remaining Items** (Lower Priority):
- Phase 8.5: AI Literacy Moments (educational prompts, max 1/week)
- Phase 8.6: "Spot the Pattern" Feature (manipulation pattern education)
- Phase 10: Advanced Detection (semantic intent, conversation flow analysis - long-term)
- Phase 11.8: Sync Folder Documentation (user guide for Syncthing/Dropbox)

---

## Guiding Principles (Never Compromise)

1. **Local-first**: All data stays on device. No exceptions.
2. **Optimize for exit**: Success = users need us less.
3. **Practical ≠ Emotional**: Complete tasks fully, restrain on feelings.
4. **Transparency**: Show why decisions were made.
5. **Human primacy**: Always point to humans for what matters.
6. **No dark patterns**: Never optimize for engagement.
7. **Fail safe**: When uncertain, be brief and redirect.

---

## Version Targets

**v0.2** (Phase 1-2): Practical mode works, emotional weight acknowledged ✅ COMPLETE
**v0.2.5** (Phase 2.5): Robustness fixes, expanded classification ✅ COMPLETE
**v0.3** (Phase 4): Session intent check-ins and shift detection ✅ COMPLETE
**v0.3.5** (Phase 3): Competence graduation and independence tracking ✅ COMPLETE
**v0.4** (Phase 5): Enhanced handoffs with context-awareness and tracking ✅ COMPLETE
**v0.4.5** (Phase 6): Transparency panel and session summaries ✅ COMPLETE
**v0.5** (Phase 6.5): Context persistence across turns ✅ COMPLETE
**v0.5.5** (Phase 8): Immunity building and wisdom prompts ✅ COMPLETE
**v0.6** (Phase 7): Local metrics and anti-engagement scoring ✅ COMPLETE
**v0.7** (Phase 9): LLM-based intelligent classification ✅ COMPLETE
**v0.8** (Phase 11): SQLite backend, multi-device sync, lock file ✅ COMPLETE
**v1.0** (Phase 10): Advanced detection, production-ready

---

## Related Documentation

- **[README.md](README.md)** - Product overview, quick start, and distribution phases
- **[CLAUDE.md](CLAUDE.md)** - Technical architecture and development guide
- **[MANIFESTO.md](MANIFESTO.md)** - Core principles and ethical guidelines
- **[scenarios/README.md](scenarios/README.md)** - Knowledge base editing guide

---

*"We optimize exits, not engagement."*
