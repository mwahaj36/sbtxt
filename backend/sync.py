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
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends
from database import get_db_connection
from auth import get_current_user

router = APIRouter()

# Global progress tracker
SYNC_PROGRESS = {}

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
    print(f"🧬 [IDENTITY] Scraping profile: {username}...")
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
            print(f"🧬 [IDENTITY] Bio Extracted: \"{bio_text[:30]}...\"")
        fav_match = re.search(r'Favorites: (.*?)\. Bio:', desc)
        if not fav_match: fav_match = re.search(r'Favorites: (.*)', desc)
        if fav_match:
            fav_titles = [f.strip() for f in fav_match.group(1).split(',')]
            print(f"🧬 [IDENTITY] Found {len(fav_titles)} Favorites. Resolving posters...")
            conn = get_db_connection()
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

    if avatar: print(f"🧬 [IDENTITY] Avatar URL Mapped.")
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

async def process_single_movie(movie: dict, user_id: str, client: httpx.AsyncClient, semaphore: asyncio.Semaphore):
    async with semaphore:
        title = movie.get('movie_title')
        lb_url = movie.get('letterboxd_uri')
        interaction = movie.get('interaction_type', 'watched')
        
        try:
            # 1. QUICK CHECK: See if we already resolved this LB URL recently
            tmdb_id = movie.get('tmdb_id')
            poster_path = movie.get('poster_path')

            conn = get_db_connection()
            with conn.cursor() as cur:
                # Check letterboxd_mappings first
                if not tmdb_id and lb_url:
                    cur.execute("SELECT tmdb_id, poster_path FROM letterboxd_mappings WHERE letterboxd_url = %s", (lb_url,))
                    row = cur.fetchone()
                    if row:
                        tmdb_id, poster_path = row
                
                # Check if this user already has this movie in user_ratings (to skip redundant inserts)
                if tmdb_id:
                    cur.execute("SELECT rating, watched_date, is_liked FROM user_ratings WHERE user_id = %s AND tmdb_id = %s AND interaction_type = %s", (user_id, tmdb_id, interaction))
                    existing = cur.fetchone()
                    
                    # If everything matches exactly, we can skip entirely
                    if existing:
                        # For watched/ratings, check if date/rating matches to decide if update is needed
                        # But for a "very quick" sync, if it exists, we usually skip unless it's a force refresh
                        # Let's assume if it exists, we are good.
                        conn.close()
                        return
            conn.close()

            # 2. RESOLVE: If still missing ID, fetch it
            if not tmdb_id and lb_url:
                res = await get_tmdb_id_from_letterboxd(lb_url, client)
                if res: tmdb_id, poster_path = res
            
            if tmdb_id and not poster_path:
                poster_path = await get_poster_path_from_tmdb(tmdb_id, client)
            
            # 3. SAVE
            if tmdb_id:
                conn = get_db_connection()
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO letterboxd_mappings (letterboxd_url, tmdb_id, poster_path) VALUES (%s, %s, %s) ON CONFLICT (letterboxd_url) DO UPDATE SET tmdb_id = EXCLUDED.tmdb_id, poster_path = EXCLUDED.poster_path", (lb_url, tmdb_id, poster_path))
                    cur.execute("""
                        INSERT INTO user_ratings (user_id, movie_title, release_year, rating, watched_date, is_liked, interaction_type, tmdb_id, poster_path, letterboxd_uri) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                        ON CONFLICT (user_id, tmdb_id, interaction_type) 
                        DO UPDATE SET rating = EXCLUDED.rating, watched_date = EXCLUDED.watched_date, is_liked = EXCLUDED.is_liked, poster_path = EXCLUDED.poster_path, letterboxd_uri = EXCLUDED.letterboxd_uri
                    """, (user_id, title, movie.get('release_year'), movie.get('rating'), movie.get('watched_date'), movie.get('is_liked', False), interaction, tmdb_id, poster_path, lb_url))
                    conn.commit()
                conn.close()
                print(f"✅ [SYNC] Resolved: {title}")
            else:
                print(f"❌ [SYNC] Failed: {title}")
        except Exception as e:
            print(f"⚠️ [SYNC ERROR] {title}: {e}")
        finally:
            if user_id in SYNC_PROGRESS: SYNC_PROGRESS[user_id]["processed"] += 1

async def resolve_tmdb_ids(movies: List[Dict], user_id: str):
    print(f"📡 [SYNC] Resolving {len(movies)} items...")
    SYNC_PROGRESS[user_id]["total"] = len(movies)
    SYNC_PROGRESS[user_id]["processed"] = 0
    semaphore = asyncio.Semaphore(5)
    async with httpx.AsyncClient(timeout=20.0) as client:
        tasks = [process_single_movie(m, user_id, client, semaphore) for m in movies]
        await asyncio.gather(*tasks)

@router.get("/status")
async def get_sync_status(user_id: str = Depends(get_current_user)):
    return SYNC_PROGRESS.get(user_id, {"status": "idle", "processed": 0, "total": 0})

