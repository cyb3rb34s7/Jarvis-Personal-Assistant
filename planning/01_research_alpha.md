# JARVIS Research Report - Agent Alpha (Research Lead)
## Comprehensive Analysis of Open-Source Personal Assistant Projects

**Date:** January 29, 2026
**Purpose:** Evaluate existing projects for architecture inspiration, code reuse, and lessons learned
**Hardware Target:** RTX 4070 12GB, 32GB RAM, Ryzen 9800X3D (100% local operation)

---

## Executive Summary

After extensive research, I've identified 12 relevant open-source projects spanning voice assistants, local LLM frameworks, and personal knowledge management systems. The landscape has evolved significantly since 2023 with the rise of local LLMs, making truly private personal assistants feasible. However, most projects still have significant gaps - particularly in combining voice I/O, local LLM intelligence, and structured task management into a cohesive experience.

**Key Finding:** No single project does everything JARVIS needs. The best approach is likely a modular architecture borrowing concepts from multiple projects.

---

## Project Analysis

### 1. Leon AI

**Repository:** https://github.com/leon-ai/leon
**Stars:** ~14,000+ (as of early 2025)
**License:** MIT
**Primary Language:** TypeScript/Node.js (v2), Python (v1)

#### What It Does Well
- Clean modular architecture with "skills" as plugins
- Excellent documentation and developer experience
- Active Discord community with responsive maintainers
- Multi-language support (English, French, etc.)
- Offline-first design philosophy
- Version 2 rewrite shows modern best practices
- Built-in NLU (Natural Language Understanding) engine
- Support for multiple STT/TTS providers

#### What It Does Poorly
- V2 rewrite is still incomplete as of 2025
- No native local LLM integration (designed for rule-based NLU)
- Limited voice interaction capabilities compared to commercial assistants
- Heavy Node.js dependency might complicate Python LLM integration
- Skills ecosystem is smaller than it could be
- Wake word detection is basic

#### Tech Stack
- Core: TypeScript, Node.js
- NLU: Custom engine + optional Hugging Face
- STT: Mozilla DeepSpeech, Google Cloud, Watson
- TTS: Flite, Google Cloud, Amazon Polly
- Database: SQLite
- API: Fastify

#### Reuse Potential: MEDIUM-HIGH
- **Skill architecture pattern** is excellent and worth emulating
- Plugin system design could inform JARVIS module structure
- Documentation approach is a good template
- Would need significant adaptation for local LLM focus

#### Activity Level: ACTIVE (but slow)
- V2 development ongoing but pace is measured
- GitHub shows regular commits, active issues
- Core team of 3-5 active contributors

---

### 2. Mycroft AI / OVOS (Open Voice OS)

**Repository:** https://github.com/MycroftAI/mycroft-core (legacy)
**OVOS Fork:** https://github.com/OpenVoiceOS
**Stars:** ~6,400+ (Mycroft), growing (OVOS)
**License:** Apache 2.0
**Primary Language:** Python

#### What It Does Well
- Most mature open-source voice assistant project
- Extensive skill marketplace (hundreds of skills)
- Hardware product experience (Mark I, Mark II)
- Proper wake word detection (Precise, Porcupine)
- Robust message bus architecture
- OVOS fork is actively maintained and modernized
- Good STT/TTS abstraction layers
- Real-world deployment experience

#### What It Does Poorly
- Mycroft Inc. went bankrupt in 2023, causing fragmentation
- Original codebase has legacy Python 2 artifacts
- Cloud dependency in many original skills
- Complex setup process for full functionality
- Resource hungry for full deployment
- Documentation scattered across Mycroft/OVOS
- LLM integration is bolted-on, not native

#### Tech Stack
- Core: Python 3.8+
- Message Bus: Custom WebSocket-based
- Wake Word: Precise, Porcupine, Snowboy
- STT: Mozilla DeepSpeech, Vosk, Whisper (via plugins)
- TTS: Mimic, Mimic3, Coqui
- Skills: Python modules with intent decorators

#### Reuse Potential: HIGH
- **Message bus architecture** is production-tested
- Wake word and STT pipeline is reusable
- Skill decorator pattern is clean
- OVOS plugins for Whisper STT already exist
- Could serve as foundation if willing to accept complexity

#### Activity Level: ACTIVE (OVOS)
- Mycroft core is abandoned/archived
- OVOS is very active with regular releases
- Strong community momentum post-Mycroft bankruptcy

