import os
import shutil
import tarfile
import zipfile
import logging
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from ..models import FilePermission, FileOperation, FileSearch, DirectoryRestriction, Domain, User
from ..utils.ssh import SSHManager
import json
import re
import stat

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self, db: Session):
        self.db = db

    def set_file_permissions(self, domain_id: int, path: str, permissions: str, owner: str, group: str, is_recursive: bool = False):
        """Dosya izinlerini ayarla"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        ssh = SSHManager(domain.server.host, domain.server.port, domain.server.username, domain.server.password)

        try:
            # İzinleri ayarla
            chmod_cmd = f"chmod {permissions} {path}"
            if is_recursive:
                chmod_cmd += " -R"
            ssh.execute_command(chmod_cmd)

            # Sahip ve grubu ayarla
            chown_cmd = f"chown {owner}:{group} {path}"
            if is_recursive:
                chown_cmd += " -R"
            ssh.execute_command(chown_cmd)

            # Veritabanına kaydet
            file_perm = FilePermission(
                domain_id=domain_id,
                path=path,
                owner=owner,
                group=group,
                permissions=permissions,
                is_recursive=is_recursive
            )
            self.db.add(file_perm)
            self.db.commit()

            return file_perm

        except Exception as e:
            logger.error(f"Failed to set file permissions: {str(e)}")
            raise

    def copy_file(self, domain_id: int, user_id: int, source_path: str, destination_path: str):
        """Dosya kopyala"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        ssh = SSHManager(domain.server.host, domain.server.port, domain.server.username, domain.server.password)

        try:
            # Kopyalama işlemini başlat
            operation = FileOperation(
                domain_id=domain_id,
                user_id=user_id,
                operation_type="copy",
                source_path=source_path,
                destination_path=destination_path,
                status="in_progress"
            )
            self.db.add(operation)
            self.db.commit()

            # Dosyayı kopyala
            cp_cmd = f"cp -r {source_path} {destination_path}"
            ssh.execute_command(cp_cmd)

            # İşlemi tamamla
            operation.status = "completed"
            operation.completed_at = datetime.utcnow()
            self.db.commit()

            return operation

        except Exception as e:
            logger.error(f"Failed to copy file: {str(e)}")
            operation.status = "failed"
            operation.error_message = str(e)
            operation.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def move_file(self, domain_id: int, user_id: int, source_path: str, destination_path: str):
        """Dosya taşı"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        ssh = SSHManager(domain.server.host, domain.server.port, domain.server.username, domain.server.password)

        try:
            # Taşıma işlemini başlat
            operation = FileOperation(
                domain_id=domain_id,
                user_id=user_id,
                operation_type="move",
                source_path=source_path,
                destination_path=destination_path,
                status="in_progress"
            )
            self.db.add(operation)
            self.db.commit()

            # Dosyayı taşı
            mv_cmd = f"mv {source_path} {destination_path}"
            ssh.execute_command(mv_cmd)

            # İşlemi tamamla
            operation.status = "completed"
            operation.completed_at = datetime.utcnow()
            self.db.commit()

            return operation

        except Exception as e:
            logger.error(f"Failed to move file: {str(e)}")
            operation.status = "failed"
            operation.error_message = str(e)
            operation.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def compress_file(self, domain_id: int, user_id: int, source_path: str, destination_path: str, format: str = "zip"):
        """Dosya sıkıştır"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        ssh = SSHManager(domain.server.host, domain.server.port, domain.server.username, domain.server.password)

        try:
            # Sıkıştırma işlemini başlat
            operation = FileOperation(
                domain_id=domain_id,
                user_id=user_id,
                operation_type="compress",
                source_path=source_path,
                destination_path=destination_path,
                status="in_progress"
            )
            self.db.add(operation)
            self.db.commit()

            # Dosyayı sıkıştır
            if format == "zip":
                zip_cmd = f"zip -r {destination_path} {source_path}"
                ssh.execute_command(zip_cmd)
            elif format == "tar.gz":
                tar_cmd = f"tar -czf {destination_path} {source_path}"
                ssh.execute_command(tar_cmd)

            # İşlemi tamamla
            operation.status = "completed"
            operation.completed_at = datetime.utcnow()
            self.db.commit()

            return operation

        except Exception as e:
            logger.error(f"Failed to compress file: {str(e)}")
            operation.status = "failed"
            operation.error_message = str(e)
            operation.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def extract_file(self, domain_id: int, user_id: int, source_path: str, destination_path: str):
        """Dosya çıkart"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        ssh = SSHManager(domain.server.host, domain.server.port, domain.server.username, domain.server.password)

        try:
            # Çıkartma işlemini başlat
            operation = FileOperation(
                domain_id=domain_id,
                user_id=user_id,
                operation_type="extract",
                source_path=source_path,
                destination_path=destination_path,
                status="in_progress"
            )
            self.db.add(operation)
            self.db.commit()

            # Dosyayı çıkart
            if source_path.endswith(".zip"):
                unzip_cmd = f"unzip {source_path} -d {destination_path}"
                ssh.execute_command(unzip_cmd)
            elif source_path.endswith(".tar.gz"):
                tar_cmd = f"tar -xzf {source_path} -C {destination_path}"
                ssh.execute_command(tar_cmd)

            # İşlemi tamamla
            operation.status = "completed"
            operation.completed_at = datetime.utcnow()
            self.db.commit()

            return operation

        except Exception as e:
            logger.error(f"Failed to extract file: {str(e)}")
            operation.status = "failed"
            operation.error_message = str(e)
            operation.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def search_files(self, domain_id: int, user_id: int, search_term: str, search_path: str, file_type: str = "all", 
                    size_min: Optional[int] = None, size_max: Optional[int] = None,
                    modified_after: Optional[datetime] = None, modified_before: Optional[datetime] = None):
        """Dosya ara"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        ssh = SSHManager(domain.server.host, domain.server.port, domain.server.username, domain.server.password)

        try:
            # Arama komutunu oluştur
            find_cmd = f"find {search_path} -name '*{search_term}*'"
            
            if file_type == "file":
                find_cmd += " -type f"
            elif file_type == "directory":
                find_cmd += " -type d"

            if size_min is not None:
                find_cmd += f" -size +{size_min}c"
            if size_max is not None:
                find_cmd += f" -size -{size_max}c"

            if modified_after is not None:
                find_cmd += f" -newermt '{modified_after.strftime('%Y-%m-%d %H:%M:%S')}'"
            if modified_before is not None:
                find_cmd += f" -not -newermt '{modified_before.strftime('%Y-%m-%d %H:%M:%S')}'"

            # Arama yap
            results = ssh.execute_command(find_cmd)

            # Sonuçları kaydet
            search = FileSearch(
                domain_id=domain_id,
                user_id=user_id,
                search_term=search_term,
                search_path=search_path,
                file_type=file_type,
                size_min=size_min,
                size_max=size_max,
                modified_after=modified_after,
                modified_before=modified_before,
                results=results
            )
            self.db.add(search)
            self.db.commit()

            return search

        except Exception as e:
            logger.error(f"Failed to search files: {str(e)}")
            raise

    def add_directory_restriction(self, domain_id: int, path: str, restriction_type: str, 
                                allowed_users: List[str], allowed_groups: List[str], is_recursive: bool = True):
        """Dizin kısıtlaması ekle"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        ssh = SSHManager(domain.server.host, domain.server.port, domain.server.username, domain.server.password)

        try:
            # Kısıtlamayı kaydet
            restriction = DirectoryRestriction(
                domain_id=domain_id,
                path=path,
                restriction_type=restriction_type,
                allowed_users=allowed_users,
                allowed_groups=allowed_groups,
                is_recursive=is_recursive
            )
            self.db.add(restriction)
            self.db.commit()

            # ACL'leri ayarla
            if restriction_type == "read":
                acl_cmd = f"setfacl -R -m u::r-x,g::r-x,o::--- {path}"
            elif restriction_type == "write":
                acl_cmd = f"setfacl -R -m u::rwx,g::r-x,o::--- {path}"
            elif restriction_type == "execute":
                acl_cmd = f"setfacl -R -m u::r-x,g::r-x,o::--- {path}"
            else:  # all
                acl_cmd = f"setfacl -R -m u::rwx,g::r-x,o::--- {path}"

            if not is_recursive:
                acl_cmd = acl_cmd.replace("-R", "")

            ssh.execute_command(acl_cmd)

            # İzin verilen kullanıcılar için ACL ekle
            for user in allowed_users:
                user_acl = f"setfacl -R -m u:{user}:rwx {path}"
                if not is_recursive:
                    user_acl = user_acl.replace("-R", "")
                ssh.execute_command(user_acl)

            # İzin verilen gruplar için ACL ekle
            for group in allowed_groups:
                group_acl = f"setfacl -R -m g:{group}:rwx {path}"
                if not is_recursive:
                    group_acl = group_acl.replace("-R", "")
                ssh.execute_command(group_acl)

            return restriction

        except Exception as e:
            logger.error(f"Failed to add directory restriction: {str(e)}")
            raise

    def check_file_permissions(self, domain_id: int, path: str) -> Dict:
        """Dosya izinlerini kontrol et"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        ssh = SSHManager(domain.server.host, domain.server.port, domain.server.username, domain.server.password)

        try:
            # ls -l komutu ile izinleri al
            ls_cmd = f"ls -l {path}"
            result = ssh.execute_command(ls_cmd)[0]

            # İzinleri parse et
            parts = result.split()
            permissions = parts[0]
            owner = parts[2]
            group = parts[3]
            size = int(parts[4])
            modified = " ".join(parts[5:8])

            return {
                "permissions": permissions,
                "owner": owner,
                "group": group,
                "size": size,
                "modified": modified
            }

        except Exception as e:
            logger.error(f"Failed to check file permissions: {str(e)}")
            raise 