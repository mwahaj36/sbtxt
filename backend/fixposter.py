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

async def get_poster_path(tmdb_id, client):
    try:
        resp = await client.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}", headers=get_tmdb_headers())
        if resp.status_code == 200:
            return resp.json().get("poster_path")
    except: pass
    return None

async def fix_single_movie(row, client, semaphore, conn, stats):
    async with semaphore:
        movie_id, title, tmdb_id = row
        new_poster = await get_poster_path(tmdb_id, client)
        if new_poster:
            with conn.cursor() as cur:
                cur.execute("UPDATE user_ratings SET poster_path = %s WHERE id = %s", (new_poster, movie_id))
                cur.execute("UPDATE letterboxd_mappings SET poster_path = %s WHERE tmdb_id = %s", (new_poster, tmdb_id))
            stats['healed'] += 1
        else:
            stats['failed'] += 1

async def fix_favorites(user_id, favorites, client, semaphore, conn, stats):
    async with semaphore:
        updated = False
        new_favs = []
        for fav in favorites:
            tmdb_id = fav.get('tmdb_id')
            poster = fav.get('poster_path')
            if tmdb_id and (not poster or poster.startswith('http')):
                print(f"[FAVORITES] Healing poster for: {fav.get('title')}")
                new_path = await get_poster_path(tmdb_id, client)
                if new_path:
                    fav['poster_path'] = new_path
                    updated = True
            new_favs.append(fav)
        
        if updated:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET favorites = %s WHERE id = %s", (json.dumps(new_favs), user_id))
            stats['favs_healed'] += 1

async def main():
    conn = get_db_connection()
    conn.autocommit = True
    
    with conn.cursor() as cur:
        # 1. Gather dirty library items
        cur.execute("SELECT id, movie_title, tmdb_id FROM user_ratings WHERE tmdb_id IS NOT NULL AND (poster_path IS NULL OR poster_path LIKE 'http%')")
        library_rows = cur.fetchall()
        
        # 2. Gather users with favorites
        cur.execute("SELECT id, favorites FROM users WHERE favorites IS NOT NULL")
        user_rows = cur.fetchall()
    
    if not library_rows and not user_rows:
        print("Vault is already pure.")
        conn.close()
        return

    print(f"Purifying {len(library_rows)} library items and {len(user_rows)} user profiles...")
    
    stats = {'healed': 0, 'failed': 0, 'favs_healed': 0}
    semaphore = asyncio.Semaphore(25) # High concurrency
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Library tasks
        lib_tasks = [fix_single_movie(row, client, semaphore, conn, stats) for row in library_rows]
        # Profile tasks
        prof_tasks = []
        for u_id, favs_raw in user_rows:
            try:
                favs = json.loads(favs_raw) if isinstance(favs_raw, str) else favs_raw
                if favs: prof_tasks.append(fix_favorites(u_id, favs, client, semaphore, conn, stats))
            except: pass
            
        await asyncio.gather(*lib_tasks, *prof_tasks)

    conn.close()
    print(f"Purification Complete: {stats['healed']} Library items healed | {stats['favs_healed']} Profiles updated.")

if __name__ == "__main__":
    asyncio.run(main())
