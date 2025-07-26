from datetime import datetime
import requests
import re

def classify_pair(pair):
    try:
        liquidity = float(pair.get("liquidity", {}).get("usd", 0))
        fdv = float(pair.get("fdv", 0))
        volume_24h = float(pair.get("volume", {}).get("h24", 0))
        txns_1h = sum(pair.get("txns", {}).get("h1", {}).values())
        txns_24h = sum(pair.get("txns", {}).get("h24", {}).values())
        created_at = int(pair.get("pairCreatedAt", 0)) // 1000
        age_hours = (datetime.utcnow() - datetime.utcfromtimestamp(created_at)).total_seconds() / 3600
    
        # Very Degen
        if (
            liquidity >= 15_000 and
            fdv >= 100_000 and
            1 <= age_hours <= 72 and
            txns_1h >= 110
        ):
            return "Very Degen"

        # Degen
        if (
            liquidity >= 50_000 and
            fdv >= 500_000 and
            volume_24h >= 500_000 and
            txns_1h >= 75
        ):
            return "Degen"

        # Mid-Cap
        if (
            liquidity >= 100_000 and
            fdv >= 1_000_000 and
            volume_24h >= 1_500_000 and
            txns_1h >= 50
        ):
            return "Mid-Cap"

        # Old Mid-Caps
        if (
            liquidity >= 100_000 and
            200_000 <= fdv <= 100_000_000 and
            720 <= age_hours <= 2800 and
            txns_24h >= 2300 and
            volume_24h >= 200_000
        ):
            return "Old Mid-Cap"

        return None

    except Exception as e:
        print(f"❌ Error in classify_pair: {e}")
        return None

def score_social_proof(pair):
    socials = pair.get("info", {}).get("socials", [])
    for s in socials:
        if s.get("type") == "twitter":
            url = s.get("url", "")
            handle_match = re.search(r"(?:twitter\.com|x\.com)/([A-Za-z0-9_]+)", url)
            if handle_match:
                handle = handle_match.group(1)
                try:
                    res = requests.get(f"https://x.com/{handle}", headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                    if res.status_code == 200:
                        if re.search(r"(1h|2h|[1-5]m|min|hour|Yesterday)", res.text, re.IGNORECASE):
                            return "🟦 Active"
                        else:
                            return "⬜ Inactive"
                    else:
                        return "⬜ Inactive"
                except:
                    return "⬜ Inactive"
    return "⬛ No X"
