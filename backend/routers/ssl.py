from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from .. import models, schemas
from ..auth import get_current_user
import subprocess
import os
from datetime import datetime, timedelta
from ..services.ssl_service import SSLService
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/ssl",
    tags=["ssl"]
)

class CertificateRequest(BaseModel):
    domain_id: int
    is_wildcard: bool = False

class CertificateResponse(BaseModel):
    id: int
    domain_id: int
    type: str
    status: str
    is_wildcard: bool
    issued_at: Optional[datetime]
    expires_at: Optional[datetime]
    renewed_at: Optional[datetime]
    path: Optional[str]

    class Config:
        orm_mode = True

@router.post("/request", response_model=CertificateResponse)
async def request_certificate(
    request: CertificateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """SSL sertifikası talep et"""
    ssl_service = SSLService(db)
    return ssl_service.request_certificate(request.domain_id, request.is_wildcard)

@router.post("/{cert_id}/renew", response_model=CertificateResponse)
async def renew_certificate(
    cert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """SSL sertifikasını yenile"""
    ssl_service = SSLService(db)
    success = ssl_service.renew_certificate(cert_id)
    if success:
        return db.query(models.SSL).filter(models.SSL.id == cert_id).first()
    raise HTTPException(status_code=500, detail="Renewal failed")

@router.get("/{cert_id}/status")
async def check_certificate_status(
    cert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Sertifika durumunu kontrol et"""
    ssl_service = SSLService(db)
    return ssl_service.check_certificate_status(cert_id)

@router.get("/domain/{domain_id}", response_model=List[CertificateResponse])
async def list_certificates(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Domain sertifikalarını listele"""
    return db.query(models.SSL).filter(models.SSL.domain_id == domain_id).all()

@router.delete("/{cert_id}")
async def delete_certificate(
    cert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Sertifikayı sil"""
    cert = db.query(models.SSL).filter(models.SSL.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    try:
        if os.path.exists(cert.certificate_path):
            os.remove(cert.certificate_path)
        if os.path.exists(cert.private_key_path):
            os.remove(cert.private_key_path)
        db.delete(cert)
        db.commit()
        return {"message": "Certificate deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/install/{domain_id}")
async def install_ssl(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Install SSL certificate for a domain using Let's Encrypt"""
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    try:
        # Let's Encrypt sertifika oluşturma komutu
        certbot_command = [
            "certbot",
            "certonly",
            "--webroot",
            "-w", "/var/www/html",  # Web root dizini
            "-d", domain.name,
            "--agree-tos",
            "--email", current_user.email,
            "--non-interactive"
        ]
        
        # Sertifika oluşturma işlemini çalıştır
        result = subprocess.run(certbot_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            # SSL sertifikasını veritabanına kaydet
            ssl_cert = models.SSL(
                domain_id=domain.id,
                type="lets_encrypt",
                status="active",
                start_date=datetime.utcnow(),
                expiry_date=datetime.utcnow() + timedelta(days=90),
                certificate_path=f"/etc/letsencrypt/live/{domain.name}/fullchain.pem",
                private_key_path=f"/etc/letsencrypt/live/{domain.name}/privkey.pem"
            )
            db.add(ssl_cert)
            
            # Domain'in SSL durumunu güncelle
            domain.ssl_enabled = True
            domain.ssl_expiry = ssl_cert.expiry_date
            
            db.commit()
            return {"message": "SSL certificate installed successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"SSL installation failed: {result.stderr}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{domain_id}")
async def remove_ssl(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Remove SSL certificate for a domain"""
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    try:
        # Let's Encrypt sertifikasını kaldır
        certbot_command = [
            "certbot",
            "delete",
            "--cert-name", domain.name,
            "--non-interactive"
        ]
        
        # Sertifika kaldırma işlemini çalıştır
        result = subprocess.run(certbot_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            # SSL sertifikasını veritabanından kaldır
            ssl_cert = db.query(models.SSL).filter(models.SSL.domain_id == domain.id).first()
            if ssl_cert:
                db.delete(ssl_cert)
            
            # Domain'in SSL durumunu güncelle
            domain.ssl_enabled = False
            domain.ssl_expiry = None
            
            db.commit()
            return {"message": "SSL certificate removed successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"SSL removal failed: {result.stderr}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 