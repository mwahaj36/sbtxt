---
title: Subtext
emoji: 🌌
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Subtext: The Neural Cinema Discovery Engine

**Discover cinema through vibes, story, and soul—not just metadata.**

Subtext is a high-performance media discovery platform built to dismantle the "popularity-trap" algorithms of modern streaming. By mapping over 100,000 films into a 768-dimensional neural vector space, Subtext transforms movie discovery from a keyword search into a spatial exploration of human emotion and thematic DNA.

---

## 🛰️ The Architecture of Discovery

Subtext isn't just a database; it's a **Latent Space Navigator**. Most platforms search for *words*; Subtext searches for *meaning*.

### 1. The Neural Matrix (3D Galaxy)
A massive WebGL-powered 3D visualization of the entire movie universe.
- **High-Dimensional Mapping**: We use **UMAP (Uniform Manifold Approximation and Projection)** to project 768-dimensional embeddings from `sentence-transformers` into a navigable 3D star-field.
- **Spatial Semantic Proximity**: In this galaxy, **Distance = Meaning**. Movies that share thematic, emotional, or stylistic DNA naturally cluster together. You don't "browse" categories; you navigate through sectors of feeling.
- **Constellation Logic**: 
  - **Fuchsia Signals**: Your Personal Favorites, linked into a persistent constellation.
  - **Red Signals**: Your most recent watch history, creating a temporal trail through the void.
  - **Lime Green Signals**: Your entire "Seen" library, mapped to show you which regions of the galaxy you've already conquered.
- **Flight Controls**: Custom-built kinetic flight engine (WASD + Mouse) allowing pilots to fly through the matrix at "Neural Sprint" speeds.

### 2. The Search Algorithm (94+ Iterations)
The heart of Subtext is a hybrid search engine that combines vector similarity with deterministic metadata anchors.
- **The "Blackhole" Engine**: A multi-stage retrieval pipeline:
  1. **Stage 1 (Vector Retrieval)**: Pulls the top 200 candidates from AstraDB based on cosine similarity.
  2. **Stage 2 (Taste DNA Re-ranking)**: If logged in, results are re-weighted based on your **Neural Signature** (the centroid of your 5-star movies).
  3. **Stage 3 (Sibling Expansion)**: Injects "Thematic Siblings"—movies with similar keyword density but different vector positions—to prevent "echo chamber" results.
- **Vibe-First Queries**: Handles complex natural language like *"Lush atmospheric nostalgia in a rainy metropolis"* or *"Existential dread masked by bright colors."*

### 3. Taste DNA & Identity Sync
Your cinematic identity is more than a list of titles; it's a coordinate in the matrix.
- **Smart Sync Pipeline**: An additive, multi-threaded sync engine that processes Letterboxd ZIP exports. It reconciles your entire history without creating duplicates, using a "Resolved-First" strategy to handle missing TMDB IDs.
- **Live Sync (The Fast Lane)**: A daily background task that scrapes your Letterboxd RSS feed to keep your constellations updated in real-time without requiring a fresh ZIP upload.
- **Neural Signature Generation**: We calculate a weighted average of the vectors for every movie you've rated 4+ stars. This "Centroid" becomes your anchor in the galaxy, pulling similar films toward your search results.

---

## 🛠️ Deep Feature Detail

### 🌌 Kinetic 3D HUD
- **Dynamic Sector Detection**: The HUD identifies which "thematic sector" you are currently piloting through (e.g., *Cyberpunk, Ghibli, Noir*).
- **Target Locking**: Click any star to lock onto its signal, pulling up a deep-metadata card including TMDB posters, release years, and your personal interaction status.
- **Warp Drive**: Smooth camera tweening (Warp) allows you to jump from one end of the universe to another instantly when selecting search results.

### 🧬 Neural Search Refinement
- **Signal Filtering**: Toggle between "Exploration Mode" (see everything) and "Discovery Mode" (automatically hide everything you've already seen).
- **Genre Centroids**: Behind the scenes, the engine maintains centroids for major genres, helping the vector search stay "principled" even when queries are vague.

### 🔒 Identity & Safety
- **Danger Zone**: A dedicated suite for data management.
  - **Full Reset**: Wipe your entire Subtext library and re-sync from a fresh ZIP.
  - **Account Termination**: A permanent, double-confirmed purge that removes your user record and all associated ratings from the database.
- **Privacy-First**: No tracking. Your Taste DNA is used strictly to power your own discovery experience.

---

## 📜 The Iteration Log: Evolution of a Search Engine

The "Blackhole" engine wasn't built in a day. It is the result of a obsessive **94-iteration** cycle:

- **V0: The Metadata Baseline** (Keyword lookup only. Fast, but brain-dead).
- **V1-V12: The Vector Crisis** (Introduced embeddings. Great for "vibes" but terrible for precision. It once recommended *Toy Story* for *The Terminator* because they both had "action").
- **V27: Latent Probes** (Implemented deep re-ranking. Results became "alien"—technically accurate but too obscure for humans).
- **V45-V60: The Genre Anchor Phase** (Started weighting by genre. This "fixed" the vector drift but made results feel generic again).
- **V80-V90: Score Compression** (Tried to normalize similarity scores. Caused "Dead-Band" where every movie had a 0.85 score).
- **V94+: The Principles Approach** (The current version. Uses raw vector similarity for discovery, DNA weighting for personalization, and Sibling Expansion for variety).

---

## 🏗️ Technical Stack

### **The Intelligence (Backend)**
- **FastAPI**: Asynchronous Python backend for high-concurrency search.
- **Psycopg2/PostgreSQL**: Relational storage for user identities and high-speed interaction logging.
- **AstraDB (Cassandra)**: Distributed vector storage for 100k+ neural embeddings.
- **Sentence-Transformers**: `all-MiniLM-L6-v2` for generating 768D semantic vectors.

### **The Interface (Frontend)**
- **Next.js 15**: Leveraging the App Router for server-side performance and client-side interactivity.
- **Three.js**: The core WebGL engine for the 3D Galaxy.
- **React-Force-Graph-3D**: Specialized graph implementation for neural matrix navigation.
- **Framer Motion**: Smooth, brutalist UI transitions and custom toast/modal systems.

### **The Pipeline**
- **Docker**: Containerized deployment for consistent environments.
- **Hugging Face Spaces**: Hosting the production discovery engine.
- **Vercel**: Powering the frontend edge delivery.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.12+** and **Node.js 20+**
- **AstraDB Bundle**: Secure Connect Bundle and application token.
- **TMDB API Key**: For fetching posters and metadata.

### Installation
1. **Clone & Install**:
   ```bash
   git clone https://github.com/mwahaj36/Subtext
   cd Subtext
   npm install
   pip install -r backend/requirements.txt
   ```
2. **Environment**: Create a `.env` in `backend/` with your keys (see `.env.example`).
3. **Initialize the Matrix**:
   ```bash
   python backend/map_galaxy.py  # Syncs embeddings to AstraDB
   python backend/main.py        # Starts the API
   ```
4. **Launch Interface**:
   ```bash
   npm run dev
   ```

---

Built with obsession by [Wahaj](https://github.com/mwahaj36) 🌌
