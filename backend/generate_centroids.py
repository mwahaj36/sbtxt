import os
import json
import numpy as np
from astrapy import DataAPIClient
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

def generate_centroids():
    client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
    db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
    collection = db.get_collection("movies")

    print("Fetching movies from AstraDB to compute genre centroids...")
    
    genre_vectors = defaultdict(list)
    
    # Fetch 2000 movies (enough for a good centroid)
    batch_size = 20
    count = 0
    max_movies = 2000
    
    for doc in collection.find(projection={"genres": 1, "$vector": 1}, limit=max_movies):
        genres = doc.get("genres", [])
        vector = doc.get("$vector")
        
        if genres and vector and not all(v == 0 for v in vector[:5]):
            vec_np = np.array(vector, dtype=float)
            for g in genres:
                genre_vectors[g].append(vec_np)
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} movies...")

    print(f"Computing centroids for {len(genre_vectors)} genres...")
    
    # First, compute a global centroid of all processed movies
    all_vecs = [v for vecs in genre_vectors.values() for v in vecs]
    global_centroid = np.mean(all_vecs, axis=0)
    
    centroids = {}
    for genre, vecs in genre_vectors.items():
        if len(vecs) >= 5: 
            # Subtract global mean to "center" the vectors
            centroid = np.mean(vecs, axis=0) - global_centroid
            # Normalize
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid = centroid / norm
            centroids[genre] = centroid.tolist()

    # Also save the global centroid so taste.py can use it to center the user vector
    output_data = {
        "global_centroid": global_centroid.tolist(),
        "genres": centroids
    }

    output_path = os.path.join(os.path.dirname(__file__), "genre_centroids.json")
    with open(output_path, "w") as f:
        json.dump(output_data, f)
    
    print(f"Successfully generated {len(centroids)} genre centroids (centered) at {output_path}")

if __name__ == "__main__":
    generate_centroids()
