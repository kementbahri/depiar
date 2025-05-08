import os
import subprocess
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models import Domain, SSLCertificate
import acme
import josepy
from acme import client
from acme import messages
from acme import challenges
import OpenSSL
import requests

logger = logging.getLogger(__name__)

class SSLService:
    def __init__(self, db: Session):
        self.db = db
        self.acme_directory = "https://acme-v02.api.letsencrypt.org/directory"
        self.cert_root = "/etc/ssl/certs"
        self.key_root = "/etc/ssl/private"
        self.webroot = "/var/www/letsencrypt"

    def request_certificate(self, domain_id: int, is_wildcard: bool = False) -> SSLCertificate:
        """SSL sertifikası talep et"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        # Sertifika kaydını oluştur
        cert = SSLCertificate(
            domain_id=domain.id,
            type="letsencrypt",
            status="pending",
            is_wildcard=is_wildcard
        )
        self.db.add(cert)
        self.db.commit()

        try:
            # ACME istemcisini oluştur
            acme_client = self._create_acme_client()

            # Domain listesini hazırla
            domains = [domain.name]
            if is_wildcard:
                domains.append(f"*.{domain.name}")

            # Sertifika talebi oluştur
            order = acme_client.new_order(domains)

            # HTTP-01 doğrulaması
            for auth in order.authorizations:
                challenge = auth.body.challenges[0]
                response = challenge.response(acme_client.net.key)
                
                # Doğrulama dosyasını oluştur
                self._create_validation_file(
                    domain.name,
                    challenge.path,
                    response.validation
                )

                # Doğrulamayı tamamla
                acme_client.answer_challenge(challenge, response)

            # Sertifikayı finalize et
            order.finalize()

            # Sertifikayı indir
            cert_pem = order.fullchain_pem
            key_pem = order.private_key_pem

            # Sertifika dosyalarını kaydet
            cert_path = os.path.join(self.cert_root, f"{domain.name}.pem")
            key_path = os.path.join(self.key_root, f"{domain.name}.key")

            with open(cert_path, "wb") as f:
                f.write(cert_pem)
            with open(key_path, "wb") as f:
                f.write(key_pem)

            # Sertifika bilgilerini güncelle
            cert.status = "active"
            cert.issued_at = datetime.utcnow()
            cert.expires_at = datetime.utcnow() + timedelta(days=90)
            cert.path = cert_path
            cert.key_path = key_path
            self.db.commit()

            return cert

        except Exception as e:
            cert.status = "failed"
            self.db.commit()
            logger.error(f"Certificate request failed: {str(e)}")
            raise

    def renew_certificate(self, cert_id: int) -> bool:
        """SSL sertifikasını yenile"""
        cert = self.db.query(SSLCertificate).filter(SSLCertificate.id == cert_id).first()
        if not cert:
            raise ValueError("Certificate not found")

        try:
            # Yeni sertifika talep et
            new_cert = self.request_certificate(cert.domain_id, cert.is_wildcard)
            
            # Eski sertifikayı güncelle
            cert.status = "renewed"
            cert.renewed_at = datetime.utcnow()
            cert.renewed_by = new_cert.id
            self.db.commit()

            return True

        except Exception as e:
            logger.error(f"Certificate renewal failed: {str(e)}")
            raise

    def check_certificate_status(self, cert_id: int) -> dict:
        """Sertifika durumunu kontrol et"""
        cert = self.db.query(SSLCertificate).filter(SSLCertificate.id == cert_id).first()
        if not cert:
            raise ValueError("Certificate not found")

        try:
            # Sertifika dosyasını oku
            with open(cert.path, "rb") as f:
                cert_data = f.read()

            # Sertifika bilgilerini çıkar
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_data)
            
            return {
                "subject": x509.get_subject().CN,
                "issuer": x509.get_issuer().CN,
                "not_before": datetime.strptime(x509.get_notBefore().decode(), "%Y%m%d%H%M%SZ"),
                "not_after": datetime.strptime(x509.get_notAfter().decode(), "%Y%m%d%H%M%SZ"),
                "serial": x509.get_serial_number(),
                "version": x509.get_version()
            }

        except Exception as e:
            logger.error(f"Certificate status check failed: {str(e)}")
            raise

    def _create_acme_client(self) -> client.ClientV2:
        """ACME istemcisi oluştur"""
        # Özel anahtar oluştur
        key = josepy.JWKRSA(key=acme.jose.util.openssl_crypto.generate_private_key("rsa"))

        # ACME hesabı oluştur
        net = acme.client.ClientNetwork(key)
        directory = messages.Directory.from_json(net.get(self.acme_directory).json())
        client = client.ClientV2(directory, net)

        # Hesabı kaydet
        client.new_account(messages.NewRegistration.from_data(
            email="admin@example.com",
            terms_of_service_agreed=True
        ))

        return client

    def _create_validation_file(self, domain: str, path: str, content: str):
        """Doğrulama dosyası oluştur"""
        validation_path = os.path.join(self.webroot, path.lstrip("/"))
        os.makedirs(os.path.dirname(validation_path), exist_ok=True)
        
        with open(validation_path, "w") as f:
            f.write(content)

def start_ssl_renewal_scheduler():
    """SSL yenileme zamanlayıcısını başlat"""
    def check_certificates():
        db = Session()
        ssl_service = SSLService(db)
        
        # 30 günden az kalan sertifikaları yenile
        cutoff_date = datetime.utcnow() + timedelta(days=30)
        certs = db.query(SSLCertificate).filter(
            SSLCertificate.expires_at < cutoff_date,
            SSLCertificate.status == "active"
        ).all()

        for cert in certs:
            try:
                ssl_service.renew_certificate(cert.id)
            except Exception as e:
                logger.error(f"Certificate renewal failed for {cert.domain.name}: {str(e)}")

        db.close()

    # Her gün kontrol et
    schedule.every().day.at("02:00").do(check_certificates)

    # Zamanlayıcıyı arka planda çalıştır
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start() 