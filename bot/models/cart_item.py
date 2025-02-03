# models/cart_item.py
from sqlalchemy import Column, Integer, ForeignKey
from .base import Base

class CartItem(Base):
    """
    Текущие товары в корзине пользователей.
    user_id и product_id вместе формируют уникальную связь.
    """
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)  # Если необходимо, можно добавить ForeignKey("users.id")
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    quantity = Column(Integer, default=1)
