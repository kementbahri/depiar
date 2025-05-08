from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database
from ..auth import get_current_admin_user, get_password_hash, get_current_user
from datetime import datetime

router = APIRouter(
    prefix="/api/customers",
    tags=["customers"]
)

@router.get("/", response_model=List[schemas.Customer])
def get_customers(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Tüm müşterileri listele"""
    customers = db.query(models.Customer).all()
    return customers

@router.post("/", response_model=schemas.Customer)
def create_customer(
    customer: schemas.CustomerCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Yeni müşteri oluştur"""
    # E-posta kontrolü
    db_customer = db.query(models.Customer).filter(models.Customer.email == customer.email).first()
    if db_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi zaten kullanılıyor"
        )
    
    # Şifreyi hashle
    hashed_password = get_password_hash(customer.password)
    
    # Müşteriyi oluştur
    db_customer = models.Customer(
        name=customer.name,
        email=customer.email,
        phone=customer.phone,
        company=customer.company,
        address=customer.address,
        hashed_password=hashed_password,
        status=customer.status,
        package=customer.package
    )
    
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.get("/{customer_id}", response_model=schemas.Customer)
def get_customer(
    customer_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Müşteri detaylarını getir"""
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Müşteri bulunamadı"
        )
    return customer

@router.put("/{customer_id}", response_model=schemas.Customer)
def update_customer(
    customer_id: int,
    customer: schemas.CustomerUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Müşteri bilgilerini güncelle"""
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Müşteri bulunamadı"
        )
    
    # E-posta değişmişse kontrol et
    if customer.email != db_customer.email:
        existing_customer = db.query(models.Customer).filter(models.Customer.email == customer.email).first()
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu e-posta adresi zaten kullanılıyor"
            )
    
    # Müşteri bilgilerini güncelle
    for key, value in customer.dict(exclude_unset=True).items():
        setattr(db_customer, key, value)
    
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Müşteriyi sil"""
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Müşteri bulunamadı"
        )
    
    db.delete(db_customer)
    db.commit()
    return {"message": "Müşteri başarıyla silindi"}

@router.post("/{customer_id}/password")
def change_customer_password(
    customer_id: int,
    password_data: schemas.PasswordChange,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Müşteri şifresini değiştir"""
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not db_customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Müşteri bulunamadı"
        )
    
    # Şifreyi hashle ve güncelle
    hashed_password = get_password_hash(password_data.password)
    db_customer.hashed_password = hashed_password
    
    db.commit()
    return {"message": "Şifre başarıyla değiştirildi"}

@router.post("/customers/{customer_id}/suspend", response_model=schemas.Customer)
def suspend_customer(
    customer_id: int,
    reason: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Suspend a customer and all their domains"""
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer.status = models.CustomerStatus.SUSPENDED
    customer.suspension_reason = reason
    customer.suspension_date = datetime.utcnow()
    
    # Müşteriye ait tüm domainleri askıya al
    for domain in customer.domains:
        domain.status = models.DomainStatus.SUSPENDED
        domain.suspension_reason = f"Customer suspended: {reason}"
        domain.suspension_date = datetime.utcnow()
        
        # Domain'e ait tüm servisleri askıya al
        for email in domain.email_accounts:
            email.status = "suspended"
        
        for ftp in domain.ftp_accounts:
            ftp.status = "suspended"
    
    db.commit()
    db.refresh(customer)
    return customer

@router.post("/customers/{customer_id}/unsuspend", response_model=schemas.Customer)
def unsuspend_customer(
    customer_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Unsuspend a customer and all their domains"""
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer.status = models.CustomerStatus.ACTIVE
    customer.suspension_reason = None
    customer.suspension_date = None
    
    # Müşteriye ait tüm domainleri aktifleştir
    for domain in customer.domains:
        domain.status = models.DomainStatus.ACTIVE
        domain.suspension_reason = None
        domain.suspension_date = None
        
        # Domain'e ait tüm servisleri aktifleştir
        for email in domain.email_accounts:
            email.status = "active"
        
        for ftp in domain.ftp_accounts:
            ftp.status = "active"
    
    db.commit()
    db.refresh(customer)
    return customer

@router.get("/packages", response_model=dict)
def get_package_details():
    """Get details of all available packages"""
    return {
        "basic": models.CustomerPackage.BASIC.details,
        "pro": models.CustomerPackage.PRO.details,
        "enterprise": models.CustomerPackage.ENTERPRISE.details
    } 