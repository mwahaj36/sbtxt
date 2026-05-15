# Subtext Engine Evolution: The Full Technical Dump (V0 - V94+)

This document tracks the iterative development of the Subtext discovery engine, from a simple keyword-matching baseline to the sophisticated, thematically aware hybrid model.

---

## 1. The Iteration Record: From Keywords to Latent Probes

### **V0: The Keyword Baseline (The "Title Sniping" Era)**
*   **Mechanism**: Pure metadata lookup (Title, Overview) via Astra DB keyword indexing.
*   **Strength**: Perfect recall for exact title matches (e.g., "The Godfather").
*   **Problem**: Zero semantic understanding. A search for "scary movies" would only return movies with the word "scary" in the title. Massively polluted by keyword noise (e.g., "Cop Land" for a "La La Land" query).

### **V1 - V3: The Semantic Vanguard (The "Hallucination" Crisis)**
*   **Mechanism**: First introduction of `jina-embeddings-v2` and vector search. V3 introduced "Intent Blending."
*   **Strength**: Transformed the engine into an "Art Curator." Found masterpieces like *Stalker* and *Moonlight* based on vibe.
*   **Problem**: **Catastrophic Hallucination.** Because vector similarity was too loose, a query for "movies like La La Land" returned kids' fantasy movies (*Wonder Park*). It lost the "Text" in search of the "Subtext."

### **V4 - V6: The Entity Anchor & Hybrid Re-ranking**
*   **Mechanism**: Added spaCy NER (V4) and the first **Cross-Encoder re-ranker** (V6).
*   **Strength**: Restored user trust. Fixed the "Land" noise. Cross-encoders provided the first "High Fidelity" matches.
*   **Problem**: Significant latency and "Intent Dilution." The model became too literal, missing the "Quiet" nuance for specific actors.

