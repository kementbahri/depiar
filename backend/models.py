from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Enum, Float, BigInteger, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base
from datetime import datetime

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    RESELLER = "reseller"
    CUSTOMER = "customer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    domains = relationship("Domain", back_populates="owner", cascade="all, delete-orphan")
    email_accounts = relationship("EmailAccount", back_populates="owner", cascade="all, delete-orphan")
    databases = relationship("Database", back_populates="owner", cascade="all, delete-orphan")

    # Satıcı ise müşterileri
    customers = relationship("Customer", back_populates="reseller", cascade="all, delete-orphan")

    file_operations = relationship("FileOperation", back_populates="user", cascade="all, delete-orphan")
    file_searches = relationship("FileSearch", back_populates="user", cascade="all, delete-orphan")

    webhooks = relationship("Webhook", back_populates="user", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="user", cascade="all, delete-orphan")

    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    def is_reseller(self):
        return self.role == UserRole.RESELLER
    
    def is_customer(self):
        return self.role == UserRole.CUSTOMER

class DomainStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    EXPIRED = "expired"

class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"))
    server_id = Column(Integer, ForeignKey("ssh_servers.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, unique=True, index=True)
    status = Column(Enum(DomainStatus), default=DomainStatus.ACTIVE)
    suspension_reason = Column(Text, nullable=True)
    suspension_date = Column(DateTime(timezone=True), nullable=True)
    php_version = Column(String, default="8.1")
    server_type = Column(String, default="apache")
    ssl_enabled = Column(Boolean, default=True)
    ssl_expiry = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Customer", back_populates="domains")
    server = relationship("SSHServer", back_populates="domains")
    email_accounts = relationship("EmailAccount", back_populates="domain", cascade="all, delete-orphan")
    ssl_certificates = relationship("SSL", back_populates="domain", cascade="all, delete-orphan")
    dns_records = relationship("DNSRecord", back_populates="domain", cascade="all, delete-orphan")
    ftp_accounts = relationship("FTPAccount", back_populates="domain", cascade="all, delete-orphan")
    scheduled_tasks = relationship("ScheduledTask", back_populates="domain", cascade="all, delete-orphan")
    backups = relationship("Backup", back_populates="domain", cascade="all, delete-orphan")
    logs = relationship("DomainLog", back_populates="domain", cascade="all, delete-orphan")
    subdomains = relationship("Subdomain", back_populates="domain", cascade="all, delete-orphan")
    file_permissions = relationship("FilePermission", back_populates="domain", cascade="all, delete-orphan")
    file_operations = relationship("FileOperation", back_populates="domain", cascade="all, delete-orphan")
    file_searches = relationship("FileSearch", back_populates="domain", cascade="all, delete-orphan")
    directory_restrictions = relationship("DirectoryRestriction", back_populates="domain", cascade="all, delete-orphan")
    backup_rotation = relationship("BackupRotation", back_populates="domain", uselist=False, cascade="all, delete-orphan")
    php_configurations = relationship("PHPConfiguration", back_populates="domain", cascade="all, delete-orphan")
    web_servers = relationship("WebServer", back_populates="domain", cascade="all, delete-orphan")

class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    password = Column(String)
    quota = Column(Integer, default=1000)  # MB
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="email_accounts")
    domain = relationship("Domain", back_populates="email_accounts")

class DatabaseBackup(Base):
    __tablename__ = "database_backups"

    id = Column(Integer, primary_key=True, index=True)
    database_id = Column(Integer, ForeignKey("databases.id", ondelete="CASCADE"))
    filename = Column(String)
    size = Column(Integer)  # bytes
    status = Column(String)  # pending, completed, failed
    backup_type = Column(String)  # full, structure, data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    path = Column(String)  # backup file path

    database = relationship("Database", back_populates="backups")

class DatabaseOptimization(Base):
    __tablename__ = "database_optimizations"

    id = Column(Integer, primary_key=True, index=True)
    database_id = Column(Integer, ForeignKey("databases.id", ondelete="CASCADE"))
    status = Column(String)  # pending, completed, failed
    optimization_type = Column(String)  # analyze, optimize, repair
    tables_optimized = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    details = Column(Text, nullable=True)  # optimization details

    database = relationship("Database", back_populates="optimizations")

class Database(Base):
    __tablename__ = "databases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    username = Column(String)
    password = Column(String)
    host = Column(String, default="localhost")
    port = Column(Integer, default=3306)
    charset = Column(String, default="utf8mb4")
    collation = Column(String, default="utf8mb4_unicode_ci")
    size = Column(Integer, default=0)  # bytes
    status = Column(String, default="active")  # active, suspended, deleted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="databases")
    backups = relationship("DatabaseBackup", back_populates="database", cascade="all, delete-orphan")
    optimizations = relationship("DatabaseOptimization", back_populates="database", cascade="all, delete-orphan")

class CustomerStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    PENDING = "pending"

class CustomerPackage(str, enum.Enum):
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

    @property
    def details(self):
        return {
            "basic": {
                "name": "Temel Paket",
                "domains": 1,
                "disk_space": 5,  # GB
                "monthly_traffic": 50,  # GB
                "email_accounts": 5,
                "databases": 1,
                "ftp_accounts": 1,
                "ssl_type": "basic",
                "support_type": "email",
                "backup_frequency": "daily",
                "php_version": "8.1",
                "features": [
                    "Temel SSL Sertifikası",
                    "7/24 E-posta Desteği",
                    "Günlük Yedekleme"
                ]
            },
            "pro": {
                "name": "Profesyonel Paket",
                "domains": 5,
                "disk_space": 20,  # GB
                "monthly_traffic": 200,  # GB
                "email_accounts": 25,
                "databases": 5,
                "ftp_accounts": 5,
                "ssl_type": "wildcard",
                "support_type": "priority_email",
                "backup_frequency": "daily_weekly",
                "php_version": "8.1",
                "features": [
                    "Wildcard SSL Sertifikası",
                    "7/24 Öncelikli E-posta Desteği",
                    "Günlük Yedekleme + Haftalık Tam Yedek",
                    "Özel IP Adresi",
                    "Gelişmiş Güvenlik Özellikleri"
                ]
            },
            "enterprise": {
                "name": "Kurumsal Paket",
                "domains": -1,  # Sınırsız
                "disk_space": 100,  # GB
                "monthly_traffic": -1,  # Sınırsız
                "email_accounts": -1,  # Sınırsız
                "databases": -1,  # Sınırsız
                "ftp_accounts": -1,  # Sınırsız
                "ssl_type": "wildcard",
                "support_type": "priority_phone",
                "backup_frequency": "daily_weekly_monthly",
                "php_version": "8.1",
                "features": [
                    "Wildcard SSL Sertifikası",
                    "7/24 Öncelikli Telefon Desteği",
                    "Günlük + Haftalık + Aylık Tam Yedekleme",
                    "Özel IP Adresi",
                    "Gelişmiş Güvenlik Özellikleri",
                    "DDoS Koruması",
                    "Özel Sunucu Yönetimi",
                    "SLA Garantisi"
                ]
            }
        }[self.value]

class ResellerPlan(Base):
    __tablename__ = "reseller_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    price = Column(Integer)  # Aylık fiyat (TL)
    
    # Satıcı Limitleri
    max_customers = Column(Integer, default=10)  # Maksimum müşteri sayısı
    max_domains = Column(Integer, default=50)    # Maksimum toplam domain sayısı
    max_disk_space = Column(Integer, default=100)  # GB
    max_monthly_traffic = Column(Integer, default=1000)  # GB
    
    # Satıcı Özellikleri
    can_create_plans = Column(Boolean, default=True)  # Kendi planlarını oluşturabilir mi?
    can_manage_dns = Column(Boolean, default=True)    # DNS yönetimi yapabilir mi?
    can_manage_ssl = Column(Boolean, default=True)    # SSL yönetimi yapabilir mi?
    can_manage_backups = Column(Boolean, default=True)  # Yedekleme yönetimi yapabilir mi?
    
    # Destek ve Özellikler
    support_type = Column(String, default="email")  # email, priority_email, priority_phone
    features = Column(Text, default="[]")  # JSON string olarak özellikler listesi
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # İlişkiler
    resellers = relationship("Customer", back_populates="reseller_plan")

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    company = Column(String)
    address = Column(Text)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    status = Column(Enum(CustomerStatus), default=CustomerStatus.ACTIVE)
    suspension_reason = Column(Text, nullable=True)
    suspension_date = Column(DateTime(timezone=True), nullable=True)
    
    # Paket ve satıcı özellikleri
    service_plan_id = Column(Integer, ForeignKey("service_plans.id"), nullable=True)
    service_plan = relationship("ServicePlan", back_populates="customers")
    is_reseller = Column(Boolean, default=False)
    reseller_plan_id = Column(Integer, ForeignKey("reseller_plans.id"), nullable=True)
    reseller_plan = relationship("ResellerPlan", back_populates="resellers")
    
    # Satıcı istatistikleri
    total_customers = Column(Integer, default=0)
    total_domains = Column(Integer, default=0)
    total_disk_space = Column(Integer, default=0)  # GB
    total_monthly_traffic = Column(Integer, default=0)  # GB

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # İlişkiler
    domains = relationship("Domain", back_populates="customer", cascade="all, delete-orphan")
    email_accounts = relationship("EmailAccount", back_populates="customer", cascade="all, delete-orphan")
    databases = relationship("Database", back_populates="customer", cascade="all, delete-orphan")

class ServicePlan(Base):
    __tablename__ = "service_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    price = Column(Integer)  # Aylık fiyat (TL)
    
    # Paket Özellikleri
    domains = Column(Integer, default=1)  # -1 sınırsız için
    disk_space = Column(Integer, default=5)  # GB
    monthly_traffic = Column(Integer, default=50)  # GB
    email_accounts = Column(Integer, default=5)
    databases = Column(Integer, default=1)
    ftp_accounts = Column(Integer, default=1)
    
    # Özellikler
    ssl_type = Column(String, default="basic")  # basic, wildcard
    support_type = Column(String, default="email")  # email, priority_email, priority_phone
    backup_frequency = Column(String, default="daily")  # daily, daily_weekly, daily_weekly_monthly
    php_version = Column(String, default="8.1")
    
    # Ek Özellikler (JSON olarak saklanacak)
    features = Column(Text, default="[]")  # JSON string olarak özellikler listesi
    
    # Satıcı ilişkisi
    created_by_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    created_by = relationship("Customer", foreign_keys=[created_by_id])
    is_public = Column(Boolean, default=True)  # Herkes görebilir mi?
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # İlişkiler
    customers = relationship("Customer", back_populates="service_plan", cascade="all, delete-orphan")

class DNSType(str, enum.Enum):
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    TXT = "TXT"
    NS = "NS"
    SRV = "SRV"
    PTR = "PTR"

class DNSRecord(Base):
    __tablename__ = "dns_records"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"))
    name = Column(String)  # subdomain or @ for root
    type = Column(Enum(DNSType))
    content = Column(String)
    ttl = Column(Integer, default=3600)  # Time to live in seconds
    priority = Column(Integer, nullable=True)  # For MX records
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    domain = relationship("Domain", back_populates="dns_records")

class FTPAccount(Base):
    __tablename__ = "ftp_accounts"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"))
    username = Column(String, unique=True, index=True)
    password = Column(String)
    home_directory = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    domain = relationship("Domain", back_populates="ftp_accounts")

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"))
    name = Column(String)
    command = Column(String)
    schedule = Column(String)  # Cron expression
    status = Column(String, default="active")
    last_run = Column(DateTime(timezone=True), nullable=True)
    next_run = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    domain = relationship("Domain", back_populates="scheduled_tasks")

class Backup(Base):
    __tablename__ = "backups"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"))
    name = Column(String)
    type = Column(String)  # full, database, files
    status = Column(String)  # pending, in_progress, completed, failed
    size = Column(Integer, nullable=True)  # Size in bytes
    path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    schedule = Column(String, nullable=True)  # Cron expression for scheduled backups

    domain = relationship("Domain", back_populates="backups")

class DomainLog(Base):
    __tablename__ = "domain_logs"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"))
    type = Column(String)  # error, warning, info
    message = Column(Text)
    source = Column(String)  # apache, nginx, php, mysql, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    domain = relationship("Domain", back_populates="logs")

class SSL(Base):
    __tablename__ = "ssl_certificates"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"))
    certificate = Column(Text)
    private_key = Column(Text)
    issuer = Column(String)
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    domain = relationship("Domain", back_populates="ssl_certificates")

class SSHServer(Base):
    __tablename__ = "ssh_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    hostname = Column(String)
    port = Column(Integer, default=22)
    username = Column(String)
    password = Column(String, nullable=True)
    private_key = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    domains = relationship("Domain", back_populates="server", cascade="all, delete-orphan")
    metrics = relationship("ServerMetric", back_populates="server", cascade="all, delete-orphan")
    alerts = relationship("SecurityAlert", back_populates="server", cascade="all, delete-orphan")
    blocked_ips = relationship("IPBlock", back_populates="server", cascade="all, delete-orphan")
    updates = relationship("SystemUpdate", back_populates="server", cascade="all, delete-orphan")
    malware_scans = relationship("MalwareScan", back_populates="server", cascade="all, delete-orphan")
    software_versions = relationship("SoftwareVersion", back_populates="server", cascade="all, delete-orphan")
    php_configs = relationship("PHPConfiguration", back_populates="server", cascade="all, delete-orphan")
    database_servers = relationship("DatabaseServer", back_populates="server", cascade="all, delete-orphan")
    web_servers = relationship("WebServer", back_populates="server", cascade="all, delete-orphan")

class SSHCommand(Base):
    __tablename__ = "ssh_commands"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("ssh_servers.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    command = Column(Text)
    output = Column(Text, nullable=True)
    status = Column(String)  # success, failed, running
    exit_code = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    server = relationship("SSHServer", backref="commands")
    user = relationship("User", backref="ssh_commands")

class Subdomain(Base):
    __tablename__ = "subdomains"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"))
    name = Column(String)  # subdomain adı (örn: www, blog)
    document_root = Column(String)  # web sitesi dosyalarının bulunduğu dizin
    php_version = Column(String, default="8.1")
    ssl_enabled = Column(Boolean, default=True)
    status = Column(String, default="active")  # active, suspended, pending
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # İlişkiler
    domain = relationship("Domain", back_populates="subdomains")
    ftp_accounts = relationship("FTPAccount", back_populates="subdomain", cascade="all, delete-orphan")
    backups = relationship("Backup", back_populates="subdomain", cascade="all, delete-orphan") 

class ServerMetric(Base):
    __tablename__ = "server_metrics"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("ssh_servers.id", ondelete="CASCADE"))
    cpu_usage = Column(Float)  # CPU kullanımı (%)
    memory_usage = Column(Float)  # RAM kullanımı (%)
    disk_usage = Column(Float)  # Disk kullanımı (%)
    network_in = Column(BigInteger)  # Gelen ağ trafiği (bytes)
    network_out = Column(BigInteger)  # Giden ağ trafiği (bytes)
    uptime = Column(Integer)  # Uptime (saniye)
    load_average = Column(String)  # Load average (1m, 5m, 15m)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    server = relationship("SSHServer", back_populates="metrics")

class SecurityAlert(Base):
    __tablename__ = "security_alerts"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("ssh_servers.id", ondelete="CASCADE"))
    type = Column(String)  # modsecurity, fail2ban, firewall, malware
    severity = Column(String)  # low, medium, high, critical
    message = Column(Text)
    source_ip = Column(String, nullable=True)
    status = Column(String, default="new")  # new, in_progress, resolved
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    server = relationship("SSHServer", back_populates="alerts")

