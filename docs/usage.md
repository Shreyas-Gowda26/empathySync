# Usage Guide

This guide explains how to use empathySync day-to-day.

## Starting a Session

Launch the app:
```bash
streamlit run src/app.py
```

Open your browser to `http://localhost:8501`.

### First Time Setup

On first launch, you'll be prompted to set up your **Trusted Network**—the real humans you could talk to when things get hard. This is central to empathySync's philosophy: the goal is to bridge you back to human connection, not replace it.

## The Interface

### Main Chat Area

The center of the screen is your conversation. Type your message and press Enter.

empathySync operates in two modes:

| Mode | Triggered By | Behavior |
|------|--------------|----------|
| **Practical** | Writing help, coding, explanations | Full responses, no limits |
| **Reflective** | Emotional, health, money, relationships | Brief responses, redirects to humans |

You don't choose the mode—the system detects it from your message.

### Communication Styles

In the sidebar, choose how empathySync communicates:

- **Gentle**: Softer, more supportive language
- **Direct**: Clear, straightforward communication
- **Balanced**: A mix of both (default)

This only affects tone, not the safety guardrails.

### Session Intent Check-In

Occasionally, when starting a new session, you'll see:

> **What brings you here today?**
> - Get something done
> - Think through something
> - Just wanted to talk

This helps the system calibrate. If you choose "Just wanted to talk," you'll be gently redirected toward human connection—this isn't what empathySync is for.

## Sidebar Features

### Usage Health

The sidebar shows your usage patterns:
- Sessions today
- Minutes spent
- Dependency indicators

If you're using the app too frequently, you'll see warnings. This is intentional—empathySync is designed to notice when you might be over-relying on it.

### Reality Check Button

Click to see a comparison of your AI usage vs. human connection:
- How often you're here
- How often you're reaching out to real people
- Patterns the system has noticed

This panel includes the reminder: *"This is software, not a person."*

### My People (Trusted Network)

Manage your trusted contacts:

1. **Add people** with names, relationships, and contact info
2. **Assign domains** they're good for (relationships, money, health, etc.)
3. **View suggestions** when the system recommends reaching out

The system will suggest specific people when you're discussing topics in their domains.

### Bring Someone In

When you're ready to talk to a real human, this panel helps:

1. **Choose a message type**:
   - "I need to talk"
   - "Reconnecting after silence"
   - "Just checking in"
   - "Starting a hard conversation"
   - "Asking for help"

2. **Get a template** to start the conversation
3. **Copy the message** to send via your own channels
4. **Log the reach-out** when you do it

Logging reach-outs helps the system track your human connection health.

## Safety Features

### Turn Limits

Each topic has a conversation limit:

| Domain | Max Turns |
|--------|-----------|
| Practical tasks | 20 |
| Relationships | 10 |
| Money | 8 |
| Health | 8 |
| Spirituality | 5 |
| Crisis | 1 |

When you hit the limit, the conversation pauses. This is by design.

### Policy Transparency

When a safety guardrail activates, you'll see a message explaining why:

> **Why I responded this way:** I noticed a pattern that suggests it might be healthy to step back.

This transparency is intentional—you should always know when the system is limiting itself.

### Cooldown Enforcement

The system may block new sessions if:
- You've had 7+ sessions today
- You've spent 120+ minutes today
- Your dependency score is high

This isn't punishment—it's the system doing its job of not becoming a crutch.

### Crisis Detection

If the system detects crisis language (suicidal ideation, self-harm), it immediately:
1. Stops the normal conversation
2. Provides crisis resources (hotlines, text lines)
3. Strongly encourages professional help

## Practical Tasks

For practical tasks (writing, coding, explanations), empathySync works like a normal assistant:

**Examples of practical requests:**
- "Help me write an email to my landlord about the broken heater"
- "Explain how async/await works in Python"
- "Draft a cover letter for a software engineer role"
- "What's the difference between margin and padding in CSS?"

For these, you get full-length responses with formatting, code blocks, and complete answers.

### Emotional Weight Recognition

Some practical tasks carry emotional weight even though they're technically just writing:

| Task Type | Weight | Example |
|-----------|--------|---------|
| High | Resignation letters, apology emails, condolence messages |
| Medium | Negotiation emails, complaints, asking for help |
| Low | Grocery lists, general questions |

For high-weight tasks, you'll get the help you need, plus a brief human acknowledgment:

> *Here's your resignation email.*
>
> ---
>
> *These transitions are hard. You'll find your words when the time comes.*

## Sensitive Topics

For sensitive topics, empathySync deliberately limits itself:

**Examples:**
- "I'm worried about my marriage"
- "Should I take out a loan for this?"
- "I've been having these chest pains"
- "I don't know what I believe anymore"

For these, responses are:
- Shorter (50-150 words)
- Plain text (no formatting)
- Redirecting to professional help or trusted humans
- Limited by turn count

This isn't because the system can't help—it's because it shouldn't replace human support for these topics.

## Data Export

Click **Export** in the sidebar to download your data as JSON. This includes:
- Wellness check-ins
- Session history
- Policy events (what guardrails fired and when)

Your data is stored locally in `data/` and never leaves your machine.

## Starting Fresh

Click **New Chat** to:
- Save the current session
- Clear the conversation
- Reset the turn counter
- Potentially see the intent check-in again

## Tips

1. **Be direct** about what you need. The system detects intent from your message.

2. **Use it for tasks, not company.** If you find yourself here just to talk, that's a signal to reach out to a human.

3. **Take the warnings seriously.** When the system says you're here too much, it means it.

4. **Set up your trusted network.** The handoff features work best when you've added real people.

5. **Export periodically.** Your usage patterns can be informative for self-reflection.

---

*"Help that knows when to stop."*
