import os
from astrapy import DataAPIClient
from dotenv import load_dotenv

load_dotenv()
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

def init_astra():
    try:
        client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
        db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
        
        print("Checking Astra DB initialization...")

        # Create the collection only if it doesn't exist
        if "movies" not in db.list_collection_names():
            print("Creating 'movies' collection (768 dimensions)...")
            db.create_collection("movies", dimension=768, metric="cosine")
            print("Initialization complete.")
        else:
            print("Collection 'movies' already exists. Skipping.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    init_astra()