class IPBlock(Base):
    __tablename__ = "ip_blocks"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("ssh_servers.id", ondelete="CASCADE"))
    ip_address = Column(String)
    reason = Column(String)  # manual, fail2ban, modsecurity
    blocked_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    server = relationship("SSHServer", back_populates="blocked_ips")

class SystemUpdate(Base):
    __tablename__ = "system_updates"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("ssh_servers.id", ondelete="CASCADE"))
    package_name = Column(String)
    current_version = Column(String)
    available_version = Column(String)
    update_type = Column(String)  # security, bugfix, enhancement
    status = Column(String, default="available")  # available, scheduled, installed, failed
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    installed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    server = relationship("SSHServer", back_populates="updates")

class MalwareScan(Base):
    __tablename__ = "malware_scans"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("ssh_servers.id", ondelete="CASCADE"))
    scan_type = Column(String)  # full, quick, custom
    status = Column(String)  # pending, running, completed, failed
    threats_found = Column(Integer, default=0)
    scan_path = Column(String)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    details = Column(Text, nullable=True)

class SoftwareVersion(Base):
    __tablename__ = "software_versions"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("ssh_servers.id", ondelete="CASCADE"))
    software_type = Column(String)  # php, mysql, apache, nginx
    current_version = Column(String)
    available_versions = Column(JSON)  # Mevcut ve yüklenebilir versiyonlar
    status = Column(String, default="active")  # active, updating, failed
    last_check = Column(DateTime(timezone=True), server_default=func.now())
    last_update = Column(DateTime(timezone=True), nullable=True)
    update_log = Column(Text, nullable=True)

    server = relationship("SSHServer", back_populates="software_versions")

