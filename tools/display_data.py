import json
import os

bucket = "matches"

with open(os.path.join('data', f"{bucket}.txt"), 'r') as f:
  data = f.read()
  for line in data.splitlines():
    print(json.loads(line))