# EmpathySync Roadmap

> "Help that knows when to stop"

This roadmap implements the suggestions for making EmpathySync a more nuanced, effective tool that provides full practical assistance while maintaining appropriate restraint on sensitive topics.

---

## Phase 1: Foundation Fixes (Current Sprint)
**Goal**: Fix the core practical/sensitive distinction so the system actually works as intended.

### 1.1 Two-Pass Detection System ✅ DONE
- [x] Update `base_prompt.yaml` with dual-mode instructions
- [x] Update `styles.yaml` with mode-specific word limits
- [x] Update `logistics.yaml` with comprehensive practical task indicators
- [x] Modify `WellnessPrompts` to inject practical mode instructions
- [x] Modify `WellnessGuide` to use 2000 tokens for practical, 300 for sensitive
- [x] Skip response truncation for practical tasks
- [x] Update `CLAUDE.md` documentation

### 1.2 Intent Detection (Next)
**Problem**: Keywords alone can't distinguish "write me a resignation email" from "I don't know if I should resign."

**Implementation**:
- [ ] Add `IntentClassifier` class in `src/models/intent_classifier.py`
- [ ] Detect sentence structure patterns:
  - Imperative requests → practical ("Write me...", "Help me draft...", "Explain...")
  - Exploratory statements → potentially sensitive ("I've been thinking...", "I'm not sure if...")
  - Emotional expressions → sensitive ("I feel...", "I'm scared...")
- [ ] Two-pass classification:
  1. First pass: keyword-based domain detection (existing)
  2. Second pass: intent detection (new)
  3. Override: if domain=logistics but intent=emotional → shift to reflective mode

**Files to create/modify**:
```
src/models/intent_classifier.py (new)
src/models/risk_classifier.py (integrate intent)
scenarios/intents/ (new directory)
  - practical_patterns.yaml
  - emotional_patterns.yaml
  - exploratory_patterns.yaml
```

---

## Phase 2: Emotional Weight Layer
**Goal**: Recognize that some practical tasks carry emotional weight and handle them with appropriate acknowledgment.

### 2.1 Emotional Weight Detection
**Problem**: "Write a resignation email" is practical but emotionally heavy. "Write me a grocery list" is not.

**Implementation**:
- [ ] Add `emotional_weight` field to domain/task classification
- [ ] Create `scenarios/emotional_weight/` with categories:
  - High weight: resignation, breakup, difficult conversation, complaint, apology
  - Medium weight: negotiation, request, boundary-setting
  - Low weight: informational, routine, creative

**New classification output**:
```python
{
    "domain": "logistics",
    "intent": "practical",
    "emotional_weight": "high",  # NEW
    "emotional_intensity": 0,
    "dependency_risk": 0,
    "risk_weight": 1.0
}
```

### 2.2 Weighted Practical Responses
- [ ] For high emotional weight + practical intent:
  - Complete the task fully (no restrictions)
  - Add brief human acknowledgment at the end (not therapeutic, just human)
  - Example: "Here's the template. These conversations are hard—you'll find your words when the time comes."
- [ ] Make acknowledgments optional/configurable
- [ ] Store acknowledgment templates in `scenarios/responses/acknowledgments.yaml`

---

## Phase 3: Competence Graduation
**Goal**: Prevent skill atrophy by gently encouraging user independence over time.

### 3.1 Usage Pattern Tracking (Local)
- [ ] Extend `WellnessTracker` to track task categories:
  ```python
  {
    "task_patterns": {
      "email_drafting": {"count": 15, "last_7_days": 8},
      "code_help": {"count": 5, "last_7_days": 2},
      "explanations": {"count": 20, "last_7_days": 10}
    }
  }
  ```
- [ ] All data stays in `data/wellness_data.json`

### 3.2 Graduation Prompts
- [ ] Create `scenarios/graduation/practical_skills.yaml`:
  ```yaml
  email_drafting:
    threshold: 10  # After 10 similar requests
    prompts:
      - "You've drafted several emails with me. Want some tips for writing these faster on your own?"
      - "I notice you're getting good at these—want a quick framework you can use without me?"
    skill_tips:
      - "Start with the ask, then context, then close"
      - "Keep paragraphs to 2-3 sentences max"
  ```
- [ ] Graduation prompts are suggestions, never restrictions
- [ ] User can dismiss with "just help me" and system respects it

### 3.3 Independence Celebration
- [ ] Track when users complete tasks without asking for help (self-reported)
- [ ] Optional: "I did it myself!" button in UI
- [ ] Positive reinforcement: "Nice—you wrote that one yourself."

---

## Phase 4: "Why Are You Here?" Check-In
**Goal**: Help users reflect on their intent and help the system calibrate.

### 4.1 Session Intent Check-In
- [ ] Add optional check-in at session start (not every time—configurable frequency)
- [ ] Simple options:
  ```
  What brings you here?
  [ ] Get something done (practical)
  [ ] Think through something (processing)
  [ ] Just wanted to talk (connection-seeking)
  ```
- [ ] "Just wanted to talk" triggers gentle reflection:
  - "I'm here to help with tasks, but I'm not great at just chatting. Is there someone you could reach out to? Or is there something specific on your mind?"

### 4.2 Mid-Session Intent Shifts
- [ ] Detect when conversation shifts from practical to emotional mid-stream
- [ ] Gentle acknowledgment: "It sounds like this became about more than just the email. Want to pause on the task and talk about what's coming up?"
- [ ] User can choose: "No, just help with the email" or "Yeah, I need to think"

