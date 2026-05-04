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

# 1. Load the search model
print("Loading high-quality search engine (Jina AI V2)...")
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = SentenceTransformer('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True).to(device)

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

def search(query):
    # 1. Local Named Entity Recognition (NER)
    query_lower = query.lower()
    found_people = []
    for person in sorted(KNOWN_PEOPLE, key=len, reverse=True):
        if person in query_lower:
            found_people.append(person)
            query_lower = query_lower.replace(person, "")
            
    # 2. Vectorize the query
    query_vector = model.encode(query).tolist()

    # 3. Perform Vector Search in Astra
    # We retrieve more results to allow for hybrid re-ranking
    results = collection.vector_find(
        vector=query_vector,
        limit=20,
        include_similarity=True
    )

    final_results = []
    for doc in results:
        vibe_score = doc.get("$similarity", 0)
        title = doc.get("title", "Unknown")
        reviews = doc.get("reviews", "").lower()
        overview = doc.get("overview", "").lower()
        
        # Simple Python-side Hybrid Boosting
        ner_boost = 0.3 if any(p in reviews or p in overview for p in found_people) else 0.0
        keyword_boost = 0.0
        
        # Check if query words appear in reviews (Manual keyword boost)
        clean_words = [w for w in re.sub(r'[^a-zA-Z0-9 ]', '', query).split() if len(w) > 3]
        for word in clean_words:
            if word.lower() in reviews or word.lower() in overview:
                keyword_boost += 0.05

        final_score = (vibe_score * 0.7) + ner_boost + min(keyword_boost, 0.2)
        
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