---

### 3. Jasper

**Repository:** https://github.com/jasper-clients/jasper-client
**Stars:** ~5,500+
**License:** MIT
**Primary Language:** Python

#### What It Does Well
- Simple, educational codebase
- Good starting point for understanding voice assistant architecture
- Lightweight and runs on Raspberry Pi
- Modular microphone/speaker handling

#### What It Does Poorly
- **ABANDONED** - No updates since 2016-2017
- Python 2 codebase (incompatible with modern libraries)
- Outdated STT/TTS integrations
- No LLM awareness whatsoever
- Documentation is severely outdated
- Won't run on modern systems without significant work

#### Tech Stack
- Core: Python 2.7 (!)
- STT: PocketSphinx, Google STT (deprecated API)
- TTS: eSpeak, Festival
- Profile: YAML configuration

#### Reuse Potential: LOW
- Historical interest only
- Architecture concepts might inspire, but code is unusable
- Demonstrates what NOT to do (tight coupling, no async)

#### Activity Level: DEAD
- Last meaningful commit: 2016
- Issues are unanswered
- Project should be considered archived

---

### 4. Rhasspy

**Repository:** https://github.com/rhasspy/rhasspy
**Stars:** ~2,200+
**License:** MIT
**Primary Language:** Python

#### What It Does Well
- **100% offline by design** - perfect alignment with JARVIS goals
- Excellent Home Assistant integration
- Modular audio pipeline (wake word -> STT -> intent -> TTS)
- Supports multiple languages
- Docker deployment option
- Satellite/base station architecture for distributed setups
- Intent recognition without cloud
- Well-documented HTTP API

#### What It Does Poorly
- Focused on home automation commands, not general assistance
- No built-in LLM integration
- Intent system is rule-based (fsticuffs, fuzzywuzzy)
- UI is functional but dated
- Learning curve for custom intent training
- Version 3 rewrite has been slow

#### Tech Stack
- Core: Python 3.7+
- Wake Word: Porcupine, Snowboy, Raven
- STT: Kaldi, Vosk, DeepSpeech, Whisper
- TTS: Larynx, MaryTTS, eSpeak
- Intent: fsticuffs, fuzzywuzzy, Rasa NLU
- API: HTTP/WebSocket/MQTT

#### Reuse Potential: HIGH
- **Audio pipeline architecture** is excellent reference
- Offline-first approach matches JARVIS requirements
- STT integration code could be directly useful
- Home Assistant integration patterns valuable

#### Activity Level: MODERATE
- Core v2 is stable but maintenance mode
- v3 (next-gen) in development
- Community maintains various components

---

### 5. LocalAI

**Repository:** https://github.com/mudler/LocalAI
**Stars:** ~20,000+
**License:** MIT
**Primary Language:** Go

#### What It Does Well
- **Drop-in OpenAI API replacement** - huge ecosystem compatibility
- Supports many model formats (GGUF, GGML, transformers)
- Built-in Whisper STT support
- Text-to-speech with various backends
- Image generation support
- GPU acceleration (CUDA, ROCm, Metal)
- Active development with frequent releases
- Embeddings API for semantic search
- Function calling support

#### What It Does Poorly
- Not a personal assistant - just an API server
- No voice interaction handling
- No wake word or audio capture
- Configuration can be complex for optimal performance
- Memory management requires tuning
- Go codebase less accessible for Python developers

#### Tech Stack
- Core: Go
- LLM: llama.cpp, GPT4All, rwkv.cpp
- STT: Whisper.cpp
- TTS: Piper, bark
- API: OpenAI-compatible REST

#### Reuse Potential: VERY HIGH
- **Could serve as JARVIS's LLM backend**
- OpenAI API compatibility means easy integration
- Whisper integration handles STT
- Embeddings API enables semantic search
- Well-tested on consumer GPUs including RTX 4070

#### Activity Level: VERY ACTIVE
- Daily commits
- Large contributor base
- Regular releases and improvements
- Strong Discord community

---

### 6. Ollama

**Repository:** https://github.com/ollama/ollama
**Stars:** ~70,000+
**License:** MIT
**Primary Language:** Go

