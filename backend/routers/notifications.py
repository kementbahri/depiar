from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from services.notification_service import NotificationService
from database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

class NotificationPageBase(BaseModel):
    type: str
    title: str
    content: str

class NotificationPageCreate(NotificationPageBase):
    pass

class NotificationPageUpdate(NotificationPageBase):
    pass

class NotificationPageResponse(NotificationPageBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

@router.get("/", response_model=List[NotificationPageResponse])
def list_notification_pages(db: Session = Depends(get_db)):
    """Tüm bildirim sayfalarını listele"""
    service = NotificationService(db)
    return service.list_notification_pages()

@router.get("/{type}", response_model=NotificationPageResponse)
def get_notification_page(type: str, db: Session = Depends(get_db)):
    """Bildirim sayfasını getir"""
    service = NotificationService(db)
    notification = service.get_notification_page(type)
    if not notification:
        raise HTTPException(status_code=404, detail="Bildirim sayfası bulunamadı")
    return notification

@router.post("/", response_model=NotificationPageResponse)
def create_notification_page(notification: NotificationPageCreate, db: Session = Depends(get_db)):
    """Yeni bildirim sayfası oluştur"""
    service = NotificationService(db)
    return service.update_notification_page(
        type=notification.type,
        title=notification.title,
        content=notification.content
    )

@router.put("/{type}", response_model=NotificationPageResponse)
def update_notification_page(
    type: str,
    notification: NotificationPageUpdate,
    db: Session = Depends(get_db)
):
    """Bildirim sayfasını güncelle"""
    service = NotificationService(db)
    updated = service.update_notification_page(
        type=type,
        title=notification.title,
        content=notification.content
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Bildirim sayfası bulunamadı")
    return updated

@router.patch("/{type}/toggle")
def toggle_notification_page(type: str, is_active: bool, db: Session = Depends(get_db)):
    """Bildirim sayfasını aktif/pasif yap"""
    service = NotificationService(db)
    notification = service.toggle_notification_page(type, is_active)
    if not notification:
        raise HTTPException(status_code=404, detail="Bildirim sayfası bulunamadı")
    return {"message": "Bildirim sayfası durumu güncellendi"} 