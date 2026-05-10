# 📝 Subtext: The Master Checklist

This is the absolute, granular list of every single task required to build **Subtext** with **Dual-Signal (Positive/Negative) Personalization**.

---

## 🛠️ Phase 0: Environment & Hardware (Setup)
- [x] **NVIDIA Drivers:** Update to latest version.
- [x] **CUDA Toolkit:** Install CUDA 12.x.
- [x] **cuDNN:** Copy files to CUDA directory.
- [x] **Python:** Install 3.11+.
- [x] **Monorepo:** Create `backend/` and `frontend/`.
- [x] **GPU Verification:** Run `torch.cuda.is_available()` script.

---

## 🛰️ Phase 1: The 100k Data Pipeline
- [x] **Links Collection:** Merge MovieLens 25M with TMDB Daily Exports.
- [x] **TMDB API Key:** Secure your token.
- [x] **Async Scraper:**
    - [x] Build `scraper.py` with `httpx/asyncio`.
    - [x] Scrape 100,000 movie metadata packets.

---

## 🗄️ Phase 2: Database Engineering (Aiven/PostgreSQL)
- [x] **Aiven Setup:** Create project and enable `vector` extension.
- [x] **Schema:**
    - [x] Table `movies` (id, title, poster_path, embedding).
- [x] **Initial Sync:** Upload the 99,186 movie IDs and Titles.

---

## 🧠 Phase 3: AI Vectorization (The Professor Model)
- [x] **High-Res Brain:** Switched to `all-mpnet-base-v2` (768 dimensions).
- [x] **Batch Processing:** Vectorizing 100k rows locally using RTX 4060 (~15%).
- [x] **Hybrid Search Query:**
    - [x] Implement SQL for Vector Distance + Full Text Search (Keywords).
    - [ ] Weighting: `(vibe_score * 0.7) + (keyword_score * 0.3)`.
- [x] **IVFFlat Index:** Create storage-efficient index for 1GB limit.

---

## 🐍 Phase 4: Backend API (FastAPI)
- [ ] **FastAPI Setup:** Initialize `main.py` and CORS.
- [ ] **`/v1/search`:** Hybrid endpoint for vibes and keywords.
- [ ] **`/v1/profile`:** Process Letterboxd CSV to generate Taste Vectors.
- [ ] **HuggingFace Proxy:** (Optional) Offload search embeddings to HF Inference API.

---

## 🎭 Phase 6: Frontend (Electric Void UI)
- [ ] **Next.js 15:** Initialize with Tailwind.
- [ ] **Electric Void CSS:** Define neon fuchsia and deep black variables.
- [ ] **Vibe Sliders:** Build interactive UI to let users control the "Repulsion Strength."

---

## 🧬 Phase 7: Personalization (The Core Logic)
- [ ] **Letterboxd Parser:** Map ratings to your internal TMDB IDs.
- [ ] **Centroid Calculation:** 
    - [ ] `Positive_Centroid = average(embeddings of movies rated 4.5-5)`.
    - [ ] `Negative_Centroid = average(embeddings of movies rated 0.5-1.5)`.

---

---

## 🌌 Phase 9: The Subtext Galaxy (Visualization)
- [ ] **UMAP Processing:** Squash 768-dim vectors to 2D/3D coordinates.
- [ ] **WebGL Engine:** Setup `react-force-graph-3d` or `Three.js` viewer.
- [ ] **Interactive Constellations:**
    - [ ] Implement movie poster hovers in 3D space.
    - [ ] Create "Fly-to" animations for search results.
    - [ ] Map the "Taste Nebula" (User likes in Gold, dislikes in Red).
