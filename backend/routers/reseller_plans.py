from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
from .. import models, schemas
from ..database import get_db
from ..auth import get_current_admin_user

router = APIRouter(
    prefix="/api/reseller-plans",
    tags=["reseller-plans"]
)

@router.get("/", response_model=List[schemas.ResellerPlan])
def get_reseller_plans(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Tüm satıcı planlarını listele"""
    return db.query(models.ResellerPlan).all()

@router.get("/active", response_model=List[schemas.ResellerPlan])
def get_active_reseller_plans(
    db: Session = Depends(get_db)
):
    """Aktif satıcı planlarını listele"""
    return db.query(models.ResellerPlan).filter(models.ResellerPlan.is_active == True).all()

@router.post("/", response_model=schemas.ResellerPlan)
def create_reseller_plan(
    plan: schemas.ResellerPlanCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Yeni satıcı planı oluştur"""
    # İsim kontrolü
    existing_plan = db.query(models.ResellerPlan).filter(models.ResellerPlan.name == plan.name).first()
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu isimde bir satıcı planı zaten mevcut"
        )
    
    # Features'ı JSON string'e çevir
    features_json = json.dumps(plan.features)
    
    db_plan = models.ResellerPlan(
        name=plan.name,
        description=plan.description,
        price=plan.price,
        max_customers=plan.max_customers,
        max_domains=plan.max_domains,
        max_disk_space=plan.max_disk_space,
        max_monthly_traffic=plan.max_monthly_traffic,
        can_create_plans=plan.can_create_plans,
        can_manage_dns=plan.can_manage_dns,
        can_manage_ssl=plan.can_manage_ssl,
        can_manage_backups=plan.can_manage_backups,
        support_type=plan.support_type,
        features=features_json
    )
    
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

@router.put("/{plan_id}", response_model=schemas.ResellerPlan)
def update_reseller_plan(
    plan_id: int,
    plan: schemas.ResellerPlanUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Satıcı planını güncelle"""
    db_plan = db.query(models.ResellerPlan).filter(models.ResellerPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Satıcı planı bulunamadı"
        )
    
    # İsim değişmişse kontrol et
    if plan.name and plan.name != db_plan.name:
        existing_plan = db.query(models.ResellerPlan).filter(models.ResellerPlan.name == plan.name).first()
        if existing_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu isimde bir satıcı planı zaten mevcut"
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
def delete_reseller_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Satıcı planını sil"""
    db_plan = db.query(models.ResellerPlan).filter(models.ResellerPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Satıcı planı bulunamadı"
        )
    
    # Planı kullanan satıcı var mı kontrol et
    if db_plan.resellers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu planı kullanan satıcılar var. Önce satıcıların planını değiştirin."
        )
    
    db.delete(db_plan)
    db.commit()
    return {"message": "Satıcı planı başarıyla silindi"}

@router.post("/{plan_id}/toggle")
def toggle_reseller_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Satıcı planını aktif/pasif yap"""
    db_plan = db.query(models.ResellerPlan).filter(models.ResellerPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Satıcı planı bulunamadı"
        )
    
    db_plan.is_active = not db_plan.is_active
    db.commit()
    return {"message": f"Satıcı planı {'aktif' if db_plan.is_active else 'pasif'} duruma getirildi"} 