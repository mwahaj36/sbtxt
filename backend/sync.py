import os
import zipfile
import io
import csv
import httpx
import re
import asyncio
import random
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends, Form
from database import get_db_connection
from state import SYNC_PROGRESS
from auth import get_current_user
from taste import refresh_taste_vector_bg

router = APIRouter()

# Global progress tracker (moved to state.py)

# Constants
LB_BODY_ID_REGEX = re.compile(r'data-tmdb-id="(\d+)"')
LB_AVATAR_REGEX = re.compile(r'class="profile-avatar">.*?src="(.*?)"', re.DOTALL)
LB_NAME_REGEX = re.compile(r'<h1 class="title-1"> (.*?) </h1>')

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def get_ghost_headers(username=None):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    if username:
        headers["Referer"] = f"https://letterboxd.com/{username}/"
    return headers

def get_tmdb_headers():
    token = os.getenv("TMDB_TOKEN") or os.getenv("TMDB_API_KEY")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

async def get_poster_path_from_tmdb(tmdb_id: int, client: httpx.AsyncClient) -> Optional[str]:
    try:
        resp = await client.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}", headers=get_tmdb_headers())
        if resp.status_code == 200:
            return resp.json().get('poster_path')
    except: pass
    return None

async def search_tmdb_for_poster(title: str, client: httpx.AsyncClient) -> Optional[tuple]:
    try:
        clean_title = re.sub(r'\s\(\d{4}\)$', '', title)
        resp = await client.get("https://api.themoviedb.org/3/search/movie", params={"query": clean_title}, headers=get_tmdb_headers())
        data = resp.json()
        if data.get('results'):
            movie = data['results'][0]
            return movie['id'], movie.get('poster_path')
    except: pass
    return None

async def scrape_letterboxd_profile_data(username: str, client: httpx.AsyncClient):
    print(f"[IDENTITY] Scraping profile: {username}...")
    resp = await client.get(f"https://letterboxd.com/{username}/", headers=get_ghost_headers(username))
    if resp.status_code != 200: return None
    html = resp.text
    avatar = LB_AVATAR_REGEX.search(html)
    name = LB_NAME_REGEX.search(html)
    og_desc = re.search(r'property="og:description" content="(.*?)"', html)
    bio_text = ""
    films_count = "0"
    favorites = []

    if og_desc:
        desc = og_desc.group(1)
        count_match = re.search(r'([\d,]+) films watched', desc)
        if count_match: films_count = count_match.group(1).replace(',', '')
        bio_match = re.search(r'Bio: (.*)', desc)
        if bio_match: 
            bio_text = bio_match.group(1).strip()
            print(f"[IDENTITY] Bio Extracted: \"{bio_text[:30]}...\"")
        fav_match = re.search(r'Favorites: (.*?)\. Bio:', desc)
        if not fav_match: fav_match = re.search(r'Favorites: (.*)', desc)
        if fav_match:
            fav_titles = [f.strip() for f in fav_match.group(1).split(',')]
            print(f"[IDENTITY] Found {len(fav_titles)} Favorites. Resolving posters...")
            conn = get_db_connection()
            if not conn: return {"avatar": avatar.group(1) if avatar else None, "name": name.group(1) if name else username, "bio": bio_text, "films_count": films_count, "favorites": []}
            with conn.cursor() as cur:
                for full_title in fav_titles[:4]:
                    clean_title = re.sub(r'\s\(\d{4}\)$', '', full_title)
                    cur.execute("SELECT tmdb_id, poster_path FROM user_ratings WHERE movie_title ILIKE %s LIMIT 1", (f"%{clean_title}%",))
                    row = cur.fetchone()
                    tmdb_id, poster = (row[0], row[1]) if row else (None, None)
                    if not tmdb_id or not poster:
                        res = await search_tmdb_for_poster(clean_title, client)
                        if res: tmdb_id, poster = res
                    favorites.append({"title": clean_title, "tmdb_id": tmdb_id, "poster_path": poster})
            conn.close()

    if avatar: print(f"[IDENTITY] Avatar URL Mapped.")
    return {"avatar": avatar.group(1) if avatar else None, "name": name.group(1) if name else username, "bio": bio_text, "films_count": films_count, "favorites": favorites}

