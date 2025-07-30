from datetime import datetime

def is_potential_x100(pair):
    try:
        liquidity = float(pair.get("liquidity", {}).get("usd", 0))
        liquidity_change = pair.get("liquidityChange", {}).get("h1", 0)
        lp_removed_pct = pair.get("lpRemovedPercent", 0)
        market_cap = float(pair.get("marketCap", 0))
        fdv = float(pair.get("fdv", 0))
        volume = pair.get("volume", {})
        txns = pair.get("txns", {})

        volume_1h = float(volume.get("h1", 0))
        volume_6h = float(volume.get("h6", 0))
        volume_24h = float(volume.get("h24", 0))

        txns_1h = sum(txns.get("h1", {}).values())
        txns_6h = sum(txns.get("h6", {}).values())

        buys_1h = txns.get("h1", {}).get("buys", 0)
        sells_1h = txns.get("h1", {}).get("sells", 1)  # prevent divide-by-zero
        buy_sell_ratio = buys_1h / sells_1h if sells_1h > 0 else float('inf')

        price_change_1h = float(pair.get("priceChange", {}).get("h1", 0))
        price_change_24h = float(pair.get("priceChange", {}).get("h24", 0))

        created_at = int(pair.get("pairCreatedAt", 0)) // 1000
        age_hours = (datetime.utcnow() - datetime.utcfromtimestamp(created_at)).total_seconds() / 3600

        # --- Core Filter ---
        if not (100_000 <= market_cap <= 10_000_000):
            return False
        if liquidity < 50_000:
            return False
        if liquidity_change < -20_000:  # Large LP removal
            return False
        if lp_removed_pct > 20:
            return False
        if fdv >= 50_000_000:
            return False
        if volume_24h <= 500_000:
            return False
        if txns_1h <= 100:
            return False
        if buys_1h < 50:
            return False
        if age_hours < 4:
            return False
        if price_change_1h > 150:
            return False
        if price_change_24h >= 500:
            return False
        if buy_sell_ratio <= 1.0:
            return False

        # --- Momentum Boost ---
        if txns_6h > 0 and txns_1h < (txns_6h / 6):
            return False
        if volume_6h > 0 and volume_1h < (volume_6h / 6):
            return False

        return True

    except Exception as e:
        print(f"❌ Error in is_potential_x100: {e}")
        return False
    
def is_good_entry_point(pair: dict) -> bool:
    try:
        price_change = pair.get("priceChange", {})
        volume = pair.get("volume", {})

        price_5m = float(price_change.get("m5", 0))
        price_15m = float(price_change.get("m15", 0))
        price_1h = float(price_change.get("h1", 0))

        volume_1h = float(volume.get("h1", 0))
        volume_6h = float(volume.get("h6", 0))

        txns = pair.get("txns", {})
        buys_1h = txns.get("h1", {}).get("buys", 0)
        sells_1h = txns.get("h1", {}).get("sells", 1)  # prevent div-by-zero
        buy_sell_ratio = buys_1h / sells_1h if sells_1h > 0 else float('inf')

        current_price = float(pair.get("priceUsd", 0))
        ma_5 = float(pair.get("ma", {}).get("m5", current_price))
        ma_15 = float(pair.get("ma", {}).get("m15", current_price))

        # --- Conditions ---

        # 1. Avoid high momentum spikes
        if price_5m > 30 or price_15m > 60:
            return False

        # 2. Accumulation: volume rising, price flat
        if volume_6h > 0 and volume_1h > (volume_6h / 6) and abs(price_1h) < 5:
            return True

        # 3. Healthy buy pressure, not dumped yet
        if buy_sell_ratio > 2.0 and price_1h < 20:
            return True

        # 4. Trending above moving averages
        if current_price >= ma_5 >= ma_15:
            return True

        return False

    except Exception as e:
        print(f"❌ Error in is_good_entry_point: {e}")
        return False