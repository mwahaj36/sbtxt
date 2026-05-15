---
title: Subtext
emoji: 🌌
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Subtext: Semantic Cinema Discovery

**A movie discovery engine that prioritizes thematic similarity over simple metadata.**

Subtext is a technical experiment in media discovery. It uses vector embeddings to map over 100,000 films into a 384-dimensional latent space, allowing for discovery based on mood, atmosphere, and narrative style rather than just genre tags or popularity.

---

## 🛠️ Technical Core

The project focuses on two primary challenges: **Live Library Synchronization** and **Personalized Semantic Retrieval**.

### 1. Personalized Search Pipeline
Subtext uses a three-stage retrieval process to surface movies that align with both a search query and the user's specific taste:

1.  **Vector Retrieval**: Initial candidates are pulled from a DataStax AstraDB (Cassandra) vector store based on cosine similarity between the search query and movie embeddings (`all-MiniLM-L6-v2`).
2.  **Taste DNA Re-ranking**: For authenticated users, the system calculates a "Taste Centroid"—a weighted average vector of every movie the user has rated 4 stars or higher. Search results are then re-ranked based on their proximity to this personal centroid.
3.  **Thematic Sibling Expansion**: To ensure variety, the engine injects "thematic siblings"—movies that share similar metadata (keywords/genres) with the top results but occupy different positions in the vector space.

### 2. Live Sync Engine
Rather than relying solely on static ZIP exports, Subtext implements a multi-channel synchronization strategy:
- **RSS-Based Live Sync**: A daily background task that monitors the user's Letterboxd RSS feed. It automatically scrapes new ratings and diary entries, keeping the 3D visualization updated without user intervention.
- **Additive Reconciliation**: The sync logic uses a "Resolved-First" approach to handle data from various sources (CSV, RSS, API), ensuring that existing metadata (like TMDB IDs and poster paths) is preserved while new interactions are merged.

### 3. 3D Visualization
The entire library is projected into a navigable 3D environment using `react-force-graph-3d` (Three.js).
- **Dimensionality Reduction**: We use **UMAP** to project the 384-dimensional embeddings into 3D space, preserving thematic clusters.
- **Dynamic Linkages**: The visualization draws "Constellation" lines between movies in the user's favorites and recent history, providing a visual map of their cinematic journey.

---

## 🔬 Search Algorithm Evolution (The Iteration Log)

The current retrieval system is the result of a 94+ iteration cycle focused on balancing semantic "vibe" with metadata accuracy:

- **V0–V10 (Keyword Baseline)**: Pure metadata indexing in AstraDB. Fast, but limited to exact word matches.
- **V11–V30 (Early Vector Search)**: First implementation of semantic embeddings. Faced significant "drift" where thematic similarity was technically high but contextually irrelevant (e.g., matching a documentary about space with a sci-fi comedy).
- **V31–V60 (Latent Probes)**: Introduced re-ranking based on genre centroids. This stabilized results but created "similarity plateaus" where results were too homogeneous.
- **V61–V90 (Score Normalization)**: Focused on calibrating cosine similarity thresholds. Solved the "Dead-Band" problem where score compression made ranking impossible.
- **V94+ (Current)**: The hybrid approach—combining vector similarity, Taste DNA weighting, and metadata-based sibling injection.

---

## 💻 Infrastructure & Stack

### **Backend**
- **FastAPI**: Asynchronous API layer for low-latency search and sync operations.
- **PostgreSQL**: Relational storage for user accounts, library history, and sync logs.
- **AstraDB**: Distributed vector database for high-dimensional semantic search.
- **Sentence-Transformers**: `all-MiniLM-L6-v2` for generating 384-dimensional vectors.

### **Frontend**
- **Next.js 15**: App Router architecture for unified server/client performance.
- **React-Force-Graph-3D**: WebGL-based visualization engine for the 3D environment.
- **Framer Motion**: State-driven UI transitions and custom notification systems.

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- AstraDB Secure Connect Bundle
- TMDB API Key

### Quick Start
1. **Clone & Install**:
   ```bash
   git clone https://github.com/mwahaj36/Subtext
   npm install
   pip install -r backend/requirements.txt
   ```
2. **Configuration**: Set your API keys in `backend/.env`.
3. **Map Library**:
   ```bash
   python backend/map_galaxy.py  # Synchronizes movie embeddings
   ```
4. **Run**:
   ```bash
   python backend/main.py  # Backend
   npm run dev            # Frontend
   ```

---

Built by [Wahaj](https://github.com/mwahaj36) | [GitHub](https://github.com/mwahaj36)
