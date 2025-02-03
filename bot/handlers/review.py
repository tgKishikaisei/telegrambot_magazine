from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

router = Router()

class ReviewState(StatesGroup):
    waiting_for_order_id = State()
    waiting_for_review_text = State()

@router.message(Command(commands=["review"]))
async def review_start(message: types.Message, state: FSMContext):
    await message.answer("Введите номер заказа, который хотите оценить:")
    await state.set_state(ReviewState.waiting_for_order_id)

@router.message(ReviewState.waiting_for_order_id)
async def get_order_id(message: types.Message, state: FSMContext):
    order_id = message.text.strip()
    await state.update_data(order_id=order_id)
    await message.answer("Введите ваш отзыв:")
    await state.set_state(ReviewState.waiting_for_review_text)

@router.message(ReviewState.waiting_for_review_text)
async def get_review_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    review_text = message.text.strip()
    # Здесь можно сохранить отзыв в базу, но для демонстрации просто подтверждаем.
    await message.answer(f"Ваш отзыв для заказа #{order_id} принят:\n«{review_text}»")
    await state.clear()
