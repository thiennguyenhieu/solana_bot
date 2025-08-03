import json
import os
from typing import List
from pathlib import Path

TRACKED_FILE = Path("tracked_pairs.json")
COUNT_THRESHOLD = 5

def load_json(path):
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load {path}: {e}")
        return {}

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to save {path}: {e}")

def update_pair_tracking(passed_pairs, file_path="tracked_pairs.json", threshold=5):
    data = {}

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)

    updated_data = {}
    for pair in passed_pairs:
        pair_id = pair.get("pairAddress")
        if not pair_id:
            continue

        existing = data.get(pair_id, {})
        count = existing.get("count", 0) + 1
        pair["count"] = count
        updated_data[pair_id] = pair

    # Decrease count or remove for missing pairs
    for pair_id, old_pair in data.items():
        if pair_id not in updated_data:
            new_count = old_pair.get("count", 1) - 1
            if new_count > 0:
                old_pair["count"] = new_count
                updated_data[pair_id] = old_pair
            # else: dropped

    with open(file_path, "w") as f:
        json.dump(updated_data, f, indent=2)

    return updated_data  # Return full tracking data

