"""Тесты оформления заказа (SQLite в памяти, Telegram подменяется)."""
import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.update({
    "TELEGRAM_BOT_TOKEN": "123456789:TEST-TOKEN-NOT-REAL",
    "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
    "ADMIN_ID": "100",
})

from aiogram.fsm.context import FSMContext  # noqa: E402
from aiogram.fsm.storage.base import StorageKey  # noqa: E402
from aiogram.fsm.storage.memory import MemoryStorage  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import bot.database.session as db_session  # noqa: E402
from bot.handlers import cart  # noqa: E402
from bot.models import Base, CartItem, Category, Order, Product, User  # noqa: E402

USER_TG = 555


@pytest.fixture(autouse=True)
def db(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool,
                                 connect_args={"check_same_thread": False})
    factory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(db_session, "AsyncSessionLocal", factory)

    async def setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with factory() as s:
            cat = Category(name="Phones")
            s.add(cat)
            await s.flush()
            s.add(Product(id=1, name="Phone", price=500, category_id=cat.id))
            await s.commit()

    asyncio.run(setup())
    yield factory
    asyncio.run(engine.dispose())


@pytest.fixture
def bot_mock(monkeypatch):
    fake = SimpleNamespace(send_message=AsyncMock())
    monkeypatch.setattr(cart, "bot", fake)
    return fake


def _state():
    return FSMContext(storage=MemoryStorage(), key=StorageKey(bot_id=1, chat_id=USER_TG, user_id=USER_TG))


def _callback(data):
    message = SimpleNamespace(edit_text=AsyncMock(), answer=AsyncMock(), delete=AsyncMock())
    return SimpleNamespace(data=data, from_user=SimpleNamespace(id=USER_TG), message=message, answer=AsyncMock())


def _message(text=None, location=None):
    return SimpleNamespace(text=text, location=location, from_user=SimpleNamespace(id=USER_TG),
                           content_type="location" if location else "text", answer=AsyncMock())


async def _checkout(state):
    await cart.add_to_cart(_callback("add_1"))
    await cart.add_to_cart(_callback("add_1"))
    await cart.checkout(_callback("checkout"), state)


async def _order(factory):
    async with factory() as s:
        return (await s.execute(select(Order))).scalar_one()


@pytest.mark.asyncio
async def test_address_is_saved_to_order_and_admin_notified(db, bot_mock):
    """Адрес доставки попадает в заказ, а администратор получает уведомление."""
    state = _state()
    await _checkout(state)
    await cart.process_delivery_option(_callback("delivery_courier"), state)
    await cart.ask_for_text_address(_callback("input_address"), state)
    assert await state.get_state() == cart.CheckoutState.waiting_for_address.state
    await cart.process_address(_message("ул. Навои, 10"), state)

    order = await _order(db)
    assert order.total == 1000
    assert order.contact_info == "Курьером: ул. Навои, 10"
    bot_mock.send_message.assert_awaited_once()
    text = bot_mock.send_message.await_args.kwargs["text"]
    assert f"#{order.id}" in text and "ул. Навои, 10" in text and "1000" in text
    assert await state.get_state() is None


@pytest.mark.asyncio
async def test_pickup_and_location_are_saved(db, bot_mock):
    state = _state()
    await _checkout(state)
    await cart.process_delivery_option(_callback("delivery_self"), state)
    assert (await _order(db)).contact_info == "Самовывоз"


@pytest.mark.asyncio
async def test_location_saved(db, bot_mock):
    state = _state()
    await _checkout(state)
    await cart.process_delivery_option(_callback("delivery_post"), state)
    await state.set_state(cart.CheckoutState.waiting_for_location)
    await cart.process_location(_message(location=SimpleNamespace(latitude=41.3, longitude=69.24)), state)
    assert (await _order(db)).contact_info == "Почтой: геолокация 41.300000, 69.240000"


@pytest.mark.asyncio
async def test_address_state_handler_is_reachable():
    """Фильтр хендлера — состояние FSM, а не несуществующий F.state у сообщения."""
    from aiogram.fsm.state import State
    handler = next(h for h in cart.router.message.handlers if h.callback is cart.process_address)
    assert any(isinstance(f.callback, State) for f in handler.filters)


@pytest.mark.asyncio
async def test_short_address_rejected(db, bot_mock):
    state = _state()
    await _checkout(state)
    await state.set_state(cart.CheckoutState.waiting_for_address)
    msg = _message("ab")
    await cart.process_address(msg, state)
    assert "от 5 до 250" in msg.answer.await_args.args[0]
    assert (await _order(db)).contact_info == ""


@pytest.mark.asyncio
async def test_unknown_product_and_quantity_limit(db, bot_mock, monkeypatch):
    cb = _callback("add_999")
    await cart.add_to_cart(cb)
    cb.answer.assert_awaited_with("Товар не найден", show_alert=True)

    monkeypatch.setattr(cart, "MAX_QUANTITY", 2)
    for _ in range(3):
        await cart.add_to_cart(_callback("add_1"))
    async with db() as s:
        item = (await s.execute(select(CartItem))).scalar_one()
        assert item.quantity == 2


@pytest.mark.asyncio
async def test_order_of_other_user_is_not_touched(db, bot_mock):
    """order_id из FSM проверяется на принадлежность пользователю."""
    state = _state()
    await _checkout(state)
    async with db() as s:
        other = User(telegram_id=777)
        s.add(other)
        await s.flush()
        order = (await s.execute(select(Order))).scalar_one()
        order.user_id = other.id
        await s.commit()
    await cart.process_delivery_option(_callback("delivery_self"), state)
    assert (await _order(db)).contact_info == ""
    bot_mock.send_message.assert_not_awaited()
