# ATLAS — Autonomous Thinking & Learning Adaptive System

> A locally-running, fully offline AI assistant with voice, vision, system awareness, and proactive reasoning. No API keys. No cloud. Built entirely from scratch.

A personal Jarvis — built end to end over one continuous project, from a text-only chatbot to a fully voice-driven, screen-aware, self-monitoring AI with a native desktop GUI.

---

## What is ATLAS?

ATLAS started as a modular cognitive architecture and grew into a complete local-first AI assistant: it listens, talks, sees your screen, knows what you're doing on your computer, learns your habits over time, takes real actions on your behalf, and now has its own dedicated desktop app.

Everything runs on-device. No data leaves your machine.

---

## Features

### Voice
- Wake word detection ("Hey Jarvis"), fully offline
- Real-time speech-to-text via Whisper (CUDA-accelerated)
- Offline text-to-speech with a natural male voice (Coqui TTS)

### Tool Execution
- Open any installed app by name — no hardcoded paths, fuzzy-matches against Start Menu, drives, and Microsoft Store apps, with confidence-gated matching so it never guesses wrong
- Multi-command chaining ("open Chrome and tell me the time")
- System control — volume, brightness, lock, shutdown/restart (with spoken confirmation)
- Reminders with real natural-language time parsing ("remind me to call mom at 5pm")
- Weather, search, and general utility commands

### System Awareness
- Live tracking of active app, focus duration, CPU/RAM/battery
- Historical time-tracking per app, queryable by voice ("how much time did I spend on VS Code today")
- A standalone 24/7 background data collector, fully decoupled from the assistant itself, building toward personalized pattern learning

### Proactive Reasoning
- ATLAS can notice things and speak up — without being asked
- Chime-first delivery: a gentle notification sound, then only speaks if you respond, never interrupts forcefully
- Real triggers: long focus sessions, low battery, due reminders, distraction detection (content-aware — tells productive app-switching apart from doom-scrolling), late-night usage, daily usage summaries

### Local Vision
- Screen capture + LLaVA (via Ollama) — ask "what's on my screen" or "what's wrong with this code"
- Detects DRM-protected content (Netflix, Prime Video) instead of guessing at a black screen
- Everything processed in memory — screenshots are never written to disk

### Long-Term Memory
- ATLAS quietly extracts genuine, durable facts about you from conversation (where you live, preferences, relationships) using a local LLM
- Deduplicated, stored locally, reviewable any time

### Desktop GUI
- A real native app (Electron), not a browser tab — live conversation feed, system stats, today's usage breakdown, pattern-learning progress, reminders panel, and a mute control for proactive notifications
- One-click desktop launcher — starts voice, backend, and GUI together

---

## Architecture

```
ATLAS/
├── atlas_core/              # Identity, ethics, versioning, boot
├── cognition/               # Intent, reasoning, state, emotion, model routing
├── core/                    # Main ATLAS engine (process loop)
├── memory/                  # Goals, emotions, reminders, extracted long-term facts
├── interface/
│   ├── voice/               # STT, TTS, wake word, voice runtime
│   └── gui_electron/        # Native desktop GUI (Electron + Flask backend)
└── services/
    ├── tools/               # Tool matcher + all tool categories
    │   ├── tool_definitions/    # App/web, system, utility, dev, awareness, vision tools
    │   └── app_launcher_v0_1/   # Generic app finder (Start Menu, drives, UWP)
    └── monitoring/
        ├── system_awareness_v0_1/    # Live + historical activity tracking
        ├── proactive_engine_v0_1/    # Trigger detection, content classifier
        ├── pattern_learning_v0_1/    # Level 3 statistics engine
        └── memory_extraction_v0_1/   # LLM-based long-term fact extraction

E:\Requirements\DataCollector\   # Standalone 24/7 background activity logger (separate project)
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
Tool Matcher — instant match? execute directly, skip LLM
        ↓ (no match)
ATLAS Cognitive Engine / Ollama LLM
        ↓
Text-to-Speech — Coqui TTS VCTK VITS (male voice)
        ↓
Speaker output → back to listening
```

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM backend | Ollama (Mistral, LLaMA 3.1, DeepSeek Coder, Phi3) |
| Vision | LLaVA via Ollama |
| Speech-to-Text | faster-whisper (Whisper medium, CUDA accelerated) |
| Text-to-Speech | Coqui TTS — VCTK VITS, speaker p326 (male) |
| Wake Word | OpenWakeWord |
| Desktop GUI | Electron + Flask (local HTTP bridge to Python backend) |
| System awareness | psutil, pywin32 |
| Language | Python 3.11, JavaScript (GUI only) |

