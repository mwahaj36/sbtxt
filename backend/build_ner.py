import json

def build_people_index():
    print("Building Named Entity Recognition (NER) index for all actors and directors...")
    people = set()
    
    with open('movies_data.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            
            # Top 10 Cast
            cast = data.get("credits", {}).get("cast", [])
            for member in cast[:10]:
                name = member.get("name", "").lower()
                # Only keep full names (2+ words) to prevent false positives like "Bob"
                if len(name.split()) >= 2:
                    people.add(name)
                    
            # Directors & Writers
            crew = data.get("credits", {}).get("crew", [])
            for member in crew:
                if member.get("job") in ["Director", "Screenplay", "Writer"]:
                    name = member.get("name", "").lower()
                    if len(name.split()) >= 2:
                        people.add(name)
                        
    # Save to a quick-load JSON file
    with open('people_index.json', 'w', encoding='utf-8') as f:
        json.dump(list(people), f)
        
    print(f"Successfully indexed {len(people)} unique Hollywood names!")

if __name__ == "__main__":
    build_people_index()
