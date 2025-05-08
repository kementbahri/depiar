from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    ip_address = Column(String(50))
    hostname = Column(String(255))
    os_type = Column(String(50))
    os_version = Column(String(50))
    cpu_cores = Column(Integer)
    ram_gb = Column(Float)
    disk_gb = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # İlişkiler
    services = relationship("Service", back_populates="server") 