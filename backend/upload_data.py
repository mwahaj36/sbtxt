import os
import json
from astrapy import DataAPIClient
from dotenv import load_dotenv

load_dotenv()
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

def upload_movies():
    client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
    db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
    collection = db.get_collection("movies")

    print("Loading reviews into memory...")
    movie_reviews = {}
    if os.path.exists("movie_reviews.jsonl"):
        with open("movie_reviews.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                movie_reviews[data['id']] = " ".join(data.get('reviews', []))
    
    batch_size = 50
    batch = []
    total_count = 0
    
    print("Starting metadata-enriched upload to Astra DB...")
    with open("movies_data.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            movie = json.loads(line)
            m_id = str(movie.get('id'))
            
            # Credits extraction
            credits = movie.get('credits', {})
            director = next((m['name'] for m in credits.get('crew', []) if m['job'] == 'Director'), "")
            cast_names = [m['name'] for m in credits.get('cast', [])[:5]]
            
            # Year extraction
            rel_date = movie.get('release_date', '')
            release_year = int(rel_date[:4]) if rel_date and len(rel_date) >= 4 else None

            # Create fully enriched document
            doc = {
                "_id": m_id,
                "title": movie.get('title'),
                "poster_path": movie.get('poster_path'),
                "overview": movie.get('overview', '')[:7000],
                "reviews": movie_reviews.get(int(m_id), "")[:7000],
                "original_language": movie.get('original_language', ''),
                "release_year": release_year,
                "vote_average": movie.get('vote_average', 0),
                "vote_count": movie.get('vote_count', 0),
                "genres": [g['name'] for g in movie.get('genres', [])],
                "runtime": movie.get('runtime', 0),
                "director": director,
                "cast_names": cast_names,
                "$vector": None # To be filled by generate_embeddings.py
            }
            
            batch.append(doc)
            if len(batch) >= batch_size:
                collection.insert_many(batch)
                total_count += len(batch)
                print(f"Uploaded {total_count} movies...", end='\r')
                batch = []
        
        if batch:
            collection.insert_many(batch)
            total_count += len(batch)

    print(f"\nDone. {total_count} movies have been imported to Astra DB.")

if __name__ == "__main__":
    upload_movies()