#### What It Does Well
- **Simplest local LLM experience** - just works
- Excellent model management (pull, run, delete)
- Native Mac/Windows/Linux support
- Automatic GPU detection and utilization
- Growing model library with easy access
- Memory-efficient model loading
- REST API is simple and well-documented
- Multimodal support (vision models)
- Active development, fast iteration

#### What It Does Poorly
- Not an assistant, just an LLM server
- No voice capabilities
- No built-in embeddings server (added recently but basic)
- Less configurable than LocalAI
- Model customization options limited
- No function calling (as of early 2025)

#### Tech Stack
- Core: Go
- LLM: llama.cpp
- API: REST (simple)
- Format: GGUF models

#### Reuse Potential: VERY HIGH
- **Primary candidate for JARVIS LLM backend**
- Simpler than LocalAI for basic use cases
- RTX 4070 12GB handles most 7B-13B models easily
- Could use Ollama for LLM + separate Whisper for STT

#### Activity Level: EXTREMELY ACTIVE
- Most active local LLM project
- Daily commits, weekly releases
- Huge community
- Corporate backing (believed to have funding)

---

### 7. Private GPT

**Repository:** https://github.com/imartinez/privateGPT
**Stars:** ~50,000+
**License:** Apache 2.0
**Primary Language:** Python

#### What It Does Well
- **Document Q&A with local LLMs** - RAG done right
- Production-ready RAG implementation
- Supports multiple LLM backends (Ollama, llama.cpp, etc.)
- Vector store integration (Chroma, Qdrant)
- Ingestion pipeline for various document types
- Clean Python codebase
- Good API design
- UI included

#### What It Does Poorly
- Focused on document Q&A, not general assistant
- No voice interface
- No task management features
- Heavy dependencies
- Can be resource intensive
- UI is basic

#### Tech Stack
- Core: Python 3.10+
- LLM: Ollama, llama-cpp-python
- Embeddings: HuggingFace, OpenAI-compatible
- Vector Store: Chroma, Qdrant
- Framework: FastAPI, Gradio
- RAG: LlamaIndex

#### Reuse Potential: HIGH
- **RAG architecture is directly applicable** to JARVIS knowledge base
- Document ingestion pipeline reusable
- Vector search patterns valuable
- Could inform "save links/articles" feature

#### Activity Level: ACTIVE
- Regular updates
- Large contributor base
- Good issue response time

---

### 8. GPT4All

**Repository:** https://github.com/nomic-ai/gpt4all
**Stars:** ~65,000+
**License:** MIT
**Primary Language:** C++/Python

#### What It Does Well
- Cross-platform desktop app with GUI
- LocalDocs feature for document chat
- Simple model downloading
- Chat interface out of the box
- Python bindings available
- Nomic backing provides resources
- Regular model releases

#### What It Does Poorly
- Desktop app is Electron (heavy)
- No voice interface
- LocalDocs RAG is basic compared to PrivateGPT
- API is limited
- Not designed as a framework
- Customization options limited

#### Tech Stack
- Core: C++, Python bindings
- GUI: Qt/QML
- LLM: Custom llama.cpp integration
- LocalDocs: Basic RAG

#### Reuse Potential: MEDIUM
- Good reference for desktop LLM integration
- Python bindings could be useful
- LocalDocs shows basic RAG approach
- Not ideal as foundation - better as reference

#### Activity Level: ACTIVE
- Regular releases
- Corporate backing (Nomic AI)
- Active community

---

### 9. Khoj

**Repository:** https://github.com/khoj-ai/khoj
**Stars:** ~8,000+
**License:** AGPL-3.0
**Primary Language:** Python

#### What It Does Well
- **Personal AI with memory** - close to JARVIS vision
- Supports local LLMs (Ollama, llama.cpp)
- Note/document search and retrieval
- Chat with your data
- Multiple interfaces (web, Emacs, Obsidian)
- Image search support
- Scheduled tasks/automation
- Self-hostable

#### What It Does Poorly
- No voice interface
- AGPL license may be restrictive
- Setup can be complex
- Resource requirements high for full features
- Web UI centric (less suited for desktop app)
- Sync features need cloud for full functionality

#### Tech Stack
- Core: Python 3.10+
- LLM: OpenAI, Ollama, llama.cpp
- Search: Embeddings + Vector DB
- Storage: SQLite, Postgres
- API: FastAPI
- UI: Web-based (React)

