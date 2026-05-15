import os
import re
import math
import torch
import numpy as np
import spacy
from sentence_transformers import SentenceTransformer
from astrapy import DataAPIClient
from dotenv import load_dotenv

load_dotenv()
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

# 1. Load models
print("Loading high-quality search engine (Jina AI V2 - FP16)...")
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = SentenceTransformer('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True, local_files_only=True).to(device)
model.half()
model.max_seq_length = 2048

print("Loading NLP keyword extractor (spaCy)...")
nlp = spacy.load("en_core_web_sm")

# 2. Pre-calculate Genre "Vibe" Vectors with Context
TMDB_GENRE_MAP = {
    "Action": "An action-packed movie with stunts and excitement",
    "Adventure": "An adventurous journey or quest",
    "Animation": "An animated or cartoon movie",
    "Comedy": "A funny comedy movie that makes people laugh",
    "Crime": "A crime drama or thriller about criminals",
    "Documentary": "A real-life documentary film",
    "Drama": "A serious, emotional drama movie about life and feelings",
    "Family": "A family-friendly movie for all ages",
    "Fantasy": "A fantasy movie with magic and mythical creatures",
    "History": "A historical movie based on real past events",
    "Horror": "A scary horror movie intended to frighten",
    "Music": "A movie focused on music, musicals, or musicians",
    "Mystery": "A mystery movie about solving a puzzle or crime",
    "Romance": "A romantic movie about love and relationships",
    "Science Fiction": "A sci-fi movie about technology, space, or the future",
    "Thriller": "A suspenseful thriller movie with high tension",
    "War": "A movie about war and military conflict",
    "Western": "A western movie about cowboys and the old west"
}

print("Pre-calculating contextual genre map...")
GENRE_VECTORS = {g: model.encode(desc) for g, desc in TMDB_GENRE_MAP.items()}

# 3. Initialize Astra
client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
collection = db.get_collection("movies")

# --- Helpers ---

def extract_keywords(text):
    doc = nlp(text.lower())
    keywords = [token.text for token in doc if not token.is_stop and not token.is_punct and len(token.text) > 1]
    return " ".join(keywords) if keywords else text

def smart_split(query):
    query = query.lower().strip()
    parts = re.split(r'\s+and\s+|\s+with\s+|\s+but\s+|,\s*', query)
    return [p.strip() for p in parts if len(p.strip()) > 2]

def enrich_query(text):
    return f"{text}. This describes the theme, tone, and narrative style of a movie."

def get_intent_weight(intent):
    words = intent.split()
    if len(words) >= 3: return 1.5 # Boost long intents
    if intent in ["movie", "film", "good", "nice"]: return 0.5
    return 1.0

# --- MAIN SEARCH ---

def search(query, filters=None, num_results=10):
    # 1. INTENT DECOMPOSITION
    sub_intents = smart_split(query)
    all_intents = list(set(sub_intents + [query]))
    
    keyword_query = query.lower().strip()
    if len(query.split()) > 4:
        keyword_query = extract_keywords(query)
        if keyword_query != query.lower().strip():
            all_intents = list(set(all_intents + [keyword_query]))

    # 2. SEMANTIC GENRE EXTRACTION (Refined to Top-1)
    query_vec_for_genres = model.encode(query)
    all_genre_matches = []
    for g_name, g_vec in GENRE_VECTORS.items():
        similarity = np.dot(query_vec_for_genres, g_vec) / (np.linalg.norm(query_vec_for_genres) * np.linalg.norm(g_vec))
        all_genre_matches.append((g_name, similarity))
    
    all_genre_matches.sort(key=lambda x: x[1], reverse=True)
    # We only take the TOP ONE genre match to avoid "Double Boosting" unrelated themes
    detected_genres = [g for g in all_genre_matches[:1] if g[1] > 0.7]
    
    if detected_genres:
        print(f"Primary Genre Intent: {detected_genres[0][0]} ({round(float(detected_genres[0][1]), 2)})")

    # 2.5. DIRECT TITLE LOOKUP
    title_vector = None
    title_match = collection.find_one({"title": {"$eq": query}}, include_similarity=False)
    if not title_match:
        for variant in [query.title(), query.upper(), query.lower()]:
            title_match = collection.find_one({"title": {"$eq": variant}}, include_similarity=False)
            if title_match: break
    
    if title_match:
        m_id = title_match["_id"]
        vec_doc = collection.find_one({"_id": m_id}, projection={"$vector": 1})
        if vec_doc and "$vector" in vec_doc:
            title_vector = np.array(vec_doc["$vector"])
            print(f"Direct title match found: '{title_match.get('title')}'")

    # 3. CONSOLIDATED VECTOR SEARCH
    print(f"Blending {len(all_intents)} intents into Master Vector...")
    all_vectors = []
    for intent in all_intents:
        is_full = (intent == query)
        is_key = (intent == keyword_query)
        
        # We give much more weight to the full query (the "Anchor")
        weight = get_intent_weight(intent)
        if is_full: weight *= 2.0 
        elif is_key: weight *= 1.2
        
        if title_vector is not None and is_full:
            query_vec = title_vector
        else:
            vec1 = model.encode(intent)
            vec2 = model.encode(enrich_query(intent))
            query_vec = (vec1 * 0.7 + vec2 * 0.3)
        all_vectors.append(query_vec * weight)

    master_vector = np.mean(all_vectors, axis=0).tolist()

    # 4. Search with Hibernation Retry
    astra_filter = {}
    if filters:
        if filters.get("language"): astra_filter["original_language"] = filters["language"]
        if filters.get("year_min"): astra_filter["release_year"] = {"$gte": int(filters["year_min"])}
        if filters.get("year_max"):
            if "release_year" not in astra_filter: astra_filter["release_year"] = {}
            astra_filter["release_year"]["$lte"] = int(filters["year_max"])
        if filters.get("vote_min"): astra_filter["vote_average"] = {"$gte": float(filters["vote_min"])}

    try:
        results = list(collection.find(astra_filter, sort={"$vector": master_vector}, limit=100, include_similarity=True))
    except Exception as e:
        print(f"DB is likely resuming... retrying in 5s: {e}")
        import time; time.sleep(5)
        results = list(collection.find(astra_filter, sort={"$vector": master_vector}, limit=100, include_similarity=True))

    if not results: return []

    # 5. FINAL SCORING & RE-RANKING
    max_sim = results[0].get("$similarity", 1.0)
    final_results = []

    for doc in results:
        m_id = doc["_id"]
        raw_sim = doc.get("$similarity", 0)
        base_score = raw_sim / max_sim

        # --- Semantic Boosts ---
        
        # 1. ACTOR BOOST
        actor_boost = 0.0
        cast = doc.get("cast_names", [])
        if isinstance(cast, str): cast = [c.strip() for c in cast.split(",")]
        for actor in (cast or []):
            if len(actor) > 3 and actor.lower() in query.lower():
                actor_boost = 1.0; break

        # 2. TITLE BOOST
        title = doc.get("title", "")
        title_boost = 2.0 if query.lower() == title.lower() else 0.0

        # 3. SEMANTIC GENRE BOOST (Refined)
        genre_boost = 0.0
        genres = doc.get("genres", [])
        if isinstance(genres, str): genres = [g.strip() for g in genres.split(",")]
        movie_genre_names = [g.get("name", g) if isinstance(g, dict) else str(g) for g in genres]
        
        for g_name, g_similarity in detected_genres:
            if g_name in movie_genre_names:
                # Apply a strong boost only for the SINGLE best genre
                genre_boost += (g_similarity * 0.7)

        # 4. POPULARITY BOOST
        pop_score = doc.get("popularity", 0)
        popularity_boost = math.log10(pop_score + 1) * 0.15

        total_score = base_score + actor_boost + title_boost + genre_boost + popularity_boost

        final_results.append({
            "title": title,
            "score": total_score,
            "id": m_id,
            "vibe_pct": min(total_score * 10, 99)
        })

    final_results.sort(key=lambda x: x["score"], reverse=True)
    return final_results[:num_results]


if __name__ == "__main__":
    q = "movies which are sad like la la land"
    print(f"\nQuery: '{q}'")
    for i, res in enumerate(search(q)):
        print(f"  {i+1}. {res['title']} (Score: {res['score']:.2f})")
