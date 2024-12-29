# init_db.py
import asyncio
from database import engine
from models import Base  # В models.py у вас Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        # Удаляем все таблицы, если нужно "с чистого листа"
        # await conn.run_sync(Base.metadata.drop_all)

        # Создаём все таблицы
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_db())
