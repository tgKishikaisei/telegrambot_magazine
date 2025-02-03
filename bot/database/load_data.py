import asyncio
import json
import os

from bot.database.session import get_session, engine
from bot.models import Category, Product
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

# Определяем базовую директорию текущего файла и формируем путь к файлу data.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, "../../data/data.json")  # Если структура репозитория, как описано выше

async def load_data():
    # 1) Читаем data.json
    if not os.path.exists(JSON_FILE):
        print(f"Файл {JSON_FILE} не найден!")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    categories_data = data.get("categories", [])
    products_data = data.get("products", [])

    async with get_session() as session:
        # 2) Вставляем (или обновляем) категории
        for cat in categories_data:
            cat_id = cat.get("id")
            cat_name = cat.get("name")

            # Проверим, есть ли уже такая категория в базе
            stmt = select(Category).where(Category.id == cat_id)
            result = await session.execute(stmt)
            db_cat = result.scalar_one_or_none()

            if db_cat is None:
                # Создаём новую категорию
                new_cat = Category(id=cat_id, name=cat_name)
                session.add(new_cat)
                print(f"Добавлена категория: {cat_name}")
            else:
                # Обновляем название, если необходимо
                db_cat.name = cat_name
                print(f"Обновлена категория: {cat_name}")

        # 3) Сохраняем изменения, чтобы категории точно были созданы (иначе товары не смогут ссылаться на них)
        try:
            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            print("Ошибка при вставке категорий:", e)
            return

        # 4) Вставляем (или обновляем) товары
        for prod in products_data:
            p_id = prod.get("id")
            p_cat_id = prod.get("category_id")
            p_name = prod.get("name")
            p_price = prod.get("price")
            p_desc = prod.get("description")

            # Проверим, есть ли такая категория
            stmt_cat = select(Category).where(Category.id == p_cat_id)
            result_cat = await session.execute(stmt_cat)
            db_cat = result_cat.scalar_one_or_none()

            if db_cat is None:
                print(f"Пропускаем товар id={p_id}: Категории {p_cat_id} нет в базе!")
                continue  # либо можно создать категорию автоматически

            # Проверим, есть ли уже такой товар
            stmt_prod = select(Product).where(Product.id == p_id)
            result_prod = await session.execute(stmt_prod)
            db_prod = result_prod.scalar_one_or_none()

            if db_prod is None:
                # Создаём новый товар
                new_prod = Product(
                    id=p_id,
                    name=p_name,
                    price=p_price,
                    description=p_desc,
                    category_id=p_cat_id
                )
                session.add(new_prod)
                print(f"Добавлен товар: {p_name}")
            else:
                # Обновляем поля товара
                db_prod.name = p_name
                db_prod.price = p_price
                db_prod.description = p_desc
                db_prod.category_id = p_cat_id
                print(f"Обновлен товар: {p_name}")

        # 5) Пробуем зафиксировать изменения
        try:
            await session.commit()
            print("Данные успешно загружены в базу!")
        except IntegrityError as e:
            await session.rollback()
            print("Ошибка при вставке товаров:", e)

if __name__ == "__main__":
    asyncio.run(load_data())
