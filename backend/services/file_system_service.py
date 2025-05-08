import os
import pwd
import grp
import shutil
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models import Domain, FilePermission
import subprocess

logger = logging.getLogger(__name__)

class FileSystemService:
    def __init__(self, db: Session):
        self.db = db
        self.web_root = "/var/www"
        self.default_permissions = {
            "files": "644",
            "directories": "755"
        }

    def setup_domain_directory(self, domain_id: int) -> None:
        """Domain için dosya sistemi yapılandırması oluştur"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        # Kullanıcı ve grup oluştur
        self._create_user_and_group(domain.name)

        # Dizin yapısını oluştur
        domain_root = os.path.join(self.web_root, domain.name)
        public_html = os.path.join(domain_root, "public_html")
        logs_dir = os.path.join(domain_root, "logs")
        tmp_dir = os.path.join(domain_root, "tmp")

        # Dizinleri oluştur
        for directory in [domain_root, public_html, logs_dir, tmp_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

        # İzinleri ayarla
        self._set_permissions(domain_root, domain.name)
        self._set_permissions(public_html, domain.name)
        self._set_permissions(logs_dir, domain.name)
        self._set_permissions(tmp_dir, domain.name)

        # Varsayılan index.php oluştur
        index_php = os.path.join(public_html, "index.php")
        if not os.path.exists(index_php):
            with open(index_php, "w") as f:
                f.write("""<?php
phpinfo();
""")
            self._set_permissions(index_php, domain.name)

    def _create_user_and_group(self, username: str) -> None:
        """Kullanıcı ve grup oluştur"""
        try:
            # Kullanıcı oluştur
            subprocess.run(
                ["useradd", "-m", "-d", f"/var/www/{username}", username],
                check=True
            )

            # Grup oluştur
            subprocess.run(
                ["groupadd", username],
                check=True
            )

            # Kullanıcıyı gruba ekle
            subprocess.run(
                ["usermod", "-a", "-G", username, username],
                check=True
            )

            # Kullanıcıyı www-data grubuna ekle
            subprocess.run(
                ["usermod", "-a", "-G", "www-data", username],
                check=True
            )

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create user/group: {e.stderr.decode()}")
            raise

    def _set_permissions(self, path: str, username: str) -> None:
        """Dosya/dizin izinlerini ayarla"""
        try:
            # Sahipliği değiştir
            shutil.chown(path, user=username, group=username)

            # İzinleri ayarla
            if os.path.isdir(path):
                os.chmod(path, int(self.default_permissions["directories"], 8))
            else:
                os.chmod(path, int(self.default_permissions["files"], 8))

        except Exception as e:
            logger.error(f"Failed to set permissions: {str(e)}")
            raise

    def set_file_permissions(self, domain_id: int, path: str, permissions: str, is_recursive: bool = False) -> FilePermission:
        """Dosya/dizin izinlerini ayarla"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        full_path = os.path.join(self.web_root, domain.name, path.lstrip("/"))
        if not os.path.exists(full_path):
            raise ValueError("Path not found")

        try:
            # İzinleri ayarla
            if is_recursive and os.path.isdir(full_path):
                for root, dirs, files in os.walk(full_path):
                    for item in dirs + files:
                        item_path = os.path.join(root, item)
                        os.chmod(item_path, int(permissions, 8))
            else:
                os.chmod(full_path, int(permissions, 8))

            # İzinleri veritabanına kaydet
            file_permission = FilePermission(
                domain_id=domain_id,
                path=path,
                owner=domain.name,
                group=domain.name,
                permissions=permissions,
                is_recursive=is_recursive
            )
            self.db.add(file_permission)
            self.db.commit()
            self.db.refresh(file_permission)

            return file_permission

        except Exception as e:
            logger.error(f"Failed to set file permissions: {str(e)}")
            raise

    def get_file_permissions(self, domain_id: int, path: str) -> Dict[str, Any]:
        """Dosya/dizin izinlerini getir"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        full_path = os.path.join(self.web_root, domain.name, path.lstrip("/"))
        if not os.path.exists(full_path):
            raise ValueError("Path not found")

        try:
            stat = os.stat(full_path)
            return {
                "path": path,
                "owner": pwd.getpwuid(stat.st_uid).pw_name,
                "group": grp.getgrgid(stat.st_gid).gr_name,
                "permissions": oct(stat.st_mode)[-3:],
                "size": stat.st_size,
                "modified": stat.st_mtime
            }
        except Exception as e:
            logger.error(f"Failed to get file permissions: {str(e)}")
            raise 