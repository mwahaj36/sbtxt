from fastapi import APIRouter, HTTPException, Depends
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
