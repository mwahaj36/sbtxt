"""
taste.py — Taste Vector Engine for Subtext

Computes a per-user 768-dim taste embedding from their Letterboxd history.
Uses existing movie vectors from AstraDB (no new ML inference needed).

Weight scheme:
  - Base weight: 1.0 for all watched movies
  - Rating multiplier: (rating / 5.0)^2
  - Like bonus: +0.5 if is_liked = True
  - Recency decay: last 6 months get 1.2x
  - Watchlist excluded (aspirational, not taste)

Also handles auto-enrichment of missing movies into AstraDB during sync.
"""

import os
import re
import json
import asyncio
import numpy as np
import httpx
from datetime import datetime, timedelta
from database import get_db_connection
from state import SYNC_PROGRESS

# Lazy imports to avoid circular dependency with search.py
_collection = None
_embed_fn = None

GENRE_CENTROIDS_PATH = os.path.join(os.path.dirname(__file__), "genre_centroids.json")

# ─────────────────────────────────────────────────────────────────────────────
# LAZY INIT
# ─────────────────────────────────────────────────────────────────────────────

def _get_collection():
    global _collection
    if _collection is None:
        from search import collection
        _collection = collection
    return _collection


def _get_embed():
    global _embed_fn
    if _embed_fn is None:
        from search import embed
        _embed_fn = embed
    return _embed_fn


# ─────────────────────────────────────────────────────────────────────────────
# TMDB ENRICHMENT — Fetch full movie details & push to AstraDB
# ─────────────────────────────────────────────────────────────────────────────

