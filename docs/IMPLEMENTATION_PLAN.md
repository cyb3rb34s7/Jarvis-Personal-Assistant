# JARVIS - Implementation Plan

**Version:** 1.1
**Date:** January 29, 2026

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          JARVIS Core                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  INPUT LAYER                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────┐            │
│  │   Hotkey    │───►│  Microphone │───►│  Silero VAD  │            │
│  │  (pynput)   │    │ (sounddevice)│    │              │            │
│  └─────────────┘    └─────────────┘    └──────┬───────┘            │
│                                                │                    │
│  ┌─────────────────────────────────────────────▼───────┐            │
│  │              faster-whisper (STT) ~1.5GB VRAM       │            │
│  └─────────────────────────────────────────────────────┘            │
│                            │                                        │
│  AGENT LAYER               ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    LangGraph Agent (async)                  │   │
│  │  ┌────────────────────────────────────────────────────────┐ │   │
│  │  │  Built-in Tools:          MCP Tools (from JSON config):│ │   │
│  │  │  • calculator             • exa (search, code, company)│ │   │
│  │  │  • reminder_set/list      • github (issues, PRs, repos)│ │   │
│  │  │  • note_save/search       • filesystem (file ops)      │ │   │
│  │  │  • web_search (DDG)       • [any MCP server...]        │ │   │
│  │  │  • deep_search (Exa)                                   │ │   │
│  │  └────────────────────────────────────────────────────────┘ │   │
│  │                         │                                   │   │
│  │  ┌──────────────────────▼─────────────────────────────────┐ │   │
│  │  │         Ollama (Qwen2.5-7B-Instruct) ~5GB VRAM         │ │   │
│  │  └────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                            │                                        │
│  MCP LAYER                 │                                        │
│  ┌─────────────────────────┴───────────────────────────────────┐   │
│  │  langchain-mcp-adapters (MultiServerMCPClient)              │   │
│  │  ┌────────────────────────────────────────────────────────┐ │   │
│  │  │  data/mcp_servers.json  ◄── Edit this to add MCPs      │ │   │
│  │  │  • No code changes needed                              │ │   │
│  │  │  • Supports stdio, HTTP, SSE transports                │ │   │
│  │  │  • Environment variable substitution                   │ │   │
│  │  └────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                            │                                        │
│  OUTPUT LAYER              ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │              Kokoro TTS (CPU/ONNX)                      │        │
│  └─────────────────────────────┬───────────────────────────┘        │
│                                │                                    │
│  ┌─────────────────────────────▼───────────────────────────┐        │
│  │              Speaker (sounddevice)                      │        │
│  └─────────────────────────────────────────────────────────┘        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
D:\PROJECTS\JARVIS\
├── CLAUDE.md                     # Rules for Claude
├── .env                          # API keys (EXA_API_KEY, etc.)
├── docs/
│   ├── PRD.md                    # Product requirements
│   ├── IMPLEMENTATION_PLAN.md    # This file
│   ├── CONTEXT.md                # Current state
│   └── CHANGELOG.md              # Activity log
├── planning/                     # Research (reference)
├── src/
│   └── jarvis/
│       ├── __init__.py
│       ├── __main__.py           # Entry point
│       ├── cli.py                # Click CLI
│       ├── config.py             # Configuration loader
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── graph.py          # LangGraph definition (async)
│       │   ├── tools.py          # Built-in tool implementations
│       │   └── mcp_loader.py     # MCP server loader
│       ├── voice/
│       │   ├── __init__.py
│       │   ├── stt.py            # faster-whisper
│       │   ├── tts.py            # Kokoro
│       │   └── audio.py          # Audio I/O
│       ├── features/
│       │   ├── __init__.py
│       │   ├── notes.py          # Note management
│       │   ├── reminders.py      # Reminder system
│       │   ├── search.py         # DuckDuckGo search
│       │   └── deep_search.py    # Exa deep search
│       └── utils/
│           ├── __init__.py
│           └── notifications.py  # Windows toasts
├── data/
│   ├── notes/                    # User notes
│   ├── reminders.json            # Persistent reminders
│   ├── config.yaml               # User config (voice, hotkey, etc.)
│   └── mcp_servers.json          # MCP server configuration ◄── NEW
├── models/
│   └── kokoro/                   # TTS model files
├── tests/
│   ├── test_agent.py
│   ├── test_tools.py
│   └── test_voice.py
├── pyproject.toml
└── README.md
```

---

## MCP Configuration (JSON-based)

Users add MCP servers by editing `data/mcp_servers.json` - no code changes needed.

### Example Configuration

```json
{
  "mcpServers": {
    "exa": {
      "transport": "http",
      "url": "https://mcp.exa.ai/mcp",
      "headers": {
        "x-api-key": "${EXA_API_KEY}"
      }
    },
    "github": {
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "filesystem": {
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "D:/PROJECTS"]
    }
  }
}
```

### Supported Transports

| Transport | Use Case | Example |
|-----------|----------|---------|
| `http` | Remote/hosted MCP servers | Exa, hosted APIs |
| `stdio` | Local MCP servers (npm packages) | GitHub, filesystem |
| `sse` | Server-sent events | Streaming servers |

### Environment Variable Substitution

Use `${VAR_NAME}` syntax to reference environment variables from `.env`:
- `${EXA_API_KEY}` → reads from `.env`
- `${GITHUB_TOKEN}` → reads from `.env`

---

## Implementation Phases

### Phase 0: Environment Setup ✅ COMPLETE

**Goal:** All prerequisites installed and verified

**Checkpoint Test:**
```bash
ollama run qwen2.5:7b-instruct "say hello"
# Output: Hello! How can I help you today?
```

---

### Phase 1: Core Agent ✅ COMPLETE

**Goal:** Basic LLM chat with tool calling via CLI

**Checkpoint Test:**
```bash
jarvis "what is 15 * 7?"
# Output: 105
```

---

### Phase 2: Tools ✅ COMPLETE

**Goal:** All built-in tools working

**Checkpoint Test:**
```bash
jarvis "remind me to stretch in 1m"
# Notification appears after 1 minute

