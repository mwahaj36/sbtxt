import os
import json
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
#setup
load_dotenv()
DATABASE_URL=os.getenv("DATABASE_URL")

def upload_movies():
    conn=psycopg2.connect(DATABASE_URL)
    cur=conn.cursor()

    # 1. Clean start (Note: init_db.py also drops the table)
    print("Truncating table to start fresh...")
    cur.execute("TRUNCATE TABLE movies;")
    conn.commit()

    batch_size=2000 # Increased batch size for even more speed
    batch=[]
    
    # ULTRA-LEAN INSERTION QUERY
    inser_query="""
    INSERT INTO movies (id, title, poster_path, embedding)
    VALUES %s
    ON CONFLICT (id) DO UPDATE SET
        title=EXCLUDED.title,
        poster_path=EXCLUDED.poster_path;
    """
    total_count=0
    
    print("Starting data upload...")
    with open("movies_data.jsonl","r",encoding="utf-8") as f:
        for line in f:
            movie=json.loads(line)
            
            # Only keeping the bare essentials
            data=(
                movie.get('id'),
                movie.get('title'),
                movie.get('poster_path'),
                None # Embedding placeholder
            )
            
            batch.append(data)
            if len(batch)>=batch_size:
                execute_values(cur,inser_query,batch)
                conn.commit()
                total_count += len(batch)
                print(f"Uploaded {total_count} movies...")
                batch=[]
        
        if batch:
            execute_values(cur,inser_query,batch)
            conn.commit()
            total_count += len(batch)
            print(f"Final batch uploaded. Total: {total_count}")

        cur.close()
        conn.close()
        print(f"Done. {total_count} movies have been imported.")

      
if __name__ == "__main__":
    upload_movies()  
