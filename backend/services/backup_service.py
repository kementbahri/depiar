from datetime import datetime, timedelta
import os
import shutil
import subprocess
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from ..models import Backup, Domain, Database, DatabaseBackup, BackupRotation
from ..utils.database import DatabaseManager
from ..utils.ssh import SSHManager
import logging
import schedule
import time
import threading
from pathlib import Path
import json
import tarfile
import zipfile
import hashlib
import queue

logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self, db: Session):
        self.db = db
        self.ssh_manager = SSHManager()
        self.backup_queue = queue.Queue()
        self.restore_queue = queue.Queue()
        self.backup_root = "/var/backups"
        self.retention_days = {
            "daily": 7,
            "weekly": 4,
            "monthly": 12
        }
        self._start_worker_threads()

    def _start_worker_threads(self):
        """Yedekleme ve geri yükleme işlemleri için worker thread'leri başlat"""
        threading.Thread(target=self._backup_worker, daemon=True).start()
        threading.Thread(target=self._restore_worker, daemon=True).start()

    def _backup_worker(self):
        """Yedekleme işlemlerini yöneten worker thread"""
        while True:
            try:
                backup_id = self.backup_queue.get()
                self._process_backup(backup_id)
                self.backup_queue.task_done()
            except Exception as e:
                logger.error(f"Backup worker error: {str(e)}")

    def _restore_worker(self):
        """Geri yükleme işlemlerini yöneten worker thread"""
        while True:
            try:
                restore_id = self.restore_queue.get()
                self._process_restore(restore_id)
                self.restore_queue.task_done()
            except Exception as e:
                logger.error(f"Restore worker error: {str(e)}")

    def create_backup(self, domain_id: int, backup_type: str = "full", 
                     include_files: bool = True, include_database: bool = True,
                     include_emails: bool = True, compression: str = "zip") -> Backup:
        """Yeni yedek oluştur"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        # Yedek kaydını oluştur
        backup = Backup(
            domain_id=domain_id,
            type=backup_type,
            status="pending",
            include_files=include_files,
            include_database=include_database,
            include_emails=include_emails,
            compression=compression
        )
        self.db.add(backup)
        self.db.commit()

        # Yedekleme işlemini kuyruğa ekle
        self.backup_queue.put(backup.id)

        return backup

    def _process_backup(self, backup_id: int):
        """Yedekleme işlemini gerçekleştir"""
        backup = self.db.query(Backup).filter(Backup.id == backup_id).first()
        if not backup:
            return

        try:
            backup.status = "in_progress"
            backup.started_at = datetime.utcnow()
            self.db.commit()

            # Yedekleme dizinini oluştur
            backup_dir = f"/backups/{backup.domain.name}/{backup.id}"
            os.makedirs(backup_dir, exist_ok=True)

            # Dosyaları yedekle
            if backup.include_files:
                self._backup_files(backup, backup_dir)

            # Veritabanını yedekle
            if backup.include_database:
                self._backup_database(backup, backup_dir)

            # E-postaları yedekle
            if backup.include_emails:
                self._backup_emails(backup, backup_dir)

            # Yedeği sıkıştır
            self._compress_backup(backup, backup_dir)

            # Yedekleme rotasyonunu uygula
            self._apply_backup_rotation(backup.domain_id)

            backup.status = "completed"
            backup.completed_at = datetime.utcnow()
            backup.size = self._get_backup_size(backup_dir)
            backup.checksum = self._calculate_checksum(backup_dir)

        except Exception as e:
            backup.status = "failed"
            backup.error_message = str(e)
            logger.error(f"Backup failed: {str(e)}")

        finally:
            self.db.commit()

    def restore_backup(self, backup_id: int, restore_type: str = "full",
                      restore_files: bool = True, restore_database: bool = True,
                      restore_emails: bool = True) -> Dict:
        """Yedeği geri yükle"""
        backup = self.db.query(Backup).filter(Backup.id == backup_id).first()
        if not backup:
            raise ValueError("Backup not found")

        if backup.status != "completed":
            raise ValueError("Backup is not completed")

        # Geri yükleme işlemini kuyruğa ekle
        restore_id = f"{backup_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.restore_queue.put(restore_id)

        return {
            "restore_id": restore_id,
            "status": "pending",
            "message": "Restore process started"
        }

    def _process_restore(self, restore_id: str):
        """Geri yükleme işlemini gerçekleştir"""
        backup_id = int(restore_id.split('_')[0])
        backup = self.db.query(Backup).filter(Backup.id == backup_id).first()
        if not backup:
            return

        try:
            backup_dir = f"/backups/{backup.domain.name}/{backup.id}"

            # Yedeği doğrula
            if not self._verify_backup(backup_dir, backup.checksum):
                raise ValueError("Backup verification failed")

            # Yedeği aç
            self._extract_backup(backup_dir)

            # Dosyaları geri yükle
            if backup.include_files:
                self._restore_files(backup, backup_dir)

            # Veritabanını geri yükle
            if backup.include_database:
                self._restore_database(backup, backup_dir)

            # E-postaları geri yükle
            if backup.include_emails:
                self._restore_emails(backup, backup_dir)

        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            raise

    def download_backup(self, backup_id: int) -> str:
        """Yedeği indir"""
        backup = self.db.query(Backup).filter(Backup.id == backup_id).first()
        if not backup:
            raise ValueError("Backup not found")

        if backup.status != "completed":
            raise ValueError("Backup is not completed")

        backup_dir = f"/backups/{backup.domain.name}/{backup.id}"
        if not os.path.exists(backup_dir):
            raise ValueError("Backup files not found")

        # İndirme dizinini oluştur
        download_dir = f"/downloads/backups/{backup.domain.name}"
        os.makedirs(download_dir, exist_ok=True)

        # Yedeği kopyala
        download_path = f"{download_dir}/{backup.id}.{backup.compression}"
        shutil.copy2(f"{backup_dir}.{backup.compression}", download_path)

        return download_path

    def _apply_backup_rotation(self, domain_id: int):
        """Yedekleme rotasyonunu uygula"""
        rotation = self.db.query(BackupRotation).filter(
            BackupRotation.domain_id == domain_id
        ).first()

        if not rotation:
            return

        # Eski yedekleri bul
        old_backups = self.db.query(Backup).filter(
            Backup.domain_id == domain_id,
            Backup.status == "completed",
            Backup.created_at < datetime.utcnow() - timedelta(days=rotation.retention_days)
        ).all()

        # Eski yedekleri sil
        for backup in old_backups:
            self._delete_backup(backup)

    def _delete_backup(self, backup: Backup):
        """Yedeği sil"""
        try:
            backup_dir = f"/backups/{backup.domain.name}/{backup.id}"
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            if os.path.exists(f"{backup_dir}.{backup.compression}"):
                os.remove(f"{backup_dir}.{backup.compression}")

            self.db.delete(backup)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to delete backup: {str(e)}")

    def _backup_files(self, backup: Backup, backup_dir: str):
        """Dosyaları yedekle"""
        domain = backup.domain
        source_dir = f"/var/www/{domain.name}"
        target_dir = f"{backup_dir}/files"

        # Dosyaları kopyala
        shutil.copytree(source_dir, target_dir)

    def _backup_database(self, backup: Backup, backup_dir: str):
        """Veritabanını yedekle"""
        domain = backup.domain
        db_name = domain.database_name
        db_user = domain.database_user
        db_password = domain.database_password

        # MySQL dump oluştur
        dump_file = f"{backup_dir}/database.sql"
        subprocess.run([
            "mysqldump",
            f"--user={db_user}",
            f"--password={db_password}",
            db_name,
            f"--result-file={dump_file}"
        ], check=True)

    def _backup_emails(self, backup: Backup, backup_dir: str):
        """E-postaları yedekle"""
        domain = backup.domain
        mail_dir = f"/var/mail/{domain.name}"
        target_dir = f"{backup_dir}/emails"

        # E-postaları kopyala
        shutil.copytree(mail_dir, target_dir)

    def _compress_backup(self, backup: Backup, backup_dir: str):
        """Yedeği sıkıştır"""
        if backup.compression == "zip":
            with zipfile.ZipFile(f"{backup_dir}.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(backup_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_dir)
                        zipf.write(file_path, arcname)
        else:  # tar.gz
            with tarfile.open(f"{backup_dir}.tar.gz", "w:gz") as tar:
                tar.add(backup_dir, arcname=os.path.basename(backup_dir))

    def _extract_backup(self, backup_dir: str):
        """Yedeği aç"""
        if os.path.exists(f"{backup_dir}.zip"):
            with zipfile.ZipFile(f"{backup_dir}.zip", 'r') as zipf:
                zipf.extractall(backup_dir)
        elif os.path.exists(f"{backup_dir}.tar.gz"):
            with tarfile.open(f"{backup_dir}.tar.gz", "r:gz") as tar:
                tar.extractall(path=backup_dir)

    def _restore_files(self, backup: Backup, backup_dir: str):
        """Dosyaları geri yükle"""
        domain = backup.domain
        source_dir = f"{backup_dir}/files"
        target_dir = f"/var/www/{domain.name}"

        # Mevcut dosyaları yedekle
        temp_dir = f"{target_dir}_temp_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        shutil.move(target_dir, temp_dir)

        try:
            # Dosyaları geri yükle
            shutil.copytree(source_dir, target_dir)
            # Geçici dizini sil
            shutil.rmtree(temp_dir)
        except Exception as e:
            # Hata durumunda eski dosyaları geri yükle
            shutil.rmtree(target_dir)
            shutil.move(temp_dir, target_dir)
            raise e

    def _restore_database(self, backup: Backup, backup_dir: str):
        """Veritabanını geri yükle"""
        domain = backup.domain
        db_name = domain.database_name
        db_user = domain.database_user
        db_password = domain.database_password
        dump_file = f"{backup_dir}/database.sql"

        # Veritabanını geri yükle
        subprocess.run([
            "mysql",
            f"--user={db_user}",
            f"--password={db_password}",
            db_name,
            f"--execute=source {dump_file}"
        ], check=True)

    def _restore_emails(self, backup: Backup, backup_dir: str):
        """E-postaları geri yükle"""
        domain = backup.domain
        source_dir = f"{backup_dir}/emails"
        target_dir = f"/var/mail/{domain.name}"

        # Mevcut e-postaları yedekle
        temp_dir = f"{target_dir}_temp_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        shutil.move(target_dir, temp_dir)

        try:
            # E-postaları geri yükle
            shutil.copytree(source_dir, target_dir)
            # Geçici dizini sil
            shutil.rmtree(temp_dir)
        except Exception as e:
            # Hata durumunda eski e-postaları geri yükle
            shutil.rmtree(target_dir)
            shutil.move(temp_dir, target_dir)
            raise e

    def _get_backup_size(self, backup_dir: str) -> int:
        """Yedek boyutunu hesapla"""
        total_size = 0
        for dirpath, _, filenames in os.walk(backup_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size

    def _calculate_checksum(self, backup_dir: str) -> str:
        """Yedek için checksum hesapla"""
        sha256_hash = hashlib.sha256()
        for dirpath, _, filenames in os.walk(backup_dir):
            for f in sorted(filenames):
                fp = os.path.join(dirpath, f)
                with open(fp, "rb") as file:
                    for chunk in iter(lambda: file.read(4096), b""):
                        sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _verify_backup(self, backup_dir: str, expected_checksum: str) -> bool:
        """Yedeği doğrula"""
        actual_checksum = self._calculate_checksum(backup_dir)
        return actual_checksum == expected_checksum

def start_backup_scheduler():
    """Yedekleme zamanlayıcısını başlat"""
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)

    # Günlük yedekleme
    schedule.every().day.at("03:00").do(cleanup_old_backups)
    
    # Haftalık yedekleme
    schedule.every().monday.at("02:00").do(cleanup_old_backups)
    
    # Aylık yedekleme
    schedule.every().day.at("01:00").do(cleanup_old_backups)

    # Zamanlayıcıyı arka planda çalıştır
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start() 