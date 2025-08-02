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

def update_pair_tracking(passed_pairs: List[dict]) -> List[dict]:
    data = load_json(TRACKED_FILE)
    updated_data = {}
    current_ids = set()

    alerts = []

    for pair in passed_pairs:
        pair_id = pair.get("pairAddress")
        if not pair_id:
            continue

        current_ids.add(pair_id)

        if pair_id in data:
            pair["count"] = data[pair_id].get("count", 0) + 1
        else:
            pair["count"] = 1

        updated_data[pair_id] = pair

        if pair["count"] >= COUNT_THRESHOLD:
            alerts.append(pair)

    # Decrement count or remove for missing pairs
    for old_id, old_data in data.items():
        if old_id not in current_ids:
            old_count = old_data.get("count", 0)
            if old_count > 1:
                old_data["count"] = old_count - 1
                updated_data[old_id] = old_data

    save_json(TRACKED_FILE, updated_data)
    return alerts
