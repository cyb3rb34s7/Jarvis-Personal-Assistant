# JARVIS - Current Context

> **UPDATE THIS FILE EVERY SESSION**

---

## Current Status

| Aspect | Value |
|--------|-------|
| **Current Phase** | Phase 5 - Polish & MCP Integration |
| **Phase Status** | 🟡 In Progress |
| **Last Activity** | Memory system implemented (SQLite + session context) |
| **Blockers** | None |
| **Next Task** | GUI backend (FastAPI), stability testing |

---

## Phase Progress

| Phase | Status | Checkpoint |
|-------|--------|------------|
| Phase 0: Environment | ✅ Complete | `ollama run qwen2.5:7b-instruct "hello"` → "Hello there!" |
| Phase 1: Core Agent | ✅ Complete | `jarvis "15 * 7"` → "105" |
| Phase 2: Tools | ✅ Complete | Reminder fires notification |
| Phase 3: Voice Input | ✅ Complete | Speech → text works (Whisper) |
| Phase 4: Voice Output | ✅ Complete | Full voice loop (Kokoro TTS) |
| Phase 5: Polish | ⬜ Not Started | 30 min no crashes |

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

*List files touched in current session*

- `src/jarvis/database.py` - **NEW** SQLite setup with conversations, messages, user_facts tables
- `src/jarvis/memory/__init__.py` - **NEW** Memory module exports
- `src/jarvis/memory/session.py` - **NEW** Session memory with safe sliding window
- `src/jarvis/agent/graph.py` - Added session memory integration, history injection
- `src/jarvis/cli.py` - Added `chat` and `history` commands, session support in voice mode
- `data/jarvis.db` - **NEW** SQLite database file (auto-created)

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

**Phase 5: Polish & MCP Integration** ← CURRENT
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
    - SQLite database with conversations, messages, user_facts tables
    - SessionMemory class with safe sliding window (no tool call/response split)
    - 20-message context window (configurable)
    - `jarvis chat` - Interactive session with memory
    - `jarvis history` - View past conversations
    - Voice mode now persists conversation context

---

## Notes for Next Session

- Phase 1-4 complete - full voice loop working!
- STT: Whisper large-v3-turbo on GPU, Hinglish ~70-80%
- TTS: Kokoro English-only, responses forced to English
- Deep search (Exa) integrated via direct API
- **MCP Integration complete:**
  - `langchain-mcp-adapters` v0.2.1 installed
  - JSON config file (`data/mcp_servers.json`) for easy MCP management
  - Agent converted to async for MCP compatibility
  - Exa MCP working (3 tools: web_search, code_search, company_research)
  - Use `jarvis --mcp ask "query"` to enable MCP tools
  - Use `jarvis mcp-status` to see configured servers
- **Memory System complete:**
  - SQLite database at `data/jarvis.db`
  - Conversations and messages stored persistently
  - Safe sliding window (never splits tool call/response pairs)
  - Use `jarvis chat` for interactive sessions with memory
  - Use `jarvis chat --resume` to continue last conversation
  - Use `jarvis history` to view past conversations
  - Voice mode automatically uses session memory
- **GUI Plan finalized** at `docs/GUI_PLAN.md`
  - Architecture: Local Agent + Cloudflare Tunnel (no custom gateway)
  - Repo structure: `src/jarvis/api/` (FastAPI) + `ui/` (Next.js)
  - Security: Bearer token auth
  - Remote latency: Optimistic UI pattern
- **Next: Phase A - FastAPI Backend**
  - Create `src/jarvis/api/` structure
  - Implement REST + WebSocket endpoints
  - Integrate with existing agent/memory
  - Add `jarvis serve` command
- Future improvements:
  - Hindi TTS (find multilingual TTS)
  - Better Hinglish STT accuracy
  - Long-term memory (user facts extraction)

---

*Last Updated: January 29, 2026*
*Session: Architecture Finalized, Ready for Phase A*
