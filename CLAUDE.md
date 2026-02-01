# JARVIS Project - Claude Rules

> **MANDATORY:** Read this file at the start of EVERY session.

---

## Quick Context

**Project:** JARVIS - Local voice AI assistant
**Hardware:** RTX 4070 12GB, Ryzen 9800X3D, 32GB RAM, Windows
**Stack:** LangGraph + Ollama + faster-whisper (large-v3-turbo) + Kokoro-82M
**Python:** 3.12 (not 3.14 - compatibility issues)

---

## Documentation Structure

| File | Purpose | When to Update |
|------|---------|----------------|
| `docs/PRD.md` | Product requirements, features, scope | When requirements change |
| `docs/IMPLEMENTATION_PLAN.md` | Technical plan, phases, architecture | When approach changes |
| `docs/CONTEXT.md` | Current state, decisions, problems | **Every session** |
| `docs/CHANGELOG.md` | Detailed log of all work done | **After every task** |
| `planning/` | Research docs from agent debate | Reference only |

---

## Mandatory Rules

### Rule 1: Session Start
```
1. Read CLAUDE.md (this file)
2. Read docs/CONTEXT.md for current state
3. Check docs/CHANGELOG.md for last activity
4. Resume from last checkpoint
```

### Rule 2: After Every Task
```
1. Update docs/CHANGELOG.md with:
   - What was done
   - Files created/modified
   - Problems encountered
   - Solutions applied

2. Update docs/CONTEXT.md if:
   - Phase changed
   - Key decision made
   - Blocker encountered
   - Architecture changed
```

### Rule 3: After Every Session
```
1. Ensure CONTEXT.md reflects current state
2. Ensure CHANGELOG.md has all work logged
3. Note any pending tasks or blockers
```

### Rule 4: Code Changes
```
1. Test before committing
2. Log in CHANGELOG.md
3. Update phase status in CONTEXT.md
```

### Rule 5: Problem Encountered
```
1. Document in CONTEXT.md under "Active Problems"
2. Log attempts in CHANGELOG.md
3. If solved, move to "Solved Problems" with solution
```

---

## Key Constraints (Never Violate)

1. **VRAM Budget:** Never exceed 8GB total
2. **Local Only:** No cloud API dependencies (except optional fallback)
3. **Push-to-Talk:** No wake word / always listening
4. **No Plugins:** Build features directly
5. **Testable Phases:** Each phase must have a checkpoint

---

## Tech Stack (Locked)

| Component | Choice | VRAM |
|-----------|--------|------|
| Agent | LangGraph | - |
| LLM | Ollama + Qwen2.5-7B-Q4 | ~5 GB |
| STT | faster-whisper large-v3-turbo | ~1.5 GB |
| TTS | Kokoro-82M (ONNX, English-only) | ~0.3 GB |
| Audio | sounddevice + pynput | - |
| Search | keyword (BM25 later) | - |
| Python | 3.12 (not 3.14) | - |
| **Total VRAM** | | **~7 GB** |

---

## Current Phase

**Check `docs/CONTEXT.md` for current phase and status.**

---

## File Templates

When creating new source files, use:
```python
"""
JARVIS - [Module Name]
[Brief description]
"""
```

When logging to CHANGELOG:
```markdown
## [Date] - [Time]
### Task: [What was done]
- Files: [list]
- Status: [Complete/Partial/Blocked]
- Notes: [Any relevant info]
```

---

*Last Updated: February 1, 2026*
