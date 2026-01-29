# JARVIS Architecture Analysis
## Agent Beta - Architecture Specialist Report

**Date:** January 2026
**Hardware Target:** RTX 4070 12GB, 32GB DDR5 RAM, Ryzen 9800X3D, Windows

---

## Executive Summary

This document provides opinionated architectural recommendations for building JARVIS, a local personal assistant. Given the hardware profile (RTX 4070 with 12GB VRAM, 32GB system RAM), we have substantial computational headroom for running multiple AI models concurrently. The architecture prioritizes:

1. **Privacy** - All processing local, no cloud dependencies
2. **Performance** - Sub-second response times for voice interactions
3. **Extensibility** - Plugin system for future capabilities
4. **Reliability** - Graceful degradation when resources are constrained

---

## 1. LLM Integration Architecture

### Recommendation: **Ollama** as primary, with direct llama.cpp for advanced use cases

#### Why Ollama?

| Aspect | Ollama | llama.cpp (direct) | vLLM |
|--------|--------|-------------------|------|
| Ease of setup | Excellent | Moderate | Complex |
| API compatibility | OpenAI-compatible | Custom | OpenAI-compatible |
| Model management | Built-in | Manual | Manual |
| Memory efficiency | Good (4-bit quant) | Best | Good |
| Tool/Function calling | Supported | Supported | Excellent |
| Windows support | Native | Native | Limited (WSL) |
| Concurrent requests | Good | Manual | Excellent |

**Ollama wins because:**
1. **OpenAI-compatible API** - Use any existing Python library (openai, litellm, langchain) with zero code changes
2. **Model management** - `ollama pull llama3.2` vs manual GGUF downloading and configuration
3. **Automatic GPU detection** - Uses CUDA automatically on Windows
4. **Background service** - Runs as Windows service, always ready
5. **Tool calling support** - Native function calling with structured outputs

**When to use llama.cpp directly:**
- Custom quantization requirements
- Maximum performance tuning (KV cache tweaking)
- Embedding models (faster than Ollama for embeddings)
- Speculative decoding setups

**vLLM avoided because:**
- Windows support is problematic (requires WSL2)
- Designed for server workloads, overkill for single-user
- Higher VRAM overhead for batching infrastructure

### Model Recommendations for RTX 4070 12GB

| Use Case | Model | Size | VRAM Usage | Speed |
|----------|-------|------|------------|-------|
| Main reasoning | Qwen2.5-14B-Q4_K_M | ~8GB | ~9GB | 30-40 tok/s |
| Fast responses | Qwen2.5-7B-Q4_K_M | ~4GB | ~5GB | 60-80 tok/s |
| Code generation | DeepSeek-Coder-V2-Lite | ~6GB | ~7GB | 40-50 tok/s |
| Fallback/Edge | Phi-3-mini-Q4 | ~2GB | ~3GB | 100+ tok/s |

**Strategy:** Load 7B model for quick queries, 14B for complex reasoning. Hot-swap based on query complexity detection.

### Tool/Function Calling Pattern

```
User Query
    |
    v
[Intent Classifier] --> Simple query --> [7B Model Direct Response]
    |
    Complex/Tool needed
    v
[14B Model with Tools] --> Tool Call --> [Tool Executor]
    |                                          |
    v                                          v
[Response Formatter] <-- Tool Result <---------
```

**Implementation approach:**
1. Use Ollama's native tool calling (available since Ollama 0.3+)
2. Define tools as JSON schemas
3. Implement tool executor as async Python with timeout handling
4. Return tool results for model to synthesize final response

### Context Management & Memory

**Recommendation: Hybrid approach**

1. **Short-term (conversation):** Sliding window in prompt
   - Last 10-20 exchanges
   - ~4K tokens reserved

2. **Medium-term (session):** SQLite with FTS5
   - Conversation summaries
   - Entity extraction (people, dates, topics)
   - Searchable by keyword

3. **Long-term (knowledge):** Vector store (see RAG section)
   - Semantic search for relevant context
   - User preferences and learned behaviors

**Memory Schema:**
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    timestamp DATETIME,
    role TEXT,  -- user/assistant/system
    content TEXT,
    embedding BLOB,  -- for semantic search
    entities JSON,  -- extracted entities
    summary TEXT  -- generated for older messages
);

