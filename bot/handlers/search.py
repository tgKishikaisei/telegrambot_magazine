import os
import json
from aiogram import Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.handlers.catalog import send_product_card  # используем уже готовую функцию
from bot.bot_instance import bot

router = Router()

# Загрузка списка товаров из data.json
DATA_FILE = os.path.join(os.path.dirname(__file__), '../../data/data.json')
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)
    products = data.get("products", [])

@router.message(lambda message: message.text == "🔎 Поиск")
async def search_prompt(message: types.Message):
    await message.answer("Введите ключевое слово для поиска товара:")

@router.message(lambda message: message.text and message.text.lower().startswith("filter:"))
async def filter_search(message: types.Message):
    # Пример запроса: "filter: category=2 price_min=1000 price_max=5000"
    query = message.text.lower().replace("filter:", "").strip()
    filters = {}
    for part in query.split():
        if "=" in part:
            key, value = part.split("=", 1)
            filters[key] = value
    results = products
    if "category" in filters:
        try:
            cat_id = int(filters["category"])
            results = [p for p in results if p["category_id"] == cat_id]
        except Exception:
            pass
    if "price_min" in filters:
        try:
            price_min = float(filters["price_min"])
            results = [p for p in results if p["price"] >= price_min]
        except Exception:
            pass
    if "price_max" in filters:
        try:
            price_max = float(filters["price_max"])
            results = [p for p in results if p["price"] <= price_max]
        except Exception:
            pass
    if results:
        for product in results:
            await send_product_card(message.chat.id, product)
    else:
        await message.answer("Ничего не найдено по заданным критериям.")

@router.message(lambda message: message.text and not message.text.startswith("/") and not message.text.lower().startswith("filter:"))
async def simple_search(message: types.Message):
    query = message.text.strip().lower()
    results = [p for p in products if query in p["name"].lower()]
    if results:
        for product in results:
            await send_product_card(message.chat.id, product)
    else:
        await message.answer("Ничего не найдено.")

@router.message(lambda message: message.text and not message.text.startswith("/"))
async def text_handler(message: types.Message, state):
    current_state = await state.get_state()

    # 1) Если ждём контакт
    if current_state == "CheckoutState:waiting_for_contact":
        await state.update_data(contact=message.text)
        await message.answer("Есть промокод? Если да, введите его, иначе напишите 'нет'.")
        await state.set_state("CheckoutState:waiting_for_promocode")
        return

    # 2) Если ждём промокод
    if current_state == "CheckoutState:waiting_for_promocode":
        code = message.text.strip().upper()
        discount = 0
        PROMOCODES = {"SALE10": 0.1, "VIP": 0.2}
        if code in PROMOCODES:
            discount = PROMOCODES[code]
            await message.answer(f"Промокод принят! Скидка {int(discount * 100)}%.")
        else:
            if code != "НЕТ":
                await message.answer("Промокод не найден, продолжаем без скидки.")
        await state.update_data(discount=discount)

        telegram_id = message.from_user.id
        from bot.database.session import get_session
        from sqlalchemy import select
        from bot.models import CartItem, Product, User
        async with get_session() as session:
            stmt_user = select(User).where(User.telegram_id == telegram_id)
            result_user = await session.execute(stmt_user)
            db_user = result_user.scalar_one_or_none()
            total = 0
            if db_user:
                stmt_cart = select(CartItem, Product).join(Product, Product.id == CartItem.product_id).where(
                    CartItem.user_id == db_user.id)
                result_cart = await session.execute(stmt_cart)
                rows = result_cart.all()
                for cart_item, product in rows:
                    total += product.price * cart_item.quantity

            if discount > 0:
                total = int(total * (1 - discount))

            await state.update_data(total=total)
            await message.answer(f"К оплате: {total} руб.\nПришлите любое сообщение, чтобы выполнить оплату (фиктивно).")
            await state.set_state("CheckoutState:waiting_for_payment")
        return

    # 3) Если ждём «оплату» (фиктивно)
    if current_state == "CheckoutState:waiting_for_payment":
        from bot.database.session import get_session
        from sqlalchemy import select
        from bot.models import CartItem, Product, User, Order, OrderItem
        data_state = await state.get_data()
        telegram_id = message.from_user.id

        async with get_session() as session:
            stmt_user = select(User).where(User.telegram_id == telegram_id)
            result_user = await session.execute(stmt_user)
            db_user = result_user.scalar_one_or_none()

            if not db_user:
                await message.answer("У вас нет товаров в корзине.")
                await state.clear()
                return

            stmt_cart = select(CartItem, Product).join(Product, Product.id == CartItem.product_id).where(
                CartItem.user_id == db_user.id)
            result_cart = await session.execute(stmt_cart)
            rows = result_cart.all()

            if not rows:
                await message.answer("Корзина пуста, нельзя оформить заказ.")
                await state.clear()
                return

            order = Order(
                user_id=db_user.id,
                status="Принят",
                contact_info=data_state.get("contact", ""),
                total=data_state.get("total", 0)
            )
            session.add(order)
            await session.flush()  # чтобы получить order.id

            for cart_item, product in rows:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=cart_item.quantity,
                    price=product.price
                )
                session.add(order_item)

            stmt_delete = CartItem.__table__.delete().where(CartItem.user_id == db_user.id)
            await session.execute(stmt_delete)
            await session.commit()

            order_id = order.id

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")]
        ])
        await message.answer(f"Заказ #{order_id} оформлен! Мы с вами свяжемся.", reply_markup=markup)
        await state.clear()
        # bot уже импортирован из bot.bot_instance: импорт из bot.main был циклическим.
        await bot.send_message(
            chat_id=os.getenv("ADMIN_ID"),
            text=f"Новый заказ #{order_id} от пользователя {telegram_id} на сумму {data_state.get('total', 0)} руб."
        )
        return

    # 4) Иначе это поиск товара
    query = message.text.strip().lower()
    results = [p for p in products if query in p["name"].lower()]
    if results:
        from bot.handlers.catalog import send_product_card
        for product in results:
            await send_product_card(message.chat.id, product)
    else:
        await message.answer("Ничего не найдено.")
