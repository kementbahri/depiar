from database import SessionLocal, init_db
from models import (
    Customer, CustomerStatus, ServicePlan, Domain, DomainStatus,
    PHPConfiguration, WebServer, FilePermission, SSHServer
)
from services.php_service import PHPService
from services.web_server_service import WebServerService
from services.file_system_service import FileSystemService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_test_environment():
    """Test ortamını kur"""
    try:
        # Veritabanını başlat
        init_db()
        db = SessionLocal()

        # Test sunucusu oluştur
        server = SSHServer(
            name="Test Server",
            hostname="localhost",
            port=22,
            username="test",
            password="test123",
            is_active=True
        )
        db.add(server)
        db.commit()
        logger.info("Test sunucusu oluşturuldu")

        # Servis planı oluştur
        service_plan = ServicePlan(
            name="Test Plan",
            description="Test servis planı",
            price=100,
            domains=5,
            disk_space=10,
            monthly_traffic=100,
            email_accounts=10,
            databases=5,
            ftp_accounts=5,
            ssl_type="basic",
            support_type="email",
            backup_frequency="daily",
            php_version="8.1",
            features='["SSL", "Email", "Database"]'
        )
        db.add(service_plan)
        db.commit()
        logger.info("Servis planı oluşturuldu")

        # Müşteri oluştur
        customer = Customer(
            name="Test Müşteri",
            email="test@example.com",
            phone="5551234567",
            company="Test Şirket",
            address="Test Adres",
            hashed_password="test123",  # Gerçek uygulamada hash'lenmiş olmalı
            service_plan_id=service_plan.id
        )
        db.add(customer)
        db.commit()
        logger.info("Müşteri oluşturuldu")

        # Domain oluştur
        domain = Domain(
            customer_id=customer.id,
            server_id=server.id,
            name="test.com",
            status=DomainStatus.ACTIVE,
            php_version="8.1",
            server_type="nginx",
            ssl_enabled=True
        )
        db.add(domain)
        db.commit()
        logger.info("Domain oluşturuldu")

        # PHP yapılandırması oluştur
        php_service = PHPService(db)
        php_config = php_service.create_php_config(domain.id, "8.1")
        logger.info("PHP yapılandırması oluşturuldu")

        # Web sunucusu yapılandırması oluştur
        web_service = WebServerService(db)
        web_server = web_service.create_virtual_host(domain.id, "nginx")
        logger.info("Web sunucusu yapılandırması oluşturuldu")

        # Dosya sistemi yapılandırması oluştur
        file_service = FileSystemService(db)
        file_service.setup_domain_directory(domain.id)
        logger.info("Dosya sistemi yapılandırması oluşturuldu")

        # Test dosyası oluştur ve izinleri ayarla
        file_permission = file_service.set_file_permissions(
            domain_id=domain.id,
            path="/public_html/index.php",
            permissions="644"
        )
        logger.info("Dosya izinleri ayarlandı")

        # Kontroller
        domain = db.query(Domain).filter(Domain.id == domain.id).first()
        php_config = db.query(PHPConfiguration).filter(PHPConfiguration.domain_id == domain.id).first()
        web_server = db.query(WebServer).filter(WebServer.domain_id == domain.id).first()
        file_permission = db.query(FilePermission).filter(FilePermission.domain_id == domain.id).first()

        logger.info("\nKurulum Kontrolü:")
        logger.info(f"Domain: {domain.name} ({domain.status})")
        logger.info(f"PHP Config: {php_config.version} ({php_config.fpm_status})")
        logger.info(f"Web Server: {web_server.type} ({web_server.status})")
        logger.info(f"File Permission: {file_permission.path} ({file_permission.permissions})")

        return True

    except Exception as e:
        logger.error(f"Kurulum sırasında hata: {str(e)}")
        return False

    finally:
        db.close()

if __name__ == "__main__":
    setup_test_environment() 