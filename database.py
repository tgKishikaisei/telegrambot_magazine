# database.py
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def get_session():
    """
    Асинхронный контекстный менеджер для получения сессии.
    Позволяет использовать:
        async with get_session() as session:
            ...
    """
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()













































# load_dotenv()
# dbname = os.getenv('DB')
# user = os.getenv('USER')
# password = os.getenv('PASSWORD')
# host = os.getenv('HOST')
# port = os.getenv('PORT')
#
# try:
#     conn = psycopg2.connect(
#         dbname=dbname,
#         user=user,
#         password=password,
#         host=host,
#         port=port
#     )
#     cur = conn.cursor()
#     print("Connected to the database!")
#
#     # Распечатоть сведение о PostgreSQL
#     print("Информация о сервере PostgreSQL")
#     print(conn.get_dsn_parameters(), "\n")
#
#     # Выполнение SQL - запроса
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS users (
#             id SERIAL PRIMARY KEY,
#             id_telegram INTEGER,
#             name VARCHAR(100) NOT NULL,
#             email VARCHAR(100) UNIQUE NOT NULL,
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         );
#     """)
#
#     # user_carts: Корзина для каждога пользователя (user_id: quantity))
#     user_carts = {}
#     # orders: Заказы {order_id: {user_id, products, status, contact_info, total}}
#     orders = {}
#     # user_orders_history: История заказов для каждога пользователя {user_id: [order_ids]}
#     user_orders_history = {}
#
#     # Словарь промокодов для скидок
#     PROMOCODES = {"SALE10": 0.1, "VIP": 0.2}
#
#     # Текущий номер заказа, будет увеличиваться по мере создания заказов
#     current_order_id = 1000
#     cur.execute(
#         """CREATE TABLE IF NOT EXISTS user_carts(
#                 user_id INTEGER UNIQUE NOT NULL,
#                 total VARCHAR(100) NOT NULL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
#         """)
#
#     cur.execute(
#         """CREATE TABLE IF NOT EXISTS orders(
#                 order_id SERIAL PRIMARY KEY,
#                 user_id INTEGER UNIQUE NOT NULL,
#                 products VARCHAR,
#                 status TEXT,
#                 contact_info VARCHAR(30),
#                 total VARCHAR(40),
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 FOREIGN KEY (user_id) REFERENCES user_carts(user_id) ON DELETE CASCADE);
#
#         """)
#
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS user_orders_history(
#              user_id INTEGER UNIQUE NOT NULL,
#              order_ids INTEGER UNIQUE NOT NULL,
#              FOREIGN KEY (user_id) REFERENCES user_carts(user_id) ON DELETE CASCADE);
#         """)
#
#
#     def registered_user(tg_id, phone_number, name):
#         """
#
#         :param tg_id:
#         :param name:
#         """
#         # Подключение к существующего базе данных
#         conn = psycopg2.connect(
#             dbname=dbname,
#             user=user,
#             password=password,
#             host=host,
#             port=port
#         )
#
#         # Курсор для выполнения операции с базой данных
#         cur = conn.cursor()
#
#         # Выполняем SQL - запрос
#         cur.execute('INSERT INTO users'
#                        '(tg_id, phone_number, name, reg_date)'
#                        'VALUES (%s, %s, %s, %s);', (tg_id, phone_number, name))
#
#         # схороним данные
#         conn.commit()
#
#     def monitoring():
#         # Подключение к существующего базе данных
#         conn = psycopg2.connect(
#             dbname=dbname,
#             user=user,
#             password=password,
#             host=host,
#             port=port
#         )
#
#         # Курсор для выполнения операции с базой данных
#         cursor = conn.cursor()
#
#         users_info = cursor.execute('SELECT * FROM users;')
#         user_order_info = cursor.execute('SELECT * FROM user_carts;')
#         orders_info = cursor.execute('SELECT * FROM orders;')
#         user_orders_history_info = cursor.execute('SELECT * FROM user_orders_history;')
#
#
#
#         # схороним данные
#         conn.commit()
#
#     # Ротация данных:
#     def delete_base_info():
#         """Удаляйте устаревшие данные"""
#         # Подключение к существующего базе данных
#         conn = psycopg2.connect(
#             dbname=dbname,
#             user=user,
#             password=password,
#             host=host,
#             port=port
#         )
#
#         # Курсор для выполнения операции с базой данных
#         cur = conn.cursor()
#
#         cur.execute('DELETE FROM orders WHERE order_date < NOW() - INTERVAL "1 year";')
#
#         # схороним данные
#         conn.commit()
#
#     def optimase_info():
#         """Настройте индексы"""
#         # Подключение к существующего базе данных
#         conn = psycopg2.connect(
#             dbname=dbname,
#             user=user,
#             password=password,
#             host=host,
#             port=port
#         )
#
#         # Курсор для выполнения операции с базой данных
#         cur = conn.cursor()
#
#         cur.execute("CREATE INDEX idx_users_email ON users (email);")
#
#         # схороним данные
#         conn.commit()
#
#
#     def get_user_cards():
#         """
#
#         :return:
#         """
#         # Подключение к существующего базе данных
#         conn = psycopg2.connect(
#             dbname=dbname,
#             user=user,
#             password=password,
#             host=host,
#             port=port
#         )
#
#         # Курсор для выполнения операции с базой данных
#         cur = conn.cursor()
#
#         cur.execute("SELECT")
#         # схороним данные
#         conn.commit()
#
# except Exception as e:
#     print(f"Error: {e}")
#
# finally:
#     if conn:
#         # Запись обновление
#         conn.commit()
#         cur.close()
#         conn.close()
#         print("Соединение с PostgreSQL закрыто")
