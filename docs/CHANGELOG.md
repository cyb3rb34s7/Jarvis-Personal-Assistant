# JARVIS - Changelog

> **UPDATE AFTER EVERY TASK**

---

## 2026-02-01

### Session: Phase A - FastAPI Backend Implementation

#### Task: FastAPI Backend for GUI
**Time:** ~30 minutes
**Status:** ✅ Complete

**What was done:**
1. Created complete FastAPI backend structure in `src/jarvis/api/`
2. Implemented all REST + WebSocket endpoints:
   - `/api/v1/status` - System status, dependencies, database stats
   - `/api/v1/health` - Simple health check
   - `/api/v1/conversations` - CRUD for conversations
   - `/api/v1/chat` - POST endpoint for chat
   - `/api/v1/ws` - WebSocket for real-time chat
   - `/api/v1/reminders` - CRUD for reminders
   - `/api/v1/notes` - CRUD for notes with search
   - `/api/v1/mcp/servers` - List MCP servers
   - `/api/v1/mcp/tools` - List available MCP tools
   - `/api/v1/mcp/reload` - Reload MCP connections
   - `/api/v1/voice/transcribe` - Audio file → text
   - `/api/v1/voice/synthesize` - Text → WAV audio
   - `/api/v1/voice/synthesize/base64` - Text → base64 audio
3. Added Bearer token authentication (optional via JARVIS_API_SECRET)
4. Added CORS middleware for frontend development
5. Added `synthesize()` method to TTS returning WAV bytes
6. Added `transcribe_file()` method to STT for file-based transcription
7. Added `jarvis serve` CLI command to start API server
8. Added `librosa` dependency for audio file loading
9. Installed dependencies and tested all endpoints
10. Committed and pushed to GitHub

**Files created:**
- `src/jarvis/api/__init__.py` - API module exports
- `src/jarvis/api/main.py` - FastAPI app with CORS, lifespan, routers
- `src/jarvis/api/auth.py` - Bearer token authentication
- `src/jarvis/api/deps.py` - Shared dependencies (agent, session)
- `src/jarvis/api/routes/__init__.py` - Route exports
- `src/jarvis/api/routes/status.py` - Health and status endpoints
- `src/jarvis/api/routes/conversations.py` - Conversation CRUD
- `src/jarvis/api/routes/chat.py` - Chat POST + WebSocket
- `src/jarvis/api/routes/reminders.py` - Reminders CRUD
- `src/jarvis/api/routes/notes.py` - Notes CRUD with search
- `src/jarvis/api/routes/mcp.py` - MCP server/tools management
- `src/jarvis/api/routes/voice.py` - STT/TTS endpoints

**Files modified:**
- `pyproject.toml` - Added `librosa>=0.10` to voice dependencies
- `src/jarvis/cli.py` - Added `serve` command, updated SUBCOMMANDS
- `src/jarvis/voice/tts.py` - Added `synthesize()` method returning WAV bytes
- `src/jarvis/voice/stt.py` - Added `transcribe_file()` and `get_stt()` methods

**Test Results:**
- `curl http://127.0.0.1:8765/api/v1/health` → `{"status":"ok"}` ✅
- `curl http://127.0.0.1:8765/api/v1/status` → Full status JSON ✅
- `curl http://127.0.0.1:8765/api/v1/conversations` → List of 6 conversations ✅
- `jarvis serve --help` → Shows usage ✅

**Git:**
- Committed: `Add FastAPI backend for GUI (Phase A)`
- Pushed to: `https://github.com/cyb3rb34s7/Jarvis-Personal-Assistant.git`

---

## 2026-01-29

### Session: GUI Architecture Finalization

#### Task: Architecture Decision - Cloudflare Tunnel vs Custom Gateway
**Time:** ~15 minutes
**Status:** ✅ Complete

**What was done:**
1. Discussed deployment architecture for remote access
2. Developer review identified custom gateway as unnecessary complexity
3. Decided to use Cloudflare Tunnel instead of writing custom WebSocket gateway
4. Updated GUI_PLAN.md with final architecture
5. Removed `gateway/` folder from planned structure

**Architecture Decision:**
```
Original Plan:
  Local Agent → Custom WebSocket Gateway (VPS) → Next.js UI
  - Requires writing reconnection logic, packet loss handling, auth
  - Weeks of debugging potential

Final Plan:
  Local Agent → cloudflared (daemon) → Cloudflare Edge → Next.js UI
  - Zero code for tunnel
  - Free tier, DDoS protected, mTLS built-in
  - Just run: cloudflared tunnel run jarvis
```

