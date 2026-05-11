import os
import time
import re
import json
import math
import os
import numpy as np
import spacy

from dotenv import load_dotenv
from functools import lru_cache
from astrapy import DataAPIClient
import requests

from sentence_transformers import SentenceTransformer

# Hugging Face Configuration
MODEL_ID = "jinaai/jina-embeddings-v2-base-en"

_model = None

def get_model():
    global _model
    if _model is None:
        print(f"📡 Loading Local ML Model: {MODEL_ID}...")
        _model = SentenceTransformer(MODEL_ID, trust_remote_code=True)
        print("✅ Model loaded successfully.")
    return _model


def embed(text: str):
    try:
        model = get_model()
        input_text = text[:8000]
        vec = model.encode(input_text)
        return np.array(vec)
    except Exception as e:
        print(f"❌ Local Inference failed: {e}")
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
        "keywords": ["cry", "sad", "bawl", "tearjerker", "devastating", "heartbreaking", "emotional", "beautiful", "romance", "romantic", "love story", "romcom", "rom-com", "rom com", "feels", "tragic", "downward spiral"],
        "boost_genres": ["Drama", "Romance"],
        "kill_genres": ["Action", "Adventure", "Horror", "Comedy", "Crime", "Mystery", "Science Fiction", "Animation", "Family"]
    },
    "scary": {
        "keywords": ["terrifying", "scary", "horror", "spooky", "jump scare", "creepy", "nightmare"],
        "boost_genres": ["Horror", "Thriller"],
        "kill_genres": ["Romance", "Comedy", "Family", "Animation"]
    },
    "funny": {
        "keywords": ["hilarious", "laugh", "funny", "comedy", "comedies", "lmao", "fun", "humor", "feel better", "cheer me up", "romcom", "rom-com", "rom com", "lol", "slaps", "unhinged", "dark humor", "chaotic"],
        "boost_genres": ["Comedy"],
        "kill_genres": ["Horror", "War", "Documentary", "Mystery", "Thriller"]
    },
    "action": {
        "keywords": ["action", "explosions", "badass", "fight", "cool", "thrilling", "intense", "adrenaline", "hype"],
        "boost_genres": ["Action", "Adventure", "Thriller"],
        "kill_genres": ["Romance", "Documentary", "Family", "Animation"]
    },
    "investigative": {
        "keywords": ["whodunnit", "whodunit", "detective", "mystery", "solve", "clues", "investigation", "crime", "murder mystery"],
        "boost_genres": ["Mystery", "Crime"],
        "kill_genres": ["Romance", "Musical", "Fantasy", "Animation", "Family"]
    },
    "wholesome": {
        "keywords": ["wholesome", "warm", "heartwarming", "feel-good", "sweet", "comfort", "genuine", "pure", "pure-hearted", "believe in people", "green flag"],
        "boost_genres": ["Family", "Comedy", "Romance"],
        "kill_genres": ["Horror", "War", "Crime", "Thriller"]
    },
    "cozy": {
        "keywords": ["cozy", "sunday afternoon", "comforting", "peaceful", "gentle", "soft", "vibes", "chill", "relaxing", "lowkey", "comfort movie"],
        "boost_genres": ["Animation", "Family", "Comedy", "Romance"],
        "kill_genres": ["Action", "Horror", "Thriller", "War", "Science Fiction"]
    },
    "existential": {
        "keywords": ["existential", "meaning of life", "stare at the ceiling", "philosophical", "deep", "thought-provoking", "crisis", "melancholy", "melancholic", "rent free"],
        "boost_genres": ["Drama", "Science Fiction"],
        "kill_genres": ["Action", "Comedy", "Family", "Animation"]
    },
    "glamorous": {
        "keywords": ["glamorous", "glamour", "main character", "fashion", "fame", "rich", "extravagant", "chic", "aesthetic", "glitzy", "slaps", "era", "self-destructive", "downward spiral", "messy"],
        "boost_genres": ["Drama", "Music", "Comedy"],
        # FIX: Animation and Family added — prevents KPop Demon Hunters / Cars type mismatches
        "kill_genres": ["Action", "Horror", "War", "Animation", "Family"]
    },
    "nostalgic": {
        "keywords": ["nostalgic", "nostalgia", "throwback", "memory", "growing up", "retro", "vintage", "childhood", "bittersweet", "core"],
        "boost_genres": ["History", "Family", "Drama"],
        "kill_genres": []
    },
    # NEW: bittersweet endings / complicated emotions
    "bittersweet_ending": {
        "keywords": ["ended something", "quiet relief", "relief mixed", "ambivalent", "complicated feelings", "not sure how to feel", "mixed feelings", "letting go", "outgrown", "moving on"],
        "boost_genres": ["Drama", "Romance"],
        "kill_genres": ["Horror", "Action", "Comedy", "Family", "Animation", "Science Fiction"]
    },
    # NEW: watching someone fall apart
    "unraveling": {
        "keywords": ["unravel", "fall apart", "spiral", "deteriorate", "losing it", "breaking down", "can't look away", "self-destruct", "coming undone"],
        "boost_genres": ["Drama", "Thriller"],
        "kill_genres": ["Family", "Animation", "Comedy", "Romance"]
    },
    # NEW: sensory — sun-scorched landscapes
    "sun_scorched": {
        "keywords": ["dusty", "sun-bleached", "middle of nowhere", "middle-of-nowhere", "heat you can", "scorching", "desert", "barren", "arid", "sun baked", "sun-baked"],
        "boost_genres": ["Western", "Drama", "Thriller", "Crime"],
        "kill_genres": ["Family", "Animation", "Comedy", "Romance", "Science Fiction", "Horror"]
    },
    # NEW: sensory — rainy neon city noir
    "gritty_urban": {
        "keywords": ["rainy city", "neon reflections", "wet pavement", "neon lights", "night city", "urban alienation", "nobody's where", "urban drift", "city at night"],
        "boost_genres": ["Drama", "Crime", "Thriller"],
        "kill_genres": ["Family", "Animation", "Romance", "Comedy", "Western"]
    },
    # NEW: paranoid / everyone is lying
    "paranoid": {
        "keywords": ["paranoid", "everyone might be lying", "conspiracy", "can't trust anyone", "surveillance", "deceived", "manipulation", "gaslit"],
        "boost_genres": ["Thriller", "Crime", "Mystery", "Drama"],
        "kill_genres": ["Family", "Animation", "Comedy", "Romance"]
    },
    # NEW: mean wit / dark satire
    "dark_wit": {
        "keywords": ["funny but mean", "wit that makes you wince", "mean funny", "dark satire", "sharp wit", "caustic", "biting comedy", "wince", "sardonic"],
        "boost_genres": ["Comedy", "Drama", "Thriller"],
        "kill_genres": ["Family", "Animation", "Horror", "War"]
    },
    # NEW: analog / unhurried / no irony
    "analog_unhurried": {
        "keywords": ["unhurried", "analog", "no irony", "different time", "made in a different", "slow cinema", "quiet film", "deliberate pace", "restrained"],
        "boost_genres": ["Drama"],
        "kill_genres": ["Action", "Science Fiction", "Horror", "Animation", "Comedy"]
    },
}

