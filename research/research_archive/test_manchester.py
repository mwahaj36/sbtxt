from search_v3 import search

r = search("Manchester by the Sea")
for i, x in enumerate(r):
    print(f"{i+1}. {x['title']} (Score: {x['score']:.2f})")
