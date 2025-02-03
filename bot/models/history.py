from sqlalchemy import Column, Integer, ForeignKey, DateTime
from datetime import datetime
from .base import Base

class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    viewed_at = Column(DateTime, default=datetime.utcnow)
