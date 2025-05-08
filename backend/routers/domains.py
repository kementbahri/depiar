from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas
from ..auth import get_current_user, require_admin, require_reseller, check_resource_access
from datetime import datetime

router = APIRouter()

@router.get("/domains/", response_model=List[schemas.DomainResponse])
async def list_domains(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Domain listesini getir"""
    if current_user.is_admin():
        # Admin tüm domainleri görebilir
        return db.query(models.Domain).all()
    elif current_user.is_reseller():
        # Satıcı kendi müşterilerinin domainlerini görebilir
        return db.query(models.Domain).join(models.User).filter(
            models.User.reseller_id == current_user.id
        ).all()
    else:
        # Müşteri sadece kendi domainlerini görebilir
        return db.query(models.Domain).filter(models.Domain.user_id == current_user.id).all()

@router.post("/domains/", response_model=schemas.DomainResponse)
async def create_domain(
    domain: schemas.DomainCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Yeni domain oluştur"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    db_domain = models.Domain(**domain.dict(), user_id=current_user.id)
    db.add(db_domain)
    db.commit()
    db.refresh(db_domain)
    return db_domain

@router.get("/domains/{domain_id}", response_model=schemas.DomainResponse)
async def get_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Domain detaylarını getir"""
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    if not check_resource_access(current_user, domain.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this domain"
        )
    
    return domain

@router.put("/domains/{domain_id}", response_model=schemas.DomainResponse)
async def update_domain(
    domain_id: int,
    domain_update: schemas.DomainUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Domain bilgilerini güncelle"""
    db_domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not db_domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    if not check_resource_access(current_user, db_domain.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this domain"
        )
    
    for key, value in domain_update.dict(exclude_unset=True).items():
        setattr(db_domain, key, value)
    
    db.commit()
    db.refresh(db_domain)
    return db_domain

@router.delete("/domains/{domain_id}")
async def delete_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Domain sil"""
    db_domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not db_domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    if not check_resource_access(current_user, db_domain.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this domain"
        )
    
    db.delete(db_domain)
    db.commit()
    return {"message": "Domain deleted successfully"}

@router.post("/domains/{domain_id}/suspend", response_model=schemas.Domain)
def suspend_domain(
    domain_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Suspend a domain"""
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    # Müşteri askıya alınmışsa domain'i askıya alamaz
    if domain.customer.status == models.CustomerStatus.SUSPENDED:
        raise HTTPException(
            status_code=400,
            detail="Cannot suspend domain: Customer account is suspended"
        )
    
    domain.status = models.DomainStatus.SUSPENDED
    domain.suspension_reason = reason
    domain.suspension_date = datetime.utcnow()
    
    # Domain'e ait tüm servisleri askıya al
    for email in domain.email_accounts:
        email.status = "suspended"
    
    for ftp in domain.ftp_accounts:
        ftp.status = "suspended"
    
    db.commit()
    db.refresh(domain)
    return domain

@router.post("/domains/{domain_id}/unsuspend", response_model=schemas.Domain)
def unsuspend_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Unsuspend a domain"""
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    # Müşteri askıya alınmışsa domain'i aktifleştiremez
    if domain.customer.status == models.CustomerStatus.SUSPENDED:
        raise HTTPException(
            status_code=400,
            detail="Cannot unsuspend domain: Customer account is suspended"
        )
    
    domain.status = models.DomainStatus.ACTIVE
    domain.suspension_reason = None
    domain.suspension_date = None
    
    # Domain'e ait tüm servisleri aktifleştir
    for email in domain.email_accounts:
        email.status = "active"
    
    for ftp in domain.ftp_accounts:
        ftp.status = "active"
    
    db.commit()
    db.refresh(domain)
    return domain 