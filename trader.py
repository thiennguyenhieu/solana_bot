# trader.py

from statistics import median
from typing import Dict, Tuple, List, Set
from datetime import datetime, timedelta
from pathlib import Path
import json

History = Dict[str, List[float]]
TRADE_META_FILE = Path("trade_meta_store.json")
TRADE_META: Dict[str, dict] = {}

# --- Tunables ---
MIN_VOL_1H_USD = 50_000
MIN_TXNS_1H = 80
ENTRY_RATIO = 2.0
WATCH_RATIO = 1.2
EXIT_RATIO = 0.9
ENTRY_CHG_1H = (-5, 20)
SPIKE_5M_PCT = 30
BLOWOFF_1H_PCT = 120
BLOWOFF_24H_PCT = 500
DUMP_1H_PCT = -10
DUMP_5M_PCT = -8
COOLDOWN_BARS = 3
ENTRY_VOTES_NEED = 2


# --- Helpers ---
def _now(): return datetime.utcnow()

def _safe_div(a, b, default=0.0): return a / b if b else default

def _pct_change(new, old): return (new - old) / old * 100 if old else 0

def _trend_up(seq, min_len=3): return len(seq) >= min_len and seq[-1] >= median(seq[-min_len:]) and seq[-1] >= seq[-2]

def _is_cooldown(meta):
    until = meta.get("cooldown_until")
    try:
        return until and _now() < datetime.fromisoformat(until)
    except:
        return False

def _set_cooldown(meta, bars=COOLDOWN_BARS):
    meta["cooldown_until"] = (_now() + timedelta(minutes=10 * bars)).isoformat()

def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_json(path: Path, data: dict):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to save {path}: {e}")


# --- Persistence API ---
def load_trade_meta_from_tracked(tracked_file="tracked_pairs.json") -> Set[str]:
    tracked = _load_json(Path(tracked_file))
    active_ids = set(tracked.keys())
    disk_meta = _load_json(TRADE_META_FILE)

    global TRADE_META
    TRADE_META = {pid: disk_meta.get(pid, {}) for pid in active_ids}
    return active_ids

def save_trade_meta(active_ids: Set[str] | None = None):
    to_save = {pid: meta for pid, meta in TRADE_META.items() if (active_ids is None or pid in active_ids)}
    _save_json(TRADE_META_FILE, to_save)


# --- Signal engine ---
def update_histories(meta: dict, pair: dict, max_len=72) -> dict:
    txns = pair.get("txns", {}) or {}
    vol = pair.get("volume", {}) or {}
    price_change = pair.get("priceChange", {}) or {}

    buys = float(txns.get("h1", {}).get("buys", 0))
    sells = float(txns.get("h1", {}).get("sells", 0))
    ratio = min(5.0, _safe_div(buys, sells, 0))

    entry = {
        "ts": _now().isoformat(),
        "price": float(pair.get("priceUsd", 0)),
        "ratio_1h": ratio,
        "vol_1h": float(vol.get("h1", 0)),
        "vol_6h": float(vol.get("h6", 0)),
        "chg_5m": float(price_change.get("m5", 0)),
        "chg_1h": float(price_change.get("h1", 0)),
        "chg_24h": float(price_change.get("h24", 0)),
        "txns_1h": buys + sells,
        "buys_1h": buys,
        "sells_1h": sells,
    }

    for key in ["price_hist", "ratio_hist", "vol1h_hist"]:
        meta.setdefault(key, []).append(entry[key.replace("_hist", "")])
        if len(meta[key]) > max_len:
            meta[key] = meta[key][-max_len:]

    meta["last_snapshot"] = entry
    meta.setdefault("entry_votes", 0)
    meta.setdefault("exit_votes", 0)
    return meta


