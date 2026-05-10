from search import collection, model
import json

def diagnose():
    print("--- Diagnosing Inception's Rank ---")
    
    # 1. Check Heist Intent
    q_heist = "heist"
    vec_heist = model.encode(q_heist).tolist()
    res_heist = list(collection.find({}, sort={"$vector": vec_heist}, limit=300, include_similarity=True))
    
    h_rank = next((i+1 for i, r in enumerate(res_heist) if r.get("title") == "Inception"), "Not in Top 300")
    print(f"Rank for 'heist': {h_rank}")

    # 2. Check Dream Intent
    q_dream = "dream within a dream"
    vec_dream = model.encode(q_dream).tolist()
    res_dream = list(collection.find({}, sort={"$vector": vec_dream}, limit=300, include_similarity=True))
    
    d_rank = next((i+1 for i, r in enumerate(res_dream) if r.get("title") == "Inception"), "Not in Top 300")
    print(f"Rank for 'dream': {d_rank}")

    # 3. Print Inception's Metadata
    inc = collection.find_one({"title": "Inception"})
    if inc:
        print("\n--- Inception Metadata ---")
        print(f"Overview: {inc.get('overview')[:200]}...")
        print(f"Genres: {inc.get('genres')}")

if __name__ == "__main__":
    diagnose()
