---
title: Subtext
emoji: 🌌
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Subtext

**A semantic cinema discovery engine that finds movies by vibe, not keywords.**

Subtext maps 100,000+ films into a shared vector space and lets you search by feeling. Type "lonely astronaut drifting through silence" and get results that *understand* what you mean — not just movies with those words in the synopsis. Pair that with your Letterboxd history and it learns what kind of cinema resonates with you personally, re-ranking every result through your own taste.

**Live Demo**: [subtext.hf.space](https://mwahaj36-subtext.hf.space)

---

## What It Does

### Semantic Search
You describe a mood, a memory, a feeling. Subtext converts that into a 768-dimensional vector and finds the closest films in latent space. This means a search for "neon-lit existential crisis" surfaces *Drive*, *Blade Runner 2049*, and *Chungking Express* — films that share atmosphere and tone, not just genre tags.

### Taste DNA
Once you connect your Letterboxd account, Subtext builds a **Taste Centroid** — a weighted average vector of every film you've rated 4 stars or higher. Every search result is then re-ranked by how close it sits to your personal centroid. Two users searching the same query get different results.

### 3D Galaxy Visualization
Your entire library is projected into a navigable 3D space using UMAP dimensionality reduction. Films cluster by thematic similarity. Your watched history lights up as bright green signals in a field of 100,000 dim nodes. Hover to see posters. Click to explore clusters. Constellation lines connect your favorites.

### Live Letterboxd Sync
Subtext scrapes your public Letterboxd profile via RSS feeds and HTML parsing to keep your library current without manual re-imports. Rate a movie on Letterboxd, hit Quick Sync, and it appears in your Subtext library within seconds.

---

## How The Search Works

The retrieval pipeline runs in three stages:

### Stage 1: Vector Retrieval
The search query is embedded using `jinaai/jina-embeddings-v2-base-en` (768 dimensions). AstraDB returns the top 100 nearest neighbors by cosine similarity. A secondary pool fetches films that share TMDB keywords with the top result (the "anchor"), catching thematic siblings that raw vector search misses — particularly across eras.

### Stage 2: Taste DNA Re-ranking
For logged-in users, results are re-ranked based on proximity to their Taste Centroid. A user who loves slow, contemplative cinema will see *Stalker* rank higher than *Interstellar* for a "space isolation" query, even though both score well semantically.

### Stage 3: Thematic Sibling Expansion
Metadata-based injection prevents cluster homogeneity. If the top 10 results are all 2010s sci-fi, the engine pulls in thematically similar films from other decades and regions. This is where *Solaris* (1972) shows up next to *Arrival* (2016).

### Scoring Formula
```
score = (cosine_similarity × 2.0)
      + keyword_overlap_bonus      # +0.02 per shared TMDB keyword, max 0.10
      + masterpiece_bonus           # +0.05 for vote_count > 5000 & rating ≥ 7.8
      + genre_dna_boost             # +0.01–0.02 for genre overlap with anchor
      - genre_purity_penalty        # -0.01 per extraneous genre
      - tonal_mismatch_penalty      # Hard penalty for mood conflicts
      + (quality_score × 0.05)      # Tiny tie-breaker, never a ranking factor
```

No score floors. No clamps. Cosine similarity spreads naturally.

---

## The Sync Engine

### Initial Import (ZIP)
Upload your Letterboxd data export (ZIP). Subtext parses the CSVs, resolves each film against TMDB for poster art and metadata, and stores everything in PostgreSQL. Runs as a background task with real-time progress tracking.

### Quick Sync (Live)
A lightweight background sync that:
1. **Scrapes your RSS feed** for recent diary entries (ratings, reviews, watch dates)
2. **Scrapes your Films page** for non-diary watches
3. **Scrapes your Watchlist page** for new additions
4. **Deduplicates** against existing records using Letterboxd URI as the unique key
5. **Cleans up** watchlist entries that have since been watched
6. **Refreshes** your Taste DNA centroid

Runs silently in the background — no UI overlay, no interruption.

### Profile Mirroring
On every sync, Subtext scrapes your Letterboxd profile for your avatar, bio, film count, and four favorite films. These are displayed on your Subtext profile page.

---

## Features

### Search Page
- Semantic search with real-time results
- Seen/Unseen filtering (hide movies you've already watched)
- Watchlist filtering (show only your watchlist)
- Interactive poster hover with variant fetching (textless, international editions)
- Live TMDB trending feed

### Profile Page
- Letterboxd identity mirroring (avatar, bio, favorites)
- Taste DNA visualization (top genres, centroid strength)
- Recent watch history with poster grid
- Library stats

### Galaxy Page
- 100,000-node 3D force graph rendered in WebGL
- UMAP-projected coordinates preserving thematic clusters
- Personal library highlighted as distinct bright signals
- Constellation lines between favorites and recent watches
- Hover-to-preview with poster tooltips

### Settings Page
- Letterboxd ZIP upload with drag-and-drop
- Quick Sync trigger (silent background operation)
- Profile editing (email, Letterboxd username)
- Danger Zone: full database wipe + re-import
- Account deletion with confirmation modal

### Onboarding Flow
- Letterboxd username verification with live profile preview
- ZIP import with background processing
- Redirects to profile on completion

### Authentication
- Email/password signup with JWT tokens
- Login via email or username
- 30-day token expiration
- Letterboxd username becomes Subtext username during onboarding

---

## Search Algorithm: The Iteration History

The current engine (V100+) is the result of 100+ iterations:

| Phase | Versions | Approach | Problem Solved |
|-------|----------|----------|----------------|
| Keyword Baseline | V0 | Pure metadata lookup | None — zero semantic understanding |
| Semantic Vanguard | V1–V3 | First vector embeddings | Thematic discovery, but hallucination crisis |
| Entity Anchoring | V4–V6 | spaCy NER + Cross-Encoder | Restored precision, but too literal |
| Latent Probes | V7–V27 | Multi-vector queries, mood guards | 90%+ precision, but sequel/clone spam |
| Human Heuristics | V28 | Franchise capping, genre locks | First "human-feeling" results |
| Hardcoded Pools | V49–V67 | Forced specific films into results | Band-aid. Didn't scale |
| Dead-Band Era | V64–V83 | Score compression to 0.98 floor | Killed all ranking discrimination |
| CrossEncoder | V84–V94 | `ms-marco-MiniLM-L-6-v2` re-ranker | 500MB RAM for zero benefit. Removed |
| Keyword Enrichment | V94+ | TMDB keyword pools + overlap scoring | Cross-era discovery finally works |
| Tonal Guard | V100+ | Hard genre penalties + pluralization | Thematic pollution eliminated |

The key insight across all 100 iterations: **simplicity and transparency beat complexity and patches.** Every attempt to be "clever" (score floors, forced pools, cross-encoders) made things worse. The final engine lets cosine similarity speak for itself and adds targeted, deterministic signals only where embeddings are provably weak.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **API** | FastAPI | Async API with background task support |
| **Database** | PostgreSQL (Neon) | User accounts, ratings, sync state |
| **Vector Store** | DataStax AstraDB | 100K movie embeddings, cosine similarity search |
| **Embeddings** | `jina-embeddings-v2-base-en` | 768-dimensional movie vectors |
| **Retrieval** | `all-MiniLM-L6-v2` | 384-dimensional query vectors for Taste DNA |
| **NLP** | spaCy | Named entity recognition for query parsing |
| **Frontend** | Next.js 15 (App Router) | Server/client hybrid rendering |
| **3D Engine** | react-force-graph-3d (Three.js) | WebGL galaxy visualization |
| **Animations** | Framer Motion | Page transitions, modals, toasts |
| **Auth** | JWT (PyJWT) | Stateless authentication |
| **Deployment** | Docker on Hugging Face Spaces | Production hosting |

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- DataStax AstraDB account
- TMDB API key (Bearer token)
- Neon PostgreSQL database

### Environment Variables (`backend/.env`)
```
DATABASE_URL=postgresql://...
TMDB_TOKEN=eyJ...
ASTRA_DB_APPLICATION_TOKEN=AstraCS:...
ASTRA_DB_API_ENDPOINT=https://...
JWT_SECRET_KEY=your-secret
```

### Run Locally
```bash
# Clone
git clone https://github.com/mwahaj36/Subtext
cd Subtext

# Backend
pip install -r backend/requirements.txt
python backend/main.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Populate Vector Store
```bash
python backend/map_galaxy.py  # Syncs movie embeddings to AstraDB
```

---

Built by [Wahaj](https://github.com/mwahaj36)
