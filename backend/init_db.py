import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL=os.getenv("DATABASE_URL")

def init_db():
    try:
        conn=psycopg2.connect(DATABASE_URL)
        cur=conn.cursor()
        print("Connected to DB")

        # 1. Clean start
        cur.execute("DROP TABLE IF EXISTS movies;")
        
        # 2. Enable vector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("Enabled vector")
        
        # 3. ULTRA-LEAN TABLE: ID, Title, Poster, and Vibe (Vector)
        create_Table_Query="""
        CREATE TABLE movies(
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            poster_path TEXT,
            embedding vector(384)
        );
        """

        cur.execute(create_Table_Query)

        # 4. Create the HNSW index for fast vibe searching
        cur.execute("CREATE INDEX IF NOT EXISTS movies_embedding_idx ON movies USING hnsw (embedding vector_cosine_ops);")
        
        conn.commit()
        print("Database initialized successfully. Table 'movies' is ready.")
        cur.close()
        conn.close()
    except Exception as e:
         print(f"Error initializing database: {e}")

if __name__ == "__main__":
    init_db()