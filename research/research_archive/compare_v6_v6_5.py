import sys
import os
import time
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.abspath("../../backend"))

# Load environment before search imports
load_dotenv(os.path.abspath("../../backend/.env"))

import search_v6
import search_v6_5

def run_comparison(query):
    print(f"\n" + "="*80)
    print(f"QUERY: {query}")
    print("="*80)

    # --- RUN V6 (EDGE) ---
    print("\n[V6] Running Base Engine (100 candidates / Top 40 Funnel)...")
    start_v6 = time.time()
    results_v6, metrics_v6 = search_v6.search(query, num_results=10)
    v6_time = (time.time() - start_v6) * 1000
    
    # --- RUN V6.5 (STABILIZED) ---
    print("[V6.5] Running Stabilized Engine (Adaptive Tone Gating)...")
    start_v6_5 = time.time()
    results_v6_5, metrics_v6_5 = search_v6_5.search(query, num_results=10)
    v6_5_time = (time.time() - start_v6_5) * 1000

    # --- DISPLAY RESULTS ---
    print("\n" + "-"*30 + " RESULTS COMPARISON " + "-"*30)
    print(f"{'#':<3} | {'V6 (BASE)':<35} | {'V6.5 (STABILIZED)':<35}")
    print("-" * 80)
    
    overlap = 0
    v6_titles = [r['title'] for r in results_v6]
    v6_5_titles = [r['title'] for r in results_v6_5]
    
    for i in range(10):
        t6 = v6_titles[i] if i < len(v6_titles) else ""
        t6_5 = v6_5_titles[i] if i < len(v6_5_titles) else ""
        print(f"{i+1:<3} | {t6:<35} | {t6_5:<35}")
        if t6_5 in v6_titles: overlap += 1

    # --- COST ANALYSIS ---
    print("\n" + "-"*30 + " PERFORMANCE ANALYSIS " + "-"*30)
    print(f"V6 Total Latency:   {v6_time:.0f}ms")
    print(f"V6.5 Total Latency: {v6_5_time:.0f}ms")
    print(f"Stability Delta:    {((v6_5_time - v6_time)/v6_time)*100:+.1f}% latency overhead")
    print(f"Consistency:        {(overlap/10)*100:.0f}% overlap with base")
    
    # Specific Check for Drive in Ryan Gosling query
    if "ryan gosling" in query.lower():
        v6_has_drive = any("drive" in t.lower() for t in v6_titles)
        v6_5_has_drive = any("drive" in t.lower() for t in v6_5_titles)
        print(f"\n[DRIVE CHECK]")
        print(f" - V6 contains Drive:   {v6_has_drive}")
        print(f" - V6.5 contains Drive: {v6_5_has_drive}")

if __name__ == "__main__":
    test_queries = [
        "A movie about silence and isolation",
        "movies like la la land",
        "funny war movies",
        "a story about a man who forgets his past",
        "neon colors and futuristic cities",
        "heartbreaking but beautiful dramas",
        "ryan gosling in a quiet role",
        "space adventure",
        "the godfather part ii",
        "jazz music and crime"
    ]
    for q in test_queries:
        run_comparison(q)
