import paramiko
import os
from typing import Optional, Tuple
from ..models import SSHServer
from sqlalchemy.orm import Session
from datetime import datetime

class SSHManager:
    def __init__(self, server: SSHServer):
        self.server = server
        self.client = None

    def connect(self) -> bool:
        """SSH sunucusuna bağlan"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Private key veya şifre ile bağlan
            if self.server.private_key:
                key = paramiko.RSAKey.from_private_key_file(self.server.private_key)
                self.client.connect(
                    hostname=self.server.hostname,
                    port=self.server.port,
                    username=self.server.username,
                    pkey=key
                )
            else:
                self.client.connect(
                    hostname=self.server.hostname,
                    port=self.server.port,
                    username=self.server.username,
                    password=self.server.password
                )
            return True
        except Exception as e:
            print(f"SSH connection error: {str(e)}")
            return False

    def execute_command(self, command: str) -> Tuple[int, str, str]:
        """Komut çalıştır"""
        if not self.client:
            if not self.connect():
                return -1, "", "Connection failed"

        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            error = stderr.read().decode()
            return exit_code, output, error
        except Exception as e:
            return -1, "", str(e)

    def close(self):
        """Bağlantıyı kapat"""
        if self.client:
            self.client.close()

def execute_ssh_command(db: Session, server_id: int, command: str, user_id: int) -> Tuple[bool, str]:
    """SSH komutunu çalıştır ve sonucu kaydet"""
    server = db.query(SSHServer).filter(SSHServer.id == server_id).first()
    if not server:
        return False, "Server not found"

    # Komut kaydını oluştur
    command_record = SSHCommand(
        server_id=server_id,
        user_id=user_id,
        command=command,
        status="running"
    )
    db.add(command_record)
    db.commit()

    try:
        # SSH bağlantısı kur ve komutu çalıştır
        ssh = SSHManager(server)
        exit_code, output, error = ssh.execute_command(command)
        
        # Sonucu güncelle
        command_record.status = "success" if exit_code == 0 else "failed"
        command_record.output = output if exit_code == 0 else error
        command_record.exit_code = exit_code
        command_record.completed_at = datetime.utcnow()
        
        db.commit()
        return exit_code == 0, output if exit_code == 0 else error
    except Exception as e:
        command_record.status = "failed"
        command_record.output = str(e)
        command_record.completed_at = datetime.utcnow()
        db.commit()
        return False, str(e)
    finally:
        if 'ssh' in locals():
            ssh.close() 