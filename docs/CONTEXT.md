# JARVIS - Current Context

> **UPDATE THIS FILE EVERY SESSION**

---

## Current Status

| Aspect | Value |
|--------|-------|
| **Current Phase** | GUI Implementation - Phase A Complete |
| **Phase Status** | 🟡 In Progress |
| **Last Activity** | Voice mode stability fixes (model loading, MCP async) |
| **Blockers** | None |
| **Next Task** | Phase B - Next.js frontend |

---

## Phase Progress

| Phase | Status | Checkpoint |
|-------|--------|------------|
| Phase 0: Environment | ✅ Complete | `ollama run qwen2.5:7b-instruct "hello"` → "Hello there!" |
| Phase 1: Core Agent | ✅ Complete | `jarvis "15 * 7"` → "105" |
| Phase 2: Tools | ✅ Complete | Reminder fires notification |
| Phase 3: Voice Input | ✅ Complete | Speech → text works (Whisper) |
| Phase 4: Voice Output | ✅ Complete | Full voice loop (Kokoro TTS) |
| Phase 5: Polish | ✅ Complete | MCP + Memory + Config done |
| GUI Phase A: Backend | ✅ Complete | FastAPI server works |
| GUI Phase B: Frontend | ⬜ Not Started | Next.js + shadcn/ui |
| GUI Phase C: WebSocket | ⬜ Not Started | Real-time chat |
| GUI Phase D: Voice | ⬜ Not Started | Browser recording |
| GUI Phase E: Tunnel | ⬜ Not Started | Cloudflare setup |

**Legend:** ✅ Complete | 🟡 In Progress | ⬜ Not Started | 🔴 Blocked

---

## Key Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-29 | Use LangGraph | Proper agent loops, tool calling built-in |
| 2026-01-29 | Voice in v1 | User priority, not deferred |
| 2026-01-29 | ChromaDB over LanceDB | Better community support |
| 2026-01-29 | 7B model only | VRAM constraints |
| 2026-01-29 | No plugin system | Build features directly |
| 2026-01-29 | CLI first | Faster iteration |
| 2026-01-29 | Kokoro-82M over Piper | Smaller (~80MB), ONNX/CPU, simpler API |
| 2026-01-29 | BM25 for note search | Fuzzy matching, handles typos |
| 2026-01-29 | Barge-in interrupt | Essential UX for voice assistants |
| 2026-01-29 | Hardened system prompt | Brevity for voice, faster responses |
| 2026-01-29 | Python 3.12 over 3.14 | faster-whisper/PyAV incompatible with 3.14 |
| 2026-01-29 | faster-whisper over Vosk | Vosk couldn't handle Hinglish at all |
| 2026-01-29 | Whisper large-v3-turbo | Best Hinglish support, ~1.5GB VRAM |
| 2026-01-29 | language="hi" for STT | Handles Hinglish code-switching better |
| 2026-01-29 | Kokoro TTS (English only) | Best offline TTS, but no Hindi support |
| 2026-01-29 | LLM responds in English only | Required for Kokoro TTS compatibility |
| 2026-01-29 | Hybrid search: DuckDuckGo + Exa | Free tier for normal, deep search when needed |
| 2026-01-29 | MCP integration via langchain-mcp-adapters | Extensible, JSON config, no code changes to add tools |
| 2026-01-29 | Search guardrails: DDG first, Exa for complex | Saves Exa quota, free for simple queries |
| 2026-01-29 | SQLite for memory, not LangGraph checkpointer | Manual control, clean sliding window, no tool call/response split |
| 2026-01-29 | 20-message context window | Balance between memory usage and context relevance |
| 2026-01-29 | Cloudflare Tunnel over custom gateway | Free, secure, zero maintenance, no WebSocket debugging |
| 2026-01-29 | Local agent + remote UI | GPU stays local, access from anywhere via tunnel |
| 2026-01-29 | Bearer token auth for API | Simple, works with tunnel, optional for local dev |
| 2026-01-29 | Optimistic UI for remote latency | Show "Processing..." immediately, don't wait for server |

---

## Active Problems

*None currently*