CREATE VIRTUAL TABLE conversations_fts USING fts5(content, summary);
```

---

## 2. Voice Pipeline Architecture

### Speech-to-Text (STT)

**Recommendation: faster-whisper with CUDA**

| Option | Speed (RTX 4070) | Accuracy | Memory | Real-time Factor |
|--------|------------------|----------|--------|------------------|
| faster-whisper large-v3 | Excellent | Best | ~3GB VRAM | 15-20x |
| whisper.cpp large-v3 | Good | Best | ~2GB VRAM | 10-15x |
| OpenAI Whisper (original) | Slow | Best | ~4GB VRAM | 5-8x |
| Vosk | Fast | Good | ~50MB RAM | 30x+ |

**faster-whisper wins because:**
1. **CTranslate2 backend** - 4x faster than original Whisper
2. **CUDA optimized** - Full GPU acceleration
3. **Streaming capable** - Process audio chunks as they arrive
4. **Same accuracy** - Identical to OpenAI Whisper
5. **VAD integration** - Built-in voice activity detection with Silero

**Architecture for real-time:**
```
Microphone Input (16kHz)
    |
    v
[Silero VAD] -- silence --> (wait)
    |
    speech detected
    v
[Audio Buffer] -- 30s max segment
    |
    voice ends (VAD)
    v
[faster-whisper] -- CUDA inference
    |
    v
[Text Output] --> LLM Pipeline
```

**Key settings:**
```python
model = WhisperModel("large-v3", device="cuda", compute_type="float16")
# For lower VRAM, use "medium" model (~1.5GB) with minimal accuracy loss
segments, info = model.transcribe(audio,
    beam_size=5,
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=500)
)
```

**Memory budget:** With large-v3 using ~3GB and main LLM using ~9GB, total is ~12GB - fits in your 12GB VRAM with careful management. Consider medium model (~1.5GB) for safer concurrent operation.

### Text-to-Speech (TTS)

**Recommendation: Piper for primary, Coqui XTTS for voice cloning**

| Option | Quality | Speed | VRAM | Voices | Real-time |
|--------|---------|-------|------|--------|-----------|
| Piper | Good | Very Fast | ~0 (CPU) | 100+ | Yes |
| Coqui XTTS v2 | Excellent | Moderate | ~2GB | Clone any | Near RT |
| Bark | Excellent | Slow | ~4GB | Clone any | No |
| StyleTTS2 | Best | Slow | ~2GB | Limited | No |

**Piper wins for primary because:**
1. **CPU-only** - Frees GPU for LLM and STT
2. **Real-time streaming** - ~50ms latency
3. **Quality sufficient** - Very natural for English voices
4. **Simple integration** - Single binary, no Python deps
5. **Low resource** - 50MB model, minimal RAM

**Coqui XTTS for special cases:**
- Voice cloning (custom assistant voice)
- Emotional expression
- Multilingual with single model

**Architecture:**
```
LLM Response Text
    |
    v
[Sentence Splitter] -- stream sentences as generated
    |
    v
[Piper TTS] -- CPU inference, ~10x real-time
    |
    v
[Audio Queue] -- buffer sentences
    |
    v
[Audio Output] -- play with crossfade
```

**Streaming implementation:**
```python
# Stream TTS as LLM generates
async for sentence in llm_stream:
    audio = piper.synthesize(sentence)
    await audio_queue.put(audio)
```

### Voice Pipeline Integration

**Recommended flow:**
```
         +------------------+
         |  Audio Manager   |
         |  (pyaudio/sounddevice)
         +--------+---------+
                  |
        +---------+---------+
        |                   |
        v                   v
[Microphone Input]    [Speaker Output]
        |                   ^
        v                   |
[VAD + Buffer]         [Audio Queue]
        |                   ^
        v                   |
[faster-whisper]       [Piper TTS]
        |                   ^
        v                   |
