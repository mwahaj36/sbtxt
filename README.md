---
title: Subtext
emoji: 🌌
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Subtext: The Cinema Discovery Engine

**Discover movies through vibes, story, and soul.**

Subtext is a media discovery platform built to get past the generic recommendations and popularity-trap algorithms on most streaming sites. By mapping over 100,000 films into a 768-dimensional vector space, Subtext lets you explore movies through vibe-first search and an immersive 3D constellation.

---

## The Vision

Streaming algorithms are usually pretty limited—they just recommend what's popular. Subtext uses semantic similarity to understand the "vibe" of a film—the mood, atmosphere, and thematic DNA. This lets you search for things like:

- "Neon-drenched solitude in a rainy metropolis"
- "Ghibli-esque wonder with a hint of cosmic horror"
- "Brutalist architecture and industrial decay"

---

## Core Features

### 1. 3D Constellation (The Galaxy)

A real-time 3D visualization of the entire movie universe using WebGL.

- **Spatial Meaning**: In this galaxy, distance actually means something. Similar movies cluster together naturally using dimensionality reduction.
- **Personalized Signals**: Your watch history is mapped in real-time.
  - **Fuchsia**: Your Personal Favorites.
  - **Red**: Recent watch history connections.
  - **Lime Green**: "Seen" movies mapped in space.
  - **Neutral**: The rest of the void.
- **Navigation**: Use WASD + Mouse to fly through 100,000+ signals like a pilot.

### 2. Taste DNA and Smart Sync

- **Personalized Mapping**: Sync your Letterboxd library (ZIP or API sync) to generate a unique "Taste Vector."
- **Weighted Search**: Search results are weighted against your Taste DNA, surfacing matches that actually align with your personal cinematic style.
- **Smart Sync**: An additive sync pipeline that keeps your history intact while updating your library with new discoveries.

### 3. Semantic Search Engine

Get past simple tag-based search. Subtext uses deep embeddings to perform semantic search across titles, overviews, and metadata. It finds results based on what the movie is *about* conceptually rather than just matching keywords.

---

## The Struggle: Building the Search Algorithm

This algorithm didn't work on the first try. It took **94+ iterations** to get it right. I call it the "Blackhole of Search"—the deep dive from simple keywords into the actual latent space of human emotion.

### **The Iteration Record**

*   **V0: The Keyword Baseline**
    *   *The "Title Sniping" Era*. Just pure metadata lookup. No real understanding.
    *   **How it worked**: Metadata lookup (Title, Overview) via Astra DB indexing.
*   **V1–V3: The First Experiments**
    *   *The "Hallucination" Crisis*. Introduced vector search. It found the "vibe" but sometimes got totally lost—like returning kids' cartoons for gritty crime movies.
    *   **How it worked**: First use of embeddings and vector search.
*   **V27: Peak Latent Space**
    *   *The "Alien Logic" Problem*. Technically really advanced but the results were just weird.
    *   **How it worked**: Used "Latent Probes" with deep re-ranking of the top 200 candidates.
*   **V64–V83: The Dead-Band Era**
    *   *Score Compression*. I tried to be clever by "boosting" scores, but it just made all the results look the same.
    *   **How it worked**: Implemented a threshold that effectively flattened the ranking for everything that passed a certain gate.
*   **V94+: The Big Overhaul**
    *   *The Final Version*. Stripped away the hacky fixes for a more principled approach.
    *   **How it worked**: Combined vector search with genre and keyword "siblings" for a more balanced result.

> [!NOTE]
> All my research notes and the full technical post-mortem are in the [/research](file:///c:/Users/Wahaj/Documents/GitHub/Subtext/research) folder.

---

## The Tech Stack

### Frontend

- **Framework**: Next.js 15 (App Router)
- **3D Engine**: Three.js and React-Force-Graph-3D
- **Motion**: Framer Motion for UI transitions.
- **Design**: Brutalist Dark Mode with neon accents.

### Backend

- **API**: FastAPI (Python 3.12)
- **Embeddings**: Sentence-Transformers (768D vectors).
- **Mapping**: UMAP for 3D projection.
- **Auth**: JWT-based authentication.

### Infrastructure

- **Vector DB**: DataStax AstraDB.
- **RDBMS**: PostgreSQL.
- **Hosting**: Vercel and Hugging Face.

---

## Engineering Challenges Solved

- **100k Node Performance**: Optimized WebGL rendering to handle 100,000 interactive nodes.
- **Dimensionality Integrity**: Maintaining thematic clusters while reducing 768 dimensions to 3D space using UMAP.
- **Additive Sync Logic**: Building a robust synchronization pipeline that merges Letterboxd exports with real-time movie metadata without data duplication.

---

## Getting Started

### Prerequisites

- Python 3.12+ / Node.js 20+
- AstraDB and TMDB API Keys

### Quick Start

1. **Backend**: Install requirements.txt and run uvicorn main:app.
2. **Frontend**: Install npm packages and npm run dev.
3. **Map the Galaxy**: Run python backend/map_galaxy.py to synchronize the 3D matrix.

---

Built by [Wahaj](https://github.com/mwahaj36) |
