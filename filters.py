from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Tuple
import time

# ---- Configs you can tune ----
EARLY_HOURS = 72
LIQ_CAP_USD = 5_000_000.0

TARGET_PEAK_CAP = {
    "early": 200_000_000.0,
    "old":   50_000_000.0,
}

WEIGHTS = {
    "upside":    35,
    "market":    45,
    "structure": 20,
}

# ---------- helpers ----------
def _f(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)

def _ratio(buys, sells) -> float:
    b = _f(buys, 0)
    s = _f(sells, 0)
    return b / (s if s > 0 else 1.0)

def classify_age(created_ms: int, early_hours: int = EARLY_HOURS) -> str:
    if not created_ms:
        return "old"
    age_h = max(0.0, (time.time() * 1000 - created_ms) / 3_600_000.0)
    return "early" if age_h <= early_hours else "old"

@dataclass
class MarketChecks:
    category: str                     # "early" or "old"
    liq_ok: bool
    fdv_ok: bool
    liq_fdv_ok: bool
    turnover_ok: bool
    vol1h_ok: bool
    vol6h_ok: bool
    vol24h_ok: bool
    bs_h1_ok: bool
    bs_h6_ok: bool
    momentum_ok: bool
    within_liq_cap_ok: bool
    reasons: List[str]

def evaluate_market(pair: Dict[str, Any],
                    liq_cap_usd: float = LIQ_CAP_USD) -> MarketChecks:
    # safe pulls
    v  = pair.get("volume") or {}
    tx = pair.get("txns") or {}
    pc = pair.get("priceChange") or {}
    liq = _f((pair.get("liquidity") or {}).get("usd"), 0)
    fdv = _f(pair.get("fdv", pair.get("marketCap", 0)), 0)  # prefer fdv; fallback marketCap
    created_ms = int(pair.get("pairCreatedAt", 0) or 0)
    cat = classify_age(created_ms)

    v1h  = _f(v.get("h1"), 0)
    v6h  = _f(v.get("h6"), 0)
    v24h = _f(v.get("h24"), 0)

    h1 = tx.get("h1") or {}
    h6 = tx.get("h6") or {}

    r_h1 = _ratio(h1.get("buys", 0), h1.get("sells", 0))
    r_h6 = _ratio(h6.get("buys", 0), h6.get("sells", 0))

    m5   = _f(pc.get("m5"), 0)
    h1c  = _f(pc.get("h1"), 0)
    h24c = _f(pc.get("h24"), 0)

    reasons: List[str] = []
    within_liq_cap_ok = (liq <= liq_cap_usd) if liq_cap_usd > 0 else True
    if not within_liq_cap_ok:
        reasons.append(f"Liquidity {liq:,.0f} exceeds cap {liq_cap_usd:,.0f}")

    liq_fdv = (liq / fdv) if fdv > 0 else 0.0
    turnover24 = (v24h / fdv) if fdv > 0 else 0.0

    if cat == "early":
        liq_ok      = 30_000 <= liq <= 300_000
        fdv_ok      = fdv <= 1_500_000
        liq_fdv_ok  = liq_fdv >= 0.15
        turnover_ok = turnover24 >= 2.0
        vol1h_ok    = v1h  >= 100_000
        vol6h_ok    = v6h  >= 500_000
        vol24h_ok   = v24h >= 1_000_000
        bs_h1_ok    = 0.9 <= r_h1 <= 1.2
        bs_h6_ok    = 0.9 <= r_h6 <= 1.2
        momentum_ok = (m5 <= 25) and (h1c <= 60) and (h24c <= 400)

        if not liq_ok:      reasons.append(f"[early] liquidity {liq:,.0f} not in 30k–300k")
        if not fdv_ok:      reasons.append(f"[early] FDV {fdv:,.0f} > 1.5M")
        if not liq_fdv_ok:  reasons.append(f"[early] liq/FDV {liq_fdv:.3f} < 0.15")
        if not turnover_ok: reasons.append(f"[early] 24h turnover {turnover24:.2f} < 2.0")
        if not vol1h_ok:    reasons.append(f"[early] 1h vol {v1h:,.0f} < 100k")
        if not vol6h_ok:    reasons.append(f"[early] 6h vol {v6h:,.0f} < 500k")
        if not vol24h_ok:   reasons.append(f"[early] 24h vol {v24h:,.0f} < 1M")
        if not bs_h1_ok:    reasons.append(f"[early] h1 buy/sell {r_h1:.2f} not in [0.9,1.2]")
        if not bs_h6_ok:    reasons.append(f"[early] h6 buy/sell {r_h6:.2f} not in [0.9,1.2]")
        if not momentum_ok: reasons.append(f"[early] momentum guards tripped m5/h1/h24")
    else:
        liq_ok      = 100_000 <= liq <= liq_cap_usd
        fdv_ok      = fdv <= 10_000_000
        liq_fdv_ok  = 0.05 <= liq_fdv <= 0.50
        turnover_ok = turnover24 >= 0.5
        vol1h_ok    = v1h  >= 50_000
        vol6h_ok    = v6h  >= 300_000
        vol24h_ok   = v24h >= 500_000
        bs_h1_ok    = 0.8 <= r_h1 <= 1.25
        bs_h6_ok    = 0.8 <= r_h6 <= 1.25
        momentum_ok = (-30 <= h24c <= 150)

        if not liq_ok:      reasons.append(f"[old] liquidity {liq:,.0f} not in 100k–{liq_cap_usd:,.0f}")
        if not fdv_ok:      reasons.append(f"[old] FDV {fdv:,.0f} > 10M")
        if not liq_fdv_ok:  reasons.append(f"[old] liq/FDV {liq_fdv:.3f} not in [0.05,0.50]")
        if not turnover_ok: reasons.append(f"[old] 24h turnover {turnover24:.2f} < 0.5")
        if not vol1h_ok:    reasons.append(f"[old] 1h vol {v1h:,.0f} < 50k")
        if not vol6h_ok:    reasons.append(f"[old] 6h vol {v6h:,.0f} < 300k")
        if not vol24h_ok:   reasons.append(f"[old] 24h vol {v24h:,.0f} < 500k")
        if not bs_h1_ok:    reasons.append(f"[old] h1 buy/sell {r_h1:.2f} not in [0.8,1.25]")
        if not bs_h6_ok:    reasons.append(f"[old] h6 buy/sell {r_h6:.2f} not in [0.8,1.25]")
        if not momentum_ok: reasons.append(f"[old] h24 change {h24c:.2f}% not in [-30,150]")

    return MarketChecks(
        category=cat,
        liq_ok=liq_ok,
        fdv_ok=fdv_ok,
        liq_fdv_ok=liq_fdv_ok,
        turnover_ok=turnover_ok,
        vol1h_ok=vol1h_ok,
        vol6h_ok=vol6h_ok,
        vol24h_ok=vol24h_ok,
        bs_h1_ok=bs_h1_ok,
        bs_h6_ok=bs_h6_ok,
        momentum_ok=momentum_ok,
        within_liq_cap_ok=within_liq_cap_ok,
        reasons=reasons
    )

