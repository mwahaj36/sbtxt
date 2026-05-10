from fastapi import FastAPI,Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn

from search import search
import movie

#initialize app
app=FastAPI(
    title="Subtext",
    description="Vector based discovery engine",
    version="1.2"
)

#implement middlewre
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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

