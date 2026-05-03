"""
A modular, async, multi-strategy TMDB ID scraper.
Automatically rotates through Genres and Years to reach any target count.
"""

import os
import asyncio
import httpx
import pandas as pd
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
TMDB_TOKEN = os.getenv("TMDB_TOKEN")
BASE_URL = "https://api.themoviedb.org/3/discover/movie"
TARGET_COUNT = 100000
CONCURRENT_PAGES = 20  # Fetch 20 pages at a time
OUTPUT_FILE = "100k_ids.csv"

# --- CORE FUNCTIONS ---
async def fetch_page(client: httpx.AsyncClient, semaphore: asyncio.Semaphore, params: dict):
    """Fetches a single page of results from TMDB."""
    async with semaphore:
        headers = {
            "Authorization": f"Bearer {TMDB_TOKEN}",
            "accept": "application/json"
        }
        try:
            resp = await client.get(BASE_URL, headers=headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                return [m['id'] for m in data.get('results', [])]
        except Exception:
            pass
        return []

async def run_strategy(name: str, strategy_params: dict, existing_ids: set, client: httpx.AsyncClient, semaphore: asyncio.Semaphore):
    """Executes a specific search strategy across up to 500 pages."""
    print(f"\nSTARTING STRATEGY: {name}")
    
    for page_start in range(1, 501, CONCURRENT_PAGES):
        if len(existing_ids) >= TARGET_COUNT:
            return

        tasks = []
        for p in range(page_start, page_start + CONCURRENT_PAGES):
            if p > 500:
                break
            # Create a unique param set for this specific page
            p_params = strategy_params.copy()
            p_params["page"] = p
            tasks.append(fetch_page(client, semaphore, p_params))

        # Execute batch of pages
        results = await asyncio.gather(*tasks)
        
        # Deduplicate and update
        for id_list in results:
            existing_ids.update(id_list)
        
        # AUTO-SAVE progress
        pd.DataFrame(list(existing_ids), columns=['tmdbId']).to_csv(OUTPUT_FILE, index=False)
        print(f"[{name}] Total Unique IDs: {len(existing_ids)}")

async def main():
    # Load existing progress
    if os.path.exists(OUTPUT_FILE):
        df = pd.read_csv(OUTPUT_FILE)
        existing_ids = set(df['tmdbId'])
    else:
        existing_ids = set()

    print(f"📊 Initial Dataset Size: {len(existing_ids)}")
    
    semaphore = asyncio.Semaphore(CONCURRENT_PAGES)
    
    # Define our Master Strategy List programmatically
    strategies = []
    
    # Strategy A: All Genres (Deep Dive)
    genre_ids = [28, 12, 16, 35, 80, 99, 18, 10751, 14, 36, 27, 10402, 9648, 10749, 878, 53, 10752, 37]
    for gid in genre_ids:
        strategies.append({
            "name": f"Genre ID {gid}", 
            "params": {"with_genres": gid, "sort_by": "popularity.desc", "vote_count.gte": 10}
        })
        
    # Strategy B: Historical Sweep (2025 back to 1920)
    for year in range(2025, 1920, -1):
        strategies.append({
            "name": f"Year {year}", 
            "params": {"primary_release_year": year, "sort_by": "vote_count.desc", "vote_count.gte": 1}
        })

    # Execute the plan
    async with httpx.AsyncClient(timeout=15.0) as client:
        for s in strategies:
            if len(existing_ids) >= TARGET_COUNT:
                print("\n🏁 Target reach! Stopping ingestor.")
                break
            await run_strategy(s["name"], s["params"], existing_ids, client, semaphore)

    print(f"\nSUCCESS! Final dataset at {len(existing_ids)} entries.")

if __name__ == "__main__":
    asyncio.run(main())
