# Memory Infrastructure

This project is a “memory layer” for an AI product. Think of it like a personal library and a smart assistant combined: it stores what a user has shared, understands it, and brings back the most relevant pieces at the right time. Over time, it learns what matters most and gets better at surfacing the right context.

In plain terms, you can:
- Add content (notes, articles, links, snippets)
- Ask for relevant context (“What do I know about retention?”)
- See how the system learns and organizes that information

## What You Built (Plain English)
- **Memory Ingestion**: A way to add content to the system. The system turns text into a numeric “fingerprint” (embedding), stores it, and keeps metadata like title, type, tags, and timestamps.
- **Smart Retrieval**: When you ask a question, the system searches for the most relevant memories and returns a clean, formatted context you can feed into an AI prompt.
- **Compounding Intelligence**: Every time content is added or accessed, the system learns. It finds related entries, tracks freshness, and gradually decays stale items.
- **Voice Profile**: A lightweight profile that captures writing tone patterns (e.g., direct, optimistic, concise) so AI responses can match the user’s style.
- **Debug Dashboard**: A simple UI to see stats, recent memories, and a preview of what the AI would “see.”

## Features
- FastAPI backend with memory ingestion and retrieval (RAG)
- Local vector store + embedding generator (offline/dev-friendly)
- Compounding logic (related entries, decay, duplicate merging)
- Next.js dashboard to visualize memory health and context

## Quick Start

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` to view the dashboard. The backend runs at `http://localhost:8000`.

## Environment Variables
- `NEXT_PUBLIC_API_BASE_URL` (frontend): API base URL (default `http://localhost:8000`)

## Notes
- The local vector store and embedding client are deterministic for repeatable demos.
- In production, replace the local adapters with Qdrant + Voyage AI clients.

## If You’re Curious (Simple Flow)
1. You **ingest content** → it gets stored + indexed.
2. You **ask a question** → the system finds and ranks relevant memories.
3. You **see the context** → the AI can use it to answer better.
4. The system **learns** with every interaction.
