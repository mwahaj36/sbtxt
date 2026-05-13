# ⚙️ Subtext Backend: The Sync Engine

The Subtext backend is a high-performance FastAPI application responsible for Letterboxd synchronization, user authentication, and latent taste calculation.

## 🚀 Core Systems

### 1. The Stealth Sync Engine (`sync.py`)
This is the heart of the platform's data ingestion. It handles the extraction and mapping of Letterboxd ZIP exports into structured SQL data.
- **Concurrency Control**: Limited to 4 parallel workers to respect Letterboxd rate limits.
- **User-Agent Rotation**: Cycles through a list of modern browser agents to avoid fingerprinting.
- **Global Mappings Cache**: Stores `letterboxd_url` -> `tmdb_id` relationships globally to eliminate redundant scraping for all users.

### 2. Authentication System (`auth.py`)
- **JWT-Based**: Secure session management using JSON Web Tokens.
- **Profile Integration**: Automatically fetches Letterboxd avatars and bios during onboarding.

## 🛠️ Database Schema

### `users`
Core user identity and Letterboxd profile metadata.

### `letterboxd_mappings`
The "Cinematic Map." A global lookup table for mapping Letterboxd URLs to TMDB IDs.
- Columns: `letterboxd_url`, `tmdb_id`, `title`, `year`.

### `user_ratings`
The "Taste DNA" source data. Stores every movie a user has watched, rated, or liked.
- Columns: `user_id`, `tmdb_id`, `rating`, `is_liked`, `interaction_type` (watched/watchlist).

## 🔑 Environment Variables

Required variables for `main.py`:
- `DATABASE_URL`: Your Postgres connection string (Neon.tech recommended).
- `JWT_SECRET_KEY`: A secure string for signing tokens.

## 🏃 Running Locally

1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env`
3. Launch: `python main.py`