class PHPConfiguration(Base):
    __tablename__ = "php_configurations"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("ssh_servers.id", ondelete="SET NULL"), nullable=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"))
    version = Column(String)
    config_path = Column(String)
    fpm_status = Column(String, default="active")
    max_execution_time = Column(Integer, default=30)
    memory_limit = Column(String, default="128M")
    upload_max_filesize = Column(String, default="2M")
    post_max_size = Column(String, default="8M")
    max_input_vars = Column(Integer, default=1000)
    display_errors = Column(Boolean, default=False)
    error_reporting = Column(String, default="E_ALL & ~E_DEPRECATED & ~E_STRICT")
    last_modified = Column(DateTime(timezone=True), server_default=func.now())

    server = relationship("SSHServer", back_populates="php_configs")
    domain = relationship("Domain", back_populates="php_configurations")

class DatabaseServer(Base):
    __tablename__ = "database_servers"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("ssh_servers.id", ondelete="CASCADE"))
    type = Column(String)  # mysql, mariadb
    version = Column(String)
    port = Column(Integer, default=3306)
    root_password = Column(String)
    status = Column(String, default="active")  # active, stopped, failed
    max_connections = Column(Integer, default=151)
    max_allowed_packet = Column(String, default="16M")
    innodb_buffer_pool_size = Column(String, default="128M")
    query_cache_size = Column(String, default="16M")
    last_modified = Column(DateTime(timezone=True), server_default=func.now())

    server = relationship("SSHServer", back_populates="database_servers")