def _get_tmdb_headers():
    token = os.getenv("TMDB_TOKEN") or os.getenv("TMDB_API_KEY")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def enrich_and_push_movie(tmdb_id: int, client: httpx.AsyncClient) -> bool:
    """
    Fetches full movie details from TMDB, builds a vibe string,
    generates an embedding, and pushes the full document to AstraDB.
    Returns True if successful, False otherwise.
    """
    try:
        collection = _get_collection()
        if collection is None:
            print(f"⚠️ [ENRICH] AstraDB not available, skipping {tmdb_id}")
            return False

        # Check if already exists in AstraDB (Threaded to avoid blocking loop)
        existing = await asyncio.to_thread(
            collection.find_one,
            filter={"_id": str(tmdb_id)},
            projection={"$vector": 1}
        )
        if existing:
            vec = existing.get("$vector")
            if vec and not all(v == 0 for v in vec[:5]):
                return True  # Already has a valid vector

        # Fetch from TMDB with appended credits + keywords
        # Probe MOVIE first, then TV (covers 100% of Letterboxd content)
        endpoint = "movie"
        resp = await client.get(
            f"https://api.themoviedb.org/3/{endpoint}/{tmdb_id}",
            params={"append_to_response": "keywords,credits"},
            headers=_get_tmdb_headers(),
            timeout=15.0
        )
        
        if resp.status_code == 404:
            endpoint = "tv"
            print(f"ℹ️ [ENRICH] {tmdb_id} not found in 'movie', probing 'tv'...")
            resp = await client.get(
                f"https://api.themoviedb.org/3/{endpoint}/{tmdb_id}",
                params={"append_to_response": "keywords,credits"},
                headers=_get_tmdb_headers(),
                timeout=15.0
            )

        if resp.status_code != 200:
            print(f"❌ [ENRICH] TMDB fetch failed for {tmdb_id} (Tried movie & tv): {resp.status_code}")
            return False

        movie = resp.json()

        # Extract structured data (handling differences between Movie and TV schemas)
        title = movie.get("title") or movie.get("name", "Unknown Title")
        overview = movie.get("overview", "")
        genres = [g["name"] for g in movie.get("genres", [])]
        genres_str = ", ".join(genres)
        
        keywords_data = movie.get("keywords", {})
        # TMDB TV uses "results", Movie uses "keywords"
        kw_list = keywords_data.get("keywords", keywords_data.get("results", []))
        keywords = [k["name"] for k in kw_list]
        keywords_str = ", ".join(keywords)

        credits = movie.get("credits", {})
        director = ""
        if endpoint == "movie":
            director = next((m["name"] for m in credits.get("crew", []) if m.get("job") == "Director"), "")
        else:
            # For TV, we prioritize creators, then executive producers
            creators = [c["name"] for c in movie.get("created_by", [])]
            if not creators:
                creators = [m["name"] for m in credits.get("crew", []) if m.get("job") in ["Executive Producer", "Producer"]][:2]
            director = ", ".join(creators) if creators else "TV Production"

        cast_names = [m["name"] for m in credits.get("cast", [])[:10]]
        actors_str = ", ".join(cast_names)

        # Handle release years (first_air_date for TV)
        release_date = movie.get("release_date") or movie.get("first_air_date", "")
        release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None

        # Build vibe string — same format as generate_embeddings.py
        vibe = (
            f"{overview} {overview}. "
            f"Keywords: {keywords_str} {keywords_str}. "
            f"Genres: {genres_str}. "
            f"Cast: {actors_str}. "
            f"Director: {director}. "
            f"(Title: {title})"
        )

        # Generate embedding
        embed = _get_embed()
        vec = embed(vibe[:8000])
        if vec is None or np.all(vec == 0):
            print(f"⚠️ [ENRICH] Embedding failed for {title}")
            return False

        # Build AstraDB document
        doc = {
            "_id": str(tmdb_id),
            "title": title,
            "overview": overview,
            "genres": genres,
            "keywords": keywords,
            "tagline": movie.get("tagline", ""),
            "cast_names": cast_names,
            "director": director,
            "vote_average": movie.get("vote_average", 0),
            "vote_count": movie.get("vote_count", 0),
            "popularity": movie.get("popularity", 0),
            "poster_path": movie.get("poster_path"),
            "release_year": release_year,
            "original_language": movie.get("original_language", ""),
            "runtime": movie.get("runtime"),
            "$vector": vec.tolist(),
        }

        # Upsert into AstraDB (Threaded)
        if existing:
            await asyncio.to_thread(
                collection.find_one_and_update,
                {"_id": str(tmdb_id)},
                {"$set": {k: v for k, v in doc.items() if k != "_id"}}
            )
        else:
            await asyncio.to_thread(collection.insert_one, doc)

        print(f"🌟 [ENRICH] Pushed to AstraDB: {title} ({release_year})")
        return True

    except Exception as e:
        print(f"⚠️ [ENRICH ERROR] tmdb_id={tmdb_id}: {e}")
        return False


async def enrich_missing_movies(tmdb_ids: list[int]):
    """
    Batch-checks which tmdb_ids are missing from AstraDB and enriches them.
    Called during sync to ensure all user movies are in the vector DB.
    """
    collection = _get_collection()
    if collection is None:
        return

    # 1. Check which IDs are missing or have zero vectors
    missing_ids = []
    batch_size = 100
    print(f"🔍 [ENRICH] Checking AstraDB for {len(tmdb_ids)} movies...")
    for i in range(0, len(tmdb_ids), batch_size):
        batch = tmdb_ids[i:i + batch_size]
        str_ids = [str(tid) for tid in batch]
        try:
            docs = list(await asyncio.to_thread(
                collection.find,
                filter={"_id": {"$in": str_ids}},
                projection={"$vector": 1},
                limit=batch_size
            ))
            found_ids = {int(doc["_id"]) for doc in docs if doc.get("$vector")}
            for tid in batch:
                if tid not in found_ids:
                    missing_ids.append(tid)
            
            if (i + batch_size) % 500 == 0 or (i + batch_size) >= len(tmdb_ids):
                print(f"🔍 [ENRICH] Checked {min(i + batch_size, len(tmdb_ids))}/{len(tmdb_ids)} movies...")
        except Exception as e:
            print(f"⚠️ [ENRICH] Batch check failed: {e}")
            missing_ids.extend(batch)

    if not missing_ids:
        print(f"✅ [ENRICH] All {len(tmdb_ids)} movies already in AstraDB")
        return

    print(f"🔄 [ENRICH] {len(missing_ids)}/{len(tmdb_ids)} movies missing from AstraDB. Enriching...")

    semaphore = asyncio.Semaphore(10)  # Faster concurrency for TMDB API
    async with httpx.AsyncClient(timeout=20.0) as client:
        async def enrich_one(tid):
            async with semaphore:
                await enrich_and_push_movie(tid, client)

        tasks = [enrich_one(tid) for tid in missing_ids]
        await asyncio.gather(*tasks)

    print(f"🌟 [ENRICH] Enrichment complete. Processed {len(missing_ids)} movies.")


