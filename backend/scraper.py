import os
import pandas as pd
import httpx
import json
from dotenv import load_dotenv
import asyncio

#Setup 
load_dotenv()
TMDB_TOKEN=os.getenv("TMDB_TOKEN")
BASE_URL = "https://api.themoviedb.org/3/movie"
SEMAPHORE_LIMIT = 50 # How many requests to run at once

#Get Movie Data
async def fetch_movie(movie_id:int,client:httpx.AsyncClient,semaphore: asyncio.Semaphore):
    async with semaphore:
        url=f"{BASE_URL}/{movie_id}"
        headers={
            "accept":"application/json",
            "Authorization":f"Bearer {TMDB_TOKEN}"
        }
        params={
            "append_to_response":"keywords,credits,recommendations,videos,images,reviews",
            "language":"en-US"
        }
        try:
            response=await client.get(url,headers=headers,params=params)
            if response.status_code==200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"Connection error for {movie_id}:{e}")
            return None

async def process_batch(batch_ids,client,semaphore):
    tasks=[fetch_movie(mid,client,semaphore) for mid in batch_ids]
    return await asyncio.gather(*tasks)

async def main():
    df=pd.read_csv("100k_ids.csv")
    movie_ids=df['tmdbId'].tolist()
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(0, len(movie_ids), 1000):
            batch=movie_ids[i:i+1000]
            results=await process_batch(batch,client,semaphore)
            valid_results = [r for r in results if r is not None]
            with open("movies_data.jsonl", "a", encoding="utf-8") as f:
                for movie in valid_results:
                    # Save each movie as its own line
                    f.write(json.dumps(movie) + "\n")
            
            print(f"Progress: {i + len(batch)} / {len(movie_ids)} movies saved.")

if __name__=="__main__":
    asyncio.run(main())