+-------+-------------------+-------+
|           LLM Core                |
+-----------------------------------+
```

---

## 3. Knowledge Base / RAG Architecture

### Vector Database

**Recommendation: LanceDB**

| Database | Performance | Memory | Persistence | Features | Complexity |
|----------|-------------|--------|-------------|----------|------------|
| LanceDB | Excellent | Low | Native | Versioning, SQL | Low |
| ChromaDB | Good | Moderate | SQLite | Simple API | Very Low |
| Qdrant | Excellent | Moderate | Native | Filtering, clustering | Medium |
| SQLite-vec | Good | Low | SQLite | SQL integration | Low |

**LanceDB wins because:**
1. **Zero-copy columnar format** - Fast scans without loading all into RAM
2. **Native persistence** - No separate server process
3. **Versioning** - Time travel for knowledge updates
4. **Hybrid search** - Vector + full-text + metadata filtering
5. **Low memory** - Disk-based by default, memory-maps as needed
6. **Python-native** - Pure Python, easy Windows installation

**ChromaDB as alternative:**
- Simpler API for prototyping
- Larger community
- But: Higher memory usage, server mode issues on Windows

**Qdrant avoided because:**
- Requires running separate server
- Overkill for personal assistant scale
- More operational complexity

### Embedding Models

**Recommendation: BGE-M3 (multilingual) or nomic-embed-text (English)**

| Model | Dimensions | Quality | Speed (4070) | VRAM |
|-------|------------|---------|--------------|------|
| BGE-M3 | 1024 | Excellent | 500+ docs/s | ~1GB |
| nomic-embed-text | 768 | Very Good | 1000+ docs/s | ~300MB |
| all-MiniLM-L6 | 384 | Good | 2000+ docs/s | ~100MB |
| UAE-Large-V1 | 1024 | Excellent | 400+ docs/s | ~1.5GB |

**BGE-M3 recommended because:**
1. **Multi-vector** - Dense + sparse + colbert in one model
2. **Multilingual** - 100+ languages
3. **Long context** - 8192 tokens
4. **State-of-art retrieval** - Top MTEB scores

**For resource-constrained scenarios:** nomic-embed-text runs great on CPU and is ~800MB total.

**Implementation:**
```python
# Using sentence-transformers
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("BAAI/bge-m3", device="cuda")
embeddings = embedder.encode(documents, normalize_embeddings=True)
```

### Chunking Strategy

**Recommendation: Semantic chunking with overlap**

```
Document
    |
    v
[Sentence Tokenizer] -- split into sentences
    |
    v
[Semantic Grouper] -- group by topic similarity
    |
    v
[Chunk Sizer] -- target 200-500 tokens with 50 token overlap
    |
    v
[Metadata Extractor] -- source, date, entities
    |
    v
[Vector Store]
```

**Key parameters:**
- **Chunk size:** 400 tokens (sweet spot for retrieval precision)
- **Overlap:** 50 tokens (maintain context at boundaries)
- **Grouping:** Semantic (not fixed-size) for coherent chunks

### RAG Pipeline

```
User Query
    |
    v
[Query Embedding] -- BGE-M3
    |
    v
[Hybrid Search] -- vector + keyword (LanceDB)
    |
    +--> Top 5 by vector similarity
    +--> Top 5 by keyword match (BM25)
    |
    v
[Reranker] -- BGE-reranker or cross-encoder
    |
    v
[Top 3 chunks] --> LLM Context
    |
    v
[LLM with RAG prompt]
```

**Reranker:** Use BGE-reranker-v2-m3 for final ranking. Slower but dramatically improves relevance.

---

## 4. Plugin/Skill System Architecture

### Recommendation: Event-driven with async handlers

After analyzing Leon AI and Mycroft architectures:

**Leon AI approach:**
- Skills as Python packages
- NLU-driven intent routing
- Action-resolver pattern
- Good: Clear structure
- Bad: Tight NLU coupling

**Mycroft approach:**
- Message bus (websocket)
- Skills register intents
- Event emission
- Good: Decoupled
- Bad: Complex setup

**JARVIS Hybrid approach:**

```
+------------------+
|   Core Engine    |
|   (Async Event   |
|    Bus)          |
+--------+---------+
         |
    +----+----+----+----+
    |    |    |    |    |
    v    v    v    v    v
 [Plugin] [Plugin] [Plugin] [Plugin] [Built-in]
 Calendar  Weather  Notes   Smart    Core
                           Home     Commands
```

### Plugin Interface

```python
# plugin_interface.py
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class PluginCapability:
    name: str
    description: str
    parameters: dict  # JSON Schema
    examples: List[str]

