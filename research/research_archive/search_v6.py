import os
import re
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from astrapy import DataAPIClient
from dotenv import load_dotenv
import spacy
from functools import lru_cache
import time

# Load environment
load_dotenv()

# Initialize Astra DB
client = DataAPIClient(os.getenv("ASTRA_DB_APPLICATION_TOKEN"))
db = client.get_database_by_api_endpoint(os.getenv("ASTRA_DB_API_ENDPOINT"))
collection = db.get_collection("movies")

# Initialize Models
print("Loading Subtext V6 Edge Engine...")
model = SentenceTransformer('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True)
# Using a faster, 3-layer cross-encoder for production
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2') 
nlp = spacy.load("en_core_web_sm")

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

@lru_cache(maxsize=100)
def get_cached_embedding(text):
    return model.encode(text)

def search(query, num_results=10):
    metrics = {}
    start_total = time.time()
    
    # --- PHASE 1: NLP INTENT COST ---
    start_nlp = time.time()
    doc_nlp = nlp(query)
    is_navigation = False
    navigation_phrases = ["movies like", "similar to"]
    if any(p in query.lower() for p in navigation_phrases): is_navigation = True
    entities = [ent.label_ for ent in doc_nlp.ents]
    if "PERSON" in entities or "WORK_OF_ART" in entities: is_navigation = True
    clean_query = query.lower().strip()
    metrics["nlp_ms"] = int((time.time() - start_nlp) * 1000)
    
    # --- PHASE 2: ANCHOR COST ---
    start_anchor = time.time()
    clean_title = query.lower()
    for phrase in ["movies like ", "similar to "]:
        if clean_title.startswith(phrase):
            clean_title = clean_title.replace(phrase, "").strip()
            is_navigation = True; break
            
    title_vector = None
    title_genres = []
    anchor_themes = []
    title_match = collection.find_one({"title": {"$eq": clean_title}}, projection={"$vector": 1, "genres": 1, "title": 1, "overview": 1})
    if title_match and "$vector" in title_match:
        title_vector = np.array(title_match["$vector"])
        title_genres = get_genres_from_doc(title_match)
        ov = title_match.get("overview", "").lower()
        if any(w in ov for w in ["music", "jazz", "sing", "musical", "band", "dance"]): anchor_themes.append("music")
        if any(w in ov for w in ["scary", "murder", "kill", "death", "dark", "horror"]): anchor_themes.append("dark")
        if any(w in ov for w in ["dystopian", "future", "system", "control", "animal"]): anchor_themes.append("dystopian")
    metrics["anchor_db_ms"] = int((time.time() - start_anchor) * 1000)

    # --- PHASE 3: EMBEDDING COST ---
    start_emb = time.time()
    q_vec_main = get_cached_embedding(query)
    enrichment = f"{query}. " + " ".join(anchor_themes)
    q_vec_vibe = get_cached_embedding(f"{enrichment}. Mood and style.")
    metrics["embedding_ms"] = int((time.time() - start_emb) * 1000)
    
    # --- PHASE 4: DB RETRIEVAL COST ---
    start_ret = time.time()
    vibe_weight = 0.4 if not is_navigation else 0.1
    master_vec = (q_vec_main * (1 - vibe_weight) + q_vec_vibe * vibe_weight)
    candidates = list(collection.find({}, sort={"$vector": master_vec.tolist()}, limit=100, include_similarity=True, projection={"title": 1, "overview": 1, "genres": 1, "cast_names": 1, "release_date": 1}))
    metrics["vector_db_ms"] = int((time.time() - start_ret) * 1000)

    # --- PHASE 5: RE-RANKING COST (THE FUNNEL) ---
    start_rr = time.time()
    top_candidates = candidates[:40] # FUNNEL: Only top 40
    descriptions = []
    for doc in top_candidates:
        title = doc.get("title", "Unknown")
        year = doc.get("release_date", "0000")[:4]
        genres = ", ".join(get_genres_from_doc(doc))
        descriptions.append(f"{title} ({year}). {genres}. {doc.get('overview', '')}")
    cross_scores = cross_encoder.predict([(query, d) for d in descriptions])
    metrics["rerank_model_ms"] = int((time.time() - start_rr) * 1000)
    
    # Scoring Logic
    final_candidates = []
    for i, doc in enumerate(top_candidates):
        semantic_score = float(cross_scores[i])
        movie_genres = get_genres_from_doc(doc)
        title_low = doc.get("title", "").lower()
        ov_low = doc.get("overview", "").lower()
        candidate_themes = []
        if any(w in title_low or w in ov_low for w in ["music", "jazz", "sing", "musical", "band", "dance"]): candidate_themes.append("music")
        if any(w in title_low or w in ov_low for w in ["scary", "murder", "kill", "death", "dark", "horror"]): candidate_themes.append("dark")
        if any(w in title_low or w in ov_low for w in ["dystopian", "future", "system", "control", "animal", "satire"]): candidate_themes.append("dystopian")
        penalty = 0.0; theme_resonance = 0.0
        for c_theme in candidate_themes:
            if c_theme in anchor_themes: theme_resonance += 7.0
            else: penalty -= 10.0
        actor_boost = 0.0
        cast = doc.get("cast_names", [])
        if isinstance(cast, str): cast = [c.strip() for c in cast.split(",")]
        for actor in (cast or []):
            if len(actor) > 3 and actor.lower() in query.lower(): actor_boost = 5.0; break
        total_score = (semantic_score * 2.0) + (actor_boost * 15.0) + theme_resonance + penalty
        final_candidates.append({"title": doc.get("title"), "score": total_score})

    final_candidates.sort(key=lambda x: x["score"], reverse=True)
    metrics["total_ms"] = int((time.time() - start_total) * 1000)
    
    print(f"COST DASHBOARD: {metrics}")
    return final_candidates[:num_results], metrics

if __name__ == "__main__":
    q = "movies like la la land"
    results = search(q, num_results=5)
    for r in results:
        print(f"- {r['title']}")
