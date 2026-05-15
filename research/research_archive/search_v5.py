import os
import json
import re
import torch
import numpy as np
import math
import spacy
from sentence_transformers import SentenceTransformer, CrossEncoder
from astrapy import DataAPIClient
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

# 1. Load Engines
print("Loading Subtext V5 Adaptive Engine...")
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Bi-Encoder (For fast retrieval)
model = SentenceTransformer('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True)
model.half()
model.to(device)

# Cross-Encoder (For high-precision re-ranking)
print("Loading Cross-Encoder re-ranker...")
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', device=device)

# NLP for Intent Detection
print("Loading NLP intent classifier...")
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# 2. Initialize Astra
client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
collection = db.get_collection("movies")

CONFLICT_MAP = {
    "Comedy": ["War", "Horror", "Documentary"],
    "Romance": ["War", "Horror", "Action"],
    "Family": ["Horror", "Thriller", "Crime"],
    "Music": ["War", "Horror"]
}

def get_genres_from_doc(doc):
    genres = doc.get("genres", [])
    if isinstance(genres, str):
        return [g.strip() for g in genres.split(",")]
    return genres

def search(query, filters=None, num_results=10):
    # --- PHASE 1: INTENT CLASSIFICATION ---
    doc_nlp = nlp(query)
    is_navigation = False
    
    # Check for title/actor indicators
    navigation_phrases = ["movies like", "film like", "starring", "with", "actor", "similar to", "anything like"]
    if any(p in query.lower() for p in navigation_phrases):
        is_navigation = True
    
    # Check for named entities (PERSON/WORK_OF_ART)
    entities = [ent.label_ for ent in doc_nlp.ents]
    if "PERSON" in entities or "WORK_OF_ART" in entities or "ORG" in entities or "FAC" in entities:
        is_navigation = True
        
    # Heuristic: Consecutive capitalized words are almost always Entities
    if re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', query):
        is_navigation = True

    # 2. Multi-Case Title Check for Intent
    # (If the query matches a known title, it's Navigation)
    clean_query = query.lower().strip()
    title_variants = [clean_query, clean_query.title(), clean_query.capitalize()]
    title_exists = collection.find_one({"title": {"$in": title_variants}}, projection={"title": 1})
    if title_exists:
        is_navigation = True
        print(f"Case-match found for '{title_exists.get('title')}'. Upgrading to NAVIGATION.")

    print(f"Intent Mode: {'NAVIGATION' if is_navigation else 'DISCOVERY'}")

    # --- PHASE 2: ANCHOR EXTRACTION (V4.1 Logic) ---
    clean_title = query.lower()
    for phrase in ["movies like ", "movie like ", "films like ", "film like ", "similar to ", "anything like "]:
        if clean_title.startswith(phrase):
            clean_title = clean_title.replace(phrase, "").strip()
            is_navigation = True
            break
            
    title_vector = None
    title_genres = []
    
    # Attempt Title match
    variants = [clean_title, clean_title.title(), query, query.title()]
    title_match = None
    for v in variants:
        if len(v) < 2: continue
        title_match = collection.find_one({"title": {"$eq": v}}, projection={"$vector": 1, "genres": 1, "title": 1, "overview": 1})
        if title_match: break
        
    if not title_match and is_navigation:
        # Mini vector search for title
        temp_v = model.encode(clean_title).tolist()
        v_matches = list(collection.find({}, sort={"$vector": temp_v}, limit=1, include_similarity=True))
        if v_matches and v_matches[0].get("$similarity", 0) > 0.94:
            title_match = v_matches[0]

    anchor_themes = []
    if title_match and "$vector" in title_match:
        title_vector = np.array(title_match["$vector"])
        title_genres = get_genres_from_doc(title_match)
        
        # --- NEW: Extract Hidden Themes from Overview ---
        ov = title_match.get("overview", "").lower()
        if any(w in ov for w in ["music", "jazz", "sing", "musical", "band", "dance"]):
            title_genres.append("Music")
            anchor_themes.append("music")
        if any(w in ov for w in ["scary", "murder", "kill", "death", "dark"]):
            anchor_themes.append("dark")
        if any(w in ov for w in ["dystopian", "future", "system", "control"]):
            anchor_themes.append("dystopian")
            
        print(f"Anchor Locked: '{title_match.get('title')}' (Enhanced Genres: {title_genres})")

    # --- PHASE 3: FAST RETRIEVAL (Bi-Encoder) ---
    q_vec_main = model.encode(query)
    
    # Enrich query with anchor themes if found
    enrichment = f"{query}. " + " ".join(anchor_themes)
    q_vec_vibe = model.encode(f"{enrichment}. Mood, atmosphere, and cinematic style.")
    
    vibe_weight = 0.5 if not is_navigation else 0.1
    master_vec = (q_vec_main * (1 - vibe_weight) + q_vec_vibe * vibe_weight)
    
    if title_vector is not None and title_vector.shape == master_vec.shape:
        master_vec = (master_vec * 0.3) + (title_vector * 0.7)
    
    master_vec = master_vec.tolist()

    astra_filter = {} 
    # BUFF: Increased limit to 200 to catch 'Hidden Classics' like Singin' in the Rain
    candidates = list(collection.find(
        astra_filter, 
        sort={"$vector": master_vec}, 
        limit=200, 
        include_similarity=True,
        projection={"title": 1, "overview": 1, "genres": 1, "cast_names": 1, "release_date": 1, "$vector": 1}
    ))
    if not candidates: return []


    # --- PHASE 4: HIGH-FIDELITY RE-RANKING (Cross-Encoder) ---
    # ENRICHMENT: Feed the Cross-Encoder Title, Year, and Genres, not just Overview
    descriptions = []
    for doc in candidates:
        title = doc.get("title", "Unknown")
        year = doc.get("release_date", "0000")[:4]
        genres = ", ".join(get_genres_from_doc(doc))
        ov = doc.get("overview", "")
        descriptions.append(f"{title} ({year}). Genres: {genres}. {ov}")
        
    cross_scores = cross_encoder.predict([(query, desc) for desc in descriptions])
    
    final_candidates = []
    for i, doc in enumerate(candidates):
        semantic_score = float(cross_scores[i])
        
        # --- Theme Detection Buff (Check Title/Overview) ---
        movie_genres = get_genres_from_doc(doc)
        title_low = doc.get("title", "").lower()
        ov_low = doc.get("overview", "").lower()
        
        # Detect candidate themes dynamically
        candidate_themes = []
        if any(w in title_low or w in ov_low for w in ["music", "jazz", "sing", "musical", "band", "dance"]): 
            candidate_themes.append("music")
        if any(w in title_low or w in ov_low for w in ["scary", "murder", "kill", "death", "dark", "horror"]): 
            candidate_themes.append("dark")
        if any(w in title_low or w in ov_low for w in ["dystopian", "future", "system", "control", "animal", "satire"]): 
            candidate_themes.append("dystopian")
        
        # Entity Boosts
        actor_boost = 0.0
        cast = doc.get("cast_names", [])
        if isinstance(cast, str): cast = [c.strip() for c in cast.split(",")]
        for actor in (cast or []):
            if len(actor) > 3 and actor.lower() in query.lower():
                actor_boost = 5.0; break
        
        # Title Boost (Adaptive)
        t_boost_val = 5.0 if is_navigation else 1.0
        title_boost = t_boost_val if query.lower() == doc.get("title", "").lower() else 0.0
        
        # Genre Profile
        genre_match_score = 0.0
        target_genres = set(title_genres)
        for g in movie_genres:
            if g in target_genres:
                genre_match_score += 1.0
        
        # Conflict Penalty
        penalty = 0.0
        if not is_navigation:
            for g in movie_genres:
                for target in target_genres:
                    if g in CONFLICT_MAP.get(target, []):
                        penalty -= 2.0; break

        # --- V5.5 TONAL CONSISTENCY ---
        theme_resonance = 0.0
        for c_theme in candidate_themes:
            if c_theme in anchor_themes:
                theme_resonance += 7.0 # Buffed resonance
            else:
                # Penalty for introducing a 'heavy' theme the anchor doesn't have
                penalty -= 10.0 

        # FINAL V5.5 SCORE
        entity_multiplier = 15.0 
        
        if is_navigation:
            total_score = (semantic_score * 0.2) + (actor_boost * entity_multiplier) + (title_boost * entity_multiplier) + (genre_match_score * 4.0) + theme_resonance + penalty
            # DEBUG
            if "Lobster" in doc.get("title", "") or "Silver Linings" in doc.get("title", ""):
                 print(f"DEBUG {doc.get('title')}: Match={genre_match_score}, Resonance={theme_resonance}, Penalty={penalty}")
        else:
            total_score = (semantic_score * 2.0) + (actor_boost * entity_multiplier) + (title_boost * entity_multiplier) + (genre_match_score * 1.0) + theme_resonance + penalty
                
        final_candidates.append({
            "title": doc.get("title"),
            "score": total_score,
            "genres": movie_genres,
            "id": doc["_id"],
            "vibe_pct": min(max(0, (semantic_score + 10) * 5), 99) # Map -10/10 range to 0-99
        })

    final_candidates.sort(key=lambda x: x["score"], reverse=True)
    return final_candidates[:num_results]

if __name__ == "__main__":
    test_queries = ["1950s musical like la la land"]
    for q in test_queries:
        print(f"\n--- V5 Results for: '{q}' ---")
        results = search(q, num_results=5)
        for i, res in enumerate(results):
            print(f"{i+1}. {res['title']} (Score: {res['score']:.2f}) {res['genres']}")
