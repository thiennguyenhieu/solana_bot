from screener import get_solana_token_profiles, get_pair_address, get_pair_details
from filters import is_potential_x100
from rugcheck import get_rugcheck_report, evaluate_rugcheck
from tracker import update_pair_tracking
from telegram_bot import send_telegram_message
from log_formatter import build_alert_log

def main():
    tokens = get_solana_token_profiles()
    #print(f"✅ Found {len(tokens)} Solana token profiles.\n")

    passed_pairs = []

    for address in tokens:
        if not address:
            #print("⚠️ Skipping token: Missing address")
            continue

        pair_address = get_pair_address("solana", address)
        if not pair_address:
            #print(f"⚠️ Skipping {address}: Failed to get pair address")
            continue

        pair = get_pair_details("solana", pair_address)
        if not pair:
            #print(f"⚠️ Skipping {address}: Failed to get pair details for pair {pair_address}")
            continue

        if not is_potential_x100(pair):
            #print(f"❌ Skipping {pair_address}: Not a potential x100 candidate")
            continue

        base = pair.get("baseToken", {})
        mint_address = base.get("address", "")

        rugcheck_data = get_rugcheck_report(mint_address)
        rug_status, rug_score, rug_reasons, rug_link = evaluate_rugcheck(rugcheck_data)

        # 🚫 Skip if rug score too low or metadata is mutable by owner
        if rug_score < 70 or any("Token metadata can be changed by the owner" in r for r in rug_reasons):
            continue

        #print(f"✅ PASSED: {pair_address}")

        # Enrich pair with evaluated data
        pair["rug_status"] = rug_status
        pair["rug_score"] = rug_score
        pair["rug_reasons"] = rug_reasons
        pair["rug_link"] = rug_link
        
        passed_pairs.append(pair)

    if passed_pairs:
        all_tracked = update_pair_tracking(passed_pairs)
        if all_tracked:
            log_text = build_alert_log(all_tracked)  # Will highlight internally
            send_telegram_message(log_text)

if __name__ == "__main__":
    main()
