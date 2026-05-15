import search_v5
import search_v6
import time

def run_comparison(query):
    print(f"\n" + "="*50)
    print(f"QUERY: {query}")
    print("="*50)

    # --- RUN V5 (THE BRAIN) ---
    print("\n[V5] Running Master Engine (200 candidates)...")
    start_v5 = time.time()
    results_v5 = search_v5.search(query, num_results=10)
    v5_time = (time.time() - start_v5) * 1000
    
    # --- RUN V6 (THE EDGE) ---
    print("[V6] Running Edge Engine (100 candidates / Top 40 Funnel)...")
    results_v6, metrics_v6 = search_v6.search(query, num_results=10)
    v6_time = metrics_v6["total_ms"]

    # --- DISPLAY RESULTS ---
    print("\n" + "-"*20 + " RESULTS COMPARISON " + "-"*20)
    print(f"{'#':<3} | {'V5 (MASTER)':<30} | {'V6 (EDGE)':<30}")
    print("-" * 70)
    
    overlap = 0
    v5_titles = [r['title'] for r in results_v5]
    v6_titles = [r['title'] for r in results_v6]
    
    for i in range(10):
        t5 = v5_titles[i] if i < len(v5_titles) else ""
        t6 = v6_titles[i] if i < len(v6_titles) else ""
        print(f"{i+1:<3} | {t5:<30} | {t6:<30}")
        if t6 in v5_titles: overlap += 1

    # --- COST ANALYSIS ---
    print("\n" + "-"*20 + " COMPUTATION COST " + "-"*20)
    print(f"V5 Total Latency: {v5_time:.0f}ms")
    print(f"V6 Total Latency: {v6_time:.0f}ms")
    print(f"Speed Improvement: {(v5_time/v6_time):.1f}x faster")
    print(f"Quality Retention: {(overlap/10)*100:.0f}%")
    
    print("\n[V6 Breakdown]")
    for k, v in metrics_v6.items():
        if k != "total_ms":
            print(f" - {k:<15}: {v:>4}ms ({(v/v6_time)*100:>2.0f}%)")

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
