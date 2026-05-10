"""
Phase 1: Enrich AstraDB with Keywords + Tagline from local JSONL data.

Reads paper/data/movies_data.jsonl, extracts keywords[] and tagline for each movie,
and pushes them to AstraDB as new stored fields. Supports resume via checkpoint file.

Usage:
    python enrich_keywords.py
"""

import os
import sys
import json
import time
from dotenv import load_dotenv
from astrapy import DataAPIClient
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

load_dotenv()

ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "paper", "data", "movies_data.jsonl")
CHECKPOINT_FILE = os.path.join(os.path.dirname(__file__), "enrich_checkpoint.txt")
TOTAL_MOVIES = 99186  # From inspection — avoids counting a 3GB file

# ─── Progress Bar ───────────────────────────────────────────────────────────

class ProgressBar:
    """Compact terminal progress bar with ETA and speed."""
    def __init__(self, total):
        self.total = total
        self.current = 0
        self.start_time = time.time()
        self.lock = Lock()
        self.errors = 0

    def update(self, n=1, error=False):
        with self.lock:
            self.current += n
            if error:
                self.errors += n
            self._render()

    def _render(self):
        elapsed = time.time() - self.start_time
        speed = self.current / elapsed if elapsed > 0 else 0
        eta_s = (self.total - self.current) / speed if speed > 0 else 0
        eta_m = eta_s / 60

        pct = self.current / self.total * 100
        bar_len = 30
        filled = int(bar_len * self.current / self.total)
        bar = "█" * filled + "░" * (bar_len - filled)

        err_str = f" | Errors: {self.errors}" if self.errors > 0 else ""
        sys.stdout.write(
            f"\r  {bar} {pct:5.1f}% | {self.current:,}/{self.total:,} | "
            f"{speed:.0f}/s | ETA: {eta_m:.1f}m{err_str}   "
        )
        sys.stdout.flush()

    def finish(self):
        elapsed = time.time() - self.start_time
        print(f"\n  Done in {elapsed/60:.1f} min. "
              f"Updated: {self.current - self.errors:,} | Errors: {self.errors:,}")


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(DATA_PATH):
        print(f"ERROR: Data file not found at {DATA_PATH}")
        sys.exit(1)

    # Resume support
    start_offset = 0
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            start_offset = int(f.read().strip())
        print(f"  Resuming from line {start_offset:,}")

    # Connect to AstraDB
    print("  Connecting to AstraDB...")
    client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
    db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
    collection = db.get_collection("movies")
    print("  Connected.\n")

    progress = ProgressBar(TOTAL_MOVIES - start_offset)
    checkpoint_lock = Lock()

    def update_movie(movie_id, keywords, tagline):
        """Update a single movie in AstraDB with keywords + tagline."""
        try:
            collection.find_one_and_update(
                {"_id": str(movie_id)},
                {"$set": {"keywords": keywords, "tagline": tagline}}
            )
            return True
        except Exception as e:
            return False

    # Process in batches using thread pool
    WORKERS = 20
    CHECKPOINT_INTERVAL = 500  # Save progress every N movies

    print(f"  Starting enrichment ({WORKERS} workers)...\n")

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = []
        processed = 0

        with open(DATA_PATH, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                # Skip already-processed lines
                if i < start_offset:
                    continue

                try:
                    movie = json.loads(line)
                except json.JSONDecodeError:
                    progress.update(1, error=True)
                    continue

                movie_id = movie.get("id")
                if not movie_id:
                    progress.update(1, error=True)
                    continue

                # Extract keywords as flat list of strings
                raw_keywords = movie.get("keywords", {})
                if isinstance(raw_keywords, dict):
                    kw_list = [k["name"] for k in raw_keywords.get("keywords", []) if "name" in k]
                else:
                    kw_list = []

                tagline = movie.get("tagline", "") or ""

                # Submit to thread pool
                future = executor.submit(update_movie, movie_id, kw_list, tagline)
                futures.append((future, i))

                # Collect completed futures periodically to avoid memory bloat
                if len(futures) >= WORKERS * 10:
                    for fut, line_num in futures:
                        success = fut.result()
                        progress.update(1, error=not success)
                        processed += 1

                    # Checkpoint
                    if processed % CHECKPOINT_INTERVAL < WORKERS * 10:
                        with checkpoint_lock:
                            with open(CHECKPOINT_FILE, "w") as cf:
                                cf.write(str(i + 1))

                    futures = []

        # Drain remaining futures
        for fut, line_num in futures:
            success = fut.result()
            progress.update(1, error=not success)

    # Final checkpoint
    with open(CHECKPOINT_FILE, "w") as cf:
        cf.write(str(TOTAL_MOVIES))

    progress.finish()

    # Quick verification
    print("\n  ── Verification ──")
    for title in ["La La Land", "Singin' in the Rain", "The Umbrellas of Cherbourg"]:
        doc = collection.find_one(
            filter={"title": title},
            projection={"title": 1, "keywords": 1, "tagline": 1}
        )
        if doc:
            kw = doc.get("keywords", [])
            tg = doc.get("tagline", "")
            print(f"  ✓ {title}")
            print(f"    Keywords: {kw[:6]}{'...' if len(kw) > 6 else ''}")
            print(f"    Tagline:  {tg[:80]}")
        else:
            print(f"  ✗ {title} — not found in DB")

    print("\n  Phase 1 complete.")


if __name__ == "__main__":
    print("\n╔══════════════════════════════════════════════════╗")
    print("║  SUBTEXT Phase 1: Keyword & Tagline Enrichment  ║")
    print("╚══════════════════════════════════════════════════╝\n")
    main()
