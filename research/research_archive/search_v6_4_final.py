import os
import re
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from astrapy import DataAPIClient
from dotenv import load_dotenv
import spacy
from functools import lru_cache
from sklearn.metrics.pairwise import cosine_similarity
import time

# Load environment
load_dotenv()

# Initialize Astra DB
client = DataAPIClient(os.getenv("ASTRA_DB_APPLICATION_TOKEN"))
db = client.get_database_by_api_endpoint(os.getenv("ASTRA_DB_API_ENDPOINT"))
collection = db.get_collection("movies")

# Initialize Models
print("Initializing Subtext V8 Precision Engine...")
model = SentenceTransformer('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True)
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2') 
nlp = spacy.load("en_core_web_sm")

@lru_cache(maxsize=200)
def get_cached_embedding(text):
    return model.encode(text)

def search(query, num_results=10):
    start_total = time.time()
    
    # --- PHASE 1: PRECISION ENTITY ANCHORING ---
    doc_nlp = nlp(query.title()) # Title case for better NER
    # Detect specific actors/directors for HARD FILTERING
    hard_entities = [ent.text for ent in doc_nlp.ents if ent.label_ in ["PERSON"]]
    
    # --- PHASE 2: ANCHOR & EXCLUSION LOGIC ---
    clean_query = query.lower()
    anchor_title = ""
    for p in ["movies like ", "similar to "]:
        if clean_query.startswith(p):
            anchor_title = clean_query.replace(p, "").strip()
            break
            
    # --- PHASE 3: DATABASE FUNNEL (RECALL) ---
    search_filter = {}
    if hard_entities:
        or_clauses = []
        for ent in hard_entities:
            or_clauses.append({"cast_names": ent})
            or_clauses.append({"director": ent})
        search_filter["$or"] = or_clauses

    q_vec = get_cached_embedding(query)
    
    # DYNAMIC RECALL: If we have an entity, we need a wider net to find all their work
    limit_val = 200 if hard_entities else 50
    
    candidates = list(collection.find(
        filter=search_filter if search_filter else {},
        sort={"$vector": q_vec.tolist()}, 
        limit=limit_val, 
        projection={"title": 1, "overview": 1, "genres": 1, "cast_names": 1, "vote_average": 1, "popularity": 1}
    ))

    # --- PHASE 4: THE PRECISION RANKER ---
    final_results = []
    for doc in candidates:
        title = doc.get("title", "")
        # SURGICAL EXCLUSION: Only exclude the EXACT anchor film
        if anchor_title and title.lower() == anchor_title:
            continue
            
        desc = f"{title}. {doc.get('overview', '')}"
        semantic_score = float(cross_encoder.predict([(query, desc)])[0])
        
        pop = doc.get("popularity", 1.0)
        rating = doc.get("vote_average", 5.0)
        prestige = (rating / (np.log1p(pop) + 1))
        
        score = (semantic_score * 3.0) + (prestige * 0.5)
        
        # RELAXED FLOOR: Let the reranker's soul-searching work
        if score < -2.0: continue
        
        final_results.append({
            "title": title,
            "score": round(score, 2),
            "prestige": prestige > 3.0,
            "overview": doc.get("overview")
        })

    # --- PHASE 5: DIVERSITY (SIMPLE & FAST) ---
    # Instead of MMR, we just pick the top N and ensure unique genres/themes
    final_results.sort(key=lambda x: x["score"], reverse=True)
    
    # Quick filter to prevent sequel bloat
    deduped = []
    seen_roots = set()
    for r in final_results:
        # Simple root detection (e.g. 'The Godfather' vs 'The Godfather Part II')
        root = r['title'].split(':')[0].split('Part')[0].strip()
        if root not in seen_roots:
            deduped.append(r)
            seen_roots.add(root)
        if len(deduped) >= num_results: break

    print(f"Subtext V8 Latency: {int((time.time() - start_total)*1000)}ms")
    return deduped

if __name__ == "__main__":
    print("\n[V8] PRECISION ENGINE: The Great Pruning")
    res = search("ryan gosling in a quiet role", num_results=5)
    for r in res:
        print(f"[{r['score']}] - {r['title']} (Prestige: {r['prestige']})")