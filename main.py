from screener import get_solana_token_profiles, get_pair_address, get_pair_details
from filters import classify_pair, score_social_proof

def main():
    tokens = get_solana_token_profiles()
    print(f"✅ Found {len(tokens)} Solana token profiles.\n")

    for token in tokens:
        address = token.get("tokenAddress")

        pair_address = get_pair_address("solana", address)
        if not pair_address:
            continue

        pair = get_pair_details("solana", pair_address)
        if not pair:
            continue

        category = classify_pair(pair)
        if not category:
            continue

        social_status = score_social_proof(pair)

        base = pair.get("baseToken", {})
        quote = pair.get("quoteToken", {})
        price_usd = pair.get("priceUsd", "N/A")
        liquidity = pair.get("liquidity", {}).get("usd", 0)
        market_cap = pair.get("marketCap", 0)
        change_24h = pair.get("priceChange", {}).get("h24", "N/A")
        url = pair.get("url", "")

        print(f"🟩 {category} | {base.get('symbol', 'N/A')} / {quote.get('symbol', 'N/A')} | {social_status}")
        print(f"💰 Price: ${price_usd} | MC: ${market_cap:,.0f} | Liquidity: ${liquidity:,.0f} | 24H Change: {change_24h}%")
        print(f"🔗 {url}")
        print("-" * 80)

if __name__ == "__main__":
    main()
