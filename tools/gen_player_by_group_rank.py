import json
import os

ranking_str = ""

with open(os.path.join('data', 'ranking.txt'), 'r', encoding='utf-8') as f:
    ranking_str = f.readlines()[-1]

ranking = json.loads(ranking_str).get('ranking', [])

players = [
    {'nickname': ranking[0]['nickname']},
    {'nickname': ranking[3]['nickname']},
    {'nickname': ranking[1]['nickname']},
    {'nickname': ranking[4]['nickname']}
]

print(json.dumps(players))
