# Telegram-бот магазина

Магазин электроники внутри Telegram на aiogram 3: каталог по категориям, корзина, оформление заказа с выбором доставки. Администратор получает каждый заказ с адресом в личные сообщения.

[![License](https://img.shields.io/github/license/tgKishikaisei/telegrambot_magazine)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/tgKishikaisei/telegrambot_magazine/ci.yml?branch=main&label=CI)](https://github.com/tgKishikaisei/telegrambot_magazine/actions/workflows/ci.yml)

## Что умеет

- **Каталог и поиск.** Категории и товары из базы, поиск по названию, история просмотренных товаров.
- **Корзина.** Добавить, изменить количество (до 99), удалить позицию, очистить, посчитать итог.
- **Заказ.** FSM проводит через выбор доставки (самовывоз, курьер, почта) и адрес; заказ сохраняется вместе с ними.
- **Аккаунт.** «Мои заказы», избранное, отзывы о товарах, раздел поддержки.

## Стек

Python 3.12, aiogram 3, SQLAlchemy 2 (async), asyncpg, PostgreSQL. Тесты на pytest-asyncio и aiosqlite.

## Запуск

```bash
git clone https://github.com/tgKishikaisei/telegrambot_magazine.git
cd telegrambot_magazine
python -m venv venv
venv\Scripts\activate                  # Linux и macOS: source venv/bin/activate
pip install --require-hashes -r requirements.txt
cp .env.example .env                    # TELEGRAM_BOT_TOKEN, ADMIN_ID, DATABASE_URL
python -m bot.database.init_db          # создать таблицы
python -m bot.database.load_data        # загрузить категории и товары из data/data.json
python -m bot.main
```

## Тесты

```bash
pip install --require-hashes -r requirements-dev.txt
pytest
```

Тесты поднимают SQLite в памяти, поэтому PostgreSQL и токен бота для них не нужны.

## Демо

Скриншотов нет: бот работает в Telegram, запустите его со своим токеном от @BotFather.

## Лицензия

[MIT](LICENSE) © 2025-2026 Behruz Avezmatov
