from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class SSHServer(Base):
    __tablename__ = "ssh_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    host = Column(String(255))
    port = Column(Integer, default=22)
    username = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # İlişkiler
    ssh_keys = relationship("SSHKey", back_populates="server") 