# =============================================================================
# SENSORY QUERY EXPANSION
# For queries that are primarily aesthetic/sensory, we expand the text before
# embedding so the vector captures cinematic texture rather than literal words.
# "dusty sun-bleached" by itself doesn't sit near film embeddings — adding
# film-vocabulary context anchors it in the right part of the space.
# =============================================================================

SENSORY_EXPANSIONS = {
    "dusty":            "neo-western slow deliberate arid landscape minimalist isolation",
    "sun-bleached":     "western arthouse heat haze desolate wide open slow burn",
    "middle of nowhere":"western road movie isolation quiet desolate slow",
    "neon":             "urban noir nighttime alienation rain cinematic atmospheric",
    "wet pavement":     "noir atmospheric urban loneliness cinematic drifting",
    "rainy city":       "noir atmospheric urban nighttime drifting alienation",
    "rainy":            "atmospheric melancholic city night slow deliberate",
    "analog":           "unhurried classical restrained period texture no irony sincere",
    "unhurried":        "slow cinema deliberate arthouse quiet restrained",
    "no irony":         "sincere earnest classical unironic human",
    "unravel":          "psychological deterioration obsession disintegration intense",
    "fall apart":       "psychological deterioration slow disintegration character study",
    "paranoid":         "conspiracy surveillance deception institutional mistrust",
    "glamorous":        "stylish extravagant decadent fame ambition self-destruction",
    "self-destructive": "excess ambition unraveling tragic glamour downfall",
}