async def get_tmdb_id_from_letterboxd(lb_url: str, client: httpx.AsyncClient) -> Optional[tuple]:
    try:
        response = await client.get(lb_url, headers=get_ghost_headers(), follow_redirects=True, timeout=10.0)
        if response.status_code != 200: return None
        html = response.text
        tmdb_match = LB_BODY_ID_REGEX.search(html)
        tmdb_id = int(tmdb_match.group(1)) if tmdb_match else None
        image_match = re.search(r'"image":"(.*?)"', html)
        poster_path = None
        if image_match:
            img_url = image_match.group(1)
            if "tmdb.org" in img_url:
                path_match = re.search(r'/t/p/w\d+/(.*?)$', img_url)
                if path_match: poster_path = "/" + path_match.group(1)
            else: poster_path = img_url
        return tmdb_id, poster_path
    except: return None

def _process_movie_db_sync(movie: dict, user_id: str, tmdb_id: Optional[int], poster_path: Optional[str]):
    """Synchronous DB logic for processing a movie."""
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            # Check mapping
            if not tmdb_id and movie.get('letterboxd_uri'):
                cur.execute("SELECT tmdb_id, poster_path FROM letterboxd_mappings WHERE letterboxd_url = %s", (movie['letterboxd_uri'],))
                row = cur.fetchone()
                if row: tmdb_id, poster_path = row
            
            # Check existing rating - include date in check to allow rewatches to be updated/added
            if tmdb_id:
                interaction = movie.get('interaction_type', 'watched')
                watched_date = movie.get('watched_date')
                
                # We check for exact match of user, movie, type AND date. 
                # If date is different, we want to proceed so the date gets updated.
                if watched_date:
                    cur.execute("SELECT 1 FROM user_ratings WHERE user_id = %s AND tmdb_id = %s AND interaction_type = %s AND watched_date = %s", (user_id, tmdb_id, interaction, watched_date))
                else:
                    cur.execute("SELECT 1 FROM user_ratings WHERE user_id = %s AND tmdb_id = %s AND interaction_type = %s AND watched_date IS NULL", (user_id, tmdb_id, interaction))
                
                if cur.fetchone(): return tmdb_id, poster_path, True # Found exact record, skip
                
        return tmdb_id, poster_path, False
    finally: conn.close()

def _save_movies_batch(results: List[tuple], user_id: str):
    """Saves a batch of movies to the database in a single transaction."""
    conn = get_db_connection()
    if not conn: 
        print(f"[SYNC][ERROR] DB connection failed for user {user_id}")
        return
    try:
        with conn.cursor() as cur:
            for movie, tmdb_id, poster_path in results:
                # 1. Update Mapping Cache
                cur.execute("INSERT INTO letterboxd_mappings (letterboxd_url, tmdb_id, poster_path) VALUES (%s, %s, %s) ON CONFLICT (letterboxd_url) DO UPDATE SET tmdb_id = EXCLUDED.tmdb_id, poster_path = EXCLUDED.poster_path", (movie['letterboxd_uri'], tmdb_id, poster_path))
                
                # 2. Save User Rating/Watchlist Item
                interaction = movie.get('interaction_type', 'watched')
                cur.execute("""
                    INSERT INTO user_ratings (user_id, movie_title, release_year, rating, watched_date, is_liked, interaction_type, tmdb_id, poster_path, letterboxd_uri) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                    ON CONFLICT (user_id, tmdb_id, interaction_type) 
                    DO UPDATE SET rating = EXCLUDED.rating, watched_date = EXCLUDED.watched_date, is_liked = EXCLUDED.is_liked, poster_path = EXCLUDED.poster_path, letterboxd_uri = EXCLUDED.letterboxd_uri
                """, (user_id, movie['movie_title'], movie.get('release_year'), movie.get('rating'), movie.get('watched_date'), movie.get('is_liked', False), interaction, tmdb_id, poster_path, movie['letterboxd_uri']))
            conn.commit()
            print(f"[SYNC][BATCH] Successfully committed {len(results)} movies.")
    finally: conn.close()

