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
from typing import Optional, List, Dict
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


async def enrich_and_push_movie(tmdb_id: int, client: httpx.AsyncClient) -> Optional[dict]:
    """
    Fetches full movie details from TMDB, builds a vibe string,
    generates an embedding, and pushes the full document to AstraDB.
    Returns a dict with movie details if newly enriched, or None if it already exists/fails.
    """
    try:
        collection = _get_collection()
        if collection is None:
            print(f"⚠️ [ENRICH] AstraDB not available, skipping {tmdb_id}")
            return None

        # Check if already exists in AstraDB (Threaded to avoid blocking loop)
        existing = await asyncio.to_thread(
            collection.find_one,
            filter={"_id": str(tmdb_id)},
            projection={"$vector": 1}
        )
        if existing:
            vec = existing.get("$vector")
            if vec and not all(v == 0 for v in vec[:5]):
                return None  # Already has a valid vector

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
            return None

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
            return None

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
        return {"id": str(tmdb_id), "title": title, "vector": vec.tolist()}

    except Exception as e:
        print(f"⚠️ [ENRICH ERROR] tmdb_id={tmdb_id}: {e}")
        return None


def update_galaxy_mapping(newly_enriched: list[dict]):
    """
    Projects newly enriched movie embeddings into 3D using the saved UMAP reducer
    and appends them to all existing copies of galaxy_points.json in the project.
    """
    try:
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(backend_dir, "umap_reducer.pkl")
        
        if not os.path.exists(model_path):
            model_url = os.getenv("UMAP_MODEL_URL")
            if model_url:
                try:
                    print(f"📥 [GALAXY UPDATE] UMAP reducer not found. Downloading from {model_url}...")
                    import urllib.request
                    temp_model_path = model_path + ".tmp"
                    urllib.request.urlretrieve(model_url, temp_model_path)
                    os.replace(temp_model_path, model_path)
                    print("✅ [GALAXY UPDATE] UMAP model downloaded successfully.")
                except Exception as dl_err:
                    print(f"⚠️ [GALAXY UPDATE] Failed to download UMAP model: {dl_err}")
                    return
            else:
                print(f"⚠️ [GALAXY UPDATE] UMAP reducer model not found at {model_path} and UMAP_MODEL_URL is not set. Skipping galaxy points update.")
                return

        import pickle
        import umap
        
        print(f"🧠 [GALAXY UPDATE] Loading UMAP model from {model_path}...")
        with open(model_path, "rb") as f:
            reducer = pickle.load(f)
            
        print(f"🌌 [GALAXY UPDATE] Projecting {len(newly_enriched)} new vectors...")
        vectors = np.array([m["vector"] for m in newly_enriched])
        coords = reducer.transform(vectors)
        
        new_points = []
        for i, m in enumerate(newly_enriched):
            x, y, z = coords[i]
            new_points.append({
                "i": str(m["id"]),
                "t": m["title"][:60],
                "x": float(round(x, 3)),
                "y": float(round(y, 3)),
                "z": float(round(z, 3))
            })
            
        possible_paths = [
            os.path.join(backend_dir, "galaxy_points.json"),
            os.path.join(os.path.dirname(backend_dir), "galaxy_points.json"),
            os.path.join(os.path.dirname(backend_dir), "frontend", "public", "galaxy_points.json"),
        ]
        
        existing_paths = [p for p in possible_paths if os.path.exists(p)]
        if not existing_paths:
            print("⚠️ [GALAXY UPDATE] No galaxy_points.json files found to update.")
            return
            
        for path in existing_paths:
            try:
                print(f"📝 [GALAXY UPDATE] Updating {path}...")
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                existing_ids = {str(item["i"]) for item in data}
                points_to_add = [p for p in new_points if str(p["i"]) not in existing_ids]
                
                if points_to_add:
                    data.extend(points_to_add)
                    temp_path = path + ".tmp"
                    with open(temp_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, separators=(',', ':'))
                    os.replace(temp_path, path)
                    print(f"✅ [GALAXY UPDATE] Successfully added {len(points_to_add)} new points to {path}")
                else:
                    print(f"ℹ [GALAXY UPDATE] All {len(new_points)} points already exist in {path}")
            except Exception as fe:
                print(f"⚠️ [GALAXY UPDATE] Failed to update {path}: {fe}")
                
    except Exception as e:
        print(f"⚠️ [GALAXY UPDATE ERROR] Failed to project/update galaxy mapping: {e}")


def load_existing_galaxy_ids() -> set:
    """
    Attempts to read galaxy_points.json from the nearest location and return the set of all existing movie IDs.
    """
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(backend_dir, "galaxy_points.json"),
        os.path.join(os.path.dirname(backend_dir), "galaxy_points.json"),
        os.path.join(os.path.dirname(backend_dir), "frontend", "public", "galaxy_points.json"),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return {str(item["i"]) for item in data}
            except Exception as e:
                print(f"⚠️ [GALAXY CHECK] Failed to load {path}: {e}")
    return set()


