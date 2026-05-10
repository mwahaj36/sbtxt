# 🎬 Subtext: The Master Engineering Roadmap

This is the ultimate guide to building **Subtext**. It combines high-level product vision, deep technical architecture, and a granular learning path.

---

## 🧠 Core Learning Concepts (Prerequisites)
1.  **Vector Embeddings & Latent Space**: Turning text into multidimensional coordinates.
2.  **Transformer Architecture**: The "Attention" mechanism that powers BERT/DistilBERT.
3.  **Contrastive Learning (Triplet Loss)**: Training a model using (Anchor, Positive, Negative) triplets.
4.  **Local AI Acceleration (CUDA)**: Utilizing your RTX 4060 for parallel tensor math.
5.  **Vector Math & Centroids**: Calculating the "center point" of a group of vectors (User Taste).
6.  **HNSW (Hierarchical Navigable Small World)**: High-speed approximate nearest neighbor search.

---

## ✨ Core Features (The Product)

### 1. Semantic "Vibe" Search
*   **Description:** Search for movies using feelings, colors, or moods instead of genres.
*   **Example:** *"A movie that feels like a cold winter night in a big city"* or *"Action but it feels like a dream."*

### 2. Dual-Signal Personalization (Positive/Negative)
*   **The Taste Anchor:** Boosts movies that align with your highest-rated films (4.0+ stars).
*   **The Repulsion Signal:** Actively suppresses and hides movies that align with your lowest-rated films (0.5 - 1.5 stars).

### 3. The Vibe Mixer (Live Weighting)
*   **Description:** A set of UI sliders that let the user decide how much the search results should prioritize their taste vs. the literal query.
*   **Sliders:** [Literal Match] --- [My Taste] --- [Discovery Mode].

### 4. Taste Visualization (Latent Mapping)
*   **Description:** A 2D interactive map (using t-SNE) showing the 100,000 movies as a "galaxy," highlighting where your taste sits and where the "Anti-Vibe" zone is.

---

## 🎭 Application Structure (The Pages)

### 1. The Landing Portal (`/`)
*   **Hero:** A minimalist, "Electric Void" themed search bar.
*   **Interaction:** Real-time search suggestions as you type.
*   **Visuals:** Subtle background animations that react to the "vibe" of the query.

### 2. The Search Results View (`/search`)
*   **The Grid:** High-quality posters for the top 20-40 matches.
*   **Similarity Badges:** Each movie shows a "Vibe Match %" and a "Personal Match %."
*   **The Mixer Panel:** Floating sidebar with sliders to adjust the recommendation algorithm in real-time.

### 3. The Onboarding / Import Page (`/import`)
*   **The Upload:** Drag-and-drop for the Letterboxd `ratings.csv`.
*   **Processing State:** Animated visual showing the AI "reading" your history and mapping it to the 100k database.

### 4. The Movie Deep-Dive (`/movie/[id]`)
*   **Vibe Profile:** A breakdown of why the movie sits where it does in latent space.
*   **Latent Neighbors:** "If you liked the vibe of this, you'll also like..." (using vector similarity).

---

## 🔍 Market Analysis: How Subtext Wins
| Feature | Letterboxd / IMDb | ChatGPT / LLMs | **Subtext** |
| :--- | :--- | :--- | :--- |
| **Semantic Search** | ❌ (Keyword only) | ✅ (Good) | ✅ (100k optimized) |
| **Personalization** | ❌ (Static) | ❌ (No History) | ✅ (Taste Anchoring) |
| **Data Accuracy** | ✅ (High) | ❌ (Hallucinations) | ✅ (Verified TMDB IDs) |
| **Vibe Mixing** | ❌ | ❌ | ✅ (Vector Sliders) |

---

## 🛠️ The Advanced Stack
*   **Frontend:** Next.js 15 (App Router), Tailwind CSS, Framer Motion.
*   **Backend:** FastAPI (Python 3.11+).
*   **Database:** Neon (Postgres + pgvector).
*   **ML Training (Local):** `PyTorch` (CUDA), `sentence-transformers`, `RTX 4060 GPU`.

---

## 🛰️ Phase-by-Phase Implementation
### Phase 1: Data Ingestion & Pipeline (Completed)
*   **The 100k Skeleton:** TMDB Daily Exports.
*   **TMDB Async Enrichment:** Scraped 99,186 metadata packets.
*   **Data Ingestion:** High-speed bulk upload to Aiven/PostgreSQL.

### Phase 2: High-Quality Vectorization (In Progress)
*   **The Brain:** `all-mpnet-base-v2` (768 dimensions) for superior semantic understanding.
*   **Local Processing:** Leveraging RTX 4060 for ~1 hour batch embedding run.
*   **Storage Optimization:** Implementing IVFFlat indexing to stay within 1GB limit.

### Phase 3: Hybrid Search & API (Up Next)
*   **The Hybrid Engine:** Combining vector similarity with Full Text Search (Keyword matching).
*   **FastAPI Backend:** Build the bridge between the database and the UI.
*   **HuggingFace Inference API:** Integration for low-RAM production environments.

### Phase 4: The "Electric Void" UI & Pulse (Completed)
*   **Frontend:** Next.js implementation of the design system with "Living Poster" hover effects.
*   **The Discovery Pulse:** Real-time TMDB trending integration with verified fallback assets.
*   **Living Posters:** Real-time alternative variant fetching on hover for immersive browsing.

### Phase 5: The Tonal Guard Engine (Completed)
*   **Vibe Rules:** Custom keyword-to-genre mapping for high-intent queries (e.g., "rom com", "whodunnit").
*   **Tonal Penalties:** Hard suppression of conflicting genres (e.g., preventing Horror from polluting Comedy results).
*   **Semantic Pluralization:** Native support for plural and singular genre queries ("comedy" vs "comedies").
*   **TMDB Multi-Asset Pipeline:** Integration with TMDB Image API for variant artwork retrieval.

---

## ⏳ Solo Developer Timeline (6-8 Weeks)
*   **Total Dev Hours:** ~120 - 150 hours.
*   **Main Bottleneck:** Data scraping (TMDB rate limits) and UI polish.

---

## 🏁 Exactly Where To Start (Day 1)
### Step 1: Hardware & Environment
1.  Install **CUDA 12.x** and **Python 3.12**.
2.  Create `backend` virtual env.
3.  Install PyTorch with CUDA support.
### Step 2: The 100k Seed
1.  Download **MovieLens 25M** and sign up for **TMDB API**.
### Step 3: Neon Setup
1.  Initialize Neon DB with `pgvector`.

---

## 📚 Study List (Search these on YouTube/Medium)
- "PyTorch CUDA setup for Windows"
- "Sentence Embeddings clearly explained"
- "Hard Negative Mining in NLP"
- "Vector Centroids and Weighted Averages"
- "pgvector indexing for performance"
- "FastAPI Async/Await patterns"
