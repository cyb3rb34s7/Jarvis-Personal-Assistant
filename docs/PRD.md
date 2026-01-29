# JARVIS - Product Requirements Document

**Version:** 1.1
**Date:** January 29, 2026
**Status:** Approved (Updated with MCP Integration)

---

## 1. Product Overview

### 1.1 Vision
JARVIS is a local, privacy-first AI personal assistant with voice interaction capabilities. It runs entirely on the user's hardware with zero cloud dependencies.

### 1.2 Target User
- Developer/power user comfortable with CLI
- Owns capable GPU (RTX 4070 or similar)
- Values privacy over convenience
- Wants voice interaction for hands-free queries

### 1.3 Core Value Proposition
- **100% Local:** No data leaves your machine
- **Voice-First:** Natural push-to-talk interaction
- **Agentic:** Performs tasks, not just chat
- **Low Cost:** $0 operational cost after setup

---

## 2. User Hardware

| Component | Specification |
|-----------|---------------|
| CPU | Ryzen 7 9800X3D |
| RAM | 32GB DDR5 6000MHz |
| GPU | RTX 4070 12GB VRAM |
| Storage | 1TB SSD |
| OS | Windows |

---

## 3. Features

### 3.1 Core Features (v1)

#### Voice Input
- **Activation:** Push-to-talk hotkey (Ctrl+Space default)
- **Processing:** faster-whisper medium model
- **Accuracy Target:** >90% on clear speech
- **Feedback:** Visual indicator while listening

#### Voice Output
- **Engine:** Kokoro TTS (ONNX, CPU)
- **Streaming:** Sentence-level for low latency
- **Voice:** English only (af_heart voice)
- **Limitation:** No Hindi/multilingual support yet

#### LLM Agent
- **Framework:** LangGraph
- **Model:** Qwen2.5-7B-Instruct via Ollama
- **Capabilities:** Tool calling, multi-turn context

#### Built-in Tools
| Tool | Function |
|------|----------|
| `calculator` | Math operations |
| `reminder_set` | Create time-based reminders |
| `reminder_list` | List pending reminders |
| `note_save` | Save a note to file |
| `note_search` | Search saved notes |
| `web_search` | DuckDuckGo search (free, unlimited) |
| `deep_search` | Exa semantic search (2000/month free) |

#### MCP Integration (Extensibility)
- **Protocol:** Model Context Protocol (MCP) - industry standard
- **Configuration:** JSON file (`data/mcp_servers.json`)
- **No code changes:** Add new tools by editing config file
- **Multi-server:** Connect to multiple MCP servers simultaneously

| Example MCP Servers | Tools Provided |
|---------------------|----------------|
| Exa | Web search, code search, company research |
| GitHub | Issues, PRs, repos, code search |
| Filesystem | Read, write, list files |
| Brave Search | Web search |
| Slack | Messages, channels |

#### Reminders
- Natural language time parsing ("in 30 minutes", "at 3pm")
- Persistent across restarts
- Windows toast notifications

#### Notes
- Save as markdown files
- Keyword-based search
- Timestamped organization

#### CLI Interface
```bash
jarvis "question"           # Ask anything
jarvis --voice              # Voice mode
jarvis note "text"          # Save note
jarvis remind "msg" --in "30m"  # Set reminder
jarvis search "term"        # Search notes
```

### 3.2 Deferred Features (v2+)
- RAG / semantic search (ChromaDB)
- Web UI (FastAPI + HTMX)
- System tray application
- Clipboard integration
- Conversation history persistence
- Hindi TTS (multilingual voice output)
- Better Hinglish STT accuracy

### 3.3 Out of Scope
- Wake word / always listening
- Smart home control
- Calendar integration (can add via MCP later)
- Email access (can add via MCP later)
- PC automation
- Multi-user support
- Mobile companion

**Note:** Some "out of scope" features can be added later via MCP servers without code changes (e.g., Google Calendar MCP, Gmail MCP).

---

## 4. Non-Functional Requirements

### 4.1 Performance
| Metric | Target |
|--------|--------|
| Voice transcription latency | <500ms |
| LLM first token | <200ms |
| LLM generation speed | >50 tok/s |
| TTS first audio | <100ms |
| End-to-end voice response | <2s (simple queries) |

### 4.2 Resource Usage
| Resource | Limit |
|----------|-------|
| VRAM | <8GB (of 12GB) |
| RAM | <4GB |
| Disk (models) | ~10GB |

### 4.3 Reliability
- No crashes in 30 min of normal use
- Graceful degradation on errors
- Clear error messages

### 4.4 Privacy
- Zero network calls except explicit web search
- All data stored locally
- User owns all data (plain files)

---

## 5. Success Criteria

### v1 Launch Criteria
- [x] Voice input >90% accurate (Whisper large-v3-turbo)
- [x] Voice output natural and clear (Kokoro TTS)
- [x] All built-in tools functional (7 tools)
- [x] Reminders persist across restarts
- [x] Notes save and search correctly
- [ ] MCP integration working (JSON config)
- [ ] No crashes in extended use (30 min test)

### User Success Criteria
- Can complete real tasks faster than alternatives
- Would use daily without frustration
- Would recommend to others

---

## 6. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| VRAM overflow | Conservative budget, monitoring |
| Poor voice accuracy | Configurable Whisper model size |
| Windows audio issues | sounddevice, fallback options |
| LLM quality issues | Structured output, validation |
| Scope creep | Strict feature freeze |

---

## 7. References

- **Research:** `planning/01_research_alpha.md`
- **Architecture:** `planning/02_architecture_beta.md`
- **Debate:** `planning/05_debate_epsilon.md`, `planning/06_devils_advocate_zeta.md`
- **Reference Projects:**
  - https://github.com/vndee/local-talking-llm
  - https://github.com/clawdbot/clawdbot

---

*Document Owner: User*
*Last Updated: January 29, 2026*
