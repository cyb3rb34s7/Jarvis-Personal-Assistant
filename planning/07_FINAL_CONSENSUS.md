# JARVIS Final Consensus Document (REVISED)

**Date:** January 29, 2026
**Revision:** 2.0 - Post-debate revision incorporating user feedback
**Status:** AUTHORITATIVE - This document supersedes all previous versions

---

## Revision Summary

Key changes from v1.0:
- **Voice IN v1** (was deferred to v0.2)
- **LangGraph** added as agent framework (was raw Ollama)
- **Incremental phases** with testable checkpoints (was 4-week timeline)
- **Reference implementations** documented (local-talking-llm, Clawdbot)

---

## Executive Summary

**Core Philosophy:** Build incrementally with testable checkpoints. Each phase produces working software.

**Key Decisions:**
- **LangGraph** for agent orchestration (not raw Ollama)
- **Voice in v1** - faster-whisper + Piper (not deferred)
- **CLI first**, Web UI optional
- **ChromaDB** when RAG needed
- **7B model only** (no hot-swapping)
- **No plugin system** - build features directly

---

## Part 1: Technology Stack

### Agent Layer

| Component | Choice | Why |
|-----------|--------|-----|
| Framework | **LangGraph** | Built-in agent loops, tool calling, state management |
| LLM Client | langchain-ollama | Clean Ollama integration |
| State | LangGraph StateGraph | Conversation context, checkpointing |

**Why LangGraph over raw Ollama:**
- Handles tool calling loops automatically (agent → tool → agent)
- State management between turns
- Conditional branching on tool failures
- Can checkpoint and resume conversations

### LLM Layer

| Component | Choice | Why |
|-----------|--------|-----|
| Runtime | **Ollama** | Simple model management, Windows native |
| Model | **Qwen2.5-7B-Instruct-Q4_K_M** | Best 7B for tools, ~5GB VRAM |

### Voice Layer

| Component | Choice | Why |
|-----------|--------|-----|
| STT | **faster-whisper** (medium) | 4x faster than Whisper, ~1.5GB VRAM |
| TTS | **Kokoro-82M** (kokoro-onnx) | ~80MB, ONNX/CPU, Apache 2.0 |
| Audio I/O | **sounddevice** | Better than PyAudio on Windows |
| VAD | **Silero VAD** | Accurate voice activity detection |
| Interrupt | **Barge-in** | Threaded audio with stop flag |

### Storage Layer

| Component | Choice | Why |
|-----------|--------|-----|
| Notes | Markdown files | Portable, user-owned |
| Reminders | JSON file | Simple, persistent |
| Config | YAML | Human-readable |
| Vector DB | **ChromaDB** (when RAG added) | Community support |

---

## Part 2: VRAM Budget

**Target:** Stay under 8GB to maintain 4GB headroom on 12GB card.

| Component | VRAM | Status |
|-----------|------|--------|
| Qwen2.5-7B-Q4_K_M | 5.0 GB | Always loaded |
| faster-whisper medium | 1.5 GB | Always loaded |
| nomic-embed-text | 0.3 GB | On-demand |
| System buffer | 1.2 GB | Reserved |
| **Total** | **8.0 GB** | ✅ 4GB headroom |

---

## Part 3: Feature Set

### v1 INCLUDES:

1. **Voice Input (Push-to-Talk)**
   - Hotkey activation (Ctrl+Space default)
   - faster-whisper transcription
   - Silero VAD for auto-stop
   - Visual feedback while listening

2. **Voice Output**
   - Piper TTS
   - Sentence-level streaming
   - Configurable voice

3. **LLM Agent (LangGraph)**
   - Tool calling with automatic loops
   - Conversation context (last N turns)
   - Streaming responses

4. **Tools:**
   - `calculator` - Math operations
   - `reminder_set` - Create reminders with natural language
   - `reminder_list` - Show pending reminders
   - `note_save` - Save a note
   - `note_search` - Search notes
   - `web_search` - DuckDuckGo search

5. **Reminders**
   - Natural language time parsing
   - Persistent across sessions
   - Windows toast notifications

6. **Notes**
   - Save as markdown files
   - BM25 fuzzy search (rank_bm25) - handles typos/partial matches
   - Timestamped filenames

7. **CLI Interface**
   - `jarvis "question"` - Ask anything
   - `jarvis --voice` - Enter voice mode
   - `jarvis note "text"` - Save note
   - `jarvis remind "msg" --in "30m"` - Set reminder

### OUT OF SCOPE:

- Wake word / always listening
- Smart home control
- Calendar integration
- Email access
- PC automation
- Plugin/skill system
- Multi-user support

---

## Part 4: Implementation Phases

### Phase 1: Core Agent (~30 min)

**Testable Checkpoint:**
```bash
jarvis "what is 2+2"
# Returns: "4"
```

**Tasks:**
- [ ] Set up Python venv with dependencies
- [ ] Install Ollama, pull Qwen2.5-7B
- [ ] Create LangGraph agent with calculator tool
- [ ] CLI entry point
- [ ] Streaming output to terminal

**Files:**
```
src/jarvis/__main__.py
src/jarvis/cli.py
src/jarvis/agent/graph.py
src/jarvis/agent/tools.py
```

---

### Phase 2: Tools (~30 min)

**Testable Checkpoint:**
```bash
jarvis remind "test this" --in "1m"
# Notification fires after 1 minute

jarvis note "Great idea for the project"
jarvis search "idea"
# Returns the note
```

**Tasks:**
- [ ] Reminder tool with persistent storage
- [ ] Note save/search tools
- [ ] Web search tool (DuckDuckGo)
- [ ] Windows notifications (plyer)

