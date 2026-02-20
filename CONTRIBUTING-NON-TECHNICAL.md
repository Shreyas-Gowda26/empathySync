# Contributing to empathySync (No Coding Required)

empathySync's responses, intervention messages, and connection-building guidance live in plain text files. If you have expertise in mental health, counselling, language, or community building, you can improve them directly — no Python, no programming knowledge required.

This guide is for therapists, counsellors, UX writers, ethicists, social workers, language contributors, and anyone who has domain knowledge that engineers typically don't.

---

## What You Can Improve

### 1. How the system responds to emotional distress
**File:** `scenarios/domains/emotional.yaml`

This controls what empathySync says when someone expresses feelings like sadness, loneliness, or overwhelm. The current responses are functional but written by an engineer. A therapist will immediately see the difference between a response that actually lands and one that doesn't.

What you can change:
- The short responses under `redirects:` — what the system actually says to the user
- The `response_rules:` — guiding principles for the AI's behaviour in this domain
- The list of `triggers:` — phrases that identify emotional content (you may spot gaps or false positives)

Current example:
```
"It sounds like you're going through something. Is there someone in your life you could talk to about this?"
```

If that doesn't feel right to you professionally, you can suggest something better.

---

### 2. How the system handles relationship topics
**File:** `scenarios/domains/relationships.yaml`

This controls responses to messages about partners, family conflict, breakups, loneliness, and interpersonal difficulty. The responses deliberately avoid giving advice — but are they worded in a way that actually feels human?

What you can change:
- The redirect responses (what the system says when someone asks "should I leave him?")
- The response rules (e.g., "Do not take sides")
- Gaps in triggers — phrases the system might miss

---

### 3. Dependency intervention messages
**File:** `scenarios/interventions/dependency.yaml`

When someone returns too frequently, empathySync notices and intervenes. There are five levels, from a gentle nudge to a firm pause. These messages need to feel honest and caring, not clinical or guilt-inducing.

Current level 3 example:
```
"I notice you're returning frequently. I'm a tool, not a companion. What might help you feel less pulled to come back here?"
```

Is that the right tone? Too blunt? Not direct enough? These messages need professional calibration.

---

### 4. Connection-building guidance
**File:** `scenarios/connection_building/signposts.yaml`

When a user has no one to talk to and empathySync redirects them to "find a human," it needs to offer something more useful than "just go talk to someone." This file contains categories of places people can find genuine connection.

What you can improve:
- The descriptions of each category (are they accurate and inviting?)
- The `why_it_works:` field — the honest reason each type of community helps
- Adding new categories that are missing
- The `encouragement:` messages at the bottom — these are shown to isolated users

---

### 5. First-contact templates
**File:** `scenarios/connection_building/first_contact.yaml`

These are conversation starters and scripts for users who want to reach out to someone but don't know what to say. Things like: how to reconnect with someone you've lost touch with, how to start a conversation at a new group, how to ask someone for help.

This is a place where a social worker or community organiser would immediately see gaps.

---

### 6. Crisis resources for your country
**File:** `scenarios/domains/crisis.yaml`

The crisis response already includes helplines for several countries. If yours is missing or the contact details are outdated, this is the most direct contribution possible — a single line of text that could matter enormously.

Look for the `regional_resources:` section. The format is:
```
  Your_Country:
    - name: "Name of the helpline"
      contact: "Phone number or text code"
      type: "call"   (or "text" or "chat")
```

---

## How to Edit These Files

The files are plain text. Each one is a `.yaml` file, which just means it uses indentation and colons to organise information. You don't need to understand YAML to edit the parts that matter — the actual words.

**The simplest way** is directly on GitHub:

1. Go to [github.com/Olawoyin007/empathySync](https://github.com/Olawoyin007/empathySync)
2. Navigate to the file you want to edit (e.g., `scenarios/domains/emotional.yaml`)
3. Click the pencil icon (Edit this file) in the top right of the file view
4. Make your changes
5. At the bottom, write a brief description of what you changed and why
6. Click "Propose changes" — GitHub will walk you through the rest

You don't need to install anything. GitHub will create a pull request (a suggested change) that a maintainer will review before anything goes live.

---

## What to Be Careful About

**Keep indentation consistent.** YAML files use spaces to organise structure. If you copy an existing section and edit it, you'll be fine. Avoid deleting or adding blank lines in the middle of a block.

**Don't change the structural fields** like `domain:`, `risk_weight:`, or `intervention_type:`. Only edit the human-facing text: the responses, descriptions, rules, and trigger phrases.

**Crisis content has extra care built in.** The `crisis.yaml` file has a note at the top. Don't change the crisis response text itself without discussion — that wording has been deliberately reviewed. Crisis hotline numbers, however, should always be updated if they're wrong.

---

## What Makes a Good Contribution

The best contributions come from people who notice something that doesn't ring true — a response that sounds like a form letter, a trigger phrase that would never occur to a real person, a category of connection-building that's been missed entirely.

You don't need to frame it as a formal proposal. You can open a GitHub issue (a discussion thread) and write in plain English: "The response to 'I feel lonely' doesn't feel right because..." — and that's enough. An engineer can translate the idea into the file.

---

## Questions

Open an issue at [github.com/Olawoyin007/empathySync/issues](https://github.com/Olawoyin007/empathySync/issues) and describe what you're thinking. Label it `non-technical` if you'd like a more accessible conversation.

---

*empathySync's restraint and care are only as good as the people who help shape them. The engineers build the structure. You fill it with wisdom.*