def _upside_capacity(fdv: float, category: str) -> Tuple[float, float]:
    """
    Returns (potential_multiple, capped_score_component_0..1).
    Map multiples to a 0..1 score: 0 at 1x, 0.5 at 10x, 1 at 100x+.
    """
    cap = max(1.0, TARGET_PEAK_CAP.get(category, 50_000_000.0))
    fdv = max(1.0, fdv)
    pot = cap / fdv
    if pot <= 1:
        s = 0.0
    elif pot >= 100:
        s = 1.0
    elif pot >= 10:
        s = 0.5 + 0.5 * (pot - 10) / 90.0
    else:
        s = 0.5 * (pot - 1) / 9.0
    return pot, s

def score_market(pair: Dict[str, Any]) -> Dict[str, Any]:
    m = evaluate_market(pair, liq_cap_usd=LIQ_CAP_USD)

    liq = _f((pair.get("liquidity") or {}).get("usd"), 0)
    fdv = _f(pair.get("fdv", pair.get("marketCap", 0)), 0)

    # --- Upside score
    pot_mult, pot_score = _upside_capacity(fdv, m.category)
    upside_points = WEIGHTS["upside"] * pot_score

    # --- Structure score (caps & bands)
    structure_passes = sum([
        1 if m.within_liq_cap_ok else 0,
        1 if m.liq_ok else 0,
        1 if m.fdv_ok else 0,
    ])
    structure_points = WEIGHTS["structure"] * (structure_passes / 3.0)

    # --- Market quality score
    sub_flags = [
        m.liq_fdv_ok, m.turnover_ok, m.vol1h_ok, m.vol6h_ok, m.vol24h_ok,
        m.bs_h1_ok, m.bs_h6_ok, m.momentum_ok
    ]

    # tiny bonus if liq/fdv sits in a sweet spot
    liq_fdv = (liq / fdv) if fdv > 0 else 0.0
    sweet = (0.12 <= liq_fdv <= 0.35) if m.category == "early" else (0.08 <= liq_fdv <= 0.30)
    sub_passes = sum(1 for x in sub_flags if x)
    market_points = WEIGHTS["market"] * ((sub_passes + (0.5 if sweet else 0)) / (len(sub_flags) + 0.5))

    total = round(upside_points + structure_points + market_points, 2)

    # Labeling
    base_ok = all([
        m.within_liq_cap_ok, m.liq_ok, m.fdv_ok,
        m.turnover_ok, m.vol24h_ok, m.momentum_ok
    ])

    if base_ok and pot_mult >= 100 and total >= 75:
        label = "x100-candidate"
    elif base_ok and pot_mult >= 10 and total >= 60:
        label = "x10-ready"
    else:
        label = "reject"

    return {
        "label": label,
        "score": total,
        "potential_multiple": round(pot_mult, 1),
        "market": asdict(m),
    }
