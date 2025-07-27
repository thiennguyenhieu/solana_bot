# 🔍 Solana x100 Token Scanner Bot

This bot scans new Solana tokens using DEX Screener and evaluates them based on filters like volume, liquidity, transaction activity, and rug risk. It logs and sends filtered results to a Telegram channel.

## ✅ Features

- Scans Solana token pairs in real-time.
- Categorizes tokens: 🟥 Very Degen, 🟧 Degen, 🟨 Mid-Cap, 🟩 Old Mid-Cap.
- Evaluates risk with Rugcheck API.
- Sends formatted alerts to Telegram.
- Scheduled to run every 30 minutes.

## 📦 Requirements

```bash
pip install -r requirements.txt
```

## 🔑 Environment Variables

Set these variables in your system or in a `.env` file:

```env
TELEGRAM_BOT_TOKEN=<your_bot_token>
TELEGRAM_CHAT_ID=<your_chat_id>
```

You can get your chat ID by sending a message to your bot, then calling:

```bash
curl https://api.telegram.org/bot<your_bot_token>/getUpdates
```

## 🚀 Run Manually

```bash
python main.py
```

## ⏱️ Schedule with Interval

```bash
python scheduler.py
```

## 🧠 Logic Overview

- Token data fetched from DEX Screener.
- Pair details evaluated for:
  - Liquidity
  - FDV (Fully Diluted Valuation)
  - Transaction count
  - Volume (1h/24h)
  - Age of token
- Rugcheck safety evaluation via API.
- Telegram message includes:
  - Category + Symbol
  - Price, Market Cap, Liquidity, 24h Change
  - Rugcheck score and reasons (if any)
  - Dex link + Rugcheck link

## 📬 Telegram Output Format

```
🟧 Degen | NARTO / SOL
💰 Price: $0.001852 | MC: $1,852,047 | Liquidity: $156,032 | 24H Change: 12301%
🟠 Risky | Score: 55 / 100
⚠️ Top 1 holder > 10%
⚠️ LP locked < 90%
🔍 https://rugcheck.xyz/tokens/xxxxxxx
🔗 https://dexscreener.com/solana/xxxxxxxxxx
```

## 📁 Project Structure

```
solana_bot/
├── main.py
├── scheduler.py
├── screener.py
├── filters.py
├── rugcheck.py
├── telegram_bot.py
├── requirements.txt
└── README.md
```

---

Built with ❤️ for x100 hunters on Solana.