<!-- Template:
### Problem: [Title]
**Status:** Investigating / Attempted / Blocked
**Description:** [What's wrong]
**Attempts:**
1. [What was tried]
2. [What was tried]
**Current Theory:** [Best guess]
-->

---

## Solved Problems

### Problem: Python 3.14 incompatible with faster-whisper
**Solution:** Installed Python 3.12 via winget, recreated venv
**Date Solved:** 2026-01-29
**Lesson:** Bleeding-edge Python versions often have Cython/native extension issues

### Problem: Vosk couldn't understand Hinglish
**Solution:** Switched to faster-whisper with Whisper large-v3-turbo
**Date Solved:** 2026-01-29
**Lesson:** Vosk models are language-specific, Whisper is multilingual

### Problem: CUDA cublas64_12.dll not found
**Solution:** Added pip-installed CUDA 12 DLLs to PATH at runtime in stt.py
**Date Solved:** 2026-01-29
**Lesson:** pip nvidia-* packages install DLLs but don't add to PATH; CUDA 13 toolkit doesn't include CUDA 12 libs

### Problem: Kokoro TTS pickle error with HuggingFace voice files
**Solution:** Downloaded correct model files from kokoro-onnx GitHub releases instead of onnx-community HuggingFace
**Date Solved:** 2026-01-29
**Lesson:** Always use model files from the package author's official releases

### Problem: Kokoro phoneme overflow on long text
**Solution:** Split text into sentences before TTS, truncate sentences >400 chars
**Date Solved:** 2026-01-29
**Lesson:** Kokoro has ~510 phoneme limit; handle long text gracefully

### Problem: Models loaded lazily, bad voice UX
**Solution:** Add preload methods, load all models at startup before user prompt
**Date Solved:** 2026-02-02
**Lesson:** Load LLM first (needs contiguous VRAM), then TTS, then STT

### Problem: MCP tools fail with "StructuredTool does not support sync invocation"
**Solution:** Use `run_agent_async()` with `loop.run_until_complete()` for MCP voice mode
**Date Solved:** 2026-02-02
**Lesson:** MCP tools are async-only; can't use sync agent with MCP tools

### Problem: MCP fails with "Event loop is closed" on second query
**Solution:** Use persistent event loop instead of `asyncio.run()` for MCP voice mode
**Date Solved:** 2026-02-02
**Lesson:** `asyncio.run()` closes loop; MCP connections are tied to the loop

### Problem: MCP tool content is list, SQLite can't store
**Solution:** Convert list to string with `"\n".join()` before saving
**Date Solved:** 2026-02-02
**Lesson:** Always serialize complex types before database storage

### Problem: Emojis cause Windows encoding errors
**Solution:** Replace emojis with ASCII equivalents in terminal output
**Date Solved:** 2026-02-02
**Lesson:** Windows console uses limited charset; avoid emojis in CLI apps

<!-- Template:
### Problem: [Title]
**Solution:** [What fixed it]
**Date Solved:** [Date]
**Lesson:** [What we learned]
-->

---

## Environment Info

| Item | Value |
|------|-------|
| Python | 3.12.10 ✅ (switched from 3.14 for faster-whisper compatibility) |
| Ollama | 0.15.2 ✅ |
| Ollama Path | `C:\Users\loots\AppData\Local\Programs\Ollama\ollama.exe` |
| LLM Model | qwen2.5:7b-instruct (4.7 GB) ✅ |
| STT Model | Whisper large-v3-turbo (~1.5 GB VRAM) ✅ |
| CUDA | 13.1 installed, using pip CUDA 12 libs for faster-whisper |
| VRAM Used | ~8 GB (LLM + Whisper loaded) |
| VRAM Budget | 8 GB max |
| VRAM Available | 12.3 GB total |

---

## Files Modified This Session

*List files touched in current session (2026-02-02)*

- `src/jarvis/cli.py` - Model preloading, persistent event loop for MCP, loading order fix
- `src/jarvis/voice/tts.py` - Added `preload()` method
- `src/jarvis/voice/stt.py` - Added `preload_stt()` function
- `src/jarvis/voice/__init__.py` - Export `preload_stt`
- `src/jarvis/voice/audio.py` - Replace emojis with ASCII
- `src/jarvis/agent/graph.py` - Convert MCP tool content to string for SQLite

---

## Pending Tasks

**Phase 0: Environment Setup** ✅ COMPLETE
1. [x] Install Python 3.11+ → 3.14.0
2. [x] Install Ollama → 0.15.2
3. [x] Start Ollama service → Running
4. [x] Pull Qwen2.5-7B model → 4.7 GB
5. [x] Verify model runs → "Hello there!"
6. [x] Check VRAM usage → ~6.5 GB (within budget)

**Phase 1: Core Agent** ✅ COMPLETE
1. [x] Create `src/` directory structure
2. [x] Create `pyproject.toml`
3. [x] Install dependencies (langgraph, langchain-ollama)
4. [x] Pass Gate 1 (LangGraph + Ollama tool calling)
5. [x] Build CLI with calculator tool
6. [x] Test checkpoint: `jarvis "15 * 7"` → 105

**Phase 2: Tools** ✅ COMPLETE
1. [x] Implement reminder_set tool
2. [x] Implement reminder_list tool
3. [x] Implement note_save tool
4. [x] Implement note_search tool (keyword search)
5. [x] Implement web_search tool
6. [x] Implement Windows notifications
7. [x] Test checkpoint: reminder fires notification

**Phase 3: Voice Input** ✅ COMPLETE
1. [x] Switch to Python 3.12 (3.14 incompatible with faster-whisper)
2. [x] Install faster-whisper with CUDA support
3. [x] Fix CUDA PATH issue (cublas64_12.dll)
4. [x] Implement STT wrapper with Whisper large-v3-turbo
5. [x] Implement audio capture (sounddevice)
6. [x] Implement hotkey listener (pynput) - Ctrl+Space
7. [x] Test checkpoint: speech → text ✅
   - English: Perfect
   - Hindi: ~70-80% accurate (Devanagari output)
   - Hinglish: Works but sometimes fumbles

**Phase 4: Voice Output** ✅ COMPLETE
1. [x] Install Kokoro TTS (kokoro-onnx)
2. [x] Download correct model files from GitHub releases
3. [x] Implement TTS wrapper with sentence splitting
4. [x] Integrate with voice mode
5. [x] Test checkpoint: JARVIS speaks responses ✅
   - English: Works well
   - Limitation: English-only TTS

**Phase 5: Polish & MCP Integration** ✅ COMPLETE
1. [x] Install langchain-mcp-adapters ✅
2. [x] Create MCP config loader (`mcp_loader.py`) ✅
3. [x] Create default `mcp_servers.json` ✅
4. [x] Convert agent to async ✅
5. [x] Update CLI for async ✅
6. [x] Test with Exa MCP ✅ (3 tools loaded)
7. [ ] Test with GitHub MCP (optional - needs GITHUB_TOKEN)
8. [x] Configuration system (YAML config file) ✅
9. [x] Error handling improvements ✅
10. [ ] Logging system (optional)
11. [ ] Stability testing (30 min no crashes) ← USER TESTING
12. [x] README documentation ✅
13. [x] Memory system (SQLite + session context) ✅

**GUI Phase A: FastAPI Backend** ✅ COMPLETE
1. [x] Create `src/jarvis/api/` structure
2. [x] Implement auth.py (Bearer token)
3. [x] Implement deps.py (shared dependencies)
4. [x] Implement routes/status.py (health, status)
5. [x] Implement routes/conversations.py (CRUD)
6. [x] Implement routes/chat.py (POST + WebSocket)
7. [x] Implement routes/reminders.py (CRUD)
8. [x] Implement routes/notes.py (CRUD + search)
9. [x] Implement routes/mcp.py (servers, tools, reload)
10. [x] Implement routes/voice.py (transcribe, synthesize)
11. [x] Add TTS synthesize() method (returns WAV bytes)
12. [x] Add STT transcribe_file() method
13. [x] Add CLI `serve` command
14. [x] Test all endpoints ✅
15. [x] Commit and push to GitHub ✅

**GUI Phase B: Next.js Frontend** ← NEXT
1. [ ] Create `ui/` folder with Next.js 14
2. [ ] Install shadcn/ui components
3. [ ] Create chat interface layout
4. [ ] Implement message list component
5. [ ] Implement input area with send button
6. [ ] Connect to /api/v1/chat endpoint
7. [ ] Display conversation history
8. [ ] Implement optimistic UI (show "Processing..." immediately)

---

## Notes for Next Session

- Phase 1-5 complete - full voice loop + memory + MCP working!
- STT: Whisper large-v3-turbo on GPU, Hinglish ~70-80%
- TTS: Kokoro English-only, responses forced to English
- **Voice Mode Stability Fixes (2026-02-02):**
  - Models preload at startup (LLM → TTS → STT order)
  - MCP uses persistent event loop (fixes "Event loop is closed")
  - MCP tool content converted to string (fixes SQLite error)
  - Emojis replaced with ASCII (fixes Windows encoding)
- **MCP Integration complete:**
  - `langchain-mcp-adapters` v0.2.1 installed
  - Use `jarvis --mcp --voice` for voice with MCP tools
  - Exa tools working: web_search, code_search, company_research
- **Memory System complete:**
  - SQLite database at `data/jarvis.db`
  - Safe sliding window (never splits tool call/response pairs)
- **GUI Phase A (Backend) complete:**
  - FastAPI at `src/jarvis/api/`
  - All endpoints working
  - `jarvis serve` command to start server
- **Next: Phase B - Next.js Frontend**
  - Create `ui/` folder with Next.js 14 + shadcn/ui
  - Implement chat interface with message history
  - Connect to FastAPI backend
- Future improvements:
  - Hindi TTS (find multilingual TTS)
  - Better Hinglish STT accuracy

---

*Last Updated: February 2, 2026*
*Session: Voice Mode Stability Fixes*
