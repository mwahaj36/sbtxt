import database
import json

def check_movie(title):
    conn = database.get_db_connection()
    if not conn:
        print("DB Connection failed")
        return
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT movie_title, interaction_type, tmdb_id FROM user_ratings WHERE movie_title ILIKE %s", (f"%{title}%",))
            rows = cur.fetchall()
            print(f"Results for '{title}':")
            for r in rows:
                print(f" - {r[0]} | Type: {r[1]} | TMDB: {r[2]}")
            if not rows:
                print("No matches found.")
    finally:
        conn.close()

if __name__ == "__main__":
    check_movie("Haywire")
    check_movie("Moving")
