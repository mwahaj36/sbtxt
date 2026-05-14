from fastapi import FastAPI,Query,Depends,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import uvicorn
import jwt
import os
import auth

from search import search
import movie
import sync
import taste as taste_module

from contextlib import asynccontextmanager
from database import get_db_connection
import database

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
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS taste_vector FLOAT8[];")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS taste_vector_updated_at TIMESTAMPTZ;")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS taste_vector_movie_count INT DEFAULT 0;")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS taste_top_genres TEXT;")
                
                # Performance Index for Profile/Library
                cur.execute("CREATE INDEX IF NOT EXISTS idx_user_ratings_profile ON user_ratings (user_id, interaction_type, watched_date DESC NULLS LAST, id DESC);")
                
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
    version="1.4",
    lifespan=lifespan,
    redirect_slashes=True # This will handle /auth/login and /auth/login/
)

# Debug endpoint to see all registered routes
@app.get("/debug/routes")
def get_all_routes():
    return [{"path": route.path, "name": route.name, "methods": list(route.methods)} for route in app.routes]

# Move these UP before other logic
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

# Optional auth — returns user_id if token present, None otherwise
optional_security = HTTPBearer(auto_error=False)

def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)):
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        return payload.get("sub")
    except:
        return None

#search page api
@app.get("/search")
async def get_movies(
    q: str = Query("", description="The actual Query"),
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    language: Optional[str] = None,
    min_vote: Optional[float] = None,
    k: int = 10,
    taste_blend: Optional[float] = None,
    watchlist_only: Optional[bool] = False,
    user_id: Optional[str] = Depends(get_optional_user),
):
    # Fetch taste vector and watched history if personalization requested
    taste_vector = None
    watchlist_ids = None
    exclude_ids = None
    user_top_genres = None
    
    if user_id:
        # Get watched/liked movies to exclude from "For You"
        conn = database.get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    # 1. Fetch Watched history to exclude (watched + rated)
                    cur.execute(
                        "SELECT tmdb_id FROM user_ratings WHERE user_id = %s AND interaction_type IN ('watched', 'rated') AND tmdb_id IS NOT NULL",
                        (user_id,)
                    )
                    exclude_ids = [str(row[0]) for row in cur.fetchall()]
                    
                    # 2. Fetch Watchlist if requested
                    if watchlist_only:
                        cur.execute(
                            "SELECT tmdb_id FROM user_ratings WHERE user_id = %s AND interaction_type = 'watchlist' AND tmdb_id IS NOT NULL",
                            (user_id,)
                        )
                        watchlist_ids = [str(row[0]) for row in cur.fetchall()]
            finally:
                conn.close()

        if taste_blend and taste_blend > 0:
            taste_data = await taste_module.get_taste_vector(user_id)
            if taste_data:
                taste_vector = taste_data["vector"]
                user_top_genres = taste_data.get("top_genres")
    
    # Discovery mode
    results = search(
        q,
        k=k,
        min_year=min_year,
        max_year=max_year,
        language=language,
        min_vote=min_vote,
        taste_vector=taste_vector,
        taste_blend=1.0 if not q.strip() and taste_vector is not None else taste_blend,
        watchlist_ids=watchlist_ids,
        exclude_ids=exclude_ids,
        user_top_genres=user_top_genres
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