async def process_single_movie(movie: dict, user_id: str, client: httpx.AsyncClient, semaphore: asyncio.Semaphore) -> Optional[tuple]:
    """Resolves a single movie and returns the data for batch saving."""
    async with semaphore:
        title = movie.get('movie_title', 'Unknown')
        try:
            # 1. Threaded DB Check (Still important to avoid redundant fetches)
            tmdb_id, poster_path, exists = await asyncio.to_thread(_process_movie_db_sync, movie, user_id, movie.get('tmdb_id'), movie.get('poster_path'))
            if exists: 
                return None # Already exists, skip
            
            # 2. RESOLVE: If still missing ID, fetch it
            if not tmdb_id and movie.get('letterboxd_uri'):
                print(f"[SYNC][TMDB] Resolving: {title}")
                res = await get_tmdb_id_from_letterboxd(movie['letterboxd_uri'], client)
                if res: tmdb_id, poster_path = res
            
            if tmdb_id and not poster_path:
                poster_path = await get_poster_path_from_tmdb(tmdb_id, client)
            
            # 3. RETURN DATA (for batching)
            if tmdb_id:
                return (movie, tmdb_id, poster_path)
            else:
                print(f"[SYNC] Failed to resolve: {title}")
                return None
        except Exception as e:
            print(f"[SYNC ERROR] {title}: {e}")
            return None
        finally:
            if user_id in SYNC_PROGRESS:
                SYNC_PROGRESS[user_id]["processed"] += 1

async def resolve_tmdb_ids(movies: List[Dict], user_id: str, client: Optional[httpx.AsyncClient] = None, sequential: bool = False, skip_refresh: bool = False):
    """Resolves titles to TMDB IDs using a semaphore to limit concurrency."""
    print(f"[SYNC] Resolving {len(movies)} items...")
    SYNC_PROGRESS[user_id]["total"] = len(movies)
    SYNC_PROGRESS[user_id]["processed"] = 0
    
    # Turbo mode for large batches, sequential for order-sensitive ones
    concurrency = 1 if sequential else 50
    semaphore = asyncio.Semaphore(concurrency)
    
    resolved_batch = []
    
    async def run_with_client(target_client):
        nonlocal resolved_batch
        tasks = [process_single_movie(m, user_id, target_client, semaphore) for m in movies]
        
        # Process tasks as they complete
        for i, future in enumerate(asyncio.as_completed(tasks)):
            result = await future
            if result:
                resolved_batch.append(result)
                # Save in chunks of 50 for efficiency
                if len(resolved_batch) >= 50:
                    batch_to_save = resolved_batch[:]
                    resolved_batch = []
                    await asyncio.to_thread(_save_movies_batch, batch_to_save, user_id)
            
            if (i + 1) % 100 == 0:
                print(f"[SYNC][PROGRESS] Processed {i + 1}/{len(movies)} items...")

    if client is None:
        async with httpx.AsyncClient(timeout=20.0) as new_client:
            await run_with_client(new_client)
    else:
        await run_with_client(client)
    
    # Save final remaining items
    if resolved_batch:
        await asyncio.to_thread(_save_movies_batch, resolved_batch, user_id)
        print(f"[SYNC] Final batch of {len(resolved_batch)} movies committed.")
    
    if skip_refresh:
        SYNC_PROGRESS[user_id] = {"status": "completed", "processed": len(movies), "total": len(movies), "message": "Sync complete!"}
        return

    # Refresh taste vector in the background (takes longer)
    await refresh_taste_vector_bg(user_id)
    
    # Mark as completed only AFTER taste DNA is ready
    SYNC_PROGRESS[user_id] = {"status": "completed", "processed": len(movies), "total": len(movies), "message": "DNA Mapped & Sync Complete!"}

@router.get("/status")
async def get_sync_status(user_id: str = Depends(get_current_user)):
    return SYNC_PROGRESS.get(user_id, {"status": "idle", "processed": 0, "total": 0})