def expand_query_for_embedding(query: str) -> str:
    """
    Appends film-vocabulary context for sensory/aesthetic queries so that
    the embedding lands closer to relevant films rather than literal word matches.
    """
    q_low = query.lower()
    expansions = []
    for trigger, expansion in SENSORY_EXPANSIONS.items():
        if trigger in q_low:
            expansions.append(expansion)
    if expansions:
        # Deduplicate expansion words
        seen = set()
        deduped = []
        for chunk in expansions:
            for word in chunk.split():
                if word not in seen:
                    seen.add(word)
                    deduped.append(word)
        return query + " " + " ".join(deduped)
    return query


# =============================================================================
# ILLNESS HARD FILTER
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


def detect_negation(query: str, keyword: str) -> bool:
    q = query.lower()
    k = keyword.lower()
    negators = ["no ", "not ", "without ", "none ", "never ", "stop ", "zero "]
    for n in negators:
        # Use s? to catch plurals like 'rom-coms' or 'thrillers'
        if re.search(rf"\b{n}{k}s?\b", q):
            return True
    return False


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
# =============================================================================

TEXTURE_KEYWORD_MAP = {
    "slow burn": "slow-burn restrained atmospheric deliberate",
    "atmospheric": "atmospheric immersive mood-driven",
    "surrealism": "surreal dreamlike nonlinear experimental",
    "nonlinear timeline": "nonlinear fragmented time structure",
    "unreliable narrator": "unreliable narrator deceptive perspective",
    "psychological thriller": "psychological manipulation power games tension",
    "mind game": "mind games psychological tension deception",
    "obsession": "obsessive compulsive fixation intensity",
    "dark comedy": "darkly comic ironic subversive",
    "bittersweet": "bittersweet melancholic hopeful ambivalent",
    "melancholy": "melancholic longing emotional weight",
    "wholesome": "heartwarming wholesome genuine warm",
    "cozy": "cozy comforting peaceful low-key",
    "nostalgic": "nostalgic sentimental bittersweet childhood",
    "glamorous": "glamorous stylish chic extravagant",
    "existential": "existential philosophical deep reflective",
    "female protagonist": "female-led woman-centred perspective",
    "lgbtq": "queer identity sexuality desire",
    "forbidden love": "forbidden desire repressed longing taboo",
    "class differences": "class tension social hierarchy power",
    "based on novel": "literary adapted source material",
    "twist ending": "twist revelation recontextualisation surprise",
    "period piece": "period historical costume detailed world",
    "foreign language": "foreign language subtitled international arthouse",
    # NEW texture tags
    "paranoia": "paranoid institutional distrust surveillance conspiracy",
    "ambivalent": "ambivalent complicated mixed emotion unresolved",
    "psychological deterioration": "unraveling disintegration obsession breakdown",
    "isolation": "isolation confined space solitude sparse",
    "sun": "arid heat desolate sun-scorched landscape",
    "rain": "rain atmospheric wet moody urban",
}


def build_texture_enrichment(keywords: list) -> str:
    enrichments = []
    kw_lower = [k.lower() for k in (keywords or [])]
    for trigger, descriptor in TEXTURE_KEYWORD_MAP.items():
        if any(trigger in k for k in kw_lower):
            enrichments.append(descriptor)
    return " ".join(enrichments)


