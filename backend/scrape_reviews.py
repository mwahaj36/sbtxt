import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()
TMDB_TOKEN = os.getenv("TMDB_TOKEN")
DATA_FILE = "movies_data.jsonl"
OUT_FILE = "movie_reviews.jsonl"
SEMAPHORE_LIMIT = 50  # Increased for maximum speed

async def fetch_reviews(movie_id, client, semaphore, retries=0):
    if retries > 5:
        return {"id": movie_id, "reviews": []}
        
    async with semaphore:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}/reviews?language=en-US&page=1"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {TMDB_TOKEN}"
        }
        try:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                reviews = [r['content'] for r in data.get('results', [])]
                return {"id": movie_id, "reviews": reviews}
            elif response.status_code == 429:
                await asyncio.sleep(0.5)
                return await fetch_reviews(movie_id, client, semaphore, retries + 1)
            else:
                print(f"Error {response.status_code} for {movie_id}: {response.text}")
                return {"id": movie_id, "reviews": []}
        except Exception as e:
            return {"id": movie_id, "reviews": []}

async def main():
    print("Starting TMDB Review Scraper (Up to 20 Reviews per Movie)...")
    
    # Load all movie IDs
    all_ids = set()
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            all_ids.add(json.loads(line)['id'])
            
    # Load already processed IDs to support resuming
    processed_ids = set()
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                processed_ids.add(json.loads(line)['id'])
                
    remaining_ids = list(all_ids - processed_ids)
    print(f"Total Movies: {len(all_ids)}")
    print(f"Already Processed: {len(processed_ids)}")
    print(f"Remaining to Fetch: {len(remaining_ids)}")
    
    if not remaining_ids:
        print("✅ All reviews fetched!")
        return

    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
    limits = httpx.Limits(max_connections=SEMAPHORE_LIMIT)
    
    async with httpx.AsyncClient(timeout=30.0, limits=limits) as client:
        with open(OUT_FILE, "a", encoding="utf-8") as f:
            completed = 0
            # Process in chunks of 1000 to prevent asyncio memory bloat
            for i in range(0, len(remaining_ids), 1000):
                batch = remaining_ids[i:i+1000]
                tasks = [fetch_reviews(mid, client, semaphore) for mid in batch]
                
                for future in asyncio.as_completed(tasks):
                    res = await future
                    if res and res["reviews"]:
                        f.write(json.dumps(res) + "\n")
                    
                    completed += 1
                    if completed % 100 == 0:
                        print(f"Progress: {completed} / {len(remaining_ids)} movies checked.", end='\r')

if __name__ == "__main__":
    asyncio.run(main())