def _meets_entry_quality(snap, vol1h_hist, ratio_hist) -> Tuple[bool, List[str]]:
    reasons = []
    if snap["chg_5m"] > SPIKE_5M_PCT:
        return False, ["5m spike > 30% (cooldown)"]
    if snap["chg_1h"] >= BLOWOFF_1H_PCT or snap["chg_24h"] >= BLOWOFF_24H_PCT:
        return False, ["Already pumped hard"]

    if snap["vol_1h"] < MIN_VOL_1H_USD:
        return False, [f"1h volume < ${MIN_VOL_1H_USD:,}"]
    if snap["txns_1h"] < MIN_TXNS_1H:
        return False, [f"1h txns < {MIN_TXNS_1H}"]

    vol_rising = _trend_up(vol1h_hist) or (snap["vol_6h"] > 0 and snap["vol_1h"] >= snap["vol_6h"] / 6)
    in_band = ENTRY_CHG_1H[0] <= snap["chg_1h"] <= ENTRY_CHG_1H[1]

    if snap["ratio_1h"] >= ENTRY_RATIO and vol_rising and in_band:
        reasons = [
            f"Buy/Sell ratio ≥ {ENTRY_RATIO}",
            "1h volume rising",
            f"1h price in {ENTRY_CHG_1H[0]}%…{ENTRY_CHG_1H[1]}% band"
        ]
        return True, reasons
    return False, []


def _meets_exit_quality(snap, ratio_hist, price_hist) -> Tuple[bool, List[str]]:
    reasons = []
    prev_price = price_hist[-2] if len(price_hist) >= 2 else snap["price"]
    prev_ratio = ratio_hist[-2] if len(ratio_hist) >= 2 else snap["ratio_1h"]

    if snap["chg_1h"] >= BLOWOFF_1H_PCT or snap["chg_24h"] >= BLOWOFF_24H_PCT:
        return True, ["Blow-off top detected"]
    if snap["chg_1h"] <= DUMP_1H_PCT or snap["chg_5m"] <= DUMP_5M_PCT:
        return True, ["Momentum dump"]

    if snap["ratio_1h"] <= EXIT_RATIO:
        return True, [f"Buy/Sell ratio ≤ {EXIT_RATIO} (sell pressure)"]

    if prev_ratio > 0 and (snap["ratio_1h"] - prev_ratio) / max(prev_ratio, 1e-9) <= -0.30:
        return True, ["Buy/Sell ratio dropped ≥ 30%"]

    if _pct_change(snap["price"], prev_price) <= -10:
        return True, ["Price down ≥ 10% from last check"]

    return False, []


def get_trade_signal(meta: dict) -> Tuple[str, List[str]]:
    snap = meta.get("last_snapshot", {})
    if not snap:
        return "No Signal", []

    if _is_cooldown(meta):
        return "Watching", ["Cooldown active"]

    price_hist = meta.get("price_hist", [])
    ratio_hist = meta.get("ratio_hist", [])
    vol1h_hist = meta.get("vol1h_hist", [])

    if _meets_exit_quality(snap, ratio_hist, price_hist)[0]:
        meta["entry_votes"] = 0
        meta["exit_votes"] = meta.get("exit_votes", 0) + 1
        _set_cooldown(meta)
        return "Exit", _meets_exit_quality(snap, ratio_hist, price_hist)[1]

    entry_ok, reasons = _meets_entry_quality(snap, vol1h_hist, ratio_hist)
    if entry_ok:
        meta["entry_votes"] = meta.get("entry_votes", 0) + 1
        meta["exit_votes"] = 0
        return ("Entry", reasons) if meta["entry_votes"] >= ENTRY_VOTES_NEED else ("Watching", ["1/2 entry confirmations"] + reasons)

    meta["entry_votes"] = 0
    meta["exit_votes"] = 0
    return "No Signal", []


def enrich_with_trade_signal(pair: dict) -> dict:
    pair_id = pair.get("pairAddress")
    if not pair_id:
        return pair

    meta_old = TRADE_META.get(pair_id, {})
    meta_new = update_histories(meta_old, pair)
    signal, reasons = get_trade_signal(meta_new)
    pair["trade_signal"] = signal
    pair["trade_reasons"] = reasons
    TRADE_META[pair_id] = meta_new
    return pair