# =============================================================================
# UTILS
# =============================================================================

def normalize_score(raw_score: float, mode: str) -> float:
    """
    Sigmoid normalization — preserves ranking order and avoids ceiling collapse.
    Replaces the old min(display_score, 1.0) hard cap which made genuinely
    different scores (0.95 vs 0.72) both appear as 1.0.
    Centered at 0.5, steepness 5 — gives ~0.95 at the top, ~0.50 at midpoint.
    """
    if mode == "SIBLING_DISCOVERY":
        raw_score = raw_score / 2.5
    else:
        raw_score = raw_score / 1.05
    return round(1 / (1 + math.exp(-5 * (raw_score - 0.5))), 4)


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
    variants = list(set([
        title,
        title.title(),
        title.capitalize(),
        smart_title(title),
        title.lower(),
        title.upper(),
        title.replace(" ", ""),
        " ".join(re.findall(r'[A-Z][a-z]*|[a-z]+', title.title()))
    ]))

    f = {"title": {"$in": variants}}
    if year:
        f["release_year"] = year

    proj_with_vec = {**proj, "$vector": 1, "vote_count": 1}
    candidates = list(collection.find(
        filter=f,
        projection=proj_with_vec,
        limit=5
    ))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x.get("vote_count", 0), reverse=True)
    doc = candidates[0]

    if not doc:
        return None

    if "$vector" in doc and doc["$vector"]:
        if np.all(np.array(doc["$vector"]) == 0):
            del doc["$vector"]

    if "$vector" not in doc:
        print(f"📡 Generating missing vector for: {doc['title']}")
        vec = embed(doc["title"] + " " + doc.get("overview", ""))
        if vec is not None and not np.all(vec == 0):
            doc["$vector"] = vec.tolist()

    return doc


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
    kill_hits = sum(1 for g in doc_genres if g in kill_genres)
    boost_hits = sum(1 for g in doc_genres if g in boost_genres)
    return max(0, kill_hits - boost_hits) * 0.50


def compute_genre_alignment_penalty(anchor_genres: list, doc_genres: list, query_focus: str) -> float:
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


CLASH_GENRES = {"Thriller", "Horror", "War", "Science Fiction", "Action", "Crime", "Mystery"}

def compute_vibe_purge_penalty(anchor_genres: list, doc_genres: list) -> float:
    if not anchor_genres:
        return 0.0
    anchor_set = set(anchor_genres)
    is_romance_anchor = "Romance" in anchor_set or "Musical" in anchor_set
    if not is_romance_anchor:
        return 0.0

    anchor_clash_identity = anchor_set.intersection(CLASH_GENRES)
    doc_set = set(doc_genres)
    true_clashes = doc_set.intersection(CLASH_GENRES) - anchor_clash_identity

    if not true_clashes:
        return 0.0

    if "Music" in doc_genres or "Musical" in doc_genres:
        return 0.15

    return 0.60