class WebServer(Base):
    __tablename__ = "web_servers"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("ssh_servers.id", ondelete="SET NULL"), nullable=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"))
    type = Column(String)
    version = Column(String)
    status = Column(String, default="active")
    config_path = Column(String)
    document_root = Column(String, default="/var/www/html")
    max_clients = Column(Integer, default=150)
    keep_alive = Column(Boolean, default=True)
    keep_alive_timeout = Column(Integer, default=5)
    last_modified = Column(DateTime(timezone=True), server_default=func.now())

    server = relationship("SSHServer", back_populates="web_servers")
    domain = relationship("Domain", back_populates="web_servers")

class FilePermission(Base):
    __tablename__ = "file_permissions"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"))
    path = Column(String)
    owner = Column(String)
    group = Column(String)
    permissions = Column(String)
    is_recursive = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    domain = relationship("Domain", back_populates="file_permissions")

class FileOperation(Base):
    __tablename__ = "file_operations"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    operation_type = Column(String)  # copy, move, delete, compress, extract
    source_path = Column(String)
    destination_path = Column(String, nullable=True)
    status = Column(String)  # pending, in_progress, completed, failed
    size = Column(BigInteger, nullable=True)  # bytes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    domain = relationship("Domain", back_populates="file_operations")
    user = relationship("User", back_populates="file_operations")

