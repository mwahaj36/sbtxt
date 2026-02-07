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

## ✨ What Subtext Does

- **Semantic search** for movies using natural language
- **Vector database retrieval** (pgvector)
- **FastAPI backend** with modern ML tooling
- **Next.js frontend** with a clean design system

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
- **Supabase** (PostgreSQL + pgvector)

### **AI / ML**
- **sentence-transformers** (HuggingFace)  
- Runs locally or on-server

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

## 1) 🧱 Database Setup (Supabase)

1. Create a free Supabase project at:

   **database.new**

2. Go to **SQL Editor** and run this:

```sql
create extension vector;

create table movies (
  id bigint primary key generated always as identity,
  title text not null,
  overview text,
  embedding vector(384) -- Dimension for 'all-MiniLM-L6-v2'
);
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
SUPABASE_URL="your_supabase_url"
SUPABASE_KEY="your_supabase_anon_key"
TMDB_API_KEY="your_tmdb_key"
```

---

## 🗺️ Roadmap

- [ ] **Phase 1:** Data ingestion pipeline (TMDB → Vector DB)
- [ ] **Phase 2:** Basic semantic search (Text → Vector)
- [ ] **Phase 3:** Letterboxd CSV import
- [ ] **Phase 4:** Active learning (user feedback loop)

---

## 🎨 Design System — *Electric Void*

- **Background:** `#0a0a0a` (Neutral 950)
- **Accent:** `#d946ef` (Fuchsia 500)
- **Typography:** Sans-serif, tracking-wide
- **Mood:** clean, dark, neon, slightly ominous

---

## 🖤 Credits

Built with 🖤 by **[Your Name]**
