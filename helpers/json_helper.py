import os
import json


def load(filename) -> None:
    if not os.path.isfile(filename):
        print(f"'{filename}' not found, using empty data...")
        return {}
    else:
        with open(filename, encoding="utf-8") as file:
            return json.load(file)


def save(data, filename) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        file.seek(0)
        json.dump(data, file, indent=4)
