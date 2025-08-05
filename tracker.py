import json
from pathlib import Path
from datetime import datetime
from screener import get_pair_details

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

def update_pair_tracking(passed_pairs, file_path="tracked_pairs.json"):
    """
    - Stores minimal state per pair: count + Rugcheck fields (+ timestamps).
    - Increments count for pairs that passed this round.
    - Decrements (and drops) pairs that didn't show up this round.
    - Returns latest pair details for ALL tracked pairs, with stored Rugcheck fields merged in.
    """
    file_path = Path(file_path)
    previous_data = load_json(file_path)  # {pairAddress: {...}}
    updated_data = {}

    now_iso = datetime.utcnow().isoformat()

    # 1) Update / insert pairs that passed this round
    for pair in passed_pairs:
        pair_id = pair.get("pairAddress")
        if not pair_id:
            continue

        existing = previous_data.get(pair_id, {})
        prev = existing.get("count", 0)
        count = prev if prev >= 5 else prev + 1

        updated_data[pair_id] = {
            "count": count,
            "rug_status": pair.get("rug_status", existing.get("rug_status")),
            "rug_score": pair.get("rug_score", existing.get("rug_score")),
            "rug_reasons": pair.get("rug_reasons", existing.get("rug_reasons")),
            "rug_link": pair.get("rug_link", existing.get("rug_link")),
        }

    # 2) Decay or keep pairs that did not pass this round
    for pair_id, old_entry in previous_data.items():
        if pair_id in updated_data:
            continue
        new_count = max(0, old_entry.get("count", 1) - 1)
        if new_count > 0:
            # Keep old rug fields; just decay count and last_seen untouched (or update last_seen if you prefer)
            old_entry["count"] = new_count
            updated_data[pair_id] = old_entry
        # else: drop the pair

    # 3) Save the compact tracking state (only minimal fields)
    save_json(file_path, updated_data)

    # 4) Fetch latest details for ALL tracked pairs, merge stored Rugcheck fields, and return
    full_pairs = []
    for pair_id, meta in updated_data.items():
        latest = get_pair_details("solana", pair_id)
        if not latest:
            continue

        latest["count"] = meta.get("count", 0)
        latest["rug_status"] = meta.get("rug_status")
        latest["rug_score"] = meta.get("rug_score")
        latest["rug_reasons"] = meta.get("rug_reasons")
        latest["rug_link"] = meta.get("rug_link")

        full_pairs.append(latest)

    return full_pairs