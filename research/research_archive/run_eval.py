import json
import time
from search_eval import search

queries = [
    # 1. Exact Title Matches (10)
    "Inception", "The Dark Knight", "A Ghost Story", "Manchester by the Sea",
    "The Matrix", "Pulp Fiction", "Interstellar", "Gladiator", "The Godfather", "Titanic",
    
    # 2. Actor + Vibe (20)
    "casey affleck playing a ghost",
    "leonardo dicaprio in a dream heist",
    "keanu reeves stopping a bus bomb",
    "tom hanks stranded on an island",
    "matthew mcconaughey in space",
    "christian bale as a vigilante",
    "ryan gosling driving a getaway car",
    "joaquin phoenix descending into madness",
    "brad pitt in a fight club",
    "tom cruise doing crazy stunts",
    "harrison ford hunting replicants",
    "marlon brando in the mafia",
    "al pacino cuban drug lord",
    "robert de niro driving a taxi",
    "sigourney weaver fighting aliens",
    "natalie portman as a ballerina",
    "anthony hopkins as a cannibal",
    "russell crowe as a gladiator",
    "morgan freeman in prison",
    "scarlett johansson lost in tokyo",

    # 3. Genre / Concept Blend (Multi-Intent) (25)
    "romantic comedy but with zombies",
    "heist movie in space",
    "a western but set in the future",
    "musical horror movie",
    "time travel romance",
    "post apocalyptic road trip",
    "samurai movie in modern times",
    "a comedy about vampires sharing a flat",
    "war movie with comedy elements",
    "detective noir in a sci-fi city",
    "a superhero movie but it's dark and gritty",
    "alien invasion but from the aliens perspective",
    "a high school comedy that is actually a tragedy",
    "a mockumentary about folk music",
    "a heist movie where they steal dreams",
    "a horror movie where sound is dangerous",
    "a romance where they erase their memories",
    "a sports movie about chess",
    "a fantasy movie without any magic",
    "a war movie that has no fighting",
    "a road trip movie with a corpse",
    "a sci fi movie about linguistics",
    "a horror movie that takes place entirely on a computer screen",
    "a comedy about a hitman becoming an actor",
    "a romantic movie where they never meet",

    # 4. Plot Specifics (25)
    "a guy who loses his memory every 15 minutes",
    "a rat that knows how to cook in paris",
    "a theme park where dinosaurs escape",
    "a computer hacker discovers reality is a simulation",
    "a man is trapped in a snow globe town where his life is a tv show",
    "a family goes to a hotel for the winter and the dad goes crazy",
    "a group of friends play a game that comes to life",
    "a young wizard goes to a magic school",
    "a clown terrorizes a small town in maine",
    "a teenager goes back in time and meets his parents",
    "an archeologist hunts for the ark of the covenant",
    "a green ogre rescues a princess with a talking donkey",
    "a boy finds an alien and hides it in his closet",
    "a cop is transferred to a peaceful village that has a dark secret",
    "a man creates a social network and loses his friends",
    "a jazz drummer is pushed to the edge by his teacher",
    "a hitman protects a 12 year old girl",
    "a man builds a suit of armor in a cave with a box of scraps",
    "a fish looks for his missing son across the ocean",
    "a billionaire dresses up as a bat",
    "a robot is sent from the future to protect a boy",
    "a hobbit has to destroy a ring in a volcano",
    "a girl enters a magical spirit world to save her parents who turned into pigs",
    "a poor family infiltrates a rich family's house",
    "a man falls in love with his operating system",

    # 5. Pure Vibe / Abstract (20)
    "a movie about the crushing weight of existence",
    "neon lit cyberpunk dystopian thriller",
    "a slow burn atmospheric psychological thriller",
    "feel good summer movie about friendship",
    "an extremely claustrophobic and tense experience",
    "a visually stunning exploration of the cosmos",
    "a gritty realistic look at the criminal underworld",
    "a heartwarming tale of overcoming adversity",
    "a mind bending surreal trip",
    "a deeply unsettling and disturbing horror",
    "a nostalgic love letter to the 1980s",
    "a laugh out loud absurd comedy",
    "an epic sweeping historical drama",
    "a quiet intimate character study",
    "a high octane adrenaline fueled action ride",
    "a bleak and depressing look at the future",
    "a whimsical and quirky fairy tale",
    "a gripping courtroom drama",
    "a suspenseful whodunit murder mystery",
    "a coming of age story about suburban angst"
]

results_dict = {}

print(f"Starting evaluation on {len(queries)} queries...")

for i, q in enumerate(queries):
    print(f"[{i+1}/{len(queries)}] {q}")
    try:
        res = search(q, num_results=10) # top 10 results
        results_dict[q] = res
    except Exception as e:
        print(f"Error on {q}: {e}")
        results_dict[q] = {"error": str(e)}

with open("eval_results.json", "w") as f:
    json.dump(results_dict, f, indent=2)

print("Evaluation complete! Results saved to eval_results.json")
