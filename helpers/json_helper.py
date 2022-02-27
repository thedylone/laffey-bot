import os
import json

def load() -> None:
    if not os.path.isfile("playerData.json"):
        print("'playerData.json' not found, using empty data...")
        return {}
    else:
        with open("playerData.json", encoding='utf-8') as file:
            return json.load(file)

def save(data) -> None:
    with open("playerData.json", "w", encoding='utf-8') as file:
        file.seek(0)
        json.dump(data, file, indent=4)