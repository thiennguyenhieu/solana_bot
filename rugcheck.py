import requests

RUGCHECK_BASE_URL = "https://api.rugcheck.xyz/v1/tokens"

def get_rugcheck_report(mint: str):
    url = f"{RUGCHECK_BASE_URL}/{mint}/report"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception as e:
        return None

def evaluate_rugcheck(report: dict):
    if not report or report.get("rugged") is True:
        return "🔴 Rugged", 0, [], f"https://rugcheck.xyz/tokens/{report.get('mint')}" if report else ""

    reasons = []
    score = 100  # Start from full score

    # Top holders
    top_holders = report.get("topHolders", [])
    total_holders = report.get("totalHolders", 0)
    top1_pct = top_holders[0]["pct"] if top_holders else 100
    top10_pct = sum(h["pct"] for h in top_holders[:10]) if len(top_holders) >= 10 else 100

    # LP lock percentage
    lp_locked_pct = 0
    for market in report.get("markets", []):
        lp_locked_pct = max(lp_locked_pct, market.get("lp", {}).get("lpLockedPct", 0))

    creator_balance = report.get("creatorBalance", 1)
    transfer_fee_pct = report.get("transferFee", {}).get("pct", 0)

    # Violations and deductions
    if top1_pct > 10:
        score -= 10
        reasons.append("⚠️ Top 1 holder > 10%")
    if top10_pct > 30:
        score -= 10
        reasons.append("⚠️ Top 10 holders > 30%")
    if lp_locked_pct < 90:
        score -= 10
        reasons.append("⚠️ LP locked < 90%")
    if total_holders < 500:
        score -= 10
        reasons.append("⚠️ Total holders < 500")
    if creator_balance > 0:
        score -= 10
        reasons.append("⚠️ Creator still holds tokens")
    if report.get("mintAuthority") or report.get("freezeAuthority"):
        score -= 10
        reasons.append("⚠️ Mint or freeze authority exists")
    if transfer_fee_pct > 5:
        score -= 10
        reasons.append(f"⚠️ Transfer fee > 5% ({transfer_fee_pct}%)")

    # Risk field
    risks = report.get("risks", [])
    if risks:
        score -= 15
        for risk in risks:
            description = risk.get("description")
            if description:
                reasons.append(f"⚠️ {description}")

    # Insider detection
    if report.get("graphInsidersDetected", 0) > 0:
        score -= 15
        reasons.append("⚠️ Insider network detected")

    # Final status
    status = "🟩 Safe" if score >= 80 else "🟠 Risky" if score >= 40 else "🔴 Danger"
    rugcheck_link = f"https://rugcheck.xyz/tokens/{report.get('mint')}"

    return status, score, reasons, rugcheck_link


