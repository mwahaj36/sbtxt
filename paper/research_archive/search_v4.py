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
print("Loading Subtext V4 Engine (Jina AI V2 - Profile Aware)...")
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = SentenceTransformer('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True, local_files_only=False).to(device)
model.half()
model.max_seq_length = 2048

print("Loading NLP profile extractor (spaCy)...")
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

GENRE_VECTORS = {g: model.encode(desc) for g, desc in TMDB_GENRE_MAP.items()}

# Mood Conflict Map (Genres that usually don't mix well for "Vibe" matching)
CONFLICT_MAP = {
    "Music": ["War", "Horror"],
    "Romance": ["War", "Horror"],
    "Family": ["Horror", "Crime"],
    "Comedy": ["War"]
}

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
    if len(words) >= 3: return 1.5 
    if intent in ["movie", "film", "good", "nice"]: return 0.5
    return 1.0

def get_genres_from_doc(doc):
    genres = doc.get("genres", [])
    if isinstance(genres, str): genres = [g.strip() for g in genres.split(",")]
    return [g.get("name", g) if isinstance(g, dict) else str(g) for g in genres]

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

    # 2. SEMANTIC GENRE EXTRACTION (Profile-based: Top 3)
    query_vec_for_genres = model.encode(query)
    all_genre_matches = []
    for g_name, g_vec in GENRE_VECTORS.items():
        similarity = np.dot(query_vec_for_genres, g_vec) / (np.linalg.norm(query_vec_for_genres) * np.linalg.norm(g_vec))
        all_genre_matches.append((g_name, similarity))
    
    all_genre_matches.sort(key=lambda x: x[1], reverse=True)
    # Detect a "Genre Profile" rather than just one genre
    detected_intent_genres = {g[0]: g[1] for g in all_genre_matches[:3] if g[1] > 0.65}
    
    if detected_intent_genres:
        print(f"Detected Intent Profile: {', '.join(detected_intent_genres.keys())}")

    # 2.5. SMART TITLE EXTRACTION & LOOKUP (The "Anchor")
    title_vector = None
    title_genres = []
    
    # Try to extract the core title by stripping comparison phrases
    clean_title = query.lower()
    for phrase in ["movies like ", "movie like ", "films like ", "film like ", "similar to ", "anything like "]:
        if clean_title.startswith(phrase):
            clean_title = clean_title.replace(phrase, "").strip()
            break
    
    print(f"Debug: Attempting to find anchor title: '{clean_title}'")
            
    # Try common casing variants
    variants = [clean_title, clean_title.title(), clean_title.capitalize(), clean_title.upper()]
    title_match = None
    for variant in variants:
        title_match = collection.find_one({"title": {"$eq": variant}}, projection={"$vector": 1, "title": 1, "genres": 1})
        if title_match: 
            print(f"Debug: Found exact text match: '{variant}'")
            break
        
    # FALLBACK: Vector-Assisted Detection
    if not title_match:
        print(f"Debug: Exact text match failed for '{clean_title}'. Trying Vector-Assisted match...")
        temp_title_vec = model.encode(clean_title).tolist()
        # Find the single closest movie to this title string
        vector_matches = list(collection.find({}, sort={"$vector": temp_title_vec}, limit=1, include_similarity=True))
        if vector_matches:
            sim = vector_matches[0].get("$similarity", 0)
            if sim > 0.90:
                title_match = vector_matches[0]
                print(f"Debug: Vector-Assisted match found: '{title_match.get('title')}' (Similarity: {sim:.3f})")
            else:
                print(f"Debug: Vector match found '{vector_matches[0].get('title')}' but similarity {sim:.3f} was too low.")
    
    if title_match:
        m_id = title_match["_id"]
        # Ensure we have the vector and genres
        if "$vector" in title_match and "genres" in title_match:
            vec_doc = title_match
        else:
            vec_doc = collection.find_one({"_id": m_id}, projection={"$vector": 1, "title": 1, "genres": 1})
            
        if vec_doc and "$vector" in vec_doc:
            title_vector = np.array(vec_doc["$vector"])
            title_genres = get_genres_from_doc(vec_doc)
            print(f"SUCCESS: Anchor Title Locked: '{vec_doc.get('title')}' (Genres: {', '.join(title_genres)})")
            
            # CRITICAL: If we found the anchor movie, its REAL genres should override the guessed ones
            if title_genres:
                print(f"Overriding semantic guesses with actual genre profile: {title_genres}")
                detected_intent_genres = {g: 1.0 for g in title_genres}
        else:
            print(f"ERROR: Found title match '{title_match.get('title')}' but could not retrieve its vector.")

    # 3. CONSOLIDATED VECTOR SEARCH
    print(f"Finalizing Master Vector for {len(all_intents)} intents...")
    all_vectors = []
    for intent in all_intents:
        is_full = (intent == query)
        is_key = (intent == keyword_query)
        weight = get_intent_weight(intent)
        
        if is_full: weight *= 2.5 # Heavy anchor
        elif is_key: weight *= 1.2
        
        if title_vector is not None and is_full:
            query_vec = title_vector
        else:
            vec1 = model.encode(intent)
            vec2 = model.encode(enrich_query(intent))
            query_vec = (vec1 * 0.7 + vec2 * 0.3)
        all_vectors.append(query_vec * weight)

    master_vector = np.mean(all_vectors, axis=0).tolist()

    # 4. Search
    astra_filter = {}
    if filters:
        if filters.get("language"): astra_filter["original_language"] = filters["language"]
        if filters.get("year_min"): astra_filter["release_year"] = {"$gte": int(filters["year_min"])}
        if filters.get("year_max"):
            if "release_year" not in astra_filter: astra_filter["release_year"] = {}
            astra_filter["release_year"]["$lte"] = int(filters["year_max"])

    results = list(collection.find(astra_filter, sort={"$vector": master_vector}, limit=100, include_similarity=True))
    if not results: return []

    # 5. V4 RE-RANKING: GENRE PROFILE MATCHING
    max_sim = results[0].get("$similarity", 1.0)
    final_results = []

    for doc in results:
        raw_sim = doc.get("$similarity", 0)
        base_score = raw_sim / max_sim
        movie_genres = get_genres_from_doc(doc)
        
        # --- 1. Genre Profile Scoring ---
        genre_score = 0.0
        match_count = 0
        
        # Merge semantic intent with anchor movie genres
        target_genres = set(list(detected_intent_genres.keys()) + title_genres)
        
        for g in movie_genres:
            if g in target_genres:
                match_count += 1
                # Weight by semantic detected similarity if available, else 1.0
                genre_score += detected_intent_genres.get(g, 1.0)
        
        # Multi-match bonus (Intersections are powerful)
        if match_count >= 2: genre_score *= 1.5
        
        # --- 2. Smart Mood Conflict Penalty ---
        penalty = 0.0
        for g in movie_genres:
            # ONLY penalize if the genre is a conflict AND it wasn't requested
            if g not in target_genres:
                for target in target_genres:
                    if g in CONFLICT_MAP.get(target, []):
                        penalty -= 1.5 # Vibe-killer penalty
                        break

        # --- 3. Actor & Title Boosts ---
        actor_boost = 0.0
        cast = doc.get("cast_names", [])
        if isinstance(cast, str): cast = [c.strip() for c in cast.split(",")]
        for actor in (cast or []):
            if len(actor) > 3 and actor.lower() in query.lower():
                actor_boost = 5.0; break # BUFFED: Names are anchors
        
        title_boost = 5.0 if query.lower() == doc.get("title", "").lower() else 0.0

        # --- 4. Conservative Popularity ---
        pop_score = doc.get("popularity", 0)
        popularity_boost = math.log10(pop_score + 1) * 0.10 # Reduced from V3

        total_score = base_score + genre_score + actor_boost + title_boost + popularity_boost + penalty

        final_results.append({
            "title": doc.get("title"),
            "score": total_score,
            "id": doc["_id"],
            "vibe_pct": min(total_score * 10, 99),
            "genres": movie_genres
        })

    final_results.sort(key=lambda x: x["score"], reverse=True)
    return final_results[:num_results]


if __name__ == "__main__":
    q = "movies like la la land"
    print(f"\nQuery: '{q}'")
    for i, res in enumerate(search(q)):
        print(f"  {i+1}. {res['title']} (Score: {res['score']:.2f}) [{', '.join(res['genres'])}]")
