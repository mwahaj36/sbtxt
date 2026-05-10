import os
import time
import re
import json
import numpy as np
import spacy

from dotenv import load_dotenv
from functools import lru_cache
from sentence_transformers import SentenceTransformer, CrossEncoder
from astrapy import DataAPIClient

# =============================================================================
# ENV + DB
# =============================================================================

load_dotenv()

client = DataAPIClient(os.getenv("ASTRA_DB_APPLICATION_TOKEN"))
db = client.get_database_by_api_endpoint(os.getenv("ASTRA_DB_API_ENDPOINT"))
collection = db.get_collection("movies")

# =============================================================================
# MODELS + DATA
# =============================================================================

print("Loading Subtext V13 Constraint Engine...")

embedding_model = SentenceTransformer(
    "jinaai/jina-embeddings-v2-base-en",
    trust_remote_code=True
)

reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

nlp = spacy.load("en_core_web_sm")

# Load People Index for Precision NER
print("Loading People Index...")
PEOPLE_INDEX_PATH = os.path.join(os.path.dirname(__file__), "people_index.json")
try:
    with open(PEOPLE_INDEX_PATH, "r", encoding="utf-8") as f:
        PEOPLE_SET = set(json.load(f))
except Exception as e:
    print(f"Warning: Could not load people_index.json: {e}")
    PEOPLE_SET = set()

# =============================================================================
# CONFIG
# =============================================================================

FINAL_RESULTS = 10

# DRIVE_SIGNAL set for the tone constraint model
DRIVE_SIGNALS = {
    "quiet", "minimal", "silent", "restrained", "understated", 
    "emotionally subtle", "somber", "subdued", "moody", "neon", "noir"
}

# =============================================================================
# UTILS
# =============================================================================

@lru_cache(maxsize=256)
def embed(text: str):
    return embedding_model.encode(text)

def get_base_title(title: str):
    """
    Strips sequel/prequel markers to find the 'core' franchise name.
    """
    # 1. Remove subtitles (anything after a colon)
    base = title.split(":")[0]
    
    # 2. Remove common sequel markers
    # Matches " Part II", " Chapter 4", " Vol. 3", etc.
    base = re.sub(r'\s+(Part|Chapter|Vol|Volume)\s+[IVX0-9]+.*', '', base, flags=re.IGNORECASE)
    # Matches trailing numbers like "Toy Story 2"
    base = re.sub(r'\s+[2-9]$|\s+10$', '', base) 
    
    return base.strip()

# =============================================================================
# RESOLUTION & INTENT LAYERS
# =============================================================================

def resolve_entities(query):
    q = query.lower()
    entities = []
    
    # 1. Canonical Resolution via People Set (Sliding Window)
    # Note: DB contains Title Case names. We title() the resolved name for grounding.
    words = q.replace(",", " ").replace(".", " ").split()
    for n in [3, 2]:
        for i in range(len(words) - n + 1):
            window = " ".join(words[i:i+n])
            if window in PEOPLE_SET:
                entities.append(window.title())
                
    # 2. spaCy NER Fallback (Preserves Case)
    if not entities:
        doc = nlp(query)
        for ent in doc.ents:
            if ent.label_ in ["PERSON"]:
                entities.append(ent.text)
            
    # 3. Regex Fallback (Preserves Case)
    if not entities:
        regex_cap = r'\b[A-Z][a-z]+\s[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b'
        matches = re.findall(regex_cap, query)
        for m in matches:
            entities.append(m)

    return list(set(entities))

def classify_entity_intent(query, entities):
    q = query.lower()
    
    filmography_triggers = [
        "movies with", "movies starring", "films starring",
        "movies by", "films by", "directed by",
        "starring", "films of", "movies of", "filmography"
    ]
    
    has_person = len(entities) > 0
    is_explicit = any(t in q for t in filmography_triggers)
    
    if has_person and is_explicit:
        return "PERSON_STRICT"
    if has_person:
        return "PERSON_VIBE"
        
    return "GLOBAL"

