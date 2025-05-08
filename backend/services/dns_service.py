import logging
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from ..models import DNSRecord, SPFRecord, DKIMRecord, DMARCRecord, Domain, DNSType
from ..utils.ssh import SSHManager
import json
import re
import subprocess
import dns.resolver
import dns.zone
import dns.query
import dns.tsigkeyring
import dns.update

logger = logging.getLogger(__name__)

class DNSService:
    def __init__(self, db: Session):
        self.db = db

    def create_dns_record(self, domain_id: int, name: str, type: DNSType, content: str, 
                         ttl: int = 3600, priority: Optional[int] = None) -> DNSRecord:
        """DNS kaydı oluştur"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        # DNS kaydını oluştur
        record = DNSRecord(
            domain_id=domain_id,
            name=name,
            type=type,
            content=content,
            ttl=ttl,
            priority=priority
        )
        self.db.add(record)
        self.db.commit()

        # DNS sunucusunda kaydı güncelle
        self._update_dns_server(domain.name, record)

        return record

    def update_dns_record(self, record_id: int, content: str, ttl: Optional[int] = None, 
                         priority: Optional[int] = None) -> DNSRecord:
        """DNS kaydını güncelle"""
        record = self.db.query(DNSRecord).filter(DNSRecord.id == record_id).first()
        if not record:
            raise ValueError("DNS record not found")

        # Kaydı güncelle
        record.content = content
        if ttl is not None:
            record.ttl = ttl
        if priority is not None:
            record.priority = priority
        record.updated_at = datetime.utcnow()

        self.db.commit()

        # DNS sunucusunda kaydı güncelle
        self._update_dns_server(record.domain.name, record)

        return record

    def delete_dns_record(self, record_id: int):
        """DNS kaydını sil"""
        record = self.db.query(DNSRecord).filter(DNSRecord.id == record_id).first()
        if not record:
            raise ValueError("DNS record not found")

        # DNS sunucusundan kaydı sil
        self._delete_dns_server_record(record.domain.name, record)

        # Veritabanından kaydı sil
        self.db.delete(record)
        self.db.commit()

    def create_spf_record(self, domain_id: int, mechanisms: List[str], qualifier: str = "+") -> SPFRecord:
        """SPF kaydı oluştur"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        # SPF kaydını oluştur
        spf = SPFRecord(
            domain_id=domain_id,
            mechanisms=mechanisms,
            qualifier=qualifier
        )
        self.db.add(spf)
        self.db.commit()

        # DNS kaydını oluştur
        content = f"v=spf1 {qualifier} {' '.join(mechanisms)}"
        self.create_dns_record(
            domain_id=domain_id,
            name="@",
            type=DNSType.SPF,
            content=content
        )

        return spf

    def create_dkim_record(self, domain_id: int, selector: str, public_key: str, 
                          algorithm: str = "rsa-sha256", key_type: str = "rsa", 
                          key_size: int = 2048) -> DKIMRecord:
        """DKIM kaydı oluştur"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        # DKIM kaydını oluştur
        dkim = DKIMRecord(
            domain_id=domain_id,
            selector=selector,
            public_key=public_key,
            algorithm=algorithm,
            key_type=key_type,
            key_size=key_size
        )
        self.db.add(dkim)
        self.db.commit()

        # DNS kaydını oluştur
        content = f"v=DKIM1; k={key_type}; p={public_key}"
        self.create_dns_record(
            domain_id=domain_id,
            name=f"{selector}._domainkey",
            type=DNSType.TXT,
            content=content
        )

        return dkim

    def create_dmarc_record(self, domain_id: int, policy: str = "none", 
                           subdomain_policy: str = "none", percentage: int = 100,
                           report_aggregate: Optional[str] = None,
                           report_forensic: Optional[str] = None) -> DMARCRecord:
        """DMARC kaydı oluştur"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        # DMARC kaydını oluştur
        dmarc = DMARCRecord(
            domain_id=domain_id,
            policy=policy,
            subdomain_policy=subdomain_policy,
            percentage=percentage,
            report_aggregate=report_aggregate,
            report_forensic=report_forensic
        )
        self.db.add(dmarc)
        self.db.commit()

        # DNS kaydını oluştur
        content = f"v=DMARC1; p={policy}; sp={subdomain_policy}; pct={percentage}"
        if report_aggregate:
            content += f"; rua=mailto:{report_aggregate}"
        if report_forensic:
            content += f"; ruf=mailto:{report_forensic}"

        self.create_dns_record(
            domain_id=domain_id,
            name="_dmarc",
            type=DNSType.TXT,
            content=content
        )

        return dmarc

    def verify_dns_records(self, domain_id: int) -> Dict:
        """DNS kayıtlarını doğrula"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        results = {
            "spf": self._verify_spf(domain.name),
            "dkim": self._verify_dkim(domain.name),
            "dmarc": self._verify_dmarc(domain.name)
        }

        return results

    def _update_dns_server(self, domain_name: str, record: DNSRecord):
        """DNS sunucusunda kaydı güncelle"""
        try:
            # DNS sunucusu yapılandırmasını al
            # Bu kısım DNS sunucunuzun yapılandırmasına göre değişebilir
            # Örnek olarak BIND için:
            zone = dns.zone.from_file(f"/etc/bind/zones/{domain_name}.db", domain_name)
            update = dns.update.Update(domain_name)
            
            if record.type in [DNSType.A, DNSType.AAAA, DNSType.CNAME]:
                update.replace(record.name, record.ttl, record.type, record.content)
            elif record.type == DNSType.MX:
                update.replace(record.name, record.ttl, record.type, 
                             f"{record.priority} {record.content}")
            else:  # TXT, SPF, DKIM, DMARC
                update.replace(record.name, record.ttl, record.type, 
                             f'"{record.content}"')

            dns.query.tcp(update, "localhost")
            
        except Exception as e:
            logger.error(f"Failed to update DNS server: {str(e)}")
            raise

    def _delete_dns_server_record(self, domain_name: str, record: DNSRecord):
        """DNS sunucusundan kaydı sil"""
        try:
            update = dns.update.Update(domain_name)
            update.delete(record.name, record.type)
            dns.query.tcp(update, "localhost")
        except Exception as e:
            logger.error(f"Failed to delete DNS record: {str(e)}")
            raise

    def _verify_spf(self, domain_name: str) -> Dict:
        """SPF kaydını doğrula"""
        try:
            spf_records = dns.resolver.resolve(domain_name, "TXT")
            for record in spf_records:
                if record.strings[0].decode().startswith("v=spf1"):
                    return {
                        "status": "valid",
                        "record": record.strings[0].decode()
                    }
            return {
                "status": "missing",
                "message": "No SPF record found"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def _verify_dkim(self, domain_name: str) -> Dict:
        """DKIM kaydını doğrula"""
        try:
            # DKIM selector'ları için yaygın değerler
            selectors = ["default", "mail", "selector1", "selector2"]
            for selector in selectors:
                try:
                    dkim_records = dns.resolver.resolve(f"{selector}._domainkey.{domain_name}", "TXT")
                    for record in dkim_records:
                        if "v=DKIM1" in record.strings[0].decode():
                            return {
                                "status": "valid",
                                "selector": selector,
                                "record": record.strings[0].decode()
                            }
                except dns.resolver.NXDOMAIN:
                    continue
            return {
                "status": "missing",
                "message": "No DKIM record found"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def _verify_dmarc(self, domain_name: str) -> Dict:
        """DMARC kaydını doğrula"""
        try:
            dmarc_records = dns.resolver.resolve(f"_dmarc.{domain_name}", "TXT")
            for record in dmarc_records:
                if "v=DMARC1" in record.strings[0].decode():
                    return {
                        "status": "valid",
                        "record": record.strings[0].decode()
                    }
            return {
                "status": "missing",
                "message": "No DMARC record found"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            } 