# bot/bot_instance.py
import os
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в .env")

bot = Bot(token=TOKEN)
