from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(Command(commands=["support"]))
async def support_request(message: types.Message, state: FSMContext):
    await message.answer("Опишите вашу проблему или вопрос, и мы свяжемся с вами:")
    await state.set_state("Support:waiting_for_message")

@router.message(lambda message: message.text and message.get_state() == "Support:waiting_for_message")
async def process_support(message: types.Message, state: FSMContext):
    support_message = message.text.strip()
    from bot.bot_instance import bot
    import os
    ADMIN_ID = os.getenv("ADMIN_ID")
    await bot.send_message(chat_id=ADMIN_ID, text=f"Запрос в поддержку от {message.from_user.id}:\n{support_message}")
    await message.answer("Ваше сообщение отправлено в службу поддержки.")
    await state.clear()
