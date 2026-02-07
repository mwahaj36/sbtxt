Subtext

Don't search by genre. Search by feeling.

Subtext is a semantic movie discovery engine. unlike traditional movie databases that rely on rigid tags ("Action", "Comedy"), Subtext uses Vector Embeddings and Cosine Similarity to understand the underlying "vibe" of a query.

It allows users to search for "a lonely sci-fi movie about memory" and get Eternal Sunshine of the Spotless Mind or Blade Runner 2049—results based on mathematical proximity in latent space, not just keyword matching.

⚡ The Stack

We use a hybrid architecture to combine the best modern web framework with the best AI ecosystem.

Frontend: Next.js 15 (App Router), Tailwind CSS, Shadcn/UI.

Backend: FastAPI (Python).

Database: Supabase (PostgreSQL + pgvector).

AI/ML: sentence-transformers (HuggingFace), running locally or on-server.

Data Source: TMDB API.

🛠️ Prerequisities

Before you start, ensure you have the following installed:

Node.js v18+

Python 3.9+

Git

🚀 Quick Start

This is a monorepo. You will need two terminal windows running simultaneously.

1. The Database (Supabase)

Create a free project at database.new.

Go to the SQL Editor and run the following to enable vector search:

create extension vector;

create table movies (
  id bigint primary key generated always as identity,
  title text not null,
  overview text,
  embedding vector(384) -- Dimension for 'all-MiniLM-L6-v2'
);


2. The Backend (Python)

Terminal 1

cd backend

# Create and activate virtual environment
python -m venv venv
# Windows: .\venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload


The Brain is now online at http://127.0.0.1:8000

3. The Frontend (Next.js)

Terminal 2

cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev


The Face is now online at http://localhost:3000

🧬 Environment Variables

Create a .env file in the backend/ directory:

SUPABASE_URL="your_supabase_url"
SUPABASE_KEY="your_supabase_anon_key"
TMDB_API_KEY="your_tmdb_key"


🗺️ Roadmap

[ ] Phase 1: Data Ingestion Pipeline (TMDB -> Vector DB).

[ ] Phase 2: Basic Semantic Search (Text-to-Vector).

[ ] Phase 3: Letterboxd CSV Import.

[ ] Phase 4: Active Learning (User feedback loop).

🎨 Design System: "Electric Void"

Background: #0a0a0a (Neutral 950)

Accent: #d946ef (Fuchsia 500)

Typography: Sans-serif, tracking-wide.

Built with 🖤 by [Your Name]
