import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db_connection

def test_library_endpoint():
    conn = get_db_connection()
    user_id = '5240f6da-160c-417f-95b1-88504f789e42' # From forensic scan
    interaction = 'watchlist'
    
    try:
        with conn.cursor() as cur:
            # Replicating the exact logic from sync.py:get_library
            sql = "SELECT movie_title, tmdb_id FROM user_ratings WHERE user_id = %s AND interaction_type = %s"
            params = [user_id, interaction]
            
            cur.execute(f"SELECT COUNT(*) FROM ({sql}) AS c", params)
            total = cur.fetchone()[0]
            print(f"SQL Count Report: {total}")
            
            sql += " ORDER BY watched_date DESC NULLS LAST, id DESC LIMIT 30 OFFSET 0"
            cur.execute(sql, params)
            rows = cur.fetchall()
            print(f"Rows Returned: {len(rows)}")
            for r in rows[:5]:
                print(f" - {r[0]}")
                
    finally:
        conn.close()

if __name__ == "__main__":
    test_library_endpoint()