**Files:**
```
src/jarvis/features/reminders.py
src/jarvis/features/notes.py
src/jarvis/features/search.py
src/jarvis/utils/notifications.py
data/reminders.json
```

---

### Phase 3: Voice Input (~30 min)

**Testable Checkpoint:**
```bash
jarvis --voice
# Press Ctrl+Space, speak "what time is it"
# Text appears: "what time is it"
```

**Tasks:**
- [ ] faster-whisper integration
- [ ] Silero VAD for speech detection
- [ ] Push-to-talk hotkey (pynput)
- [ ] Audio capture (sounddevice)
- [ ] Visual feedback (listening indicator)

**Files:**
```
src/jarvis/voice/stt.py
src/jarvis/voice/audio.py
```

---

### Phase 4: Voice Output (~20 min)

**Testable Checkpoint:**
```bash
jarvis --voice
# Speak: "what is the capital of France"
# JARVIS speaks: "The capital of France is Paris"
```

**Tasks:**
- [ ] Piper TTS integration
- [ ] Sentence-level streaming
- [ ] Audio output queue
- [ ] Voice selection config

**Files:**
```
src/jarvis/voice/tts.py
```

---

### Phase 5: Polish (~30 min)

**Testable Checkpoint:**
```
Full voice conversation loop works reliably
Can use daily without frustration
```

**Tasks:**
- [ ] Error handling and recovery
- [ ] Configuration file support
- [ ] System tray icon (optional)
- [ ] Web UI (optional, FastAPI + HTMX)
- [ ] Documentation

---

## Part 5: Directory Structure

```
D:\PROJECTS\JARVIS\
├── CLAUDE.md                    # Persistent project memory
├── planning/                    # Research & debate docs
├── src/
│   └── jarvis/
│       ├── __init__.py
│       ├── __main__.py          # Entry point
│       ├── cli.py               # Click CLI
│       ├── config.py            # Configuration management
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── graph.py         # LangGraph agent
│       │   └── tools.py         # Tool definitions
│       ├── voice/
│       │   ├── __init__.py
│       │   ├── stt.py           # faster-whisper
│       │   ├── tts.py           # Piper
│       │   └── audio.py         # sounddevice I/O
│       ├── features/
│       │   ├── __init__.py
│       │   ├── notes.py
│       │   ├── reminders.py
│       │   └── search.py
│       └── utils/
│           ├── __init__.py
│           └── notifications.py
├── data/
│   ├── notes/
│   ├── reminders.json
│   └── config.yaml
├── tests/
├── pyproject.toml
└── README.md
```

---

## Part 6: Dependencies

```toml
[project]
name = "jarvis"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    # Agent Framework
    "langgraph>=0.2",
    "langchain-ollama>=0.2",
    "langchain-core>=0.3",

    # Voice
    "faster-whisper>=1.0",
    "kokoro-onnx>=0.4",
    "sounddevice>=0.4",

    # CLI & Config
    "click>=8.0",
    "pyyaml>=6.0",
    "pydantic>=2.0",

    # Utilities
    "httpx>=0.27",
    "plyer>=2.0",
    "pynput>=1.7",
    "rank_bm25>=0.2",

    # RAG (optional, for later)
    # "chromadb>=0.4",
]

[project.scripts]
jarvis = "jarvis.__main__:main"
```

---

## Part 7: Reference Implementations

### Primary Reference: local-talking-llm
**URL:** https://github.com/vndee/local-talking-llm

**Relevant patterns:**
- Whisper + Ollama + TTS pipeline
- LangChain integration
- Modular voice components
- Clean dependency management

### Secondary Reference: Clawdbot/Moltbot
**URL:** https://github.com/clawdbot/clawdbot

**Relevant patterns:**
- Gateway daemon architecture
- Streaming tool responses
- Multi-channel routing (study, don't copy)

**Note:** Clawdbot uses cloud APIs (Claude, ElevenLabs). We're local-only.

### Architecture Reference: Rhasspy
**URL:** https://github.com/rhasspy/rhasspy

**Relevant patterns:**
- Offline voice pipeline design
- Wyoming protocol for modularity

---

## Part 8: Critical Gates

### Gate 1: LangGraph + Ollama Tool Calling
**Must pass before proceeding.**

Test:
```python
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama

llm = ChatOllama(model="qwen2.5:7b-instruct")
agent = create_react_agent(llm, tools=[calculator_tool])
result = agent.invoke({"messages": [("user", "what is 15 * 7?")]})
# Must return: 105
```

If fails: Fall back to manual tool parsing or switch models.

### Gate 2: Voice Pipeline
**Must pass before Phase 4.**

Test: Speak clearly, transcription is >90% accurate.

If fails: Try Whisper large model (more VRAM) or improve audio setup.

---

## Part 9: Success Criteria

### v1 is DONE when:
- [ ] Voice input works reliably (>90% accuracy)
- [ ] Voice output sounds natural
- [ ] All 6 tools function correctly
- [ ] Reminders persist across restarts
- [ ] Notes save and search correctly
- [ ] No crashes in 30 min of use
- [ ] Can be used for real tasks

### ABANDON if:
- Gate 1 fails and no fix found in 2 hours
- Voice pipeline is unusable after 4 hours of debugging
- VRAM exceeds 10GB with required components

---

## Part 10: Immediate Next Steps

1. **Create project structure**
2. **Install dependencies**
3. **Pass Gate 1** (LangGraph + Ollama)
4. **Build Phase 1** (Core Agent)
5. **Test checkpoint**
6. **Proceed to Phase 2**

---

*Final Consensus v2.0 - Revised with user feedback*
*January 29, 2026*
*"Build incrementally. Test constantly. Ship working software."*
