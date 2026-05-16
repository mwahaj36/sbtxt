import os
import re
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def normalize_lb_uri(uri: str) -> str:
    if not uri or not isinstance(uri, str): return uri
    match = re.search(r'letterboxd\.com/[^/]+/film/([^/]+)/?', uri)
    if match:
        slug = match.group(1)
        return f"https://letterboxd.com/film/{slug}/"
    uri = uri.strip()
    if not uri.endswith('/'): uri += '/'
    return uri

def migrate():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            print("Fetching all ratings...")
            cur.execute("SELECT id, user_id, letterboxd_uri FROM user_ratings")
            rows = cur.fetchall()
            
            seen = {} # (user_id, normalized_uri) -> id
            to_delete = []
            to_update = []
            
            for rid, uid, uri in rows:
                norm = normalize_lb_uri(uri)
                key = (uid, norm)
                
                if key in seen:
                    print(f"Found duplicate: User {uid}, URI {norm}. Keeping ID {seen[key]}, deleting {rid}")
                    to_delete.append(rid)
                else:
                    seen[key] = rid
                    if norm != uri:
                        to_update.append((norm, rid))
            
            if to_delete:
                print(f"Deleting {len(to_delete)} duplicates...")
                cur.execute("DELETE FROM user_ratings WHERE id = ANY(%s)", (to_delete,))
            
            if to_update:
                print(f"Updating {len(to_update)} URIs to normalized format...")
                for norm, rid in to_update:
                    cur.execute("UPDATE user_ratings SET letterboxd_uri = %s WHERE id = %s", (norm, rid))
            
            print("Cleaning up letterboxd_mappings...")
            cur.execute("SELECT letterboxd_url, tmdb_id FROM letterboxd_mappings")
            m_rows = cur.fetchall()
            m_seen = {} # normalized_url -> tmdb_id
            m_to_delete = []
            m_to_update = []
            
            for url, tid in m_rows:
                norm = normalize_lb_uri(url)
                if norm in m_seen:
                    m_to_delete.append(url)
                else:
                    m_seen[norm] = tid
                    if norm != url:
                        m_to_update.append((norm, url))
            
            if m_to_delete:
                cur.execute("DELETE FROM letterboxd_mappings WHERE letterboxd_url = ANY(%s)", (m_to_delete,))
            if m_to_update:
                for norm, url in m_to_update:
                    cur.execute("UPDATE letterboxd_mappings SET letterboxd_url = %s WHERE letterboxd_url = %s", (norm, url))

            conn.commit()
            print("Migration complete!")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
