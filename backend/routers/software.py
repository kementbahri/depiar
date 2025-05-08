from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from ..database import get_db
from ..services.software_service import SoftwareService
from ..models import SoftwareVersion, PHPConfiguration, DatabaseServer, WebServer
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(
    prefix="/api/software",
    tags=["software"]
)

class SoftwareVersionResponse(BaseModel):
    id: int
    server_id: int
    software_type: str
    current_version: str
    available_versions: List[str]
    last_check: datetime
    last_update: Optional[datetime]

    class Config:
        orm_mode = True

class PHPConfigResponse(BaseModel):
    id: int
    server_id: int
    version: str
    config_path: str
    fpm_status: bool
    max_execution_time: int
    memory_limit: str
    upload_max_filesize: str
    post_max_size: str
    max_input_vars: int
    last_modified: datetime

    class Config:
        orm_mode = True

class DatabaseConfigResponse(BaseModel):
    id: int
    server_id: int
    type: str
    version: str
    port: int
    root_password: str
    max_connections: int
    query_cache_size: str
    innodb_buffer_pool_size: str
    last_modified: datetime

    class Config:
        orm_mode = True

class WebServerConfigResponse(BaseModel):
    id: int
    server_id: int
    type: str
    version: str
    status: bool
    config_path: str
    document_root: str
    client_max_body_size: str
    keepalive_timeout: int
    last_modified: datetime

    class Config:
        orm_mode = True

class VersionUpdateRequest(BaseModel):
    target_version: str

class ConfigUpdateRequest(BaseModel):
    config: Dict

@router.get("/versions/{server_id}", response_model=List[SoftwareVersionResponse])
def get_software_versions(server_id: int, db: Session = Depends(get_db)):
    """Sunucudaki yazılım versiyonlarını getir"""
    service = SoftwareService(db)
    service.check_software_versions(server_id)
    
    versions = db.query(SoftwareVersion).filter(
        SoftwareVersion.server_id == server_id
    ).all()
    
    return versions

@router.post("/php/{server_id}/update", response_model=SoftwareVersionResponse)
def update_php_version(
    server_id: int,
    request: VersionUpdateRequest,
    db: Session = Depends(get_db)
):
    """PHP versiyonunu güncelle"""
    service = SoftwareService(db)
    service.update_php_version(server_id, request.target_version)
    
    version = db.query(SoftwareVersion).filter(
        SoftwareVersion.server_id == server_id,
        SoftwareVersion.software_type == "php"
    ).first()
    
    return version

@router.post("/mysql/{server_id}/update", response_model=SoftwareVersionResponse)
def update_mysql_version(
    server_id: int,
    request: VersionUpdateRequest,
    db: Session = Depends(get_db)
):
    """MySQL versiyonunu güncelle"""
    service = SoftwareService(db)
    service.update_mysql_version(server_id, request.target_version)
    
    version = db.query(SoftwareVersion).filter(
        SoftwareVersion.server_id == server_id,
        SoftwareVersion.software_type == "mysql"
    ).first()
    
    return version

@router.post("/apache/{server_id}/update", response_model=SoftwareVersionResponse)
def update_apache_version(
    server_id: int,
    request: VersionUpdateRequest,
    db: Session = Depends(get_db)
):
    """Apache versiyonunu güncelle"""
    service = SoftwareService(db)
    service.update_apache_version(server_id, request.target_version)
    
    version = db.query(SoftwareVersion).filter(
        SoftwareVersion.server_id == server_id,
        SoftwareVersion.software_type == "apache"
    ).first()
    
    return version

@router.post("/nginx/{server_id}/update", response_model=SoftwareVersionResponse)
def update_nginx_version(
    server_id: int,
    request: VersionUpdateRequest,
    db: Session = Depends(get_db)
):
    """Nginx versiyonunu güncelle"""
    service = SoftwareService(db)
    service.update_nginx_version(server_id, request.target_version)
    
    version = db.query(SoftwareVersion).filter(
        SoftwareVersion.server_id == server_id,
        SoftwareVersion.software_type == "nginx"
    ).first()
    
    return version

@router.get("/php-config/{server_id}", response_model=PHPConfigResponse)
def get_php_config(server_id: int, db: Session = Depends(get_db)):
    """PHP yapılandırmasını getir"""
    config = db.query(PHPConfiguration).filter(
        PHPConfiguration.server_id == server_id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PHP configuration not found"
        )
    
    return config

@router.post("/php-config/{server_id}", response_model=PHPConfigResponse)
def update_php_config(
    server_id: int,
    request: ConfigUpdateRequest,
    db: Session = Depends(get_db)
):
    """PHP yapılandırmasını güncelle"""
    service = SoftwareService(db)
    config = service.update_php_config(server_id, request.config)
    return config

@router.get("/database-config/{server_id}", response_model=DatabaseConfigResponse)
def get_database_config(server_id: int, db: Session = Depends(get_db)):
    """Veritabanı yapılandırmasını getir"""
    config = db.query(DatabaseServer).filter(
        DatabaseServer.server_id == server_id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Database configuration not found"
        )
    
    return config

@router.post("/database-config/{server_id}", response_model=DatabaseConfigResponse)
def update_database_config(
    server_id: int,
    request: ConfigUpdateRequest,
    db: Session = Depends(get_db)
):
    """Veritabanı yapılandırmasını güncelle"""
    service = SoftwareService(db)
    config = service.update_database_config(server_id, request.config)
    return config

@router.get("/web-server-config/{server_id}", response_model=WebServerConfigResponse)
def get_web_server_config(server_id: int, db: Session = Depends(get_db)):
    """Web sunucusu yapılandırmasını getir"""
    config = db.query(WebServer).filter(
        WebServer.server_id == server_id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Web server configuration not found"
        )
    
    return config

@router.post("/web-server-config/{server_id}", response_model=WebServerConfigResponse)
def update_web_server_config(
    server_id: int,
    request: ConfigUpdateRequest,
    db: Session = Depends(get_db)
):
    """Web sunucusu yapılandırmasını güncelle"""
    service = SoftwareService(db)
    config = service.update_web_server_config(server_id, request.config)
    return config 