# bot/main.py
import asyncio
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

from bot.bot_instance import bot
from bot.handlers import register_all_handlers

load_dotenv()
# Понятная ошибка при пустом ADMIN_ID вместо TypeError из int(None).
_admin_id = os.getenv("ADMIN_ID", "")
if not _admin_id.strip().isdigit():
    raise ValueError("ADMIN_ID не установлен в .env (нужен числовой Telegram ID)")
ADMIN_ID = int(_admin_id)

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
