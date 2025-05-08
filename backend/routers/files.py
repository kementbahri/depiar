from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
from ..database import get_db
from ..services.file_service import FileService
from ..models import FilePermission, FileOperation, FileSearch, DirectoryRestriction
from pydantic import BaseModel

router = APIRouter(prefix="/api/files", tags=["files"])

# Response Models
class FilePermissionResponse(BaseModel):
    id: int
    domain_id: int
    path: str
    owner: str
    group: str
    permissions: str
    is_recursive: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class FileOperationResponse(BaseModel):
    id: int
    domain_id: int
    user_id: int
    operation_type: str
    source_path: str
    destination_path: str
    status: str
    size: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        orm_mode = True

class FileSearchResponse(BaseModel):
    id: int
    domain_id: int
    user_id: int
    search_term: str
    search_path: str
    file_type: str
    size_min: Optional[int]
    size_max: Optional[int]
    modified_after: Optional[datetime]
    modified_before: Optional[datetime]
    results: List[str]
    created_at: datetime

    class Config:
        orm_mode = True

class DirectoryRestrictionResponse(BaseModel):
    id: int
    domain_id: int
    path: str
    restriction_type: str
    allowed_users: List[str]
    allowed_groups: List[str]
    is_recursive: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Request Models
class FilePermissionRequest(BaseModel):
    path: str
    permissions: str
    owner: str
    group: str
    is_recursive: bool = False

class FileOperationRequest(BaseModel):
    source_path: str
    destination_path: str

class FileSearchRequest(BaseModel):
    search_term: str
    search_path: str
    file_type: str = "all"
    size_min: Optional[int] = None
    size_max: Optional[int] = None
    modified_after: Optional[datetime] = None
    modified_before: Optional[datetime] = None

class DirectoryRestrictionRequest(BaseModel):
    path: str
    restriction_type: str
    allowed_users: List[str]
    allowed_groups: List[str]
    is_recursive: bool = True

# Endpoints
@router.post("/permissions/{domain_id}", response_model=FilePermissionResponse)
def set_file_permissions(domain_id: int, request: FilePermissionRequest, db: Session = Depends(get_db)):
    """Dosya izinlerini ayarla"""
    file_service = FileService(db)
    try:
        return file_service.set_file_permissions(
            domain_id=domain_id,
            path=request.path,
            permissions=request.permissions,
            owner=request.owner,
            group=request.group,
            is_recursive=request.is_recursive
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/copy/{domain_id}/{user_id}", response_model=FileOperationResponse)
def copy_file(domain_id: int, user_id: int, request: FileOperationRequest, db: Session = Depends(get_db)):
    """Dosya kopyala"""
    file_service = FileService(db)
    try:
        return file_service.copy_file(
            domain_id=domain_id,
            user_id=user_id,
            source_path=request.source_path,
            destination_path=request.destination_path
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/move/{domain_id}/{user_id}", response_model=FileOperationResponse)
def move_file(domain_id: int, user_id: int, request: FileOperationRequest, db: Session = Depends(get_db)):
    """Dosya taşı"""
    file_service = FileService(db)
    try:
        return file_service.move_file(
            domain_id=domain_id,
            user_id=user_id,
            source_path=request.source_path,
            destination_path=request.destination_path
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compress/{domain_id}/{user_id}", response_model=FileOperationResponse)
def compress_file(domain_id: int, user_id: int, request: FileOperationRequest, format: str = "zip", db: Session = Depends(get_db)):
    """Dosya sıkıştır"""
    file_service = FileService(db)
    try:
        return file_service.compress_file(
            domain_id=domain_id,
            user_id=user_id,
            source_path=request.source_path,
            destination_path=request.destination_path,
            format=format
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract/{domain_id}/{user_id}", response_model=FileOperationResponse)
def extract_file(domain_id: int, user_id: int, request: FileOperationRequest, db: Session = Depends(get_db)):
    """Dosya çıkart"""
    file_service = FileService(db)
    try:
        return file_service.extract_file(
            domain_id=domain_id,
            user_id=user_id,
            source_path=request.source_path,
            destination_path=request.destination_path
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/{domain_id}/{user_id}", response_model=FileSearchResponse)
def search_files(domain_id: int, user_id: int, request: FileSearchRequest, db: Session = Depends(get_db)):
    """Dosya ara"""
    file_service = FileService(db)
    try:
        return file_service.search_files(
            domain_id=domain_id,
            user_id=user_id,
            search_term=request.search_term,
            search_path=request.search_path,
            file_type=request.file_type,
            size_min=request.size_min,
            size_max=request.size_max,
            modified_after=request.modified_after,
            modified_before=request.modified_before
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restrictions/{domain_id}", response_model=DirectoryRestrictionResponse)
def add_directory_restriction(domain_id: int, request: DirectoryRestrictionRequest, db: Session = Depends(get_db)):
    """Dizin kısıtlaması ekle"""
    file_service = FileService(db)
    try:
        return file_service.add_directory_restriction(
            domain_id=domain_id,
            path=request.path,
            restriction_type=request.restriction_type,
            allowed_users=request.allowed_users,
            allowed_groups=request.allowed_groups,
            is_recursive=request.is_recursive
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/permissions/{domain_id}/{path}", response_model=Dict)
def check_file_permissions(domain_id: int, path: str, db: Session = Depends(get_db)):
    """Dosya izinlerini kontrol et"""
    file_service = FileService(db)
    try:
        return file_service.check_file_permissions(domain_id=domain_id, path=path)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 