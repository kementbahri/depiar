from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from ..database import get_db
from ..models import Backup, Domain, BackupRotation
from ..auth import get_current_user
from ..services.backup_service import BackupService
from pydantic import BaseModel
from datetime import datetime
import os

router = APIRouter(
    prefix="/api/backup",
    tags=["backup"]
)

# Request Models
class BackupCreate(BaseModel):
    type: str = "full"
    include_files: bool = True
    include_database: bool = True
    include_emails: bool = True
    compression: str = "zip"

class BackupRestore(BaseModel):
    restore_type: str = "full"
    restore_files: bool = True
    restore_database: bool = True
    restore_emails: bool = True

class BackupRotationCreate(BaseModel):
    retention_days: int = 30
    max_backups: int = 10
    keep_daily: int = 7
    keep_weekly: int = 4
    keep_monthly: int = 3

# Response Models
class BackupResponse(BaseModel):
    id: int
    domain_id: int
    type: str
    status: str
    include_files: bool
    include_database: bool
    include_emails: bool
    compression: str
    size: Optional[int]
    checksum: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True

class BackupRotationResponse(BaseModel):
    id: int
    domain_id: int
    retention_days: int
    max_backups: int
    keep_daily: int
    keep_weekly: int
    keep_monthly: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class RestoreResponse(BaseModel):
    restore_id: str
    status: str
    message: str

# Routes
@router.post("/{domain_id}", response_model=BackupResponse)
def create_backup(
    domain_id: int,
    backup: BackupCreate,
    db: Session = Depends(get_db)
):
    """Yeni yedek oluştur"""
    service = BackupService(db)
    try:
        return service.create_backup(
            domain_id=domain_id,
            backup_type=backup.type,
            include_files=backup.include_files,
            include_database=backup.include_database,
            include_emails=backup.include_emails,
            compression=backup.compression
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{backup_id}/restore", response_model=RestoreResponse)
def restore_backup(
    backup_id: int,
    restore: BackupRestore,
    db: Session = Depends(get_db)
):
    """Yedeği geri yükle"""
    service = BackupService(db)
    try:
        return service.restore_backup(
            backup_id=backup_id,
            restore_type=restore.restore_type,
            restore_files=restore.restore_files,
            restore_database=restore.restore_database,
            restore_emails=restore.restore_emails
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{backup_id}/download")
def download_backup(
    backup_id: int,
    db: Session = Depends(get_db)
):
    """Yedeği indir"""
    service = BackupService(db)
    try:
        download_path = service.download_backup(backup_id)
        return {
            "download_url": f"/downloads/backups/{os.path.basename(download_path)}"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{domain_id}/rotation", response_model=BackupRotationResponse)
def set_backup_rotation(
    domain_id: int,
    rotation: BackupRotationCreate,
    db: Session = Depends(get_db)
):
    """Yedekleme rotasyonu ayarla"""
    # Mevcut rotasyonu kontrol et
    existing_rotation = db.query(BackupRotation).filter(
        BackupRotation.domain_id == domain_id
    ).first()

    if existing_rotation:
        # Mevcut rotasyonu güncelle
        for key, value in rotation.dict().items():
            setattr(existing_rotation, key, value)
        existing_rotation.updated_at = datetime.utcnow()
        db.commit()
        return existing_rotation
    else:
        # Yeni rotasyon oluştur
        new_rotation = BackupRotation(
            domain_id=domain_id,
            **rotation.dict()
        )
        db.add(new_rotation)
        db.commit()
        db.refresh(new_rotation)
        return new_rotation

@router.get("/{domain_id}/rotation", response_model=BackupRotationResponse)
def get_backup_rotation(
    domain_id: int,
    db: Session = Depends(get_db)
):
    """Yedekleme rotasyonu ayarlarını getir"""
    rotation = db.query(BackupRotation).filter(
        BackupRotation.domain_id == domain_id
    ).first()

    if not rotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup rotation settings not found"
        )

    return rotation

@router.get("/{domain_id}/list", response_model=List[BackupResponse])
def list_backups(
    domain_id: int,
    db: Session = Depends(get_db)
):
    """Domain için yedekleri listele"""
    backups = db.query(Backup).filter(
        Backup.domain_id == domain_id
    ).order_by(Backup.created_at.desc()).all()

    return backups

@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Yedeği sil"""
    backup = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    try:
        if os.path.exists(backup.path):
            os.remove(backup.path)
        db.delete(backup)
        db.commit()
        return {"message": "Backup deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 