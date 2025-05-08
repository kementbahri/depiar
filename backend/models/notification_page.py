from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base

class NotificationPage(Base):
    __tablename__ = "notification_pages"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)  # suspended, maintenance, error, etc.
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 