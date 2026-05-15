import os
import json
import re
import torch
import numpy as np
import math
from sentence_transformers import SentenceTransformer
from astrapy import DataAPIClient
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

# 1. Load the search model
print("Loading high-quality search engine (Jina AI V2 - FP16)...")
device = 'cuda' if torch.cuda.is_available() else 'cpu'
# local_files_only=True prevents DNS crashes during search
model = SentenceTransformer('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True).to(device)
model.half() 
model.max_seq_length = 2048

# 2. Initialize Astra
client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
collection = db.get_collection("movies")

# --- Helpers ---

def smart_split(query):
    query = query.lower().strip()
    parts = re.split(r'\s+and\s+|\s+with\s+|,\s*', query)
    parts = [p.strip() for p in parts if len(p.strip()) > 2]
    if len(parts) <= 1:
        words = query.split()
        if len(words) >= 4:
            return [" ".join(words[:-1]), words[-1]]
    return parts

def enrich_query(text):
    return f"{text}. This describes the theme and narrative style of a movie."

def get_intent_weight(intent):
    words = intent.split()
    if len(words) >= 3:
        return 1.3
    if intent in ["movie", "film", "good", "nice"]:
        return 0.5
    return 1.0

# --- MAIN SEARCH ---

def search(query, filters=None, num_results=10):
    # 1. INTENT SPLIT
    sub_intents = smart_split(query)
    all_intents = list(set(sub_intents + [query]))
    
    print(f"Searching intents: {all_intents}")
    aggregated = {}
    
    # 2. MULTI-INTENT + DUAL EMBEDDING
    for intent in all_intents:
        # Full query is the anchor
        is_full_query = (intent == query)
        weight = get_intent_weight(intent) * (2.0 if is_full_query else 1.0)
        
        vec1 = model.encode(intent)
        vec2 = model.encode(enrich_query(intent))
        query_vec = (vec1 * 0.7 + vec2 * 0.3).tolist() # Slightly more literal
        
        astra_filter = {}
        if filters:
            if filters.get("language"): astra_filter["original_language"] = filters["language"]
            if filters.get("year_min"): astra_filter["release_year"] = {"$gte": int(filters["year_min"])}
            if filters.get("year_max"):
                if "release_year" not in astra_filter: astra_filter["release_year"] = {}
                astra_filter["release_year"]["$lte"] = int(filters["year_max"])
            if filters.get("vote_min"): astra_filter["vote_average"] = {"$gte": float(filters["vote_min"])}
        
        results = list(collection.find(
            astra_filter,
            sort={"$vector": query_vec},
            limit=500, # Balanced limit
            include_similarity=True
        ))
        
        if not results: continue
        
        max_sim = results[0].get("$similarity", 1.0)
        
        for doc in results:
            m_id = doc["_id"]
            raw_sim = doc.get("$similarity", 0)
            sim = raw_sim / max_sim
            
            if m_id not in aggregated:
                aggregated[m_id] = {
                    "doc": doc,
                    "score": 0,
                    "matches": 0
                }
            
            aggregated[m_id]["score"] += sim * weight
            # High threshold to ensure true semantic matches only
            if raw_sim > 0.82:
                aggregated[m_id]["matches"] += 1
    
    # 3. FINAL SCORING & RE-RANKING
    final_results = []
    total_intents = len(all_intents)
    
    for m_id, data in aggregated.items():
        doc = data["doc"]
        base_score = data["score"]
        matches = data["matches"]
        
        # Coverage penalty
        coverage = (matches / total_intents)
        score = (base_score / total_intents) * coverage
        
        # --- Metadata Boosts (The "Soul" of Search) ---
        
        # ACTOR BOOST (Highest priority)
        actor_boost = 0.0
        cast = doc.get("cast_names", [])
        if isinstance(cast, str): cast = [c.strip() for c in cast.split(",")]
        for actor in (cast or []):
            if len(actor) > 3 and actor.lower() in query.lower():
                actor_boost = 1.0 # Significant boost for actor mention
                break
        
        # TITLE BOOST
        title = doc.get("title", "")
        title_boost = 2.0 if query.lower() == title.lower() else 0.0
        
        # POPULARITY (Logarithmic tie-breaker)
        pop_score = doc.get("popularity", 0)
        popularity_boost = math.log10(pop_score + 1) * 0.15
        
        # Combine everything
        total_score = score + actor_boost + title_boost + popularity_boost
        
        if total_score > 0:
            final_results.append({
                "title": title,
                "poster_path": doc.get("poster_path"),
                "score": total_score,
                "matches": matches,
                "id": m_id,
                "vibe_pct": min(total_score * 100, 99) # Capped at 99 for realism
            })
    
    # Sort by the final calculated score
    final_results.sort(key=lambda x: x["score"], reverse=True)
    
    # Final cleanup: ensure the vibe_pct feels "real" compared to others
    if final_results:
        top_score = final_results[0]["score"]
        for r in final_results:
            # Relative percentage but with a floor
            r["vibe_pct"] = max(20, round((r["score"] / top_score) * 98, 1))

    return final_results[:num_results]

if __name__ == "__main__":
    test_q = "casey affleck playing a ghost"
    print(f"\nFinal Stability Test: '{test_q}'")
    results = search(test_q)
    for i, res in enumerate(results[:5]):
        print(f"{i+1}. {res['title']} (Score: {res['score']:.2f} | Vibe: {res['vibe_pct']}%)")