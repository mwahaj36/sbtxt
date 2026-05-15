---
title: Subtext
emoji: 🌌
colorFrom: purple
colorTo: black
sdk: docker
app_port: 7860
pinned: false
---

# 🌌 Subtext: Neural Discovery Engine

**Discover cinema through vibes, story, and soul.**

Subtext is a high-fidelity media discovery platform that bypasses generic metadata in favor of neural similarity. By mapping 100,000+ films into a 768-dimensional vector space, Subtext allows users to navigate the cinematic universe through "vibe-first" search and interactive 3D visualizations.

---

## 🛠️ The Tech Stack

### Frontend (Electric Void UI)
- **Framework**: [Next.js 15](https://nextjs.org/) (App Router)
- **3D Engine**: [Three.js](https://threejs.org/) via `react-force-graph-3d`
- **Animations**: [Framer Motion](https://www.framer.com/motion/)
- **Styling**: Tailwind CSS (Brutalist Architecture)

### Backend (The Professor Model)
- **API**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12)
- **Neural Embeddings**: [Jina AI](https://jina.ai/) (768D Embeddings)
- **Dimensionality Reduction**: [UMAP](https://umap-learn.readthedocs.io/) for 3D spatial mapping
- **Authentication**: JWT-based secure session management

### Infrastructure & Data
- **Vector Database**: [DataStax AstraDB](https://www.datastax.com/products/astra)
- **Relational Database**: PostgreSQL (via Aiven)
- **Metadata Source**: [TMDB](https://www.themoviedb.org/) & [Letterboxd](https://letterboxd.com/)

---

## 🧬 Core Features

### 1. Neural Discovery (Dual-Signal)
Bypass the algorithm. Subtext uses vector similarity to find movies that share the same "neural fingerprint" as your query. Search by mood, lighting, or abstract concept (e.g., *"Neon-drenched solitude"* or *"Industrial decay with a glimmer of hope"*).

### 2. The Subtext Galaxy
A real-time WebGL constellation of 100,000 films. Explore your cinematic history in 3D space, where proximity equals similarity.
- **North Stars**: Your top-rated favorites.
- **Watchlist Mist**: Unexplored potential glowing in electric cyan.
- **Neural Clusters**: Visual clusters of thematic genres.

### 3. Taste DNA Calibration
Sync your Letterboxd library to generate a personalized **Taste Vector**. The engine then weights search results against your unique cinematic soul, surfacing "High Resonance" matches first.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 20+
- AstraDB & TMDB API Keys

### Backend Setup
1. Navigate to `/backend`
2. Create a `.env` file with your credentials.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the API:
   ```bash
   python main.py
   ```

### Frontend Setup
1. Navigate to `/frontend`
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

### Mapping the Galaxy
To generate the 3D coordinates for the constellation feature, run the local mapping script:
```bash
python backend/map_galaxy.py
```

---

## 📜 License
Subtext is a professional discovery framework designed for deep cinematic analysis. Built with passion for the "Electric Void."
