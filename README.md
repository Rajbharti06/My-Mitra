# 🌱 MyMitra — Your AI Mentor, Friend & Guide

> **An old-soul companion for a modern world.**
> Built with privacy at the core, MyMitra is an emotional AI mentor that listens deeply, speaks gently, and helps you grow — one honest conversation at a time.

---

## 🧭 What is MyMitra?

**MyMitra** is a **privacy-first emotional AI companion** designed to feel less like software and more like a trusted friend.

It doesn’t chase hype. It respects silence. It remembers *only what you allow*. And it runs **locally**, so your thoughts stay yours.

Think of MyMitra as:

* 🤝 a **friend** when you feel alone
* 🧠 a **mentor** when you feel lost
* 🔥 a **motivator** when you feel tired
* 🎯 a **coach** when you want discipline

All wrapped into one calm, focused system.

---

## ✨ Core Philosophy (Why MyMitra Exists)

* **Privacy is non‑negotiable** — no cloud by default, encrypted storage only
* **Emotion before intelligence** — EQ > IQ
* **Local-first, offline-capable AI** — power without dependency
* **Human-like personalities** — warm, fallible, grounding
* **Slow tech** — fewer features, deeper impact

This is not another chatbot.
This is an **AI companion built to stay**.

---

## 🚀 Highlights

* 🔐 **Privacy-first architecture** with local encryption
* 🧬 **Multiple AI personalities**:

  * **Mitra** — calm, empathetic companion *(default)*
  * **Motivator** — energetic, uplifting push
  * **Mentor** — thoughtful, long-term guidance
  * **Coach** — structured, no‑nonsense accountability
* 🎭 **Personality selector** inside chat UI
* ⚡ **Fast Mode** for short, practical questions
* 🔄 **WebSocket-powered real-time chat**
* 🧠 **Offline LLM support** via Ollama
* 📓 **Journal, Habits, Mood & Progress tracking**

---

## 📸 Screenshots

See all screenshots and UI previews in:

```
docs/screenshots/README.md
```

Included sections:

* Dashboard
* Chat Interface
* Journal
* Habits
* Mood Tracking
* Progress & Insights

---

## 📥 Downloads & Requirements

### Required Software

* **Python** (3.10+): [https://www.python.org/downloads/](https://www.python.org/downloads/)
* **Node.js** (18+ LTS): [https://nodejs.org/](https://nodejs.org/)
* **Git**: [https://git-scm.com/downloads](https://git-scm.com/downloads)
* **Ollama** (Local LLM Runtime): [https://ollama.com/](https://ollama.com/)

### Recommended AI Models

```bash
ollama pull mistral:7b
```

Tested alternatives:

* `llama3:8b`
* `gemma:7b`
* `qwen2:7b`

Choose based on your hardware.

---

## ⚙️ Quick Start

### Clone the Repository

```bash
git clone https://github.com/Rajbharti06/My-Mitra
cd My-Mitra
```

### Backend Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
```

Create `backend/.env`:

```env
ENCRYPTION_KEY=your_32_char_secret_key_here
OLLAMA_BASE_URL=http://localhost:11434
MYMITRA_OLLAMA_MODEL=mistral:7b
```

Run backend:

```bash
uvicorn backend.app.main:app --reload --port 8000
```

---

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend runs at:

```
http://localhost:3000
```

---

## 🧠 How the AI Works

* **Primary LLM**: Local Ollama model
* **Fast Mode**: Lightweight heuristic path for quick questions
* **Fallback Mode**: Graceful personality-aware responses
* **Encrypted Storage**: Chats, journals & habits stored securely
* **Zero cloud dependency by default**

---

## 🖥️ System Requirements

### Minimum

* CPU: 4 cores
* RAM: 8 GB
* Disk: 5 GB free

### Recommended

* CPU: 8+ cores
* RAM: 16 GB
* Optional GPU (CUDA-supported Ollama builds)

Supported OS:

* Windows 10/11
* macOS 12+
* Modern Linux

---

## 📊 Performance & Caching

* Encrypted DB-backed cache for non-personal FAQs
* Cache TTL: 7 days
* Personal conversations are **never cached**
* Tunable fast-path limits for low-latency responses

---

## 🧪 Verification Checklist

```bash
python --version
node --version
git --version
ollama --version
```

Health check:

```bash
curl http://localhost:8000/health
```

LLM check:

```bash
ollama run mistral:7b
```

---

## 🗂️ Project Structure

```
backend/
  app/        # FastAPI app, routes, models
  llm/        # Ollama integration
frontend/     # React UI
```

---

## 🛣️ Roadmap (What’s Coming Next)

* 🔒 Multi-user encrypted profiles
* 📱 Android APK export
* 🧩 Custom personality creation
* 📆 Smart routines & study planning
* 🌙 Offline notifications
* 🔌 Optional external LLM APIs (OpenAI / Grok / Gemini)
* 🧠 Memory boundaries per personality

---

## 🤍 Who This Is For

* Students under pressure
* Builders working alone
* People healing quietly
* Anyone who wants an AI that **listens more than it talks**

---

## 📜 License & Contribution

This project is evolving.

* Contributions welcome (docs, UI, backend, ideas)
* Please respect the **privacy-first philosophy**

---

## 🌌 Final Note

MyMitra is built with patience.

Not to replace people —
but to remind you that **you’re not alone while becoming who you’re meant to be**.

If this resonates, ⭐ the repo and walk with us.
