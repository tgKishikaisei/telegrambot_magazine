# bot/database/init_db.py
import asyncio
from bot.models import Base  # Импортируйте все ваши модели через Base
from bot.database.session import engine  # engine должен быть AsyncEngine

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Все таблицы созданы!")

if __name__ == "__main__":
    asyncio.run(init_db())

