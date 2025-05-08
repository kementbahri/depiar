from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from ..database import get_db
from ..services.file_system_service import FileSystemService
from ..models import FilePermission
from pydantic import BaseModel

router = APIRouter(prefix="/api/file-system", tags=["file-system"])

class FilePermissionCreate(BaseModel):
    path: str
    permissions: str
    is_recursive: bool = False

class FilePermissionResponse(BaseModel):
    id: int
    domain_id: int
    path: str
    owner: str
    group: str
    permissions: str
    is_recursive: bool

    class Config:
        orm_mode = True

@router.post("/{domain_id}/setup", status_code=status.HTTP_201_CREATED)
def setup_domain_directory(domain_id: int, db: Session = Depends(get_db)):
    """Domain için dosya sistemi yapılandırması oluştur"""
    try:
        service = FileSystemService(db)
        service.setup_domain_directory(domain_id)
        return {"message": "Domain directory setup completed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{domain_id}/permissions", response_model=FilePermissionResponse)
def set_file_permissions(
    domain_id: int,
    permission: FilePermissionCreate,
    db: Session = Depends(get_db)
):
    """Dosya/dizin izinlerini ayarla"""
    try:
        service = FileSystemService(db)
        file_permission = service.set_file_permissions(
            domain_id=domain_id,
            path=permission.path,
            permissions=permission.permissions,
            is_recursive=permission.is_recursive
        )
        return file_permission
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{domain_id}/permissions/{path:path}", response_model=Dict[str, Any])
def get_file_permissions(domain_id: int, path: str, db: Session = Depends(get_db)):
    """Dosya/dizin izinlerini getir"""
    try:
        service = FileSystemService(db)
        permissions = service.get_file_permissions(domain_id, path)
        return permissions
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 