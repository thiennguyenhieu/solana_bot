from statistics import median
from typing import Dict, Tuple, List
from datetime import datetime

History = Dict[str, List[float]]

def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    return a / b if b else default

def _trend_up(seq: List[float], min_len: int = 3) -> bool:
    """Simple rising check: last value >= median of last N and >= previous."""
    if len(seq) < min_len:
        return False
    return seq[-1] >= median(seq[-min_len:]) and seq[-1] >= seq[-2]

def _pct_change(new: float, old: float) -> float:
    if old == 0:
        return 0.0
    return (new - old) / old * 100.0

def update_histories(meta: dict, pair: dict, max_len: int = 72) -> dict:
    """
    Update minimal histories stored in tracker for each pair.
    Assumes your scheduler runs every ~10 min.
    max_len=72 keeps ~12 hours of 10-min bars.
    """
    txns = pair.get("txns", {})
    vol = pair.get("volume", {})
    price_change = pair.get("priceChange", {})

    buys_1h = float(txns.get("h1", {}).get("buys", 0))
    sells_1h = float(txns.get("h1", {}).get("sells", 0))
    ratio_1h = _safe_div(buys_1h, sells_1h, default=0.0)

    entry = {
        "ts": datetime.utcnow().isoformat(),
        "price": float(pair.get("priceUsd", 0) or 0),
        "ratio_1h": ratio_1h,
        "vol_1h": float(vol.get("h1", 0) or 0),
        "vol_6h": float(vol.get("h6", 0) or 0),
        "chg_5m": float(price_change.get("m5", 0) or 0),
        "chg_1h": float(price_change.get("h1", 0) or 0),
        "chg_24h": float(price_change.get("h24", 0) or 0),
    }

    # initialize arrays
    for k in ["price_hist", "ratio_hist", "vol1h_hist"]:
        meta.setdefault(k, [])

    meta["price_hist"].append(entry["price"])
    meta["ratio_hist"].append(entry["ratio_1h"])
    meta["vol1h_hist"].append(entry["vol_1h"])

    # trim
    for k in ["price_hist", "ratio_hist", "vol1h_hist"]:
        if len(meta[k]) > max_len:
            meta[k] = meta[k][-max_len:]

    # keep last snapshot too (helps with messaging)
    meta["last_snapshot"] = entry
    return meta

def get_entry_exit_signal(pair: dict, meta: dict) -> Tuple[str, List[str]]:
    """
    Returns:
      ("Entry" | "Watching" | "Exit" | "No Signal", [reasons])
    """
    reasons: List[str] = []

    # Pull latest snapshot (filled by update_histories)
    snap = meta.get("last_snapshot", {})
    price = float(snap.get("price", 0))
    chg_5m = float(snap.get("chg_5m", 0))
    chg_1h = float(snap.get("chg_1h", 0))
    chg_24h = float(snap.get("chg_24h", 0))
    ratio_1h = float(snap.get("ratio_1h", 0))
    vol_1h = float(snap.get("vol_1h", 0))
    vol_6h = float(snap.get("vol_6h", 0))

    price_hist = meta.get("price_hist", [])
    ratio_hist = meta.get("ratio_hist", [])
    vol1h_hist = meta.get("vol1h_hist", [])

    prev_price = price_hist[-2] if len(price_hist) >= 2 else price
    prev_ratio = ratio_hist[-2] if len(ratio_hist) >= 2 else ratio_1h

    # Quick guards (avoid knife catches / blow-offs)
    if chg_5m > 30:
        reasons.append("5m spike > 30% (cooldown)")
        return "Watching", reasons
    if chg_1h >= 120 or chg_24h >= 500:
        reasons.append("Already pumped hard (1h≥120% or 24h≥500%)")
        return "Exit", reasons

    # Momentum context
    price_down_10 = _pct_change(price, prev_price) <= -10

    ratio_drop_big = (prev_ratio > 0 and (ratio_1h - prev_ratio) / max(prev_ratio, 1e-9) <= -0.3)
    ratio_high = ratio_1h >= 2.0
    ratio_ok = ratio_1h >= 1.2

    vol_rising = _trend_up(vol1h_hist, min_len=3) or (vol_6h > 0 and vol_1h >= vol_6h / 6)

    # ===== Entry =====
    if ratio_high and vol_rising and (-5 <= chg_1h <= 20):
        reasons += [
            "Buy/Sell ratio ≥ 2.0",
            "1h volume rising",
            "Price within −5% … +20% (controlled)"
        ]
        return "Entry", reasons

    # ===== Exit =====
    if ratio_1h <= 1.0:
        reasons.append("Buy/Sell ratio ≤ 1.0 (sell pressure)")
        return "Exit", reasons

    if ratio_drop_big:
        reasons.append("Buy/Sell ratio dropped ≥ 30%")
        return "Exit", reasons

    if price_down_10:
        reasons.append("Price down ≥ 10% from last check")
        return "Exit", reasons

    # ===== Watching =====
    if ratio_ok and vol_rising and chg_1h < 30:
        reasons += [
            "Buy/Sell ratio ≥ 1.2",
            "1h volume rising",
            "Price growth < 30% (no blow-off)"
        ]
        return "Watching", reasons

    return "No Signal", reasons

def enrich_with_trade_signal(pair: dict, meta: Dict = None) -> Tuple[dict, Dict]:
    """
    Adds a trading signal to the pair using lightweight history.
    Args:
      pair: dexscreener pair dict
      meta: optional dict that stores rolling histories (price/ratio/volume) for this pair
    Returns:
      (pair_with_signal, updated_meta)
    """
    meta = meta or {}
    meta = update_histories(meta, pair)
    signal, reasons = get_entry_exit_signal(pair, meta)
    pair["trade_signal"] = signal
    pair["trade_reasons"] = reasons
    return pair, meta

def format_signal_line(pair: dict) -> str:
    base = pair.get("baseToken", {})
    quote = pair.get("quoteToken", {})
    symbol = f"{base.get('symbol', 'N/A')} / {quote.get('symbol', 'N/A')}"
    price_usd = pair.get("priceUsd", "N/A")
    signal = pair.get("trade_signal", "No Signal")
    reasons = pair.get("trade_reasons", [])
    reasons_txt = " · ".join(reasons[:3])  # keep it short
    return f"🕹 {signal} | {symbol} — ${price_usd}  {('· ' + reasons_txt) if reasons_txt else ''}"
