import json

from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

with open("conf.json", 'r') as config:
    REPOS = dict(json.load(config))