#### Reuse Potential: MEDIUM-HIGH
- **Note organization patterns directly applicable**
- Search/retrieval architecture useful
- Scheduler implementation interesting
- License (AGPL) requires consideration

#### Activity Level: VERY ACTIVE
- Regular commits and releases
- Active Discord community
- Two co-founders actively developing

---

### 10. Home Assistant Voice (Assist)

**Repository:** https://github.com/home-assistant/core (part of HA)
**Related:** Wyoming Protocol
**Stars:** 70,000+ (full Home Assistant)
**License:** Apache 2.0
**Primary Language:** Python

#### What It Does Well
- Production-grade voice pipeline
- Wyoming protocol for modular audio
- Local STT via Whisper
- Local TTS via Piper
- Wake word via openWakeWord
- Massive integration ecosystem
- Very active development
- Real-world usage by millions

#### What It Does Poorly
- Tightly coupled to Home Assistant
- Designed for home control, not general assistance
- Complex to extract just voice components
- Intent system is home-automation focused
- Heavy infrastructure for just voice features

#### Tech Stack
- Core: Python 3.11+
- Voice: Wyoming protocol
- STT: Whisper, Vosk
- TTS: Piper
- Wake Word: openWakeWord, Porcupine
- Intent: Hassil

#### Reuse Potential: MEDIUM
- **Wyoming protocol** is worth studying
- Piper TTS is excellent and standalone
- openWakeWord is reusable
- Voice pipeline concepts valuable
- Direct code reuse limited due to HA coupling

#### Activity Level: EXTREMELY ACTIVE
- One of most active open source projects
- Professional development team
- Massive community

---

### 11. Langchain + LangGraph

**Repository:** https://github.com/langchain-ai/langchain
**Stars:** ~80,000+
**License:** MIT
**Primary Language:** Python

#### What It Does Well
- **De facto standard for LLM application development**
- Excellent abstractions for chains, agents, tools
- Huge integration ecosystem
- Well-documented
- LangGraph adds stateful agent workflows
- Memory abstractions built-in
- RAG utilities comprehensive
- Active development

#### What It Does Poorly
- Can be over-engineered for simple use cases
- Abstraction layers add complexity
- Breaking changes in rapid development
- Performance overhead from abstractions
- Learning curve is significant
- Documentation can lag behind features

#### Tech Stack
- Core: Python
- LLM: Any (OpenAI, Ollama, etc.)
- Vector Stores: Many supported
- Tools: Extensive integrations

#### Reuse Potential: HIGH
- **Agent framework for JARVIS intelligence layer**
- Tool use patterns directly applicable
- Memory abstractions useful for conversation
- RAG chains well-tested
- Consider if complexity is justified

#### Activity Level: EXTREMELY ACTIVE
- Daily commits
- Large team
- VC funded
- Rapid iteration

---

### 12. Whisper + Whisper.cpp

**Repository:** https://github.com/openai/whisper (original)
**Repository:** https://github.com/ggerganov/whisper.cpp (C++ port)
**Stars:** 60,000+ / 30,000+
**License:** MIT
**Primary Language:** Python / C++

#### What It Does Well
- **Best open-source STT available**
- Multiple model sizes (tiny to large)
- Excellent accuracy
- Language detection
- whisper.cpp is highly optimized
- GPU acceleration
- Real-time capable with small models
- Active development on both

#### What It Does Poorly
- Original Whisper is resource intensive
- Latency can be high for larger models
- Streaming support limited in original
- No wake word detection
- Just transcription - no NLU
- whisper.cpp API less Pythonic

#### Tech Stack
- Original: PyTorch
- C++ Port: Pure C/C++, CUDA, Metal

#### Reuse Potential: ESSENTIAL
- **Must-have component for JARVIS**
- whisper.cpp for performance
- faster-whisper Python bindings excellent
- RTX 4070 handles medium model in real-time

#### Activity Level: ACTIVE
- whisper.cpp very actively maintained
- Original Whisper stable, fewer updates
- Community ports/bindings thriving

---

## Additional Notable Projects

### Piper TTS
- https://github.com/rhasspy/piper
- High-quality local TTS
- Fast on CPU
- Many voices available
- **Strongly recommended for JARVIS TTS**

### OpenWakeWord
- https://github.com/dscripka/openWakeWord
- Custom wake word training
- Runs on CPU
- Good accuracy
- **Consider for wake word detection**

