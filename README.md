# empathySync
*Help that knows when to stop*

## Mission

empathySync is a local-first AI assistant that provides **full help for practical tasks** while applying **restraint on sensitive topics**. It actively works to reduce user dependency on AI for emotional support while being genuinely helpful for everyday practical tasks.

**"We optimize exits, not engagement."**

## Why empathySync?

As AI becomes increasingly present in our daily lives, many people experience:
- Unhealthy dependency on AI for decision-making
- Digital overwhelm and technology fatigue  
- Loss of human autonomy and self-reliance
- Lack of awareness about their AI usage patterns
- No guidance for maintaining healthy tech boundaries

empathySync serves as your gentle guide, helping you:
- Recognize unhealthy AI dependency patterns
- Develop mindful technology habits  
- Find balance between AI assistance and human autonomy
- Cultivate self-awareness in digital spaces
- Honor your independence while embracing beneficial AI tools

## Core Principles

 **Empathetic**: Every interaction centers human wellbeing and emotional safety  
 **Local-First**: Complete data sovereignty, your conversations never leave your device  
 **Open Source**: Transparent, community-driven development serving users  
 **Donation-Supported**: Sustained by community generosity, not profit motives  
 **Privacy-Focused**: Technology that respects and protects user privacy  

## Quick Start

### Clone and Setup
```bash
git clone https://github.com/[your-username]/empathySync.git
cd empathySync
```

Install dependencies
```bash
pip install -r requirements.txt
```

Launch your AI wellness companion
```bash
streamlit run src/app.py
```

## Features

**Dual-Mode Intelligence**: Full assistance for practical tasks (emails, code, explanations), restraint on sensitive topics (relationships, finances, health)

**Session Intent Check-In**: "What brings you here?" - helps calibrate responses and detects connection-seeking behavior

**Emotional Weight Awareness**: Recognizes emotionally heavy tasks (resignation emails, difficult conversations) and adds brief human acknowledgment

**Trusted Network**: Build your list of real humans to reach out to, with pre-written templates for hard conversations

**Dependency Detection**: Monitors usage patterns and gently intervenes when over-reliance is detected

**Connection-Seeking Redirect**: When you "just want to talk," gently redirects to human connection

**Local-First Privacy**: All conversations processed on your device via Ollama - no external API calls, no telemetry  

## Technical Foundation

- **Local LLM Integration**: Runs entirely on your hardware via Ollama
- **Privacy-First**: Zero external API calls, complete data sovereignty  
- **Lightweight**: Optimized for consumer hardware and efficient operation
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Docker Support**: Easy deployment and consistent environment

## System Requirements

**Minimum:**
- 4GB RAM
- 2GB free storage
- Python 3.8+
- Docker (optional but recommended)

**Recommended:**
- 8GB RAM
- 4GB free storage
- GPU support for faster responses
  
## Development Phases

### Phase 1: Core Engine ✅ COMPLETE
- [x] Empathetic conversation loop
- [x] Local Ollama integration
- [x] Dual-mode operation (practical tasks vs sensitive topics)
- [x] Basic boundary-setting check-ins
- [x] Session intent detection ("What brings you here?")

### Phase 2: Emotional Intelligence ✅ COMPLETE
- [x] Local usage tracking and reflection prompts
- [x] Emotional weight detection for practical tasks
- [x] Connection-seeking detection and redirection
- [x] Mid-session intent shift detection
- [x] Context persistence across conversation turns

### Phase 3: User Empowerment ✅ COMPLETE
- [x] Competence graduation (encourage independence)
- [x] Transparency dashboard (why AI responded this way)
- [x] "My Patterns" metrics dashboard
- [x] "What Would You Tell a Friend?" wisdom prompts
- [x] "Have You Talked to Someone?" human connection gate

### Phase 4: Intelligent Classification ✅ COMPLETE
- [x] LLM-based context-aware classification (Phase 9)
- [x] Hybrid system: fast-path for safety, LLM for nuance
- [x] Classification caching for performance
- [x] Configurable via `LLM_CLASSIFICATION_ENABLED`

### Phase 5: Distribution (In Progress)
- [ ] Simple executable packaging (PyInstaller)
- [ ] Native installer creation
- [ ] User feedback collection (beta users)
- [ ] Multi-language support

### Phase 6: Community & Platform (Future)
- [ ] App store distribution (if applicable)
- [ ] Community plugin system
- [ ] Mobile companion app
- [ ] Research partnerships for wellness insights

> **Note:** For detailed feature implementation plans, see [ROADMAP.md](ROADMAP.md)


## Contributing

We welcome contributions from developers who care about digital wellness and ethical AI. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support This Project

If empathySync helps you develop a healthier relationship with AI:

- ⭐ Star this repository
- 🙏 [GitHub Sponsors](#) 
- ☕ [Ko-fi](#)
- 🤝 Contribute to the codebase
- 📢 Share with others interested in digital wellness

## License

MIT License - Built for everyone's benefit and maximum accessibility.

## Community

Join our community of digital wellness enthusiasts:
- 💬 [Discussions](https://github.com/[your-username]/empathySync/discussions)
- 🐛 [Issues](https://github.com/[your-username]/empathySync/issues)
- 📖 [Documentation](./docs/)
---

*Building technology that serves human flourishing in the age of AI.*
