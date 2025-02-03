from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy import select
from bot.database.session import get_session
from bot.models import User, Order

router = Router()

@router.message(lambda message: message.text == "👤 Личный кабинет")
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

@router.message(Command(commands=["orderstatus"]))
async def order_status(message: types.Message):
    telegram_id = message.from_user.id
    async with get_session() as session:
        # Сначала получаем пользователя
        stmt_user = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt_user)
        db_user = result.scalar_one_or_none()
        if not db_user:
            await message.answer("У вас пока нет заказов.")
            return
        # Получаем последний заказ
        stmt_order = select(Order).where(Order.user_id == db_user.id).order_by(Order.id.desc())
        result_order = await session.execute(stmt_order)
        last_order = result_order.scalar_one_or_none()
        if not last_order:
            await message.answer("У вас пока нет заказов.")
        else:
            await message.answer(
                f"Ваш последний заказ #{last_order.id}:\nСтатус: {last_order.status}\nСумма: {last_order.total} руб."
            )
