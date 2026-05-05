import os
import json
import re
import torch
from sentence_transformers import SentenceTransformer
from astrapy import DataAPIClient
from dotenv import load_dotenv

load_dotenv()
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

# 1. Load the search model (must match embedding generation settings)
print("Loading high-quality search engine (Jina AI V2 - FP16)...")
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = SentenceTransformer('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True).to(device)
model.half()  # Must match FP16 used during embedding generation
model.max_seq_length = 2048

# 2. Initialize Astra
client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
collection = db.get_collection("movies")

# Load our Local NER Database
PEOPLE_INDEX_PATH = os.path.join(os.path.dirname(__file__), 'people_index.json')
if os.path.exists(PEOPLE_INDEX_PATH):
    with open(PEOPLE_INDEX_PATH, 'r', encoding='utf-8') as f:
        KNOWN_PEOPLE = set(json.load(f))
else:
    KNOWN_PEOPLE = set()

def search(query, filters=None):
    # 1. Local Named Entity Recognition (NER)
    query_lower = query.lower()
    found_people = []
    for person in sorted(KNOWN_PEOPLE, key=len, reverse=True):
        if person in query_lower:
            found_people.append(person)
            query_lower = query_lower.replace(person, "")
            
    # 2. Vectorize the query
    query_vector = model.encode(query).tolist()

    # 3. Build Astra Filter
    astra_filter = {}
    if filters:
        if filters.get("language"):
            astra_filter["original_language"] = filters["language"]
        if filters.get("year_min"):
            astra_filter["release_year"] = {"$gte": int(filters["year_min"])}
        if filters.get("year_max"):
            if "release_year" not in astra_filter:
                astra_filter["release_year"] = {}
            astra_filter["release_year"]["$lte"] = int(filters["year_max"])
        if filters.get("vote_min"):
            astra_filter["vote_average"] = {"$gte": float(filters["vote_min"])}

    # 4. Perform Vector Search in Astra with Filters
    results = list(collection.find(
        astra_filter,
        sort={"$vector": query_vector},
        limit=100,
        include_similarity=True,
        request_timeout_ms=30000
    ))

    final_results = []
    for doc in results:
        vibe_score = doc.get("$similarity", 0)
        title = doc.get("title", "Unknown")
        
        # Title Match Boost: If query matches title exactly, give massive boost
        title_boost = 2.0 if query.lower() == title.lower() else 0.0
        
        reviews = doc.get("reviews", "").lower()
        overview = doc.get("overview", "").lower()
        
        # Person Boost (NER)
        person_boost = 0.0
        for person in found_people:
            if person in reviews or person in overview:
                person_boost = 0.4
                break
        
        final_score = (vibe_score * 0.85) + person_boost + title_boost
        
        final_results.append({
            "title": title,
            "poster_path": doc.get("poster_path"),
            "score": final_score,
            "vibe_pct": vibe_score * 100,
            "id": doc.get("_id")
        })

    # Sort by final score
    final_results.sort(key=lambda x: x['score'], reverse=True)

    if __name__ == "__main__":
        print(f"\n--- Astra Results for: '{query}' ---")
        for i, res in enumerate(final_results[:10]):
            print(f"{i+1}. {res['title']} (Score: {res['score']:.3f} | Vibe: {res['vibe_pct']:.1f}%)")
    
    return final_results[:10]

if __name__ == "__main__":
    while True:
        user_query = input("\nEnter a vibe (or 'exit'): ")
        if user_query.lower() == 'exit': break
        search(user_query)
