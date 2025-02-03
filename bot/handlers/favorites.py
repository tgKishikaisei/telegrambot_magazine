from aiogram import Router, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from bot.database.session import get_session
from bot.models import Favorite, User, Product

router = Router()


@router.callback_query(F.data.startswith("fav_"))
async def toggle_favorite(callback_query: types.CallbackQuery):
    product_id = int(callback_query.data.split("_")[1])
    telegram_id = callback_query.from_user.id

    async with get_session() as session:
        stmt_user = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt_user)
        db_user = result.scalar_one_or_none()
        if not db_user:
            # Пользователь еще не создан — создаем его без повторного импорта
            db_user = User(telegram_id=telegram_id)
            session.add(db_user)
            await session.commit()

        stmt_fav = select(Favorite).where(
            Favorite.user_id == db_user.id,
            Favorite.product_id == product_id
        )
        result_fav = await session.execute(stmt_fav)
        fav = result_fav.scalar_one_or_none()
        if fav:
            await session.delete(fav)
            action = "удалено из избранного"
        else:
            fav = Favorite(user_id=db_user.id, product_id=product_id)
            session.add(fav)
            action = "добавлено в избранное"
        await session.commit()
    await callback_query.answer(f"Товар {action}!", show_alert=True)
