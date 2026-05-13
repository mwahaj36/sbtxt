import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def upgrade_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    
    try:
        print("Upgrading 'users' table...")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS letterboxd_username TEXT;")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS letterboxd_dp TEXT;")
        conn.commit()
        print("SUCCESS: Database schema updated successfully!")
    except Exception as e:
        print(f"ERROR: Error upgrading database: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    upgrade_db()