**Key Decisions:**
| Question | Decision | Rationale |
|----------|----------|-----------|
| Remote access | Cloudflare Tunnel | Free, secure, zero maintenance |
| Custom gateway | ❌ No | Tunnel replaces weeks of WebSocket debugging |
| Auth | Bearer token | Simple, works with tunnel |
| Remote latency | Optimistic UI | Show "Processing..." immediately |

**Files modified:**
- `docs/GUI_PLAN.md` - Complete rewrite with final architecture
- `docs/CONTEXT.md` - Added architecture decisions

**Developer Feedback Incorporated:**
- "You do not need to write this" (custom gateway)
- Use Cloudflare Tunnel - robust and free
- Add Bearer token auth for security
- Implement Optimistic UI for remote latency (~500ms)

---

### Session: Memory System Implementation

#### Task: Session Memory with SQLite
**Time:** ~25 minutes
**Status:** ✅ Complete

**What was done:**
1. Created SQLite database module (`database.py`) with schema:
   - `conversations` - Chat threads with titles and timestamps
   - `messages` - All messages with role, content, tool_call_id
   - `user_facts` - Long-term memory (preferences, facts)
   - `tool_usage` - Analytics tracking
2. Created memory module (`memory/session.py`) with:
   - SessionMemory class for conversation management
   - Safe sliding window that never splits tool call/response pairs
   - Auto-generated conversation titles from first message
   - LangChain message conversion for agent input
3. Updated agent (`graph.py`) to accept session parameter:
   - History injection into LLM context
   - User facts injection into system prompt
   - Tool call/response persistence
4. Updated CLI with new commands:
   - `jarvis chat` - Interactive session with memory
   - `jarvis chat --resume` - Resume last conversation
   - `jarvis chat --id <id>` - Resume specific conversation
   - `jarvis history` - View past conversations
5. Voice mode now uses session memory automatically

**Files created:**
- `src/jarvis/database.py` - SQLite setup and CRUD operations
- `src/jarvis/memory/__init__.py` - Module exports
- `src/jarvis/memory/session.py` - Session memory with sliding window
- `data/jarvis.db` - SQLite database (auto-created)

**Files modified:**
- `src/jarvis/agent/graph.py` - Added session parameter to run_agent functions
- `src/jarvis/cli.py` - Added chat, history commands, session in voice mode

**Key Design Decisions:**
- SQLite over LangGraph checkpointer: Manual control, cleaner sliding window
- 20-message context window: Balance between memory and relevance
- Safe sliding window: Never splits tool call from tool response (prevents LLM crashes)
- tool_call_id tracking: Links tool responses to their parent calls

**Test Results:**
- `jarvis chat` → Creates session, remembers context ✅
- `jarvis history` → Shows past conversations ✅
- `jarvis chat --resume` → Continues last conversation ✅
- Voice mode → Persists entire voice session ✅
- Follow-up questions work: "What is 15*7?" → "Multiply that by 2" ✅

---

### Session: MCP Integration

#### Task: MCP Integration with langchain-mcp-adapters
**Time:** ~30 minutes
**Status:** ✅ Complete

**What was done:**
1. Updated pyproject.toml with MCP dependencies
2. Installed langchain-mcp-adapters (v0.2.1) and dependencies
3. Created `mcp_loader.py` with JSON config loading and env var substitution
4. Created default `mcp_servers.json` with Exa MCP server
5. Updated `graph.py` with async agent creation and MCP tool loading
6. Updated `cli.py` with --mcp flag and mcp-status command
7. Fixed CLI subcommand handling (subcommands vs positional args conflict)
8. Fixed MCP adapters API change (no longer uses context manager)
9. Tested MCP tool loading and usage

---

#### Task: Search Guardrails (DuckDuckGo vs Exa)
**Time:** ~15 minutes
**Status:** ✅ Complete

**What was done:**
1. Removed built-in `deep_search` (redundant with Exa MCP)
2. Updated `web_search` tool description to emphasize FREE/FIRST
3. Updated system prompt with STRICT search rules
4. Tested guardrails work correctly