class JarvisPlugin(ABC):
    """Base class for all JARVIS plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[PluginCapability]:
        """List of capabilities this plugin provides."""
        pass

    @abstractmethod
    async def execute(self, capability: str, params: dict) -> dict:
        """Execute a capability with given parameters."""
        pass

    async def on_load(self):
        """Called when plugin is loaded."""
        pass

    async def on_unload(self):
        """Called when plugin is unloaded."""
        pass
```

### Plugin Discovery & Loading

```python
# plugin_manager.py
import importlib.util
from pathlib import Path

class PluginManager:
    def __init__(self, plugin_dir: Path):
        self.plugin_dir = plugin_dir
        self.plugins: dict[str, JarvisPlugin] = {}
        self.capabilities_map: dict[str, tuple[str, str]] = {}

    async def discover_and_load(self):
        """Scan plugin directory and load all valid plugins."""
        for plugin_path in self.plugin_dir.glob("*/plugin.py"):
            await self._load_plugin(plugin_path)

    async def _load_plugin(self, path: Path):
        spec = importlib.util.spec_from_file_location("plugin", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        plugin_class = getattr(module, "Plugin")
        plugin = plugin_class()
        await plugin.on_load()

        self.plugins[plugin.name] = plugin
        for cap in plugin.capabilities:
            self.capabilities_map[cap.name] = (plugin.name, cap.name)

    def get_all_tools_for_llm(self) -> List[dict]:
        """Generate tool definitions for LLM function calling."""
        tools = []
        for plugin in self.plugins.values():
            for cap in plugin.capabilities:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": f"{plugin.name}_{cap.name}",
                        "description": cap.description,
                        "parameters": cap.parameters
                    }
                })
        return tools
```

### Event Bus

```python
# event_bus.py
import asyncio
from typing import Callable, Any
from collections import defaultdict

class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable):
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable):
        self._subscribers[event_type].remove(handler)

    async def emit(self, event_type: str, data: Any):
        handlers = self._subscribers.get(event_type, [])
        await asyncio.gather(*[h(data) for h in handlers])

# Event types
EVENTS = {
    "user.speech.started": "User began speaking",
    "user.speech.ended": "User finished speaking",
    "user.input.text": "Text input received",
    "assistant.thinking": "LLM processing started",
    "assistant.response.started": "Response generation began",
    "assistant.response.chunk": "Response chunk ready",
    "assistant.response.ended": "Response complete",
    "tool.call.started": "Tool invocation began",
    "tool.call.completed": "Tool returned result",
    "system.error": "Error occurred",
}
```

### Example Plugin

```python
# plugins/weather/plugin.py
from jarvis.plugin_interface import JarvisPlugin, PluginCapability
import httpx

class Plugin(JarvisPlugin):
    name = "weather"

    capabilities = [
        PluginCapability(
            name="get_current",
            description="Get current weather for a location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            },
            examples=["What's the weather in London?", "Is it raining outside?"]
        )
    ]

    async def execute(self, capability: str, params: dict) -> dict:
        if capability == "get_current":
            # Use free API like Open-Meteo
            async with httpx.AsyncClient() as client:
                # ... API call logic
                return {"temperature": 22, "condition": "sunny"}
```

---

## 5. GUI Framework Architecture

### Recommendation: PyQt6 with QML for modern UI, system tray integration

| Framework | Native Feel | Performance | Complexity | Windows Integration |
|-----------|-------------|-------------|------------|---------------------|
| PyQt6 | Excellent | Excellent | Medium | Excellent |
| PySide6 | Excellent | Excellent | Medium | Excellent |
| Tkinter | Poor | Good | Low | Basic |
| Web (FastAPI + React) | Good | Good | High | Custom |
| DearPyGui | Good | Excellent | Low | Basic |

**PyQt6 wins because:**
1. **Native Windows look** - Uses native widgets, feels like Windows app
2. **System tray** - First-class QSystemTrayIcon
3. **Rich widgets** - Everything needed built-in
4. **Signals/slots** - Natural async integration
5. **QML option** - Modern fluid UI possible
6. **Mature** - Battle-tested, great documentation

**PySide6 alternative:**
- Same Qt, different Python binding
- LGPL license (more permissive)
- Slightly less documentation

### System Tray Integration

```python
# system_tray.py
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction

class JarvisTray:
    def __init__(self, app: QApplication):
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon("assets/jarvis_icon.png"))
        self.tray.setToolTip("JARVIS - Personal Assistant")

        # Context menu
        menu = QMenu()

        show_action = QAction("Show JARVIS")
        show_action.triggered.connect(self.show_main_window)
        menu.addAction(show_action)

        mute_action = QAction("Mute Voice")
        mute_action.setCheckable(True)
        mute_action.triggered.connect(self.toggle_mute)
        menu.addAction(mute_action)

        menu.addSeparator()

        quit_action = QAction("Quit")
        quit_action.triggered.connect(app.quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.show()

        # Click to show
        self.tray.activated.connect(self.on_activated)

    def on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_main_window()
```

### Main Window Architecture

```python
# main_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QTextEdit, QLineEdit, QPushButton
)
from PyQt6.QtCore import pyqtSignal, QThread

class AssistantThread(QThread):
    """Background thread for LLM processing."""
    response_chunk = pyqtSignal(str)
    response_complete = pyqtSignal()

    def __init__(self, query: str, engine):
        super().__init__()
        self.query = query
        self.engine = engine

    def run(self):
        for chunk in self.engine.stream_response(self.query):
            self.response_chunk.emit(chunk)
        self.response_complete.emit()

class MainWindow(QMainWindow):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("JARVIS")
        self.setMinimumSize(400, 600)

        central = QWidget()
        layout = QVBoxLayout(central)

        # Chat history
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        # Input field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask JARVIS anything...")
        self.input_field.returnPressed.connect(self.send_message)
        layout.addWidget(self.input_field)

        # Voice button
        self.voice_btn = QPushButton("Hold to Speak")
        self.voice_btn.pressed.connect(self.start_listening)
        self.voice_btn.released.connect(self.stop_listening)
        layout.addWidget(self.voice_btn)

        self.setCentralWidget(central)
```

### Hotkey Integration (Global)

```python
# hotkeys.py
from pynput import keyboard

class GlobalHotkeys:
    def __init__(self, callbacks: dict):
        self.callbacks = callbacks
        self.current_keys = set()

    def start(self):
        listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        listener.start()

    def on_press(self, key):
        self.current_keys.add(key)

        # Ctrl+Shift+J to activate
        if (keyboard.Key.ctrl_l in self.current_keys and
            keyboard.Key.shift in self.current_keys and
            keyboard.KeyCode.from_char('j') in self.current_keys):
            self.callbacks.get('activate', lambda: None)()

    def on_release(self, key):
        self.current_keys.discard(key)
```

---

## 6. Overall System Architecture

### Component Diagram

```
+------------------------------------------------------------------+
|                          JARVIS Core                              |
+------------------------------------------------------------------+
|                                                                   |
|  +-----------------+    +------------------+    +--------------+  |
|  |   Voice Input   |    |    LLM Engine    |    | Voice Output |  |
|  |  (faster-whisper)|    |    (Ollama)     |    |   (Piper)    |  |
|  +--------+--------+    +--------+---------+    +------+-------+  |
|           |                      |                      |         |
|           v                      v                      ^         |
|  +--------+----------------------+----------------------+------+  |
|  |                      Event Bus                              |  |
|  +-----+------------+------------+------------+------------+---+  |
|        |            |            |            |            |      |
|        v            v            v            v            v      |
|  +---------+  +---------+  +---------+  +---------+  +--------+  |
|  | Plugin  |  | Plugin  |  |   RAG   |  | Memory  |  |  GUI   |  |
|  | Manager |  | Weather |  | Engine  |  | Manager |  | (PyQt) |  |
|  +---------+  +---------+  +---------+  +---------+  +--------+  |
|                                  |            |                   |
|                                  v            v                   |
|                            +----------+  +---------+              |
|                            | LanceDB  |  | SQLite  |              |
|                            +----------+  +---------+              |
+------------------------------------------------------------------+
```

### Data Flow

```
1. USER SPEAKS
   Microphone -> VAD -> faster-whisper -> Text

2. PROCESSING
   Text -> Intent Analysis -> Plugin/Tool Selection
       -> LLM with Context (memory + RAG) -> Response

3. OUTPUT
   Response -> Sentence Splitter -> Piper TTS -> Speaker
           -> GUI Update (streaming)

4. MEMORY
   Conversation -> Entity Extraction -> SQLite
   Important Info -> Embedding -> LanceDB
```

### Resource Management

**VRAM Budget (12GB):**
| Component | Allocated | Notes |
|-----------|-----------|-------|
| LLM (Qwen2.5-7B Q4) | 5GB | Primary model |
| LLM (14B hot-swap) | +4GB | Complex queries |
| faster-whisper medium | 1.5GB | Good accuracy |
| Embeddings (BGE-M3) | 1GB | Batch processing |
| Buffer | 0.5GB | Safety margin |
| **Total** | **12GB** | Fits with swapping |

**RAM Budget (32GB):**
| Component | Allocated | Notes |
|-----------|-----------|-------|
| OS + Applications | 8GB | Windows baseline |
| Python processes | 4GB | Core runtime |
| LanceDB cache | 2GB | Hot vectors |
| Audio buffers | 0.5GB | Voice pipeline |
| GUI | 0.5GB | PyQt |
| Available | 17GB | Future expansion |

### Startup Sequence

```
1. Initialize logging and config
2. Start Event Bus
3. Load SQLite memory database
4. Initialize LanceDB connection
5. Start Ollama service (if not running)
6. Load faster-whisper model
7. Initialize Piper TTS
8. Load plugins
9. Start GUI
10. Show system tray
11. Begin listening (if configured)
```

---

## 7. Technology Stack Summary

### Core Dependencies

```toml
# pyproject.toml
[project]
name = "jarvis"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    # LLM
    "ollama>=0.3",
    "openai>=1.0",  # For API compatibility

    # Voice
    "faster-whisper>=1.0",
    "piper-tts>=1.2",
    "sounddevice>=0.4",
    "silero-vad>=4.0",

    # RAG
    "lancedb>=0.4",
    "sentence-transformers>=2.2",

    # Memory
    "sqlalchemy>=2.0",

    # GUI
    "PyQt6>=6.6",

    # Utilities
    "httpx>=0.27",
    "pydantic>=2.0",
    "pynput>=1.7",
]
```

### Directory Structure

```
jarvis/
├── src/
│   └── jarvis/
│       ├── __init__.py
│       ├── main.py              # Entry point
│       ├── core/
│       │   ├── engine.py        # Main orchestrator
│       │   ├── event_bus.py     # Event system
│       │   └── config.py        # Configuration
│       ├── llm/
│       │   ├── ollama_client.py # LLM interface
│       │   ├── tools.py         # Tool definitions
│       │   └── prompts.py       # System prompts
│       ├── voice/
│       │   ├── stt.py           # Speech-to-text
│       │   ├── tts.py           # Text-to-speech
│       │   └── audio.py         # Audio I/O
│       ├── memory/
│       │   ├── short_term.py    # Conversation buffer
│       │   ├── long_term.py     # SQLite persistence
│       │   └── vectors.py       # LanceDB RAG
│       ├── plugins/
│       │   ├── manager.py       # Plugin loader
│       │   ├── interface.py     # Plugin base class
│       │   └── builtin/         # Core plugins
│       └── gui/
│           ├── app.py           # Qt application
│           ├── main_window.py   # Main UI
│           └── system_tray.py   # Tray icon
├── plugins/                     # User plugins
├── data/
│   ├── models/                  # Local model files
│   ├── voices/                  # Piper voice files
│   └── db/                      # SQLite + LanceDB
├── assets/                      # Icons, sounds
├── tests/
└── pyproject.toml
```

---

## 8. Performance Expectations

Based on RTX 4070 12GB + Ryzen 9800X3D:

| Operation | Expected Latency | Notes |
|-----------|------------------|-------|
| Wake word detection | <50ms | Silero VAD |
| Speech-to-text (5s audio) | 200-400ms | faster-whisper medium |
| LLM first token | 100-200ms | Ollama with 7B |
| LLM generation | 60-80 tok/s | Q4 quantization |
| Tool execution | Variable | Depends on tool |
| TTS first audio | 50-100ms | Piper streaming |
| End-to-end voice response | 1-2s | Simple queries |
| End-to-end with RAG | 2-3s | Complex queries |

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| VRAM exhaustion | Model hot-swapping, fallback to smaller models |
| Audio conflicts | Dedicated audio thread, proper device handling |
| Plugin crashes | Subprocess isolation, timeout enforcement |
| Ollama unavailable | Auto-start service, health checks |
| RAG irrelevance | Reranker, user feedback loop |

---

## 10. Recommendations Summary

| Component | Primary Choice | Reasoning |
|-----------|----------------|-----------|
| LLM Runtime | Ollama | Simplicity, Windows support, tool calling |
| Main Model | Qwen2.5-7B/14B | Quality/speed balance, tool calling |
| STT | faster-whisper | Speed, accuracy, CUDA support |
| TTS | Piper | CPU-only, real-time, quality |
| Vector DB | LanceDB | Lightweight, hybrid search |
| Embeddings | BGE-M3 | Quality, multilingual |
| GUI | PyQt6 | Native, system tray, mature |
| Plugin System | Custom event-driven | Flexible, async-native |
| Memory | SQLite + LanceDB | Hybrid short/long term |

---

## Next Steps

1. **Phase 1:** Core engine with Ollama integration
2. **Phase 2:** Voice pipeline (STT + TTS)
3. **Phase 3:** GUI with system tray
4. **Phase 4:** Memory and RAG
5. **Phase 5:** Plugin system
6. **Phase 6:** Polish and optimization

---

*Report generated by Agent Beta - Architecture Specialist*
*JARVIS Project - January 2026*
