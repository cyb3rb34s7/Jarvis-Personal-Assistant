# JARVIS GUI - Implementation Plan

## Overview

Build a modern GUI for JARVIS with:
- Animated particle sphere (voice visualization)
- Real-time chat with streaming responses
- Reminders, notes, and MCP management
- **Local-first with optional remote access via Cloudflare Tunnel**

---

## 1. Deployment Architecture

### Design Principle: Local Agent, Remote UI

The GPU-heavy processing (LLM, STT, TTS) runs on your local PC. The UI can be accessed locally or remotely.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Your PC (Home - GPU)                    │
│  ┌───────────────────┐      ┌────────────────────────────┐  │
│  │   JARVIS Agent    │◄────►│ cloudflared (daemon)       │  │
│  │   FastAPI :8000   │      │ (Optional - for remote)    │  │
│  │   • Ollama LLM    │      └─────────────┬──────────────┘  │
│  │   • Whisper STT   │                    │                 │
│  │   • Kokoro TTS    │                    │                 │
│  │   • Tools/Memory  │                    │                 │
│  └───────────────────┘                    │                 │
└───────────────────────────────────────────┼─────────────────┘
                                            │ Cloudflare Tunnel
                                            │ (encrypted)
                                            ▼
              ┌────────────────────────────────────────────┐
              │  https://jarvis.yourdomain.com             │
              │  (Public URL - DDoS protected, mTLS)       │
              └────────────────────────────────────────────┘
                                            │
