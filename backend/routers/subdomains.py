from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Subdomain, Domain, DNSRecord, DNSType
from ..auth import get_current_user
from pydantic import BaseModel
from datetime import datetime
import os

router = APIRouter(
    prefix="/api/subdomains",
    tags=["subdomains"]
)

class SubdomainCreate(BaseModel):
    domain_id: int
    name: str
    document_root: str = None
    php_version: str = "8.1"
    ssl_enabled: bool = True

class SubdomainResponse(BaseModel):
    id: int
    domain_id: int
    name: str
    document_root: str
    php_version: str
    ssl_enabled: bool
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

@router.post("/", response_model=SubdomainResponse)
async def create_subdomain(
    subdomain: SubdomainCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Yeni subdomain oluştur"""
    # Domain kontrolü
    domain = db.query(Domain).filter(Domain.id == subdomain.domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    # Subdomain adı kontrolü
    existing = db.query(Subdomain).filter(
        Subdomain.domain_id == subdomain.domain_id,
        Subdomain.name == subdomain.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subdomain already exists")

    # Document root oluştur
    if not subdomain.document_root:
        subdomain.document_root = f"/var/www/vhosts/{domain.name}/subdomains/{subdomain.name}"

    # Subdomain oluştur
    db_subdomain = Subdomain(**subdomain.dict())
    db.add(db_subdomain)

    # DNS kaydı oluştur
    dns_record = DNSRecord(
        domain_id=subdomain.domain_id,
        name=subdomain.name,
        type=DNSType.A,
        content=os.getenv("SERVER_IP", "127.0.0.1"),  # Sunucu IP'si
        ttl=3600
    )
    db.add(dns_record)

    # Apache/Nginx konfigürasyonu oluştur
    try:
        # Apache konfigürasyonu
        apache_conf = f"""
<VirtualHost *:80>
    ServerName {subdomain.name}.{domain.name}
    DocumentRoot {subdomain.document_root}
    
    <Directory {subdomain.document_root}>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${{APACHE_LOG_DIR}}/{subdomain.name}.{domain.name}-error.log
    CustomLog ${{APACHE_LOG_DIR}}/{subdomain.name}.{domain.name}-access.log combined
</VirtualHost>
"""
        # Konfigürasyon dosyasını kaydet
        conf_path = f"/etc/apache2/sites-available/{subdomain.name}.{domain.name}.conf"
        with open(conf_path, "w") as f:
            f.write(apache_conf)

        # Siteyi aktifleştir
        os.system(f"a2ensite {subdomain.name}.{domain.name}.conf")
        os.system("systemctl reload apache2")

        # Document root dizinini oluştur
        os.makedirs(subdomain.document_root, exist_ok=True)
        os.chown(subdomain.document_root, int(os.getenv("WEB_USER_UID", "1000")), int(os.getenv("WEB_GROUP_GID", "1000")))

        db.commit()
        return db_subdomain

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subdomain configuration failed: {str(e)}"
        )

@router.get("/", response_model=List[SubdomainResponse])
async def list_subdomains(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Domain'e ait subdomainleri listele"""
    return db.query(Subdomain).filter(Subdomain.domain_id == domain_id).all()

@router.get("/{subdomain_id}", response_model=SubdomainResponse)
async def get_subdomain(
    subdomain_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Subdomain detaylarını getir"""
    subdomain = db.query(Subdomain).filter(Subdomain.id == subdomain_id).first()
    if not subdomain:
        raise HTTPException(status_code=404, detail="Subdomain not found")
    return subdomain

@router.delete("/{subdomain_id}")
async def delete_subdomain(
    subdomain_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Subdomain'i sil"""
    subdomain = db.query(Subdomain).filter(Subdomain.id == subdomain_id).first()
    if not subdomain:
        raise HTTPException(status_code=404, detail="Subdomain not found")

    try:
        # Apache konfigürasyonunu kaldır
        conf_path = f"/etc/apache2/sites-available/{subdomain.name}.{subdomain.domain.name}.conf"
        if os.path.exists(conf_path):
            os.system(f"a2dissite {subdomain.name}.{subdomain.domain.name}.conf")
            os.remove(conf_path)
            os.system("systemctl reload apache2")

        # DNS kaydını sil
        db.query(DNSRecord).filter(
            DNSRecord.domain_id == subdomain.domain_id,
            DNSRecord.name == subdomain.name
        ).delete()

        # Subdomain'i sil
        db.delete(subdomain)
        db.commit()

        return {"message": "Subdomain deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subdomain deletion failed: {str(e)}"
        ) 