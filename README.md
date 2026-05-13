# 🌌 SUBTEXT: Cinematic Discovery Redefined

[![Hugging Face Space](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-yellow)](https://huggingface.co/spaces/mwahaj36/Subtext)
[![Tech Stack](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI%20%7C%20Postgres-blue)](https://github.com/mwahaj36/Subtext)

**Subtext** is a "vibe-first" cinematic discovery engine designed to escape the algorithmic echo chambers. By mapping your entire Letterboxd history into a latent "Taste DNA," Subtext helps you find movies that resonate with your soul, not just your genre preferences.

---

## ✨ Key Features

### 🧬 Taste DNA Engine
Unlike traditional recommenders that suggest "Action" because you watched "Action," Subtext analyzes the **tonal architecture** of your history. It looks for the "Vibe" (e.g., *Cerebral*, *Neon-Drenched*, *Existential*) to build a unique vector map of your cinematic identity.

### 🎬 Stealth Sync Pipeline
A robust, "human-like" scraping engine that imports your entire Letterboxd history (Watched, Watchlist, Ratings, and Likes) with:
- **Idempotent Logic**: Never syncs the same movie twice.
- **Human Jitter**: Randomized delays to respect platform rate limits.
- **Global Mapping Cache**: Uses a shared database to instantly resolve TMDB IDs for movies already mapped by the community.

### 🏛️ Cinema Vault
A high-density library interface to browse, search, and filter your imported history. Visualize your Taste DNA source data in real-time.

---

## 🛠️ Technology Stack

- **Frontend**: Next.js 14, Framer Motion (Cinematic Animations), Tailwind CSS.
- **Backend**: FastAPI (Python), `httpx` (Async Scraping), `psycopg2`.
- **Database**: Neon Postgres (Serverless SQL).
- **Inference**: Jina AI v2 Latent Embeddings (Planned).

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- A Neon.tech (or Postgres) Database URL.

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
# Create .env based on .env.example
python main.py
```

### Frontend Setup
```bash
cd frontend
npm install
# Create .env.local with NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

---

## 🛡️ License
MIT License. Built with 🖤 for the lovers of cinema.
