# Subtext Algorithm V94: Final Production Architecture

This document summarizes the final architectural state of the Subtext discovery engine as of V94. The engine has transitioned from a heuristic-heavy experimental model to a high-fidelity, hybrid semantic discovery system optimized for Astra DB.

## 1. Hybrid Intent Decomposition
Subtext decomposes user queries into three primary intents before any database interaction occurs:
- **SIBLING_DISCOVERY:** Triggered by "movies like [X]". Uses the anchor film's "DNA" (embeddings, keywords, director) to find thematic peers.
- **PERSON_STRICT:** Triggered by explicit triggers like "movies starring [X]". Enforces a **Hard Identity Lock** at the database level.
- **GLOBAL / PERSON_VIBE:** General semantic exploration (e.g., "femme witch cult movies"). Uses vector search with weighted tonal penalties.

## 2. Astra-Safe Anchor Resolution
To handle the lack of `$regex` support in Astra DB and the prevalence of long subtitles in movie titles (e.g., *Borat: Cultural Learnings...*), V94 implements a multi-stage lookup:
1. **Canonical Match:** Checks 8 title casing variants in a single `$in` query.
2. **Year-Aware Disambiguation:** Extracts 4-digit years from queries to correctly identify remakes (e.g., *Road House 2024* vs. *Road House 1989*).
3. **Range-Based Prefix Search:** Fallback using string ranges (e.g., searching between "Borat" and "Borau") to catch movies starting with the requested keyword.

## 3. Multi-Pool Retrieval Strategy
Instead of a single vector call, Subtext merges candidates from four distinct pools:
- **Pool A (Vector):** The top 100 semantic matches for the "vibe" embedding.
- **Pool B (DNA):** High-quality films (7.5+ rating) sharing the anchor's semantic space.
- **Pool C (Keywords):** Movies sharing the top 5 niche keywords from the anchor.
- **Pool D (Heritage):** Directorial filmography retrieval to ensure legacy consistency.

## 4. Asymmetric Additive Scoring
Ranking is determined by a transparent penalty-based formula:
- **Base:** Cosine similarity spread (preserved, not compressed).
- **Boosts:** Director match (+0.15), Niche Keyword overlap (+0.02 per hit), Masterpiece status (+0.05).
- **Penalties:** 
    - **Vibe Purge:** Strong penalty (-0.60) for tonal clashes (e.g., Horror in a Romance query).
    - **Purity Penalty:** Deductions for movies that drift too far from the anchor's genre footprint.
    - **Identity Lock:** Heavy penalty (-0.50) for movies missing the requested actor in VIBE mode.

## 5. Score Normalization & UI
- **Display Score:** Capped at 0.99 for siblings and 1.0 for the pinned anchor to ensure a premium UI experience.
- **Deduplication:** Uses `(title, year)` composite keys to allow remakes to appear alongside originals.

---
*Algorithm V94 represents the culmination of 94 systematic iterations, achieving a balance between AI-driven discovery and deterministic metadata precision.*
