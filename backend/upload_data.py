import os
import json
from astrapy import DataAPIClient
from dotenv import load_dotenv

load_dotenv()
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

def upload_movies():
    # Initialize Astra Client
    client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
    db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
    collection = db.get_collection("movies")

    print("Loading reviews into memory for enrichment...")
    movie_reviews = {}
    if os.path.exists("movie_reviews.jsonl"):
        with open("movie_reviews.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                movie_reviews[data['id']] = " ".join(data.get('reviews', []))
    
    batch_size = 50 # Astra prefers smaller batches for insert_many
    batch = []
    total_count = 0
    
    print("Starting enriched data upload to Astra DB...")
    with open("movies_data.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            movie = json.loads(line)
            m_id = movie.get('id')
            
            # Truncate to 7500 characters to stay under Astra's 8000-byte index limit
            reviews_text = movie_reviews.get(m_id, "")[:7500]
            overview_text = movie.get('overview', '')[:7500]
            
            # Create document
            doc = {
                "_id": str(m_id),
                "title": movie.get('title'),
                "poster_path": movie.get('poster_path'),
                "overview": overview_text,
                "reviews": reviews_text,
                "$vector": None
            }
            
            batch.append(doc)
            if len(batch) >= batch_size:
                collection.insert_many(batch)
                total_count += len(batch)
                print(f"Uploaded {total_count} movies to Astra...", end='\r')
                batch = []
        
        if batch:
            collection.insert_many(batch)
            total_count += len(batch)
            print(f"\nFinal batch uploaded. Total: {total_count}")

    print(f"Done. {total_count} movies have been imported to Astra DB.")

if __name__ == "__main__":
    upload_movies()
