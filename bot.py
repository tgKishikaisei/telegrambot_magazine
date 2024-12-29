# bot.py
import os
import json
import asyncio

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram.filters import Command

from sqlalchemy import select
from dotenv import load_dotenv

from models import CartItem, User, Product, OrderItem, Order
from database import get_session

# Загружаем .env (TOKEN, ADMIN_ID, и т.д.)
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в .env")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID не установлен в .env")

# Создаём объекты бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# Загружаем данные о товарах и категориях из data.json
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    categories = data["categories"]
    products = data["products"]

# Словарь промокодов
PROMOCODES = {"SALE10": 0.1, "VIP": 0.2}


# Состояния для оформления заказа (FSM)
class CheckoutState(StatesGroup):
    waiting_for_contact = State()
    waiting_for_promocode = State()
    waiting_for_payment = State()


# --------------------
# Команда /start, /menu
# --------------------
@router.message(Command(commands=["start", "menu"]))
async def start_menu(message: types.Message):
    """
    Приветственное меню с кнопками.
    """
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🛍️ Каталог"),
                KeyboardButton(text="🔎 Поиск")
            ],
            [
                KeyboardButton(text="🛒 Корзина"),
                KeyboardButton(text="👤 Личный кабинет")
            ],
            [
                KeyboardButton(text="ℹ️ Инфо о доставке")
            ]
        ],
        resize_keyboard=True
    )
    await message.answer("Добро пожаловать в наш магазин!", reply_markup=kb)


# --------------------
# Кнопка "Каталог"
# --------------------
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

    # Отправляем карточку каждого товара
    for product in cat_products:
        await send_product_card(callback_query.from_user.id, product)
    await callback_query.answer()


