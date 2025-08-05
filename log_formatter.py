from trader import get_trade_signal

def build_alert_log(pairs: list) -> str:
    log_entries = []

    for data in pairs:
        base = data.get("baseToken", {})
        quote = data.get("quoteToken", {})
        price_usd = data.get("priceUsd", "N/A")
        market_cap = data.get("marketCap", 0)
        liquidity = data.get("liquidity", {}).get("usd", 0)
        change_24h = data.get("priceChange", {}).get("h24", "N/A")
        url = data.get("url", "")
        rug_status = data.get("rug_status", "")
        rug_score = data.get("rug_score", 0)
        rug_reasons = data.get("rug_reasons", [])
        rug_link = data.get("rug_link", "")
        count = data.get("count", 0)

        log = []
        prefix = "🔥" if count >= 5 else "➖"
        log.append(f"{prefix} {base.get('symbol', 'N/A')} / {quote.get('symbol', 'N/A')}")
        log.append(f"💰 Price: ${price_usd} | MC: ${market_cap:,.0f} | Liquidity: ${liquidity:,.0f} | 24H Change: {change_24h}%")
        log.append(f"{rug_status} | Score: {rug_score} / 100")
        if rug_link:
            log.append(f"🔍 {rug_link}")
        for reason in rug_reasons:
            log.append(reason)
        log.append(get_trade_signal(data))
        log.append(f"🔗 {url}")
        log.append("-" * 20)

        log_entries.append("\n".join(log))

    return "\n\n".join(log_entries)
