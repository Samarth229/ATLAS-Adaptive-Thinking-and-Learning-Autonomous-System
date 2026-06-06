# ATLAS — Autonomous Thinking & Learning Adaptive System

> A locally-running, fully offline AI assistant with modular cognitive architecture and voice I/O. No API keys. No cloud. Built from scratch.

---

## What is ATLAS?

ATLAS is a personal AI system designed to run entirely on your local machine. It combines a modular cognitive engine with voice interaction — wake word detection, speech-to-text, and text-to-speech — all offline, all on-device.

Think of it as a foundation for building your own Jarvis.

---

## Features

- **Voice I/O** — Wake word detection, real-time STT via Whisper, offline TTS with male voice
- **Modular cognitive architecture** — Intent engine, reasoning engine, state engine, emotion tracking
- **Multi-model routing** — Automatically routes queries to the best local LLM (Mistral, LLaMA, DeepSeek, Phi)
- **Persistent memory** — Tracks goals, emotions, interaction history, and cognitive weights across sessions
- **Ethics layer** — Hardcoded principles that cannot be overridden at runtime
- **Dual mode** — Run as text CLI or full voice assistant

---

## Architecture

```
ATLAS/
├── atlas_core/          # Identity, ethics, versioning, boot
├── cognition/           # Intent, reasoning, state, emotion, model routing
│   ├── intent_engine/
│   ├── reasoning/
│   ├── models/          # Adapters + router for Ollama models
│   ├── state/
│   ├── behavior/        # Goal conflict, decision arbitration, priority
│   └── meta/            # Confidence, clarification, volatility engines
├── memory/              # Persistent goals, emotions, interaction logs
├── core/                # Main ATLAS engine (process loop)
├── interface/
│   └── voice/           # STT, TTS, wake word, voice runtime
└── services/            # Runtime daemon, event bus, tool registry
```

---

## Voice Pipeline

```
Microphone (always listening)
        ↓
Wake Word Detection — OpenWakeWord
        ↓
Speech-to-Text — faster-whisper (Whisper medium, CUDA)
        ↓
ATLAS Cognitive Engine
        ↓
Text-to-Speech — Coqui TTS VCTK VITS (male voice)
        ↓
Speaker output
        ↓
Back to listening
```

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM backend | Ollama (Mistral, LLaMA 3.1, DeepSeek Coder, Phi3) |
| Speech-to-Text | faster-whisper (Whisper medium, CUDA accelerated) |
| Text-to-Speech | Coqui TTS — VCTK VITS, speaker p326 (male) |
| Wake Word | OpenWakeWord |
| Language | Python 3.11 |
| UI | Rich (terminal) |

---

## Requirements

### System
- Windows 10/11 (64-bit)
- NVIDIA GPU with CUDA 12.x (for GPU-accelerated STT)
- [Ollama](https://ollama.com) installed and running
- [eSpeak-ng](https://github.com/espeak-ng/espeak-ng/releases) installed

### Ollama Models
Pull these before running:
```bash
ollama pull mistral
ollama pull llama3.1:8b
ollama pull deepseek-coder:6.7b
ollama pull phi3
```

### Python Dependencies
```bash
pip install -r requirements.txt
```

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/ATLAS.git
cd ATLAS
```

### 2. Create a Python 3.11 virtual environment
```bash
py -3.11 -m venv venv_voice
```

Activate it:
```bash
# Windows CMD
venv_voice\Scripts\activate.bat

# Windows PowerShell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
venv_voice\Scripts\Activate.ps1
```

### 3. Install dependencies
```bash
pip install -r ATLAS/requirements.txt
```

### 4. Set environment variables
Point model downloads to your preferred location:
```bash
setx HF_HOME "E:\Requirements\huggingface"
setx TTS_HOME "E:\Requirements\coqui_models"
setx OLLAMA_MODELS "E:\Requirements\.ollama\models"
```

### 5. Pre-download models (first run only)
```python
# Whisper medium
from faster_whisper import WhisperModel
WhisperModel("medium", device="cpu", compute_type="int8", download_root=r"E:\Requirements\huggingface\hub")

# Coqui TTS (auto-downloads on first voice run)
# OpenWakeWord (auto-downloads on first voice run)
```

---

## Running ATLAS

### Text mode (default)
```bash
cd ATLAS
python main.py
```

### Voice mode
```bash
cd ATLAS
python main.py voice
```

Say **"Hey Jarvis"** to activate. ATLAS will respond with a male voice.

---

## Project Status

| Version | Status |
|---|---|
| v0.1.0 | Active development |
| Boot count | 117+ |
| Runtime version | v0.5 |
| Voice | ✅ Integrated |
| Tool execution | 🔄 In progress |
| GUI dashboard | 📋 Planned |

---

## Roadmap

- [x] Modular cognitive architecture
- [x] Multi-LLM routing via Ollama
- [x] Persistent memory system
- [x] Voice I/O (STT + TTS + wake word)
- [ ] Tool execution layer (open apps, control system)
- [ ] System awareness (active window, process monitoring)
- [ ] Proactive reasoning loop
- [ ] Vision input (screen capture + LLaVA)
- [ ] GUI dashboard

---

## Built By

**Samarth Kadam** — B.Tech Computer Science, VIT Bhopal  
Personal AI systems project — started February 2025

---

## License

MIT License — use freely, build on top of it.
