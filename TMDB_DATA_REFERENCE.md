# 📚 TMDB Data Reference Sheet

This document serves as a guide for handling TMDB data within **Subtext**, specifically for transforming raw API responses into usable Frontend assets.

---

## 🖼️ Image Handling (Posters & Backdrops)
TMDB returns relative paths (e.g., `/xXyYzZ.jpg`). To display them, you must prefix them with the TMDB Image CDN URL.

### Base URL: `https://image.tmdb.org/t/p/`

| Type | Recommended Size | Full URL Example |
| :--- | :--- | :--- |
| **Poster** | `w500` | `https://image.tmdb.org/t/p/w500/path.jpg` |
| **Thumbnail** | `w200` | `https://image.tmdb.org/t/p/w200/path.jpg` |
| **Backdrop** | `original` | `https://image.tmdb.org/t/p/original/path.jpg` |
| **Profile** (Actor) | `h632` | `https://image.tmdb.org/t/p/h632/path.jpg` |

---

## 🎬 Video Handling (Trailers)
When using `append_to_response=videos`, the response contains a `results` list of video objects.

### YouTube Logic:
*   **Base URL:** `https://www.youtube.com/watch?v=`
*   **Key:** Found in `movie['videos']['results'][0]['key']`
*   **Full URL:** `https://www.youtube.com/watch?v={key}`

---

## 🧠 Scraper Data Structure
We are currently scraping with the following parameters:
`append_to_response=keywords,credits,recommendations,videos,images`

### Key Data Locations:
*   **Vibe Keywords:** `movie['keywords']['keywords']` (List of name/id pairs)
*   **Director:** Found in `movie['credits']['crew']` where `job == "Director"`.
*   **Main Cast:** Top actors are in `movie['credits']['cast']`.
*   **Similar Vibes:** `movie['recommendations']['results']`.

---

## 💡 Industry Tips
1.  **Fallbacks:** Not every movie has a trailer or backdrop. Always implement a "Placeholder" image in the Frontend.
2.  **Lazy Loading:** Always lazy-load images to keep the Next.js site fast.
3.  **Caching:** We save the raw JSON to `movies_data.jsonl` to avoid hitting the TMDB API rate limits during development.
