from screener import get_solana_token_profiles, get_pair_address, get_pair_details
from filters import is_potential_x100
from rugcheck import get_rugcheck_report, evaluate_rugcheck
from tracker import update_pair_tracking
from telegram_bot import send_telegram_message
from log_formatter import build_alert_log
from trader import enrich_with_trade_signal

PAIR_META_STORE = {}  # {pairAddress: meta}

def main():
    tokens = get_solana_token_profiles()

    passed_pairs = []

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
        mint_address = base.get("address", "")

        rugcheck_data = get_rugcheck_report(mint_address)
        rug_status, rug_score, rug_reasons, rug_link = evaluate_rugcheck(rugcheck_data)

        # Skip if rug score too low or metadata is mutable by owner
        if rug_score < 70 or any("Token metadata can be changed by the owner" in r for r in rug_reasons):
            continue

        # attach trade signal
        pair_id = pair.get("pairAddress")
        meta_old = PAIR_META_STORE.get(pair_id, {})
        pair, meta_new = enrich_with_trade_signal(pair, meta_old)
        PAIR_META_STORE[pair_id] = meta_new

        # Enrich pair with evaluated data
        pair["rug_status"] = rug_status
        pair["rug_score"] = rug_score
        pair["rug_reasons"] = rug_reasons
        pair["rug_link"] = rug_link

        passed_pairs.append(pair)

    if passed_pairs:
        all_tracked = update_pair_tracking(passed_pairs)
        if all_tracked:
            log_text = build_alert_log(all_tracked)  # includes 🔥 for count≥5
            send_telegram_message(log_text)

if __name__ == "__main__":
    main()
