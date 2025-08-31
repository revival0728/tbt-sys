import json
from random import randint

ranking = ["A", "韓", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"]
compiled_ranking = []

for r in ranking:
    compiled_ranking.append({
        'nickname': r,
        'tw_match': randint(0, 10),
        'tw_game': randint(0, 30),
        'tl_game': randint(0, 30),
        'tw_point': randint(0, 100),
        'tl_point': randint(0, 100),
    })

with open("data/ranking.txt", "w", encoding="utf-8") as f:
    f.write(json.dumps({'ranking': compiled_ranking}) + "\n")