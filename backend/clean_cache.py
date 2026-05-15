import json
import os

CACHE_FILE = "vector_cache.json"

if os.path.exists(CACHE_FILE):
    print(f"📦 Analyzing {CACHE_FILE}...")
    with open(CACHE_FILE, "r") as f:
        data = json.load(f)
    
    initial_count = len(data)
    # Deduplicate based on 'id'
    unique_data = {d['id']: d for d in data}.values()
    final_count = len(unique_data)
    
    print(f"Initial items: {initial_count}")
    print(f"Unique items: {final_count}")
    print(f"Duplicates removed: {initial_count - final_count}")
    
    if initial_count != final_count:
        print("💾 Saving cleaned cache...")
        with open(CACHE_FILE, "w") as f:
            json.dump(list(unique_data), f)
        print("✅ Cache cleaned.")
    else:
        print("✨ No duplicates found in cache.")
else:
    print("❌ No cache file found.")
