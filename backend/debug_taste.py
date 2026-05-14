import psycopg2
import numpy as np
import json
import os
from database import get_db_connection

def debug_taste():
    GENRE_CENTROIDS_PATH = "genre_centroids.json"
    user_id = "5240f6da-160c-417f-95b1-88504f789e42"
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT taste_vector FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    if not row or not row[0]:
        print("No taste vector found for user")
        return
    
    vec = np.array(row[0])
    
    if not os.path.exists(GENRE_CENTROIDS_PATH):
        print("Centroids file not found")
        return
        
    with open(GENRE_CENTROIDS_PATH, "r") as f:
        centroids = json.load(f)
        
    scores = []
    for g, c in centroids.items():
        c_vec = np.array(c)
        # Cosine similarity
        sim = float(np.dot(vec, c_vec) / (np.linalg.norm(vec) * np.linalg.norm(c_vec)))
        scores.append((g, sim))
        
    scores.sort(key=lambda x: x[1], reverse=True)
    print("TOP GENRES RAW SCORES:")
    for g, s in scores[:10]:
        print(f"{g}: {s:.4f}")

if __name__ == "__main__":
    debug_taste()
