import subprocess
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from ..models import SoftwareVersion, PHPConfiguration, DatabaseServer, WebServer, SSHServer
from ..utils.ssh import SSHManager
import json
import re

logger = logging.getLogger(__name__)

class SoftwareService:
    def __init__(self, db: Session):
        self.db = db

    def check_software_versions(self, server_id: int):
        """Sunucudaki yazılım versiyonlarını kontrol et"""
        server = self.db.query(SSHServer).filter(SSHServer.id == server_id).first()
        if not server:
            raise ValueError("Server not found")

        ssh = SSHManager(server.host, server.port, server.username, server.password)

        try:
            # PHP versiyonlarını kontrol et
            php_cmd = "php -v"
            php_version = ssh.execute_command(php_cmd)[0].split()[1]
            php_available = self._get_available_php_versions(ssh)
            
            self._update_software_version(
                server,
                "php",
                php_version,
                php_available
            )

            # MySQL/MariaDB versiyonunu kontrol et
            mysql_cmd = "mysql --version"
            mysql_version = ssh.execute_command(mysql_cmd)[0].split()[4]
            mysql_available = self._get_available_mysql_versions(ssh)
            
            self._update_software_version(
                server,
                "mysql",
                mysql_version,
                mysql_available
            )

            # Apache versiyonunu kontrol et
            apache_cmd = "apache2 -v"
            apache_version = ssh.execute_command(apache_cmd)[0].split()[2].split("/")[1]
            apache_available = self._get_available_apache_versions(ssh)
            
            self._update_software_version(
                server,
                "apache",
                apache_version,
                apache_available
            )

            # Nginx versiyonunu kontrol et
            nginx_cmd = "nginx -v"
            nginx_version = ssh.execute_command(nginx_cmd)[0].split()[2].split("/")[1]
            nginx_available = self._get_available_nginx_versions(ssh)
            
            self._update_software_version(
                server,
                "nginx",
                nginx_version,
                nginx_available
            )

        except Exception as e:
            logger.error(f"Software version check failed: {str(e)}")
            raise

    def update_php_version(self, server_id: int, target_version: str):
        """PHP versiyonunu güncelle"""
        server = self.db.query(SSHServer).filter(SSHServer.id == server_id).first()
        if not server:
            raise ValueError("Server not found")

        ssh = SSHManager(server.host, server.port, server.username, server.password)

        try:
            # PHP-FPM'i durdur
            ssh.execute_command("systemctl stop php-fpm")

            # PHP'yi güncelle
            update_cmd = f"apt-get install -y php{target_version} php{target_version}-fpm php{target_version}-mysql php{target_version}-cli php{target_version}-common php{target_version}-json php{target_version}-opcache php{target_version}-mbstring php{target_version}-xml php{target_version}-gd php{target_version}-curl"
            ssh.execute_command(update_cmd)

            # PHP-FPM'i başlat
            ssh.execute_command("systemctl start php-fpm")

            # Versiyon bilgisini güncelle
            self._update_software_version(
                server,
                "php",
                target_version,
                self._get_available_php_versions(ssh)
            )

            return True

        except Exception as e:
            logger.error(f"PHP update failed: {str(e)}")
            raise

    def update_mysql_version(self, server_id: int, target_version: str):
        """MySQL/MariaDB versiyonunu güncelle"""
        server = self.db.query(SSHServer).filter(SSHServer.id == server_id).first()
        if not server:
            raise ValueError("Server not found")

        ssh = SSHManager(server.host, server.port, server.username, server.password)

        try:
            # MySQL'i durdur
            ssh.execute_command("systemctl stop mysql")

            # MySQL'i güncelle
            update_cmd = f"apt-get install -y mysql-server-{target_version}"
            ssh.execute_command(update_cmd)

            # MySQL'i başlat
            ssh.execute_command("systemctl start mysql")

            # Versiyon bilgisini güncelle
            self._update_software_version(
                server,
                "mysql",
                target_version,
                self._get_available_mysql_versions(ssh)
            )

            return True

        except Exception as e:
            logger.error(f"MySQL update failed: {str(e)}")
            raise

    def update_apache_version(self, server_id: int, target_version: str):
        """Apache versiyonunu güncelle"""
        server = self.db.query(SSHServer).filter(SSHServer.id == server_id).first()
        if not server:
            raise ValueError("Server not found")

        ssh = SSHManager(server.host, server.port, server.username, server.password)

        try:
            # Apache'yi durdur
            ssh.execute_command("systemctl stop apache2")

            # Apache'yi güncelle
            update_cmd = f"apt-get install -y apache2={target_version}*"
            ssh.execute_command(update_cmd)

            # Apache'yi başlat
            ssh.execute_command("systemctl start apache2")

            # Versiyon bilgisini güncelle
            self._update_software_version(
                server,
                "apache",
                target_version,
                self._get_available_apache_versions(ssh)
            )

            return True

        except Exception as e:
            logger.error(f"Apache update failed: {str(e)}")
            raise

    def update_nginx_version(self, server_id: int, target_version: str):
        """Nginx versiyonunu güncelle"""
        server = self.db.query(SSHServer).filter(SSHServer.id == server_id).first()
        if not server:
            raise ValueError("Server not found")

        ssh = SSHManager(server.host, server.port, server.username, server.password)

        try:
            # Nginx'i durdur
            ssh.execute_command("systemctl stop nginx")

            # Nginx'i güncelle
            update_cmd = f"apt-get install -y nginx={target_version}*"
            ssh.execute_command(update_cmd)

            # Nginx'i başlat
            ssh.execute_command("systemctl start nginx")

            # Versiyon bilgisini güncelle
            self._update_software_version(
                server,
                "nginx",
                target_version,
                self._get_available_nginx_versions(ssh)
            )

            return True

        except Exception as e:
            logger.error(f"Nginx update failed: {str(e)}")
            raise

    def update_php_config(self, server_id: int, config: Dict):
        """PHP yapılandırmasını güncelle"""
        server = self.db.query(SSHServer).filter(SSHServer.id == server_id).first()
        if not server:
            raise ValueError("Server not found")

        php_config = self.db.query(PHPConfiguration).filter(
            PHPConfiguration.server_id == server_id
        ).first()

        if not php_config:
            php_config = PHPConfiguration(server_id=server_id)

        # Yapılandırmayı güncelle
        for key, value in config.items():
            setattr(php_config, key, value)

        php_config.last_modified = datetime.utcnow()
        self.db.add(php_config)
        self.db.commit()

        # PHP-FPM'i yeniden başlat
        ssh = SSHManager(server.host, server.port, server.username, server.password)
        ssh.execute_command("systemctl restart php-fpm")

        return php_config

    def update_database_config(self, server_id: int, config: Dict):
        """Veritabanı yapılandırmasını güncelle"""
        server = self.db.query(SSHServer).filter(SSHServer.id == server_id).first()
        if not server:
            raise ValueError("Server not found")

        db_config = self.db.query(DatabaseServer).filter(
            DatabaseServer.server_id == server_id
        ).first()

        if not db_config:
            db_config = DatabaseServer(server_id=server_id)

        # Yapılandırmayı güncelle
        for key, value in config.items():
            setattr(db_config, key, value)

        db_config.last_modified = datetime.utcnow()
        self.db.add(db_config)
        self.db.commit()

        # MySQL'i yeniden başlat
        ssh = SSHManager(server.host, server.port, server.username, server.password)
        ssh.execute_command("systemctl restart mysql")

        return db_config

    def update_web_server_config(self, server_id: int, config: Dict):
        """Web sunucusu yapılandırmasını güncelle"""
        server = self.db.query(SSHServer).filter(SSHServer.id == server_id).first()
        if not server:
            raise ValueError("Server not found")

        web_config = self.db.query(WebServer).filter(
            WebServer.server_id == server_id
        ).first()

        if not web_config:
            web_config = WebServer(server_id=server_id)

        # Yapılandırmayı güncelle
        for key, value in config.items():
            setattr(web_config, key, value)

        web_config.last_modified = datetime.utcnow()
        self.db.add(web_config)
        self.db.commit()

        # Web sunucusunu yeniden başlat
        ssh = SSHManager(server.host, server.port, server.username, server.password)
        if web_config.type == "apache":
            ssh.execute_command("systemctl restart apache2")
        else:
            ssh.execute_command("systemctl restart nginx")

        return web_config

    def _update_software_version(
        self,
        server: SSHServer,
        software_type: str,
        current_version: str,
        available_versions: List[str]
    ):
        """Yazılım versiyon bilgisini güncelle"""
        version = self.db.query(SoftwareVersion).filter(
            SoftwareVersion.server_id == server.id,
            SoftwareVersion.software_type == software_type
        ).first()

        if not version:
            version = SoftwareVersion(
                server_id=server.id,
                software_type=software_type
            )

        version.current_version = current_version
        version.available_versions = available_versions
        version.last_check = datetime.utcnow()
        self.db.add(version)
        self.db.commit()

    def _get_available_php_versions(self, ssh: SSHManager) -> List[str]:
        """Kullanılabilir PHP versiyonlarını al"""
        cmd = "apt-cache search php[0-9]\\.[0-9] | grep '^php[0-9]\\.[0-9]' | cut -d' ' -f1 | sort -V | uniq"
        result = ssh.execute_command(cmd)
        return [v.replace("php", "") for v in result]

    def _get_available_mysql_versions(self, ssh: SSHManager) -> List[str]:
        """Kullanılabilir MySQL versiyonlarını al"""
        cmd = "apt-cache search mysql-server-[0-9]\\.[0-9] | grep '^mysql-server-[0-9]\\.[0-9]' | cut -d' ' -f1 | sort -V | uniq"
        result = ssh.execute_command(cmd)
        return [v.replace("mysql-server-", "") for v in result]

    def _get_available_apache_versions(self, ssh: SSHManager) -> List[str]:
        """Kullanılabilir Apache versiyonlarını al"""
        cmd = "apt-cache search apache2 | grep '^apache2 ' | cut -d' ' -f1 | sort -V | uniq"
        result = ssh.execute_command(cmd)
        return [v.replace("apache2", "") for v in result]

    def _get_available_nginx_versions(self, ssh: SSHManager) -> List[str]:
        """Kullanılabilir Nginx versiyonlarını al"""
        cmd = "apt-cache search nginx | grep '^nginx ' | cut -d' ' -f1 | sort -V | uniq"
        result = ssh.execute_command(cmd)
        return [v.replace("nginx", "") for v in result] 