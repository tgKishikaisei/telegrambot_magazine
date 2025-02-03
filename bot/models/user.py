# models/user.py
from sqlalchemy import Column, Integer
from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)  # внутренний ID в БД
    telegram_id = Column(Integer, unique=True, index=True)  # user_id из Телеграм

    # Здесь можно добавить другие поля, например, username или phone
