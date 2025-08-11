# trader.py
from statistics import median
from typing import Dict, Tuple, List, Set
from datetime import datetime, timedelta
from pathlib import Path
import json

History = Dict[str, List[float]]

# ---- Tunables ----
MIN_VOL_1H_USD = 50_000
MIN_TXNS_1H    = 80
ENTRY_RATIO    = 2.0
WATCH_RATIO    = 1.2
EXIT_RATIO     = 0.9
ENTRY_CHG_1H   = (-5, 20)
SPIKE_5M_PCT   = 30
BLOWOFF_1H_PCT = 120
BLOWOFF_24H_PCT= 500
DUMP_1H_PCT    = -10
DUMP_5M_PCT    = -8
COOLDOWN_BARS  = 3
ENTRY_VOTES_NEED = 2

TRADE_META_FILE = Path("trade_meta_store.json")

# In-memory store (kept lean by syncing with tracked_pairs.json)
TRADE_META: Dict[str, dict] = {}  # {pairAddress: meta}

# ---------- Utility (persist/filter) ----------
def _now():
    return datetime.utcnow()

def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    return a / b if b else default

def _trend_up(seq: List[float], min_len: int = 3) -> bool:
    if len(seq) < min_len:
        return False
    return seq[-1] >= median(seq[-min_len:]) and seq[-1] >= seq[-2]

def _pct_change(new: float, old: float) -> float:
    if old == 0:
        return 0.0
    return (new - old) / old * 100.0

def _is_cooldown(meta: dict) -> bool:
    until = meta.get("cooldown_until")
    if not until:
        return False
    try:
        return _now() < datetime.fromisoformat(until)
    except Exception:
        return False

def _set_cooldown(meta: dict, bars: int = COOLDOWN_BARS):
    meta["cooldown_until"] = (_now() + timedelta(minutes=10 * bars)).isoformat()

def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_json(path: Path, data: dict):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to save {path}: {e}")

def load_trade_meta_from_tracked(tracked_file: str = "tracked_pairs.json") -> Set[str]:
    """
    Load trade meta from disk, but keep only those pair IDs present in tracked_pairs.json.
    Returns the active pair id set.
    """
    tracked = _load_json(Path(tracked_file))  # {pairAddress: {...}}
    active_ids = set(tracked.keys())

    disk_meta = _load_json(TRADE_META_FILE)   # {pairAddress: meta}
    # Filter to active only
    global TRADE_META
    TRADE_META = {pid: disk_meta.get(pid, {}) for pid in active_ids}
    return active_ids

def save_trade_meta(active_ids: Set[str] | None = None):
    """
    Persist trade meta to disk. If active_ids provided, filter to those keys only.
    """
    if active_ids is not None:
        to_save = {pid: meta for pid, meta in TRADE_META.items() if pid in active_ids}
    else:
        to_save = TRADE_META
    _save_json(TRADE_META_FILE, to_save)

# ---------- Signal engine ----------
def update_histories(meta: dict, pair: dict, max_len: int = 72) -> dict:
    txns = pair.get("txns", {}) or {}
    vol = pair.get("volume", {}) or {}
    price_change = pair.get("priceChange", {}) or {}

    buys_1h  = float(txns.get("h1", {}).get("buys", 0) or 0)
    sells_1h = float(txns.get("h1", {}).get("sells", 0) or 0)
    ratio_1h = min(5.0, _safe_div(buys_1h, sells_1h, default=0.0))

    entry = {
        "ts": _now().isoformat(),
        "price": float(pair.get("priceUsd", 0) or 0),
        "ratio_1h": ratio_1h,
        "vol_1h": float(vol.get("h1", 0) or 0),
        "vol_6h": float(vol.get("h6", 0) or 0),
        "chg_5m": float(price_change.get("m5", 0) or 0),
        "chg_1h": float(price_change.get("h1", 0) or 0),
        "chg_24h": float(price_change.get("h24", 0) or 0),
        "txns_1h": float(buys_1h + sells_1h),
        "buys_1h": buys_1h,
        "sells_1h": sells_1h,
    }

    for k in ["price_hist", "ratio_hist", "vol1h_hist"]:
        meta.setdefault(k, [])

    meta["price_hist"].append(entry["price"])
    meta["ratio_hist"].append(entry["ratio_1h"])
    meta["vol1h_hist"].append(entry["vol_1h"])

    for k in ["price_hist", "ratio_hist", "vol1h_hist"]:
        if len(meta[k]) > max_len:
            meta[k] = meta[k][-max_len:]

    meta["last_snapshot"] = entry
    meta.setdefault("entry_votes", 0)
    meta.setdefault("exit_votes", 0)
    return meta