# =============================================================================
# SCORING MODEL (V25 GENRE CONSISTENCY)
# =============================================================================

REPETITION_LOG = {}

def cosine_similarity(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return np.dot(a, b) / (norm_a * norm_b)

def get_enriched_text(doc):
    title = doc.get("title", "")
    overview = doc.get("overview", "")
    genres = " ".join(doc.get("genres", []))
    return f"[{genres}] {title}: {overview}"

def score_movie_v26(query, query_vec, doc_vec, doc, mode, entities, cross_score=None, anchor_genres=None):
    q_low = query.lower()
    doc_genres = doc.get("genres", [])
    
    # 1. Base Deep Score
    semantic = float(cosine_similarity(query_vec, doc_vec))
    norm_cross = (cross_score + 15) / 30 
    deep_score = np.clip(norm_cross, 0.0, 1.0) if cross_score is not None else semantic

    # 2. Mood Purity Rule (Generic Tone Enforcement)
    # This rule penalizes movies that have 'Mood Killers' in their genre list
    genre_penalty = 0.0
    
    # MOOD: TENSE/SCARY (Horror/Thriller) -> Killer: Comedy, Family
    if any(w in q_low for w in ["scary", "scare", "horror", "terrify", "thrilling"]):
        if any(g in doc_genres for g in ["Comedy", "Family"]):
            genre_penalty = 0.50
            
    # MOOD: FUN/LAUGH (Comedy) -> Killer: Horror, Thriller, War
    if any(w in q_low for w in ["laugh", "funny", "comedy", "joke"]):
        if any(g in doc_genres for g in ["Horror", "Thriller", "War"]):
            genre_penalty = 0.40
            
    # MOOD: EMOTIONAL (Drama/Cry/Beautiful) -> Killer: Action, Adventure, Horror, Comedy
    if any(w in q_low for w in ["heartbreaking", "beautiful", "cry", "sad", "emotional"]):
        if any(g in doc_genres for g in ["Action", "Adventure", "Horror", "Comedy"]):
            genre_penalty = 0.60 # Strongest lock for emotional purity

    # 3. Quality & Popularity
    vote_raw = float(doc.get("vote_average", 5.0))
    pop_raw = float(doc.get("popularity", 5.0))
    quality_score = (vote_raw / 10.0)
    pop_score = np.log1p(pop_raw) / 5.0 
    
    # 4. Reputation
    penalty = 0.0
    if doc.get("title") in REPETITION_LOG:
        penalty = 0.05 * REPETITION_LOG[doc.get("title")]

    # 5. Genre Alignment (Vibe Consistency)
    alignment_bonus = 0.0
    alignment_penalty = 0.0
    if anchor_genres and mode != "PERSON_STRICT":
        overlap = set(doc_genres).intersection(set(anchor_genres))
        if not overlap:
            # Harsh penalty for absolute vibe mismatch (e.g. Western matching a Crime anchor)
            alignment_penalty = 0.35
        else:
            # Bonus for sharing multiple core genres
            alignment_bonus = len(overlap) * 0.03

    # 7. Legacy Boost (Masterpiece Discovery)
    legacy_boost = 0.0
    vote_count = float(doc.get("vote_count", 0))
    if vote_count > 1000 and alignment_bonus > 0:
        legacy_boost = np.log10(vote_count) * 0.02 # Rewards high-quality, widely-seen thematic matches

    # 8. Intent Weights
    if mode == "GLOBAL" or mode == "SIBLING_DISCOVERY":
        return (deep_score * 0.70) + (quality_score * 0.15) + (pop_score * 0.10) + (semantic * 0.05) + alignment_bonus + legacy_boost - genre_penalty - alignment_penalty - penalty
    
    if mode == "PERSON_STRICT":
        constraint_match = 0.0
        cast = doc.get("cast_names", [])
        director = str(doc.get("director", "")).lower()
        if isinstance(cast, str):
            cast = [c.lower().strip() for c in cast.split(",")]
        else:
            cast = [str(c).lower() for c in (cast or [])]
        for ent in entities:
            if ent.lower() in director or any(ent.lower() == c for c in cast):
                constraint_match = 1.0
                break
        return (deep_score * 0.30) + (quality_score * 0.40) + (pop_score * 0.10) + (constraint_match * 0.20) + alignment_bonus + legacy_boost - genre_penalty - alignment_penalty
    
    if mode == "PERSON_VIBE":
        constraint_match = 0.0
        cast = doc.get("cast_names", [])
        director = str(doc.get("director", "")).lower()
        if isinstance(cast, str):
            cast = [c.lower().strip() for c in cast.split(",")]
        else:
            cast = [str(c).lower() for c in (cast or [])]
        for ent in entities:
            if ent.lower() in director or any(ent.lower() == c for c in cast):
                constraint_match = 1.0
                break
        return (deep_score * 0.60) + (quality_score * 0.10) + (pop_score * 0.10) + (constraint_match * 0.10) + (semantic * 0.10) + alignment_bonus + legacy_boost - genre_penalty - alignment_penalty - penalty

    return deep_score

# =============================================================================
# SEARCH ENGINE (RESOLVE -> GROUND -> RETRIEVE -> RANK)
# =============================================================================

def search(query: str, k: int = 10):
    global REPETITION_LOG
    start_time = time.time()
    q_low = query.lower()
    
    # 1. RESOLVE INTENT
    entities = resolve_entities(query)
    mode = classify_entity_intent(query, entities)
    
    # 2. 'MOVIES LIKE' SPECIAL HANDLER (Sibling Discovery)
    search_vec = None
    like_triggers = ["movies like", "films like", "similar to", "reminds me of"]
    reference_title = None
    ref_genres = []
    
    for trigger in like_triggers:
        if trigger in q_low:
            reference_title = query[q_low.find(trigger) + len(trigger):].strip().strip("'\"")
            mode = "SIBLING_DISCOVERY"
            break
            
    if reference_title and len(reference_title) > 2:
        ref_doc = collection.find_one(filter={"title": reference_title})
        if not ref_doc:
            ref_doc = collection.find_one(filter={"title": reference_title.title()})
        if ref_doc:
            search_vec = embed(get_enriched_text(ref_doc))
            ref_genres = ref_doc.get("genres", [])
            print(f"[SIBLING_MODE] Grounding to: '{ref_doc.get('title')}' Genres: {ref_genres}")

    if search_vec is None:
        search_vec = embed(query)
    
    # 3. HYBRID FILTERING
    search_filter = {}
    excluded_genres = ["Documentary", "TV Movie"]
    
    if mode == "SIBLING_DISCOVERY" and ref_genres:
        # GENRE LOCK: Must share at least one genre with the reference
        # We use $in to ensure overlap
        search_filter = {
            "$and": [
                {"genres": {"$in": ref_genres}},
                {"genres": {"$nin": excluded_genres}},
                {"popularity": {"$gt": 1.0}}
            ]
        }
    elif mode in ["PERSON_STRICT", "PERSON_VIBE"]:
        or_clauses = [{"cast_names": name} for name in entities] + [{"director": name} for name in entities]
        search_filter = {"$and": [{"$or": or_clauses}, {"genres": {"$nin": excluded_genres}}]}
    else:
        # Global Discovery Anchors
        anchors = []
        if any(w in q_low for w in ["space", "mars"]): anchors.append("Science Fiction")
        if any(w in q_low for w in ["funny", "laugh", "comedy"]): anchors.append("Comedy")
        if any(w in q_low for w in ["scary", "horror", "scare"]): anchors.append("Horror")
        if "action" in q_low: anchors.append("Action")
        if "jazz" in q_low: anchors.append("Music")
        
        filters = [{"genres": {"$nin": excluded_genres}}, {"popularity": {"$gt": 1.0}}]
        if anchors: filters.append({"genres": {"$in": anchors}})
        search_filter = {"$and": filters}

    # 4. RETRIEVE
    candidates = list(collection.find(
        filter=search_filter,
        sort={"$vector": search_vec.tolist()}, 
        limit=200, # Increased for better thematic diversity in re-ranking
        projection={
            "title": 1, "overview": 1, "genres": 1, 
            "cast_names": 1, "director": 1, "release_date": 1, 
            "vote_average": 1, "popularity": 1, "vote_count": 1
        }
    ))
    
    if not candidates:
        candidates = list(collection.find(sort={"$vector": search_vec.tolist()}, limit=50))

    # 5. DEEP RE-RANK
    exclude_title = reference_title.lower() if reference_title else ""
    pairs = []
    valid_candidates = []
    for doc in candidates:
        if doc.get("title", "").lower() == exclude_title: continue
        pairs.append([query, get_enriched_text(doc)])
        valid_candidates.append(doc)
        
    cross_scores = reranker.predict(pairs)
    
    # 5.5 Identify Vibe Anchor (Top semantic match)
    anchor_genres = []
    if valid_candidates and len(cross_scores) > 0:
        best_idx = np.argmax(cross_scores)
        if cross_scores[best_idx] > 2.0: # Grounding threshold
            anchor_genres = valid_candidates[best_idx].get("genres", [])
    
    scored_results = []
    for i, doc in enumerate(valid_candidates):
        doc_vec = embed(get_enriched_text(doc))
        score = score_movie_v26(query, search_vec, doc_vec, doc, mode, entities, cross_score=cross_scores[i], anchor_genres=anchor_genres)
        
        if score > -0.5:
            scored_results.append({
                "title": doc.get("title"),
                "year": str(doc.get("release_date", "0000"))[:4],
                "score": round(score, 4),
                "mode": mode,
                "popularity": doc.get("popularity", 0),
                "genres": doc.get("genres", []),
                "vote": doc.get("vote_average", 0)
            })
        
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    
    final_output = []
    seen = set()
    franchise_counts = {}
    FRANCHISE_CAP = 2 # Prevent one series from dominating the top results
    
    for r in scored_results:
        title = r["title"]
        base_title = get_base_title(title)
        
        if title not in seen:
            count = franchise_counts.get(base_title, 0)
            if count < FRANCHISE_CAP:
                final_output.append(r)
                seen.add(title)
                franchise_counts[base_title] = count + 1
                REPETITION_LOG[title] = REPETITION_LOG.get(title, 0) + 1
            else:
                # Log skipped sequels for visibility in development
                # print(f"[CAP] Skipping '{title}' (Franchise '{base_title}' cap reached)")
                pass
                
        if len(final_output) >= k:
            break
            
    latency = int((time.time() - start_time) * 1000)
    print(f"[{mode}] Query: '{query}' | Latency: {latency}ms")
    return final_output

# =============================================================================
# TEST SUITE
# =============================================================================

if __name__ == "__main__":
    test_queries = [
        "Ryan Gosling movies",
        "movies directed by Christopher Nolan",
        "A movie about silence and isolation",
        "movies like La La Land",
        "funny war movies",
        "a story about a man who forgets his past",
        "neon colors and futuristic cities",
        "heartbreaking but beautiful dramas",
        "ryan gosling in a quiet role",
        "space adventure",
        "the godfather part ii",
        "jazz music and crime",
        "action movies",
        "comedy movies",
        "Laugh out loud comedy",
        "something that will make me laugh till my stomach hurts",
        "movies that will make me cry",
        "thrilling action movies",
        "scare the shit out of me"
    ]
    
    for q in test_queries:
        print(f"\n--- {q.upper()} ---")
        results = search(q)
        for i, res in enumerate(results, 1):
            print(f"{i}. {res['title']} ({res['year']}) - Score: {res['score']} | Pop: {res['popularity']} | Genres: {res['genres']}")