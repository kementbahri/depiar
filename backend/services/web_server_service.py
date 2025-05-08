import os
import subprocess
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models import WebServer, Domain
import yaml
from datetime import datetime

logger = logging.getLogger(__name__)

class WebServerService:
    def __init__(self, db: Session):
        self.db = db
        self.nginx_conf_dir = "/etc/nginx"
        self.nginx_sites_dir = "/etc/nginx/sites-available"
        self.nginx_sites_enabled = "/etc/nginx/sites-enabled"
        self.apache_conf_dir = "/etc/apache2"
        self.apache_sites_dir = "/etc/apache2/sites-available"
        self.apache_sites_enabled = "/etc/apache2/sites-enabled"

    def create_virtual_host(self, domain_id: int, server_type: str = "nginx") -> WebServer:
        """Domain için virtual host oluştur"""
        domain = self.db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            raise ValueError("Domain not found")

        if not domain.server_id:
            raise ValueError("Domain has no associated server")

        if server_type == "nginx":
            config = self._generate_nginx_config(domain)
            config_path = os.path.join(self.nginx_sites_dir, f"{domain.name}.conf")
            self._write_config(config_path, config)
            self._enable_site(domain.name, "nginx")
        elif server_type == "apache":
            config = self._generate_apache_config(domain)
            config_path = os.path.join(self.apache_sites_dir, f"{domain.name}.conf")
            self._write_config(config_path, config)
            self._enable_site(domain.name, "apache")
        else:
            raise ValueError(f"Unsupported server type: {server_type}")

        # Web sunucu yapılandırmasını kaydet
        web_server = WebServer(
            server_id=domain.server_id,
            domain_id=domain_id,
            type=server_type,
            version=self._get_server_version(server_type),
            config_path=config_path,
            document_root=f"/var/www/{domain.name}/public_html",
            status="active"
        )
        self.db.add(web_server)
        self.db.commit()
        self.db.refresh(web_server)

        # Web sunucusunu yeniden başlat
        self._restart_server(server_type)

        return web_server

    def _generate_nginx_config(self, domain: Domain) -> str:
        """Nginx virtual host yapılandırması oluştur"""
        return f"""server {{
    listen 80;
    server_name {domain.name} www.{domain.name};
    root /var/www/{domain.name}/public_html;
    index index.php index.html index.htm;

    location / {{
        try_files $uri $uri/ /index.php?$query_string;
    }}

    location ~ \.php$ {{
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/run/php/php{domain.php_version}-fpm-{domain.name}.sock;
    }}

    location ~ /\.ht {{
        deny all;
    }}

    # SSL yapılandırması
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/{domain.name}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain.name}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}}
"""

    def _generate_apache_config(self, domain: Domain) -> str:
        """Apache virtual host yapılandırması oluştur"""
        return f"""<VirtualHost *:80>
    ServerName {domain.name}
    ServerAlias www.{domain.name}
    DocumentRoot /var/www/{domain.name}/public_html

    <Directory /var/www/{domain.name}/public_html>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    <FilesMatch \.php$>
        SetHandler "proxy:unix:/run/php/php{domain.php_version}-fpm-{domain.name}.sock|fcgi://localhost"
    </FilesMatch>

    ErrorLog ${{APACHE_LOG_DIR}}/{domain.name}-error.log
    CustomLog ${{APACHE_LOG_DIR}}/{domain.name}-access.log combined
</VirtualHost>

<VirtualHost *:443>
    ServerName {domain.name}
    ServerAlias www.{domain.name}
    DocumentRoot /var/www/{domain.name}/public_html

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/{domain.name}/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/{domain.name}/privkey.pem

    <Directory /var/www/{domain.name}/public_html>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    <FilesMatch \.php$>
        SetHandler "proxy:unix:/run/php/php{domain.php_version}-fpm-{domain.name}.sock|fcgi://localhost"
    </FilesMatch>

    ErrorLog ${{APACHE_LOG_DIR}}/{domain.name}-error.log
    CustomLog ${{APACHE_LOG_DIR}}/{domain.name}-access.log combined
</VirtualHost>
"""

    def _write_config(self, path: str, config: str) -> None:
        """Yapılandırma dosyasını kaydet"""
        with open(path, "w") as f:
            f.write(config)

    def _enable_site(self, domain_name: str, server_type: str) -> None:
        """Virtual host'u etkinleştir"""
        if server_type == "nginx":
            source = os.path.join(self.nginx_sites_dir, f"{domain_name}.conf")
            target = os.path.join(self.nginx_sites_enabled, f"{domain_name}.conf")
        else:
            source = os.path.join(self.apache_sites_dir, f"{domain_name}.conf")
            target = os.path.join(self.apache_sites_enabled, f"{domain_name}.conf")

        if not os.path.exists(target):
            os.symlink(source, target)

    def _restart_server(self, server_type: str) -> None:
        """Web sunucusunu yeniden başlat"""
        try:
            if server_type == "nginx":
                subprocess.run(["systemctl", "restart", "nginx"], check=True)
            else:
                subprocess.run(["systemctl", "restart", "apache2"], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart {server_type}: {e.stderr.decode()}")
            raise

    def _get_server_version(self, server_type: str) -> str:
        """Web sunucu versiyonunu al"""
        try:
            if server_type == "nginx":
                result = subprocess.run(
                    ["nginx", "-v"],
                    capture_output=True,
                    text=True
                )
            else:
                result = subprocess.run(
                    ["apache2", "-v"],
                    capture_output=True,
                    text=True
                )
            return result.stderr.split("/")[1].split()[0]
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get {server_type} version: {e.stderr}")
            raise 