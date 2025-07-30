# 🔍 Solana x100 Token Scanner Bot

This bot scans newly listed Solana tokens using DEX Screener and evaluates them based on a set of checklist filters designed to find potential "x100" tokens. It tracks how often promising pairs appear and sends alerts to Telegram when a token consistently meets criteria.

---

## ✅ Features

- Pulls tokens from 3 DEX Screener sources:
  - `/token-boosts/latest/v1`
  - `/token-boosts/top/v1`
  - `/token-profiles/latest/v1`
- Merges and deduplicates token list
- Evaluates each token pair for:
  - Market cap, FDV, liquidity, volume
  - Transaction momentum & buy/sell ratio
  - Rugcheck risk score and insider flags
  - Price action and liquidity change
  - Good entry point based on MA trends
- Tracks frequency of token appearance
- Sends alert to Telegram when a token appears ≥ 5 times
- Updates local `pair_tracker.json` every run

---

## 📦 Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Set in `.env` or system env:

```env
TELEGRAM_BOT_TOKEN=<your_bot_token>
TELEGRAM_CHAT_ID=<your_chat_id>
```

You can find `chat_id` via:

```bash
curl https://api.telegram.org/bot<your_bot_token>/getUpdates
```

---

## 🚀 Usage

### Manual Run

```bash
python main.py
```

### Scheduled Scanning

```bash
python scheduler.py
```

This runs `main.py` every 10 minutes.

---

## 📬 Telegram Message Format

```
✅ PASSED: 6HgRt...hRJtP
NARTO / SOL
💰 Price: $0.001852 | MC: $1,852,047 | Liquidity: $156,032 | 24H Change: 12301%
✅ Entry Signal Detected
🟠 Risky | Score: 55 / 100
⚠️ Top 1 holder > 10%
⚠️ LP locked < 90%
⚠️ Only a few users are providing liquidity
🔍 https://rugcheck.xyz/tokens/xxxxxxxx
🔗 https://dexscreener.com/solana/xxxxxxxx
```

---

## 📁 Project Structure

```
solana_bot/
├── main.py               # Scanning logic
├── screener.py           # DEX Screener API helpers
├── filters.py            # X100 token filter logic
├── rugcheck.py           # Rugcheck API integration
├── tracker.py            # Pair appearance tracker
├── telegram_bot.py       # Telegram message sending
├── scheduler.py          # Interval execution
├── pair_tracker.json     # Stores appearance counts
├── requirements.txt
└── README.md
```

---

## 🧠 Key Criteria

- Market Cap: $100K – $10M  
- Liquidity: > $50K  
- FDV < $50M  
- Volume 24h: > $500K  
- Buys 1h: ≥ 50  
- Buy/Sell Ratio > 1.0  
- Momentum: volume and txns increasing  
- No large LP removal recently  
- Rugcheck Score ≥ 70 and no critical risks  
- Price change 1h < 150%, 24h < 500%  
- Entry point: Price ≥ MA5 ≥ MA15

---

Built with ❤️ for alpha hunters on Solana.