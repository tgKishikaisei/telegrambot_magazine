from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select
from bot.database.session import get_session
from bot.models import CartItem, User, Product, Order, OrderItem
from bot.handlers.start_menu import start_menu
from bot.bot_instance import bot

# Например, в файле bot/handlers/cart.py или в отдельном файле (delivery.py)
from aiogram.fsm.state import StatesGroup, State

class CheckoutState(StatesGroup):
    waiting_for_contact = State()
    waiting_for_promocode = State()
    waiting_for_payment = State()
    waiting_for_delivery_option = State()   # Новый этап: выбор способа доставки
    waiting_for_address = State()           # Новый этап: ввод адреса доставки
    waiting_for_location = State()

router = Router()

@router.message(F.text == "🛒 Корзина")
async def show_cart(message: types.Message):
    await view_cart(message.from_user.id, message, page=0)

@router.callback_query(F.data == "choose_delivery")
async def choose_delivery(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Предлагаем выбрать способ доставки.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚶 Самовывоз", callback_data="delivery_self"),
            InlineKeyboardButton(text="🚚 Курьером", callback_data="delivery_courier")
        ],
        [
            InlineKeyboardButton(text="📦 Почтой", callback_data="delivery_post")
        ],
        [
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")
        ]
    ])
    await callback_query.message.edit_text("Выберите способ доставки:", reply_markup=keyboard)
    await state.set_state("CheckoutState:waiting_for_delivery_option")
    await callback_query.answer()

@router.callback_query(F.data.in_(["delivery_self", "delivery_courier", "delivery_post"]))
async def process_delivery_option(callback_query: types.CallbackQuery, state: FSMContext):
    option = callback_query.data
    await state.update_data(delivery_option=option)
    if option in ["delivery_courier", "delivery_post"]:
        # Генерируем клавиатуру для выбора типа ввода адреса
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Ввести адрес текстом", callback_data="input_address"),
                InlineKeyboardButton(text="Отправить геолокацию", callback_data="input_location")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="choose_delivery")
            ]
        ])
        await callback_query.message.edit_text(
            "Как вы хотите отправить адрес?",
            reply_markup=keyboard
        )
    else:
        # Самовывоз
        # Бот сообщает адрес, куда подъехать, и завершаем заказ
        pickup_address = "г. Москва, ул. Примерная, д.1"  # пример
        await callback_query.message.edit_text(
            f"Вы выбрали самовывоз. Забрать заказ можно по адресу: {pickup_address}.\nСпасибо за покупку!"
        )
        await state.clear()
    await callback_query.answer()

@router.callback_query(F.data == "input_address")
async def ask_for_text_address(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text("Введите адрес доставки (улица, дом, квартира и т.п.):")
    await state.set_state(CheckoutState.waiting_for_address)
    await callback_query.answer()


@router.callback_query(F.data == "input_location")
async def ask_for_location(callback_query: types.CallbackQuery, state: FSMContext):
    location_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить геолокацию", request_location=True)]
        ],
        resize_keyboard=True
    )
    # Редактируем старое сообщение (если нужно) или отправляем новое
    await callback_query.message.edit_text(
        "Пожалуйста, нажмите кнопку, чтобы отправить свою геолокацию.\n"
        "Или введите адрес вручную, если хотите."
    )
    # Отправим новое сообщение с "ReplyKeyboardMarkup"
    await callback_query.message.answer(
        "Нажмите кнопку ниже, чтобы отправить геолокацию:",
        reply_markup=location_kb
    )
    await state.set_state(CheckoutState.waiting_for_location)
    await callback_query.answer()


@router.message(F.text & (F.state == CheckoutState.waiting_for_address))
async def process_address(message: types.Message, state: FSMContext):
    address = message.text.strip()
    await state.update_data(delivery_address=address)
    data = await state.get_data()
    # Здесь можно добавить сохранение информации о доставке в заказ
    text = (
        f"Заказ оформлен!\n\n"
        f"Способ доставки: {data.get('delivery_option')}\n"
        f"Адрес доставки: {address}\n"
        "Спасибо за покупку!"
    )
    # Удалим кнопки и вернём обычную клавиатуру
    await message.answer(text, reply_markup=types.ReplyKeyboardRemove())
    await state.clear()