async def sync_live_history(username: str, user_id: str):
    """
    Quickly syncs recent activity (watched), watchlist, and profile metadata.
    """
    print(f"[SYNC][START] Starting live history sync for user: {username} (ID: {user_id})")
    SYNC_PROGRESS[user_id] = {"status": "syncing", "processed": 0, "total": 1, "message": "Fetching RSS feeds..."}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            # 1. Fetch History Feed (RSS)
            print(f"[SYNC][RSS] Fetching history feed from Letterboxd...")
            feeds = [(f"https://letterboxd.com/{username}/rss/", "watched")]
            all_new_movies = []
            ns = {'letterboxd': 'https://letterboxd.com', 'tmdb': 'https://themoviedb.org'}
            
            for rss_url, interaction_type in feeds:
                resp = await client.get(rss_url, headers=get_ghost_headers(username))
                if resp.status_code == 200:
                    root = ET.fromstring(resp.text)
                    items = root.findall('.//item')
                    conn = get_db_connection()
                    if not conn: break
                    try:
                        with conn.cursor() as cur:
                            for item in items:
                                title_tag = item.find('letterboxd:filmTitle', ns)
                                if title_tag is None: continue
                                title = title_tag.text
                                link_tag = item.find('link')
                                lb_uri = link_tag.text if link_tag is not None else None
                                
                                # Extract watched date
                                date_tag = item.find('letterboxd:watchedDate', ns)
                                watched_date = date_tag.text if date_tag is not None else None
                                
                                cur.execute("SELECT 1 FROM user_ratings WHERE user_id = %s AND letterboxd_uri = %s AND interaction_type = 'watched' AND watched_date = %s", (user_id, lb_uri, watched_date))
                                if cur.fetchone(): continue # Already synced this specific watch
                                
                                year_tag = item.find('letterboxd:filmYear', ns)
                                rating_tag = item.find('letterboxd:memberRating', ns)
                                tmdb_id_tag = item.find('tmdb:movieId', ns)
                                
                                all_new_movies.append({
                                    'movie_title': title,
                                    'release_year': int(year_tag.text) if year_tag is not None else None,
                                    'rating': float(rating_tag.text) if rating_tag is not None else None,
                                    'interaction_type': 'watched',
                                    'letterboxd_uri': lb_uri,
                                    'tmdb_id': int(tmdb_id_tag.text) if tmdb_id_tag is not None else None,
                                    'watched_date': watched_date
                                })
                    finally: conn.close()

            # 2. Fetch Watchlist via Scraper
            print(f"[SYNC][SCRAPE] Starting watchlist scraper for {username}...")
            SYNC_PROGRESS[user_id]["message"] = "Checking watchlist additions..."
            watchlist_movies = await scrape_watchlist_quick(username, client)
            if watchlist_movies:
                print(f"[SYNC][SCRAPE] Found {len(watchlist_movies)} items in public watchlist.")
                conn = get_db_connection()
                if conn:
                    try:
                        with conn.cursor() as cur:
                            # Process scraper items in reverse (Oldest to Newest) 
                            # so Newest gets processed last and gets the HIGHEST ID
                            for m in reversed(watchlist_movies):
                                cur.execute("SELECT 1 FROM user_ratings WHERE user_id = %s AND letterboxd_uri = %s AND interaction_type = 'watchlist'", (user_id, m['letterboxd_uri']))
                                if not cur.fetchone(): 
                                    # Set watched_date to current time for watchlist items to maintain sort order
                                    m['watched_date'] = datetime.now().isoformat()
                                    all_new_movies.append(m)
                    finally: conn.close()

            if all_new_movies:
                SYNC_PROGRESS[user_id]["total"] = len(all_new_movies)
                # Split: Process watchlist items sequentially to preserve ID order/sort
                watched_items = [m for m in all_new_movies if m['interaction_type'] == 'watched']
                watchlist_items = [m for m in all_new_movies if m['interaction_type'] == 'watchlist']
                
                if watched_items:
                    await resolve_tmdb_ids(watched_items, user_id, client, skip_refresh=True)
                
                if watchlist_items:
                    # Sequential is KEY for correct watchlist sorting (id-based)
                    await resolve_tmdb_ids(watchlist_items, user_id, client, sequential=True, skip_refresh=True)

            # 3. Mirror Identity Data
            SYNC_PROGRESS[user_id]["message"] = "Mirroring profile data..."
            profile_data = await scrape_letterboxd_profile_data(username, client)
            if profile_data:
                conn = get_db_connection()
                if conn:
                    try:
                        with conn.cursor() as cur:
                            cur.execute("UPDATE users SET bio = %s, avatar_url = %s, favorites = %s, letterboxd_films_count = %s WHERE id = %s", (profile_data['bio'], profile_data['avatar'], json.dumps(profile_data['favorites']), profile_data['films_count'], user_id))
                            conn.commit()
                    finally: conn.close()
            
            # 4. Refresh Taste DNA
            SYNC_PROGRESS[user_id]["message"] = "Finalizing Taste DNA..."
            await refresh_taste_vector_bg(user_id)
            
            SYNC_PROGRESS[user_id] = {"status": "completed", "processed": 0, "total": 0, "message": "Sync complete!"}
            print(f"[SYNC][COMPLETE] Full library synchronization finished for user: {username}")
            
    except Exception as e:
        print(f"[SYNC ERROR] {e}")
        import traceback
        traceback.print_exc()
        SYNC_PROGRESS[user_id] = {"status": "error", "message": str(e)}

