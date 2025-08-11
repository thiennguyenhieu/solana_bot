# tracker.py
from pathlib import Path
from datetime import datetime
import json
from screener import get_pair_details
from trader import update_histories, get_trade_signal

TRACKED_FILE = Path("tracked_pairs.json")
COUNT_CAP = 5

def load_json(path: Path):
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load {path}: {e}")
        return {}

def save_json(path: Path, data: dict):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to save {path}: {e}")

def update_pair_tracking(passed_pairs, file_path="tracked_pairs.json"):
    """
    Stores minimal state per pair:
      - count (capped) + Rugcheck + Trade signal/meta + Market fields
    Increments count for seen pairs, decays for unseen pairs,
    then fetches latest pair details and merges stored fields.
    """
    file_path = Path(file_path)
    previous = load_json(file_path)  # {pairAddress: {...}}
    updated = {}

    now_iso = datetime.utcnow().isoformat()

    # 1) Upsert pairs that passed this round
    for pair in passed_pairs:
        pair_id = pair.get("pairAddress")
        if not pair_id:
            continue

        prev_entry = previous.get(pair_id, {})
        prev_count = int(prev_entry.get("count", 0))
        new_count = min(COUNT_CAP, prev_count + 1)

        # --- keep & update compact trade history ---
        trade_meta = prev_entry.get("trade_meta", {})
        trade_meta = update_histories(trade_meta, pair, max_len=72)  # ~12h of 10‑min bars
        signal, reasons = get_trade_signal(trade_meta)

        updated[pair_id] = {
            "count": new_count,
            "last_seen": now_iso,

            # Rugcheck fields (prefer latest if present)
            "rug_status": pair.get("rug_status", prev_entry.get("rug_status")),
            "rug_score": pair.get("rug_score", prev_entry.get("rug_score")),
            "rug_reasons": pair.get("rug_reasons", prev_entry.get("rug_reasons")),
            "rug_link": pair.get("rug_link", prev_entry.get("rug_link")),

            # Market fields (persisted)
            "market_label": pair.get("market_label", prev_entry.get("market_label")),
            "market_score": pair.get("market_score", prev_entry.get("market_score")),
            "potential_multiple": pair.get("potential_multiple", prev_entry.get("potential_multiple")),
            "market_checks": pair.get("market_checks", prev_entry.get("market_checks")),

            # Trade fields
            "trade_signal": signal,
            "trade_reasons": reasons,
            "trade_meta": trade_meta,
            "last_signal_at": now_iso,
        }

    # 2) Decay or keep pairs that did not pass this round
    for pair_id, old_entry in previous.items():
        if pair_id in updated:
            continue
        new_count = max(0, int(old_entry.get("count", 1)) - 1)
        if new_count > 0:
            old_entry["count"] = new_count
            # keep their last trade/rug/market state
            updated[pair_id] = old_entry
        # else drop

    # 3) Save compact tracking state
    save_json(file_path, updated)

    # 4) Fetch latest details for ALL tracked pairs, merge fields, return
    full_pairs = []
    for pair_id, meta in updated.items():
        latest = get_pair_details("solana", pair_id)
        if not latest:
            continue

        # counts
        latest["count"] = meta.get("count", 0)

        # rug fields
        latest["rug_status"] = meta.get("rug_status")
        latest["rug_score"] = meta.get("rug_score")
        latest["rug_reasons"] = meta.get("rug_reasons")
        latest["rug_link"] = meta.get("rug_link")

        # market fields
        latest["market_label"] = meta.get("market_label")
        latest["market_score"] = meta.get("market_score")
        latest["potential_multiple"] = meta.get("potential_multiple")
        latest["market_checks"] = meta.get("market_checks")

        # trade fields
        latest["trade_signal"] = meta.get("trade_signal", "No Signal")
        latest["trade_reasons"] = meta.get("trade_reasons", [])

        full_pairs.append(latest)

    return full_pairs
