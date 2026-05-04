# **Subtext**
### *Don’t search by genre. Search by feeling.*

**Subtext** is a semantic movie discovery engine.

Traditional movie databases rely on rigid tags like **Action**, **Comedy**, or **Drama**. Subtext doesn’t.  
It uses **vector embeddings** + **cosine similarity** to understand the underlying *vibe* of a query.

So instead of searching:

> “Sci-fi”

You can search:

> “a lonely sci-fi movie about memory”

…and get results like:

- **Eternal Sunshine of the Spotless Mind**
- **Blade Runner 2049**

Not because of keywords — but because they sit close together in **latent space**.

---

## ✨ Technical Scale
- **Dataset**: 100,000+ Movies indexed via TMDB.
- **Deep-Context Search**: 8,192-token context window (powered by Jina AI V2).
- **Human Vibe Engine**: Ingests **1.5M+ human reviews** to understand subtext, tropes, and slang.
- **Vector Space**: **76 Million+ dimensions** stored in a serverless cloud architecture.
- **Infrastructure**: **DataStax Astra DB** (Serverless Vector) for lightning-fast retrieval.
- **Vibe Engine**: Hybrid Search combining Dense Vector embeddings with Keyword and Actor/Director NER.

---

## ⚡ The Stack

This project uses a hybrid architecture: modern web + best-in-class AI ecosystem.

### **Frontend**
- **Next.js 15** (App Router)
- **Tailwind CSS**
- **shadcn/ui**

### **Backend**
- **FastAPI** (Python)

### **Database**
- **DataStax Astra DB** (Serverless Vector / NoSQL)

### **AI / ML**
- **Model:** `jinaai/jina-embeddings-v2-base-en`
- **Context Window:** 8,192 tokens (Full reviews + plot metadata)
- **Dimensions:** 768
- **Hardware:** Local GPU (CUDA) for high-speed ingestion

### **Data Source**
- **TMDB API**

---

## 🛠️ Prerequisites

Before you start, make sure you have:

- **Node.js v18+**
- **Python 3.9+**
- **Git**

---

## 🚀 Quick Start

This is a **monorepo**, so you’ll need **two terminal windows** running at the same time.

---

## 1) 🌌 Database Setup (Astra DB)

1. Create a **Serverless Vector** database on **Astra.DataStax.com**.

2. Generate an **Application Token** and copy your **API Endpoint**.

3. Run the initialization script to create the `movies` collection:
```bash
python init_db.py
```

---

## 2) 🧠 Backend Setup (FastAPI)

### Terminal 1

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload
```

✅ The Brain is now online at:

**http://127.0.0.1:8000**

---

## 3) 🎭 Frontend Setup (Next.js)

### Terminal 2

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

✅ The Face is now online at:

**http://localhost:3000**

---

## 🧬 Environment Variables

Create a `.env` file inside:

`backend/`

```env
ASTRA_DB_APPLICATION_TOKEN="AstraCS:..."
ASTRA_DB_API_ENDPOINT="https://..."
TMDB_TOKEN="your_tmdb_read_access_token"
```

---

## 🗺️ Roadmap

- [x] **Phase 1:** High-performance 100k Data Pipeline
- [x] **Phase 2:** Deep-Context Review Integration (1.5M+ human reviews)
- [x] **Phase 3:** Jina AI V2 Migration (8,192 token context)
- [/] **Phase 4:** Hybrid Two-Tower Search Engine
- [ ] **Phase 5:** Electric Void Web Dashboard
- [ ] **Phase 6:** WebGL 3D Vector Galaxy Visualization

---

## 🎨 Design System — *Electric Void*

- **Background:** `#0a0a0a` (Neutral 950)
- **Accent:** `#d946ef` (Fuchsia 500)
- **Typography:** Sans-serif, tracking-wide
- **Mood:** clean, dark, neon, slightly ominous

---