---

## Requirements

- MAKE SURE DEVELOPER MODE IS ON B4 RUNNING. ( SETTINGS-->PRIVACYA AND SECURITY-->SEARCH 'DEVELOPER')

### System
- Windows 10/11 (64-bit)
- *NVIDIA GPU with CUDA 12.4 (for GPU-accelerated STT and vision)*
- [Ollama](https://ollama.com) installed and running
- [eSpeak-ng](https://github.com/espeak-ng/espeak-ng/releases) installed
- [Node.js](https://nodejs.org) (for the Electron GUI)

### Ollama Models
```bash
ollama pull mistral #done
ollama pull llama3.1:8b 
ollama pull deepseek-coder:6.7b 
ollama pull phi3 #done
ollama pull llava
```

### Python Dependencies
```bash
pip install -r ATLAS/requirements.txt
```

### GUI Dependencies
```bash
cd ATLAS/interface/gui_electron
npm install
```

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/Samarth229/ATLAS-Adaptive-Thinking-and-Learning-Autonomous-System.git
cd ATLAS
```

### 2. Create a Python 3.11 virtual environment
```bash
py -3.11 -m venv venv_voice
venv_voice\Scripts\activate.bat
pip install -r ATLAS/requirements.txt
```

### 3. Set environment variables
```bash
setx HF_HOME "E:\Requirements\huggingface"
setx TTS_HOME "E:\Requirements\coqui_models"
setx OLLAMA_MODELS "E:\Requirements\.ollama\models"
```

### 4. Install GUI dependencies
```bash
cd ATLAS/interface/gui_electron
npm install
```

---

## Running ATLAS

## OPTION A : One-click (voice + GUI together)
```bash
python launch_atlas.py
```
Launches voice mode, the local Flask backend, and the Electron GUI together. Closing the GUI window shuts everything down cleanly.

### OPTION B Voice only
```bash
cd ATLAS
python main.py voice
```

### OPTION C Text mode
```bash
cd ATLAS
python main.py
```

Say **"Hey Jarvis"** to activate.

---

## Project Status — Version 1 Complete

| Capability | Status |
|---|---|
| Voice I/O | ✅ |
| Tool execution + generic app launcher | ✅ |
| System awareness (live + historical) | ✅ |
| Proactive reasoning (rule-based + content-aware) | ✅ |
| Local vision | ✅ |
| Long-term memory extraction | ✅ |
| Native desktop GUI | ✅ |
| Pattern learning (Level 3) | 🔄 Foundation built, learning from live data, not yet wired into behavior |

---

## Roadmap

- [x] Voice I/O (wake word, STT, TTS)
- [x] Tool execution layer + generic app launcher
- [x] System awareness (live state + historical tracking)
- [x] Proactive reasoning (reminders, focus, battery, distraction detection, daily summaries)
- [x] Local vision (screen understanding via LLaVA)
- [x] Long-term memory extraction
- [x] Native desktop GUI (Electron)
- [ ] Pattern learning fully wired into live trigger thresholds (needs weeks of accumulated data)
- [ ] Long-term memory actually influencing live conversation responses
- [ ] Custom wake word ("Hey ATLAS")

---

## Built By

**Samarth Kadam** — B.Tech Computer Science, VIT Bhopal  
Personal AI systems project — started February 2025, version 1 completed June 2026

**Kousthubh Vasudevan** - B.Tech Computer Science, VIT Bhopal  
Intern.

---

## License

MIT License — use freely, build on top of it.