@router.message(StateFilter(CheckoutState.waiting_for_location))
async def process_location(message: types.Message, state: FSMContext):
    if message.content_type == "location":
        print("Обработчик process_location вызван!")  # <-- отладочный вывод
        location = message.location
        lat = location.latitude
        lon = location.longitude

        # Сохраняем в состояние
        await state.update_data(delivery_lat=lat, delivery_lon=lon)

        text = (
            f"Заказ оформлен!\n"
            f"Мы получили координаты: {lat}, {lon}\n"
            "Спасибо за покупку!"
        )

        # Убираем клавиатуру (ReplyKeyboardRemove) и завершаем диалог
        await message.answer(text, reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
    else:
        # Предложим кнопку "Ввести адрес текстом" + "Назад"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Ввести адрес текстом", callback_data="input_address"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="choose_delivery")
            ]
        ])
        await message.answer(
            "Вы не отправили локацию. Выберите другой вариант:",
            reply_markup=keyboard
        )




@router.message(StateFilter(CheckoutState.waiting_for_location))
async def process_text_in_location_state(message: types.Message, state: FSMContext):
    """
    Если пользователь ввел текст, хотя бот ждёт геолокацию,
    можно или попросить всё-таки нажать кнопку, или перевести в режим ввода адреса.
    """
    await message.answer("Пожалуйста, нажмите кнопку для отправки геолокации или вернитесь назад.")


async def view_cart(telegram_id: int, msg_or_callback: types.Message | types.CallbackQuery, page: int = 0):
    async with get_session() as session:
        stmt_user = select(User).where(User.telegram_id == telegram_id)
        result_user = await session.execute(stmt_user)
        db_user = result_user.scalar_one_or_none()

        if not db_user:
            if isinstance(msg_or_callback, types.Message):
                await msg_or_callback.answer("🛒 Ваша корзина пуста.")
            else:
                await msg_or_callback.message.edit_text("🛒 Ваша корзина пуста.")
            return

        stmt_cart = (
            select(CartItem, Product)
            .join(Product, Product.id == CartItem.product_id)
            .where(CartItem.user_id == db_user.id)
        )
        result_cart = await session.execute(stmt_cart)
        rows = result_cart.all()

        if not rows:
            if isinstance(msg_or_callback, types.Message):
                await msg_or_callback.answer("🛒 Ваша корзина пуста.")
            else:
                await msg_or_callback.message.edit_text("🛒 Ваша корзина пуста.")
            return

        total = 0
        for cart_item, product in rows:
            total += product.price * cart_item.quantity

        items_per_page = 5
        total_items = len(rows)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        start = page * items_per_page
        end = start + items_per_page
        page_rows = rows[start:end]

        text = "🛒 Ваша корзина:\n"
        for cart_item, product in page_rows:
            subtotal = product.price * cart_item.quantity
            text += f"• {product.name} × {cart_item.quantity} — {subtotal} руб.\n"
        text += f"\n💰 Итого: {total} руб."
        if total_pages > 1:
            text += f"\nСтраница {page + 1} из {total_pages}."

        # Собираем клавиатуру для редактирования каждой позиции
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for cart_item, product in page_rows:
            row = [
                InlineKeyboardButton(text="➖", callback_data=f"decrease_{product.id}"),
                InlineKeyboardButton(text="❌", callback_data=f"remove_{product.id}"),
                InlineKeyboardButton(text="➕", callback_data=f"increase_{product.id}")
            ]
            keyboard.inline_keyboard.append(row)

        # Глобальные кнопки
        global_buttons = [
            InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart"),
            InlineKeyboardButton(text="📦 Оформить заказ", callback_data="checkout"),
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")
        ]
        keyboard.inline_keyboard.append(global_buttons)

        # Если нужны кнопки пагинации
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"cart_page_{page - 1}"))
        if page < total_pages - 1:
            pagination_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"cart_page_{page + 1}"))
        if pagination_buttons:
            keyboard.inline_keyboard.append(pagination_buttons)
        if isinstance(msg_or_callback, types.Message):
            await msg_or_callback.answer(text, reply_markup=keyboard)
        else:
            await msg_or_callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback_query: types.CallbackQuery):
    print("add_to_cart handler вызван, данные:", callback_query.data)  # Отладочный вывод
    product_id = int(callback_query.data.split("_")[1])
    telegram_id = callback_query.from_user.id

    async with get_session() as session:
        stmt_user = select(User).where(User.telegram_id == telegram_id)
        result_user = await session.execute(stmt_user)
        db_user = result_user.scalar_one_or_none()

        if not db_user:
            db_user = User(telegram_id=telegram_id)
            session.add(db_user)
            await session.commit()

        stmt_cart = select(CartItem).where(
            CartItem.user_id == db_user.id,
            CartItem.product_id == product_id
        )
        result_cart = await session.execute(stmt_cart)
        cart_item = result_cart.scalar_one_or_none()

        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(user_id=db_user.id, product_id=product_id, quantity=1)
            session.add(cart_item)

        await session.commit()

    await callback_query.answer("✅ Товар добавлен в корзину!", show_alert=True)