def _meets_entry_quality(snap: dict, vol1h_hist: List[float], ratio_hist: List[float]) -> Tuple[bool, List[str]]:
    reasons = []
    chg_5m = float(snap.get("chg_5m", 0))
    chg_1h = float(snap.get("chg_1h", 0))
    chg_24h= float(snap.get("chg_24h", 0))
    vol_1h = float(snap.get("vol_1h", 0))
    vol_6h = float(snap.get("vol_6h", 0))
    ratio_1h = float(snap.get("ratio_1h", 0))
    txns_1h = float(snap.get("txns_1h", 0))

    if chg_5m > SPIKE_5M_PCT:
        return False, ["5m spike > 30% (cooldown)"]
    if chg_1h >= BLOWOFF_1H_PCT or chg_24h >= BLOWOFF_24H_PCT:
        return False, ["Already pumped hard (1h≥120% or 24h≥500%)"]

    if vol_1h < MIN_VOL_1H_USD:
        return False, [f"1h volume < ${MIN_VOL_1H_USD:,}"]
    if txns_1h < MIN_TXNS_1H:
        return False, [f"1h txns < {MIN_TXNS_1H}"]

    vol_rising = _trend_up(vol1h_hist, min_len=3) or (vol_6h > 0 and vol_1h >= vol_6h / 6)
    in_band = (ENTRY_CHG_1H[0] <= chg_1h <= ENTRY_CHG_1H[1])

    if ratio_1h >= ENTRY_RATIO and vol_rising and in_band:
        reasons += [
            f"Buy/Sell ratio ≥ {ENTRY_RATIO}",
            "1h volume rising",
            f"1h price in {ENTRY_CHG_1H[0]}%…{ENTRY_CHG_1H[1]}% band"
        ]
        return True, reasons

    return False, []

def _meets_exit_quality(snap: dict, ratio_hist: List[float], price_hist: List[float]) -> Tuple[bool, List[str]]:
    reasons = []
    price = float(snap.get("price", 0))
    chg_1h = float(snap.get("chg_1h", 0))
    chg_24h= float(snap.get("chg_24h", 0))
    chg_5m = float(snap.get("chg_5m", 0))
    ratio_1h = float(snap.get("ratio_1h", 0))

    prev_price = price_hist[-2] if len(price_hist) >= 2 else price
    prev_ratio = ratio_hist[-2] if len(ratio_hist) >= 2 else ratio_1h

    if chg_1h >= BLOWOFF_1H_PCT or chg_24h >= BLOWOFF_24H_PCT:
        return True, ["Blow-off top detected"]
    if chg_1h <= DUMP_1H_PCT or chg_5m <= DUMP_5M_PCT:
        return True, ["Momentum dump (1h≤-10% or 5m≤-8%)"]

    if ratio_1h <= EXIT_RATIO:
        reasons.append(f"Buy/Sell ratio ≤ {EXIT_RATIO} (sell pressure)")
        return True, reasons

    if prev_ratio > 0 and (ratio_1h - prev_ratio) / max(prev_ratio, 1e-9) <= -0.30:
        return True, ["Buy/Sell ratio dropped ≥ 30%"]

    if _pct_change(price, prev_price) <= -10:
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

    exit_ok, exit_reasons = _meets_exit_quality(snap, ratio_hist, price_hist)
    if exit_ok:
        meta["entry_votes"] = 0
        meta["exit_votes"] = meta.get("exit_votes", 0) + 1
        _set_cooldown(meta, COOLDOWN_BARS)
        return "Exit", exit_reasons

    entry_ok, entry_reasons = _meets_entry_quality(snap, vol1h_hist, ratio_hist)
    if entry_ok:
        meta["entry_votes"] = meta.get("entry_votes", 0) + 1
        meta["exit_votes"] = 0
        if meta["entry_votes"] >= ENTRY_VOTES_NEED:
            return "Entry", entry_reasons
        else:
            return "Watching", ["1/2 entry confirmations"] + entry_reasons

    meta["entry_votes"] = 0
    meta["exit_votes"] = 0
    return "No Signal", []

def enrich_with_trade_signal(pair: dict) -> dict:
    """
    Stateless API for callers:
    - Reads & updates the global TRADE_META for this pairAddress.
    - Attaches trade_signal + trade_reasons on the pair.
    - Returns the pair (mutated).
    """
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
