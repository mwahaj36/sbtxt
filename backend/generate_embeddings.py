import os
import sys
import types
import json
import time
import torch
from astrapy import DataAPIClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Thread

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

# 1. Load the model in FP16 for maximum GPU throughput
print("Loading Jina AI model in FP16 mode...")
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Device: {device}")
model = SentenceTransformer('jinaai/jina-embeddings-v2-base-en', trust_remote_code=True).to(device)
model.half()  # FP16: halves VRAM usage, doubles GPU throughput
model.max_seq_length = 2048
print("Model loaded in FP16. VRAM usage should be ~50% lower.")

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

def main():
    # Initialize Astra Client
    client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
    db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
    collection = db.get_collection("movies")
    
    PROGRESS_FILE = "last_processed.txt"
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as pf:
            START_OFFSET = int(pf.read().strip())
    else:
        START_OFFSET = 0

    print(f"Resuming from line: {START_OFFSET}")
    
    batch_size = 128
    max_context = 2048
    
    # --- THE HIGH-SPEED FP16 PIPELINE ---
    data_queue = Queue(maxsize=256)  # Buffer up to 256 movies in advance

    def producer():
        """Reads from disk and extracts text in the background."""
        with open("movies_data.jsonl", "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i < START_OFFSET:
                    continue
                movie = json.loads(line)
                m_id = str(movie.get('id'))
                vibe_text = extract_vibe(movie)[:max_context * 4]
                data_queue.put({"id": m_id, "text": vibe_text})
        data_queue.put(None)

    Thread(target=producer, daemon=True).start()

    # Thread pool for background database updates
    executor = ThreadPoolExecutor(max_workers=20)

    batch_data = []
    processed_this_run = 0
    start_time = time.time()

    while True:
        item = data_queue.get()
        if item is None:
            break
            
        batch_data.append(item)

        if len(batch_data) >= batch_size:
            # 1. GPU INFERENCE
            gpu_start = time.time()
            texts = [b['text'] for b in batch_data]
            with torch.no_grad():
                embeddings = model.encode(texts, show_progress_bar=False)
            gpu_time = time.time() - gpu_start
            
            # 2. BACKGROUND UPLOAD
            upload_start = time.time()
            def upload_batch(items, vecs):
                for m, v in zip(items, vecs):
                    collection.find_one_and_update(
                        {"_id": str(m['id'])},
                        {"$set": {"$vector": v.tolist()}}
                    )
            
            executor.submit(upload_batch, list(batch_data), embeddings)
            
            # 3. PROGRESS + LOGGING
            processed_this_run += len(batch_data)
            current_total = START_OFFSET + processed_this_run
            elapsed = time.time() - start_time
            speed = processed_this_run / (elapsed / 60) if elapsed > 0 else 0
            
            with open(PROGRESS_FILE, "w") as pf:
                pf.write(str(current_total))
            
            print(f"[FP16] {current_total} done | GPU: {gpu_time:.2f}s | Speed: {speed:.1f}/min | Queue: {data_queue.qsize()}", end='\r')
            batch_data = []

    # Final cleanup
    if batch_data:
        texts = [b['text'] for b in batch_data]
        with torch.no_grad():
            embeddings = model.encode(texts, show_progress_bar=False)
        for m, v in zip(batch_data, embeddings):
            collection.find_one_and_update(
                {"_id": str(m['id'])},
                {"$set": {"$vector": v.tolist()}}
            )

    print("\nWaiting for background uploads to finish...")
    executor.shutdown(wait=True)
    
    total_time = time.time() - start_time
    print(f"\nDone! Processed {processed_this_run} movies in {total_time/3600:.1f} hours.")

if __name__ == "__main__":
    main()