# ─────────────────────────────────────────────────────────────────────────────
# VECTOR BATCH FETCH FROM ASTRADB
# ─────────────────────────────────────────────────────────────────────────────

async def fetch_vectors_batch(tmdb_ids: list[int], batch_size: int = 20) -> dict:
    """
    Fetches existing $vector values from AstraDB for a list of TMDB IDs.
    Returns {tmdb_id: np.array} dict. Skips movies with no/zero vectors.
    """
    collection = _get_collection()
    if collection is None:
        return {}

    vectors = {}
    for i in range(0, len(tmdb_ids), batch_size):
        batch = tmdb_ids[i:i + batch_size]
        str_ids = [str(tid) for tid in batch]
        try:
            docs = list(await asyncio.to_thread(
                collection.find,
                filter={"_id": {"$in": str_ids}},
                projection={"$vector": 1},
                limit=batch_size
            ))
            for doc in docs:
                vec = doc.get("$vector")
                if vec and not all(v == 0 for v in vec[:5]):
                    vectors[int(doc["_id"])] = np.array(vec, dtype=float)
        except Exception as e:
            print(f"⚠️ [TASTE] Batch vector fetch failed: {e}")

    return vectors


# ─────────────────────────────────────────────────────────────────────────────
# CORE TASTE VECTOR COMPUTATION
# ─────────────────────────────────────────────────────────────────────────────

