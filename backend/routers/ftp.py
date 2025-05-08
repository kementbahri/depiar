from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas
from ..auth import get_current_user
import subprocess
import os
from datetime import datetime

router = APIRouter()

@router.get("/domains/{domain_id}/ftp", response_model=List[schemas.FTPAccount])
def get_ftp_accounts(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all FTP accounts for a domain"""
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    return domain.ftp_accounts

@router.post("/domains/{domain_id}/ftp", response_model=schemas.FTPAccount)
def create_ftp_account(
    domain_id: int,
    ftp_account: schemas.FTPAccountCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new FTP account for a domain"""
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    # Check if username already exists
    existing_account = db.query(models.FTPAccount).filter(
        models.FTPAccount.username == ftp_account.username
    ).first()
    if existing_account:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    try:
        # Create FTP user in system
        useradd_command = [
            "useradd",
            "-m",  # Create home directory
            "-d", ftp_account.home_directory,  # Set home directory
            "-s", "/bin/false",  # Disable shell access
            ftp_account.username
        ]
        
        result = subprocess.run(useradd_command, capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to create FTP user: {result.stderr}")
        
        # Set password
        chpasswd_command = f"echo '{ftp_account.username}:{ftp_account.password}' | chpasswd"
        result = subprocess.run(chpasswd_command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to set password: {result.stderr}")
        
        # Create FTP account in database
        db_ftp_account = models.FTPAccount(
            domain_id=domain_id,
            username=ftp_account.username,
            password=ftp_account.password,  # In production, hash the password
            home_directory=ftp_account.home_directory
        )
        db.add(db_ftp_account)
        db.commit()
        db.refresh(db_ftp_account)
        
        return db_ftp_account
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/domains/{domain_id}/ftp/{account_id}", response_model=schemas.FTPAccount)
def update_ftp_account(
    domain_id: int,
    account_id: int,
    ftp_account: schemas.FTPAccountUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update an FTP account"""
    db_account = db.query(models.FTPAccount).filter(
        models.FTPAccount.id == account_id,
        models.FTPAccount.domain_id == domain_id
    ).first()
    
    if not db_account:
        raise HTTPException(status_code=404, detail="FTP account not found")
    
    try:
        update_data = ftp_account.dict(exclude_unset=True)
        
        # Update password if provided
        if "password" in update_data:
            chpasswd_command = f"echo '{db_account.username}:{update_data['password']}' | chpasswd"
            result = subprocess.run(chpasswd_command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                raise HTTPException(status_code=500, detail=f"Failed to update password: {result.stderr}")
        
        # Update home directory if provided
        if "home_directory" in update_data:
            usermod_command = [
                "usermod",
                "-d", update_data["home_directory"],
                db_account.username
            ]
            result = subprocess.run(usermod_command, capture_output=True, text=True)
            if result.returncode != 0:
                raise HTTPException(status_code=500, detail=f"Failed to update home directory: {result.stderr}")
        
        # Update database record
        for key, value in update_data.items():
            setattr(db_account, key, value)
        
        db.commit()
        db.refresh(db_account)
        return db_account
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/domains/{domain_id}/ftp/{account_id}")
def delete_ftp_account(
    domain_id: int,
    account_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete an FTP account"""
    db_account = db.query(models.FTPAccount).filter(
        models.FTPAccount.id == account_id,
        models.FTPAccount.domain_id == domain_id
    ).first()
    
    if not db_account:
        raise HTTPException(status_code=404, detail="FTP account not found")
    
    try:
        # Delete FTP user from system
        userdel_command = [
            "userdel",
            "-r",  # Remove home directory
            db_account.username
        ]
        
        result = subprocess.run(userdel_command, capture_output=True, text=True)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to delete FTP user: {result.stderr}")
        
        # Delete from database
        db.delete(db_account)
        db.commit()
        
        return {"message": "FTP account deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 