class CheckLikedRequest(BaseModel):
    tmdb_ids: List[int]

@router.post("/check_liked")
async def check_liked(request: CheckLikedRequest, user_id: str = Depends(get_current_user)):
    conn = get_db_connection()
    if not conn: return {"movies": [], "total": 0, "page": 1, "pages": 1}
    try:
        with conn.cursor() as cur:
            if not request.tmdb_ids:
                return {}
            # Filter None/invalid IDs just in case
            valid_ids = [tid for tid in request.tmdb_ids if tid is not None]
            if not valid_ids:
                return {}
            format_strings = ','.join(['%s'] * len(valid_ids))
            cur.execute(f"SELECT tmdb_id FROM user_ratings WHERE user_id = %s AND is_liked = TRUE AND tmdb_id IN ({format_strings})", [user_id] + valid_ids)
            liked_ids = {row[0]: True for row in cur.fetchall()}
            return liked_ids
    finally:
        conn.close()

@router.post("/letterboxd")
async def sync_letterboxd_zip(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    wipe: bool = Form(False),
    user_id: str = Depends(get_current_user)
):
    try:
        content = await file.read()
        z = zipfile.ZipFile(io.BytesIO(content))
        
        movies_to_sync = []
        # Process files: ratings.csv, watched.csv, watchlist.csv, likes.csv
        file_map = {
            "ratings.csv": "watched",
            "watched.csv": "watched",
            "watchlist.csv": "watchlist",
            "likes.csv": "liked"
        }
        
        # Track seen to avoid duplicates within the ZIP
        seen_keys = set()

        for filename, interaction in file_map.items():
            if filename in z.namelist():
                with z.open(filename) as f:
                    # Letterboxd CSVs are usually UTF-8
                    reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8'))
                    for row in reader:
                        title = row.get('Name') or row.get('Title')
                        year = row.get('Year') or row.get('Release Year')
                        uri = row.get('Letterboxd URI') or row.get('Link')
                        rating = row.get('Rating')
                        date = row.get('Date') or row.get('Watched Date')
                        
                        if not title: continue
                        
                        # Create a unique key for this entry
                        key = f"{title}-{year}-{interaction}"
                        if key in seen_keys: continue
                        seen_keys.add(key)

                        movie_data = {
                            "movie_title": title,
                            "release_year": int(year) if year and year.isdigit() else None,
                            "letterboxd_uri": uri,
                            "interaction_type": interaction if interaction != 'liked' else 'watched',
                            "is_liked": interaction == 'liked',
                            "rating": float(rating) if rating else None,
                            "watched_date": date
                        }
                        
                        # If it's a rating, it's already 'watched', but we might have a 'liked' status from elsewhere
                        # Merging logic could be complex, but for now we just append
                        movies_to_sync.append(movie_data)

        # RECONCILIATION: Clear existing data if corresponding CSVs are present to ensure deletions are synced
        is_reconciling_watched = "watched.csv" in z.namelist() or "ratings.csv" in z.namelist()
        is_reconciling_watchlist = "watchlist.csv" in z.namelist()

        if wipe:
            print(f"⚠️ [DANGER] Full Wipe requested for user {user_id}. Clearing all library data...")
            conn = get_db_connection()
            if not conn:
                raise Exception("Database unavailable for wipe")
            try:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM user_ratings WHERE user_id = %s", (user_id,))
                    conn.commit()
            finally: conn.close()
            print("[SYNC] Database wiped. Starting clean import...")
        elif is_reconciling_watched or is_reconciling_watchlist:
            print(f"[SYNC] Reconciliation started for user {user_id}. Using Additive-Only Sync.")
            # We no longer DELETE in additive mode.
            print("[SYNC] Mappings are preserved, resolution will be rapid.")

        if not movies_to_sync:
            raise HTTPException(status_code=400, detail="No valid movies found in ZIP")

        # Initialize progress
        SYNC_PROGRESS[user_id] = {"status": "syncing", "processed": 0, "total": len(movies_to_sync)}
        
        # Start background resolution
        background_tasks.add_task(resolve_tmdb_ids, movies_to_sync, user_id, None, False, False)
        
        return {"status": "started", "total_movies": len(movies_to_sync)}
        
    except Exception as e:
        print(f"[ZIP SYNC ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/live")
