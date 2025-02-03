from aiogram import Router, types
from sqlalchemy import select
from bot.database.session import get_session
from bot.models import History, Product

router = Router()

@router.message(lambda message: message.text == "История просмотров")
async def show_view_history(message: types.Message):
    user_id = message.from_user.id
    async with get_session() as session:
        stmt = select(History, Product).join(Product, Product.id == History.product_id).where(History.user_id == user_id)
        result = await session.execute(stmt)
        rows = result.all()
        if not rows:
            await message.answer("История просмотров пуста.")
            return
        text = "История просмотров:\n"
        for history, product in rows:
            text += f"{product.name} (просмотрен: {history.viewed_at.strftime('%Y-%m-%d %H:%M')})\n"
        await message.answer(text)
