from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
from .. import models, schemas
from ..database import get_db
from ..auth import get_current_admin_user

router = APIRouter(
    prefix="/api/service-plans",
    tags=["service-plans"]
)

@router.get("/", response_model=List[schemas.ServicePlan])
def get_service_plans(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Tüm servis planlarını listele"""
    return db.query(models.ServicePlan).all()

@router.get("/active", response_model=List[schemas.ServicePlan])
def get_active_service_plans(
    db: Session = Depends(get_db)
):
    """Aktif servis planlarını listele"""
    return db.query(models.ServicePlan).filter(models.ServicePlan.is_active == True).all()

@router.post("/", response_model=schemas.ServicePlan)
def create_service_plan(
    plan: schemas.ServicePlanCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Yeni servis planı oluştur"""
    # İsim kontrolü
    existing_plan = db.query(models.ServicePlan).filter(models.ServicePlan.name == plan.name).first()
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu isimde bir servis planı zaten mevcut"
        )
    
    # Features'ı JSON string'e çevir
    features_json = json.dumps(plan.features)
    
    db_plan = models.ServicePlan(
        name=plan.name,
        description=plan.description,
        price=plan.price,
        domains=plan.domains,
        disk_space=plan.disk_space,
        monthly_traffic=plan.monthly_traffic,
        email_accounts=plan.email_accounts,
        databases=plan.databases,
        ftp_accounts=plan.ftp_accounts,
        ssl_type=plan.ssl_type,
        support_type=plan.support_type,
        backup_frequency=plan.backup_frequency,
        php_version=plan.php_version,
        features=features_json
    )
    
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

@router.put("/{plan_id}", response_model=schemas.ServicePlan)
def update_service_plan(
    plan_id: int,
    plan: schemas.ServicePlanUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Servis planını güncelle"""
    db_plan = db.query(models.ServicePlan).filter(models.ServicePlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servis planı bulunamadı"
        )
    
    # İsim değişmişse kontrol et
    if plan.name and plan.name != db_plan.name:
        existing_plan = db.query(models.ServicePlan).filter(models.ServicePlan.name == plan.name).first()
        if existing_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu isimde bir servis planı zaten mevcut"
            )
    
    # Features'ı JSON string'e çevir
    if plan.features:
        features_json = json.dumps(plan.features)
        plan_dict = plan.dict(exclude_unset=True)
        plan_dict["features"] = features_json
    else:
        plan_dict = plan.dict(exclude_unset=True)
    
    # Planı güncelle
    for key, value in plan_dict.items():
        setattr(db_plan, key, value)
    
    db.commit()
    db.refresh(db_plan)
    return db_plan

@router.delete("/{plan_id}")
def delete_service_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Servis planını sil"""
    db_plan = db.query(models.ServicePlan).filter(models.ServicePlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servis planı bulunamadı"
        )
    
    # Planı kullanan müşteri var mı kontrol et
    if db_plan.customers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu planı kullanan müşteriler var. Önce müşterilerin planını değiştirin."
        )
    
    db.delete(db_plan)
    db.commit()
    return {"message": "Servis planı başarıyla silindi"}

@router.post("/{plan_id}/toggle")
def toggle_service_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Servis planını aktif/pasif yap"""
    db_plan = db.query(models.ServicePlan).filter(models.ServicePlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servis planı bulunamadı"
        )
    
    db_plan.is_active = not db_plan.is_active
    db.commit()
    return {"message": f"Servis planı {'aktif' if db_plan.is_active else 'pasif'} duruma getirildi"} 