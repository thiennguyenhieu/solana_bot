import os
from telegram import Bot

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "<your_bot_token>")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "<your_chat_id>")

bot = Bot(token=TELEGRAM_BOT_TOKEN)

def send_telegram_message(text: str):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        print(f"[Telegram] Failed to send message: {e}")
