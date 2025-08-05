def get_trade_signal(pair: dict) -> str:
    try:
        price_change = pair.get("priceChange", {})
        volume = pair.get("volume", {})
        txns = pair.get("txns", {})

        price_5m = float(price_change.get("m5", 0))
        price_1h = float(price_change.get("h1", 0))
        price_24h = float(price_change.get("h24", 0))

        volume_1h = float(volume.get("h1", 0))
        volume_6h = float(volume.get("h6", 0))

        buys_1h = txns.get("h1", {}).get("buys", 0)
        sells_1h = txns.get("h1", {}).get("sells", 1)
        buy_sell_ratio = buys_1h / sells_1h if sells_1h > 0 else float("inf")

        current_price = float(pair.get("priceUsd", 0))
        ma_1h = current_price / (1 + price_1h / 100) if price_1h != 0 else current_price

        # Entry Signal: healthy momentum and volume accumulation
        if volume_6h > 0 and volume_1h > (volume_6h / 6) and abs(price_1h) < 5:
            return "🟢 Entry Detected"
        if buy_sell_ratio > 2.0 and price_1h < 20 and current_price >= ma_1h:
            return "🟢 Entry Detected"

        # Exit Signal: pump or dump behavior
        if price_5m > 30 or price_1h > 150 or price_24h > 500:
            return "🔴 Exit Detected"
        if buy_sell_ratio < 0.5 and price_1h < -10:
            return "🔴 Exit Detected"

        return "⏳ Watching"

    except Exception as e:
        print(f"❌ Error in get_trade_signal: {e}")
        return "⏳ Watching"
