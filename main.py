from screener import get_solana_token_profiles, get_pair_address, get_pair_details
from filters import score_market
from rugcheck import get_rugcheck_report, evaluate_rugcheck
from tracker import update_pair_tracking
from telegram_bot import send_telegram_message
from log_formatter import build_alert_log
from trader import enrich_with_trade_signal, load_trade_meta_from_tracked, save_trade_meta

def main():
    # Load meta for currently-tracked pairs only (keeps RAM bounded)
    load_trade_meta_from_tracked("tracked_pairs.json")

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

        res = score_market(pair)
        if res["label"] not in ("x10-ready", "x100-candidate"):
            continue

        pair["market_label"] = res["label"]
        pair["market_score"] = res["score"]
        pair["potential_multiple"] = res["potential_multiple"]
        pair["market_checks"] = res["market"]  # raw sub-checks + reasons

        base = pair.get("baseToken", {})
        mint_address = base.get("address", "")

        rugcheck_data = get_rugcheck_report(mint_address)
        rug_status, rug_score, rug_reasons, rug_link = evaluate_rugcheck(rugcheck_data)

        # Skip if rug score too low
        if rug_score < 80:
            continue

        pair["rug_status"] = rug_status
        pair["rug_score"] = rug_score
        pair["rug_reasons"] = rug_reasons
        pair["rug_link"] = rug_link

        # attach trade signal
        pair = enrich_with_trade_signal(pair)

        passed_pairs.append(pair)

    if passed_pairs:
        all_tracked = update_pair_tracking(passed_pairs)
        if all_tracked:
            # Save TRADE_META filtered to currently tracked ids
            active_ids = {p.get("pairAddress") for p in all_tracked if p.get("pairAddress")}
            save_trade_meta(active_ids)

            log_text = build_alert_log(all_tracked)  # includes 🔥 for count≥5
            send_telegram_message(log_text)

if __name__ == "__main__":
    main()
