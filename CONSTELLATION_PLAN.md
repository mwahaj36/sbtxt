# 🌌 Implementation Plan: The Subtext Galaxy (Interactive Constellations)

Objective: Transform the 768-dimensional neural embeddings of 100,000+ movies into a navigatible, interactive 3D constellation.

---

## 🖥️ System Requirements

### Client-Side (The Browser)
- **GPU**: WebGL 2.0 compatible hardware. Dedicated GPU (RTX 30 series or equivalent) is recommended for 100k points, though modern integrated GPUs (M-series Mac or Intel Iris Xe) will suffice with optimization.
- **RAM**: 8GB Minimum (16GB recommended). Storing 100k coordinate points and metadata in memory requires ~1.2GB of dedicated browser heap.
- **Display**: High-refresh rate monitor recommended for smooth "fly-to" transitions.

### Backend (Preprocessing & Streaming)
- **RAM**: 16GB+ required for initial UMAP calculation. The manifold projection of 100k x 768D vectors is memory-intensive.
- **CPU**: 8+ cores recommended. UMAP is multi-threaded but computationally heavy during the initial fit.
- **Storage**: ~50MB of additional DB space for spatial coordinates.

---

## ⚙️ Technical Workflow: How It Works

1. **The Projection (One-Time)**:
    - We extract all 768D vectors from AstraDB.
    - UMAP project these into a 3D Euclidean space.
    - Result: Every movie gets a permanent `(x, y, z)` coordinate between -100 and 100.
2. **The Stream (JSON/Protobuf)**:
    - The backend serves a compressed stream of coordinates.
    - We use **Binary Encoding** or **Brotli Compression** to keep the 100k point payload under 10MB.
3. **The Rendering (BufferGeometry)**:
    - Instead of creating 100,000 individual React components (which would crash the browser), we use a single **THREE.BufferGeometry**.
    - All 100k points are sent to the GPU in a single draw call.
4. **The Intersection (Raycasting)**:
    - We use a **GPU Picker** or **Octree** to detect which "star" the user is hovering over, allowing for instant title/poster display without lag.

---

## 🏗️ Phase 1: Backend & Data Preparation (The Mapping)
The goal is to translate abstract "similarity" into physical `(x, y, z)` coordinates. **This phase is performed locally to save 100% of AstraDB write costs.**

1. **Local Dimensionality Reduction (UMAP)**:
    - **Tool**: `umap-learn` in Python.
    - **Process**: Load all 100k embeddings from AstraDB to your local machine.
    - **Target**: Reduce 768D vectors to 3D coordinates.
2. **Static JSON Export (Cost Optimization)**:
    - **Outcome**: Instead of updating AstraDB, the script generates `galaxy_points.json`.
    - **Structure**: Uses ultra-short keys (`i, t, x, y, z`) and 4-decimal precision to keep the 100k-point file under 15MB.
    - **Cost**: **$0.00** (Bypasses 100,000 database writes).
3. **Cloud Serving (Hugging Face)**:
    - **Process**: Upload `galaxy_points.json` directly to your Hugging Face Space as a static asset.
    - **Efficiency**: The browser downloads the file once and caches it.



---

## 🎨 Phase 2: Frontend 3D Engine (The Visualization)
Building a high-performance WebGL environment.

1. **Engine Selection**: `react-force-graph-3d` (powered by `Three.js`).
    - **Why?**: Handles large datasets efficiently and provides built-in "Fly-to" and hover logic.
2. **Rendering Strategy**:
    - **Point Cloud**: For the 100k global set, use simple neon points.
    - **Sprite Overlays**: As the user zooms in, dynamically replace points with movie poster sprites.
    - **Frustum Culling**: Ensure the browser only renders what is currently in view.
3. **Environment Design**:
    - **The Void**: Deep black background (`#000000`).
    - **Star Dust**: Subtle ambient particles to give depth to the emptiness.

---

## 🧬 Phase 3: The Taste Nebula (Personalization)
Mapping the user's soul onto the stars.

1. **User Overlays**:
    - Fetch the user's `user_ratings` and `watchlist`.
    - **Gold Nodes**: Movies rated 4.0+ (The user's "North Stars").
    - **Red Nodes**: Movies rated 2.0- (The "Black Holes").
    - **Blue Nodes**: Watchlist items.
2. **Neural Connections**:
    - Draw subtle neon lines between the user's top 5 movies and their closest neighbors to visualize "Personalized Clusters."

---

## ⚡ Phase 4: Performance & UX
Ensuring a "Quiet Luxury" smooth experience.

1. **Octree Searching**: Use an Octree to manage spatial queries (e.g., "Which movie is my cursor hovering over?").
2. **Progressive Loading**: Load a low-res version of the galaxy (10k points) instantly, then stream the remaining 90k in the background.
3. **Fly-To Integration**: Search results in the main search page should have a "Locate in Galaxy" button that triggers a 3D camera transition.

---

## 📱 Universal Access & Optimization (Low-End & Mobile)

To ensure the Galaxy is accessible on everything from an RTX 4090 to an iPhone:

1. **Hierarchical Level of Detail (LoD)**:
    - **The 10k Core**: By default, only load the top 10,000 most popular movies. This reduces memory usage by 90% while still representing the overall shape of the galaxy.
    - **Sector Streaming**: As the user zooms into a neighborhood, the engine fetches the "finer stars" for that specific 3D sector only.
2. **Dynamic Quality Scaling**:
    - Detect the user's hardware on load.
    - **Mobile**: Disable Bloom, use simple `THREE.Points` with a fixed size, and cap the frame rate at 30fps to save battery.
    - **Desktop**: Enable post-processing, dynamic sprites, and unlimited frame rate.
3. **2D "Atlas" Toggle**:
    - Provide a button to "Flatten Galaxy." This switches to a 2D UMAP projection, which is exponentially easier for integrated GPUs to render.
4. **Binary Point Format**:
    - Serve coordinates in a **Typed Array (Float32)** format directly. This allows the browser to upload data to the GPU with zero parsing overhead.