async def trigger_live_sync(background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user)):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT letterboxd_username FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        if not row or not row[0]: raise HTTPException(status_code=400, detail="No Letterboxd username")
        username = row[0]
    conn.close()
    background_tasks.add_task(sync_live_history, username, user_id)
    return {"status": "started"}

@router.get("/profile")
async def get_profile(username: str, user_id: str = Depends(get_current_user)):
    conn = get_db_connection()
    with conn.cursor() as cur:
        # Check if we already have any profile data in the DB
        cur.execute("SELECT bio, avatar_url, favorites, letterboxd_films_count FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        if row and (row[3] is not None): # If films_count is set, we have a profile
            favs = row[2]
            if isinstance(favs, str): favs = json.loads(favs)
            return {
                "username": username,
                "avatar": row[1],
                "name": username,
                "bio": row[0],
                "films_count": row[3],
                "favorites": favs or []
            }
    conn.close()

    # Only scrape if user is brand new or has zero data
    async with httpx.AsyncClient(timeout=20.0) as client:
        data = await scrape_letterboxd_profile_data(username, client)
        if not data: raise HTTPException(status_code=500, detail="Profile mirror failed")
        
        # Save this initial scrape so it's instant next time
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET bio = %s, avatar_url = %s, favorites = %s, letterboxd_films_count = %s WHERE id = %s", (data['bio'], data['avatar'], json.dumps(data['favorites']), data['films_count'], user_id))
            conn.commit()
        conn.close()
        
        return {"username": username, "avatar": data['avatar'], "name": data['name'], "bio": data['bio'], "films_count": data['films_count'], "favorites": data['favorites']}

async def scrape_watchlist_quick(username: str, client: httpx.AsyncClient) -> List[Dict]:
    """
    Directly scrapes the first page of a user's watchlist.
    Returns list of movies with interaction_type='watchlist'.
    """
    url = f"https://letterboxd.com/{username}/watchlist/"
    try:
        resp = await client.get(url, headers=get_ghost_headers(username), follow_redirects=True)
        if resp.status_code != 200: return []
        
        html = resp.text
        # First try the data attribute
        items = re.findall(r'data-film-slug=["\'](.*?/?)["\']', html)
        
        # Fallback: if no data-film-slug found, just find all /film/ links
        if not items:
            items = re.findall(r'/film/[a-z0-9\-]+?/', html)
        
        movies = []
        found_slugs = set()
        
        for slug in items:
            if slug.startswith('/film/'):
                clean_slug = slug if slug.endswith('/') else slug + '/'
                if clean_slug not in found_slugs:
                    movies.append({
                        'movie_title': re.sub(r'\s\d{4}(\s\d+)?$', '', clean_slug.split('/')[-2].replace('-', ' ').title()),
                        'letterboxd_uri': f"https://letterboxd.com{clean_slug}",
                        'interaction_type': 'watchlist'
                    })
                    found_slugs.add(clean_slug)
            
        print(f"[WATCHLIST SCRAPE] Found {len(movies)} potential items on first page.")
        return movies
    except Exception as e:
        print(f"[WATCHLIST SCRAPE ERROR] {e}")
        return []

@router.get("/library")
async def get_library(type: str = "watched", page: int = 1, query: Optional[str] = None, user_id: str = Depends(get_current_user)):
    limit = 30
    offset = (page - 1) * limit
    conn = get_db_connection()
    if not conn: return {"movies": [], "total": 0, "page": 1, "pages": 1}
    try:
        with conn.cursor() as cur:
            interaction = 'watchlist' if type == 'watchlist' else 'watched'
            sql = "SELECT movie_title, release_year, tmdb_id, rating, watched_date, is_liked, poster_path FROM user_ratings WHERE user_id = %s AND interaction_type = %s"
            params = [user_id, interaction]
            if query: 
                query = query.strip()
                sql += " AND movie_title ILIKE %s"
                params.append(f"%{query}%")
            cur.execute(f"SELECT COUNT(*) FROM ({sql}) AS c", params)
            total = cur.fetchone()[0]
            sql += " ORDER BY watched_date DESC NULLS LAST, id DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            cur.execute(sql, params)
            rows = cur.fetchall()
        return {"movies": [{"title": r[0], "year": r[1], "tmdb_id": r[2], "rating": float(r[3]) if r[3] else None, "date": r[4], "is_liked": r[5], "poster_path": r[6]} for r in rows], "total": total, "page": page, "pages": (total + limit - 1) // limit}
    finally: conn.close()

@router.post("/mass")
async def trigger_mass_sync(background_tasks: BackgroundTasks, secret: str = None):
    """
    Admin only: Triggers a sequential quick sync for all users in the database.
    Designed to be called by a daily cron job.
    """
    admin_secret = os.getenv("ADMIN_SECRET", "default_secret_change_me")
    if secret != admin_secret:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    background_tasks.add_task(process_mass_sync)
    return {"status": "Mass sync initiated in background"}

async def process_mass_sync():
    conn = get_db_connection()
    if not conn:
        print("[MASS SYNC] Database connection failed. Aborting.")
        return
    users = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, letterboxd_username FROM users WHERE letterboxd_username IS NOT NULL")
            users = cur.fetchall()
    finally:
        conn.close()
    
    print(f"🚀 [MASS SYNC] Starting sync for {len(users)} users...")
    
    for user_id, lb_username in users:
        try:
            print(f"🔄 [MASS SYNC] Syncing {lb_username}...")
            await sync_live_history(lb_username, user_id)
            # Jitter to avoid Letterboxd rate limits/bot detection
            await asyncio.sleep(5) 
        except Exception as e:
            print(f"❌ [MASS SYNC ERROR] Failed for {lb_username}: {e}")
            
    print("✅ [MASS SYNC] All users processed.")

@router.get("/recent")
async def get_recent_watches(user_id: str = Depends(get_current_user)):
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT movie_title, release_year, tmdb_id, watched_date, poster_path, rating, is_liked FROM user_ratings WHERE user_id = %s AND interaction_type = 'watched' ORDER BY watched_date DESC NULLS LAST, id DESC LIMIT 4", (user_id,))
            rows = cur.fetchall()
        return [{"title": r[0], "year": r[1], "tmdb_id": r[2], "date": r[3], "poster_path": r[4], "rating": float(r[5]) if r[5] else None, "is_liked": r[6]} for r in rows]
    finally: conn.close()
