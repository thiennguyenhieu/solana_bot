from screener import get_solana_token_profiles, get_pair_address, get_pair_details
from filters import classify_pair
from rugcheck import get_rugcheck_report, evaluate_rugcheck

def main():
    tokens = get_solana_token_profiles()
    print(f"✅ Found {len(tokens)} Solana token profiles.\n")

    for token in tokens:
        address = token.get("tokenAddress")
        if not address:
            continue

        pair_address = get_pair_address("solana", address)
        if not pair_address:
            continue

        pair = get_pair_details("solana", pair_address)
        if not pair:
            continue

        category = classify_pair(pair)
        if not category:
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
        rug_status, rug_reasons, rug_link = evaluate_rugcheck(rugcheck_data)

        print(f"{category} | {base.get('symbol', 'N/A')} / {quote.get('symbol', 'N/A')}")
        print(f"💰 Price: ${price_usd} | MC: ${market_cap:,.0f} | Liquidity: ${liquidity:,.0f} | 24H Change: {change_24h}%")
        print(f"{rug_status}")
        if rug_link:
            print(f"🔍 {rug_link}")
        for reason in rug_reasons:
            print(reason)
        print(f"🔗 {url}")
        print("-" * 80)
    
if __name__ == "__main__":
    main()