┌───────────────────────────────────────────┼─────────────────┐
│                     Vercel (or local)                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   Next.js UI                                           │  │
│  │   • Chat interface                                     │  │
│  │   • Particle sphere                                    │  │
│  │   • Voice recording                                    │  │
│  │   calls: /api/* → localhost:8000 OR tunnel URL        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Why NOT a Custom Gateway?

| Approach | Effort | Maintenance | Security |
|----------|--------|-------------|----------|
| Custom WebSocket Gateway | High | Reconnection logic, packet loss, auth | DIY |
| **Cloudflare Tunnel** | Low | Zero (managed service) | DDoS, mTLS built-in |

**Decision:** Use Cloudflare Tunnel (free tier) instead of writing custom gateway code.

### Deployment Modes

| Mode | Use Case | How to Run |
|------|----------|------------|
| **Local** | At home, same network | `jarvis serve` → http://localhost:8000 |
| **Remote** | Access from anywhere | `cloudflared tunnel run jarvis` |

---

## 2. Repository Structure (Final)

```
D:\PROJECTS\JARVIS\
│
├── src/jarvis/               # Python - Agent + API
│   ├── agent/                # ✅ Existing: LangGraph agent
│   ├── voice/                # ✅ Existing: STT, TTS
│   ├── features/             # ✅ Existing: notes, reminders, search
│   ├── memory/               # ✅ Existing: SQLite sessions
│   ├── database.py           # ✅ Existing: SQLite setup
│   ├── config.py             # ✅ Existing: YAML config
│   ├── cli.py                # ✅ Existing: CLI interface
│   │
│   └── api/                  # 🆕 NEW: FastAPI backend
│       ├── __init__.py
│       ├── main.py           # FastAPI app, CORS, lifespan
│       ├── deps.py           # Dependencies, auth verification
│       ├── auth.py           # Bearer token validation
│       ├── websocket.py      # WebSocket handler (chat, voice)
│       └── routes/
│           ├── __init__.py
│           ├── status.py     # GET /status
│           ├── chat.py       # POST /chat, WebSocket /ws
│           ├── conversations.py
│           ├── reminders.py
│           ├── notes.py
│           ├── mcp.py
│           └── voice.py      # POST /voice/transcribe, /synthesize
│
├── ui/                       # 🆕 NEW: Next.js frontend
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx          # Main chat view
│   │   ├── reminders/
│   │   ├── notes/
│   │   ├── mcp/
│   │   └── settings/
│   ├── components/
│   │   ├── chat/
│   │   ├── voice/
│   │   ├── reminders/
│   │   ├── notes/
│   │   └── ui/               # shadcn components
│   ├── lib/
│   │   ├── api.ts            # REST client
│   │   ├── websocket.ts      # WebSocket manager
│   │   └── store.ts          # Zustand store
│   ├── hooks/
│   ├── public/
│   ├── package.json
│   ├── tailwind.config.js
│   └── next.config.js
│
├── data/
│   ├── jarvis.db             # ✅ SQLite database
│   ├── config.yaml           # ✅ App configuration
│   ├── mcp_servers.json      # ✅ MCP configuration
│   └── notes/                # ✅ Markdown notes
│
├── models/
│   └── kokoro/               # ✅ TTS model files
│
└── docs/
    ├── GUI_PLAN.md           # This file
    ├── CONTEXT.md
    ├── CHANGELOG.md
    └── ...
```

**Note:** No `gateway/` folder - Cloudflare Tunnel replaces custom gateway code.

---

## 3. Security

### API Authentication

All API requests require a Bearer token (except `/status`).

```python
# src/jarvis/api/auth.py
import os
from fastapi import Header, HTTPException

API_SECRET = os.getenv("JARVIS_API_SECRET")

async def verify_token(authorization: str = Header(None)):
    """Verify Bearer token for API access."""
    if not API_SECRET:
        return  # No auth configured (local dev mode)

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")

    token = authorization.split(" ")[1]
    if token != API_SECRET:
        raise HTTPException(401, "Invalid API token")
```

```python
# src/jarvis/api/deps.py
from fastapi import Depends
from .auth import verify_token

# Use in routes that need auth
@router.post("/chat")
async def chat(message: str, _: None = Depends(verify_token)):
    ...
```

### Environment Variables

```bash
# .env (add to existing)
JARVIS_API_SECRET=your-secret-token-here  # Generate with: openssl rand -hex 32
```

### CORS Configuration

```python
# src/jarvis/api/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",           # Local Next.js dev
        "https://jarvis-ui.vercel.app",    # Production UI
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 4. Data Storage (Implemented ✅)

### Current State

| Data | Storage | Status |
|------|---------|--------|
| Conversations | `data/jarvis.db` (SQLite) | ✅ Implemented |
| Messages | `data/jarvis.db` (SQLite) | ✅ Implemented |
| User Facts | `data/jarvis.db` (SQLite) | ✅ Implemented |
| Notes content | `data/notes/*.md` | ✅ Existing |
| Reminders | `data/reminders.json` | ✅ Existing (migrate to SQLite later) |
| MCP Config | `data/mcp_servers.json` | ✅ Existing |
| App Config | `data/config.yaml` | ✅ Existing |

### SQLite Schema (Already Created)

```sql
-- Conversations
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    title TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    archived BOOLEAN DEFAULT FALSE
);

-- Messages (with tool_call_id for safe sliding window)
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    message_type TEXT DEFAULT 'text',
    tool_name TEXT,
    tool_args TEXT,
    tool_call_id TEXT,
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User preferences/facts (long-term memory)
CREATE TABLE user_facts (
    id TEXT PRIMARY KEY,
    fact_type TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    created_at DATETIME,
    updated_at DATETIME
);

-- Tool usage analytics
CREATE TABLE tool_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL,
    query TEXT,
    success BOOLEAN,
    used_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. API Design

### REST Endpoints

```
BASE: /api/v1

# Health & Status (no auth required)
GET  /status                    # System status, dependencies

# Conversations
GET  /conversations             # List conversations
POST /conversations             # Create new conversation
GET  /conversations/:id         # Get conversation with messages
DELETE /conversations/:id       # Delete conversation

# Chat
POST /conversations/:id/messages    # Send message, get response
WebSocket /ws                       # Real-time chat

# Reminders
GET    /reminders               # List reminders
POST   /reminders               # Create reminder
PATCH  /reminders/:id           # Update (complete, snooze)
DELETE /reminders/:id           # Delete reminder

# Notes
GET    /notes                   # List notes
POST   /notes                   # Create note
GET    /notes/:id               # Get note content
PATCH  /notes/:id               # Update note
DELETE /notes/:id               # Delete note
GET    /notes/search?q=         # Full-text search

# MCP Management
GET    /mcp/servers             # List configured servers
GET    /mcp/tools               # List available tools
POST   /mcp/reload              # Reload MCP connections

# Voice
POST   /voice/transcribe        # Upload audio → text
POST   /voice/synthesize        # Text → audio file

# Configuration
GET    /config                  # Get current config
PATCH  /config                  # Update config
```

### WebSocket Protocol

**Endpoint:** `ws://localhost:8000/ws` or `wss://jarvis.yourdomain.com/ws`

**Server → Client Events:**
```typescript
{ type: "connected", session_id: "abc123" }
{ type: "state", state: "idle" | "listening" | "processing" | "speaking" }
{ type: "transcript", text: "what is the weather", interim: boolean }
{ type: "response_start", message_id: "msg_123" }
{ type: "response_delta", message_id: "msg_123", delta: "The weather" }
{ type: "response_end", message_id: "msg_123", content: "..." }
{ type: "tool_start", tool: "web_search", args: {...} }
{ type: "tool_end", tool: "web_search", result: "..." }
{ type: "audio", data: "<base64 opus>" }
{ type: "error", message: "...", code: "..." }
```

**Client → Server Commands:**
```typescript
{ action: "send_message", text: "...", conversation_id: "..." }
{ action: "voice_start" }
{ action: "voice_stop" }
{ action: "voice_data", audio: "<base64 opus>" }
{ action: "interrupt" }
{ action: "cancel" }
```

---

## 6. Voice Architecture

### Latency Optimization

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐             │
│  │ Microphone│──►│ VAD       │──►│ OPUS      │──► WebSocket│
│  │           │   │ (hark.js) │   │ Encoder   │             │
│  └───────────┘   └───────────┘   └───────────┘             │
│                                                             │
│  Key: Only stream when voice detected. OPUS = 10x smaller. │
└─────────────────────────────────────────────────────────────┘
```

### Remote Latency Handling

**Problem:** Remote access adds ~300-500ms latency.

**Solution:** Optimistic UI

```typescript
// Don't wait for server acknowledgment
const sendVoice = async (audio: Blob) => {
  // Immediately show "Processing..." state
  setVoiceState('processing');
  playThinkingSound();  // Optional: audio feedback

  // Then actually send
  await websocket.send({ action: 'voice_data', audio });
};
```

### Barge-In (Interrupt)

User can interrupt JARVIS while speaking:

```typescript
// Client sends
{ action: "interrupt" }

// Server immediately:
// 1. Kills TTS thread
// 2. Clears audio queue
// 3. Sends confirmation

// Server responds
{ type: "interrupted" }
{ type: "state", state: "listening" }

// Client immediately:
audioRef.current.pause();
audioRef.current.currentTime = 0;
```

---

## 7. Frontend Architecture (Next.js)

### Tech Stack

| Category | Choice |
|----------|--------|
| Framework | Next.js 14 (App Router) |
| Styling | TailwindCSS |
| Components | shadcn/ui |
| State | Zustand |
| WebSocket | Native + reconnection |
| 3D | react-three-fiber |
| Audio | Web Audio API |

### Component Structure

```
ui/components/
├── chat/
│   ├── ChatWindow.tsx        # Main container
│   ├── MessageList.tsx       # Scrollable messages
│   ├── MessageBubble.tsx     # Individual message
│   ├── MessageRenderer.tsx   # Rich tool outputs
│   ├── InputBar.tsx          # Text input + voice button
│   └── ToolIndicator.tsx     # Shows active tool
│
├── voice/
│   ├── ParticleSphere.tsx    # 3D animated sphere
│   ├── VoiceButton.tsx       # Hold-to-talk button
│   ├── Transcript.tsx        # Live transcript
│   └── useVoice.ts           # Voice recording hook
│
├── cards/                    # Rich tool outputs
│   ├── SearchResultsCard.tsx
│   ├── WeatherCard.tsx
│   ├── ReminderCard.tsx
│   ├── CodeResultsCard.tsx
│   └── CompanyCard.tsx
│
└── ui/                       # shadcn components
```

### Zustand Store

```typescript
interface JarvisState {
  // Connection
  connected: boolean;
  agentOnline: boolean;  // For remote: is local PC running?

  // Voice
  voiceState: 'idle' | 'listening' | 'processing' | 'speaking';
  transcript: string;
  audioLevel: number;

  // Chat
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  streamingMessage: string;

  // Actions
  sendMessage: (text: string) => void;
  startListening: () => void;
  stopListening: () => void;
  interrupt: () => void;
}
```

---

## 8. Particle Sphere

### State Colors

| State | Color | Animation |
|-------|-------|-----------|
| `idle` | Cyan `#00f3ff` | Slow rotation |
| `listening` | Red `#ff2a2a` | Breathing pulse |
| `processing` | Orange `#ffaa00` | Fast spin |
| `speaking` | Green `#00ff88` | Amplitude-reactive |

### Implementation

```tsx
// See full implementation in Section 10 of previous version
// Key points:
// - 2000 particles on sphere surface
// - useFrame for 60fps animation
// - lerp for smooth transitions
// - Audio amplitude drives scale when speaking
```

---

## 9. Implementation Phases

### Phase A: FastAPI Backend ← CURRENT
1. Create `src/jarvis/api/` structure
2. Implement FastAPI app with CORS
3. Add Bearer token auth
4. Implement REST endpoints (status, conversations, chat)
5. Implement WebSocket handler
6. Integrate with existing agent/memory
7. Test locally

**Deliverable:** `jarvis serve` → API at localhost:8000

### Phase B: Basic Frontend
1. Set up Next.js project
2. Implement Zustand store
3. Implement WebSocket connection
4. Create basic chat UI
5. Display streaming responses

**Deliverable:** Chat working in browser

### Phase C: Voice Integration
1. Implement VAD + OPUS recording
2. Send audio via WebSocket
3. Play TTS responses
4. Add hold-to-talk (spacebar)
5. Implement barge-in

**Deliverable:** Voice chat working

### Phase D: Particle Sphere
1. Set up react-three-fiber
2. Create particle geometry
3. Implement state animations
4. Sync with audio levels

**Deliverable:** Animated sphere

### Phase E: Features UI
1. Reminders management
2. Notes browser + editor
3. MCP server management
4. Settings page

**Deliverable:** Full-featured UI

### Phase F: Remote Access
1. Install cloudflared
2. Create tunnel
3. Configure auth
4. Deploy UI to Vercel
5. Test end-to-end

**Deliverable:** Access from anywhere

### Phase G: Tauri Desktop (Future)
1. Set up Tauri
2. Bundle frontend
3. System tray
4. Global hotkeys

**Deliverable:** Native desktop app

---

## 10. Decisions Log (Finalized)

| Question | Decision | Rationale |
|----------|----------|-----------|
| Remote access | Cloudflare Tunnel | Free, secure, no custom gateway code |
| Custom gateway | ❌ No | Tunnel replaces weeks of WebSocket debugging |
| Auth | Bearer token | Simple, works with tunnel |
| Chat history | Keep all | "Remember that code from last week" is powerful |
| Multi-conversation | Yes | Fresh context for different topics |
| Theme | Dark mode only | It's JARVIS. Iron Man didn't have light mode. |
| Voice hotkey | Spacebar hold-to-talk | Definitive, tactical, less anxiety |
| Remote latency | Optimistic UI | Show "Processing..." immediately |
| Note editor | Simple markdown | Don't build Notion |

---

## 11. Cloudflare Tunnel Setup (Phase F)

### One-time Setup

```bash
# Install cloudflared
winget install Cloudflare.cloudflared

# Login to Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create jarvis

# Configure DNS (in Cloudflare dashboard)
# jarvis.yourdomain.com → tunnel UUID
```

### Running the Tunnel

```bash
# Start tunnel (connects local :8000 to public URL)
cloudflared tunnel run --url http://localhost:8000 jarvis
```

### Auto-start (Windows)

Create a scheduled task or service to run cloudflared on boot.

---

## 12. Environment Variables (Complete)

```bash
# .env
# Existing
EXA_API_KEY=your-exa-key

# New for API
JARVIS_API_SECRET=your-secret-token  # openssl rand -hex 32
JARVIS_API_HOST=0.0.0.0              # Bind to all interfaces
JARVIS_API_PORT=8000                 # API port

# For UI (Next.js)
NEXT_PUBLIC_API_URL=http://localhost:8000      # Local dev
# NEXT_PUBLIC_API_URL=https://jarvis.yourdomain.com  # Production
```

---

*Last Updated: January 29, 2026*
*Architecture: Local Agent + Cloudflare Tunnel (No Custom Gateway)*
