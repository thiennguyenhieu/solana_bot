import json
import os

def update_pair_tracking(current_pairs, tracked_file="tracked_pairs.json", threshold=5):
    # Load existing data
    if os.path.exists(tracked_file):
        with open(tracked_file, "r") as f:
            data = json.load(f)
    else:
        data = {}

    updated_data = {}
    alerts = []

    for pair in current_pairs:
        pair_id = pair["pairAddress"]
        existing = data.get(pair_id, {})
        count = existing.get("count", 0) + 1

        # Always update latest data
        updated_data[pair_id] = pair.copy()
        updated_data[pair_id]["count"] = count

        if count >= threshold:
            alerts.append(pair)

    # Handle missing pairs (decay or remove)
    for pair_id, existing in data.items():
        if pair_id not in updated_data:
            count = existing.get("count", 0) - 1
            if count > 0:
                existing["count"] = count
                updated_data[pair_id] = existing  # keep decayed data

    # Save
    with open(tracked_file, "w") as f:
        json.dump(updated_data, f, indent=2)

    return alerts