async def compute_taste_vector(user_id: str) -> dict:
    """
    Builds a 768-dim taste embedding from a user's Letterboxd history.
    Returns dict with 'vector', 'movie_count', 'top_genres', or None if insufficient data.
    """
    # 1. Fetch user's rated/watched movies (exclude watchlist)
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tmdb_id, rating, is_liked, watched_date 
                FROM user_ratings 
                WHERE user_id = %s 
                  AND interaction_type = 'watched'
                  AND tmdb_id IS NOT NULL
            """, (user_id,))
            rows = cur.fetchall()
    finally:
        conn.close()

    if len(rows) < 10:
        print(f"⚠️ [TASTE] User {user_id} has only {len(rows)} movies. Need 10+ for taste vector.")
        return None

    # 2. Fetch vectors from AstraDB
    tmdb_ids = [row[0] for row in rows]
    vectors = await fetch_vectors_batch(tmdb_ids)

    if len(vectors) < 5:
        print(f"⚠️ [TASTE] Only {len(vectors)} vectors found in AstraDB. Not enough for taste vector.")
        return None

    # 3. Compute weights
    now = datetime.now()
    six_months_ago = now - timedelta(days=180)
    
    weighted_vecs = []
    weights = []
    
    for row in rows:
        tmdb_id, rating, is_liked, watched_date = row
        if tmdb_id not in vectors:
            continue

        w = 1.0
        
        # Rating multiplier (quadratic — 5★ dominates, 2★ barely contributes)
        if rating:
            w *= (float(rating) / 5.0) ** 2
        
        # Like bonus
        if is_liked:
            w += 0.5
        
        # Recency decay
        if watched_date:
            try:
                if isinstance(watched_date, str):
                    watched_dt = datetime.strptime(watched_date, "%Y-%m-%d")
                else:
                    watched_dt = datetime.combine(watched_date, datetime.min.time())
                if watched_dt > six_months_ago:
                    w *= 1.2
            except:
                pass

        weighted_vecs.append(vectors[tmdb_id])
        weights.append(w)

    if not weighted_vecs:
        return None

    # 4. Weighted average
    vec_matrix = np.array(weighted_vecs)
    weight_array = np.array(weights)
    taste_vec = np.average(vec_matrix, axis=0, weights=weight_array)

    # 5. L2 normalize
    norm = np.linalg.norm(taste_vec)
    if norm > 0:
        taste_vec = taste_vec / norm

    # 6. Compute top genres by analyzing which genre centroids are closest
    top_genres = _compute_top_genres(taste_vec)

    return {
        "vector": taste_vec,
        "movie_count": len(weighted_vecs),
        "top_genres": top_genres,
    }


def _compute_top_genres(taste_vec: np.ndarray) -> list:
    """
    Compares taste vector against genre centroids to determine user's genre affinities.
    Uses centering (subtracting global mean) and contrast boosting.
    """
    try:
        if os.path.exists(GENRE_CENTROIDS_PATH):
            with open(GENRE_CENTROIDS_PATH, "r") as f:
                data = json.load(f)
            
            global_centroid = np.array(data["global_centroid"], dtype=float)
            centroids = data["genres"]
            
            # 2. Subtract global centroid (80% strength to preserve raw preference)
            # This prevents common genres like 'Drama' from being completely erased.
            center_strength = 0.8
            vec = taste_vec - (global_centroid * center_strength)
            
            scores = []
            for genre, centroid in centroids.items():
                centered_centroid = np.array(centroid, dtype=float) - (global_centroid * center_strength)
                
                # Cosine Similarity
                sim = np.dot(vec, centered_centroid) / (np.linalg.norm(vec) * np.linalg.norm(centered_centroid) + 1e-9)
                scores.append((genre, sim))
            
            scores.sort(key=lambda x: x[1], reverse=True)
            
            # Contrast Boosting: Scale the top genre to be high, and others relative.
            # Raw centered similarities are often in range [0.1, 0.5]
            if not scores: return []
            
            max_sim = scores[0][1]
            min_sim = scores[-1][1]
            sim_range = max_sim - min_sim if max_sim != min_sim else 1.0
            
            results = []
            # Increase to Top 6 to capture sub-genres (like Romance in RomComs)
            for g, s in scores[:6]:
                # Relative score in range [0, 1]
                rel_score = (s - min_sim) / sim_range
                # Boost contrast (power < 1 makes the curve steeper at the bottom)
                boosted = rel_score ** 0.6 
                affinity = round(45 + (boosted * 53)) # Map to range [45%, 98%]
                results.append({"genre": g, "affinity": affinity})
                
            return results
    except Exception as e:
        print(f"⚠️ [TASTE] Genre centroid computation failed: {e}")
    
    return []


# ─────────────────────────────────────────────────────────────────────────────
# ANTI-TASTE VECTOR (movies rated ≤ 2★)
# ─────────────────────────────────────────────────────────────────────────────

async def compute_anti_taste_vector(user_id: str) -> np.ndarray:
    """
    Builds a 768-dim anti-taste embedding from poorly-rated movies.
    Returns normalized vector or None if not enough data.
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tmdb_id FROM user_ratings 
                WHERE user_id = %s 
                  AND interaction_type = 'watched'
                  AND rating IS NOT NULL AND rating <= 2.0
                  AND tmdb_id IS NOT NULL
            """, (user_id,))
            rows = cur.fetchall()
    finally:
        conn.close()

    if len(rows) < 3:
        return None  # Need at least 3 poorly-rated movies

    tmdb_ids = [row[0] for row in rows]
    vectors = await fetch_vectors_batch(tmdb_ids)

    if len(vectors) < 3:
        return None

    vec_matrix = np.array(list(vectors.values()))
    anti_vec = np.mean(vec_matrix, axis=0)
    
    norm = np.linalg.norm(anti_vec)
    if norm > 0:
        anti_vec = anti_vec / norm
    
    return anti_vec


# ─────────────────────────────────────────────────────────────────────────────
# PERSISTENCE
# ─────────────────────────────────────────────────────────────────────────────

def _save_taste_vector_sync(user_id: str, taste_data: dict):
    """Saves taste vector + metadata to PostgreSQL (Sync)."""
    conn = get_db_connection()
    if not conn: return
    try:
        vector_list = taste_data["vector"].tolist()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE users SET 
                    taste_vector = %s,
                    taste_vector_updated_at = NOW(),
                    taste_vector_movie_count = %s,
                    taste_top_genres = %s
                WHERE id = %s
            """, (vector_list, taste_data["movie_count"], json.dumps(taste_data["top_genres"]), user_id))
            conn.commit()
    finally: conn.close()

