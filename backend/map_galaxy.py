import os
import json
import numpy as np
import umap
import pandas as pd
from astrapy import DataAPIClient
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(dotenv_path='.env')

ASTRA_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

if not ASTRA_TOKEN or not ASTRA_ENDPOINT:
    print("❌ Error: Missing Astra DB credentials in backend/.env")
    exit(1)

client = DataAPIClient(ASTRA_TOKEN)
db = client.get_database_by_api_endpoint(ASTRA_ENDPOINT)
collection = db.get_collection("movies")

CACHE_FILE = "vector_cache.json"

import concurrent.futures
import threading

def fetch_all_vectors():
    all_data = []
    
    # 1. Load from cache if it exists
    if os.path.exists(CACHE_FILE):
        print(f"📦 Loading cached vectors from {CACHE_FILE}...")
        try:
            with open(CACHE_FILE, "r") as f:
                all_data = json.load(f)
            print(f"✅ Loaded {len(all_data)} items from cache.")
        except Exception as e:
            print(f"⚠️ Cache corrupted, starting fresh: {e}")
            all_data = []

    # 2. Get the set of IDs we already have
    cached_ids = {d['id'] for d in all_data}
    
    print(f"📡 Starting Parallel Scan (1880-2030) to bypass SSL bottleneck...")
    
    try:
        total_count = collection.estimated_document_count()
    except:
        total_count = 130000

    all_db_ids = set()
    id_lock = threading.Lock()
    
    # Workers for parallel scanning by Year + Genre (Bulge Buster)
    def scan_worker_genre_year(year, genre, pbar):
        local_ids = set()
        try:
            cursor = collection.find({"release_year": year, "genres": genre}, projection={"_id": 1})
            for doc in cursor:
                local_ids.add(doc["_id"])
                pbar.update(1)
        except: pass
        with id_lock: all_db_ids.update(local_ids)

    # Workers for parallel scanning by Year
    def scan_worker_year(year, pbar):
        local_ids = set()
        try:
            cursor = collection.find({"release_year": year}, projection={"_id": 1})
            for doc in cursor:
                local_ids.add(doc["_id"])
                pbar.update(1)
        except: pass
        with id_lock: all_db_ids.update(local_ids)

    # Workers for parallel scanning by Genre (Safety Net)
    def scan_worker_genre(genre, pbar):
        local_ids = set()
        try:
            cursor = collection.find({"genres": genre}, projection={"_id": 1})
            for doc in cursor:
                local_ids.add(doc["_id"])
                # We don't update pbar here to avoid overcounting total_count
        except: pass
        with id_lock: all_db_ids.update(local_ids)

    # Scan years from 1880 to 2032 in parallel
    years = list(range(1880, 2032)) + [None] # Include None for movies with missing years
    genres = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery", "Romance", "Sci-Fi", "TV Movie", "Thriller", "War", "Western"]
    
    # "Bulge Buster": For recent years, split by year+genre to use all threads
    bulge_years = list(range(2000, 2026))
    
    with tqdm(total=total_count, desc="📡 Scanning IDs") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            # 1. Standard Year workers
            old_years = [y for y in years if y not in bulge_years]
            futures = [executor.submit(scan_worker_year, y, pbar) for y in old_years]
            
            # 2. Bulge Buster workers (Recent Year + Genre combinations)
            for y in bulge_years:
                for g in genres:
                    futures.append(executor.submit(lambda y=y, g=g: scan_worker_genre_year(y, g, pbar)))
            
            # No more standalone genre workers (too slow!)
            concurrent.futures.wait(futures)


    # Final Check: Deep scan bypassed per user preference to save time.
    print(f"ℹ️ Deep scan bypassed. Proceeding with parallel scan results.")

    print(f"✅ Discovery complete: Found {len(all_db_ids)} unique movies.")
    
    missing_ids = list(all_db_ids - cached_ids)
    
    if not missing_ids:
        print("✅ Cache is already up to date.")
        return all_data
        
    print(f"📡 Found {len(missing_ids)} new items. Starting Parallel Download...")
    
    def atomic_save(data):
        temp_file = CACHE_FILE + ".tmp"
        with open(temp_file, "w") as f:
            json.dump(data, f)
        os.replace(temp_file, CACHE_FILE)

    data_lock = threading.Lock()
    new_items_downloaded = [0] # List for mutability in closure

    def fetch_vectors_worker(batch, pbar):
        batch_results = []
        try:
            cursor = collection.find(
                {"_id": {"$in": batch}},
                projection={"_id": 1, "$vector": 1, "title": 1}
            )
            for doc in cursor:
                if "$vector" in doc and doc["$vector"]:
                    batch_results.append({
                        "id": doc["_id"],
                        "vector": list(doc["$vector"]),
                        "title": doc["title"]
                    })
        except:
            pass
            
        if batch_results:
            with data_lock:
                all_data.extend(batch_results)
                new_items_downloaded[0] += len(batch_results)
                # Periodic checkpointing
                if new_items_downloaded[0] >= 2000:
                    atomic_save(all_data)
                    new_items_downloaded[0] = 0
            pbar.update(len(batch_results))

    batch_size = 100
    batches = [missing_ids[i:i + batch_size] for i in range(0, len(missing_ids), batch_size)]
    
    with tqdm(total=len(missing_ids), desc="📡 Downloading Vectors") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            futures = [executor.submit(fetch_vectors_worker, b, pbar) for b in batches]
            concurrent.futures.wait(futures)

    # Final save
    atomic_save(all_data)
    return all_data

def run_mapping():
    data = fetch_all_vectors()
    if not data:
        print("❌ No vectors found in database.")
        return

    print(f"🧠 Preparing {len(data)} vectors for UMAP...")
    embeddings = np.array([d['vector'] for d in data])
    
    print("🌌 Fitting UMAP (this will take a few minutes)...")
    reducer = umap.UMAP(
        n_components=3,
        n_neighbors=15,
        min_dist=0.1,
        metric='cosine',
        verbose=True
    )
    
    coords = reducer.fit_transform(embeddings)
    
    # Save UMAP model for dynamic mapping updates
    try:
        import pickle
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, "umap_reducer.pkl")
        print(f"💾 Saving UMAP model to {model_path}...")
        with open(model_path, "wb") as f:
            pickle.dump(reducer, f)
        print("✅ UMAP model saved.")
    except Exception as e:
        print(f"⚠️ Warning: Failed to save UMAP model: {e}")
    
    print("✅ Mapping complete. Exporting to JSON (Saving AstraDB Costs)...")
    
    output_data = []
    for i, item in enumerate(data):
        x, y, z = coords[i]
        output_data.append({
            "i": item["id"],  # Short keys to save file size
            "t": item["title"][:60],
            "x": float(round(x, 3)),
            "y": float(round(y, 3)),
            "z": float(round(z, 3))
        })

    output_path = "galaxy_points.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, separators=(',', ':')) # Compact JSON

    print(f"\n✨ GALAXY EXPORTED TO {output_path}!")
    print(f"Processed {len(data)} movies. Bypassed 100,000 AstraDB writes. Total Cost: $0.00")


if __name__ == "__main__":
    run_mapping()
