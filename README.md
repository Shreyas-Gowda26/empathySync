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

### Phase 1: Core Engine & Usability ✅ COMPLETE
- [x] Empathetic conversation loop
- [x] Local Ollama integration
- [x] Dual-mode operation (practical tasks vs sensitive topics)
- [x] Basic boundary-setting check-ins
- [x] Session intent detection ("What brings you here?")
- [ ] Simple executable packaging (PyInstaller)
- [ ] Setup script for dependencies

### Phase 2: Validation & Polish (Current)
- [x] Local usage tracking and reflection prompts
- [x] Emotional weight detection for practical tasks
- [x] Connection-seeking detection and redirection
- [x] Mid-session intent shift detection
- [ ] User feedback collection (5-10 beta users)
- [ ] Native installer creation
- [ ] Iteration based on real user experiences

### Phase 3: Enhanced Features
- [ ] Competence graduation (encourage independence)
- [ ] Multi-language support
- [ ] Weekly/monthly wellness patterns
- [ ] Desktop notifications for check-ins
- [ ] Transparency dashboard (why AI responded this way)

### Phase 4: Community & Distribution
- [ ] App store distribution (if applicable)
- [ ] Community plugin system
- [ ] Donation and sponsorship channels

### Phase 5: Advanced Platform
- [ ] Mobile companion app
- [ ] Research partnerships for wellness insights
- [ ] Long-term sustainability model

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