def compute_multi_vibe_bonus(q_low: str, doc_genres: list) -> float:
    """
    Rewards films that satisfy multiple vibe dimensions simultaneously.
    A film matching 'glamorous + self-destructive + great soundtrack' should
    rank above one that only matches 'glamorous'.
    Adds 0.10 per additional vibe matched beyond the first (capped at 0.30).
    """
    matched_count = 0
    for vibe, rules in VIBE_RULES.items():
        matched_keywords = [w for w in rules["keywords"] if w in q_low]
        if not matched_keywords:
            continue
        all_negated = all(detect_negation(q_low, w) for w in matched_keywords)
        if all_negated:
            continue
        if any(g in doc_genres for g in rules["boost_genres"]):
            matched_count += 1
    if matched_count >= 2:
        return min(0.10 * (matched_count - 1), 0.30)
    return 0.0


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
    multi_vibe_bonus = 0.0

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
    tonal_penalty = 0.0
    explicit_genres = ["Comedy", "Horror", "Action", "Romance", "Science Fiction", "Documentary", "Animation", "Thriller", "Crime", "Mystery"]
    for eg in explicit_genres:
        is_romcom = any(x in q_low for x in ["romcom", "rom-com", "rom com"])
        is_mystery = any(x in q_low for x in ["mystery", "whodunnit", "whodunit", "detective"])
        
        # POSITIVE INTENT: user wants this genre
        if (re.search(rf"\b{eg.lower()}s?\b", q_low) or (eg == "Comedy" and ("comedies" in q_low or is_romcom)) or (eg == "Romance" and is_romcom) or (eg == "Mystery" and is_mystery)) and eg not in doc_genres:
            # Waiver: don't penalize if the intent was actually negated
            if not detect_negation(q_low, eg.lower()) and not (eg == "Comedy" and detect_negation(q_low, "comedy")):
                tonal_penalty += 0.85

        # NEGATIVE INTENT: user explicitly forbids a genre/style
        if detect_negation(q_low, eg.lower()) or (eg == "Comedy" and detect_negation(q_low, "comedy")):
            if eg in doc_genres:
                penalty += 0.50
                # Special Case: 'No Rom-com' implies blocking both Romance and Comedy
                if is_romcom and detect_negation(q_low, "rom-com") and "Romance" in doc_genres and "Comedy" in doc_genres:
                    penalty += 0.40 # Additional penalty for rom-com specifically

    # --- Vibe Rules + Multi-vibe bonus ---
    for vibe, rules in VIBE_RULES.items():
        matched_keywords = [w for w in rules["keywords"] if w in q_low]
        if matched_keywords:
            all_negated = all(detect_negation(q_low, w) for w in matched_keywords)
            if not all_negated:
                if any(g in doc_genres for g in rules["boost_genres"]):
                    vibe_boost += 0.15
                genre_penalty += compute_genre_penalty(doc_genres, rules["kill_genres"], rules["boost_genres"])

    # Multi-vibe intersection bonus — rewards matching all dimensions of a compound vibe query
    multi_vibe_bonus = compute_multi_vibe_bonus(q_low, doc_genres)
    vibe_boost += multi_vibe_bonus

    # --- Vibe Purge (anchor-aware, self-penalty safe) ---
    penalty += compute_vibe_purge_penalty(anchor_genres or [], doc_genres)

    # --- Quality signals ---
    vote_raw = float(doc.get("vote_average", 5.0))
    vote_count = float(doc.get("vote_count", 0))
    quality_score = vote_raw / 10.0

    p_raw = float(doc.get("popularity", 0))
    p_score = min(np.log1p(p_raw) / 8.0, 1.0)

    # --- Mood Guard ---
    cynical_kw = ["dystopian", "absurdist", "satire", "dark comedy", "surreal", "survival", "experimental"]
    if anchor_genres and ("Romance" in anchor_genres or "Musical" in anchor_genres):
        if any(k in doc.get("overview", "").lower() for k in cynical_kw):
            mood_penalty += 0.50

    # SADNESS GUARD: Pure comedies without Drama/Thriller get penalized for dark/existential queries
    sad_triggers = ["sad", "existential", "melancholy", "depressing", "tragic", "stare at the ceiling", "unravel", "fall apart"]
    if any(t in q_low for t in sad_triggers):
        if "Comedy" in doc_genres and "Drama" not in doc_genres and "Thriller" not in doc_genres:
            mood_penalty += 0.40

    # --- Masterpiece Bonus ---
    masterpiece_bonus = 0.05 if (vote_count > 5000 and vote_raw >= 7.8) else 0.0

    # --- Legacy Boost ---
    legacy_boost = np.log10(vote_count) * 0.01 if vote_count > 2000 else 0.0

    # --- Person Alignment ---
    if entities:
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
            person_penalty = 0.50

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
            + vibe_boost
            - genre_penalty
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
            (semantic * 0.90)
            + (quality_score * 0.07)
            + (p_score * 0.03)
            + legacy_boost
            + vibe_boost
            - genre_penalty
            - person_penalty
            - penalty
            - mood_penalty
        )

    # --- Reason ---
    matched_vibes = []
    for v_name, rules in VIBE_RULES.items():
        matched_keywords = [w for w in rules["keywords"] if w in q_low]
        # FIX: keyword gate — only append vibe if keywords actually matched in query
        if not matched_keywords:
            continue
        if all(detect_negation(q_low, w) for w in matched_keywords):
            continue
        if any(g in doc_genres for g in rules["boost_genres"]):
            matched_vibes.append(v_name)

    if mode == "PERSON_STRICT":
        reason = f"Matches your interest in {', '.join(entities)}."
    elif mode == "SIBLING_DISCOVERY":
        if keyword_bonus >= 0.10:
            reason = "Strong thematic sibling — shares key story elements."
        elif dna_boost >= 0.02:
            reason = "Closely matches the genre DNA of your reference film."
        else:
            reason = "Thematic sibling that matches the style of the movie you referenced."
    elif matched_vibes:
        vibe_labels = {
            "emotional": "emotional",
            "scary": "scary",
            "funny": "funny",
            "action": "high-octane",
            "investigative": "investigative",
            "wholesome": "wholesome",
            "cozy": "cozy",
            "existential": "existential",
            "glamorous": "glamorous",
            "nostalgic": "nostalgic",
            "bittersweet_ending": "bittersweet",
            "unraveling": "emotionally intense",
            "sun_scorched": "sun-scorched and desolate",
            "gritty_urban": "urban and atmospheric",
            "paranoid": "paranoid",
            "dark_wit": "sharp and darkly funny",
            "analog_unhurried": "unhurried and analog",
        }
        labels = [vibe_labels.get(v, v) for v in matched_vibes]
        if len(labels) > 1:
            reason = f"Matches the {', '.join(labels[:-1])} and {labels[-1]} vibes of your search."
        else:
            reason = f"Captured the {labels[0]} essence of your request."
    elif semantic > 0.85:
        reason = "Direct semantic match to the core of your query."
    else:
        reason = "Matches the overall vibe of your search."

    breakdown = {
        "semantic": round(semantic, 4),
        "keyword_bonus": round(keyword_bonus, 4),
        "dna_boost": round(dna_boost, 4),
        "vibe_boost": round(vibe_boost, 4),
        "multi_vibe_bonus": round(multi_vibe_bonus, 4),
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
    q_low = query.lower()

    # --- AUTO-FILTER PARSING ---
    if not min_year and not max_year:
        decade_match = re.search(r'\b(19|20)?(\d0)s\b', q_low)
        if decade_match:
            century = decade_match.group(1) or "19"
            decade = decade_match.group(2)
            min_year = int(f"{century}{decade}")
            max_year = min_year + 9
            print(f"📅 [AUTO-FILTER] Detected decade: {min_year}-{max_year}")
        elif "1900s" in q_low:
            min_year, max_year = 1900, 1909
        elif any(w in q_low for w in ["old movies", "classic movies", "vintage movies"]):
            max_year = 1980
            print(f"📅 [AUTO-FILTER] Detected 'old' intent: max_year=1980")

    if not language:
        lang_map = {
            "hindi": "hi", "korean": "ko", "japanese": "ja",
            "french": "fr", "spanish": "es", "german": "de",
            "italian": "it", "chinese": "zh", "tamil": "ta",
            "telugu": "te", "malayalam": "ml", "kannada": "kn",
            "arabic": "ar", "russian": "ru"
        }
        for lang_name, lang_code in lang_map.items():
            if f"{lang_name} movies" in q_low or f"{lang_name} film" in q_low or q_low.startswith(f"{lang_name} "):
                language = lang_code
                print(f"🌐 [AUTO-FILTER] Detected language: {lang_name} ({lang_code})")
                break

    repetition_log = {}
    start_time = time.time()

    vibe_match = None
    for v_name, rules in VIBE_RULES.items():
        if any(w in q_low for w in rules["keywords"]):
            vibe_match = v_name
            break
    if vibe_match:
        print(f"🎭 [VIBE DETECTED] Query has {vibe_match} tone. Applying constraints.")

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

    for trigger in like_triggers:
        if trigger in q_low:
            reference_title = query[q_low.find(trigger) + len(trigger):].strip().strip("'\"")
            mode = "SIBLING_DISCOVERY"
            break

    if not reference_title:
        genre_like_match = re.search(r"\b(movies|films|comedies|dramas|thrillers|horror|action|sci-fi|animated|romance|shows)\s+like\s+(.*)", q_low)
        if genre_like_match:
            reference_title = genre_like_match.group(2).strip().strip("'\"")
            mode = "SIBLING_DISCOVERY"

    if not reference_title:
        for s_trig in suffix_triggers:
            if s_trig in q_low:
                reference_title = query[:q_low.find(s_trig)].strip().strip("'\"")
                mode = "SIBLING_DISCOVERY"
                break

    if not reference_title:
        auto_ref = find_movie_by_title(query)
        if auto_ref:
            reference_title = auto_ref["title"]
            mode = "SIBLING_DISCOVERY"

    # FIX: Apply sensory query expansion before embedding for GLOBAL queries.
    # SIBLING_DISCOVERY uses anchor text enrichment instead, so we skip there.
    vibe_anchor_text = query
    embedding_query = expand_query_for_embedding(query) if mode == "GLOBAL" else query

    if reference_title and len(reference_title) >= 2:
        anchor_year = None
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', reference_title)
        if year_match:
            anchor_year = int(year_match.group(1))
            reference_title = reference_title.replace(str(anchor_year), "").strip()

        proj_with_year = {**proj, "release_year": 1}
        ref_doc = find_movie_by_title_with_vector(reference_title, proj_with_year, year=anchor_year)

        if not ref_doc:
            prefix = reference_title.strip().title()
            if len(prefix) >= 2:
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
                    candidates.sort(key=lambda x: x.get("vote_count", 0), reverse=True)
                    ref_doc = candidates[0]

        if ref_doc:
            anchor_id = ref_doc.get("_id")
            print(f"--- [ANCHOR FOUND] --- {ref_doc['title']} ({ref_doc.get('release_year', 'N/A')}) | id={anchor_id} | votes={ref_doc.get('vote_count', 0)}")

            anchor_overview = strip_names(ref_doc.get("overview", ""))
            anchor_genres_str = ", ".join(ref_doc.get("genres", []))
            anchor_keywords = ref_doc.get("keywords", [])
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
        # Use expanded query for embedding (sensory expansions applied here)
        search_vec = embed(embedding_query)

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
    if np.all(search_vec == 0):
        print("⚠️ Warning: Embedding failed. Falling back to Keyword Search.")
        try:
            keyword_results = list(collection.find(
                filter={},
                limit=10,
                projection=proj
            ))
            return keyword_results
        except Exception as e:
            print(f"❌ Keyword Fallback Failed: {e}")
            return []

    try:
        pool_a = list(collection.find(
            filter=search_filter,
            sort={"$vector": search_vec.tolist()},
            limit=100,
            projection=proj
        ))

        pool_b = []
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
    if mode == "SIBLING_DISCOVERY" and ref_doc:
        kw_list = ref_doc.get("keywords", [])[:5]
        if kw_list:
            pool_c = list(collection.find(
                filter={**search_filter, "keywords": {"$in": kw_list}},
                limit=30,
                projection=proj
            ))

    pool_d = []
    if ref_doc and ref_doc.get("director"):
        pool_d = list(collection.find(
            filter={**search_filter, "director": ref_doc["director"]},
            limit=20,
            projection=proj
        ))

    candidate_map = {doc["_id"]: doc for doc in pool_a + pool_b + pool_c + pool_d}

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
    # -------------------------------------------------------------------------
    scored_results = []
    anchor_rating = ref_doc.get("vote_average", 7.0) if (mode == "SIBLING_DISCOVERY" and ref_doc) else 7.0

    for doc in candidates:
        if anchor_id and doc.get("_id") == anchor_id:
            continue

        doc_v = doc.get("$vector")
        if doc_v is None:
            continue

        if illness_intent and not illness_matches_doc(illness_intent, doc):
            continue

        score, reason, breakdown = score_movie(
            vibe_anchor_text, search_vec, doc_v, doc, mode, entities,
            anchor_genres=anchor_genres, anchor_rating=anchor_rating,
            ref_doc=ref_doc, query_focus=query_focus
        )

        if score > 0.1:
            display_score = normalize_score(score, mode)

            result = {
                "id": str(doc.get("_id")),
                "title": doc.get("title"),
                "year": doc.get("release_year", 0),
                "score": display_score,
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
    # 6. DEDUP + FRANCHISE CAP + GENRE DIVERSITY
    # -------------------------------------------------------------------------
    final_output = []
    seen = set()
    franchise_counts = {}
    # FIX: track genre fingerprint saturation to prevent About Time / Inside Out
    # appearing across 5 different prompts — applies a soft re-rank nudge when
    # the same genre combo is already well-represented in the output.
    genre_representation = {}

    for r in scored_results:
        base = get_base_title(r["title"])
        movie_key = (r["title"], r["year"])
        genre_key = tuple(sorted(r["genres"]))

        # Soft diversity nudge — don't hard-block, just reduce score slightly
        genre_saturation = genre_representation.get(genre_key, 0)
        if genre_saturation >= 2:
            r["score"] = round(r["score"] * 0.82, 4)

        if movie_key not in seen and franchise_counts.get(base, 0) < 2:
            final_output.append(r)
            seen.add(movie_key)
            franchise_counts[base] = franchise_counts.get(base, 0) + 1
            genre_representation[genre_key] = genre_saturation + 1
            repetition_log[r["title"]] = repetition_log.get(r["title"], 0) + 1

        if len(final_output) >= k:
            break

    # -------------------------------------------------------------------------
    # 7. ANCHOR PIN (SIBLING_DISCOVERY)
    # -------------------------------------------------------------------------
    if mode == "SIBLING_DISCOVERY" and ref_doc:
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
                "score": 1.0,
                "reason": "This is the movie you searched for.",
                "mode": mode,
                "genres": ref_doc.get("genres", []),
                "vote": va,
                "poster_path": ref_doc.get("poster_path"),
            }
            if debug:
                anchor_result["breakdown"] = {"note": "anchor — pinned to #1, not scored"}

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
        # New vibe test queries from evaluation
        ("main character energy glamorous self-destructive great soundtrack", 10),
        ("dusty sun-bleached middle of nowhere heat", 10),
        ("rainy city at night neon reflections wet pavement", 10),
        ("watching someone slowly unravel uncomfortable", 10),
        ("the 70s but paranoid everyone might be lying", 10),
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
            f.write("| Rank | Title | Year | Score | Genres | sem | kw | multi_vibe | penalty |\n")
            f.write("|------|-------|------|-------|--------|-----|----|----|--------|\n")
            for i, r in enumerate(results):
                bd = r.get("breakdown", {})
                f.write(
                    f"| {i+1} | {r['title']} | {r['year']} | {r['score']} "
                    f"| {r.get('genres')} "
                    f"| {bd.get('semantic', 'N/A')} "
                    f"| {bd.get('keyword_bonus', 'N/A')} "
                    f"| {bd.get('multi_vibe_bonus', 'N/A')} "
                    f"| {bd.get('total_penalty', 'N/A')} |\n"
                )
        for i, r in enumerate(results):
            bd = r.get("breakdown", {})
            print(f"{i+1:3}. [{r['score']}] {r['title']} ({r['year']}) | {r.get('genres')} | sem={bd.get('semantic', 'N/A')} mvb={bd.get('multi_vibe_bonus', 'N/A')} pen={bd.get('total_penalty', 'N/A')}")