### **V7 - V26: The "Latent Probe" & Adaptive Gating Phase**
*   **Mechanism**: 20 iterations of fine-tuning weights, implementing **Mood Guards** (V12), and **Asymmetric Additive Scoring** (V18). This phase experimented with "Latent Probes"—sending multiple vectors per query.
*   **Strength**: Achieved 90%+ precision on complex thematic queries. Discovered obscure gems like *Man with No Past* by metadata enrichment.
*   **Problem**: The "Number Bias" peaked here. The model became so good at semantic matching that it would prioritize an obscure sequel with a high semantic score over a legendary masterpiece (e.g., returning *L'ultimo padrino* for a Godfather query).

### **V27: The Brutal Evaluation (The "Peak Latent" Model)**
*   **Mechanism**: Aggressive latent probing and deep re-ranking of 200+ candidates.
*   **Strength**: Extremely high precision for niche queries (e.g., "neon colors and futuristic cities").
*   **Problem**: Failed the "Godfather Diversification" test. It returned 10 versions of *The Godfather* (clones, foreign versions) instead of thematic siblings. It lacked "Human Common Sense."

### **V28: The "Wiser" Model (Human Heuristics)**
*   **Mechanism**: Added Franchise Capping, Genre Alignment Shield, Legacy Boost, and Explainability.
*   **Strength**: First model that felt "human." Diverse, prestigious, relevant results.
*   **Problem**: Still relied on a single vector pool. Classic films from pre-1980 remained invisible.

---

## 2. The V28–V94 Arc: From Patches to Principles

### **V49–V67: The Heritage Hunt (Hardcoded Era)**
*   **Mechanism**: Progressively added hardcoded retrieval pools to surface specific missing films.
*   Pool D: Forced lookup of "The Umbrellas of Cherbourg" by title variations.
*   Pool E: Era-based safety net (1960s Romance/Music/Drama films).
*   Pool F: Direct ID lookup (`_id: "5967"`).
*   Pool C: Ghost pool for vectorless legends.
*   **Strength**: Specific classics like Umbrellas of Cherbourg finally appeared in results.
*   **Problem**: These were patches on a broken retrieval system, not fixes. For every film hardcoded in, hundreds remained invisible. The approach could not scale.

### **V64–V83: The Dead-Band Era (Scoring Compression)**
*   **Mechanism**: Introduced `vector_trust` binary threshold and `max(deep_score, 0.98)` floor. Any film passing a cosine threshold was boosted to 0.98 regardless of actual similarity.
*   **Strength**: Prevented low-similarity noise from dominating.
*   **Problem**: **Catastrophic score compression.** Ranks 2–55 were separated by only 0.05—effectively random ordering within a band. The engine could not distinguish a great match (0.92 cosine) from a mediocre one (0.76 cosine). Both scored ~1.93.

### **V84–V94: The CrossEncoder Experiment**
*   **Mechanism**: Loaded `cross-encoder/ms-marco-MiniLM-L-6-v2` for potential re-ranking.
*   **Discovery**: The model is trained for information retrieval ("does this document answer this query?"), not vibe similarity. It actively punished thematic siblings like *Moulin Rouge!* for not literally being "about" La La Land.
*   **Resolution**: CrossEncoder was loaded but never integrated into scoring. Consumed ~500MB RAM for zero benefit.

---

## 3. The V94+ Overhaul: Diagnosis and Systematic Fix

A critical external audit identified five distinct problems layered on top of each other:

### **Problem 1: Score Dead-Band Compression**
The `max(deep_score, 0.98)` floor made the top 55 results nearly indistinguishable. Combined with `vibe_power = semantic * 1.0`, the effective formula was `0.98 + semantic` ≈ 1.86–1.95 for everything. No discrimination.

**Fix**: Removed the floor entirely. New formula: `semantic * 2.0`, giving natural spread. A 0.92 similarity → 1.84, a 0.78 → 1.56 — **0.28 gap** instead of 0.05.

### **Problem 2: CrossEncoder Loaded But Never Used**
500MB of RAM wasted on a model that was never called and would have hurt quality if it was.

**Fix**: Removed import and initialization entirely.

### **Problem 3: Hardcoded Retrieval Pools**
Three pools (D, E, F) existed solely to force specific films into results. This masked the real retrieval problem and couldn't scale.

**Fix**: Replaced all three with a single organic **Keyword Siblings Pool**. When the anchor film has TMDB keywords (e.g., La La Land → `"musical", "jazz", "hollywood", "dancing", "ambition"`), retrieve films sharing those keywords. This surfaces Singin' in the Rain, Cabaret, and Umbrellas of Cherbourg *automatically* without hardcoding.

### **Problem 4: On-the-Fly Encoding (Latency Killer)**
When a candidate had no stored vector, the engine called `embedding_model.encode()` synchronously mid-loop. With multiple vectorless docs from Pool C (Ghost Pool), latency ballooned to ~16,000ms.

**Fix**: Skip vectorless docs. After the keyword enrichment pipeline, the vast majority of films have vectors. The few that don't are not worth 2+ seconds of encoding each.

### **Problem 5: Keywords Not Stored as Metadata**
The embedding pipeline (`generate_embeddings.py`) already baked TMDB keywords into the vibe string for vector generation. But keywords were not stored as a queryable field in AstraDB, preventing keyword-based retrieval and keyword overlap scoring.

**Fix**: Created `enrich_keywords.py` to read the source JSONL (99,186 movies) and push `keywords[]` and `tagline` fields to every document in AstraDB. This enables:
1. **Keyword-based retrieval pool** — catch thematic siblings that vector search misses
2. **Keyword overlap scoring bonus** — deterministic signal (max +0.10) independent of embedding quality
3. **Richer anchor text** — `get_enriched_text()` now includes keywords + tagline

---

## 4. Current Architecture (Post-V94+)

### Embedding Model
`jinaai/jina-embeddings-v2-base-en` — 768 dimensions, cosine similarity, stored in AstraDB.

### Vibe String (Index Time)
```
{overview} {overview}. Keywords: {keywords} {keywords}. Genres: {genres}. 
Cast: {actors}. Director: {director}. User Reviews: {reviews}. (Title: {title})
```
Overview and keywords are double-weighted to emphasize thematic content over metadata.

### Multi-Pool Retrieval
| Pool | Purpose | Filter | Limit |
|------|---------|--------|-------|
| **A: Vector** | Raw semantic similarity | None (full heritage access) | 100 |
| **B: Genre DNA** | High-rated genre matches | `genres ∈ anchor_genres, vote ≥ 7.0` | 50 |
| **C: Keywords** | Thematic siblings via shared keywords | `keywords ∈ anchor_top5, vote ≥ 6.5` | 50 |

All pools are merged, deduplicated, sorted by cosine similarity, and the top 100 are scored.

### Scoring Formula (SIBLING_DISCOVERY mode)
```
score = (semantic × 2.0) 
      + dna_boost              # +0.01–0.02 for genre overlap
      + keyword_bonus           # +0.02 per shared keyword, max 0.10
      + masterpiece_bonus       # +0.05 for vote_count > 5000 & rating ≥ 7.8
      - purity_penalty          # -0.01 per extra genre
      + (quality_score × 0.05)  # Tiny quality tie-breaker
      - penalty                 # Genre clash, reputation spam
      - mood_penalty            # Tonal conflict (cynical/absurdist)
      - alignment_penalty       # Slapstick in romance queries
```

### Key Design Decisions
1. **No score floors or clamps** — cosine similarity spreads naturally
2. **Semantic dominance** — quality is a 5% tie-breaker, not a ranking factor
3. **Penalty-based system** — films start with their vibe score and lose points for tonal mismatch
4. **Franchise capping** — max 2 results per franchise base title
5. **No on-the-fly encoding** — all vectors pre-computed at index time

---

## 5. Failure Analysis: The Cross-Era Vocabulary Gap

The most persistent challenge across V0–V94 was cross-era discovery. A search anchored on *La La Land* (2016) consistently failed to surface *Singin' in the Rain* (1952), despite both being Hollywood musicals about aspiring artists and romance.

**Root Cause**: Embedding models encode the *language* of a plot synopsis, not its themes. A 1952 synopsis ("A silent film star falls for a chorus girl") and a 2016 synopsis ("A jazz pianist pursues his dreams in Los Angeles") share almost no vocabulary despite identical thematic DNA.

**Why hardcoded pools failed**: Forcing specific films into results addresses one film at a time. There are hundreds of thematically relevant classics that share this vocabulary gap problem.

**Why keyword enrichment works**: TMDB keywords are *normalized tags*, not era-specific prose. Both films share keywords like `"musical"`, `"hollywood"`, `"romantic"`, `"exuberant"`. When these keywords are:
1. Embedded into the vibe string (already done at index time)
2. Stored as queryable metadata (done via `enrich_keywords.py`)
3. Used for both retrieval (Pool C) and scoring (keyword overlap bonus)

...the era gap effectively disappears. The retrieval becomes theme-aware rather than vocabulary-dependent.

---

## 6. The Great Pivot: Why "Technical Purity" Failed (V27 vs V28 vs V94+)

A critical turning point occurred between V27 and V28. In V27, we had achieved what we called "Peak Latent Space"—a model that used multi-vector "probes" to navigate the highest dimensions of the embedding space. Technically, it was our most advanced version.

**So why did we move to a "dumber" model (V28)?**

1.  **The "Alien Logic" Problem**: V27 was mathematically brilliant but humanly annoying. It would find a movie that was 99.9% semantically similar to *The Godfather*, but that movie would be a low-budget clone from 1974 that no one wants to watch. The AI saw a "match"; the human saw "noise."
2.  **The Sequel Trap**: The highly technical model had no concept of a "franchise." It treated every movie as an isolated vector. This led to results being dominated by 10 different versions of the same series, effectively killing the "Discovery" aspect of the engine.
3.  **Heuristics > Hyper-Parameters**: We realized that a "dumber" model with **Human-Centric Heuristics** (like Sequel Capping and Genre Locks) performed better in real-world tests than a "smart" model with complex math. By adding "common sense" constraints, we stopped the AI from over-optimizing for the wrong things.

**The same lesson repeated in V94+**: The dead-band compression (V64–V83) was an attempt to be clever—boosting everything above a threshold to a flat 0.98. The keyword pool (V94+) replaced 3 hardcoded hacks with 1 principled solution. In both cases, **simplicity and transparency beat complexity and patches.**

**V94+ isn't "simpler"; it's "principled."** It uses the same semantic engine but strips away accumulated hacks, lets cosine similarity speak for itself, and adds targeted deterministic signals (keyword overlap) where the embedding model is weakest (cross-era matching).

---

## 8. V100: The Tonal Guard & Living Poster Era

The latest evolution addresses the final frontier of semantic search: **Thematic Pollution.** While V94+ achieved high semantic recall, it lacked "Tonal Discipline." A search for "comedies" would often return "horror comedies" where the horror elements outweighed the humor.

### **Mechanism 1: Hard Tonal Penalties**
We implemented a **Tonal Guard** system that applies a flat **0.85 penalty** to any film that doesn't align with an explicitly requested genre.
*   **The "Comedy Rule"**: If a user searches for "comedy," any film without the Comedy genre tag is severely penalized. This effectively "kills" horror movies or dark thrillers that might share a few semantic overlaps but fail the "Vibe Test."
*   **The "Rom-Com" Bridge**: Added specialized logic to treat "rom-com" as a dual-signal (Romance + Comedy), ensuring both genres are boosted simultaneously.

### **Mechanism 2: Semantic Pluralization**
Traditional vector models often treat "comedy" and "comedies" as different distances. V100 adds a **Keyword Normalization** layer that maps plural variations and common shorthands (like "whodunnit" → Mystery/Crime) to their respective hard genre requirements.

### **Mechanism 3: The Living Poster Engine**
On the UI layer, we introduced **Interactive Variant Fetching**. Instead of displaying a static image, the search results now fetch alternative posters (textless, international, variant designs) in real-time on hover. This allows the user to see the different "visual facets" of a film's vibe before even clicking.

### **Mechanism 4: TMDB Pulse Integration**
Transitioned from static fallbacks to a **Live Trending Feed** synchronized with the TMDB global frequency. This ensures that the platform always feels "current" and alive, matching the latest cinematic trends across the world.

---

## 9. Final Conclusion
Our engine is no longer just a search bar; it is a **Cinematic Navigator.** By combining raw vector similarity (the "Vibe") with hard tonal guards (the "Discipline") and interactive visual variants (the "Pulse"), we have created a discovery tool that understands not just what a movie is about, but how it intends to make you feel.
