# models.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy import Column, Integer, String, ForeignKey, Float

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)  # внутренний ID в БД
    telegram_id = Column(Integer, unique=True, index=True)  # user_id из Телеграм

    # Можно добавить поля, например, username или phone


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    # Связь с Product (одна категория -> много продуктов)
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    description = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"))

    category = relationship("Category", back_populates="products")


class CartItem(Base):
    """
    Текущие товары в корзине пользователей.
    user_id и product_id вместе формируют "уникальную" связь (один и тот же товар в корзине).
    """
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)  # ForeignKey можно убрать, если не связываете
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    quantity = Column(Integer, default=1)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    status = Column(String, default="Принят")
    contact_info = Column(String)
    total = Column(Integer, default=0)

    # Связь с позициями в заказе
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"))
    quantity = Column(Integer, default=1)
    price = Column(Integer, default=0)  # цена за единицу товара на момент оформления

    order = relationship("Order", back_populates="items")