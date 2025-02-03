import os
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.bot_instance import bot

router = Router()

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

@router.message(Command(commands=["help"]))
async def help_command(message: types.Message):
    help_text = (
        "Доступные команды:\n"
        "/start, /menu - Главное меню\n"
        "/help - Помощь по командам\n"
        "🔎 Поиск - Поиск товара\n"
        "🛍️ Каталог - Просмотр категорий товаров\n"
        "🛒 Корзина - Просмотр и редактирование корзины\n"
        "👤 Личный кабинет - История заказов\n"
        "ℹ️ Инфо о доставке - Информация о доставке\n"
        "Также, в процессе оформления заказа можно ввести /cancel для отмены."
    )
    await message.answer(help_text)

@router.message(Command(commands=["cancel"]))
async def cancel_order(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активной операции для отмены.")
        return
    await state.clear()
    await message.answer("Операция отменена. Возвращаюсь в главное меню.")
    await start_menu(message)

@router.message(lambda message: message.text == "ℹ️ Инфо о доставке")
async def info(message: types.Message):
    text = (
        "ℹ️ Информация о доставке:\n\n"
        "🚚 Доставка по всей стране.\n"
        "⏳ Срок доставки: 3-7 рабочих дней.\n"
        "📞 Контакт: +7 999 123-45-67\n"
        "📧 Email: info@shop.com"
    )
    await message.answer(text)
