from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database import get_db
from ..models import Integration
from ..services.integration_service import IntegrationService
from ..auth import get_current_user
from pydantic import BaseModel, HttpUrl
from datetime import datetime

router = APIRouter(
    prefix="/api/integrations",
    tags=["integrations"]
)

# Request Models
class IntegrationCreate(BaseModel):
    type: str
    name: str
    config: Dict[str, Any]

class IntegrationUpdate(BaseModel):
    config: Dict[str, Any] = None
    is_active: bool = None

# Response Models
class IntegrationResponse(BaseModel):
    id: int
    type: str
    name: str
    is_active: bool
    last_sync: datetime = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Routes
@router.post("", response_model=IntegrationResponse)
def create_integration(
    integration: IntegrationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Yeni entegrasyon oluştur"""
    service = IntegrationService(db)
    return service.create_integration(
        user_id=current_user.id,
        type=integration.type,
        name=integration.name,
        config=integration.config
    )

@router.get("", response_model=List[IntegrationResponse])
def list_integrations(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Entegrasyonları listele"""
    service = IntegrationService(db)
    return service.get_integrations(current_user.id)

@router.put("/{integration_id}", response_model=IntegrationResponse)
def update_integration(
    integration_id: int,
    integration: IntegrationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Entegrasyonu güncelle"""
    service = IntegrationService(db)
    updated_integration = service.update_integration(
        integration_id=integration_id,
        config=integration.config,
        is_active=integration.is_active
    )
    if not updated_integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    return updated_integration

@router.delete("/{integration_id}")
def delete_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Entegrasyonu sil"""
    service = IntegrationService(db)
    service.delete_integration(integration_id)
    return {"message": "Integration deleted successfully"}

@router.post("/{integration_id}/sync")
async def sync_integration(
    integration_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Entegrasyonu senkronize et"""
    service = IntegrationService(db)
    integration = service.get_integrations(current_user.id)
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Arka planda senkronize et
    background_tasks.add_task(service.sync_integration, integration_id)
    return {"message": "Integration sync started"} 