async def fetch_vectors_and_titles_from_astra(tmdb_ids: list[int], batch_size: int = 50) -> list[dict]:
    """
    Fetches $vector and title values from AstraDB for a list of TMDB IDs.
    Returns a list of dicts: {"id": str, "title": str, "vector": list}.
    """
    collection = _get_collection()
    if collection is None:
        return []

    results = []
    for i in range(0, len(tmdb_ids), batch_size):
        batch = tmdb_ids[i:i + batch_size]
        str_ids = [str(tid) for tid in batch]
        try:
            docs = list(await asyncio.to_thread(
                collection.find,
                filter={"_id": {"$in": str_ids}},
                projection={"_id": 1, "$vector": 1, "title": 1},
                limit=batch_size
            ))
            for doc in docs:
                vec = doc.get("$vector")
                if vec and not all(v == 0 for v in vec[:5]):
                    results.append({
                        "id": str(doc["_id"]),
                        "title": doc.get("title", "Unknown Title"),
                        "vector": list(vec)
                    })
        except Exception as e:
            print(f"⚠️ [TASTE] Batch vector/title fetch failed: {e}")

    return results


async def enrich_missing_movies(tmdb_ids: list[int]):
    """
    Batch-checks which tmdb_ids are missing from AstraDB and enriches them.
    Also projects coordinates and updates galaxy_points.json for any movies
    lacking coordinates.
    """
    collection = _get_collection()
    if collection is None:
        return

    # 1. Load existing galaxy points IDs to avoid re-projecting existing ones
    existing_galaxy_ids = load_existing_galaxy_ids()

    # 2. Check which IDs are missing or have zero vectors in AstraDB
    missing_from_astra = []
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
                    missing_from_astra.append(tid)
            
            if (i + batch_size) % 500 == 0 or (i + batch_size) >= len(tmdb_ids):
                print(f"🔍 [ENRICH] Checked {min(i + batch_size, len(tmdb_ids))}/{len(tmdb_ids)} movies...")
        except Exception as e:
            print(f"⚠️ [ENRICH] Batch check failed: {e}")
            missing_from_astra.extend(batch)

    # 3. Enrich missing movies in AstraDB
    newly_enriched = []
    if missing_from_astra:
        print(f"🔄 [ENRICH] {len(missing_from_astra)}/{len(tmdb_ids)} movies missing from AstraDB. Enriching...")
        semaphore = asyncio.Semaphore(10)  # Faster concurrency for TMDB API
        async with httpx.AsyncClient(timeout=20.0) as client:
            async def enrich_one(tid):
                async with semaphore:
                    return await enrich_and_push_movie(tid, client)

            tasks = [enrich_one(tid) for tid in missing_from_astra]
            results = await asyncio.gather(*tasks)
            newly_enriched = [r for r in results if r]
    else:
        print(f"✅ [ENRICH] All {len(tmdb_ids)} movies already in AstraDB")

    # 4. Identify which of the user's movies are missing from galaxy_points.json
    missing_galaxy_ids = [tid for tid in tmdb_ids if str(tid) not in existing_galaxy_ids]
    
    # 5. Fetch vectors and titles for any missing galaxy movies that are already in AstraDB
    # (i.e. those missing from galaxy, but NOT missing from AstraDB since we didn't just enrich them)
    missing_from_astra_set = set(missing_from_astra)
    already_in_astra_but_missing_galaxy = [
        tid for tid in missing_galaxy_ids if tid not in missing_from_astra_set
    ]

    fetched_from_astra = []
    if already_in_astra_but_missing_galaxy:
        print(f"🔍 [GALAXY UPDATE] Fetching vectors for {len(already_in_astra_but_missing_galaxy)} movies already in AstraDB but missing from galaxy...")
        fetched_from_astra = await fetch_vectors_and_titles_from_astra(already_in_astra_but_missing_galaxy)

    # 6. Combine newly enriched and existing movies to project
    movies_to_project = newly_enriched + fetched_from_astra
    
    if movies_to_project:
        print(f"🌟 [GALAXY UPDATE] Found {len(movies_to_project)} movies to add to galaxy points. Updating galaxy mapping...")
        update_galaxy_mapping(movies_to_project)
    else:
        print("✅ [GALAXY UPDATE] No missing galaxy coordinates to project.")

    print(f"🌟 [ENRICH] Enrichment complete. Processed {len(tmdb_ids)} movies.")


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
    SYNC_PROGRESS[user_id]["message"] = "🧬 mapping cinematic genome..."
    taste_data = await compute_taste_vector(user_id)
    if taste_data is None:
        print(f"⚠️ [DNA] Could not compute taste vector for user {user_id}")
        SYNC_PROGRESS[user_id]["message"] = "sync complete (need 10+ ratings for DNA)"
        return

    # 4. Save
    SYNC_PROGRESS[user_id]["message"] = "⚡ activating neural engine..."
    await save_taste_vector(user_id, taste_data)
    print(f"🧬 [DNA][END] Taste DNA successfully mapped for user {user_id}")
    SYNC_PROGRESS[user_id]["message"] = "DNA mapped successfully!"
