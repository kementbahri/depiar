from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas
from ..auth import get_current_user
import asyncio
import json
from datetime import datetime, timedelta

router = APIRouter()

# WebSocket bağlantılarını tutacak sözlük
active_connections = {}

@router.get("/domains/{domain_id}/logs", response_model=List[schemas.DomainLog])
def get_domain_logs(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    limit: int = 100,
    type: str = None,
    source: str = None,
    start_date: datetime = None,
    end_date: datetime = None
):
    """Get domain logs with filtering options"""
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    query = db.query(models.DomainLog).filter(models.DomainLog.domain_id == domain_id)
    
    if type:
        query = query.filter(models.DomainLog.type == type)
    if source:
        query = query.filter(models.DomainLog.source == source)
    if start_date:
        query = query.filter(models.DomainLog.created_at >= start_date)
    if end_date:
        query = query.filter(models.DomainLog.created_at <= end_date)
    
    return query.order_by(models.DomainLog.created_at.desc()).limit(limit).all()

@router.post("/domains/{domain_id}/logs", response_model=schemas.DomainLog)
def create_domain_log(
    domain_id: int,
    log: schemas.DomainLogCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new domain log entry"""
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    db_log = models.DomainLog(
        domain_id=domain_id,
        type=log.type,
        message=log.message,
        source=log.source
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    # WebSocket bağlantılarına yeni log'u gönder
    if domain_id in active_connections:
        for connection in active_connections[domain_id]:
            asyncio.create_task(connection.send_json(db_log.dict()))
    
    return db_log

@router.websocket("/ws/domains/{domain_id}/logs")
async def websocket_endpoint(websocket: WebSocket, domain_id: int, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time log updates"""
    await websocket.accept()
    
    # Bağlantıyı kaydet
    if domain_id not in active_connections:
        active_connections[domain_id] = []
    active_connections[domain_id].append(websocket)
    
    try:
        while True:
            # Son 100 log'u gönder
            logs = db.query(models.DomainLog)\
                .filter(models.DomainLog.domain_id == domain_id)\
                .order_by(models.DomainLog.created_at.desc())\
                .limit(100)\
                .all()
            
            await websocket.send_json([log.dict() for log in logs])
            
            # Bağlantıyı canlı tut
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        # Bağlantı koptuğunda listeyi güncelle
        active_connections[domain_id].remove(websocket)
        if not active_connections[domain_id]:
            del active_connections[domain_id] 