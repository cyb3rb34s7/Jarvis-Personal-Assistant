# JARVIS

Local, privacy-first AI voice assistant running entirely on your hardware.

## Features

- **100% Local** - No cloud dependencies, your data stays on your machine
- **Voice Interaction** - Push-to-talk with Whisper STT and Kokoro TTS
- **Conversation Memory** - Remembers context within sessions and across conversations
- **Tool Calling** - Calculator, reminders, notes, web search
- **MCP Integration** - Extensible via Model Context Protocol
- **Hinglish Support** - Understands Hindi-English code-switching

## Requirements

| Component | Minimum |
|-----------|---------|
| GPU | NVIDIA with 8GB+ VRAM (tested on RTX 4070) |
| RAM | 16GB |
| Python | 3.12 |
| OS | Windows 10/11 |

## Quick Start

### 1. Install Ollama

```bash
winget install Ollama.Ollama
ollama pull qwen2.5:7b-instruct
```

### 2. Clone and Install

```bash
git clone https://github.com/cyb3rb34s7/Jarvis-Personal-Assistant.git
cd Jarvis-Personal-Assistant

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -e ".[full]"
```

### 3. Download TTS Model

Download from [kokoro-onnx releases](https://github.com/thewh1teagle/kokoro-onnx/releases):
- `kokoro-v1.0.onnx` → `models/kokoro/`
- `voices-v1.0.bin` → `models/kokoro/`

### 4. Configure API Keys (Optional)

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 5. Run

```bash
# Text mode (single query)
jarvis "what is 2 + 2"

# Interactive chat with memory
jarvis chat

# Voice mode
jarvis --voice

# With MCP tools
jarvis --mcp ask "find python async examples"
```

## Usage

### Text Mode (Single Query)

```bash
jarvis "what is the capital of France"
jarvis "remind me to take a break in 30 minutes"
jarvis "save a note: buy groceries tomorrow"
jarvis "search my notes for groceries"
```

### Interactive Chat (With Memory)

```bash
# Start new conversation
jarvis chat

# Resume last conversation
jarvis chat --resume

# Resume specific conversation
jarvis chat --id abc123

# View conversation history
jarvis history
```

**Example conversation:**
```
You: What is 15 * 7?
JARVIS: 105

You: Multiply that by 2
JARVIS: 210          # JARVIS remembers "that" refers to 105
```

### Voice Mode

```bash
jarvis --voice
```

- Press **Ctrl+Space** to speak
- Say "exit" or "quit" to stop
- Press **Ctrl+C** to force quit
- Voice mode automatically remembers conversation context

### With MCP Tools

```bash
# Check configured MCP servers
jarvis mcp-status

# Enable MCP tools
jarvis --mcp ask "your query"
```

**Search behavior with MCP:**
| Query Type | Tool Used | Cost |
|------------|-----------|------|
| Simple (weather, facts) | DuckDuckGo | Free |
| Code/programming | Exa code_search | Exa quota |
| Company research | Exa company_research | Exa quota |
| "deep search..." | Exa web_search | Exa quota |

### Check Status

```bash
jarvis status
```

Shows: Ollama status, dependencies, config, memory stats.

## Configuration

Edit `data/config.yaml`:

```yaml
model:
  name: qwen2.5:7b-instruct
  temperature: 0.7

voice:
  stt_model: large-v3-turbo
  stt_language: hi  # For Hinglish support
  hotkey: ctrl+space
  tts_voice: af_heart

mcp:
  enabled: false  # Set true to always load MCP tools
```

## MCP Servers

Add MCP servers by editing `data/mcp_servers.json`:

```json
{
  "mcpServers": {
    "exa": {
      "transport": "http",
      "url": "https://mcp.exa.ai/mcp",
      "headers": { "x-api-key": "${EXA_API_KEY}" }
    },
    "github": {
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" }
    }
  }
}
```

## Built-in Tools

| Tool | Description |
|------|-------------|
| `calculator` | Math expressions |
| `reminder_set` | Set reminders ("in 30m", "in 2h") |
| `reminder_list` | List pending reminders |
| `note_save` | Save notes as markdown |
| `note_search` | Search saved notes |
| `web_search` | DuckDuckGo search (free) |

## Memory System

JARVIS remembers conversations using SQLite:

- **Session Context**: Last 20 messages in active context
- **Conversation History**: All messages persisted to database
- **Safe Sliding Window**: Never splits tool call/response pairs

```bash
# View past conversations
jarvis history

# Resume a conversation
jarvis chat --id <conversation_id>
```

Database location: `data/jarvis.db`

## Project Structure

```
jarvis/
├── src/jarvis/
│   ├── agent/          # LangGraph agent, tools, MCP loader
│   ├── voice/          # STT (Whisper), TTS (Kokoro), audio
│   ├── features/       # Notes, reminders, search
│   ├── memory/         # Session memory, conversation management
│   ├── utils/          # Errors, notifications
│   ├── database.py     # SQLite setup
│   └── config.py       # Configuration management
├── data/
│   ├── jarvis.db       # SQLite database (conversations, messages)
│   ├── config.yaml     # User configuration
│   ├── mcp_servers.json # MCP server config
│   ├── notes/          # Saved notes (markdown)
│   └── reminders.json  # Persistent reminders
├── models/
│   └── kokoro/         # TTS model files
├── docs/
│   ├── GUI_PLAN.md     # GUI implementation plan
│   ├── CONTEXT.md      # Current development context
│   └── CHANGELOG.md    # Development changelog
└── .env                # API keys (not committed)
```

## Troubleshooting

### CUDA cublas64_12.dll not found

The app automatically adds pip-installed CUDA libraries to PATH. If issues persist:
```bash
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

### Whisper model download slow

Models are cached in `~/.cache/huggingface/`. First run downloads ~1.5GB.

### TTS not speaking

Ensure model files are in `models/kokoro/`:
- `kokoro-v1.0.onnx`
- `voices-v1.0.bin`

### MCP tools not loading

1. Check `jarvis mcp-status`
2. Verify API keys in `.env`
3. Check `data/mcp_servers.json` syntax

### Memory not working

1. Check database exists: `data/jarvis.db`
2. Run `jarvis status` to see conversation count
3. Use `jarvis chat` (not plain `jarvis "query"`) for memory

## Tech Stack

- **LLM**: Qwen2.5-7B-Instruct via Ollama
- **Agent**: LangGraph
- **STT**: faster-whisper (large-v3-turbo)
- **TTS**: Kokoro (ONNX)
- **Memory**: SQLite
- **MCP**: langchain-mcp-adapters

## Roadmap

- [x] Core agent with tool calling
- [x] Voice input/output
- [x] MCP integration
- [x] Conversation memory
- [ ] Web UI (Next.js)
- [ ] Remote access (Cloudflare Tunnel)
- [ ] Desktop app (Tauri)

## License

MIT

## Acknowledgments

- [Ollama](https://ollama.ai) - Local LLM runtime
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent framework
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Speech recognition
- [Kokoro](https://github.com/thewh1teagle/kokoro-onnx) - Text-to-speech
- [Exa](https://exa.ai) - Semantic search API
