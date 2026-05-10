import os
import time
import re
import json
import os
import numpy as np
import spacy

from dotenv import load_dotenv
from functools import lru_cache
from astrapy import DataAPIClient
import requests

# Hugging Face Inference API Config
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = "sentence-transformers/all-mpnet-base-v2"
# Using the explicit pipeline URL which is more reliable for some models
HF_API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{MODEL_ID}"

def embed(text: str):
    """
    Fetches embeddings from Hugging Face Inference API.
    Returns a zero-vector on failure to prevent downstream crashes.
    """
    if not HF_TOKEN:
        print("Warning: HF_TOKEN not found in environment.")
        return np.zeros(768)
        
    payload = {"inputs": text, "options": {"wait_for_model": True}}
    try:
        print(f"📡 DEBUG: Fetching embedding from {HF_API_URL}")
        print(f"📡 DEBUG: Token prefix: {HF_TOKEN[:5] if HF_TOKEN else 'NONE'}...")
        
        response = requests.post(
            HF_API_URL,
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json=payload,
            timeout=15
        )
        print(f"📡 DEBUG: HF Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"HF API Error: {response.status_code} - Content: {response.text[:100]}")
            return np.zeros(768)
        
        res = response.json()
        vec = res[0] if isinstance(res, list) and isinstance(res[0], list) else res
        return np.array(vec)
    except Exception as e:
        print(f"HF API connection failed: {e}")
        return np.zeros(768)

# =============================================================================
# ENV + DB
# =============================================================================

load_dotenv()

ASTRA_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

if not ASTRA_TOKEN or not ASTRA_ENDPOINT:
    print("❌ ERROR: Missing Astra DB Environment Variables!")
    print(f"ASTRA_DB_APPLICATION_TOKEN: {'SET' if ASTRA_TOKEN else 'MISSING'}")
    print(f"ASTRA_DB_API_ENDPOINT: {'SET' if ASTRA_ENDPOINT else 'MISSING'}")
    # We don't crash here, we just initialize as None and handle it later
    db = None
    collection = None
else:
    client = DataAPIClient(ASTRA_TOKEN)
    db = client.get_database_by_api_endpoint(ASTRA_ENDPOINT)
    collection = db.get_collection("movies")

# =============================================================================
# MODELS + DATA
# =============================================================================

print("Loading Subtext Core Search Engine...")


nlp = spacy.load("en_core_web_sm")

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

VIBE_RULES = {
    "emotional": {
        "keywords": ["cry", "sad", "bawl", "tearjerker", "devastating", "heartbreaking", "emotional", "beautiful", "romance", "romantic", "love story", "romcom", "rom-com", "rom com"],
        "boost_genres": ["Drama", "Romance"],
        "kill_genres": ["Action", "Adventure", "Horror", "Comedy", "Crime", "Mystery", "Science Fiction"]
    },
    "scary": {
        "keywords": ["terrifying", "scary", "horror", "spooky", "jump scare", "creepy"],
        "boost_genres": ["Horror", "Thriller"],
        "kill_genres": ["Romance", "Comedy", "Family"]
    },
    "funny": {
        "keywords": ["hilarious", "laugh", "funny", "comedy", "comedies", "lmao", "fun", "humor", "feel better", "cheer me up", "romcom", "rom-com", "rom com"],
        "boost_genres": ["Comedy"],
        "kill_genres": ["Horror", "War", "Documentary", "Mystery", "Thriller"]
    },
    "action": {
        "keywords": ["action", "explosions", "badass", "fight", "cool", "thrilling", "intense"],
        "boost_genres": ["Action", "Adventure", "Thriller"],
        "kill_genres": ["Romance", "Documentary", "Family"]
    },
    "investigative": {
        "keywords": ["whodunnit", "whodunit", "detective", "mystery", "solve", "clues", "investigation", "crime", "murder mystery"],
        "boost_genres": ["Mystery", "Crime"],
        "kill_genres": ["Romance", "Musical", "Fantasy"]
    }
}

# =============================================================================
# ILLNESS HARD FILTER
# When a query contains a specific medical condition, candidates are required
# to mention it in their overview or keywords. This prevents The Notebook
# appearing in cancer searches, Interstellar in Alzheimer searches, etc.
# =============================================================================

ILLNESS_KEYWORDS = {
    "cancer": [
        "cancer", "tumor", "tumour", "chemotherapy", "chemo",
        "oncology", "leukemia", "leukaemia", "lymphoma",
        "carcinoma", "malignant", "terminal diagnosis"
    ],
    "alzheimer": ["alzheimer", "dementia", "memory loss", "memory disease"],
    "aids": ["aids", "hiv", "hiv-positive", "immune deficiency"],
    "blind": ["blind", "blindness", "sight loss", "visually impaired", "losing sight"],
    "deaf": ["deaf", "deafness", "hearing loss", "hearing impaired"],
    "paralysis": ["paralys", "paralyz", "quadriplegic", "paraplegic", "wheelchair"],
    "diabetes": ["diabetes", "diabetic", "insulin"],
    "mental illness": ["mental illness", "schizophrenia", "bipolar", "psychosis", "psychiatric"],
}


def detect_illness_intent(query: str):
    q = query.lower()
    for illness, terms in ILLNESS_KEYWORDS.items():
        if any(t in q for t in terms):
            return illness
    return None


def illness_matches_doc(illness_key: str, doc: dict) -> bool:
    terms = ILLNESS_KEYWORDS.get(illness_key, [])
    overview = doc.get("overview", "").lower()
    keywords = " ".join(doc.get("keywords", [])).lower()
    return any(t in (overview + " " + keywords) for t in terms)


# =============================================================================
# CINEMATIC TEXTURE TAGS
# For SIBLING_DISCOVERY, we enrich the anchor text with texture descriptors
# pulled from TMDB keywords. This helps the embedding capture *how* a film
# feels (cold, precise, psychological) not just *what* it's about.
# =============================================================================

TEXTURE_KEYWORD_MAP = {
    # Slow-burn / arthouse
    "slow burn": "slow-burn restrained atmospheric deliberate",
    "atmospheric": "atmospheric immersive mood-driven",
    "surrealism": "surreal dreamlike nonlinear experimental",
    "nonlinear timeline": "nonlinear fragmented time structure",
    "unreliable narrator": "unreliable narrator deceptive perspective",
    # Psychological
    "psychological thriller": "psychological manipulation power games tension",
    "mind game": "mind games psychological tension deception",
    "obsession": "obsessive compulsive fixation intensity",
    # Tone
    "dark comedy": "darkly comic ironic subversive",
    "bittersweet": "bittersweet melancholic hopeful",
    "melancholy": "melancholic longing emotional weight",
    # Style
    "female protagonist": "female-led woman-centred perspective",
    "lgbtq": "queer identity sexuality desire",
    "forbidden love": "forbidden desire repressed longing taboo",
    "class differences": "class tension social hierarchy power",
    "based on novel": "literary adapted source material",
    "twist ending": "twist revelation recontextualisation surprise",
    "period piece": "period historical costume detailed world",
    "foreign language": "foreign language subtitled international arthouse",
}


def build_texture_enrichment(keywords: list) -> str:
    """
    Maps TMDB keywords to cinematic texture descriptors.
    Appended to the anchor text so the embedding captures directorial feel,
    not just plot surface.
    """
    enrichments = []
    kw_lower = [k.lower() for k in (keywords or [])]
    for trigger, descriptor in TEXTURE_KEYWORD_MAP.items():
        if any(trigger in k for k in kw_lower):
            enrichments.append(descriptor)
    return " ".join(enrichments)


# =============================================================================
# UTILS
# =============================================================================

# Local cache removed for the API-based embed function to avoid complexity, 
# but can be re-implemented if needed.


def smart_title(t):
    lowers = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', 'in', 'of'}
    words = t.split()
    return " ".join([w.title() if i == 0 or w.lower() not in lowers else w.lower() for i, w in enumerate(words)])


def get_base_title(title: str):
    base = title.split(":")[0]
    base = re.sub(r'\s+(Part|Chapter|Vol|Volume)\s+[IVX0-9]+.*', '', base, flags=re.IGNORECASE)
    base = re.sub(r'\s+[2-9]$|\s+10$', '', base)
    return base.strip()


def strip_names(text: str):
    doc = nlp(text)
    return " ".join(["CHARACTER" if token.ent_type_ == "PERSON" else token.text for token in doc])


# =============================================================================
# AstraDB-COMPATIBLE TITLE LOOKUP
# AstraDB does not support $regex. We try all casing variants in one $in query.
# =============================================================================

def find_movie_by_title(title: str):
    variants = list(set([
        title,
        title.title(),
        title.capitalize(),
        smart_title(title),
        title.lower(),
        title.upper(),
    ]))
    return collection.find_one(filter={"title": {"$in": variants}})


def find_movie_by_title_with_vector(title: str, proj: dict, year: int = None):
    """
    Fetches anchor doc with $vector included.
    """
    variants = list(set([
        title,
        title.title(),
        title.capitalize(),
        smart_title(title),
        title.lower(),
        title.upper(),
        title.replace(" ", ""),  # roadhouse
        " ".join(re.findall(r'[A-Z][a-z]*|[a-z]+', title.title())) # Road House
    ]))
    
    f = {"title": {"$in": variants}}
    if year:
        f["release_year"] = year

    # First get the canonical title via $in
    stub = collection.find_one(filter=f)
    if not stub:
        return None
        
    # Then fetch full doc with vector using the canonical title
    # We maintain the year filter to ensure we get the right vector
    vec_filter = {"title": stub["title"]}
    if year:
        vec_filter["release_year"] = year

    vec = embed(stub["title"]).tolist()
    results = list(collection.find(
        filter=vec_filter,
        sort={"$vector": vec},
        limit=1,
        projection=proj
    ))
    return results[0] if results else stub


# =============================================================================
# RESOLUTION & INTENT LAYERS
# =============================================================================

def resolve_entities(query):
    q = query.lower()
    entities = []

    words = q.replace(",", " ").replace(".", " ").split()
    for n in [3, 2]:
        for i in range(len(words) - n + 1):
            window = " ".join(words[i:i + n])
            if window in PEOPLE_SET:
                entities.append(window.title())

    if not entities:
        doc = nlp(query)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                entities.append(ent.text)

    if not entities:
        matches = re.findall(r'\b[A-Z][a-z]+\s[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b', query)
        entities.extend(matches)

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


def infer_query_focus(q_low: str, anchor_genres: list) -> str:
    """
    Identifies the primary genre the user cares most about.
    Used to weight genre alignment penalties correctly.
    """
    if "romance" in q_low or "romantic" in q_low or "love story" in q_low:
        return "Romance"
    if "horror" in q_low or "scary" in q_low:
        return "Horror"
    if "comedy" in q_low or "funny" in q_low:
        return "Comedy"
    if "action" in q_low:
        return "Action"
    if "thriller" in q_low:
        return "Thriller"
    # Fall back to anchor's first genre
    if anchor_genres:
        return anchor_genres[0]
    return ""


# =============================================================================
# SCORING HELPERS
# =============================================================================

def cosine_similarity(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def compute_genre_penalty(doc_genres: list, kill_genres: list, boost_genres: list) -> float:
    """
    Kill penalty is intersection-aware: each boost genre cancels one kill.
    50/50 (Comedy+Drama) won't be fully killed by Comedy kill rules
    because Drama is in boost_genres for emotional queries.
    """
    kill_hits = sum(1 for g in doc_genres if g in kill_genres)
    boost_hits = sum(1 for g in doc_genres if g in boost_genres)
    return max(0, kill_hits - boost_hits) * 0.30


def compute_genre_alignment_penalty(anchor_genres: list, doc_genres: list, query_focus: str) -> float:
    """
    Penalises missing genres weighted by importance.
    Missing the primary genre (e.g. Romance in a love story query) = 0.25.
    Missing a secondary genre = 0.08.
    """
    if not anchor_genres:
        return 0.0
    missing = set(anchor_genres) - set(doc_genres)
    penalty = 0.0
    for g in missing:
        if query_focus and g.lower() == query_focus.lower():
            penalty += 0.25
        else:
            penalty += 0.08
    return penalty


# =============================================================================
# VIBE PURGE — ANCHOR-AWARE CLASH DETECTION
#
# The old version applied a blanket 0.60 penalty to any Thriller/Crime doc
# when the anchor was Romance. This caused The Handmaiden to self-penalise
# because it is [Drama, Thriller, Romance] — its own genres fired the purge.
#
# Fix: we check whether the anchor ITSELF has clash genres. If it does,
# we exempt candidates that share those same clash genres (they're not clashes,
# they're part of the film's identity). Only penalise genres that genuinely
# clash with the anchor's identity.
# =============================================================================

CLASH_GENRES = {"Thriller", "Horror", "War", "Science Fiction", "Action", "Crime", "Mystery"}

def compute_vibe_purge_penalty(anchor_genres: list, doc_genres: list) -> float:
    if not anchor_genres:
        return 0.0
    anchor_set = set(anchor_genres)
    is_romance_anchor = "Romance" in anchor_set or "Musical" in anchor_set
    if not is_romance_anchor:
        return 0.0

    # Genres the anchor itself contains — these are identity genres, not clashes
    anchor_clash_identity = anchor_set.intersection(CLASH_GENRES)

    doc_set = set(doc_genres)
    true_clashes = doc_set.intersection(CLASH_GENRES) - anchor_clash_identity

    if not true_clashes:
        return 0.0

    # Music/Musical crossover gets a light nudge instead of a wall
    if "Music" in doc_genres or "Musical" in doc_genres:
        return 0.15

    return 0.60


# =============================================================================
# MAIN SCORING FUNCTION
# =============================================================================

def score_movie(
    query, query_vec, doc_vec, doc, mode, entities,
    anchor_genres=None, anchor_rating=7.0, ref_doc=None, query_focus=""
):
    q_low = query.lower()
    doc_genres = doc.get("genres", [])

    semantic = cosine_similarity(query_vec, doc_vec) if doc_vec is not None else 0.0

    penalty = 0.0
    genre_penalty = 0.0
    vibe_boost = 0.0
    alignment_penalty = 0.0
    mood_penalty = 0.0
    person_penalty = 0.0

    # --- Mood Purity (SIBLING_DISCOVERY) ---
    if mode == "SIBLING_DISCOVERY":
        is_anchor_romance = any(g in {"Romance", "Drama"} for g in (anchor_genres or []))
        if is_anchor_romance:
            doc_overview = doc.get("overview", "").lower()
            clash_kw = ["stoner", "slapstick", "gross-out", "buddy comedy"]
            if any(k in doc_overview for k in clash_kw) or (
                "Comedy" in doc_genres and "Drama" not in doc_genres
            ):
                alignment_penalty += 0.50

    # --- Genre Alignment ---
    if anchor_genres and mode != "PERSON_STRICT":
        alignment_penalty += compute_genre_alignment_penalty(anchor_genres, doc_genres, query_focus)

    # --- Hard Tonal Filter ---
    # If the user explicitly asks for a genre, we penalize non-matching movies heavily.
    tonal_penalty = 0.0
    explicit_genres = ["Comedy", "Horror", "Action", "Romance", "Science Fiction", "Documentary", "Animation", "Thriller", "Crime", "Mystery"]
    for eg in explicit_genres:
        # Check for both singular and plural (e.g., 'comedy' and 'comedies')
        # Also handle shorthands like 'rom com' for both Romance and Comedy
        is_romcom = any(x in q_low for x in ["romcom", "rom-com", "rom com"])
        is_mystery = any(x in q_low for x in ["mystery", "whodunnit", "whodunit", "detective"])
        if (re.search(rf"\b{eg.lower()}\b", q_low) or (eg == "Comedy" and ("comedies" in q_low or is_romcom)) or (eg == "Romance" and is_romcom) or (eg == "Mystery" and is_mystery)) and eg not in doc_genres:
            tonal_penalty += 0.85

    # --- Vibe Rules (GLOBAL queries) ---
    for vibe, rules in VIBE_RULES.items():
        if any(w in q_low for w in rules["keywords"]):
            if any(g in doc_genres for g in rules["boost_genres"]):
                vibe_boost += 0.15
            genre_penalty += compute_genre_penalty(doc_genres, rules["kill_genres"], rules["boost_genres"])

    # --- Vibe Purge (anchor-aware, self-penalty safe) ---
    penalty += compute_vibe_purge_penalty(anchor_genres or [], doc_genres)

    # --- Quality signals ---
    vote_raw = float(doc.get("vote_average", 5.0))
    vote_count = float(doc.get("vote_count", 0))
    quality_score = vote_raw / 10.0
    p_score = min(float(doc.get("popularity", 0)) / 100.0, 1.0)

    # --- Mood Guard ---
    cynical_kw = ["dystopian", "absurdist", "satire", "dark comedy", "surreal", "survival", "experimental"]
    if anchor_genres and ("Romance" in anchor_genres or "Musical" in anchor_genres):
        if any(k in doc.get("overview", "").lower() for k in cynical_kw):
            mood_penalty += 0.50

    # --- Masterpiece Bonus ---
    masterpiece_bonus = 0.05 if (vote_count > 5000 and vote_raw >= 7.8) else 0.0

    # --- Legacy Boost ---
    legacy_boost = np.log10(vote_count) * 0.01 if vote_count > 2000 else 0.0

    # --- Person Alignment (Hard Identity Penalty) ---
    if entities:
        # Waiver: If the user says "like", "similar to", etc., they want the vibe, not just the person.
        similarity_triggers = ["like", "similar to", "reminds me of", "-esque", "vibe"]
        is_similarity_query = any(t in q_low for t in similarity_triggers)

        cast = [str(c).lower() for c in (doc.get("cast_names") or [])]
        director = str(doc.get("director", "")).lower()
        has_match = False
        for ent in entities:
            e_low = ent.lower()
            if e_low in director or any(e_low == c for c in cast):
                has_match = True
                break
        
        if not has_match and not is_similarity_query:
            person_penalty = 0.50  # Heavy sink for missing the requested actor/director

    # --- DNA Boost & Purity ---
    dna_boost = 0.0
    purity_penalty = 0.0
    if anchor_genres:
        anchor_set = set(anchor_genres)
        doc_set = set(doc_genres)
        overlap = len(doc_set.intersection(anchor_set))
        if overlap >= 3:
            dna_boost = 0.02
        elif overlap == 2:
            dna_boost = 0.01
        purity_penalty = len(doc_set - anchor_set) * 0.01

    # --- Keyword Overlap Bonus ---
    # Raised cap to 0.20 for SIBLING_DISCOVERY — keyword overlap is the
    # strongest signal for true thematic siblings (e.g. The Handmaiden's
    # "psychological-thriller", "twist-ending", "class-differences" keywords
    # should heavily boost Park Chan-wook-adjacent films).
    keyword_bonus = 0.0
    kw_overlap = 0
    if ref_doc and ref_doc.get("keywords") and doc.get("keywords"):
        anchor_kw = set(ref_doc["keywords"])
        doc_kw = set(doc.get("keywords", []))
        kw_overlap = len(anchor_kw.intersection(doc_kw))
        cap = 0.20 if mode == "SIBLING_DISCOVERY" else 0.10
        keyword_bonus = min(kw_overlap * 0.02, cap)

    if mode == "SIBLING_DISCOVERY" and kw_overlap == 0:
        purity_penalty += 0.15

    # --- Director Signal ---
    if mode == "SIBLING_DISCOVERY" and ref_doc and doc.get("director") and ref_doc.get("director"):
        if doc["director"] == ref_doc["director"]:
            dna_boost += 0.15

    # --- Final Score ---
    if mode == "SIBLING_DISCOVERY":
        score = (
            (semantic * 2.0)
            + dna_boost
            + keyword_bonus
            + masterpiece_bonus
            - purity_penalty
            + (quality_score * 0.05)
            - penalty
            - mood_penalty
            - alignment_penalty
            - tonal_penalty
        )
    elif mode == "PERSON_STRICT":
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
        score = (
            (semantic * 0.40)
            + (quality_score * 0.30)
            + (p_score * 0.10)
            + (constraint_match * 0.20)
            + legacy_boost
            - penalty
        )
    else:  # GLOBAL / PERSON_VIBE
        score = (
            (semantic * 0.60)
            + (quality_score * 0.25)
            + (p_score * 0.15)
            + legacy_boost
            + vibe_boost
            - genre_penalty
            - person_penalty
            - penalty
        )

    # --- Reason ---
    if mode == "PERSON_STRICT":
        reason = f"Matches your interest in {', '.join(entities)}."
    elif mode == "SIBLING_DISCOVERY":
        if keyword_bonus >= 0.10:
            reason = "Strong thematic sibling — shares key story elements."
        elif dna_boost >= 0.02:
            reason = "Closely matches the genre DNA of your reference film."
        else:
            reason = "Thematic sibling that matches the style of the movie you referenced."
    elif legacy_boost > 0.08:
        reason = "A widely acclaimed film with strong thematic relevance."
    elif semantic > 0.85:
        reason = "Direct semantic match to the core of your query."
    elif vibe_boost > 0:
        reason = "Matches the mood and tone of your search."
    else:
        reason = "Matches the overall vibe of your search."

    breakdown = {
        "semantic": round(semantic, 4),
        "keyword_bonus": round(keyword_bonus, 4),
        "dna_boost": round(dna_boost, 4),
        "vibe_boost": round(vibe_boost, 4),
        "quality": round(quality_score, 4),
        "legacy": round(legacy_boost, 4),
        "total_penalty": round(penalty + genre_penalty + alignment_penalty + mood_penalty + purity_penalty + person_penalty, 4),
    }

    return score, reason, breakdown


# =============================================================================
# SEARCH ENGINE
# =============================================================================

def search(
    query: str,
    k: int = 10,
    min_year: int = None,
    max_year: int = None,
    language: str = None,
    genres: list = None,
    exclude_genres: list = None,
    min_vote: float = None,
    debug: bool = False,
):
    # Per-request state — never share across calls
    repetition_log = {}
    start_time = time.time()
    q_low = query.lower()
    similarity_waiver = any(kw in q_low for kw in ["like", "similar", "vibe", "style", "-esque"])

    # -------------------------------------------------------------------------
    # 1. INTENT RESOLUTION
    # -------------------------------------------------------------------------
    entities = resolve_entities(query)
    mode = classify_entity_intent(query, entities)
    illness_intent = detect_illness_intent(query)

    proj = {
        "title": 1, "overview": 1, "genres": 1, "vote_average": 1,
        "vote_count": 1, "release_year": 1, "poster_path": 1,
        "keywords": 1, "tagline": 1, "cast_names": 1, "director": 1,
        "popularity": 1, "$vector": 1
    }

    # -------------------------------------------------------------------------
    # 2. ANCHOR RESOLUTION
    # -------------------------------------------------------------------------
    search_vec = None
    reference_title = None
    ref_doc = None
    anchor_id = None
    ref_genres = []
    anchor_genres = []
    query_focus = ""

    like_triggers = ["movies like", "movie like", "films like", "film like", "similar to", "reminds me of"]
    suffix_triggers = ["-esque", "esque", " like movies", " like movie", " vibe movies"]

    # 1. Check for explicit prefix triggers
    for trigger in like_triggers:
        if trigger in q_low:
            reference_title = query[q_low.find(trigger) + len(trigger):].strip().strip("'\"")
            mode = "SIBLING_DISCOVERY"
            break

    # 2. Check for genre-based triggers (e.g. "comedies like friday")
    if not reference_title:
        genre_like_match = re.search(r"\b(movies|films|comedies|dramas|thrillers|horror|action|sci-fi|animated|romance|shows)\s+like\s+(.*)", q_low)
        if genre_like_match:
            reference_title = genre_like_match.group(2).strip().strip("'\"")
            mode = "SIBLING_DISCOVERY"

    # 3. Check for suffix triggers
    if not reference_title:
        for s_trig in suffix_triggers:
            if s_trig in q_low:
                reference_title = query[:q_low.find(s_trig)].strip().strip("'\"")
                mode = "SIBLING_DISCOVERY"
                break

    # 4. Auto-detect: is the entire query a movie title?
    if not reference_title:
        auto_ref = find_movie_by_title(query)
        if auto_ref:
            reference_title = auto_ref["title"]
            mode = "SIBLING_DISCOVERY"

    vibe_anchor_text = query

    if reference_title and len(reference_title) >= 2:
        # Detect if a year was provided in the title (e.g. "Babylon 2022")
        anchor_year = None
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', reference_title)
        if year_match:
            anchor_year = int(year_match.group(1))
            # Clean title for better matching (remove the year)
            reference_title = reference_title.replace(str(anchor_year), "").strip()

        # Update proj to include release_year for disambiguation
        proj_with_year = {**proj, "release_year": 1}
        ref_doc = find_movie_by_title_with_vector(reference_title, proj_with_year, year=anchor_year)

        if not ref_doc:
            # Fallback: Range-based Prefix Search (Astra-Safe)
            # This catches "Borat" -> "Borat: Cultural Learnings..."
            # by looking for titles between "Borat" and "Borau".
            prefix = reference_title.strip().title()
            if len(prefix) >= 2:
                # Calculate the "next" string for the range (e.g. "Borat" -> "Borau")
                prefix_next = prefix[:-1] + chr(ord(prefix[-1]) + 1)
                
                f_prefix = {"title": {"$gte": prefix, "$lt": prefix_next}}
                if anchor_year:
                    f_prefix["release_year"] = anchor_year
                
                candidates = list(collection.find(
                    filter=f_prefix,
                    limit=10,
                    projection=proj
                ))
                
                if candidates:
                    # Pick the most popular among those that start with the prefix
                    candidates.sort(key=lambda x: x.get("vote_count", 0), reverse=True)
                    ref_doc = candidates[0]

        if ref_doc:
            anchor_id = ref_doc.get("_id")
            print(f"--- [ANCHOR FOUND] --- {ref_doc['title']} (id={anchor_id})")

            anchor_overview = strip_names(ref_doc.get("overview", ""))
            anchor_genres_str = ", ".join(ref_doc.get("genres", []))
            anchor_keywords = ref_doc.get("keywords", [])

            # TEXTURE ENRICHMENT: append cinematic feel descriptors so the
            # embedding captures directorial texture (psychological, slow-burn,
            # nonlinear) not just plot surface (forbidden love, period setting).
            texture = build_texture_enrichment(anchor_keywords)
            vibe_anchor_text = (
                f"{anchor_overview} "
                f"This movie is a {anchor_genres_str}. "
                f"{texture}"
            ).strip()

            db_vector = ref_doc.get("$vector")
            search_vec = np.array(db_vector) if db_vector else embed(vibe_anchor_text)
            ref_genres = ref_doc.get("genres", [])
    query_focus = infer_query_focus(q_low, anchor_genres)

    if search_vec is None:
        search_vec = embed(query)

    # -------------------------------------------------------------------------
    # 3. FILTERS
    # -------------------------------------------------------------------------
    filters = [{"genres": {"$nin": ["Documentary", "TV Movie"]}}]
    if min_year:
        filters.append({"release_year": {"$gte": min_year}})
    if max_year:
        filters.append({"release_year": {"$lte": max_year}})
    if language:
        filters.append({"original_language": language})
    if min_vote:
        filters.append({"vote_average": {"$gte": min_vote}})
    
    # HARD IDENTITY LOCK: We only filter the DB directly if the user was 
    # explicit (PERSON_STRICT). For VIBE queries, we use the penalty system 
    # in the scorer to allow for discovery even if NER has a false positive.
    if mode == "PERSON_STRICT" and entities and not similarity_waiver:
        p = entities[0]
        filters.append({
            "$or": [
                {"cast_names": {"$in": [p]}},
                {"director": p}
            ]
        })

    search_filter = {"$and": filters} if filters else {}

    # -------------------------------------------------------------------------
    # 4. HYBRID RETRIEVAL
    # -------------------------------------------------------------------------
    # SAFETY: Astra DB crashes on zero vectors. If embedding failed, use Keyword Fallback.
    if np.all(search_vec == 0):
        print("⚠️ Warning: Embedding failed. Falling back to Keyword Search.")
        try:
            # Simple keyword match on title or description as a backup
            keyword_results = list(collection.find(
                filter={"$or": [
                    {"title": {"$regex": f"(?i){query}"}},
                    {"overview": {"$regex": f"(?i){query}"}}
                ]},
                limit=20,
                projection=proj
            ))
            return keyword_results
        except Exception as e:
            print(f"❌ Keyword Fallback Failed: {e}")
            return []

    try:
        # Pool A: raw vector similarity (the vibe)
        pool_a = list(collection.find(
            filter=search_filter,
            sort={"$vector": search_vec.tolist()},
            limit=100,
            projection=proj
        ))

        pool_b = []
        # Pool B: High Quality Sibling DNA (Only for siblings)
        if mode == "SIBLING_DISCOVERY" and ref_doc:
            pool_b = list(collection.find(
                filter={**search_filter, "vote_average": {"$gte": 7.5}},
                sort={"$vector": search_vec.tolist()},
                limit=30,
                projection=proj
            ))
    except Exception as e:
        print(f"❌ Database Retrieval Error: {e}")
        return []

    pool_c = []
    # Pool C: Metadata Keywords (Only for siblings)
    if mode == "SIBLING_DISCOVERY" and ref_doc:
        kw_list = ref_doc.get("keywords", [])[:5]
        if kw_list:
            pool_c = list(collection.find(
                filter={**search_filter, "keywords": {"$in": kw_list}},
                limit=30,
                projection=proj
            ))

    # Pool D: Directorial Heritage
    pool_d = []
    if ref_doc and ref_doc.get("director"):
        pool_d = list(collection.find(
            filter={**search_filter, "director": ref_doc["director"]},
            limit=20,
            projection=proj
        ))

    # Merge & deduplicate by _id
    candidate_map = {doc["_id"]: doc for doc in pool_a + pool_b + pool_c + pool_d}

    # Pre-sort by cosine similarity before scoring (avoids scoring obvious misses)
    s_norm = np.linalg.norm(search_vec)

    def fast_sim(v):
        if v is None:
            return 0.0
        v_arr = np.array(v, dtype=float)
        n = np.linalg.norm(v_arr)
        return float(np.dot(search_vec, v_arr) / (s_norm * n)) if n > 0 else 0.0

    candidates = sorted(
        candidate_map.values(),
        key=lambda x: fast_sim(x.get("$vector")),
        reverse=True
    )

    # -------------------------------------------------------------------------
    # 5. SCORING
    # The anchor itself is EXCLUDED from scoring — it will be pinned to #1
    # separately. This prevents the anchor's own genre mix (e.g. The Handmaiden
    # being [Drama, Thriller, Romance]) from triggering the vibe purge
    # and landing it in 20th place behind its own siblings.
    # -------------------------------------------------------------------------
    scored_results = []
    anchor_rating = ref_doc.get("vote_average", 7.0) if (mode == "SIBLING_DISCOVERY" and ref_doc) else 7.0

    for doc in candidates:
        # Skip anchor — pinned separately below
        if anchor_id and doc.get("_id") == anchor_id:
            continue

        doc_v = doc.get("$vector")
        if doc_v is None:
            continue

        # Illness hard filter
        if illness_intent and not illness_matches_doc(illness_intent, doc):
            continue

        score, reason, breakdown = score_movie(
            vibe_anchor_text, search_vec, doc_v, doc, mode, entities,
            anchor_genres=anchor_genres, anchor_rating=anchor_rating,
            ref_doc=ref_doc, query_focus=query_focus
        )

        if score > -0.5:
            # Normalize for UI (0-99%)
            display_score = score
            if mode == "SIBLING_DISCOVERY":
                display_score = score / 2.0
            
            result = {
                "id": str(doc.get("_id")),
                "title": doc.get("title"),
                "year": doc.get("release_year", 0),
                "score": round(float(min(display_score, 0.99)), 4),
                "ranking_score": round(float(score), 4),
                "reason": reason,
                "mode": mode,
                "genres": doc.get("genres", []),
                "vote": doc.get("vote_average", 0),
                "poster_path": doc.get("poster_path"),
            }
            if debug:
                result["breakdown"] = breakdown
            scored_results.append(result)

    scored_results.sort(key=lambda x: x["score"], reverse=True)

    # -------------------------------------------------------------------------
    # 6. DEDUP + FRANCHISE CAP
    # -------------------------------------------------------------------------
    final_output = []
    seen = set()
    franchise_counts = {}

    for r in scored_results:
        base = get_base_title(r["title"])
        movie_key = (r["title"], r["year"])
        if movie_key not in seen and franchise_counts.get(base, 0) < 2:
            final_output.append(r)
            seen.add(movie_key)
            franchise_counts[base] = franchise_counts.get(base, 0) + 1
            repetition_log[r["title"]] = repetition_log.get(r["title"], 0) + 1
        if len(final_output) >= k:
            break

    # -------------------------------------------------------------------------
    # 7. ANCHOR PIN
    # In SIBLING_DISCOVERY mode the searched movie is always #1.
    # This gives the user confirmation the system understood their query,
    # and avoids the anchor self-penalising due to its own genre mix.
    # We insert it ahead of the ranked siblings and trim to k.
    # -------------------------------------------------------------------------
    if mode == "SIBLING_DISCOVERY" and ref_doc:
        # Check if anchor satisfies user filters (Year, Rating, Language)
        passes = True
        ry = ref_doc.get("release_year", 0)
        va = ref_doc.get("vote_average", 0)
        ol = ref_doc.get("original_language", "")

        if min_year and ry < min_year: passes = False
        if max_year and ry > max_year: passes = False
        if min_vote and va < min_vote: passes = False
        if language and ol != language: passes = False

        if passes:
            anchor_result = {
                "id": str(ref_doc.get("_id")),
                "title": ref_doc.get("title"),
                "year": ry,
                "score": 1.0,  # Sentinel — always #1 (100% match)
                "reason": "This is the movie you searched for.",
                "mode": mode,
                "genres": ref_doc.get("genres", []),
                "vote": va,
                "poster_path": ref_doc.get("poster_path"),
            }
            if debug:
                anchor_result["breakdown"] = {"note": "anchor — pinned to #1, not scored"}

            # Remove anchor if it somehow slipped through dedup, then prepend
            final_output = [r for r in final_output if r["id"] != str(ref_doc.get("_id"))]
            final_output = [anchor_result] + final_output[:k - 1]

    latency = int((time.time() - start_time) * 1000)
    print(
        f"[{mode}] '{query}' | "
        f"illness={illness_intent} | "
        f"anchor={ref_doc['title'] if ref_doc else None} | "
        f"candidates={len(candidates)} | "
        f"scored={len(scored_results)} | "
        f"latency={latency}ms"
    )
    return final_output


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    test_queries = [
        ("the handmaiden", 25),
        ("romance movies about cancer", 25),
        ("la la land", 10),
        ("funny cancer movie", 10),
        ("movies like blue valentine", 10),
    ]

    os.makedirs("paper", exist_ok=True)

    for query, k in test_queries:
        print(f"\n{'='*60}")
        print(f"QUERY: {query}")
        print('='*60)
        results = search(query, k=k, debug=True)
        slug = query.replace(" ", "_")[:30]
        with open(f"paper/results_{slug}.md", "w", encoding="utf-8") as f:
            f.write(f"# Results: {query}\n\n")
            f.write("| Rank | Title | Year | Score | Genres | sem | kw | penalty |\n")
            f.write("|------|-------|------|-------|--------|-----|----|---------|\n")
            for i, r in enumerate(results):
                bd = r.get("breakdown", {})
                f.write(
                    f"| {i+1} | {r['title']} | {r['year']} | {r['score']} "
                    f"| {r.get('genres')} "
                    f"| {bd.get('semantic', 'N/A')} "
                    f"| {bd.get('keyword_bonus', 'N/A')} "
                    f"| {bd.get('total_penalty', 'N/A')} |\n"
                )
        for i, r in enumerate(results):
            bd = r.get("breakdown", {})
            print(f"{i+1:3}. [{r['score']}] {r['title']} ({r['year']}) | {r.get('genres')} | sem={bd.get('semantic', 'N/A')} pen={bd.get('total_penalty', 'N/A')}")