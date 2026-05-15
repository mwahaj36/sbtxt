---
title: Subtext
emoji: 🌌
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# 🌌 Subtext: The Neural Discovery Engine

**"Discover cinema through vibes, story, and soul."**

Subtext is a high-fidelity, production-grade media discovery platform designed to bypass generic metadata and "popularity-trap" algorithms. By mapping over **100,000 films** into a **768-dimensional vector space**, Subtext allows users to navigate the cinematic universe through "vibe-first" search and an immersive 3D WebGL constellation.

---

## 🚀 The Vision
Generic streaming algorithms are broken. They recommend what's popular, not what resonates. Subtext uses **Neural Similarity** to understand the *subtext* of a film—its mood, atmosphere, and thematic DNA—allowing for queries like:
- *"Neon-drenched solitude in a rainy metropolis"*
- *"Ghibli-esque wonder with a hint of cosmic horror"*
- *"Brutalist architecture and industrial decay"*

---

## 🧬 Core Features

### 1. 3D Neural Galaxy (The Constellation)
A real-time WebGL visualization of the entire cinematic universe. 
- **Proximity as Meaning**: In this galaxy, distance is meaning. Similar movies cluster together naturally through **UMAP** dimensionality reduction.
- **Personalized Signals**: Your watch history is visualized in real-time.
    - 🌸 **Fuchsia**: Your Personal Favorites constellation.
    - 🔴 **Red**: Recent watch history connections.
    - 🍏 **Lime Green**: "Seen" movies mapped in space.
    - ⚪ **Neutral**: The undiscovered void.
- **Warp Speed Navigation**: Fluid 3D pilot controls (WASD + Mouse) to navigate through 100,000+ signals.

### 2. Taste DNA & Smart Sync
- **Neural Personalization**: Sync your **Letterboxd** library (additive ZIP/API sync) to generate a unique **Taste Vector**.
- **Vector Weighted Search**: Your search results are dynamically weighted against your Taste DNA, surfacing "High Resonance" matches that align with your unique cinematic soul.
- **Smart Sync**: Additive synchronization that preserves history while rapidly updating your library with new discoveries.

### 3. Neural Search Engine
Bypass the tag-based search. Subtext uses **Jina AI Embeddings** to perform semantic search across titles, overviews, and deep metadata, providing results based on conceptual similarity rather than keyword matching.

---

## 🛠️ The Engineering Stack

### Frontend (Electric Void UI)
- **Framework**: [Next.js 15](https://nextjs.org/) (App Router)
- **3D Engine**: [Three.js](https://threejs.org/) & [React-Force-Graph-3D](https://github.com/vasturiano/react-force-graph-3d)
- **State & Motion**: [Framer Motion](https://www.framer.com/motion/) for fluid UI transitions.
- **Aesthetics**: Brutalist Dark Mode with high-contrast neon accents.

### Backend (The Discovery Core)
- **API**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12)
- **Embeddings**: [Jina AI](https://jina.ai/) (v2-base-en) 768D vectors.
- **Spatial Mapping**: [UMAP](https://umap-learn.readthedocs.io/) for high-dimensional to 3D projection.
- **Authentication**: Secure JWT-based auth with guest discovery access.

### Infrastructure
- **Vector DB**: [DataStax AstraDB](https://www.datastax.com/products/astra) (Serverless Vector Storage).
- **RDBMS**: PostgreSQL for relational metadata.
- **Deployment**: Optimized for Vercel (Frontend) and Hugging Face/Docker (Backend).

---

## 📈 Engineering Challenges Solved
- **100k Node Performance**: Optimized WebGL rendering to handle 100,000 interactive nodes at 60FPS.
- **Dimensionality Integrity**: Maintaining thematic clusters while reducing 768 dimensions to 3D space using UMAP.
- **Additive Sync Logic**: Building a robust synchronization pipeline that merges Letterboxd exports with real-time movie metadata without data duplication.
- **Cross-Platform Pilot Controls**: Implementing custom Pointer Lock navigation for a "flight-sim" feel in a web browser.

---

## 📜 Roadmap
- [x] 3D Galaxy Visualization
- [x] Letterboxd Smart Sync
- [x] Taste DNA weighted search
- [ ] Multi-user collaborative constellations
- [ ] Real-time "Vibe Streaming" (Neural Radio)

---

## 🛰️ Getting Started

### Prerequisites
- Python 3.12+ / Node.js 20+
- AstraDB & TMDB API Keys

### Quick Start
1. **Backend**: Install `requirements.txt` and run `uvicorn main:app`.
2. **Frontend**: Install `npm` packages and `npm run dev`.
3. **Map the Galaxy**: Run `python backend/map_galaxy.py` to synchronize the 3D matrix.

---
Built with 🌌 by [Wahaj](https://github.com/mwahaj36) | *Part of the Electric Void.*
