from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Webhook
from ..services.webhook_service import WebhookService
from ..auth import get_current_user
from pydantic import BaseModel, HttpUrl
from datetime import datetime

router = APIRouter(
    prefix="/api/webhooks",
    tags=["webhooks"]
)

# Request Models
class WebhookCreate(BaseModel):
    url: HttpUrl
    events: List[str]

class WebhookUpdate(BaseModel):
    url: HttpUrl = None
    events: List[str] = None
    is_active: bool = None

# Response Models
class WebhookResponse(BaseModel):
    id: int
    url: str
    events: List[str]
    is_active: bool
    last_triggered: datetime = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Routes
@router.post("", response_model=WebhookResponse)
def create_webhook(
    webhook: WebhookCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Yeni webhook oluştur"""
    service = WebhookService(db)
    return service.create_webhook(
        user_id=current_user.id,
        url=str(webhook.url),
        events=webhook.events
    )

@router.get("", response_model=List[WebhookResponse])
def list_webhooks(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Webhook'ları listele"""
    service = WebhookService(db)
    return service.get_webhooks(current_user.id)

@router.put("/{webhook_id}", response_model=WebhookResponse)
def update_webhook(
    webhook_id: int,
    webhook: WebhookUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Webhook'u güncelle"""
    service = WebhookService(db)
    updated_webhook = service.update_webhook(
        webhook_id=webhook_id,
        url=str(webhook.url) if webhook.url else None,
        events=webhook.events,
        is_active=webhook.is_active
    )
    if not updated_webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    return updated_webhook

@router.delete("/{webhook_id}")
def delete_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Webhook'u sil"""
    service = WebhookService(db)
    service.delete_webhook(webhook_id)
    return {"message": "Webhook deleted successfully"}

@router.post("/{webhook_id}/trigger")
async def trigger_webhook(
    webhook_id: int,
    event: str,
    payload: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Webhook'u tetikle"""
    service = WebhookService(db)
    webhook = service.get_webhooks(current_user.id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    # Arka planda tetikle
    background_tasks.add_task(service.trigger_webhook, event, payload)
    return {"message": "Webhook triggered successfully"} 