@router.callback_query(F.data == "clear_cart")
async def clear_cart_callback(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    async with get_session() as session:
        stmt_user = select(User).where(User.telegram_id == telegram_id)
        result_user = await session.execute(stmt_user)
        db_user = result_user.scalar_one_or_none()

        if db_user:
            stmt_delete = CartItem.__table__.delete().where(CartItem.user_id == db_user.id)
            await session.execute(stmt_delete)
            await session.commit()

    await callback_query.answer("Корзина очищена!", show_alert=True)
    await callback_query.message.edit_text("🛒 Ваша корзина пуста.")

@router.callback_query(lambda c: c.data and c.data.startswith("increase_"))
async def increase_quantity(callback_query: types.CallbackQuery):
    product_id = int(callback_query.data.split("_")[1])
    telegram_id = callback_query.from_user.id
    async with get_session() as session:
        stmt_user = select(User).where(User.telegram_id == telegram_id)
        result_user = await session.execute(stmt_user)
        db_user = result_user.scalar_one_or_none()
        if not db_user:
            await callback_query.answer("Пользователь не найден", show_alert=True)
            return

        stmt_cart = select(CartItem).where(
            CartItem.user_id == db_user.id,
            CartItem.product_id == product_id
        )
        result_cart = await session.execute(stmt_cart)
        cart_item = result_cart.scalar_one_or_none()
        if cart_item:
            cart_item.quantity += 1
            await session.commit()
            await callback_query.answer("Количество увеличено")
        else:
            await callback_query.answer("Товар не найден в корзине", show_alert=True)
    await view_cart(telegram_id, callback_query, page=0)

@router.callback_query(lambda c: c.data and c.data.startswith("decrease_"))
async def decrease_quantity(callback_query: types.CallbackQuery):
    product_id = int(callback_query.data.split("_")[1])
    telegram_id = callback_query.from_user.id
    async with get_session() as session:
        stmt_user = select(User).where(User.telegram_id == telegram_id)
        result_user = await session.execute(stmt_user)
        db_user = result_user.scalar_one_or_none()
        if not db_user:
            await callback_query.answer("Пользователь не найден", show_alert=True)
            return

        stmt_cart = select(CartItem).where(
            CartItem.user_id == db_user.id,
            CartItem.product_id == product_id
        )
        result_cart = await session.execute(stmt_cart)
        cart_item = result_cart.scalar_one_or_none()
        if cart_item:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                await session.commit()
                await callback_query.answer("Количество уменьшено")
            else:
                await session.delete(cart_item)
                await session.commit()
                await callback_query.answer("Товар удалён")
        else:
            await callback_query.answer("Товар не найден в корзине", show_alert=True)
    await view_cart(telegram_id, callback_query, page=0)

@router.callback_query(lambda c: c.data and c.data.startswith("remove_"))
async def remove_item(callback_query: types.CallbackQuery):
    product_id = int(callback_query.data.split("_")[1])
    telegram_id = callback_query.from_user.id
    async with get_session() as session:
        stmt_user = select(User).where(User.telegram_id == telegram_id)
        result_user = await session.execute(stmt_user)
        db_user = result_user.scalar_one_or_none()
        if not db_user:
            await callback_query.answer("Пользователь не найден", show_alert=True)
            return

        stmt_cart = select(CartItem).where(
            CartItem.user_id == db_user.id,
            CartItem.product_id == product_id
        )
        result_cart = await session.execute(stmt_cart)
        cart_item = result_cart.scalar_one_or_none()
        if cart_item:
            await session.delete(cart_item)
            await session.commit()
            await callback_query.answer("Товар удалён")
        else:
            await callback_query.answer("Товар не найден в корзине", show_alert=True)
    await view_cart(telegram_id, callback_query, page=0)

@router.callback_query(lambda c: c.data and c.data.startswith("cart_page_"))
async def paginate_cart(callback_query: types.CallbackQuery):
    page = int(callback_query.data.split("_")[-1])
    telegram_id = callback_query.from_user.id
    await view_cart(telegram_id, callback_query, page)
    await callback_query.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()  # Удаляем текущее сообщение
    from bot.handlers.start_menu import start_menu
    await start_menu(callback_query.message)  # Отправляем главное меню
    await state.clear()
    await callback_query.answer()


async def calculate_total(user_id: int, session) -> int:
    """
    Считает общую стоимость корзины (или заказ) для указанного пользователя.
    """
    total = 0
    stmt = (
        select(CartItem, Product)
        .join(Product, Product.id == CartItem.product_id)
        .where(CartItem.user_id == user_id)
    )
    result = await session.execute(stmt)
    rows = result.all()
    for cart_item, product in rows:
        total += product.price * cart_item.quantity
    return total


@router.callback_query(F.data == "checkout")
async def checkout(callback_query: types.CallbackQuery, state: FSMContext):
    telegram_id = callback_query.from_user.id
    async with get_session() as session:
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

        # Считаем сумму заказа
        total_value = await calculate_total(db_user.id, session)

        # Создаем заказ и позиции в заказе
        order = Order(
            user_id=db_user.id,
            status="Принят",
            contact_info="",  # Если контакт не требуется, оставляем пустым
            total=total_value
        )
        session.add(order)
        await session.flush()  # чтобы получить order.id

        # Создаем записи для каждой позиции заказа
        stmt_cart_details = select(CartItem, Product).join(Product, Product.id == CartItem.product_id).where(
            CartItem.user_id == db_user.id
        )
        result_cart_details = await session.execute(stmt_cart_details)
        rows = result_cart_details.all()
        for cart_item, product in rows:
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=cart_item.quantity,
                price=product.price
            )
            session.add(order_item)

        # Очищаем корзину
        stmt_delete = CartItem.__table__.delete().where(CartItem.user_id == db_user.id)
        await session.execute(stmt_delete)
        await session.commit()

        order_id = order.id

    # Вместо запроса контакта сразу переходим к выбору способа доставки
    delivery_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚶 Самовывоз", callback_data="delivery_self"),
            InlineKeyboardButton(text="🚚 Курьером", callback_data="delivery_courier")
        ],
        [
            InlineKeyboardButton(text="📦 Почтой", callback_data="delivery_post")
        ],
        [
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")
        ]
    ])
    # Редактируем сообщение, чтобы удалить старые кнопки и показать варианты доставки
    await callback_query.message.edit_text(
        f"Заказ #{order_id} оформлен! Выберите способ доставки:",
        reply_markup=delivery_keyboard
    )
    await state.set_state("CheckoutState:waiting_for_delivery_option")
    await callback_query.answer()