async def save_taste_vector(user_id: str, taste_data: dict):
    """Saves taste vector + metadata to PostgreSQL (Async wrapper)."""
    await asyncio.to_thread(_save_taste_vector_sync, user_id, taste_data)
    print(f"🧬 [TASTE] Saved taste vector for user {user_id}")

def _get_taste_vector_sync(user_id: str) -> dict:
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT taste_vector, taste_vector_updated_at, taste_vector_movie_count, taste_top_genres FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if not row or not row[0]: return None
            
            vector_data = row[0]
            if isinstance(vector_data, str):
                try:
                    vector_data = json.loads(vector_data)
                except:
                    pass
            
            top_genres = row[3]
            if isinstance(top_genres, str): top_genres = json.loads(top_genres)
            
            return {
                "vector": np.array(vector_data, dtype=float),
                "updated_at": row[1].isoformat() if row[1] else None,
                "movie_count": row[2] or 0,
                "top_genres": top_genres or [],
            }
    finally: conn.close()

async def get_taste_vector(user_id: str) -> dict:
    return await asyncio.to_thread(_get_taste_vector_sync, user_id)


# ─────────────────────────────────────────────────────────────────────────────
# BACKGROUND TASK WRAPPER
# ─────────────────────────────────────────────────────────────────────────────

async def refresh_taste_vector_bg(user_id: str):
    """
    Background task that:
    1. Enriches any missing movies into AstraDB
    2. Computes the taste vector
    3. Saves it to PostgreSQL
    """
    print(f"🧬 [DNA][START] Starting cinematic DNA mapping for user {user_id}...")
    # Using state.SYNC_PROGRESS
    # 1. Collect all user's tmdb_ids
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT tmdb_id FROM user_ratings 
                WHERE user_id = %s AND tmdb_id IS NOT NULL
            """, (user_id,))
            all_ids = [row[0] for row in cur.fetchall()]
    finally:
        conn.close()

    if not all_ids:
        print(f"⚠️ [DNA] No movies found to compute taste for user {user_id}")
        return

    # 2. Enrich missing movies
    SYNC_PROGRESS[user_id]["message"] = f"Enriching {len(all_ids)} movies..."
    await enrich_missing_movies(all_ids)

    # 3. Compute taste vector
    SYNC_PROGRESS[user_id]["message"] = "Calculating cinematic DNA..."
    taste_data = await compute_taste_vector(user_id)
    if taste_data is None:
        print(f"⚠️ [DNA] Could not compute taste vector for user {user_id}")
        return

    # 4. Save
    SYNC_PROGRESS[user_id]["message"] = "Saving profile..."
    await save_taste_vector(user_id, taste_data)
    print(f"🧬 [DNA][END] Taste DNA successfully mapped for user {user_id}")