### faster-whisper
- https://github.com/SYSTRAN/faster-whisper
- CTranslate2-based Whisper
- 4x faster than original
- Lower memory usage
- **Best Python Whisper option for JARVIS**

---

## Comparative Matrix

| Project | Voice I/O | Local LLM | Task Mgmt | Knowledge Base | GUI | Activity |
|---------|-----------|-----------|-----------|----------------|-----|----------|
| Leon AI | Partial | No | Yes | No | Web | Active |
| OVOS/Mycroft | Yes | Plugin | Yes | No | Optional | Active |
| Jasper | Yes | No | No | No | No | Dead |
| Rhasspy | Yes | No | No | No | Web | Moderate |
| LocalAI | API only | Yes | No | Embeddings | No | Very Active |
| Ollama | No | Yes | No | No | No | Extremely Active |
| PrivateGPT | No | Yes | No | Yes | Web | Active |
| GPT4All | No | Yes | No | Basic | Desktop | Active |
| Khoj | No | Yes | Partial | Yes | Web | Very Active |
| HA Voice | Yes | No | HA only | No | HA | Extremely Active |
| Langchain | No | Yes | Agents | Yes | No | Extremely Active |
| Whisper | Input only | No | No | No | No | Active |

---

## Recommendations for JARVIS Architecture

### Recommended Component Stack

1. **LLM Backend:** Ollama (simplicity) or LocalAI (features)
   - RTX 4070 12GB can run Llama 3 8B, Mistral 7B comfortably
   - Consider Mixtral 8x7B with quantization for better quality

2. **Speech-to-Text:** faster-whisper or whisper.cpp
   - Medium model provides good accuracy/speed balance
   - GPU acceleration essential

3. **Text-to-Speech:** Piper
   - Fast, high-quality, many voices
   - CPU is sufficient, leaving GPU for LLM/STT

4. **Wake Word (if needed):** openWakeWord
   - Custom "Hey JARVIS" wake word possible
   - Low resource usage

5. **RAG/Knowledge Base:** Inspired by PrivateGPT/Khoj
   - ChromaDB or Qdrant for vector storage
   - LlamaIndex or Langchain for orchestration

6. **Agent Framework:** Langchain/LangGraph or custom
   - Depends on complexity needs
   - Custom might be simpler for defined use cases

### Architecture Patterns to Emulate

1. **Leon AI's Skill System** - Modular capabilities
2. **OVOS's Message Bus** - Component communication
3. **Rhasspy's Audio Pipeline** - Voice processing flow
4. **PrivateGPT's RAG** - Knowledge retrieval
5. **Khoj's Memory** - Conversation persistence

### What to Avoid

1. **Jasper's tight coupling** - Keep components separate
2. **Over-engineering with Langchain** - Start simple
3. **Electron for GUI** - Use lighter alternatives (PyQt, Dear PyGui)
4. **Cloud dependencies** - Even optional ones creep in

---

## Critical Assessment

### Projects That Are Overhyped
- **GPT4All**: Desktop app is mediocre, better to use Ollama directly
- **AutoGPT/AgentGPT**: Autonomous agents are unreliable for personal use
- **Many "JARVIS clone" repos**: Usually abandoned proof-of-concepts

### Projects That Are Underrated
- **Rhasspy**: Excellent offline voice architecture, under-appreciated
- **OVOS**: Continuing Mycroft's work with improvements
- **Piper TTS**: Best local TTS, not widely known outside HA community
- **faster-whisper**: Significant improvement over original Whisper

### The Gap JARVIS Can Fill
No existing project combines:
- Quality voice interaction (push-to-talk or wake word)
- Local LLM intelligence
- Structured task/reminder management
- Semantic knowledge base for saved content
- Clean desktop GUI
- Modular, maintainable architecture

This is the opportunity for JARVIS.

---

## Next Steps for Other Agents

1. **Agent Beta (Architecture)**: Design modular system using above components
2. **Agent Gamma (Voice)**: Deep dive into faster-whisper + Piper integration
3. **Agent Delta (Knowledge)**: Prototype RAG system for links/notes
4. **Agent Epsilon (UI)**: Evaluate GUI frameworks for desktop app

---

*Report compiled by Agent Alpha (Research Lead)*
*Based on knowledge through May 2025 + domain expertise*
*Note: Live web verification was unavailable; recommend manual verification of current project status*
