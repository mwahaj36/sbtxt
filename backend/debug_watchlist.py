
import asyncio
import httpx
import re
from database import get_db_connection
from sync import scrape_watchlist_quick, get_ghost_headers

async def debug_user_watchlist():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Find the user (assuming you're the main active user)
            cur.execute("SELECT id, username, letterboxd_username FROM users ORDER BY id DESC LIMIT 1")
            user = cur.fetchone()
            if not user:
                print("[ERROR] No users found in database.")
                return
            
            user_id, username, lb_username = user
            print(f"[DEBUG] Target User: {username} (LB: {lb_username})")
            
            # Check current DB state
            cur.execute("SELECT COUNT(*) FROM user_ratings WHERE user_id = %s AND interaction_type = 'watchlist'", (user_id,))
            current_count = cur.fetchone()[0]
            print(f"[DATABASE] Current Watchlist Count: {current_count}")
            
            # Run the scraper
            async with httpx.AsyncClient(timeout=20.0) as client:
                url = f"https://letterboxd.com/{lb_username}/watchlist/"
                print(f"[SCRAPER] Scraping {url} ...")
                resp = await client.get(url, headers=get_ghost_headers(lb_username), follow_redirects=True)
                print(f"[HTTP] Status: {resp.status_code}")
                html = resp.text
                print(f"[HTML] Snippet: {html[:500]}...")
                
                has_slug = "data-film-slug" in html
                has_poster = "poster" in html
                has_film_id = "film-id" in html
                film_links = len(re.findall(r'/film/.*?/', html))
                
                print(f"[HTML] Contains 'data-film-slug': {has_slug}")
                print(f"[HTML] Contains 'poster': {has_poster}")
                print(f"[HTML] Contains 'film-id': {has_film_id}")
                print(f"[HTML] Count of '/film/' links: {film_links}")
                
                if film_links > 0:
                    print(f"[HTML] First 3 film links: {re.findall(r'/film/.*?/', html)[:3]}")
                
                scraped_movies = await scrape_watchlist_quick(lb_username, client)
                
                # Check for the 2 new ones
                new_discoveries = []
                filtered_by_title = 0
                for m in scraped_movies:
                    # Check by URI
                    cur.execute("SELECT 1 FROM user_ratings WHERE user_id = %s AND letterboxd_uri = %s AND interaction_type = 'watchlist'", (user_id, m['letterboxd_uri']))
                    if cur.fetchone(): continue
                    
                    # Check by Title (Fuzzy)
                    cur.execute("SELECT 1 FROM user_ratings WHERE user_id = %s AND movie_title ILIKE %s AND interaction_type = 'watchlist'", (user_id, m['movie_title']))
                    if cur.fetchone():
                        filtered_by_title += 1
                        continue
                        
                    new_discoveries.append(m['movie_title'])
                
                print(f"[FILTER] {filtered_by_title} movies already exist in DB by title.")
                if new_discoveries:
                    print(f"[FOUND] {len(new_discoveries)} truly new movies: {', '.join(new_discoveries)}")
                else:
                    print("[CLEAN] No truly new movies found.")

    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(debug_user_watchlist())
