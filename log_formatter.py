def build_alert_log(pairs: list) -> str:
    lines = []

    for data in pairs:
        base = data.get("baseToken", {}) or {}
        quote = data.get("quoteToken", {}) or {}

        symbol = f"{base.get('symbol', 'N/A')} / {quote.get('symbol', 'N/A')}"
        price_usd = data.get("priceUsd", "N/A")

        market_cap = float(data.get("marketCap", 0) or 0)
        liquidity = float((data.get("liquidity", {}) or {}).get("usd", 0) or 0)
        change_24h = (data.get("priceChange", {}) or {}).get("h24", "N/A")
        url = data.get("url", "")

        rug_status = data.get("rug_status", "")
        rug_score = int(data.get("rug_score", 0) or 0)
        rug_reasons = data.get("rug_reasons", []) or []
        rug_link = data.get("rug_link", "")

        count = int(data.get("count", 0) or 0)
        prefix = "🔥" if count >= 5 else "➖"

        signal = data.get("trade_signal", "No Signal")
        sig_icon = (
            "🟢" if signal == "Entry"
            else "🟡" if signal == "Watching"
            else "🔴" if signal == "Exit"
            else "⚪"
        )
        reasons = data.get("trade_reasons", []) or []
        reasons_txt = (" — " + " · ".join(reasons[:2])) if reasons else ""

        # Market fields (new)
        market_label = data.get("market_label", "")
        market_score = data.get("market_score", None)
        potential_mult = data.get("potential_multiple", None)
        market_checks = data.get("market_checks", {})

        header = f"{prefix} {sig_icon} {signal} | {symbol}{reasons_txt}"
        metrics = f"💰 Price: ${price_usd} | MC: ${market_cap:,.0f} | Liquidity: ${liquidity:,.0f} | 24H Change: {change_24h}%"
        rugline = f"{rug_status} | Score: {rug_score} / 100"

        market_line = f"📊 Market: {market_label} | Score: {market_score} | Pot.Mult: x{potential_mult}"
        if market_checks:
            market_line += f" | Checks: {sum(1 for k,v in market_checks.items() if v)} OK / {len(market_checks)}"

        parts = [header, metrics, rugline, market_line]

        if rug_reasons:
            parts.extend([f"{r}" for r in rug_reasons])

        if rug_link:
            parts.append(f"🔍 {rug_link}")

        parts.append(f"🔗 {url}")
        parts.append("-" * 40)

        lines.append("\n".join(parts))

    return "\n".join(lines)
