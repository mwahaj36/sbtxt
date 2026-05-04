import os
import sys
import types
import json
import torch
from astrapy import DataAPIClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# --- JINA AI PYTHON 3.12 BUGFIX HACKS ---
try:
    import transformers.onnx
except ImportError:
    mock_onnx = types.ModuleType("transformers.onnx")
    mock_onnx.OnnxConfig = object
    sys.modules["transformers.onnx"] = mock_onnx

import transformers.pytorch_utils
if not hasattr(transformers.pytorch_utils, "find_pruneable_heads_and_indices"):
    def find_pruneable_heads_and_indices(heads, n_heads, head_size, already_pruned_heads):
        return heads, already_pruned_heads
    transformers.pytorch_utils.find_pruneable_heads_and_indices = find_pruneable_heads_and_indices
# ---------------------------------------

load_dotenv()
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

# 1. Load the "Review & Vibe" model (8192 token limit, 768 dimensions)
print("Loading high-quality Jina AI model...")
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = SentenceTransformer('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True).to(device)
model.max_seq_length = 2048 # Cap sequence length to save VRAM on 8GB GPUs

# Load reviews into memory for context
print("Loading reviews into memory...")
movie_reviews = {}
if os.path.exists('movie_reviews.jsonl'):
    with open('movie_reviews.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            movie_reviews[data['id']] = " ".join(data.get('reviews', []))
print(f"Loaded reviews for {len(movie_reviews)} movies.")

def extract_vibe(movie):
    movie_id = movie.get('id')
    title = movie.get('title', '')
    overview = movie.get('overview', '')
    genres = ", ".join([g['name'] for g in movie.get('genres', [])])
    keywords = ", ".join([k['name'] for k in movie.get('keywords', {}).get('keywords', [])])
    
    # Get Director and Top 10 Actors
    credits = movie.get('credits', {})
    director = next((m['name'] for m in credits.get('crew', []) if m['job'] == 'Director'), "")
    actors = ", ".join([m['name'] for m in credits.get('cast', [])[:10]])
    
    # Get Reviews
    reviews = movie_reviews.get(movie_id, "")
    
    # V2 VIBE STRING
    vibe = f"{overview} {overview}. Keywords: {keywords} {keywords}. Genres: {genres}. Cast: {actors}. Director: {director}. User Reviews: {reviews}. (Title: {title})"
    return vibe

def process_and_update(collection, model, batch_data):
    texts = [item['text'] for item in batch_data]
    
    with torch.no_grad():
        embeddings = model.encode(texts, show_progress_bar=False)
    
    # In Astra, we update the $vector field
    for item, vec in zip(batch_data, embeddings):
        collection.find_one_and_update(
            {"_id": str(item['id'])},
            {"$set": {"$vector": vec.tolist()}}
        )

def main():
    # Initialize Astra Client
    client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
    db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
    collection = db.get_collection("movies")
    
    print("Starting full database upgrade to Astra Vibe Vectors...")
    batch_size = 16 # Adjust based on GPU VRAM
    batch_data = []
    processed_this_run = 0

    with open("movies_data.jsonl", "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            movie = json.loads(line)
            vibe_text = extract_vibe(movie)
            batch_data.append({"id": movie.get('id'), "text": vibe_text})

            if len(batch_data) >= batch_size:
                process_and_update(collection, model, batch_data)
                processed_this_run += len(batch_data)
                print(f"Progress: {processed_this_run} / 100,000 movies updated...", end='\r')
                batch_data = []
    
    if batch_data:
        process_and_update(collection, model, batch_data)
        processed_this_run += len(batch_data)
        print(f"Final progress: {processed_this_run} movies.")

    print("All high-quality embeddings have been generated and pushed to Astra DB.")

if __name__ == "__main__":
    main()