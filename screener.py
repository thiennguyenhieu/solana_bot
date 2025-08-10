import requests

DEX_BASE = "https://api.dexscreener.com"

def get_solana_token_profiles():
    endpoints = [
        f"{DEX_BASE}/token-boosts/latest/v1",
        f"{DEX_BASE}/token-boosts/top/v1",
        f"{DEX_BASE}/token-profiles/latest/v1"
    ]

    token_addresses = set()

    for url in endpoints:
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            data = res.json()

            for item in data:
                if item.get("chainId") == "solana":
                    token_addr = item.get("tokenAddress")
                    if token_addr:
                        token_addresses.add(token_addr)
        except Exception as e:
            print(f"❌ Failed to fetch from {url}: {e}")

    return list(token_addresses)

def get_pair_address(chain_id, token_address):
    try:
        url = f"{DEX_BASE}/token-pairs/v1/{chain_id}/{token_address}"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        if isinstance(data, list) and data:
            return data[0].get("pairAddress")
    except Exception as e:
        print(f"⚠️ Failed to fetch pair address for {token_address}: {e}")
    return None

def get_pair_details(chain_id, pair_address):
    try:
        url = f"{DEX_BASE}/latest/dex/pairs/{chain_id}/{pair_address}"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data.get("pair")
    except Exception as e:
        print(f"⚠️ Failed to fetch pair data for {pair_address}: {e}")
    return None