**Files modified:**
- `src/jarvis/agent/tools.py` - Removed deep_search, updated web_search description
- `src/jarvis/agent/graph.py` - Added strict search rules to prompt
- `src/jarvis/agent/__init__.py` - Removed deep_search export

**Search Guardrails:**
```
1. ALWAYS use web_search (DuckDuckGo) FIRST - it's FREE
2. Use Exa MCP tools ONLY when:
   - User says "deep search", "research", "detailed info"
   - User asks about CODE → code_search_exa
   - User asks about COMPANY → company_research_exa
   - DuckDuckGo results are clearly insufficient
3. NEVER use Exa for simple queries (weather, basic facts)
```

**Test Results:**
| Query | Tool Used | Status |
|-------|-----------|--------|
| "weather today" | DuckDuckGo | ✅ Free |
| "weather today" (--mcp) | DuckDuckGo | ✅ Free |
| "python async examples github" | Exa code_search | ✅ |
| "research OpenAI company" | Exa company_research | ✅ |
| "deep search quantum computing" | Exa web_search | ✅ |

**Usage:**
```bash
jarvis --mcp ask "what is the weather"        # Uses DuckDuckGo (free)
jarvis --mcp ask "find react hooks examples"  # Uses Exa code search
jarvis --mcp ask "research about Tesla"       # Uses Exa company research
jarvis --mcp ask "deep search AI trends"      # Uses Exa web search
```

---

#### Task: README, Configuration System, Error Handling
**Time:** ~20 minutes
**Status:** ✅ Complete

**What was done:**
1. Created comprehensive README.md with setup instructions
2. Created config.py with YAML configuration loading
3. Created default config.yaml with all settings
4. Created errors.py with custom exceptions and utilities
5. Updated CLI with new commands: status, config
6. Added Ollama status check before running queries
7. Improved error messages throughout

**Files created:**
- `README.md` - Full documentation
- `src/jarvis/config.py` - Configuration management
- `data/config.yaml` - Default configuration
- `src/jarvis/utils/errors.py` - Error handling utilities

**Files modified:**
- `src/jarvis/cli.py` - Added status, config commands, error handling
- `src/jarvis/utils/__init__.py` - Added error exports

**New CLI Commands:**
```bash
jarvis status    # Show dependencies and configuration
jarvis config    # Show config file contents
jarvis --verbose # Enable verbose error output
```

**Configuration Options (data/config.yaml):**
- model.name, model.temperature
- voice.stt_model, voice.stt_language, voice.hotkey
- voice.tts_voice, voice.tts_speed
- mcp.enabled, mcp.config_path
- verbose, log_file

---

### Session: Deep Search Integration

#### Task: Hybrid Search System (DuckDuckGo + Exa)
**Time:** ~15 minutes
**Status:** ✅ Complete

**What was done:**
1. Researched Exa API capabilities (semantic/neural search, 2000 free/month)
2. Created `.env` file with EXA_API_KEY
3. Installed `exa-py` and `python-dotenv` dependencies
4. Created `deep_search.py` module with Exa integration
5. Fixed API parameter change (`type="neural"` → `type="auto"`)
6. Added `deep_search` tool to `tools.py`
7. Updated system prompt in `graph.py` for hybrid search guidance
8. Tested both web_search and deep_search work correctly

**Files created:**
- `.env` - Environment variables with Exa API key
- `src/jarvis/features/deep_search.py` - Exa deep search module

**Files modified:**
- `src/jarvis/agent/tools.py` - Added deep_search tool
- `src/jarvis/agent/graph.py` - Updated system prompt for search tool selection

**How hybrid search works:**
- `web_search` (DuckDuckGo): Free, unlimited, for quick/simple queries
- `deep_search` (Exa): 2000/month free, for complex research queries
- LLM decides based on: user says "deep search/research" or results seem insufficient

**Test Results:**
- `jarvis "what is the weather"` → Uses web_search ✅
- `jarvis "deep search latest AI news"` → Uses deep_search ✅
- Exa returns rich content with highlights and summaries ✅

---

### Session: Initial Planning & Documentation Setup

#### Task: Multi-Agent Planning Debate
**Time:** ~45 minutes
**Status:** ✅ Complete

