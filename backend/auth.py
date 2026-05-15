from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import json
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
import psycopg2
from database import get_db_connection
import jwt
from datetime import datetime,timedelta,timezone
import os
from dotenv import load_dotenv

load_dotenv()



router=APIRouter()
pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
SECRET_KEY=os.getenv("JWT_SECRET_KEY")
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60*24*30

class userCreate(BaseModel):
    email: str
    password: str
    username:str
    letterboxd_username: str=None

class userLogin(BaseModel):
    identifier:str
    password: str

class ProfileUpdateRequest(BaseModel):
    username: str = None
    email: str = None
    letterboxd_username: str = None

def create_access_token(data:dict):
    to_encode=data.copy()

    expire=datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})

    encodedd_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encodedd_jwt


@router.post("/signup")
def signup(user: userCreate):
    hashed_pwd=pwd_context.hash(user.password)
    
    conn=get_db_connection()
    if not conn:
        raise HTTPException(status_code=500,detail="Database connection failed")
    cursor=conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (email,username,hashed_password,letterboxd_username)
            VALUES(%s,%s,%s,%s) RETURNING id
            """,
            (user.email,user.username,hashed_pwd,user.letterboxd_username)
        )
        new_user_id=cursor.fetchone()[0]
        conn.commit()

        # Generate token for auto-login
        access_token = create_access_token(data={"sub": str(new_user_id)})

        return{
            "message":"User birthed succesfully",
            "access_token": access_token,
            "token_type": "bearer",
            "user_id":new_user_id
        }
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400,detail="Email already registered")
    finally:
        cursor.close()
        conn.close()

@router.post("/login")
def login(user_credentials:userLogin):

    conn=get_db_connection()
    if not conn:
        raise HTTPException(status_code=500,detail="Database Connection Failed")
    cursor=conn.cursor()

    cursor.execute(
        """
        SELECT id,hashed_password FROM users where email=%s OR username=%s
        """,
        (user_credentials.identifier,user_credentials.identifier))

    db_user=cursor.fetchone()
    cursor.close()
    conn.close()

    if not db_user:
        raise HTTPException(status_code=400,detail="Invalid Credentials")
    
    if not pwd_context.verify(user_credentials.password,db_user[1]):
        raise HTTPException(status_code=400,detail="invalid password")

    access_token = create_access_token(data={"sub": str(db_user[0])})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": db_user[0]
    }

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

class PreferenceRequest(BaseModel):
    vibes: list[str]

@router.post("/preferences")
async def save_preferences(
    req: PreferenceRequest,
    user_id: str = Depends(get_current_user)
):
    # This is where we will later trigger the Taste DNA vector calculation
    print(f"User {user_id} selected vibes: {req.vibes}")
    return {"status": "success", "message": "Preferences saved"}
@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username, email, letterboxd_username, letterboxd_dp FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return {
                "id": user_id,
                "username": user[0],
                "email": user[1],
                "letterboxd_username": user[2],
                "letterboxd_dp": user[3]
            }
    finally:
        conn.close()

@router.put("/update")
async def update_profile(
    req: ProfileUpdateRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            updates = []
            params = []
            if req.username is not None:
                updates.append("username = %s")
                params.append(req.username)
            if req.email is not None:
                updates.append("email = %s")
                params.append(req.email)
            if req.letterboxd_username is not None:
                updates.append("letterboxd_username = %s")
                params.append(req.letterboxd_username)
            
            if not updates:
                return {"status": "success", "message": "Nothing to update"}

            query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
            params.append(user_id)
            
            cur.execute(query, params)
            conn.commit()

            # If Letterboxd username was updated, trigger a live sync
            if req.letterboxd_username:
                try:
                    from sync import sync_live_history
                    background_tasks.add_task(sync_live_history, req.letterboxd_username, user_id)
                except Exception as e:
                    print(f"Error triggering sync: {e}")

            return {"status": "success", "message": "Profile updated successfully"}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Username or email already taken")
    finally:
        conn.close()

@router.get("/taste")
async def get_taste_status(user_id: str = Depends(get_current_user)):
    """Returns taste vector metadata."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT taste_vector_updated_at, taste_vector_movie_count, taste_top_genres FROM users WHERE id = %s",
                (user_id,)
            )
            row = cur.fetchone()
            if not row or not row[0]:
                return {
                    "has_taste_vector": False,
                    "movie_count": 0,
                    "last_updated": None,
                    "top_genres": [],
                }
            
            top_genres = row[2]
            if isinstance(top_genres, str):
                try:
                    top_genres = json.loads(top_genres)
                except:
                    top_genres = []
            
            return {
                "has_taste_vector": True,
                "movie_count": row[1] or 0,
                "last_updated": row[0].isoformat() if row[0] else None,
                "top_genres": top_genres or [],
            }
    finally:
        conn.close()

@router.post("/taste/refresh")
async def force_taste_refresh(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """Manual taste vector refresh."""
    from taste import refresh_taste_vector_bg
    background_tasks.add_task(refresh_taste_vector_bg, user_id)
    return {"status": "refreshing"}

@router.get("/bundle")
async def get_profile_bundle(user_id: str = Depends(get_current_user)):
    """The 'Turbo' endpoint: Fetches profile, taste DNA, and initial library in one connection."""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        with conn.cursor() as cur:
            # 1. Fetch Profile Info
            cur.execute("SELECT username, email, letterboxd_username, avatar_url, bio, letterboxd_films_count, favorites FROM users WHERE id = %s", (user_id,))
            u = cur.fetchone()
            if not u: raise HTTPException(status_code=404, detail="User not found")
            
            favs = u[6]
            if isinstance(favs, str): favs = json.loads(favs)

            profile = {
                "id": user_id,
                "username": u[0],
                "email": u[1],
                "letterboxd_username": u[2],
                "avatar": u[3],
                "bio": u[4],
                "films_count": u[5],
                "favorites": favs or []
            }

            # 2. Fetch Taste DNA
            cur.execute("SELECT taste_vector_updated_at, taste_vector_movie_count, taste_top_genres FROM users WHERE id = %s", (user_id,))
            t = cur.fetchone()
            taste = {
                "has_taste_vector": bool(t and t[0]),
                "movie_count": t[1] if t else 0,
                "last_updated": t[0].isoformat() if t and t[0] else None,
                "top_genres": json.loads(t[2]) if t and t[2] else []
            }

            # 3. Fetch Top 8 Recent (for the identity card)
            cur.execute("""
                SELECT movie_title, release_year, tmdb_id, poster_path, rating, is_liked 
                FROM user_ratings 
                WHERE user_id = %s AND interaction_type = 'watched' 
                ORDER BY watched_date DESC NULLS LAST, id DESC LIMIT 8
            """, (user_id,))
            recent = [{"title": r[0], "year": r[1], "tmdb_id": r[2], "poster_path": r[3], "rating": float(r[4]) if r[4] else None, "is_liked": r[5]} for r in cur.fetchall()]

            return {
                "profile": profile,
                "taste": taste,
                "recent": recent
            }
    finally:
        conn.close()
@router.delete("/delete")
async def delete_user(user_id: str = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Delete associated ratings
            cur.execute("DELETE FROM user_ratings WHERE user_id = %s", (user_id,))
            # Delete user account
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            return {"status": "success", "message": "User and all associated data purged successfully"}
    finally:
        conn.close()
