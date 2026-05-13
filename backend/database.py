import os
import psycopg2
from dotenv import load_dotenv

# Load your .env variables
load_dotenv()

# Get the Neon connection string
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Opens a connection to the Neon database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print("Database connection failed:", e)
        return None