class FileSearch(Base):
    __tablename__ = "file_searches"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    search_term = Column(String)
    search_path = Column(String)
    file_type = Column(String, nullable=True)  # all, file, directory
    size_min = Column(BigInteger, nullable=True)
    size_max = Column(BigInteger, nullable=True)
    modified_after = Column(DateTime(timezone=True), nullable=True)
    modified_before = Column(DateTime(timezone=True), nullable=True)
    results = Column(JSON)  # Arama sonuçları
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    domain = relationship("Domain", back_populates="file_searches")
    user = relationship("User", back_populates="file_searches")

class DirectoryRestriction(Base):
    __tablename__ = "directory_restrictions"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"))
    path = Column(String)  # Kısıtlanacak dizin
    restriction_type = Column(String)  # read, write, execute, all
    allowed_users = Column(JSON)  # İzin verilen kullanıcılar
    allowed_groups = Column(JSON)  # İzin verilen gruplar
    is_recursive = Column(Boolean, default=True)  # Alt dizinlere uygula
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    domain = relationship("Domain", back_populates="directory_restrictions")

class BackupRotation(Base):
    __tablename__ = "backup_rotations"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"))
    retention_days = Column(Integer, default=30)  # Varsayılan 30 gün
    max_backups = Column(Integer, default=10)  # Maksimum yedek sayısı
    keep_daily = Column(Integer, default=7)  # Son 7 günlük yedeği sakla
    keep_weekly = Column(Integer, default=4)  # Son 4 haftalık yedeği sakla
    keep_monthly = Column(Integer, default=3)  # Son 3 aylık yedeği sakla
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    domain = relationship("Domain", back_populates="backup_rotation")

class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    url = Column(String)
    events = Column(JSON)  # ["domain.created", "backup.completed", etc.]
    secret = Column(String)  # Webhook imzalama için
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="webhooks")

class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    type = Column(String)  # cpanel, directadmin, cloudflare, etc.
    name = Column(String)
    config = Column(JSON)  # API anahtarları, sunucu bilgileri vb.
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="integrations")
