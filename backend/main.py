from fastapi import FastAPI,Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
import auth

from search import search
import movie
import sync

from contextlib import asynccontextmanager
from database import get_db_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Migration Check
    print("Checking database schema...")
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("ALTER TABLE letterboxd_mappings ADD COLUMN IF NOT EXISTS poster_path TEXT;")
                cur.execute("ALTER TABLE user_ratings ADD COLUMN IF NOT EXISTS poster_path TEXT;")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS letterboxd_films_count TEXT;")
                conn.commit()
            print("Database schema verified.")
        except Exception as e:
            print(f"Migration error: {e}")
        finally:
            conn.close()
    yield

#initialize app
app=FastAPI(
    title="Subtext",
    description="Vector based discovery engine",
    version="1.2",
    lifespan=lifespan
)

app.include_router(auth.router,prefix="/auth",tags=["Authentication"])
app.include_router(sync.router,prefix="/sync",tags=["Letterboxd Sync"])
#implement middlewre
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

#search page api
@app.get("/search")
async def get_movies(
    q: str = Query(..., description="The actual Query"),
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    language: Optional[str] = None,
    min_vote: Optional[float] = None,
    k: int = 10 
):
    # Call the finalized search engine with advanced filter support
    results = search(
        q, 
        k=k, 
        min_year=min_year, 
        max_year=max_year, 
        language=language,
        min_vote=min_vote
    ) 
    return results


#movie details api
@app.get("/movies/{movie_id}")
async def get_movie(movie_id:str):
    movie_details=movie.movie_info(movie_id)
    return movie_details

#recommendations based on this movie
@app.get("/movies/{movie_id}/recommendations")
async def get_rec(movie_id:str):
    return movie.get_recommendations(movie_id)

#root
@app.get("/")
def read_root():
    return{"status":"Subtext is online"}

# V28.7 REFRESH
if __name__=="__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

