from datetime import datetime

def is_potential_x100(pair):
    try:
        liquidity = float(pair.get("liquidity", {}).get("usd", 0))
        market_cap = float(pair.get("marketCap", 0))
        fdv = float(pair.get("fdv", 0))
        volume_24h = float(pair.get("volume", {}).get("h24", 0))
        txns = pair.get("txns", {})
        txns_1h = sum(txns.get("h1", {}).values())
        buys_1h = txns.get("h1", {}).get("buys", 0)
        sells_1h = txns.get("h1", {}).get("sells", 1)  # prevent divide-by-zero
        buy_sell_ratio = buys_1h / sells_1h if sells_1h > 0 else float('inf')
        price_change_24h = float(pair.get("priceChange", {}).get("h24", 0))
        created_at = int(pair.get("pairCreatedAt", 0)) // 1000
        age_hours = (datetime.utcnow() - datetime.utcfromtimestamp(created_at)).total_seconds() / 3600

        # Unified X100 Criteria
        if not (100_000 <= market_cap <= 10_000_000):
            return False
        if liquidity < 50_000:
            return False
        if fdv >= 50_000_000:
            return False
        if volume_24h <= 500_000:
            return False
        if txns_1h <= 100:
            return False
        if age_hours > 168:  # < 7 days
            return False
        if price_change_24h >= 500:
            return False
        if buy_sell_ratio <= 1.0:
            return False

        return True  # all conditions met

    except Exception as e:
        print(f"❌ Error in is_potential_x100: {e}")
        return False
