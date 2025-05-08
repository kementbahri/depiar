from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Database, DatabaseBackup, DatabaseOptimization
from ..auth import get_current_user
from ..utils.database import DatabaseManager
from pydantic import BaseModel
from datetime import datetime
import os
import shutil

router = APIRouter(
    prefix="/api/database-management",
    tags=["database-management"]
)

class DatabaseBackupCreate(BaseModel):
    database_id: int
    backup_type: str = "full"  # full, structure, data

class DatabaseOptimizationCreate(BaseModel):
    database_id: int
    optimization_type: str = "all"  # all, analyze, optimize, repair

class DatabaseBackupResponse(BaseModel):
    id: int
    database_id: int
    filename: str
    size: int
    status: str
    backup_type: str
    created_at: datetime
    completed_at: Optional[datetime]
    path: str

    class Config:
        orm_mode = True

class DatabaseOptimizationResponse(BaseModel):
    id: int
    database_id: int
    status: str
    optimization_type: str
    tables_optimized: int
    created_at: datetime
    completed_at: Optional[datetime]
    details: Optional[str]

    class Config:
        orm_mode = True

@router.post("/backup", response_model=DatabaseBackupResponse)
async def create_backup(
    backup: DatabaseBackupCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Veritabanı yedeği oluştur"""
    database = db.query(Database).filter(Database.id == backup.database_id).first()
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")

    # Yedekleme dizinini oluştur
    backup_dir = f"/var/backups/databases/{database.name}"
    os.makedirs(backup_dir, exist_ok=True)

    # Yedek dosya adını oluştur
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{database.name}_{backup.backup_type}_{timestamp}.sql"
    backup_path = os.path.join(backup_dir, filename)

    # Yedekleme kaydını oluştur
    backup_record = DatabaseBackup(
        database_id=database.id,
        filename=filename,
        size=0,
        status="pending",
        backup_type=backup.backup_type,
        path=backup_path
    )
    db.add(backup_record)
    db.commit()

    try:
        # Veritabanı yöneticisini oluştur
        db_manager = DatabaseManager(
            host=database.host,
            port=database.port,
            username=database.username,
            password=database.password
        )

        # Yedekleme işlemini gerçekleştir
        success, message = db_manager.backup_database(
            database=database.name,
            backup_path=backup_path,
            backup_type=backup.backup_type
        )

        if success:
            # Yedekleme kaydını güncelle
            backup_record.status = "completed"
            backup_record.completed_at = datetime.utcnow()
            backup_record.size = os.path.getsize(backup_path)
            db.commit()
            return backup_record
        else:
            backup_record.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail=message)

    except Exception as e:
        backup_record.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restore/{backup_id}")
async def restore_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Veritabanı yedeğini geri yükle"""
    backup = db.query(DatabaseBackup).filter(DatabaseBackup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    database = db.query(Database).filter(Database.id == backup.database_id).first()
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")

    try:
        # Veritabanı yöneticisini oluştur
        db_manager = DatabaseManager(
            host=database.host,
            port=database.port,
            username=database.username,
            password=database.password
        )

        # Geri yükleme işlemini gerçekleştir
        success, message = db_manager.restore_database(
            database=database.name,
            backup_path=backup.path
        )

        if success:
            return {"message": "Database restored successfully"}
        else:
            raise HTTPException(status_code=500, detail=message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize", response_model=DatabaseOptimizationResponse)
async def optimize_database(
    optimization: DatabaseOptimizationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Veritabanını optimize et"""
    database = db.query(Database).filter(Database.id == optimization.database_id).first()
    if not database:
        raise HTTPException(status_code=404, detail="Database not found")

    # Optimizasyon kaydını oluştur
    optimization_record = DatabaseOptimization(
        database_id=database.id,
        status="pending",
        optimization_type=optimization.optimization_type
    )
    db.add(optimization_record)
    db.commit()

    try:
        # Veritabanı yöneticisini oluştur
        db_manager = DatabaseManager(
            host=database.host,
            port=database.port,
            username=database.username,
            password=database.password
        )

        # Optimizasyon işlemini gerçekleştir
        success, message, details = db_manager.optimize_database(database.name)

        if success:
            # Optimizasyon kaydını güncelle
            optimization_record.status = "completed"
            optimization_record.completed_at = datetime.utcnow()
            optimization_record.tables_optimized = len(details.get("optimized", []))
            optimization_record.details = str(details)
            db.commit()
            return optimization_record
        else:
            optimization_record.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail=message)

    except Exception as e:
        optimization_record.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backups/{database_id}", response_model=List[DatabaseBackupResponse])
async def list_backups(
    database_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Veritabanı yedeklerini listele"""
    return db.query(DatabaseBackup).filter(DatabaseBackup.database_id == database_id).all()

@router.get("/optimizations/{database_id}", response_model=List[DatabaseOptimizationResponse])
async def list_optimizations(
    database_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Veritabanı optimizasyonlarını listele"""
    return db.query(DatabaseOptimization).filter(DatabaseOptimization.database_id == database_id).all()

@router.delete("/backup/{backup_id}")
async def delete_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Veritabanı yedeğini sil"""
    backup = db.query(DatabaseBackup).filter(DatabaseBackup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    try:
        # Yedek dosyasını sil
        if os.path.exists(backup.path):
            os.remove(backup.path)

        # Yedekleme kaydını sil
        db.delete(backup)
        db.commit()

        return {"message": "Backup deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 