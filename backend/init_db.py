import os
from astrapy import DataAPIClient
from dotenv import load_dotenv

load_dotenv()
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

def init_astra():
    try:
        # Initialize the client
        client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
        db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
        
        print(f"Connected to Astra DB.")

        # 1. Drop existing collection if it exists
        try:
            db.drop_collection("movies")
            print("Dropped existing 'movies' collection.")
        except:
            pass
        
        # 2. Create the collection with Vector support (using new 2.x syntax)
        # Dimension 768 for Jina AI V2
        collection = db.create_collection(
            "movies",
            definition={
                "vector": {
                    "dimension": 768,
                    "metric": "cosine"
                }
            }
        )
        
        print("Astra DB initialized successfully. Collection 'movies' is ready.")
        
    except Exception as e:
        print(f"Error initializing Astra DB: {e}")

if __name__ == "__main__":
    init_astra()