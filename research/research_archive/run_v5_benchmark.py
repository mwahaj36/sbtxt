import os
import sys
import json
from datetime import datetime
import search_v5

QUERIES = [
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

def run_v5_only():
    print(f"\n--- Running Subtext V5 (Adaptive Hybrid) Benchmark ---\n")
    
    for q_idx, query in enumerate(QUERIES):
        print(f"[{q_idx+1}/10] Query: '{query}'")
        try:
            results = search_v5.search(query, num_results=10)
            res_str = "<br>".join([f"{i+1}. {r['title']}" for i, r in enumerate(results)])
            
            print(f"| V5 (Adaptive Hybrid) | {res_str} | V5 Logic |")
            print("-" * 30)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_v5_only()