jarvis "deep search latest AI news"
# Returns rich Exa results
```

**Tools Implemented:**
- `calculator` - Math operations
- `reminder_set` / `reminder_list` - Time-based reminders
- `note_save` / `note_search` - Note management
- `web_search` - DuckDuckGo (free, unlimited)
- `deep_search` - Exa API (2000/month free, semantic search)

---

### Phase 3: Voice Input ✅ COMPLETE

**Goal:** Push-to-talk speech recognition

**Checkpoint Test:**
```bash
jarvis --voice
# Press Ctrl+Space, speak "hello world"
# Terminal shows: "hello world"
```

---

### Phase 4: Voice Output ✅ COMPLETE

**Goal:** TTS responses

**Checkpoint Test:**
```bash
jarvis --voice
# Speak: "what is the capital of France"
# JARVIS speaks: "The capital of France is Paris"
```

---

### Phase 5: Polish & MCP Integration ◄── CURRENT

**Goal:** Production-ready with extensible MCP support

**Checkpoint Tests:**
```bash
# Test 1: Stability
Use JARVIS for 30 minutes without crashes

# Test 2: MCP tools load from config
jarvis "search github for langchain issues"
# Uses GitHub MCP tools

# Test 3: Add new MCP without code changes
Edit mcp_servers.json → restart → new tools available
```

**Tasks:**

| Task | File | Status |
|------|------|--------|
| **MCP Integration** | | |
| Install langchain-mcp-adapters | `pyproject.toml` | ⬜ |
| Create MCP config loader | `src/jarvis/agent/mcp_loader.py` | ⬜ |
| Create default mcp_servers.json | `data/mcp_servers.json` | ⬜ |
| Convert agent to async | `src/jarvis/agent/graph.py` | ⬜ |
| Merge MCP tools with built-in tools | `src/jarvis/agent/graph.py` | ⬜ |
| Update CLI for async | `src/jarvis/cli.py` | ⬜ |
| Test with Exa MCP | - | ⬜ |
| Test with GitHub MCP | - | ⬜ |
| Document MCP setup in README | `README.md` | ⬜ |
| **Polish** | | |
| Configuration system (YAML) | `src/jarvis/config.py` | ⬜ |
| Error handling improvements | All files | ⬜ |
| Logging system | All files | ⬜ |
| Stability testing | - | ⬜ |

**New Dependencies:**
```
langchain-mcp-adapters>=0.1
python-dotenv>=1.0
```

---

## MCP Loader Implementation

### `src/jarvis/agent/mcp_loader.py`

```python
"""Load MCP tools from JSON configuration."""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

# Load .env for API keys
load_dotenv()

CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "data" / "mcp_servers.json"


