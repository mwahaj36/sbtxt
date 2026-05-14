import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db_connection

def forensic_scan():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to DB")
        return

    try:
        with conn.cursor() as cur:
            # 1. Get user ID
            cur.execute("SELECT id, letterboxd_username FROM users WHERE letterboxd_username = 'chamkadar1234'")
            user = cur.fetchone()
            if not user:
                print("User not found")
                return
            user_id = user[0]
            print(f"Scanning for User: {user[1]} ({user_id})")

            # 2. Count all interactions
            cur.execute("SELECT interaction_type, count(*) FROM user_ratings WHERE user_id = %s GROUP BY interaction_type", (user_id,))
            counts = cur.fetchall()
            print(f"Database Counts: {counts}")

            # 3. List recent watchlist items
            cur.execute("SELECT movie_title, tmdb_id, letterboxd_uri FROM user_ratings WHERE user_id = %s AND interaction_type = 'watchlist' ORDER BY id DESC LIMIT 50", (user_id,))
            watchlist = cur.fetchall()
            print(f"\nRecent Watchlist (Top 50):")
            for m in watchlist:
                print(f" - {m[0]} (ID: {m[1]}) | {m[2]}")

            # 4. Check for 'Moving'
            cur.execute("SELECT interaction_type, tmdb_id FROM user_ratings WHERE user_id = %s AND movie_title ILIKE '%%Moving%%'", (user_id,))
            moving = cur.fetchall()
            print(f"\n'Moving' check: {moving}")

    finally:
        conn.close()

if __name__ == "__main__":
    forensic_scan()
