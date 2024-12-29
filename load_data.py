import asyncio
import json
import os

from database import get_session, engine
from models import Category, Product
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

JSON_FILE = "data.json"  # путь к вашему JSON


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
            cat_id = cat["id"]
            cat_name = cat["name"]

            # Проверим, есть ли уже такая категория в базе
            stmt = select(Category).where(Category.id == cat_id)
            result = await session.execute(stmt)
            db_cat = result.scalar_one_or_none()

            if db_cat is None:
                # Создаём новую
                new_cat = Category(id=cat_id, name=cat_name)
                session.add(new_cat)
            else:
                # Обновляем name, если нужно
                db_cat.name = cat_name

        # 3) Сохраняем изменения, чтобы категории точно были созданы
        #    (иначе products не сможет ссылаться на категории)
        try:
            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            print("Ошибка при вставке категорий:", e)
            return

        # 4) Вставляем (или обновляем) товары
        for prod in products_data:
            p_id = prod["id"]
            p_cat_id = prod["category_id"]
            p_name = prod["name"]
            p_price = prod["price"]
            p_desc = prod["description"]

            # Проверим, есть ли такая категория
            stmt_cat = select(Category).where(Category.id == p_cat_id)
            result_cat = await session.execute(stmt_cat)
            db_cat = result_cat.scalar_one_or_none()

            if db_cat is None:
                print(f"Пропускаем товар id={p_id}: Категории {p_cat_id} нет в базе!")
                continue  # либо пропустить, либо создать категорию автоматически

            # Проверим, есть ли уже такой товар
            stmt_prod = select(Product).where(Product.id == p_id)
            result_prod = await session.execute(stmt_prod)
            db_prod = result_prod.scalar_one_or_none()

            if db_prod is None:
                # Создаём новый
                new_prod = Product(
                    id=p_id,
                    name=p_name,
                    price=p_price,
                    description=p_desc,
                    category_id=p_cat_id
                )
                session.add(new_prod)
            else:
                # Обновляем поля
                db_prod.name = p_name
                db_prod.price = p_price
                db_prod.description = p_desc
                db_prod.category_id = p_cat_id

        # 5) Пробуем зафиксировать изменения
        try:
            await session.commit()
            print("Данные успешно загружены в базу!")
        except IntegrityError as e:
            await session.rollback()
            print("Ошибка при вставке товаров:", e)


if __name__ == "__main__":
    asyncio.run(load_data())
