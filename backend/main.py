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
    version="1.0"
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
async def get_movies(q:str=Query(..., description="The actual Query"),
year_min: Optional[int]=None,
year_max: Optional[int]=None,
language: Optional[int]=None,
vote_min: Optional[int]=None




):
    filters={
        "year_min":year_min,
        "year_max":year_max,
        "language":language,
        "vote_min":vote_min

    }
    filters={k:v for k,v in filters.items() if v is not None} #clean up filters, no need to pass if none
    results = search(q, filters=filters) 
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

if __name__=="__main__":
    uvicorn.run("main:app",host="127.0.0.1",port=8000,reload=True)

