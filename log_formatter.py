def build_alert_log(pairs: list) -> str:
    logs = []

    for pair in pairs:
        base = pair.get("baseToken", {})
        quote = pair.get("quoteToken", {})
        price_usd = pair.get("priceUsd", "N/A")
        market_cap = pair.get("marketCap", 0)
        liquidity = pair.get("liquidity", {}).get("usd", 0)
        change_24h = pair.get("priceChange", {}).get("h24", "N/A")
        url = pair.get("url", "")
        rug_status = pair.get("rug_status", "")
        rug_score = pair.get("rug_score", 0)
        rug_reasons = pair.get("rug_reasons", [])
        rug_link = pair.get("rug_link", "")

        entry_text = (
            f"{base.get('symbol', 'N/A')} | {base.get('address', '')}\n"
            f"{rug_status} | Score: {rug_score} / 100\n"        
            f"💰 Price: ${price_usd} | MC: ${market_cap:,.0f} | Liquidity: ${liquidity:,.0f} | 24H Change: {change_24h}%\n"
        )

        if pair.get("is_good_entry"):
            entry_text += "✅ Entry Signal Detected\n"
        else:
            entry_text += "⏳ Not ideal entry point\n"

        if rug_link:
            entry_text += f"🔍 {rug_link}\n"

        for reason in rug_reasons:
            entry_text += f"{reason}\n"

        entry_text += f"🔗 {url}\n"
        entry_text += "-" * 30

        logs.append(entry_text)

    return "\n\n".join(logs)