async def sync_live_history(username: str, user_id: str):
    SYNC_PROGRESS[user_id] = {"status": "syncing", "processed": 0, "total": 1}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            rss_url = f"https://letterboxd.com/{username}/rss/"
            resp = await client.get(rss_url, headers=get_ghost_headers(username))
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                ns = {'letterboxd': 'https://letterboxd.com', 'tmdb': 'https://themoviedb.org'}
                items = root.findall('.//item')
                new_movies = []
                conn = get_db_connection()
                with conn.cursor() as cur:
                    for item in items:
                        title_tag = item.find('letterboxd:filmTitle', ns)
                        if title_tag is None: continue
                        title = title_tag.text
                        watched_date_tag = item.find('letterboxd:watchedDate', ns)
                        pub_date_tag = item.find('pubDate')
                        dt = None
                        if watched_date_tag is not None:
                            try: dt = datetime.strptime(watched_date_tag.text, "%Y-%m-%d").date()
                            except: pass
                        if dt is None and pub_date_tag is not None:
                            try: dt = datetime.strptime(pub_date_tag.text, "%a, %d %b %Y %H:%M:%S %z").date()
                            except: pass
                        
                        # SMART SYNC REVERTED: Stop as soon as title + date matches. Fast as lightning.
                        if dt:
                            cur.execute("SELECT 1 FROM user_ratings WHERE user_id = %s AND movie_title = %s AND watched_date = %s", (user_id, title, dt))
                            if cur.fetchone():
                                print(f"🛑 [SMART SYNC] Caught up at: {title} ({dt}). Stopping.")
                                break
                        
                        link = item.find('link').text if item.find('link') is not None else ""
                        year = item.find('letterboxd:filmYear', ns)
                        rating = item.find('letterboxd:memberRating', ns)
                        tmdb_id = item.find('tmdb:movieId', ns)
                        interaction = 'watchlist' if '/watchlist/' in link else 'watched'
                        new_movies.append({"movie_title": title, "release_year": int(year.text) if year is not None else None, "rating": float(rating.text) if rating is not None else None, "tmdb_id": int(tmdb_id.text) if tmdb_id is not None else None, "letterboxd_uri": link, "watched_date": dt, "interaction_type": interaction})
                conn.close()
                if new_movies:
                    await resolve_tmdb_ids(new_movies, user_id)

            print("🧬 [IDENTITY SYNC] Mirroring profile...")
            profile_data = await scrape_letterboxd_profile_data(username, client)
            if profile_data:
                conn = get_db_connection()
                with conn.cursor() as cur:
                    cur.execute("UPDATE users SET bio = %s, avatar_url = %s, favorites = %s, letterboxd_films_count = %s WHERE id = %s", (profile_data['bio'], profile_data['avatar'], json.dumps(profile_data['favorites']), profile_data['films_count'], user_id))
                    conn.commit()
                conn.close()
                print("🎉 [IDENTITY SYNC] Profile mirrored successfully.")
            SYNC_PROGRESS[user_id]["status"] = "completed"
            SYNC_PROGRESS[user_id]["processed"] = SYNC_PROGRESS[user_id]["total"]
    except Exception as e:
        print(f"🚨 [SYNC ERROR] {e}")
        SYNC_PROGRESS[user_id] = {"status": "error", "message": str(e)}

class CheckLikedRequest(BaseModel):
    tmdb_ids: List[int]

@router.post("/check_liked")
async def check_liked(request: CheckLikedRequest, user_id: str = Depends(get_current_user)):
    conn = get_db_connection()
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
async def sync_letterboxd_zip(background_tasks: BackgroundTasks, file: UploadFile = File(...), user_id: str = Depends(get_current_user)):
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

        if not movies_to_sync:
            raise HTTPException(status_code=400, detail="No valid movies found in ZIP")

        # Initialize progress
        SYNC_PROGRESS[user_id] = {"status": "syncing", "processed": 0, "total": len(movies_to_sync)}
        
        # Start background resolution
        background_tasks.add_task(resolve_tmdb_ids, movies_to_sync, user_id)
        
        return {"status": "started", "total_movies": len(movies_to_sync)}
        
    except Exception as e:
        print(f"❌ [ZIP SYNC ERROR] {e}")
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

@router.get("/library")
async def get_library(type: str = "watched", page: int = 1, query: Optional[str] = None, user_id: str = Depends(get_current_user)):
    limit = 32
    offset = (page - 1) * limit
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            interaction = 'watchlist' if type == 'watchlist' else 'watched'
            sql = "SELECT movie_title, release_year, tmdb_id, rating, watched_date, is_liked, poster_path FROM user_ratings WHERE user_id = %s AND interaction_type = %s"
            params = [user_id, interaction]
            if query: sql += " AND movie_title ILIKE %s"; params.append(f"%{query}%")
            cur.execute(f"SELECT COUNT(*) FROM ({sql}) AS c", params)
            total = cur.fetchone()[0]
            sql += " ORDER BY watched_date DESC NULLS LAST, id DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            cur.execute(sql, params)
            rows = cur.fetchall()
        return {"movies": [{"title": r[0], "year": r[1], "tmdb_id": r[2], "rating": float(r[3]) if r[3] else None, "date": r[4], "is_liked": r[5], "poster_path": r[6]} for r in rows], "total": total, "page": page, "pages": (total + limit - 1) // limit}
    finally: conn.close()

@router.get("/recent")
async def get_recent_watches(user_id: str = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT movie_title, release_year, tmdb_id, watched_date, poster_path, rating, is_liked FROM user_ratings WHERE user_id = %s AND interaction_type = 'watched' ORDER BY watched_date DESC NULLS LAST, id DESC LIMIT 4", (user_id,))
            rows = cur.fetchall()
        return [{"title": r[0], "year": r[1], "tmdb_id": r[2], "date": r[3], "poster_path": r[4], "rating": float(r[5]) if r[5] else None, "is_liked": r[6]} for r in rows]
    finally: conn.close()
