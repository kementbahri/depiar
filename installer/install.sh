#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Bu script root yetkisi gerektirir.${NC}"
    exit 1
fi

# Check if port 8000 is in use
echo -e "${YELLOW}Port 8000 kontrol ediliyor...${NC}"
if lsof -i :8000 > /dev/null; then
    echo -e "${RED}Port 8000 kullanımda! Lütfen diğer servisleri durdurun.${NC}"
    exit 1
fi

# Check and create www-data user if not exists
echo -e "${YELLOW}Nginx kullanıcısı kontrol ediliyor...${NC}"
if ! id "www-data" &>/dev/null; then
    echo -e "${YELLOW}www-data kullanıcısı oluşturuluyor...${NC}"
    useradd -r -s /bin/false www-data
    groupadd -f www-data
    usermod -a -G www-data www-data
fi

# Check system requirements
echo -e "${YELLOW}Sistem gereksinimleri kontrol ediliyor...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 bulunamadı. Lütfen Python3'ü yükleyin.${NC}"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}pip3 bulunamadı. Lütfen pip3'ü yükleyin.${NC}"
    exit 1
fi

# Install system dependencies
echo -e "${YELLOW}Sistem bağımlılıkları yükleniyor...${NC}"
apt-get update
apt-get install -y python3-venv python3-dev build-essential libssl-dev libffi-dev nginx mysql-server lsof

# Create application directory
echo -e "${YELLOW}Uygulama dizini oluşturuluyor...${NC}"
mkdir -p /var/www/depiar
cd /var/www/depiar

# Create and activate virtual environment
echo -e "${YELLOW}Python sanal ortamı oluşturuluyor...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${YELLOW}Python bağımlılıkları yükleniyor...${NC}"
pip install --upgrade pip
pip install uvicorn[standard] fastapi sqlalchemy pymysql python-jose passlib python-multipart bcrypt python-dotenv requests aiofiles jinja2 slowapi

# Verify uvicorn installation
if ! command -v uvicorn &> /dev/null; then
    echo -e "${RED}Uvicorn kurulumu başarısız!${NC}"
    exit 1
fi

# Configure MySQL
echo -e "${YELLOW}MySQL yapılandırılıyor...${NC}"
mysql -e "CREATE DATABASE IF NOT EXISTS depiar CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS 'depiar'@'localhost' IDENTIFIED BY '${MYSQL_DEPIAR_PASSWORD}';"
mysql -e "GRANT ALL PRIVILEGES ON depiar.* TO 'depiar'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

# Create systemd service file
echo -e "${YELLOW}Systemd servis dosyası oluşturuluyor...${NC}"
cat > /etc/systemd/system/depiar.service << EOL
[Unit]
Description=Depiar API Service
After=network.target mysql.service
Requires=mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/depiar
Environment="PATH=/var/www/depiar/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=/var/www/depiar"
Environment="MYSQL_DEPIAR_PASSWORD=${MYSQL_DEPIAR_PASSWORD}"
ExecStart=/var/www/depiar/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload --log-level debug
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# Set permissions
echo -e "${YELLOW}Dizin izinleri ayarlanıyor...${NC}"
chown -R www-data:www-data /var/www/depiar
chmod -R 755 /var/www/depiar

# Configure Nginx
echo -e "${YELLOW}Nginx yapılandırılıyor...${NC}"
# Remove existing configuration
rm -f /etc/nginx/sites-enabled/depiar
rm -f /etc/nginx/sites-available/depiar

# Create Nginx main configuration
cat > /etc/nginx/nginx.conf << 'EOL'
user www-data;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 768;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    gzip on;
    gzip_disable "msie6";

    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOL

# Create Nginx site configuration
cat > /etc/nginx/sites-available/depiar << 'EOL'
server {
    listen 80 default_server;
    server_name _;

    client_max_body_size 100M;
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /var/www/depiar/static;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media {
        alias /var/www/depiar/media;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
EOL

# Create required directories for Nginx
echo -e "${YELLOW}Nginx dizinleri oluşturuluyor...${NC}"
mkdir -p /var/log/nginx
mkdir -p /var/cache/nginx
chown -R www-data:www-data /var/log/nginx
chown -R www-data:www-data /var/cache/nginx

# Enable Nginx site
ln -sf /etc/nginx/sites-available/depiar /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Enable and start services
echo -e "${YELLOW}Servisler etkinleştiriliyor ve başlatılıyor...${NC}"
systemctl daemon-reload

# Start MySQL first
echo -e "${YELLOW}MySQL başlatılıyor...${NC}"
systemctl enable mysql
systemctl restart mysql
sleep 5

# Start Depiar service first
echo -e "${YELLOW}Depiar servisi başlatılıyor...${NC}"
systemctl enable depiar
systemctl restart depiar
sleep 10

# Check if Depiar is running
if ! curl -s http://127.0.0.1:8000 > /dev/null; then
    echo -e "${RED}Depiar API servisi başlatılamadı!${NC}"
    journalctl -u depiar -n 50
    exit 1
fi

# Start Nginx
echo -e "${YELLOW}Nginx başlatılıyor...${NC}"
systemctl enable nginx
systemctl restart nginx
sleep 5

# Check service status
echo -e "${YELLOW}Servis durumları kontrol ediliyor...${NC}"
if systemctl is-active --quiet mysql; then
    echo -e "${GREEN}MySQL başarıyla başlatıldı!${NC}"
else
    echo -e "${RED}MySQL başlatılamadı!${NC}"
    journalctl -u mysql -n 50
    exit 1
fi

if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}Nginx başarıyla başlatıldı!${NC}"
else
    echo -e "${RED}Nginx başlatılamadı!${NC}"
    journalctl -u nginx -n 50
    exit 1
fi

if systemctl is-active --quiet depiar; then
    echo -e "${GREEN}Depiar API servisi başarıyla başlatıldı!${NC}"
else
    echo -e "${RED}Depiar API servisi başlatılamadı!${NC}"
    journalctl -u depiar -n 50
    exit 1
fi

echo -e "${GREEN}Kurulum tamamlandı!${NC}"
echo -e "${YELLOW}Panel arayüzüne http://localhost adresinden erişebilirsiniz.${NC}" 