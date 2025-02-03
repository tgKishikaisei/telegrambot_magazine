# models/order.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    status = Column(String, default="Принят")
    contact_info = Column(String)
    total = Column(Integer, default=0)

    # Связь с позициями в заказе
    items = relationship("OrderItem", back_populates="order")
