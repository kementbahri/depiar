from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import SSHServer, SSHCommand, User
from ..auth import get_current_user, check_admin
from ..utils.ssh import execute_ssh_command
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(
    prefix="/api/ssh",
    tags=["ssh"]
)

class SSHServerCreate(BaseModel):
    name: str
    hostname: str
    port: int = 22
    username: str
    password: str = None
    private_key: str = None
    description: str = None

class SSHServerResponse(BaseModel):
    id: int
    name: str
    hostname: str
    port: int
    username: str
    description: str = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class SSHCommandCreate(BaseModel):
    server_id: int
    command: str

class SSHCommandResponse(BaseModel):
    id: int
    server_id: int
    user_id: int
    command: str
    status: str
    output: str = None
    exit_code: int = None
    created_at: datetime
    completed_at: datetime = None

    class Config:
        orm_mode = True

@router.post("/servers", response_model=SSHServerResponse)
async def create_ssh_server(
    server: SSHServerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Yeni SSH sunucusu ekle"""
    db_server = SSHServer(**server.dict())
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server

@router.get("/servers", response_model=List[SSHServerResponse])
async def list_ssh_servers(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """SSH sunucularını listele"""
    return db.query(SSHServer).all()

@router.get("/servers/{server_id}", response_model=SSHServerResponse)
async def get_ssh_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """SSH sunucusu detaylarını getir"""
    server = db.query(SSHServer).filter(SSHServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server

@router.delete("/servers/{server_id}")
async def delete_ssh_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """SSH sunucusunu sil"""
    server = db.query(SSHServer).filter(SSHServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    db.delete(server)
    db.commit()
    return {"message": "Server deleted successfully"}

@router.post("/execute", response_model=SSHCommandResponse)
async def execute_command(
    command: SSHCommandCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """SSH komutu çalıştır"""
    success, output = execute_ssh_command(
        db=db,
        server_id=command.server_id,
        command=command.command,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=output
        )
    
    command_record = db.query(SSHCommand).order_by(SSHCommand.id.desc()).first()
    return command_record

@router.get("/commands", response_model=List[SSHCommandResponse])
async def list_commands(
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Çalıştırılan komutları listele"""
    return db.query(SSHCommand).order_by(SSHCommand.created_at.desc()).all()

@router.get("/commands/{command_id}", response_model=SSHCommandResponse)
async def get_command(
    command_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    """Komut detaylarını getir"""
    command = db.query(SSHCommand).filter(SSHCommand.id == command_id).first()
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    return command 