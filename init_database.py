import json
data = {'A': 100, 'B': 100, 'C': 100}
with open('data.json', 'w') as fp:
    json.dump(data, fp)

