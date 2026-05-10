import os 
import json
import re
from astrapy import DataAPIClient
from dotenv import load_dotenv


#initialize db
load_dotenv()
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
collection = db.get_collection("movies")

#return movie info from database
def movie_info(movie:str):
    return collection.find_one({"_id":movie})

#return recommendations
def get_recommendations(movie:str):
    current_movie=collection.find_one({"_id":movie},projection={"$vector": True, "genres": True} )
    if not current_movie or "$vector" not in current_movie:
        return[]
    else:
        original_genres = set(current_movie.get("genres", []))
        results=collection.find(
            sort={"$vector":current_movie["$vector"]},
            limit=20,
            include_similarity=True
        )

        recommendations=[]
        for doc in results:
            if doc["_id"]==movie:
                continue
            vibe_score=doc.get("$similarity",0)
            doc_genres=set(doc.get("genres",[]))

            shared_genres = original_genres.intersection(doc_genres)
            extra_genres = doc_genres.difference(original_genres) 
            
            genre_punish = len(extra_genres) * -0.2 #we punish if the genre has smth else than our original
            genre_boost = len(shared_genres) * 0.1 # we boost if they share genre too
            final_score = vibe_score + genre_boost + genre_punish
            recommendations.append({
                "id": doc["_id"],
                "title": doc.get("title"),
                "genres": doc.get("genres"),
                "release_year":doc.get("release_year"),
                "shared": list(shared_genres),
                "final_score": final_score,
                "similarity": vibe_score
            })
        recommendations.sort(key=lambda x: x["final_score"], reverse=True)
        return recommendations[:5]