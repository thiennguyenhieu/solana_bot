from screener import get_solana_token_profiles, get_pair_address, get_pair_details
from filters import is_potential_x100
from rugcheck import get_rugcheck_report, evaluate_rugcheck
from telegram_bot import send_telegram_message

def main():
    tokens = get_solana_token_profiles()
    print(f"✅ Found {len(tokens)} Solana token profiles.\n")

    log_entries = []

    for address in tokens:
        if not address:
            continue

        pair_address = get_pair_address("solana", address)
        if not pair_address:
            continue

        pair = get_pair_details("solana", pair_address)
        if not pair:
            continue

        if not is_potential_x100(pair):
            continue
        
        base = pair.get("baseToken", {})
        quote = pair.get("quoteToken", {})
        price_usd = pair.get("priceUsd", "N/A")
        market_cap = pair.get("marketCap", 0)
        liquidity = pair.get("liquidity", {}).get("usd", 0)
        change_24h = pair.get("priceChange", {}).get("h24", "N/A")
        url = pair.get("url", "")

        mint_address = base.get("address", "")
        rugcheck_data = get_rugcheck_report(mint_address)
        rug_status, rug_score, rug_reasons, rug_link = evaluate_rugcheck(rugcheck_data)

        if (rug_score < 70):
            continue

        log = []
        log.append(f"{base.get('symbol', 'N/A')} / {quote.get('symbol', 'N/A')}")
        log.append(f"💰 Price: ${price_usd} | MC: ${market_cap:,.0f} | Liquidity: ${liquidity:,.0f} | 24H Change: {change_24h}%")
        log.append(f"{rug_status} | Score: {rug_score} / 100")
        if rug_link:
            log.append(f"🔍 {rug_link}")
        for reason in rug_reasons:
            log.append(reason)
        log.append(f"🔗 {url}")
        log.append("-" * 20)

        log_entries.append("\n".join(log))
    
    if log_entries:
        final_log = "\n".join(log_entries)
        print(final_log)  # still print locally
        send_telegram_message(final_log)

if __name__ == "__main__":
    main()