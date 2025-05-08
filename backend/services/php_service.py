import os
import subprocess
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models import PHPConfiguration, Domain
import yaml
from datetime import datetime

logger = logging.getLogger(__name__)

class PHPService:
    def __init__(self, db: Session):
        self.db = db
        self.php_versions = ["7.4", "8.0", "8.1", "8.2"]
        self.php_fpm_pool_dir = "/etc/php/{version}/fpm/pool.d"
        self.php_fpm_conf_dir = "/etc/php/{version}/fpm"
        self.php_ini_dir = "/etc/php/{version}/fpm/conf.d"

    def create_php_config(self, domain_id: int, version: str) -> PHPConfiguration:
        """Domain için PHP yapılandırması oluştur"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        if not domain.server_id:
            raise ValueError("Domain has no associated server")

        # PHP-FPM havuzu oluştur
        pool_name = f"{domain.name}.conf"
        pool_config = self._generate_pool_config(domain, version)
        self._write_pool_config(version, pool_name, pool_config)

        # PHP yapılandırmasını kaydet
        php_config = PHPConfiguration(
            server_id=domain.server_id,
            domain_id=domain_id,
            version=version,
            config_path=f"{self.php_fpm_pool_dir.format(version=version)}/{pool_name}",
            fpm_status="active"
        )
        self.db.add(php_config)
        self.db.commit()
        self.db.refresh(php_config)

        # PHP-FPM'i yeniden başlat
        self._restart_php_fpm(version)

        return php_config

    def update_php_config(self, config_id: int, settings: Dict[str, Any]) -> PHPConfiguration:
        """PHP yapılandırmasını güncelle"""
        config = self.db.query(PHPConfiguration).filter(PHPConfiguration.id == config_id).first()
        if not config:
            raise ValueError("PHP configuration not found")

        # PHP.ini ayarlarını güncelle
        self._update_php_ini(config.version, settings)

        # Yapılandırmayı güncelle
        for key, value in settings.items():
            if hasattr(config, key):
                setattr(config, key, value)
        config.last_modified = datetime.utcnow()

        self.db.commit()
        self.db.refresh(config)

        # PHP-FPM'i yeniden başlat
        self._restart_php_fpm(config.version)

        return config

    def _generate_pool_config(self, domain: Domain, version: str) -> str:
        """PHP-FPM havuz yapılandırması oluştur"""
        return f"""[{domain.name}]
user = {domain.name}
group = {domain.name}
listen = /run/php/php{version}-fpm-{domain.name}.sock
listen.owner = www-data
listen.group = www-data
pm = dynamic
pm.max_children = 5
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 3
php_admin_value[upload_max_filesize] = 32M
php_admin_value[post_max_size] = 32M
php_admin_value[memory_limit] = 256M
php_admin_value[max_execution_time] = 30
php_admin_value[max_input_vars] = 3000
"""

    def _write_pool_config(self, version: str, pool_name: str, config: str) -> None:
        """PHP-FPM havuz yapılandırmasını kaydet"""
        pool_path = os.path.join(
            self.php_fpm_pool_dir.format(version=version),
            pool_name
        )
        with open(pool_path, "w") as f:
            f.write(config)

    def _update_php_ini(self, version: str, settings: Dict[str, Any]) -> None:
        """PHP.ini ayarlarını güncelle"""
        ini_path = os.path.join(
            self.php_ini_dir.format(version=version),
            "custom.ini"
        )
        
        # Mevcut ayarları oku
        current_settings = {}
        if os.path.exists(ini_path):
            with open(ini_path, "r") as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        current_settings[key.strip()] = value.strip()

        # Yeni ayarları ekle/güncelle
        current_settings.update(settings)

        # Ayarları kaydet
        with open(ini_path, "w") as f:
            for key, value in current_settings.items():
                f.write(f"{key} = {value}\n")

    def _restart_php_fpm(self, version: str) -> None:
        """PHP-FPM'i yeniden başlat"""
        try:
            subprocess.run(
                ["systemctl", "restart", f"php{version}-fpm"],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart PHP-FPM: {e.stderr.decode()}")
            raise

    def get_available_versions(self) -> List[str]:
        """Kullanılabilir PHP versiyonlarını getir"""
        return self.php_versions

    def get_php_info(self, version: str) -> Dict[str, Any]:
        """PHP bilgilerini getir"""
        try:
            result = subprocess.run(
                ["php", "-i"],
                capture_output=True,
                text=True
            )
            return {
                "version": version,
                "info": result.stdout
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get PHP info: {e.stderr}")
            raise 