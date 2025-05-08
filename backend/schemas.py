from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from .models import CustomerStatus, CustomerPackage, DNSType

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class DomainBase(BaseModel):
    name: str
    php_version: str = "8.1"
    server_type: str = "apache"
    ssl_enabled: bool = True

class DomainCreate(DomainBase):
    pass

class Domain(DomainBase):
    id: int
    customer_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class EmailAccountBase(BaseModel):
    username: str
    domain_id: int
    quota: Optional[int] = 1000

class EmailAccountCreate(EmailAccountBase):
    password: str

class EmailAccount(EmailAccountBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class DatabaseBase(BaseModel):
    name: str
    username: str

class DatabaseCreate(DatabaseBase):
    password: str

class Database(DatabaseBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    company: Optional[str] = None
    address: Optional[str] = None
    status: CustomerStatus = CustomerStatus.ACTIVE
    package: CustomerPackage = CustomerPackage.BASIC

class CustomerCreate(CustomerBase):
    password: str

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    status: Optional[CustomerStatus] = None
    package: Optional[CustomerPackage] = None

class Customer(CustomerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class PasswordChange(BaseModel):
    password: str

class DNSRecordBase(BaseModel):
    name: str
    type: DNSType
    content: str
    ttl: int = 3600
    priority: Optional[int] = None

class DNSRecordCreate(DNSRecordBase):
    pass

class DNSRecordUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[DNSType] = None
    content: Optional[str] = None
    ttl: Optional[int] = None
    priority: Optional[int] = None

class DNSRecord(DNSRecordBase):
    id: int
    domain_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class FTPAccountBase(BaseModel):
    username: str
    home_directory: str = "/"

class FTPAccountCreate(FTPAccountBase):
    password: str

class FTPAccountUpdate(BaseModel):
    password: Optional[str] = None
    home_directory: Optional[str] = None
    status: Optional[str] = None

class FTPAccount(FTPAccountBase):
    id: int
    domain_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ScheduledTaskBase(BaseModel):
    name: str
    command: str
    schedule: str

class ScheduledTaskCreate(ScheduledTaskBase):
    pass

class ScheduledTaskUpdate(BaseModel):
    name: Optional[str] = None
    command: Optional[str] = None
    schedule: Optional[str] = None
    status: Optional[str] = None

class ScheduledTask(ScheduledTaskBase):
    id: int
    domain_id: int
    status: str
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class BackupBase(BaseModel):
    name: str
    type: str
    schedule: Optional[str] = None

class BackupCreate(BackupBase):
    pass

class BackupUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    schedule: Optional[str] = None

class Backup(BackupBase):
    id: int
    domain_id: int
    status: str
    size: Optional[int] = None
    path: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class DomainLogBase(BaseModel):
    type: str
    message: str
    source: str

class DomainLogCreate(DomainLogBase):
    pass

class DomainLog(DomainLogBase):
    id: int
    domain_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class ResellerPlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: int
    max_customers: int
    max_domains: int
    max_disk_space: int
    max_monthly_traffic: int
    can_create_plans: bool = True
    can_manage_dns: bool = True
    can_manage_ssl: bool = True
    can_manage_backups: bool = True
    support_type: str
    features: List[str]

class ResellerPlanCreate(ResellerPlanBase):
    pass

class ResellerPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    max_customers: Optional[int] = None
    max_domains: Optional[int] = None
    max_disk_space: Optional[int] = None
    max_monthly_traffic: Optional[int] = None
    can_create_plans: Optional[bool] = None
    can_manage_dns: Optional[bool] = None
    can_manage_ssl: Optional[bool] = None
    can_manage_backups: Optional[bool] = None
    support_type: Optional[str] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ResellerPlan(ResellerPlanBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class ServicePlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: int
    domains: int
    disk_space: int
    monthly_traffic: int
    email_accounts: int
    databases: int
    ftp_accounts: int
    ssl_type: str
    support_type: str
    backup_frequency: str
    php_version: str
    features: List[str]
    is_public: bool = True

class ServicePlanCreate(ServicePlanBase):
    pass

class ServicePlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    domains: Optional[int] = None
    disk_space: Optional[int] = None
    monthly_traffic: Optional[int] = None
    email_accounts: Optional[int] = None
    databases: Optional[int] = None
    ftp_accounts: Optional[int] = None
    ssl_type: Optional[str] = None
    support_type: Optional[str] = None
    backup_frequency: Optional[str] = None
    php_version: Optional[str] = None
    features: Optional[List[str]] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None

class ServicePlan(ServicePlanBase):
    id: int
    is_active: bool
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True 