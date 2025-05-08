from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas
from ..auth import get_current_user
import subprocess
import os
from datetime import datetime
import croniter

router = APIRouter()

# Scheduled Tasks Endpoints
@router.get("/domains/{domain_id}/tasks", response_model=List[schemas.ScheduledTask])
def get_scheduled_tasks(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all scheduled tasks for a domain"""
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    return domain.scheduled_tasks

@router.post("/domains/{domain_id}/tasks", response_model=schemas.ScheduledTask)
def create_scheduled_task(
    domain_id: int,
    task: schemas.ScheduledTaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new scheduled task for a domain"""
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    # Validate cron expression
    try:
        croniter.croniter(task.schedule)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid cron expression: {str(e)}")
    
    # Create task in database
    db_task = models.ScheduledTask(
        domain_id=domain_id,
        name=task.name,
        command=task.command,
        schedule=task.schedule
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Add to crontab
    try:
        cron_line = f"{task.schedule} {task.command}\n"
        with open(f"/etc/cron.d/domain_{domain_id}_{db_task.id}", "w") as f:
            f.write(cron_line)
    except Exception as e:
        db.delete(db_task)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to create cron job: {str(e)}")
    
    return db_task

@router.put("/domains/{domain_id}/tasks/{task_id}", response_model=schemas.ScheduledTask)
def update_scheduled_task(
    domain_id: int,
    task_id: int,
    task: schemas.ScheduledTaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a scheduled task"""
    db_task = db.query(models.ScheduledTask).filter(
        models.ScheduledTask.id == task_id,
        models.ScheduledTask.domain_id == domain_id
    ).first()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task.dict(exclude_unset=True)
    
    # Validate cron expression if provided
    if "schedule" in update_data:
        try:
            croniter.croniter(update_data["schedule"])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid cron expression: {str(e)}")
    
    # Update crontab if schedule or command changed
    if "schedule" in update_data or "command" in update_data:
        try:
            cron_line = f"{update_data.get('schedule', db_task.schedule)} {update_data.get('command', db_task.command)}\n"
            with open(f"/etc/cron.d/domain_{domain_id}_{task_id}", "w") as f:
                f.write(cron_line)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update cron job: {str(e)}")
    
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task

@router.delete("/domains/{domain_id}/tasks/{task_id}")
def delete_scheduled_task(
    domain_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a scheduled task"""
    db_task = db.query(models.ScheduledTask).filter(
        models.ScheduledTask.id == task_id,
        models.ScheduledTask.domain_id == domain_id
    ).first()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        # Remove from crontab
        os.remove(f"/etc/cron.d/domain_{domain_id}_{task_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove cron job: {str(e)}")
    
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted successfully"}

# Backup Endpoints
@router.get("/domains/{domain_id}/backups", response_model=List[schemas.Backup])
def get_backups(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all backups for a domain"""
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    return domain.backups

@router.post("/domains/{domain_id}/backups", response_model=schemas.Backup)
def create_backup(
    domain_id: int,
    backup: schemas.BackupCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new backup for a domain"""
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    # Create backup directory if it doesn't exist
    backup_dir = f"/var/backups/domains/{domain.name}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create backup record
    db_backup = models.Backup(
        domain_id=domain_id,
        name=backup.name,
        type=backup.type,
        status="pending",
        path=backup_dir,
        schedule=backup.schedule
    )
    db.add(db_backup)
    db.commit()
    db.refresh(db_backup)
    
    # Start backup process
    try:
        if backup.type == "full":
            # Backup both files and database
            backup_command = f"tar -czf {backup_dir}/{backup.name}.tar.gz /var/www/{domain.name} && mysqldump -u root -p {domain.name} > {backup_dir}/{backup.name}.sql"
        elif backup.type == "database":
            backup_command = f"mysqldump -u root -p {domain.name} > {backup_dir}/{backup.name}.sql"
        else:  # files
            backup_command = f"tar -czf {backup_dir}/{backup.name}.tar.gz /var/www/{domain.name}"
        
        # Run backup in background
        subprocess.Popen(backup_command, shell=True)
        
        # Update backup status
        db_backup.status = "in_progress"
        db.commit()
        
    except Exception as e:
        db_backup.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to start backup: {str(e)}")
    
    return db_backup

@router.delete("/domains/{domain_id}/backups/{backup_id}")
def delete_backup(
    domain_id: int,
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a backup"""
    db_backup = db.query(models.Backup).filter(
        models.Backup.id == backup_id,
        models.Backup.domain_id == domain_id
    ).first()
    
    if not db_backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    try:
        # Delete backup files
        if db_backup.type == "full":
            os.remove(f"{db_backup.path}/{db_backup.name}.tar.gz")
            os.remove(f"{db_backup.path}/{db_backup.name}.sql")
        elif db_backup.type == "database":
            os.remove(f"{db_backup.path}/{db_backup.name}.sql")
        else:  # files
            os.remove(f"{db_backup.path}/{db_backup.name}.tar.gz")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete backup files: {str(e)}")
    
    db.delete(db_backup)
    db.commit()
    return {"message": "Backup deleted successfully"} 