# MyMitra — AI Companion

> A presence engine, not a chatbot.
> MyMitra listens, remembers, and grows with you — running entirely on your machine.

---

## What is MyMitra?

MyMitra is a **privacy-first AI companion** built to feel like a person who knows you, not software describing itself.

It detects your emotional state, adapts its tone, tracks your growth over time, and never leaks system language into conversation. Your data stays local. Your thoughts stay yours.

**Personalities:**
- **Mitra** — warm, present, minimal. The default.
- **Mentor** — thoughtful, long-view guidance
- **Motivator** — energetic, forward-pushing
- **Coach** — structured, action-oriented

---

## Architecture

```
frontend/          React + Tailwind + Framer Motion
backend/app/       FastAPI
  soul_engine.py   — organic interjections, meaning moments
  mitra_state.py   — unified identity layer (emotion + memory + growth → single LLM context)
  care_layer.py    — warmth injection, human timing delays
  initiative_engine.py — proactive check-ins (same-day, next-morning, 3-day)
  smart_tasks.py   — gentle automation (focus timer, habit creation, breathing)
  stream_routes.py — full soul loop via SSE streaming
  growth_engine.py — milestone detection, relationship arc
  growth_routes.py — /growth/arc, /growth/topics, /growth/milestone
  routes.py        — all REST endpoints incl. mood log/history
backend/llm/       Ollama integration + personality system
chroma_db/         Vector memory (opt-in long-term memory)
```

**Storage:** SQLite (encrypted) · ChromaDB (vector embeddings) · localStorage (offline fallback)

---

## Requirements

- Python 3.10+
- Node.js 18+ LTS
- [Ollama](https://ollama.com/) with at least one model pulled

**Tested models:**

```bash
ollama pull mistral        # recommended, ~4GB
ollama pull phi            # lighter, ~1.6GB
ollama pull llama3:8b      # higher quality, ~5GB
```

Cloud-routed models via Ollama (e.g. `kimi-k2.5:cloud`) also work if available in your Ollama install.

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/Rajbharti06/My-Mitra
cd My-Mitra
```

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env`:

```env
SECRET_KEY=your_32_char_secret_here
ENCRYPTION_KEY=your_32_char_encryption_key
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

Start backend:

```bash
uvicorn app.main:app --reload --port 8000
```

For local dev without auth (auto-creates a test user):

```bash
ALLOW_TEST_TOKEN=true OLLAMA_MODEL=mistral uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm start
```

Opens at `http://localhost:3000`.

### 4. Verify

```bash
curl http://localhost:8000/api/v1/health
# → {"status":"ok","message":"MyMitra backend is running"}
```

---

## How It Works

Every message goes through the **soul loop**:

```
user message
  → emotion detection
  → unified Mitra state (mitra_state.py)
      fuses: emotion + memory + growth arc + personality
      → single coherent LLM context
  → human timing pause (feels like thinking, not loading)
  → care injection (warmth phrase if vulnerable)
  → LLM response via Ollama
  → presence filter (strips any leaked AI/system language)
  → anti-repeat check (never same response twice in a row)
  → SSE token stream to frontend
```

The frontend renders tokens as they arrive — no waiting for full response.

**Presence filter** — a safety layer that catches phrases like "I'm having technical difficulties" or "as an AI" before they reach the user. If caught, replaces with a calm presence phrase ("I'm here. Go on.").

**Soul prompt** — built fresh each message from the user's emotional trajectory, relationship phase, memory fragments, and growth arc. Injected directly into the LLM context so it responds as a person who knows you, not as a fresh chatbot.

---

## Features

| Feature | Status |
|---|---|
| SSE streaming chat | Live |
| Emotion detection (8 categories) | Live |
| 5 AI personalities | Live |
| Soul layer (care, timing, interjection) | Live |
| Growth arc + milestone tracking | Live |
| Manual mood check-in + 7-day chart | Live |
| Proactive initiative messages | Live |
| Vector long-term memory (opt-in) | Live |
| Journal | Live |
| Habits + streaks | Live |
| Encrypted local storage | Live |
| Offline fallback (localStorage) | Live |
| WebSocket typing indicators | Live |

---

## API Reference

```
POST /api/v1/chat/stream       SSE streaming chat
GET  /api/v1/chat/initiative   Proactive check-in message
GET  /api/v1/chat/personalities All available personalities
GET  /api/v1/growth/arc        Relationship arc + phase
GET  /api/v1/growth/topics     Life topics discussed
POST /api/v1/growth/milestone  Detect + record milestone
POST /api/v1/mood/log          Log manual mood check-in
GET  /api/v1/mood/history      Recent mood entries
GET  /api/v1/habits            Habit list
POST /api/v1/habits            Create habit
GET  /api/v1/journals          Journal entries
GET  /api/v1/health            Backend health
```

---

## System Requirements

**Minimum:** 4-core CPU, 8 GB RAM, 5 GB disk
**Recommended:** 8+ cores, 16 GB RAM (for larger Ollama models)
**GPU:** Optional — CUDA-supported Ollama builds will use it automatically

Supported: Windows 10/11, macOS 12+, Linux

---

## Project Structure

```
backend/
  app/
    main.py              FastAPI app + DB init
    routes.py            REST endpoints
    stream_routes.py     SSE soul loop
    soul_engine.py       Interjections, meaning moments
    mitra_state.py       Unified identity layer
    care_layer.py        Warmth injection, timing
    initiative_engine.py Proactive check-ins
    smart_tasks.py       Gentle automation detection
    growth_engine.py     Milestone + arc computation
    growth_routes.py     Growth API endpoints
    mitra_core.py        Intent detection, emotion mapping
    models.py            SQLAlchemy models
    crud.py              DB operations
    security.py          JWT auth
  llm/
    ollama_model.py      Ollama client + personality system
  vector_memory.py       ChromaDB long-term memory
  encryption_utils.py    SQLite encryption

frontend/
  src/
    Chat.js              Full streaming SSE chat UI
    App.js               Sidebar + emotion-reactive background
    index.css            Design system (glassmorphism, emotion colors)
    pages/
      MoodTracking.js    Mood check-in + 7-day chart
      GrowthTimeline.jsx Growth arc + milestones
      Insights.js        Growth journey view
    services/
      api.js             All backend API calls
```

---

## Roadmap

- Multi-user encrypted profiles
- Android APK export
- Custom personality creation
- Smart study planner
- Offline push notifications
- Memory boundaries per personality

---

## Philosophy

MyMitra is built on one rule: **never break presence**.

Users forgive slow responses. They don't forgive a companion that says "I'm having technical difficulties."

Every layer — soul prompt, presence filter, care injection, human timing — exists to protect that one thing.

---

## Who This Is For

Students under pressure. Builders working alone. People healing quietly. Anyone who wants an AI that listens more than it talks.

---

## License

MIT. Contributions welcome — respect the privacy-first philosophy.
