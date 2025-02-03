import os
import json
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from aiogram.types import FSInputFile
from bot.bot_instance import bot

router = Router()

# Загрузка данных о категориях и товарах из data.json
DATA_FILE = os.path.join(os.path.dirname(__file__), '../../data/data.json')
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)
    categories = data["categories"]
    products = data["products"]

@router.message(F.text == "🛍️ Каталог")
async def show_categories(message: types.Message):
    buttons = []
    for c in categories:
        buttons.append([InlineKeyboardButton(text=c["name"], callback_data=f"cat_{c['id']}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите категорию:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("cat_"))
async def show_products_in_category(callback_query: types.CallbackQuery):
    cat_id = int(callback_query.data.split("_")[1])
    cat_products = [p for p in products if p["category_id"] == cat_id]
    if not cat_products:
        await callback_query.message.answer("В этой категории пока нет товаров.")
        await callback_query.answer()
        return
    # Покажем первую страницу
    await send_products_page(callback_query, cat_products, page=0, cat_id=cat_id)
    await callback_query.answer()


async def send_products_page(callback_query, product_list, page, cat_id):
    items_per_page = 5
    total_items = len(product_list)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    start = page * items_per_page
    end = start + items_per_page
    page_products = product_list[start:end]

    text = f"Товары (страница {page + 1} из {total_pages}):"
    # Создаем клавиатуру с кнопками для каждого товара
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for prod in page_products:
        # Каждая кнопка вызывает callback_data "prod_{id}"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"{prod['name']} — {prod['price']} руб.", callback_data=f"prod_{prod['id']}")
        ])
    # Добавляем навигационные кнопки и кнопку "🔙 Главное меню"
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"cat_page_{cat_id}_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"cat_page_{cat_id}_{page+1}"))
    if nav_buttons:
        keyboard.inline_keyboard.append(nav_buttons)
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")])

    await callback_query.message.edit_text(text, reply_markup=keyboard)



@router.callback_query(lambda c: c.data and c.data.startswith("cat_page_"))
async def paginate_category(callback_query: types.CallbackQuery):
    # Формат: cat_page_{cat_id}_{page}
    parts = callback_query.data.split("_")
    cat_id = int(parts[2])
    page = int(parts[3])
    cat_products = [p for p in products if p["category_id"] == cat_id]
    await send_products_page(callback_query, cat_products, page, cat_id)
    await callback_query.answer()

@router.callback_query(lambda c: c.data and c.data.startswith("prod_"))
async def show_product_card_from_list(callback_query: types.CallbackQuery):
    product_id = int(callback_query.data.split("_")[1])
    product = next((p for p in products if p["id"] == product_id), None)
    if product:
        await send_product_card(callback_query.from_user.id, product)
    await callback_query.answer()


import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.bot_instance import bot


import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from bot.bot_instance import bot

async def send_product_card(chat_id, product):
    """
    Отправить карточку товара с кнопками "➕ Добавить в корзину" и "❤️ Избранное".
    Поддерживает отправку фото как по URL, так и из локального файла.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить в корзину", callback_data=f"add_{product['id']}"),
            InlineKeyboardButton(text="❤️ Избранное", callback_data=f"fav_{product['id']}")
        ]
    ])

    caption = (
        f"📦 {product['name']}\n"
        f"💰 Цена: {product['price']} руб.\n"
        f"📝 {product['description']}"
    )

    photo = product.get("photo")
    if photo:
        if photo.startswith("http://") or photo.startswith("https://"):
            # Отправляем фото по URL
            await bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                reply_markup=keyboard
            )
        else:
            # Отправляем локальное фото, если файл существует
            if os.path.exists(photo):
                input_file = FSInputFile(photo, chunk_size=65536)
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=input_file,
                    caption=caption,
                    reply_markup=keyboard,
                    request_timeout=60
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption + "\n[Фото не найдено]",
                    reply_markup=keyboard
                )
    else:
        # Если фото не задано – отправляем текстовое сообщение
        await bot.send_message(
            chat_id=chat_id,
            text=caption,
            reply_markup=keyboard
        )


    # Записываем просмотр в историю
    from bot.database.session import get_session
    from bot.models import User
    from bot.models.history import History
    async with get_session() as session:
        # Найдем пользователя по telegram_id (chat_id)
        stmt = select(User).where(User.telegram_id == chat_id)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        # Если пользователь не найден, создадим его
        if not db_user:
            db_user = User(telegram_id=chat_id)
            session.add(db_user)
            await session.commit()  # Теперь db_user.id заполнен

        # Теперь используем первичный ключ пользователя (db_user.id) для записи истории
        history = History(user_id=db_user.id, product_id=product['id'])
        session.add(history)
        await session.commit()