def substitute_env_vars(obj):
    """Replace ${VAR} with environment variable values."""
    if isinstance(obj, str):
        if obj.startswith("${") and obj.endswith("}"):
            var_name = obj[2:-1]
            return os.getenv(var_name, "")
        return obj
    elif isinstance(obj, dict):
        return {k: substitute_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [substitute_env_vars(item) for item in obj]
    return obj


async def load_mcp_tools():
    """Load all MCP tools from config file."""
    if not CONFIG_PATH.exists():
        return []

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    servers = config.get("mcpServers", {})
    if not servers:
        return []

    # Substitute environment variables
    servers = substitute_env_vars(servers)

    client = MultiServerMCPClient(servers)
    tools = await client.get_tools()

    return tools
```

### Updated `src/jarvis/agent/graph.py` (async)

```python
"""JARVIS - LangGraph agent definition (async with MCP support)."""

import asyncio
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from .tools import ALL_TOOLS, init_tools
from .mcp_loader import load_mcp_tools

SYSTEM_PROMPT = """You are JARVIS, a voice assistant. Rules:
- ALWAYS respond in English only (even if user speaks Hindi/Hinglish)
- Answer in 1-2 sentences max
- No preamble ("Sure!", "Of course!")
- Use tools when needed, report results directly
- For web searches:
  - Use web_search for quick/simple queries
  - Use deep_search for complex research
- If unsure, ask one clarifying question"""


async def create_agent(model: str = "qwen2.5:7b-instruct"):
    """Create and return the JARVIS agent with MCP tools."""
    init_tools()

    # Load MCP tools from config
    mcp_tools = await load_mcp_tools()

    # Combine built-in + MCP tools
    all_tools = ALL_TOOLS + mcp_tools

    llm = ChatOllama(model=model)
    agent = create_react_agent(llm, all_tools, prompt=SYSTEM_PROMPT)

    return agent


async def run_agent(query: str, agent=None) -> str:
    """Run a query through the agent and return the response."""
    if agent is None:
        agent = await create_agent()

    result = await agent.ainvoke({"messages": [("user", query)]})

    messages = result.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.type == "ai":
            return msg.content

    return "No response generated"
```

---

## Dependencies (Complete)

```toml
[project]
name = "jarvis"
version = "0.2.0"
requires-python = ">=3.12"

dependencies = [
    # Agent Framework
    "langgraph>=0.2",
    "langchain-ollama>=0.2",
    "langchain-core>=0.3",

    # MCP Integration
    "langchain-mcp-adapters>=0.1",
    "python-dotenv>=1.0",

    # Voice Input
    "faster-whisper>=1.0",
    "sounddevice>=0.4",
    "pynput>=1.7",

    # Voice Output
    "kokoro-onnx>=0.4",

    # CLI & Config
    "click>=8.0",
    "pyyaml>=6.0",

    # Utilities
    "httpx>=0.27",
    "plyer>=2.0",
    "exa-py>=1.0",
]

[project.scripts]
jarvis = "jarvis.__main__:main"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
```

---

## VRAM Budget

| Component | Usage | Cumulative |
|-----------|-------|------------|
| Qwen2.5-7B-Instruct | 5.0 GB | 5.0 GB |
| faster-whisper large-v3-turbo | 1.5 GB | 6.5 GB |
| Buffer | 1.5 GB | 8.0 GB |
| **Headroom** | **4.0 GB** | 12 GB total |

---

## Gates (Must Pass)

### Gate 1: LangGraph + Ollama Tool Calling ✅ PASSED

### Gate 2: Voice Pipeline ✅ PASSED

### Gate 3: MCP Tool Loading ⬜ NEW
**When:** During Phase 5
**Test:**
```python
# MCP tools load and work with Qwen2.5
tools = await load_mcp_tools()
assert len(tools) > 0
# Agent successfully calls MCP tool
```
**Fallback:** Direct API integration (current approach for Exa)

---

## Popular MCP Servers Reference

| MCP Server | Install | Tools Provided |
|------------|---------|----------------|
| **Exa** | HTTP: `https://mcp.exa.ai/mcp` | web_search, code_search, company_research |
| **GitHub** | `npx @modelcontextprotocol/server-github` | issues, PRs, repos, code search |
| **Filesystem** | `npx @modelcontextprotocol/server-filesystem` | read, write, list files |
| **Brave Search** | `npx @anthropics/server-brave-search` | web search |
| **PostgreSQL** | `npx @modelcontextprotocol/server-postgres` | SQL queries |
| **Slack** | `npx @anthropics/server-slack` | messages, channels |

---

*Last Updated: January 29, 2026*
