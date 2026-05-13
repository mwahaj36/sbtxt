from database import get_db_connection

def check_schema():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
    cols = [r[0] for r in cur.fetchall()]
    print(f"Columns: {cols}")
    
    # Add columns if missing
    if 'bio' not in cols:
        print("Adding bio column...")
        cur.execute("ALTER TABLE users ADD COLUMN bio TEXT")
    if 'avatar_url' not in cols:
        print("Adding avatar_url column...")
        cur.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
    if 'favorites' not in cols:
        print("Adding favorites column...")
        cur.execute("ALTER TABLE users ADD COLUMN favorites JSONB")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    check_schema()