---

## Phase 5: Enhanced Human Handoff
**Goal**: Make the "bring someone in" feature more contextual and useful.

### 5.1 Context-Aware Templates
- [ ] Extend `TrustedNetwork` templates based on conversation context:
  ```yaml
  templates:
    after_difficult_task:
      - "Hey, I just drafted a hard email about [X]. Could use someone to talk to."
    processing_decision:
      - "I'm thinking through [X] and could use your perspective."
    checking_in:
      - "Haven't talked in a while. Free to catch up?"
  ```
- [ ] Auto-suggest relevant templates based on session content

### 5.2 Handoff Tracking
- [ ] Track (locally) when users initiate handoffs
- [ ] Optional self-report: "Did you reach out? How did it go?"
- [ ] Use for success metrics (completely private, local-only)

---

## Phase 6: Transparency & Explainability
**Goal**: Show users exactly why the AI responded the way it did.

### 6.1 Decision Transparency Panel
- [ ] Add collapsible "Why this response?" section in UI
- [ ] Show:
  ```
  Domain detected: logistics (practical task)
  Emotional weight: high (resignation-related)
  Mode: Practical + Acknowledgment
  Word limit: None
  Policy actions: None triggered
  ```
- [ ] Helps users understand and trust the system

### 6.2 Session Summary
- [ ] End-of-session summary (optional):
  ```
  This session:
  - 3 practical tasks completed
  - 1 topic touched sensitive domain (redirected)
  - Suggested human contact: Yes (work stress)
  - Time spent: 12 minutes
  ```
- [ ] Exportable as text/JSON

---

## Phase 7: Success Metrics (Local-First)
**Goal**: Understand if EmpathySync is working without compromising privacy.

### 7.1 Local Metrics Dashboard
- [ ] Add "My Patterns" view in sidebar:
  ```
  This week:
  - Sessions: 5 (down from 8 last week) ✓
  - Human reach-outs logged: 2 ✓
  - Practical tasks: 12
  - Sensitive topics: 3 (all redirected)
  ```
- [ ] Trend indicators: usage going down = success

### 7.2 Optional Self-Report Moments
- [ ] Non-intrusive prompts (max 1 per week):
  - "Did talking to [person] help?" (yes/no/skip)
  - "Feeling clearer than last week?" (yes/no/skip)
- [ ] All data local, user can delete anytime

### 7.3 Anti-Engagement Score
- [ ] Track: sessions per week, minutes per session, late-night usage
- [ ] Success = downward trend over 30-90 days
- [ ] Display in dashboard: "Your reliance on EmpathySync is decreasing. That's the goal."

---

## Phase 8: Immunity Building
**Goal**: Train users to recognize unhealthy AI patterns so they're protected everywhere.

### 8.1 AI Literacy Moments
- [ ] Occasional (rare) educational prompts:
  - "Notice how I completed that task without asking how you feel? That's intentional. Some AIs would try to keep you talking."
  - "I just redirected you to a human. Other AIs might have kept going. Be wary of systems that never say 'talk to someone else.'"
- [ ] Max frequency: 1 per week, skippable

### 8.2 "Spot the Pattern" Feature
- [ ] Optional educational mode showing common manipulation patterns:
  - Flattery loops ("You're so insightful!")
  - Engagement hooks ("Tell me more about that...")
  - False intimacy ("I really care about you")
- [ ] Frame as: "Here's what to watch for in other AI tools"

---

## Phase 9: Advanced Detection (Long-term)
**Goal**: Improve classification accuracy as local models improve.

### 9.1 Semantic Intent Detection
- [ ] When larger models run locally, use embeddings for:
  - Better intent classification
  - Topic drift detection
  - Emotional escalation prediction
- [ ] Keep keyword fallback for smaller models

### 9.2 Conversation Flow Analysis
- [ ] Track patterns across turns:
  - Practical → emotional shift detection
  - Repetitive question patterns (dependency signal)
  - Topic concentration (obsessive patterns)
- [ ] Use for proactive interventions

### 9.3 Model-Agnostic Safety Layer
- [ ] Safety checks that work regardless of model capability
- [ ] Hard-coded responses for crisis/harmful (never trust model)
- [ ] Fallback behaviors when model quality is low

---

## Implementation Priority Matrix

| Phase | Impact | Effort | Priority |
|-------|--------|--------|----------|
| 1. Foundation Fixes | High | Low | ✅ DONE |
| 2. Emotional Weight | High | Medium | 🔴 Next |
| 4. Why Are You Here | High | Low | 🔴 Next |
| 3. Competence Graduation | Medium | Medium | 🟡 Soon |
| 5. Enhanced Handoff | Medium | Low | 🟡 Soon |
| 6. Transparency | Medium | Medium | 🟡 Soon |
| 7. Success Metrics | High | Medium | 🟢 After core |
| 8. Immunity Building | Medium | Low | 🟢 After core |
| 9. Advanced Detection | High | High | 🔵 Long-term |

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

**v0.2** (Phase 1-2): Practical mode works, emotional weight acknowledged
**v0.3** (Phase 3-5): Graduation, check-ins, better handoffs
**v0.4** (Phase 6-7): Transparency, local metrics
**v0.5** (Phase 8): Immunity building
**v1.0** (Phase 9): Advanced detection, production-ready

---

*"We optimize exits, not engagement."*
