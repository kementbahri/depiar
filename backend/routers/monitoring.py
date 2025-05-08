from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import ServerMetric, SecurityAlert, IPBlock, SystemUpdate, MalwareScan, MalwareThreat
from ..auth import get_current_user
from ..services.monitoring_service import MonitoringService
from pydantic import BaseModel
from datetime import datetime, timedelta

router = APIRouter(
    prefix="/api/monitoring",
    tags=["monitoring"]
)

class MetricResponse(BaseModel):
    id: int
    server_id: int
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_in: int
    network_out: int
    uptime: int
    load_average: str
    created_at: datetime

    class Config:
        orm_mode = True

class SecurityAlertResponse(BaseModel):
    id: int
    server_id: int
    type: str
    severity: str
    message: str
    source_ip: Optional[str]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        orm_mode = True

class IPBlockResponse(BaseModel):
    id: int
    server_id: int
    ip_address: str
    reason: str
    blocked_at: datetime
    expires_at: Optional[datetime]
    is_active: bool

    class Config:
        orm_mode = True

class SystemUpdateResponse(BaseModel):
    id: int
    server_id: int
    package_name: str
    current_version: str
    available_version: str
    update_type: str
    status: str
    scheduled_at: Optional[datetime]
    installed_at: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True

class MalwareScanResponse(BaseModel):
    id: int
    server_id: int
    scan_type: str
    status: str
    threats_found: int
    scan_path: str
    started_at: datetime
    completed_at: Optional[datetime]
    details: Optional[str]

    class Config:
        orm_mode = True

class MalwareThreatResponse(BaseModel):
    id: int
    scan_id: int
    file_path: str
    threat_type: str
    severity: str
    status: str
    detected_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        orm_mode = True

@router.get("/metrics/{server_id}", response_model=List[MetricResponse])
async def get_metrics(
    server_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Sunucu metriklerini getir"""
    query = db.query(ServerMetric).filter(ServerMetric.server_id == server_id)
    
    if start_time:
        query = query.filter(ServerMetric.created_at >= start_time)
    if end_time:
        query = query.filter(ServerMetric.created_at <= end_time)
    
    return query.order_by(ServerMetric.created_at.desc()).all()

@router.get("/alerts/{server_id}", response_model=List[SecurityAlertResponse])
async def get_alerts(
    server_id: int,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Güvenlik uyarılarını getir"""
    query = db.query(SecurityAlert).filter(SecurityAlert.server_id == server_id)
    
    if status:
        query = query.filter(SecurityAlert.status == status)
    if severity:
        query = query.filter(SecurityAlert.severity == severity)
    
    return query.order_by(SecurityAlert.created_at.desc()).all()

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Güvenlik uyarısını çözüldü olarak işaretle"""
    alert = db.query(SecurityAlert).filter(SecurityAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Alert resolved successfully"}

@router.get("/blocked-ips/{server_id}", response_model=List[IPBlockResponse])
async def get_blocked_ips(
    server_id: int,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Engellenen IP'leri getir"""
    query = db.query(IPBlock).filter(IPBlock.server_id == server_id)
    
    if active_only:
        query = query.filter(IPBlock.is_active == True)
    
    return query.order_by(IPBlock.blocked_at.desc()).all()

@router.post("/block-ip/{server_id}")
async def block_ip(
    server_id: int,
    ip: str,
    reason: str,
    duration_days: int = 1,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """IP adresini engelle"""
    monitoring = MonitoringService(db)
    server = db.query(SSHServer).filter(SSHServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    monitoring._block_ip(server, ip, reason)
    return {"message": "IP blocked successfully"}

@router.delete("/block-ip/{block_id}")
async def unblock_ip(
    block_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """IP engelini kaldır"""
    block = db.query(IPBlock).filter(IPBlock.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="IP block not found")
    
    block.is_active = False
    db.commit()
    
    return {"message": "IP unblocked successfully"}

@router.get("/updates/{server_id}", response_model=List[SystemUpdateResponse])
async def get_updates(
    server_id: int,
    status: Optional[str] = None,
    update_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Sistem güncellemelerini getir"""
    query = db.query(SystemUpdate).filter(SystemUpdate.server_id == server_id)
    
    if status:
        query = query.filter(SystemUpdate.status == status)
    if update_type:
        query = query.filter(SystemUpdate.update_type == update_type)
    
    return query.order_by(SystemUpdate.created_at.desc()).all()

@router.post("/updates/{update_id}/install")
async def install_update(
    update_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Sistem güncellemesini yükle"""
    update = db.query(SystemUpdate).filter(SystemUpdate.id == update_id).first()
    if not update:
        raise HTTPException(status_code=404, detail="Update not found")
    
    monitoring = MonitoringService(db)
    server = db.query(SSHServer).filter(SSHServer.id == update.server_id).first()
    
    try:
        ssh = SSHManager(server.host, server.port, server.username, server.password)
        ssh.execute_command(f"apt-get install -y {update.package_name}")
        
        update.status = "installed"
        update.installed_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Update installed successfully"}
    except Exception as e:
        update.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/malware-scans/{server_id}", response_model=List[MalwareScanResponse])
async def get_malware_scans(
    server_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Malware taramalarını getir"""
    query = db.query(MalwareScan).filter(MalwareScan.server_id == server_id)
    
    if status:
        query = query.filter(MalwareScan.status == status)
    
    return query.order_by(MalwareScan.started_at.desc()).all()

@router.post("/malware-scan/{server_id}")
async def start_malware_scan(
    server_id: int,
    scan_type: str = "quick",
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Malware taraması başlat"""
    monitoring = MonitoringService(db)
    try:
        scan = monitoring.scan_malware(server_id, scan_type)
        return scan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/malware-threats/{scan_id}", response_model=List[MalwareThreatResponse])
async def get_malware_threats(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Malware tehditlerini getir"""
    return db.query(MalwareThreat).filter(MalwareThreat.scan_id == scan_id).all()

@router.post("/malware-threats/{threat_id}/resolve")
async def resolve_malware_threat(
    threat_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Malware tehdidini çözüldü olarak işaretle"""
    threat = db.query(MalwareThreat).filter(MalwareThreat.id == threat_id).first()
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    threat.status = "resolved"
    threat.resolved_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Threat resolved successfully"} 