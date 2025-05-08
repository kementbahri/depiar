from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class ServicePlan(Base):
    __tablename__ = "service_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    description = Column(String(500))
    price = Column(Float)
    disk_gb = Column(Float)
    bandwidth_gb = Column(Float)
    max_domains = Column(Integer)
    max_databases = Column(Integer)
    max_email_accounts = Column(Integer)
    max_ftp_accounts = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # İlişkiler
    customers = relationship("Customer", secondary="customer_service_plans") 