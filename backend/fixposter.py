import os
import asyncio
import httpx
import json
from dotenv import load_dotenv
from database import get_db_connection

load_dotenv()

def get_tmdb_headers():
    token = os.getenv("TMDB_TOKEN") or os.getenv("TMDB_API_KEY")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

async def get_poster_path(tmdb_id, title, client):
    try:
        # 1. Try Movie by ID
        resp = await client.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}", headers=get_tmdb_headers())
        if resp.status_code == 200:
            return resp.json().get("poster_path"), tmdb_id
        
        # 2. Try TV by ID
        if resp.status_code == 404:
            resp = await client.get(f"https://api.themoviedb.org/3/tv/{tmdb_id}", headers=get_tmdb_headers())
            if resp.status_code == 200:
                return resp.json().get("poster_path"), tmdb_id

        # 3. Search Fallback (Title Search)
        print(f"🔍 [SEARCHING] {title}...")
        search_resp = await client.get(
            f"https://api.themoviedb.org/3/search/multi", 
            params={"query": title},
            headers=get_tmdb_headers()
        )
        if search_resp.status_code == 200:
            results = search_resp.json().get("results", [])
            if results:
                best = results[0] # Best match
                return best.get("poster_path"), best.get("id")

    except Exception as e:
        print(f"⚠️ [API ERROR] {title} ({tmdb_id}): {type(e).__name__} - {e}")
    return None, tmdb_id

async def fix_single_movie(row, client, semaphore, stats):
    async with semaphore:
        movie_id, title, tmdb_id = row
        new_poster, corrected_id = await get_poster_path(tmdb_id, title, client)
        if new_poster:
            conn = get_db_connection()
            if not conn:
                print(f"❌ [DB ERROR] Could not connect to heal {title}")
                return
            with conn.cursor() as cur:
                # Update with new poster AND correct the tmdb_id if it changed
                cur.execute("UPDATE user_ratings SET poster_path = %s, tmdb_id = %s WHERE id = %s", (new_poster, corrected_id, movie_id))
                cur.execute("UPDATE letterboxd_mappings SET poster_path = %s, tmdb_id = %s WHERE tmdb_id = %s", (new_poster, corrected_id, tmdb_id))
                conn.commit()
            conn.close()
            stats['healed'] += 1
            print(f"✅ [HEALED] {title} (New ID: {corrected_id})")
        else:
            stats['failed'] += 1
            print(f"❌ [FAILED] {title} (ID: {tmdb_id})")
        
        # Heartbeat log every 100 items
        processed = stats['healed'] + stats['failed']
        if processed % 100 == 0:
            print(f"[PROGRESS] {processed} movies scanned...")

async def fix_favorites(user_id, favorites, client, semaphore, stats):
    async with semaphore:
        updated = False
        new_favs = []
        for fav in favorites:
            tmdb_id = fav.get('tmdb_id')
            poster = fav.get('poster_path')
            if tmdb_id and (not poster or poster.startswith('http')):
                new_path, corrected_id = await get_poster_path(tmdb_id, fav.get('title', 'Favorite'), client)
                if new_path:
                    fav['poster_path'] = new_path
                    fav['tmdb_id'] = corrected_id
                    updated = True
            new_favs.append(fav)
        
        if updated:
            conn = get_db_connection()
            if not conn: return
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET favorites = %s WHERE id = %s", (json.dumps(new_favs), user_id))
                conn.commit()
            conn.close()
            stats['favs_healed'] += 1

async def main():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, movie_title, tmdb_id FROM user_ratings WHERE tmdb_id IS NOT NULL AND (poster_path IS NULL OR poster_path LIKE 'http%')")
        library_rows = cur.fetchall()
        cur.execute("SELECT id, favorites FROM users WHERE favorites IS NOT NULL")
        user_rows = cur.fetchall()
    conn.close()
    
    if not library_rows and not user_rows:
        print("Vault is already pure.")
        return

    print(f"🚀 [PURIFIER] Starting high-velocity cleanup for {len(library_rows)} items...")
    
    stats = {'healed': 0, 'failed': 0, 'favs_healed': 0}
    semaphore = asyncio.Semaphore(15) # Optimized for stability
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        lib_tasks = [fix_single_movie(row, client, semaphore, stats) for row in library_rows]
        prof_tasks = []
        for u_id, favs_raw in user_rows:
            try:
                favs = json.loads(favs_raw) if isinstance(favs_raw, str) else favs_raw
                if favs: prof_tasks.append(fix_favorites(u_id, favs, client, semaphore, stats))
            except: pass
            
        await asyncio.gather(*lib_tasks, *prof_tasks)

    print(f"🎉 Purification Complete: {stats['healed']} Library items healed | {stats['favs_healed']} Profiles updated.")

if __name__ == "__main__":
    asyncio.run(main())
