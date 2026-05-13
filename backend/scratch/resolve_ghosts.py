import httpx
import asyncio
import os
from database import get_db_connection

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "your_tmdb_key_here") # Assuming it's in env

async def resolve_movie(title, year):
    async with httpx.AsyncClient() as client:
        params = {"api_key": TMDB_API_KEY, "query": title}
        if year: params["year"] = year
        
        try:
            resp = await client.get("https://api.themoviedb.org/3/search/movie", params=params)
            data = resp.json()
            if data['results']:
                movie = data['results'][0]
                return movie['id'], movie.get('poster_path')
        except:
            return None, None
    return None, None

async def main():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id, movie_title, release_year FROM user_ratings WHERE tmdb_id IS NULL")
    ghosts = cur.fetchall()
    
    if not ghosts:
        print("🎉 No ghost movies found! Your vault is 100% indexed.")
        return

    print(f"🛰️  Found {len(ghosts)} ghost movies. Starting surgical resolution...")
    
    for db_id, title, year in ghosts:
        print(f"🔍 Resolving: {title} ({year})...", end="", flush=True)
        tmdb_id, poster = await resolve_movie(title, year)
        
        if tmdb_id:
            cur.execute("""
                UPDATE user_ratings 
                SET tmdb_id = %s, poster_path = %s 
                WHERE id = %s
            """, (tmdb_id, poster, db_id))
            print(f" ✅ Matched! (TMDB: {tmdb_id})")
        else:
            print(" ❌ No match found.")
            
    conn.commit()
    conn.close()
    print("\n✅ Resolution process complete.")

if __name__ == "__main__":
    asyncio.run(main())