**What was done:**
- Spawned 7 Opus agents for parallel research and debate
- Agent Alpha: Researched 12+ existing projects
- Agent Beta: Designed technical architecture
- Agent Gamma: Defined feature priorities
- Agent Delta: Analyzed risks
- Agent Epsilon: Critical review, found contradictions
- Agent Zeta: Devil's advocate, challenged assumptions
- Agent Omega: Synthesized final consensus

**Files created:**
- `planning/01_research_alpha.md`
- `planning/02_architecture_beta.md`
- `planning/03_features_gamma.md`
- `planning/04_risks_delta.md`
- `planning/05_debate_epsilon.md`
- `planning/06_devils_advocate_zeta.md`
- `planning/07_FINAL_CONSENSUS.md`

**Key findings:**
- No single existing project does what JARVIS needs
- Ollama + LangGraph is the right stack
- ChromaDB preferred over LanceDB for community support
- Voice is essential (user requirement)
- 7B model only due to VRAM constraints

---

#### Task: User Feedback Integration
**Time:** ~10 minutes
**Status:** ✅ Complete

**What was done:**
- User requested LangGraph (agent framework)
- User requested voice in v1 (not deferred)
- User requested incremental phases
- Searched for KreoSphere (not found)
- Found Clawdbot/Moltbot as reference
- Found local-talking-llm as reference

**Decisions made:**
- LangGraph added to stack
- Voice moved to v1
- Phases restructured with testable checkpoints

---

#### Task: Documentation System Setup
**Time:** ~15 minutes
**Status:** ✅ Complete

**What was done:**
- Created lean documentation structure
- Established rules for maintaining docs
- Created persistent memory system

**Files created:**
- `CLAUDE.md` - Rules and references
- `docs/PRD.md` - Product requirements
- `docs/IMPLEMENTATION_PLAN.md` - Technical plan
- `docs/CONTEXT.md` - Current state tracking
- `docs/CHANGELOG.md` - This file

**Files updated:**
- `planning/07_FINAL_CONSENSUS.md` - Revised with new decisions

---

### End of Session Summary

**Completed:**
- Full planning phase with agent debate
- Documentation system established
- Ready for implementation

**Next session:**
1. Create project structure
2. Pass Gate 1 (LangGraph + Ollama)
3. Build Phase 1 (Core Agent)

**Blockers:** None

---

---

#### Task: Phase 0 - Environment Setup
**Time:** ~10 minutes
**Status:** ✅ Complete

**What was done:**
1. Verified Python 3.14.0 installed
2. Installed Ollama 0.15.2 via winget
3. Pulled qwen2.5:7b-instruct model (4.7 GB)
4. Tested model response: "Hello there!"
5. Verified VRAM usage: ~6.5 GB (within 8 GB budget)

**Environment details:**
- Ollama path: `C:\Users\loots\AppData\Local\Programs\Ollama\ollama.exe`
- Model: qwen2.5:7b-instruct (4.7 GB)
- VRAM with model loaded: ~7.9 GB / 12.3 GB

**Notes:**
- Ollama not in PATH by default, need full path or restart terminal
- VRAM usage higher than expected (6.5 GB vs 5 GB estimate) but still within budget

---

#### Task: Phase 3 - Voice Input (Attempt 1: Vosk)
**Time:** ~15 minutes
**Status:** ❌ Failed - Poor Hinglish support

**What was done:**
1. Attempted faster-whisper - failed due to Python 3.14 incompatibility (PyAV Cython issue)
2. Switched to Vosk as workaround
3. Downloaded vosk-model-small-en-in-0.4 (Indian English, 36MB)
4. Implemented STT module with Vosk
5. Tested - Vosk couldn't handle Hinglish at all ("kya chal raha hai" → "risk")

**Problem:** Vosk Indian-English model only handles English with Indian accent, not Hindi words.

---

#### Task: Phase 4 - Voice Output (Kokoro TTS)
**Time:** ~20 minutes
**Status:** ✅ Complete (with limitations)

**What was done:**
1. Installed kokoro-onnx package
2. Initially downloaded wrong model files from HuggingFace (onnx-community) - caused pickle error
3. Found correct files from kokoro-onnx GitHub releases:
   - `kokoro-v1.0.onnx` (310MB)
   - `voices-v1.0.bin` (27MB)
4. Implemented TTS module with Kokoro
5. Integrated TTS into voice mode - JARVIS now speaks responses
6. Fixed phoneme length limit error (split long text into sentences)
7. Updated system prompt to respond in English only (Kokoro is English TTS)

