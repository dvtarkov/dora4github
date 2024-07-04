import json

with open("conf.json", 'r') as config:
    REPOS = dict(json.load(config))