async def send_product_card(chat_id, product):
    """
    Отправить карточку товара с кнопкой "Добавить в корзину".
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить в корзину", callback_data=f"add_{product['id']}")]
        ]
    )
    text = (
        f"📦 {product['name']}\n"
        f"💰 Цена: {product['price']} руб.\n"
        f"📝 {product['description']}"
    )
    await bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)


# --------------------
# Добавить в корзину
# --------------------
@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback_query: types.CallbackQuery):
    product_id = int(callback_query.data.split("_")[1])
    telegram_id = callback_query.from_user.id  # Telegram user_id

    async with get_session() as session:
        # Ищем или создаём User с таким telegram_id
        stmt_user = select(User).where(User.telegram_id == telegram_id)
        result_user = await session.execute(stmt_user)
        db_user = result_user.scalar_one_or_none()

        if not db_user:
            db_user = User(telegram_id=telegram_id)
            session.add(db_user)
            await session.commit()  # Теперь db_user.id заполнен

        # Ищем позицию cart_item
        stmt_cart = select(CartItem).where(
            CartItem.user_id == db_user.id,
            CartItem.product_id == product_id
        )
        result_cart = await session.execute(stmt_cart)
        cart_item = result_cart.scalar_one_or_none()

        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(
                user_id=db_user.id,  # В cart_items пишем db_user.id
                product_id=product_id,
                quantity=1
            )
            session.add(cart_item)

        await session.commit()

    await callback_query.answer("✅ Товар добавлен в корзину!")


# --------------------
# Показать корзину
# --------------------
@router.message(F.text == "🛒 Корзина")
async def show_cart(message: types.Message):
    """
    Показывает корзину пользователя.
    """
    await view_cart(message.from_user.id, message)


async def view_cart(telegram_id: int, message_or_callback: types.Message | types.CallbackQuery):
    async with get_session() as session:
        # Находим db_user
        stmt_user = select(User).where(User.telegram_id == telegram_id)
        result_user = await session.execute(stmt_user)
        db_user = result_user.scalar_one_or_none()

        if not db_user:
            # Пользователь в БД ещё не создан (корзины нет)
            if isinstance(message_or_callback, types.Message):
                await message_or_callback.answer("🛒 Ваша корзина пуста.")
            else:
                await message_or_callback.message.edit_text("🛒 Ваша корзина пуста.")
            return

        # Достаём товары из cart_items + products
        stmt_cart = (
            select(CartItem, Product)
            .join(Product, Product.id == CartItem.product_id)
            .where(CartItem.user_id == db_user.id)
        )
        result_cart = await session.execute(stmt_cart)
        rows = result_cart.all()  # [(CartItem, Product), ...]

        if not rows:
            # Корзина пуста
            if isinstance(message_or_callback, types.Message):
                await message_or_callback.answer("🛒 Ваша корзина пуста.")
            else:
                await message_or_callback.message.edit_text("🛒 Ваша корзина пуста.")
            return

        text = "🛒 Ваша корзина:\n"
        total = 0
        for cart_item, product in rows:
            subtotal = product.price * cart_item.quantity
            total += subtotal
            text += f"• {product.name} × {cart_item.quantity} — {subtotal} руб.\n"

        text += f"\n💰 Итого: {total} руб."

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart"),
                    InlineKeyboardButton(text="📦 Оформить заказ", callback_data="checkout")
                ]
            ]
        )

        if isinstance(message_or_callback, types.Message):
            await message_or_callback.answer(text, reply_markup=keyboard)
        else:
            await message_or_callback.message.edit_text(text, reply_markup=keyboard)


# --------------------
# Очистить корзину
# --------------------
@router.callback_query(F.data == "clear_cart")
async def clear_cart_callback(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    async with get_session() as session:
        # Ищем User
        stmt_user = select(User).where(User.telegram_id == telegram_id)
        result_user = await session.execute(stmt_user)
        db_user = result_user.scalar_one_or_none()

        if db_user:
            stmt_delete = (
                CartItem.__table__
                .delete()
                .where(CartItem.user_id == db_user.id)
            )
            await session.execute(stmt_delete)
            await session.commit()

    await callback_query.answer("Корзина очищена!")
    await callback_query.message.edit_text("Корзина пустая.")


# --------------------
# Кнопка "Оформить заказ"
# --------------------
@router.callback_query(F.data == "checkout")
async def checkout(callback_query: types.CallbackQuery, state: FSMContext):
    telegram_id = callback_query.from_user.id
    async with get_session() as session:
        # Проверяем, есть ли товары в корзине
        stmt_user = select(User).where(User.telegram_id == telegram_id)
        result_user = await session.execute(stmt_user)
        db_user = result_user.scalar_one_or_none()

        if not db_user:
            await callback_query.answer("Корзина пуста!", show_alert=True)
            return

        stmt_cart = select(CartItem).where(CartItem.user_id == db_user.id)
        result_cart = await session.execute(stmt_cart)
        items_in_cart = result_cart.scalars().all()

        if not items_in_cart:
            await callback_query.answer("Корзина пуста!", show_alert=True)
            return

    await callback_query.answer()
    # Редактируем сообщение, чтобы убрать кнопки
    await callback_query.message.edit_text("Пожалуйста, пришлите свой контакт (телефон, адрес):")
    await state.set_state(CheckoutState.waiting_for_contact)


# --------------------
# Кнопка "👤 Личный кабинет" (заказы)
# --------------------
@router.message(F.text == "👤 Личный кабинет")
async def personal_account(message: types.Message):
    telegram_id = message.from_user.id
    async with get_session() as session:
        stmt_user = select(User).where(User.telegram_id == telegram_id)
        result_user = await session.execute(stmt_user)
        db_user = result_user.scalar_one_or_none()

        if not db_user:
            await message.answer("У вас пока нет заказов.")
            return

        stmt_orders = select(Order).where(Order.user_id == db_user.id)
        result_orders = await session.execute(stmt_orders)
        orders_list = result_orders.scalars().all()

        if not orders_list:
            await message.answer("У вас пока нет заказов.")
            return

        text = "📜 История заказов:\n"
        for order in orders_list:
            text += f"Заказ #{order.id}: {order.status} на сумму {order.total} руб.\n"

        await message.answer(text)


# --------------------
# Кнопка "ℹ️ Инфо о доставке"
# --------------------
@router.message(F.text == "ℹ️ Инфо о доставке")
async def info(message: types.Message):
    text = (
        "ℹ️ Информация о доставке:\n\n"
        "🚚 Доставка по всей стране.\n"
        "⏳ Срок доставки: 3-7 рабочих дней.\n"
        "📞 Контакт: +7 999 123-45-67\n"
        "📧 Email: info@shop.com"
    )
    await message.answer(text)


# --------------------
# Кнопка "🔎 Поиск"
# --------------------
@router.message(F.text == "🔎 Поиск")
async def search_prompt(message: types.Message):
    await message.answer("Введите ключевое слово для поиска товара:")


# --------------------
# Обработка текстовых сообщений
# --------------------
class CheckoutState(StatesGroup):
    waiting_for_contact = State()
    waiting_for_promocode = State()
    waiting_for_payment = State()


@router.message()
async def text_handler(message: types.Message, state: FSMContext):
    """
    Обрабатывает текст, либо как часть оформления заказа, либо поиск.
    """
    current_state = await state.get_state()

    # 1) Если ждём контакт
    if current_state == CheckoutState.waiting_for_contact.state:
        await state.update_data(contact=message.text)
        await message.answer("Есть промокод? Если да, введите его, иначе напишите 'нет'.")
        await state.set_state(CheckoutState.waiting_for_promocode)
        return

    # 2) Если ждём промокод
    if current_state == CheckoutState.waiting_for_promocode.state:
        code = message.text.strip().upper()
        discount = 0
        if code in PROMOCODES:
            discount = PROMOCODES[code]
            await message.answer(f"Промокод принят! Скидка {int(discount * 100)}%.")
        else:
            if code != "НЕТ":
                await message.answer("Промокод не найден, продолжаем без скидки.")
        await state.update_data(discount=discount)

        # Считаем итог по корзине
        telegram_id = message.from_user.id
        async with get_session() as session:
            # Ищем db_user
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
            await message.answer(f"К оплате: {total} руб. Пришлите любое сообщение, чтобы выполнить оплату (фиктивно).")
            await state.set_state(CheckoutState.waiting_for_payment)
        return

    # 3) Если ждём «оплату» (фиктивно)
    if current_state == CheckoutState.waiting_for_payment.state:
        data = await state.get_data()
        telegram_id = message.from_user.id

        # Оформляем заказ
        async with get_session() as session:
            # Ищем пользователя
            stmt_user = select(User).where(User.telegram_id == telegram_id)
            result_user = await session.execute(stmt_user)
            db_user = result_user.scalar_one_or_none()

            if not db_user:
                # Если нет пользователя, значит корзина реально пуста
                await message.answer("У вас нет товаров в корзине.")
                await state.clear()
                return

            # Собираем позиции
            stmt_cart = select(CartItem, Product).join(Product, Product.id == CartItem.product_id).where(
                CartItem.user_id == db_user.id)
            result_cart = await session.execute(stmt_cart)
            rows = result_cart.all()

            if not rows:
                await message.answer("Корзина пуста, нельзя оформить заказ.")
                await state.clear()
                return

            # Создаём заказ
            order = Order(
                user_id=db_user.id,
                status="Принят",
                contact_info=data.get("contact", ""),
                total=data.get("total", 0)
            )
            session.add(order)
            await session.flush()  # Получить order.id

            # Создаём OrderItem
            for cart_item, product in rows:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=cart_item.quantity,
                    price=product.price
                )
                session.add(order_item)

            # Очищаем корзину (cart_items)
            stmt_delete = CartItem.__table__.delete().where(CartItem.user_id == db_user.id)
            await session.execute(stmt_delete)
            await session.commit()

            order_id = order.id

        await message.answer(f"Заказ #{order_id} оформлен! Мы с вами свяжемся.")
        await state.clear()

        # Уведомляем админа
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Новый заказ #{order_id} от пользователя {telegram_id} на сумму {data.get('total', 0)} руб."
        )
        return

    # 4) Иначе это поиск товара
    query = message.text.strip().lower()
    results = [p for p in products if query in p["name"].lower()]
    if results:
        for product in results:
            await send_product_card(message.chat.id, product)
    else:
        await message.answer("Ничего не найдено.")


# ---------------------
# Запуск бота
# ---------------------
async def main():
    dp.include_router(router)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