**Files created:**
- `src/jarvis/voice/tts.py` - Kokoro TTS wrapper
- `models/kokoro/kokoro-v1.0.onnx` - TTS model
- `models/kokoro/voices-v1.0.bin` - Voice embeddings

**Files modified:**
- `src/jarvis/voice/__init__.py` - Added TTS exports
- `src/jarvis/cli.py` - Added TTS to voice mode
- `src/jarvis/agent/graph.py` - Added "respond in English only" to prompt

**Known Limitations:**
- Kokoro is English-only TTS (Hindi responses won't work)
- Long text causes phoneme overflow - now handled by sentence splitting
- Voice quality is good but robotic compared to cloud TTS

**Test Results:**
- English responses: ✅ Works well
- Hindi input → English response → TTS: ✅ Works
- Long responses: ✅ Handled by sentence splitting

---

#### Task: Phase 3 - Voice Input (Attempt 2: Python 3.12 + faster-whisper)
**Time:** ~30 minutes
**Status:** ✅ Complete

**What was done:**
1. Installed Python 3.12 via winget (kept 3.14 for other projects)
2. Recreated venv with Python 3.12
3. Installed faster-whisper successfully
4. Hit CUDA error: `cublas64_12.dll not found`
5. Installed nvidia-cublas-cu12 via pip - still failed (DLLs not in PATH)
6. Installed CUDA 13.1 toolkit via winget - still failed (provides cublas64_13.dll, not 12)
7. **Fixed:** Added pip-installed CUDA 12 DLLs to PATH at runtime in stt.py
8. Tested with Whisper large-v3-turbo on GPU - works!

**Files created/modified:**
- `src/jarvis/voice/stt.py` - Rewritten for faster-whisper with CUDA PATH fix
- `src/jarvis/voice/audio.py` - Hotkey and push-to-talk
- `src/jarvis/cli.py` - Added --voice flag

**Dependencies installed:**
- faster-whisper
- sounddevice
- pynput
- nvidia-cublas-cu12
- nvidia-cudnn-cu12

**CUDA PATH Fix (critical):**
```python
# In stt.py - adds pip-installed CUDA 12 DLLs to PATH
site_packages = Path(".venv/Lib/site-packages")
cuda_path = site_packages / "nvidia" / "cublas" / "bin"
os.environ["PATH"] = str(cuda_path) + os.pathsep + os.environ.get("PATH", "")
```

**Test Results:**
- English: ✅ Perfect ("Hello Jarvis, what's happening?")
- Hindi: ✅ ~70-80% accurate, outputs in Devanagari script
- Hinglish code-switching: 🟡 Works but sometimes fumbles

**Notes:**
- Using `language="hi"` for better Hinglish handling
- Model: large-v3-turbo (~1.5GB VRAM)
- GPU acceleration working on RTX 4070

---

#### Task: Phase 2 - Tools
**Time:** ~20 minutes
**Status:** ✅ Complete

**What was done:**
1. Implemented all 6 tools:
   - `calculator` - Math operations (already done)
   - `reminder_set` - Create reminders with time parsing
   - `reminder_list` - List pending reminders
   - `note_save` - Save notes as markdown
   - `note_search` - Search notes with keyword matching
   - `web_search` - DuckDuckGo search
2. Implemented Windows toast notifications
3. Background reminder checker thread
4. Fixed BM25 issue (IDF=0 with few docs) - using keyword search

**Files created:**
- `src/jarvis/features/reminders.py`
- `src/jarvis/features/notes.py`
- `src/jarvis/features/search.py`
- `src/jarvis/utils/notifications.py`

**Files modified:**
- `src/jarvis/agent/tools.py` - Added all new tools
- `src/jarvis/agent/graph.py` - Updated system prompt
- `src/jarvis/agent/__init__.py` - Added exports

**Checkpoint Test Results:**
- `jarvis "remind me to take a break in 30s"` → Sets reminder ✅
- `jarvis "list my reminders"` → Shows pending reminders ✅
- `jarvis "save a note: buy milk"` → Saves note ✅
- `jarvis "search notes for milk"` → Finds note ✅
- `jarvis "search web for weather"` → Returns DuckDuckGo results ✅
- Notification fires when reminder is due ✅

**Dependencies added:**
- httpx (already installed via langsmith)
- rank_bm25 0.2.2 (not used currently due to IDF issue)

**Notes:**
- BM25 IDF returns 0 with <3 documents (math issue)
- Switched to simple keyword search for now
- Reminders persist in `data/reminders.json`
- Notes saved as markdown in `data/notes/`

---

#### Task: Phase 1 - Core Agent
**Time:** ~15 minutes
**Status:** ✅ Complete

**What was done:**
1. Created project structure (`src/jarvis/` with all submodules)
2. Created `pyproject.toml` with dependencies
3. Created virtual environment and installed dependencies
4. Implemented LangGraph agent with calculator tool
5. Implemented CLI interface with Click
6. Fixed API compatibility (state_modifier → prompt)
7. Suppressed Python 3.14 Pydantic warning
8. Tested all functionality

**Files created:**
- `pyproject.toml`
- `src/jarvis/__init__.py`
- `src/jarvis/__main__.py`
- `src/jarvis/cli.py`
- `src/jarvis/agent/__init__.py`
- `src/jarvis/agent/graph.py`
- `src/jarvis/agent/tools.py`
- `src/jarvis/voice/__init__.py`
- `src/jarvis/features/__init__.py`
- `src/jarvis/utils/__init__.py`

**Checkpoint Test Results:**
- `jarvis "15 * 7"` → "The result of 15 * 7 is 105." ✅
- `jarvis "2 + 2"` → "The result of 2 + 2 is 4." ✅
- `jarvis "square root of 144"` → "The square root of 144 is 12." ✅
- `jarvis calc "100 / 4"` → "25" ✅
- `jarvis "hello"` → "I'm JARVIS, your personal assistant..." ✅

**Issues fixed:**
- LangGraph API changed: `state_modifier` → `prompt`
- Click CLI: Fixed subcommand handling with `nargs=-1`

**Dependencies installed:**
- langgraph 1.0.7
- langchain-ollama 1.0.1
- langchain-core 1.2.7
- click 8.3.1

---

#### Task: Senior Dev Improvements Integration
**Time:** ~5 minutes
**Status:** ✅ Complete

**What was done:**
- Evaluated 4 improvements suggested by senior dev
- Verified Kokoro-82M exists (kokoro-onnx on PyPI, v0.4.9)
- Accepted all 4 improvements

**Improvements integrated:**
1. **Kokoro-82M TTS** replaces Piper - smaller (~80MB), ONNX/CPU, Apache 2.0
2. **BM25 search** (rank_bm25) replaces grep - handles typos/partial matches
3. **Barge-in interrupt** - threaded audio with stop flag for user interrupts
4. **Hardened system prompt** - brevity guidelines for voice responses

**Files modified:**
- `docs/IMPLEMENTATION_PLAN.md` - Updated dependencies
- `docs/CONTEXT.md` - Added decisions
- `planning/07_FINAL_CONSENSUS.md` - Updated TTS, search, added barge-in

**Notes:**
- Kokoro uses ONNX runtime, CPU-only (frees GPU for LLM/STT)
- BM25 is standard ranking algorithm, lightweight dependency
- Barge-in is architectural pattern, will implement in Phase 4

---

#### Task: Plan Correction - Add Phase 0
**Time:** 2 minutes
**Status:** ✅ Complete

**Problem identified:**
- Implementation plan jumped to code without environment setup
- Missing: Python install, Ollama install, model download

**What was done:**
- Added Phase 0: Environment Setup to IMPLEMENTATION_PLAN.md
- Updated CONTEXT.md with correct phase status
- Updated pending tasks with proper sequence

**Files modified:**
- `docs/IMPLEMENTATION_PLAN.md` - Added Phase 0
- `docs/CONTEXT.md` - Fixed phase status, updated pending tasks

**Lesson learned:**
- Always start with "what needs to be installed/running first"
- Never assume infrastructure exists

---

## Template for Future Entries

```markdown
## [DATE]

### Session: [Brief Description]

#### Task: [Task Name]
**Time:** [Duration]
**Status:** ✅ Complete | 🟡 Partial | 🔴 Blocked

**What was done:**
- [Action 1]
- [Action 2]

**Files created:**
- [file1]

**Files modified:**
- [file2]

**Problems encountered:**
- [Problem]: [Solution or status]

**Notes:**
- [Any relevant observations]
```

---

*Log maintained by Claude*
*Format: Chronological, detailed, searchable*
