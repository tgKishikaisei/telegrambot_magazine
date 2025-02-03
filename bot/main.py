# bot/main.py
import asyncio
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

from bot.bot_instance import bot
from handlers import register_all_handlers

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID"))
if not ADMIN_ID:
    raise ValueError("ADMIN_ID не установлен в .env")

# Создаём объекты бота и диспетчера

dp = Dispatcher(storage=MemoryStorage())

# ---------------------
# Запуск бота
# ---------------------
async def main():
    # Регистрируем все обработчики из пакета handlers
    register_all_handlers(dp)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
